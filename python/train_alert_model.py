#!/usr/bin/env python3
"""Train a simple alert-priority model for VANET safety messages."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_CSV = PROJECT_ROOT / "data" / "alert_training_data.csv"
VALID_CSV = PROJECT_ROOT / "data" / "alert_validation_data.csv"
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
MODEL_PATH = MODELS_DIR / "alert_priority_model.joblib"
METRICS_PATH = RESULTS_DIR / "ml_training_metrics.json"


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(TRAIN_CSV)
    valid_df = pd.read_csv(VALID_CSV)

    features = [
        "avg_speed",
        "deceleration",
        "distance_to_event",
        "vehicle_density",
        "event_type",
        "hop_count",
    ]
    target = "label_priority"

    x_train = train_df[features]
    y_train = train_df[target]
    x_valid = valid_df[features]
    y_valid = valid_df[target]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                ["event_type"],
            ),
        ],
        remainder="passthrough",
    )

    model = RandomForestClassifier(
        n_estimators=180,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )

    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )

    pipeline.fit(x_train, y_train)
    preds = pipeline.predict(x_valid)
    acc = accuracy_score(y_valid, preds)

    report = classification_report(y_valid, preds, output_dict=True)
    metrics = {
        "validation_accuracy": round(float(acc), 4),
        "samples_train": int(len(train_df)),
        "samples_validation": int(len(valid_df)),
        "classification_report": report,
    }

    joblib.dump(pipeline, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Model saved to: {MODEL_PATH}")
    print(f"Training metrics saved to: {METRICS_PATH}")
    print(f"Validation accuracy: {acc:.4f}")


if __name__ == "__main__":
    main()
