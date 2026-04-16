# Beginner Guide: Traffic Safety Alert Broadcasting using VANET

## Quick start checklist
1. Install SUMO + Python dependencies.
2. Train model: `python3 python/train_alert_model.py`.
3. Run simulation: `python3 python/vanet_alert_sim.py`.
4. Compute metrics: `python3 python/metrics.py`.
5. (Optional) Deploy API: `uvicorn python.deploy_api:app --host 0.0.0.0 --port 8000`.

## Dataset files
- `data/alert_training_data.csv`
- `data/alert_validation_data.csv`

## Training output
- Model: `models/alert_priority_model.joblib`
- Metrics: `results/ml_training_metrics.json`

## Deployment link
- Local: `http://127.0.0.1:8000/docs`

## Common issues
- `ImportError: traci`: set `SUMO_HOME` and `PYTHONPATH`.
- API says model missing: run training script first.
