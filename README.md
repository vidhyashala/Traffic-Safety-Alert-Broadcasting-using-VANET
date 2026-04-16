# Traffic Safety Alert Broadcasting using VANET

This final-year project demonstrates a complete VANET safety-alert pipeline using **SUMO + OMNeT++/Veins + Python (TraCI)**, and now includes a small **ML training workflow** with CSV datasets and a deployable API.

## 1) System Architecture

### Interaction between SUMO, OMNeT++, Veins, Python (TraCI)
- **SUMO**: vehicle mobility (position, speed, lane, routes).
- **Python + TraCI**: traffic-event detection, alert creation, propagation logic, vehicle control, logging.
- **OMNeT++ + Veins**: IEEE 802.11p communications and multi-hop forwarding behavior.
- **ML model (Python)**: predicts alert priority from vehicle/event features.

### Data flow
`vehicle -> event detected -> alert generated -> nearby broadcast -> receive/rebroadcast -> action (slowdown/reroute)`

## 2) Project Structure

```text
Traffic-Safety-Alert-Broadcasting-using-VANET/
├── sumo/
│   ├── traffic_safety.nod.xml
│   ├── traffic_safety.edg.xml
│   ├── traffic_safety.net.xml
│   ├── traffic_safety.rou.xml
│   ├── traffic_safety.sumocfg
│   └── traffic_safety.launchd.xml
├── omnet/
│   ├── simulations/
│   │   ├── TrafficSafetyScenario.ned
│   │   └── omnetpp.ini
│   └── src/
│       ├── AlertMessage.msg
│       ├── TraCIDemo11pSafety.h
│       └── TraCIDemo11pSafety.cc
├── python/
│   ├── vanet_alert_sim.py
│   ├── metrics.py
│   ├── plot_results.py
│   ├── train_alert_model.py
│   ├── deploy_api.py
│   └── requirements.txt
├── data/
│   ├── alert_training_data.csv
│   └── alert_validation_data.csv
├── models/
├── results/
└── docs/
    └── beginner_guide.md
```

## 3) SUMO Implementation
- Road network and flows are defined in XML files under `sumo/`.
- `.net.xml`, `.rou.xml`, `.sumocfg` are included and ready.
- Realistic parameters: mixed flows, speed limits, 0.1s simulation step, 500s scenario duration.

## 4) Python (TraCI) Implementation
`python/vanet_alert_sim.py` includes:
- TraCI connection to SUMO.
- Event detection:
  - sudden braking (acceleration threshold),
  - injected accident event.
- Alert generation and broadcast to nearby vehicles.
- Vehicle reactions: slowdown and optional reroute.
- ML-assisted priority prediction (if trained model exists).

## 5) OMNeT++ + Veins Implementation
- `TrafficSafetyScenario.ned`: simulation topology.
- `omnetpp.ini`: Veins + SUMO integration and IEEE 802.11p parameters.
- `TraCIDemo11pSafety.{h,cc}`: message receive, duplicate suppression, TTL forwarding.

## 6) Alert Propagation Logic
- Source generates alert with `TTL` and `priority`.
- Receivers rebroadcast with random delay.
- Broadcast storm mitigation:
  - TTL decrement,
  - probabilistic forwarding,
  - duplicate filtering.

## 7) Simulation Execution

### A) Install dependencies
```bash
sudo apt update
sudo apt install -y sumo sumo-tools python3-pip python3-venv
```

### B) Python environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r python/requirements.txt
export SUMO_HOME=/usr/share/sumo
export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"
```

### C) Train ML model (new)
```bash
python3 python/train_alert_model.py
```

### D) Run TraCI simulation + metrics
```bash
python3 python/vanet_alert_sim.py
python3 python/metrics.py
python3 python/plot_results.py
```

### E) Run deployment API (new)
```bash
uvicorn python.deploy_api:app --host 0.0.0.0 --port 8000
```
- Local deployment link: **http://127.0.0.1:8000/docs**

## 8) Performance Metrics Implementation
`python/metrics.py` computes:
- Packet Delivery Ratio (PDR)
- End-to-End Delay
- Throughput
- Message dissemination range (max hop)

## 9) Visualization
- SUMO GUI for movement visualization.
- CSV packet logs in `results/alert_packet_log.csv`.
- Graph in `results/metrics_plot.png`.

## 10) Output Artifacts
- `results/alert_packet_log.csv`
- `results/simulation_summary.json`
- `results/metrics.json`
- `results/metrics_plot.png`
- `results/ml_training_metrics.json`

## 11) Bonus Improvement
- **Distance + priority-based filtering** in alert propagation.
- **ML-priority prediction** improves alert criticality assignment.

## 12) Dataset and Training Details (new)
- CSV datasets:
  - `data/alert_training_data.csv`
  - `data/alert_validation_data.csv`
- Training script:
  - `python/train_alert_model.py`
- Model output:
  - `models/alert_priority_model.joblib`

## 13) Deployment Link (new)
- API provides prediction endpoint at `/predict`.
- Local deployment link: **http://127.0.0.1:8000/docs**
- Example production link format (after cloud deployment):
  - `https://<your-app-name>.onrender.com/docs`

## OMNeT++ and Veins Installation (reference)
1. Install OMNeT++ 6.x.
2. Clone and build compatible Veins release.
3. Import `omnet/` into OMNeT++ IDE and run `omnet/simulations/omnetpp.ini`.

## Suitable for final-year students
- Modular folders, commented scripts, clear execution path, and measurable outcomes.
