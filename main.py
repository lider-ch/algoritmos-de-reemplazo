#!/usr/bin/env python3
"""
PaginaciónMemoria – Simulador de Algoritmos de Reemplazo de Páginas
====================================================================
Punto de entrada principal.  Ejecutar con:

    python main.py

Requiere:  pip install rich matplotlib numpy gitpython
"""

import os
import sys

# ── Ensure project root is on the Python path ────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# ── Auto-install dependencies if missing ─────────────────────────────────────
def _check_deps():
    missing = []
    for pkg in ("rich", "matplotlib", "numpy", "git"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg if pkg != "git" else "gitpython")
    if missing:
        print(f"Instalando dependencias faltantes: {missing}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)

_check_deps()

# ── Imports after dependency check ───────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import box

from algorithms import ALGORITHMS, ALGORITHMS as _ALGOS
from core.simulator import run_single, run_all, generate_reference_string
from core.metrics import display_metrics, build_comparison_table
from ui.menu import (
    show_banner, show_main_menu, ask_parameters, ask_git_action, about,
    ALGO_KEYS, console,
)
from ui.display import display_replacement_table
from reports.graph import (
    plot_replacement_grid, plot_faults_over_time,
    plot_comparison, plot_hit_ratio_pie,
)
from reports.latex_builder import generate_report, compile_latex
from git_integration.repo_manager import (
    init_repo, commit_results, show_log, push_to_remote,
)

GRAPH_DIR  = os.path.join(PROJECT_ROOT, "output", "graphs")
REPORT_DIR = os.path.join(PROJECT_ROOT, "output", "reports")
os.makedirs(GRAPH_DIR,  exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# ── Global simulation state ───────────────────────────────────────────────────
_params: dict | None = None          # current parameters
_last_results: list  = []            # last SimulationResult list


def _get_params() -> dict:
    """Return cached parameters or ask the user."""
    global _params
    if _params is None:
        _params = ask_parameters()
    return _params


def _build_ref_string(p: dict) -> list[int]:
    if p["ref_str"] is not None:
        return p["ref_str"]
    return generate_reference_string(p["num_pages"], p["length"], p["seed"])


def _run_and_display(algo_key: str, ref_str: list[int], num_frames: int) -> object:
    """Run a single algorithm, show table + metrics, return result."""
    console.rule(f"[bold cyan]Ejecutando {ALGORITHMS[algo_key].name}[/bold cyan]")
    result = run_single(algo_key, ref_str, num_frames)

    # 5. Replacement table
    display_replacement_table(result, console)

    # 1-4. Metrics
    display_metrics(result, console)

    # Offer to show graph
    if Confirm.ask("[dim]¿Generar gráfica PNG?[/dim]", default=True):
        short = algo_key
        grid_p = os.path.join(GRAPH_DIR, f"grid_{short}.png")
        pie_p  = os.path.join(GRAPH_DIR, f"pie_{short}.png")
        time_p = os.path.join(GRAPH_DIR, f"time_{short}.png")
        plot_replacement_grid(result, grid_p)
        plot_hit_ratio_pie(result, pie_p)
        plot_faults_over_time(result, time_p)
        console.print(f"[green]Gráficas guardadas en:[/green] {GRAPH_DIR}")

    return result


def _action_single_algo(algo_key: str) -> None:
    global _last_results
    p = _get_params()
    ref_str = _build_ref_string(p)
    result  = _run_and_display(algo_key, ref_str, p["num_frames"])
    _last_results = [result]

    if Confirm.ask("[dim]¿Cambiar parámetros para la próxima ejecución?[/dim]", default=False):
        global _params
        _params = None


def _action_compare_all() -> None:
    global _last_results
    p = _get_params()
    ref_str = _build_ref_string(p)

    console.rule("[bold cyan]Comparación de TODOS los Algoritmos[/bold cyan]")
    results = []
    for key in ALGO_KEYS:
        console.print(f"[dim]Ejecutando {key}…[/dim]")
        results.append(run_single(key, ref_str, p["num_frames"]))

    _last_results = results

    # Show individual tables
    for r in results:
        display_replacement_table(r, console)
        display_metrics(r, console)

    # Comparison summary
    console.print()
    console.print(build_comparison_table(results))

    # Generate comparison graph
    cmp_path = os.path.join(GRAPH_DIR, "comparison.png")
    plot_comparison(results, cmp_path)
    console.print(f"[green]Gráfica de comparación:[/green] {cmp_path}")

    # Individual graphs
    for r in results:
        short = r.algorithm_name.split("(")[0].split("–")[0].strip()
        plot_replacement_grid(r, os.path.join(GRAPH_DIR, f"grid_{short}.png"))
        plot_hit_ratio_pie(r, os.path.join(GRAPH_DIR, f"pie_{short}.png"))
        plot_faults_over_time(r, os.path.join(GRAPH_DIR, f"time_{short}.png"))
    console.print(f"[green]Todas las gráficas guardadas en:[/green] {GRAPH_DIR}")


def _action_generate_report() -> None:
    if not _last_results:
        console.print(
            "[yellow]Primero ejecute al menos un algoritmo "
            "(opciones 1-6) para generar el reporte.[/yellow]"
        )
        return

    results = _last_results
    # If only one result, run all for a complete report
    if len(results) == 1:
        if Confirm.ask("Solo hay un resultado. ¿Ejecutar todos los algoritmos para el reporte?", default=True):
            p = _get_params()
            ref_str = _build_ref_string(p)
            results = run_all(ref_str, p["num_frames"])
            # Regenerate all graphs
            cmp_path = os.path.join(GRAPH_DIR, "comparison.png")
            plot_comparison(results, cmp_path)
            for r in results:
                short = r.algorithm_name.split("(")[0].split("–")[0].strip()
                plot_replacement_grid(r, os.path.join(GRAPH_DIR, f"grid_{short}.png"))
                plot_hit_ratio_pie(r, os.path.join(GRAPH_DIR, f"pie_{short}.png"))
                plot_faults_over_time(r, os.path.join(GRAPH_DIR, f"time_{short}.png"))

    tex_path = generate_report(results, REPORT_DIR, GRAPH_DIR)
    console.print(f"[green]Informe LaTeX generado:[/green] {tex_path}")

    console.print("[dim]Intentando compilar con pdflatex…[/dim]")
    if compile_latex(tex_path):
        pdf_path = tex_path.replace(".tex", ".pdf")
        console.print(f"[bold green]PDF generado:[/bold green] {pdf_path}")
    else:
        console.print(
            "[yellow]pdflatex no encontrado o error de compilación.[/yellow]\n"
            f"Puede compilar manualmente: [bold]pdflatex {tex_path}[/bold]\n"
            "O use Overleaf: https://www.overleaf.com"
        )


def _action_git() -> None:
    while True:
        choice = ask_git_action()
        if choice == "0":
            break
        elif choice == "1":
            msg = init_repo(PROJECT_ROOT)
            console.print(f"[cyan]{msg}[/cyan]")
        elif choice == "2":
            commit_msg = Prompt.ask("Mensaje del commit", default="results: nueva simulación")
            msg = commit_results(PROJECT_ROOT, commit_msg)
            console.print(f"[green]{msg}[/green]")
        elif choice == "3":
            log = show_log(PROJECT_ROOT)
            if not log:
                console.print("[yellow]Sin commits aún.[/yellow]")
            else:
                tbl = Table(box=box.SIMPLE, border_style="dim")
                tbl.add_column("Hash",    style="yellow")
                tbl.add_column("Fecha",   style="dim")
                tbl.add_column("Autor",   style="cyan")
                tbl.add_column("Mensaje", style="white")
                for c in log:
                    tbl.add_row(c["hash"], c["date"], c["author"], c["message"])
                console.print(tbl)
        elif choice == "4":
            url = Prompt.ask("URL del repositorio remoto (ej: https://github.com/usuario/repo.git)")
            branch = Prompt.ask("Rama", default="main")
            msg = push_to_remote(PROJECT_ROOT, url, branch)
            console.print(f"[cyan]{msg}[/cyan]")
        console.print()


def main() -> None:
    show_banner()
    console.print(
        Panel(
            "[dim]Use el menú para seleccionar algoritmo, comparar todos,\n"
            "generar informe LaTeX o gestionar el repositorio Git.[/dim]",
            border_style="dim",
        )
    )

    while True:
        choice = show_main_menu()

        if choice == "0":
            console.print("\n[bold cyan]¡Hasta luego![/bold cyan]\n")
            sys.exit(0)

        elif choice in ("1","2","3","4","5"):
            key_map = {"1":"FIFO","2":"LRU","3":"OPT","4":"Clock","5":"LFU"}
            _action_single_algo(key_map[choice])

        elif choice == "6":
            _action_compare_all()

        elif choice == "7":
            _action_generate_report()

        elif choice == "8":
            _action_git()

        elif choice == "9":
            about()

        # Pause before returning to menu
        console.print()
        Prompt.ask("[dim]Presione Enter para continuar[/dim]", default="")


if __name__ == "__main__":
    main()
