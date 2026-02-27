"""Metrics display helpers for SimulationResult objects."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from algorithms.base import SimulationResult


def build_metrics_table(result: SimulationResult) -> Table:
    """Return a Rich Table with all 4 required metrics."""
    tbl = Table(
        title=f"[bold cyan]Métricas – {result.algorithm_name}[/bold cyan]",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        expand=False,
    )
    tbl.add_column("Métrica", style="bold yellow", min_width=35)
    tbl.add_column("Valor", justify="right", style="white", min_width=20)

    # ── 1. Resources ─────────────────────────────────────────────────────────
    tbl.add_row("[bold]1. RECURSOS UTILIZADOS[/bold]", "")
    tbl.add_row("   Marcos de página (frames)", str(result.num_frames))
    tbl.add_row("   Tamaño de página", "4 096 bytes (4 KB)")
    tbl.add_row(
        "   Memoria asignada (frames × página)",
        f"{result.memory_used_bytes:,} bytes  ({result.memory_used_kb:.1f} KB)",
    )
    tbl.add_row("   Páginas únicas en cadena de referencia", str(len(set(result.reference_string))))
    tbl.add_row("   Total de referencias", str(result.total_references))
    tbl.add_row("", "")

    # ── 2. Execution time ────────────────────────────────────────────────────
    tbl.add_row("[bold]2. TIEMPO DE EJECUCIÓN[/bold]", "")
    tbl.add_row("   Tiempo total (nanosegundos)", f"{result.execution_time_ns:,.0f} ns")
    tbl.add_row("   Tiempo total (microsegundos)", f"{result.execution_time_us:,.3f} µs")
    tbl.add_row("   Tiempo total (milisegundos)", f"{result.execution_time_ms:,.6f} ms")
    tbl.add_row("", "")

    # ── 3. System calls ──────────────────────────────────────────────────────
    tbl.add_row("[bold]3. LLAMADAS AL SISTEMA (syscalls)[/bold]", "")
    tbl.add_row(
        "   handle_page_fault() invocaciones",
        f"[red]{result.system_calls}[/red]",
    )
    tbl.add_row(
        "   Tasa de llamadas / referencia",
        f"{result.system_calls / max(result.total_references, 1):.4f}",
    )
    tbl.add_row("", "")

    # ── 4. Interrupts ────────────────────────────────────────────────────────
    tbl.add_row("[bold]4. INTERRUPCIONES UTILIZADAS[/bold]", "")
    tbl.add_row(
        "   Interrupciones de fallo de página (#14 x86)",
        f"[red]{result.interrupts}[/red]",
    )
    tbl.add_row(
        "   Aciertos (sin interrupción)",
        f"[green]{result.page_hits}[/green]",
    )
    tbl.add_row("", "")

    # ── Summary ───────────────────────────────────────────────────────────────
    tbl.add_row("[bold]RESUMEN[/bold]", "")
    tbl.add_row("   Fallos de página", f"[red bold]{result.page_faults}[/red bold]")
    tbl.add_row("   Aciertos de página", f"[green bold]{result.page_hits}[/green bold]")
    tbl.add_row(
        "   Tasa de aciertos (hit ratio)",
        f"[green]{result.hit_ratio:.2%}[/green]",
    )
    tbl.add_row(
        "   Tasa de fallos (fault ratio)",
        f"[red]{result.fault_ratio:.2%}[/red]",
    )
    return tbl


def display_metrics(result: SimulationResult, console: Console) -> None:
    console.print()
    console.print(build_metrics_table(result))
    console.print()


def build_comparison_table(results: list[SimulationResult]) -> Table:
    """Side-by-side comparison table for multiple algorithm results."""
    tbl = Table(
        title="[bold cyan]Comparación de Algoritmos[/bold cyan]",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        expand=True,
    )
    tbl.add_column("Algoritmo", style="bold yellow", min_width=30)
    tbl.add_column("Fallos", justify="right", style="red")
    tbl.add_column("Aciertos", justify="right", style="green")
    tbl.add_column("Hit Ratio", justify="right")
    tbl.add_column("Syscalls", justify="right")
    tbl.add_column("Interrupciones", justify="right")
    tbl.add_column("Tiempo (µs)", justify="right")
    tbl.add_column("Mem. (KB)", justify="right")

    best_faults = min(r.page_faults for r in results)

    for r in results:
        fault_str = (
            f"[bold green]{r.page_faults} <MEJOR>[/bold green]"
            if r.page_faults == best_faults
            else str(r.page_faults)
        )
        tbl.add_row(
            r.algorithm_name,
            fault_str,
            str(r.page_hits),
            f"{r.hit_ratio:.2%}",
            str(r.system_calls),
            str(r.interrupts),
            f"{r.execution_time_us:.3f}",
            f"{r.memory_used_kb:.1f}",
        )
    return tbl
