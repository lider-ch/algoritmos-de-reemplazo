"""Matplotlib graph generators for simulation results."""
from __future__ import annotations
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")            # non-interactive backend (safe on all systems)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba
from algorithms.base import SimulationResult

# ── Colour palette ────────────────────────────────────────────────────────────
ALGO_COLORS = [
    "#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6"
]


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


# ── 1. Page-fault heatmap / replacement grid ──────────────────────────────────
def plot_replacement_grid(result: SimulationResult, save_path: str) -> str:
    """
    Visual heatmap of which page sits in each frame at every reference step.
    Faults are marked with a red border.
    """
    _ensure_dir(save_path)
    steps = result.steps
    n_steps = len(steps)
    n_frames = result.num_frames

    # Build 2-D grid: grid[frame][step] = page number (NaN = empty)
    grid = np.full((n_frames, n_steps), np.nan)
    for col, step in enumerate(steps):
        for row, page in enumerate(step.frames):
            grid[row, col] = page

    # Map page numbers to colours
    all_pages = sorted({p for step in steps for p in step.frames})
    cmap = plt.cm.get_cmap("tab20", max(len(all_pages), 1))
    page_to_idx = {p: i for i, p in enumerate(all_pages)}

    fig, ax = plt.subplots(figsize=(max(14, n_steps * 0.45), n_frames * 0.9 + 2))
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#1E1E2E")

    cell_w, cell_h = 1.0, 1.0
    for col in range(n_steps):
        step = steps[col]
        for row in range(n_frames):
            x, y = col, (n_frames - 1 - row)
            if row < len(step.frames):
                page = step.frames[row]
                color = cmap(page_to_idx[page])
                rect = plt.Rectangle((x, y), cell_w, cell_h, color=color, alpha=0.85)
                ax.add_patch(rect)
                ax.text(
                    x + 0.5, y + 0.5, str(page),
                    ha="center", va="center", fontsize=8, fontweight="bold",
                    color="white",
                )
            else:
                rect = plt.Rectangle((x, y), cell_w, cell_h, color="#333355", alpha=0.5)
                ax.add_patch(rect)

        # Red border on fault columns
        if step.is_fault:
            for row in range(n_frames):
                yy = n_frames - 1 - row
                border = plt.Rectangle(
                    (col, yy), cell_w, cell_h,
                    fill=False, edgecolor="#FF4444", linewidth=2.0,
                )
                ax.add_patch(border)

    # Reference string above the grid
    for col, step in enumerate(steps):
        marker = "★" if step.is_fault else "·"
        color  = "#FF6666" if step.is_fault else "#66FF99"
        ax.text(
            col + 0.5, n_frames + 0.3, f"{step.reference}\n{marker}",
            ha="center", va="bottom", fontsize=7, color=color,
        )

    ax.set_xlim(0, n_steps)
    ax.set_ylim(0, n_frames + 0.8)
    ax.set_yticks([n_frames - 1 - i + 0.5 for i in range(n_frames)])
    ax.set_yticklabels([f"M{i}" for i in range(n_frames)], color="white")
    ax.set_xticks([])
    ax.set_title(
        f"Tabla de Reemplazo – {result.algorithm_name}\n"
        f"Fallos: {result.page_faults}  |  Aciertos: {result.page_hits}  |  "
        f"Hit-ratio: {result.hit_ratio:.2%}",
        color="white", fontsize=11, pad=10,
    )
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555577")

    # Legend
    patches = [
        mpatches.Patch(color=cmap(page_to_idx[p]), label=f"Pág {p}")
        for p in all_pages
    ]
    fault_patch = mpatches.Patch(facecolor="none", edgecolor="#FF4444", linewidth=2, label="Fallo (borde rojo)")
    ax.legend(
        handles=patches + [fault_patch],
        loc="upper right", fontsize=7,
        facecolor="#2A2A3E", labelcolor="white",
        ncol=max(1, len(all_pages) // 4 + 1),
    )

    fig.tight_layout()
    fig.savefig(save_path, dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path


# ── 2. Fault-over-time line chart ────────────────────────────────────────────
def plot_faults_over_time(result: SimulationResult, save_path: str) -> str:
    """Cumulative page faults as references are processed."""
    _ensure_dir(save_path)
    cumulative = []
    count = 0
    for step in result.steps:
        if step.is_fault:
            count += 1
        cumulative.append(count)

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#1E1E2E")
    ax.plot(cumulative, color="#E74C3C", linewidth=2, label="Fallos acumulados")
    ax.fill_between(range(len(cumulative)), cumulative, alpha=0.2, color="#E74C3C")
    ax.set_xlabel("Referencia #", color="white")
    ax.set_ylabel("Fallos acumulados", color="white")
    ax.set_title(f"Evolución de Fallos – {result.algorithm_name}", color="white")
    ax.tick_params(colors="white")
    ax.legend(facecolor="#2A2A3E", labelcolor="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555577")
    fig.tight_layout()
    fig.savefig(save_path, dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path


# ── 3. Algorithm comparison bar chart ────────────────────────────────────────
def plot_comparison(results: list[SimulationResult], save_path: str) -> str:
    """Grouped bar chart: faults, hits, syscalls, interrupts per algorithm."""
    _ensure_dir(save_path)
    names = [r.algorithm_name.split("(")[0].strip() for r in results]
    faults = [r.page_faults for r in results]
    hits   = [r.page_hits   for r in results]
    syscalls = [r.system_calls for r in results]

    x = np.arange(len(names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(13, 5))
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#1E1E2E")

    bars1 = ax.bar(x - width, faults,   width, label="Fallos",    color="#E74C3C", alpha=0.9)
    bars2 = ax.bar(x,         hits,     width, label="Aciertos",  color="#2ECC71", alpha=0.9)
    bars3 = ax.bar(x + width, syscalls, width, label="Syscalls",  color="#3498DB", alpha=0.9)

    for bars in (bars1, bars2, bars3):
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 0.5,
                str(int(h)), ha="center", va="bottom", fontsize=8, color="white",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(names, color="white", fontsize=9)
    ax.set_ylabel("Cantidad", color="white")
    ax.set_title("Comparación de Algoritmos de Reemplazo de Páginas", color="white", fontsize=12)
    ax.tick_params(colors="white")
    ax.legend(facecolor="#2A2A3E", labelcolor="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555577")

    fig.tight_layout()
    fig.savefig(save_path, dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path


# ── 4. Hit-ratio pie chart ────────────────────────────────────────────────────
def plot_hit_ratio_pie(result: SimulationResult, save_path: str) -> str:
    _ensure_dir(save_path)
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#1E1E2E")
    sizes  = [result.page_hits, result.page_faults]
    labels = [f"Aciertos\n{result.page_hits}", f"Fallos\n{result.page_faults}"]
    colors = ["#2ECC71", "#E74C3C"]
    ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
           textprops={"color": "white"}, startangle=140)
    ax.set_title(f"{result.algorithm_name}\nHit vs Fault", color="white")
    fig.tight_layout()
    fig.savefig(save_path, dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path
