#!/usr/bin/env python3
"""Compute VANET safety broadcast performance metrics from logs."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
PACKET_LOG = RESULTS_DIR / "alert_packet_log.csv"
OUTPUT_JSON = RESULTS_DIR / "metrics.json"


def load_rows() -> list[dict[str, str]]:
    if not PACKET_LOG.exists():
        raise FileNotFoundError("Run vanet_alert_sim.py first to generate logs.")
    with PACKET_LOG.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_metrics(rows: list[dict[str, str]]) -> dict[str, float]:
    generated = [r for r in rows if r["status"] == "GENERATED"]
    received = [r for r in rows if r["status"] == "RECEIVED"]

    msg_gen_time: dict[str, float] = {r["msg_id"]: float(r["time"]) for r in generated}
    msg_receipts: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in received:
        msg_receipts[row["msg_id"]].append(row)

    total_generated = len(generated)
    delivered_msgs = sum(1 for msg_id in msg_gen_time if msg_receipts.get(msg_id))
    pdr = (delivered_msgs / total_generated) if total_generated else 0.0

    delays = []
    all_hops = []
    for msg_id, recs in msg_receipts.items():
        gen_time = msg_gen_time[msg_id]
        for rec in recs:
            delays.append(float(rec["time"]) - gen_time)
            all_hops.append(int(rec["hop"]))

    avg_delay = sum(delays) / len(delays) if delays else 0.0

    sim_duration = max(float(r["time"]) for r in rows) - min(float(r["time"]) for r in rows)
    throughput = len(received) / sim_duration if sim_duration > 0 else 0.0

    max_hop = max(all_hops) if all_hops else 0

    return {
        "packet_delivery_ratio": round(pdr, 4),
        "avg_end_to_end_delay_s": round(avg_delay, 4),
        "throughput_packets_per_s": round(throughput, 4),
        "dissemination_range_hops": max_hop,
        "generated_alerts": total_generated,
        "received_packets": len(received),
    }


def main() -> None:
    rows = load_rows()
    metrics = compute_metrics(rows)
    OUTPUT_JSON.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
