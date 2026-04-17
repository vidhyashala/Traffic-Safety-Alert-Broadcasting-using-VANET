#!/usr/bin/env python3
"""FastAPI deployment for alert-priority inference."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "alert_priority_model.joblib"

app = FastAPI(title="VANET Alert Priority API", version="1.0.0")


class AlertFeatures(BaseModel):
    avg_speed: float = Field(..., ge=0, le=60)
    deceleration: float = Field(..., ge=0, le=12)
    distance_to_event: float = Field(..., ge=0, le=1000)
    vehicle_density: int = Field(..., ge=0, le=200)
    event_type: str = Field(..., pattern="^(sudden_brake|accident)$")
    hop_count: int = Field(..., ge=0, le=10)


@app.get("/")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "deployment_link": "http://127.0.0.1:8000/docs",
        "note": "Run uvicorn python.deploy_api:app --host 0.0.0.0 --port 8000",
    }


@app.post("/predict")
def predict(features: AlertFeatures) -> dict[str, int]:
    if not MODEL_PATH.exists():
        return {"error": "Model not found. Run python/train_alert_model.py first."}

    model = joblib.load(MODEL_PATH)
    df = pd.DataFrame([features.model_dump()])
    pred = int(model.predict(df)[0])
    return {"predicted_priority": pred}
