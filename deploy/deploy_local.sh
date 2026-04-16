#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -r python/requirements.txt
python3 python/train_alert_model.py
uvicorn python.deploy_api:app --host 0.0.0.0 --port 8000
