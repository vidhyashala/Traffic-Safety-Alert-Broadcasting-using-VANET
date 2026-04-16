#!/usr/bin/env python3
"""Plot key metrics from the generated results JSON file."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
METRICS_JSON = RESULTS_DIR / "metrics.json"


def main() -> None:
    data = json.loads(METRICS_JSON.read_text(encoding="utf-8"))

    keys = [
        "packet_delivery_ratio",
        "avg_end_to_end_delay_s",
        "throughput_packets_per_s",
        "dissemination_range_hops",
    ]
    values = [data[k] for k in keys]

    plt.figure(figsize=(9, 4))
    plt.bar(keys, values, color=["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"])
    plt.title("Traffic Safety Alert Broadcasting Metrics")
    plt.ylabel("Value")
    plt.xticks(rotation=20)
    plt.tight_layout()
    output = RESULTS_DIR / "metrics_plot.png"
    plt.savefig(output, dpi=150)
    print(f"Saved plot to {output}")


if __name__ == "__main__":
    main()
