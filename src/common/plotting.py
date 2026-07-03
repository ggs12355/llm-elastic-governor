from __future__ import annotations

from pathlib import Path


def plot_series(series: dict[str, list[float]], output: str | Path, title: str) -> None:
    import matplotlib.pyplot as plt

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    for label, values in series.items():
        ax.plot(range(len(values)), values, label=label)
    ax.set_title(title)
    ax.set_xlabel("step")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)

