"""Generate a LaTeX report from simulation results and captured graphs."""
from __future__ import annotations
import os
import subprocess
import datetime
from algorithms.base import SimulationResult


def _escape(text: str) -> str:
    """Escape special LaTeX characters."""
    replacements = {
        "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}", "\\": r"\textbackslash{}",
        "★": r"$\star$",
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return text


def _metrics_table(result: SimulationResult) -> str:
    name = _escape(result.algorithm_name)
    ref_str = ", ".join(str(p) for p in result.reference_string[:30])
    if len(result.reference_string) > 30:
        ref_str += r", \ldots"

    return rf"""
\subsection*{{{name}}}
\begin{{center}}
\begin{{tabular}}{{|l|r|}}
\hline
\textbf{{Métrica}} & \textbf{{Valor}} \\
\hline
Marcos de página & {result.num_frames} \\
Memoria asignada & {result.memory_used_bytes:,} bytes ({result.memory_used_kb:.1f} KB) \\
Total de referencias & {result.total_references} \\
\hline
Tiempo de ejecución (ns) & {result.execution_time_ns:,.0f} ns \\
Tiempo de ejecución (\textmu s) & {result.execution_time_us:.3f} \textmu s \\
\hline
Llamadas al sistema (syscalls) & {result.system_calls} \\
Interrupciones (\#PF) & {result.interrupts} \\
\hline
Fallos de página & \textbf{{{result.page_faults}}} \\
Aciertos de página & \textbf{{{result.page_hits}}} \\
Hit-ratio & {result.hit_ratio:.2\%} \\
Fault-ratio & {result.fault_ratio:.2\%} \\
\hline
\end{{tabular}}
\end{{center}}
"""


def _replacement_table_latex(result: SimulationResult, max_steps: int = 25) -> str:
    """LaTeX tabular for the first max_steps of the replacement process."""
    steps = result.steps[:max_steps]
    n_frames = result.num_frames

    # Column spec: l + one c per step
    col_spec = "l|" + "c" * len(steps)

    header_refs = " & ".join(str(s.reference) for s in steps)

    rows = []
    for fi in range(n_frames):
        cells = []
        for step in steps:
            if fi < len(step.frames):
                cells.append(str(step.frames[fi]))
            else:
                cells.append("--")
        rows.append(f"Marco {fi} & " + " & ".join(cells) + r" \\")

    fault_row = " & ".join(
        r"\textbf{F}" if s.is_fault else "H" for s in steps
    )

    rows_str = "\n".join(rows)
    note = ""
    if result.total_references > max_steps:
        note = (
            rf"\\ \noindent\small\textit{{Nota: sólo se muestran las primeras "
            rf"{max_steps} de {result.total_references} referencias.}}"
        )

    return rf"""
\begin{{center}}
\scriptsize
\begin{{tabular}}{{{col_spec}}}
\hline
\textbf{{Ref}} & {header_refs} \\
\hline
{rows_str}
\hline
\textbf{{F/H}} & {fault_row} \\
\hline
\end{{tabular}}
\end{{center}}
{note}
"""


def _include_graph(path: str, caption: str, label: str) -> str:
    if not os.path.exists(path):
        return ""
    # Use forward slashes and relative path from report dir
    rel = os.path.basename(path)
    graph_dir = "../output/graphs/"
    return rf"""
\begin{{figure}}[H]
  \centering
  \includegraphics[width=0.95\textwidth]{{{graph_dir}{rel}}}
  \caption{{{_escape(caption)}}}
  \label{{fig:{label}}}
\end{{figure}}
"""


def generate_report(
    results: list[SimulationResult],
    output_dir: str,
    graph_dir: str,
) -> str:
    """
    Generate a .tex file from simulation results.
    Returns the path to the .tex file.
    """
    os.makedirs(output_dir, exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    ref_display = ", ".join(str(p) for p in results[0].reference_string[:40])
    if len(results[0].reference_string) > 40:
        ref_display += r", \ldots"

    # ── Algorithm descriptions ────────────────────────────────────────────────
    algo_descriptions = {
        "FIFO": (
            "FIFO (First In, First Out) reemplaza la página más antigua en memoria "
            "según el orden de llegada. Es el algoritmo más simple pero puede sufrir "
            "la Anomalía de Bélády (más marcos → más fallos)."
        ),
        "LRU": (
            "LRU (Least Recently Used) reemplaza la página que no ha sido utilizada "
            "por más tiempo. Aproxima el comportamiento óptimo sin conocimiento futuro."
        ),
        "OPT": (
            "OPT (Óptimo / Bélády) reemplaza la página que no será utilizada por el "
            "mayor tiempo en el futuro. Produce el mínimo teórico de fallos; sirve "
            "como referencia comparativa."
        ),
        "Clock": (
            "Clock (Segunda Oportunidad) utiliza un bit de referencia por marco. "
            "Cuando un marco debe ser reemplazado, si su bit es 1 se pone a 0 y se "
            "avanza (segunda oportunidad); si es 0 se reemplaza."
        ),
        "LFU": (
            "LFU (Least Frequently Used) reemplaza la página con menor frecuencia "
            "de acceso. Favorece páginas muy referenciadas; desventaja: páginas muy "
            "usadas en el pasado pueden persistir aunque ya no se necesiten."
        ),
    }

    # ── Individual sections ───────────────────────────────────────────────────
    sections = []
    for r in results:
        short_key = r.algorithm_name.split("(")[0].split("–")[0].strip()
        desc = ""
        for key, val in algo_descriptions.items():
            if key.lower() in short_key.lower():
                desc = val
                break

        grid_path = os.path.join(graph_dir, f"grid_{short_key}.png")
        pie_path  = os.path.join(graph_dir, f"pie_{short_key}.png")
        time_path = os.path.join(graph_dir, f"time_{short_key}.png")

        section = rf"""
\newpage
\section{{{_escape(r.algorithm_name)}}}

{_escape(desc)}

\subsection*{{Métricas}}
{_metrics_table(r)}

\subsection*{{Tabla de Reemplazo (primeros 25 pasos)}}
{_replacement_table_latex(r, max_steps=25)}

\subsection*{{Gráficas}}
{_include_graph(grid_path, f"Mapa de reemplazo – {r.algorithm_name}", f"grid_{short_key}")}
{_include_graph(time_path, f"Fallos acumulados – {r.algorithm_name}", f"time_{short_key}")}
{_include_graph(pie_path, f"Hit vs Fault – {r.algorithm_name}", f"pie_{short_key}")}
"""
        sections.append(section)

    # ── Comparison section ────────────────────────────────────────────────────
    cmp_table_rows = []
    for r in results:
        short = _escape(r.algorithm_name.split("(")[0].split("–")[0].strip())
        cmp_table_rows.append(
            f"{short} & {r.page_faults} & {r.page_hits} & "
            f"{r.hit_ratio:.2%} & {r.system_calls} & {r.interrupts} & "
            f"{r.execution_time_us:.3f} µs & {r.memory_used_kb:.1f} KB \\\\"
        )
    cmp_rows_str = "\n".join(cmp_table_rows)

    cmp_graph = os.path.join(graph_dir, "comparison.png")

    comparison_section = rf"""
\newpage
\section{{Comparación General}}

\begin{{center}}
\small
\begin{{tabular}}{{|l|r|r|r|r|r|r|r|}}
\hline
\textbf{{Algoritmo}} & \textbf{{Fallos}} & \textbf{{Aciertos}} &
\textbf{{Hit-ratio}} & \textbf{{Syscalls}} & \textbf{{Interrupciones}} &
\textbf{{Tiempo}} & \textbf{{Memoria}} \\
\hline
{cmp_rows_str}
\hline
\end{{tabular}}
\end{{center}}

{_include_graph(cmp_graph, "Comparación de todos los algoritmos", "comparison")}
"""

    # ── Full document ─────────────────────────────────────────────────────────
    doc = rf"""
\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[spanish]{{babel}}
\usepackage{{geometry}}
\geometry{{margin=2.5cm}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\hypersetup{{colorlinks=true, linkcolor=blue, urlcolor=blue}}
\usepackage{{fancyhdr}}
\pagestyle{{fancy}}
\fancyhf{{}}
\rhead{{Simulador de Reemplazo de Páginas}}
\lhead{{\leftmark}}
\rfoot{{Pág. \thepage}}

\title{{
  \textbf{{Informe de Simulación}}\\
  \large Algoritmos de Reemplazo de Páginas en Memoria Virtual
}}
\author{{Generado automáticamente por PaginaciónMemoria}}
\date{{{now}}}

\begin{{document}}

\maketitle
\tableofcontents
\newpage

\section{{Introducción}}

Este informe presenta los resultados de la simulación de cinco algoritmos clásicos
de reemplazo de páginas en memoria virtual: \textbf{{FIFO}}, \textbf{{LRU}},
\textbf{{OPT}}, \textbf{{Clock}} y \textbf{{LFU}}.

\subsection*{{Parámetros de simulación}}
\begin{{itemize}}
  \item Número de marcos de página: \textbf{{{results[0].num_frames}}}
  \item Longitud de la cadena de referencia: \textbf{{{results[0].total_references}}}
  \item Páginas únicas: \textbf{{{len(set(results[0].reference_string))}}}
  \item Cadena de referencia: $\langle$ {ref_display} $\rangle$
\end{{itemize}}

\subsection*{{Métricas registradas}}
\begin{{enumerate}}
  \item \textbf{{Recursos utilizados}}: marcos de página, tamaño de página (4 KB),
        memoria total asignada.
  \item \textbf{{Tiempo de ejecución}}: medido con \texttt{{time.perf\_counter\_ns()}}
        (resolución de nanosegundos).
  \item \textbf{{Llamadas al sistema}}: cada fallo de página invoca
        \texttt{{handle\_page\_fault()}} (simulado).
  \item \textbf{{Interrupciones}}: cada fallo de página genera una interrupción
        \#14 (Page Fault, x86) (simulada).
  \item \textbf{{Tabla/gráfica de reemplazo}}: estado de los marcos en cada paso.
\end{{enumerate}}

{"".join(sections)}

{comparison_section}

\newpage
\section{{Conclusiones}}

\begin{{itemize}}
  \item \textbf{{OPT}} produce el mínimo teórico de fallos y sirve como cota
        inferior de comparación.
  \item \textbf{{LRU}} suele aproximar OPT con un coste de implementación razonable.
  \item \textbf{{FIFO}} es el más simple pero puede sufrir la Anomalía de Bélády.
  \item \textbf{{Clock}} es la aproximación práctica de LRU usada en sistemas reales
        (Linux \texttt{{kswapd}}).
  \item \textbf{{LFU}} favorece páginas de alta frecuencia pero puede retener
        páginas obsoletas.
\end{{itemize}}

\end{{document}}
"""

    tex_path = os.path.join(output_dir, "informe.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return tex_path


def compile_latex(tex_path: str) -> bool:
    """Try to compile .tex → .pdf using pdflatex. Returns True on success."""
    cwd = os.path.dirname(tex_path)
    try:
        for _ in range(2):   # run twice for TOC
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", os.path.basename(tex_path)],
                cwd=cwd,
                capture_output=True,
                timeout=60,
            )
        pdf_path = tex_path.replace(".tex", ".pdf")
        return os.path.exists(pdf_path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
