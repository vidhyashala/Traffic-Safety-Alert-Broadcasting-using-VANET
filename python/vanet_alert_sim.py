#!/usr/bin/env python3
"""Traffic Safety Alert Broadcasting using SUMO TraCI.

This script runs an end-to-end VANET alert workflow:
1. Detect sudden braking and accident injection events.
2. Generate priority alerts with TTL and distance filtering.
3. Broadcast alerts to nearby vehicles.
4. Apply reaction policies (slow down / reroute).
5. Write detailed logs for post-processing and metrics.
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import sys

import joblib
import pandas as pd
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

try:
    import traci
except ImportError as exc:  # pragma: no cover - runtime dependency
    raise SystemExit(
        "TraCI not found. Install SUMO and set SUMO_HOME before running."
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
SUMO_CFG = PROJECT_ROOT / "sumo" / "traffic_safety.sumocfg"

COMM_RANGE_M = 250.0
TTL_DEFAULT = 5
FORWARD_PROBABILITY = 0.65
SUDDEN_BRAKE_THRESHOLD = -4.0
REACTION_DECEL_SPEED = 8.0
MODEL_PATH = PROJECT_ROOT / "models" / "alert_priority_model.joblib"


@dataclass
class AlertMessage:
    """Represents a safety alert in the simulated vehicular network."""

    msg_id: str
    source_vehicle: str
    event_type: str
    x: float
    y: float
    timestamp: float
    ttl: int
    priority: int
    origin_edge: str
    hops: int = 0
    seen_by: Set[str] = field(default_factory=set)


class VanetAlertSimulator:
    """Main simulation controller implementing broadcast + reaction logic."""

    def __init__(self, use_gui: bool = True, seed: int = 42) -> None:
        self.use_gui = use_gui
        self.seed = seed
        random.seed(seed)
        self.prev_speed: Dict[str, float] = {}
        self.active_alerts: Dict[str, AlertMessage] = {}
        self.vehicle_alert_cache: Dict[str, Set[str]] = {}
        self.generated_count = 0
        self.accident_vehicle = ""
        self.step_length = 0.1
        self.max_steps = 5000
        self.packet_log_rows: List[Dict[str, object]] = []
        self.priority_model = self._load_priority_model()

    def _sumo_binary(self) -> str:
        return "sumo-gui" if self.use_gui else "sumo"

    def _load_priority_model(self):
        if not MODEL_PATH.exists():
            return None
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return None

    def _predict_priority(self, vehicle_id: str, event_type: str) -> int:
        if self.priority_model is None:
            return 5 if event_type == "accident" else 3
        speed = traci.vehicle.getSpeed(vehicle_id)
        decel = abs((speed - self.prev_speed.get(vehicle_id, speed)) / self.step_length)
        x, y = traci.vehicle.getPosition(vehicle_id)
        center_dist = math.dist((x, y), (500.0, 0.0))
        data = pd.DataFrame([{
            "avg_speed": speed,
            "deceleration": decel,
            "distance_to_event": center_dist,
            "vehicle_density": len(traci.vehicle.getIDList()),
            "event_type": event_type,
            "hop_count": 0,
        }])
        predicted = int(self.priority_model.predict(data)[0])
        return max(2, min(5, predicted))

    def start(self) -> None:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        cmd = [
            self._sumo_binary(),
            "-c",
            str(SUMO_CFG),
            "--step-length",
            str(self.step_length),
            "--seed",
            str(self.seed),
        ]
        traci.start(cmd)

    def stop(self) -> None:
        traci.close()

    def run(self) -> None:
        self.start()
        try:
            for step in range(self.max_steps):
                traci.simulationStep()
                sim_time = traci.simulation.getTime()

                if step == 700:
                    self._inject_accident(sim_time)

                vehicle_ids = traci.vehicle.getIDList()
                self._detect_sudden_braking(vehicle_ids, sim_time)
                self._propagate_alerts(vehicle_ids, sim_time)

                if sim_time >= 500.0:
                    break

            self._write_logs()
        finally:
            self.stop()

    def _inject_accident(self, sim_time: float) -> None:
        """Simulate an accident by hard-stopping one vehicle in the center edge."""
        candidates = [vid for vid in traci.vehicle.getIDList() if "f_eastbound" in vid]
        if not candidates:
            return
        self.accident_vehicle = candidates[0]
        traci.vehicle.setSpeed(self.accident_vehicle, 0.0)
        priority = self._predict_priority(self.accident_vehicle, "accident")
        self._create_alert(self.accident_vehicle, "accident", sim_time, priority=priority)

    def _detect_sudden_braking(self, vehicle_ids: List[str], sim_time: float) -> None:
        for vid in vehicle_ids:
            speed = traci.vehicle.getSpeed(vid)
            prev = self.prev_speed.get(vid, speed)
            accel = (speed - prev) / self.step_length
            self.prev_speed[vid] = speed

            if accel < SUDDEN_BRAKE_THRESHOLD and speed > 1.0:
                priority = self._predict_priority(vid, "sudden_brake")
                self._create_alert(vid, "sudden_brake", sim_time, priority=priority)

    def _create_alert(self, vehicle_id: str, event_type: str, sim_time: float, priority: int) -> None:
        pos_x, pos_y = traci.vehicle.getPosition(vehicle_id)
        edge_id = traci.vehicle.getRoadID(vehicle_id)
        self.generated_count += 1
        msg_id = f"A{self.generated_count:04d}"
        self.active_alerts[msg_id] = AlertMessage(
            msg_id=msg_id,
            source_vehicle=vehicle_id,
            event_type=event_type,
            x=pos_x,
            y=pos_y,
            timestamp=sim_time,
            ttl=TTL_DEFAULT,
            priority=priority,
            origin_edge=edge_id,
            seen_by={vehicle_id},
        )
        self._log_packet(
            sim_time,
            msg_id,
            vehicle_id,
            "GENERATED",
            vehicle_id,
            0,
            event_type,
        )

    def _propagate_alerts(self, vehicle_ids: List[str], sim_time: float) -> None:
        for msg_id, alert in list(self.active_alerts.items()):
            if alert.ttl <= 0:
                del self.active_alerts[msg_id]
                continue

            sender_pool = list(alert.seen_by)
            for sender in sender_pool:
                if sender not in vehicle_ids:
                    continue
                sx, sy = traci.vehicle.getPosition(sender)

                for receiver in vehicle_ids:
                    if receiver == sender:
                        continue

                    cache = self.vehicle_alert_cache.setdefault(receiver, set())
                    if msg_id in cache:
                        continue

                    rx, ry = traci.vehicle.getPosition(receiver)
                    distance = math.dist((sx, sy), (rx, ry))

                    # Bonus improvement: distance-based filtering by priority.
                    effective_range = COMM_RANGE_M + (50.0 * alert.priority)
                    if distance > effective_range:
                        continue

                    delay = random.uniform(0.01, 0.08)
                    if random.random() > FORWARD_PROBABILITY and alert.hops > 0:
                        continue

                    cache.add(msg_id)
                    alert.seen_by.add(receiver)
                    self._log_packet(
                        sim_time + delay,
                        msg_id,
                        sender,
                        "RECEIVED",
                        receiver,
                        alert.hops + 1,
                        alert.event_type,
                    )
                    self._apply_vehicle_reaction(receiver, alert)

            alert.ttl -= 1
            alert.hops += 1

    def _apply_vehicle_reaction(self, vehicle_id: str, alert: AlertMessage) -> None:
        """Simple reaction policy after receiving a safety alert."""
        current_speed = traci.vehicle.getSpeed(vehicle_id)
        if current_speed > REACTION_DECEL_SPEED:
            traci.vehicle.slowDown(vehicle_id, REACTION_DECEL_SPEED, 2.0)

        # Optional reroute for high-priority accident alerts.
        if alert.event_type == "accident" and alert.priority >= 5:
            try:
                traci.vehicle.rerouteTraveltime(vehicle_id, True)
            except traci.exceptions.TraCIException:
                # Some vehicles may not have alternate routes.
                pass

    def _log_packet(
        self,
        timestamp: float,
        msg_id: str,
        source: str,
        status: str,
        target: str,
        hop: int,
        event_type: str,
    ) -> None:
        self.packet_log_rows.append(
            {
                "time": round(timestamp, 3),
                "msg_id": msg_id,
                "source": source,
                "target": target,
                "status": status,
                "hop": hop,
                "event": event_type,
            }
        )

    def _write_logs(self) -> None:
        packet_log = RESULTS_DIR / "alert_packet_log.csv"
        with packet_log.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["time", "msg_id", "source", "target", "status", "hop", "event"]
            )
            writer.writeheader()
            writer.writerows(sorted(self.packet_log_rows, key=lambda r: (r["time"], r["msg_id"])))

        summary = {
            "total_generated": self.generated_count,
            "total_records": len(self.packet_log_rows),
            "seed": self.seed,
            "comm_range_m": COMM_RANGE_M,
            "ttl_default": TTL_DEFAULT,
        }
        (RESULTS_DIR / "simulation_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )


def main() -> None:
    use_gui = "--nogui" not in sys.argv
    sim = VanetAlertSimulator(use_gui=use_gui)
    sim.run()
    print("Simulation complete. Logs written to results/.")


if __name__ == "__main__":
    main()
