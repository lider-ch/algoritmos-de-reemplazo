"""Rich-based interactive menu system."""
from __future__ import annotations
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

BANNER = r"""
  ____  ____  ____  __  __ ____  __    ____  ______  ___ __  _  _
 (  _ \(  _ \(_  _)(  \/  )  _ \(  )  (_  _)(  __  )/ __)  )( \/ )
  ) __/ ) _ < _)(_  )    ( ) _ < )(__  _)(_  ) _) _(\__ \(_  _)\  /
 (__)  (____/(____)(_/\/\_)(____/(____)(____)(____)(/)(___/  (_)  \/

         Simulador de Algoritmos de Reemplazo de Páginas en Memoria
"""

ALGO_KEYS  = ["FIFO", "LRU", "OPT", "Clock", "LFU"]
ALGO_NAMES = {
    "FIFO":  "FIFO – First In, First Out",
    "LRU":   "LRU  – Least Recently Used",
    "OPT":   "OPT  – Óptimo (Bélády)",
    "Clock": "Clock – Segunda Oportunidad",
    "LFU":   "LFU  – Least Frequently Used",
}


def show_banner() -> None:
    console.print(
        Panel(
            Text(BANNER, style="bold cyan", justify="center"),
            border_style="bright_blue",
            padding=(0, 2),
        )
    )


def _algo_menu_table() -> Table:
    tbl = Table(box=box.SIMPLE, show_header=False, border_style="dim")
    tbl.add_column("Opción", style="bold yellow", justify="right", min_width=6)
    tbl.add_column("Descripción", style="white")
    for i, key in enumerate(ALGO_KEYS, 1):
        tbl.add_row(f"[{i}]", ALGO_NAMES[key])
    tbl.add_row("[6]", "[bright_magenta]Comparar TODOS los algoritmos[/bright_magenta]")
    tbl.add_row("[7]", "[bright_green]Generar reporte LaTeX + gráficas[/bright_green]")
    tbl.add_row("[8]", "[bright_cyan]Gestión de repositorio Git[/bright_cyan]")
    tbl.add_row("[9]", "[dim]Acerca del programa[/dim]")
    tbl.add_row("[0]", "[red]Salir[/red]")
    return tbl


def show_main_menu() -> str:
    console.print()
    console.print(
        Panel(
            _algo_menu_table(),
            title="[bold bright_blue]MENÚ PRINCIPAL[/bold bright_blue]",
            border_style="bright_blue",
        )
    )
    choice = Prompt.ask(
        "[bold yellow]Seleccione una opción[/bold yellow]",
        choices=["0","1","2","3","4","5","6","7","8","9"],
        show_choices=False,
    )
    return choice


def ask_parameters(default_frames: int = 3, default_len: int = 20) -> dict:
    """Prompt user for simulation parameters; return dict."""
    console.print(
        Panel(
            "[bold]Configuración de parámetros[/bold]",
            border_style="cyan",
        )
    )
    console.print("[dim]Presione Enter para usar el valor por defecto.[/dim]")

    mode = Prompt.ask(
        "¿Cómo desea ingresar la cadena de referencia?",
        choices=["manual", "aleatoria"],
        default="aleatoria",
    )

    num_frames = IntPrompt.ask(
        f"Número de marcos de página [bold](frames)[/bold]",
        default=default_frames,
    )
    while num_frames < 1:
        console.print("[red]El número de marcos debe ser al menos 1.[/red]")
        num_frames = IntPrompt.ask("Número de marcos", default=default_frames)

    if mode == "manual":
        raw = Prompt.ask(
            "Ingrese la cadena de referencia (números separados por espacios/comas)"
        )
        try:
            ref_str = [int(x.strip()) for x in raw.replace(",", " ").split() if x.strip()]
            if not ref_str:
                raise ValueError
        except ValueError:
            console.print("[red]Entrada inválida, se usará cadena aleatoria.[/red]")
            ref_str = None
    else:
        ref_str = None

    if ref_str is None:
        length = IntPrompt.ask("Longitud de la cadena aleatoria", default=default_len)
        num_pages = IntPrompt.ask("Número de páginas distintas (0…N-1)", default=10)
        seed_str = Prompt.ask("Semilla aleatoria (Enter = sin semilla)", default="")
        seed = int(seed_str) if seed_str.isdigit() else None
    else:
        length = len(ref_str)
        num_pages = max(ref_str) + 1
        seed = None

    return {
        "num_frames": num_frames,
        "ref_str":    ref_str,      # None = generate randomly
        "length":     length,
        "num_pages":  num_pages,
        "seed":       seed,
    }


def ask_git_action() -> str:
    console.print()
    opts = Table(box=box.SIMPLE, show_header=False)
    opts.add_column("", style="bold yellow", justify="right")
    opts.add_column("", style="white")
    opts.add_row("[1]", "Inicializar / verificar repositorio")
    opts.add_row("[2]", "Hacer commit de los resultados actuales")
    opts.add_row("[3]", "Ver historial de commits")
    opts.add_row("[4]", "Push a repositorio remoto (GitHub)")
    opts.add_row("[0]", "Volver al menú principal")
    console.print(Panel(opts, title="[bold bright_cyan]Git[/bold bright_cyan]", border_style="bright_cyan"))
    return Prompt.ask("Opción", choices=["0","1","2","3","4"], show_choices=False)


def about() -> None:
    text = (
        "[bold cyan]PaginaciónMemoria[/bold cyan] v1.0\n\n"
        "Simulador de algoritmos de reemplazo de páginas en memoria virtual.\n\n"
        "[bold]Algoritmos implementados:[/bold]\n"
        "  • FIFO  – First In, First Out\n"
        "  • LRU   – Least Recently Used\n"
        "  • OPT   – Óptimo (Bélády)\n"
        "  • Clock – Segunda Oportunidad\n"
        "  • LFU   – Least Frequently Used\n\n"
        "[bold]Métricas capturadas:[/bold]\n"
        "  1. Recursos utilizados (marcos, memoria)\n"
        "  2. Tiempo de ejecución (ns / µs / ms)\n"
        "  3. Llamadas al sistema (syscalls por fallo)\n"
        "  4. Interrupciones (#14 Page Fault x86)\n"
        "  5. Tabla y gráfica de reemplazo\n\n"
        "[bold]Salidas:[/bold] tabla Rich en terminal, gráficas PNG, informe LaTeX/PDF\n\n"
        "Tecnologías: Python 3.10+, Rich, Matplotlib, GitPython\n"
    )
    console.print(Panel(text, title="Acerca del programa", border_style="bright_blue"))
