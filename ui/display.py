"""Rich-based display functions: replacement table and step-by-step view."""
from __future__ import annotations
import math
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from algorithms.base import SimulationResult, StepRecord

MAX_COLS = 30   # max references shown in the table before splitting


def _page_color(page: int) -> str:
    """Map a page number to a stable terminal color."""
    colors = [
        "bright_red", "bright_green", "bright_yellow", "bright_blue",
        "bright_magenta", "bright_cyan", "orange3", "spring_green3",
        "deep_sky_blue1", "hot_pink", "chartreuse1", "gold1",
    ]
    return colors[page % len(colors)]


def build_replacement_table(
    result: SimulationResult, chunk_start: int = 0, chunk_size: int = MAX_COLS
) -> Table:
    """
    Build a Rich table showing the page replacement process.

    Rows  = frames (frame 0 … frame N-1)
    Cols  = each page reference in the chunk
    Extra = fault/hit indicator row
    """
    steps = result.steps[chunk_start : chunk_start + chunk_size]

    tbl = Table(
        title=(
            f"[bold cyan]Tabla de Reemplazo – {result.algorithm_name}[/bold cyan]\n"
            f"[dim]Referencias {chunk_start + 1}–{chunk_start + len(steps)} "
            f"de {result.total_references}[/dim]"
        ),
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold white on dark_blue",
        border_style="bright_blue",
        expand=False,
        padding=(0, 1),
    )

    # Header columns: "Marco" label + one column per reference step
    tbl.add_column("Marco", style="bold yellow", justify="center", min_width=6)
    for i, step in enumerate(steps):
        fault_mark = "[red]F[/red]" if step.is_fault else "[green]H[/green]"
        header_text = f"[bold]{step.reference}[/bold]\n{fault_mark}"
        tbl.add_column(header_text, justify="center", min_width=4)

    # Frame rows
    for frame_idx in range(result.num_frames):
        row_cells: list[str] = [f"M{frame_idx}"]
        for step in steps:
            if frame_idx < len(step.frames):
                p = step.frames[frame_idx]
                color = _page_color(p)
                cell = f"[{color}]{p}[/{color}]"
                # Highlight loaded page
                if step.loaded == p and step.is_fault:
                    cell = f"[bold underline {color}]{p}[/bold underline {color}]"
            else:
                cell = "[dim]–[/dim]"
            row_cells.append(cell)
        tbl.add_row(*row_cells)

    # Reference-bit row (Clock only)
    if any(step.reference_bits for step in steps):
        ref_row: list[str] = ["[italic]Ref-bit[/italic]"]
        for step in steps:
            if step.reference_bits:
                bits = " ".join(str(b) for b in step.reference_bits)
                ref_row.append(f"[dim]{bits}[/dim]")
            else:
                ref_row.append("")
        tbl.add_row(*ref_row)

    # Fault/Hit indicator row
    fh_row: list[str] = ["[bold]F/H[/bold]"]
    for step in steps:
        if step.is_fault:
            victim_label = f"\n[dim]→{step.victim}[/dim]" if step.victim is not None else ""
            fh_row.append(f"[bold red]FALLO{victim_label}[/bold red]")
        else:
            fh_row.append("[bold green]HIT[/bold green]")
    tbl.add_row(*fh_row)

    return tbl


def display_replacement_table(result: SimulationResult, console: Console) -> None:
    """Display the full replacement table, chunked if necessary."""
    total = result.total_references
    chunks = math.ceil(total / MAX_COLS)

    for chunk in range(chunks):
        start = chunk * MAX_COLS
        tbl = build_replacement_table(result, chunk_start=start, chunk_size=MAX_COLS)
        console.print()
        console.print(tbl)

    console.print()
    legend = (
        "[bold red]F[/bold red] = Fallo de página  "
        "[bold green]H[/bold green] = Acierto  "
        "[bold underline]X[/bold underline] = página cargada  "
        "[dim]→V[/dim] = víctima desalojada"
    )
    console.print(Panel(legend, title="Leyenda", border_style="dim", expand=False))
