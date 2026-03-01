from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def build_histogram_by_dates(
    out_path: Path, 
    by_date: list[dict], 
    title: str
):
    dates = [x["date"].isoformat() for x in by_date]
    present = [x["present_count"] for x in by_date]

    plt.figure(figsize=(10, 5))
    plt.bar(dates, present)
    plt.xticks(rotation=45, ha="right")
    plt.title(title)
    plt.xlabel("Дата")
    plt.ylabel("Кол-во присутствующих")
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path