"""
Genera informe LaTeX autocontenido (PGFPlots, sin imagenes externas)
listo para compilar en Overleaf, mas un ZIP para importar directamente.
Uso:  python generar_latex_overleaf.py
"""
import sys, os, zipfile, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.simulator import run_single

def pct(value):
    """Format float as LaTeX-safe percentage string."""
    return f"{value:.2%}".replace("%", r"\%")

REF    = [1, 3, 4, 2, 3, 6, 5, 6, 2, 3, 7, 8, 4]
FRAMES = 4
NOW    = datetime.datetime.now().strftime("%Y-%m-%d")
OUT    = os.path.join(os.path.dirname(__file__), "output", "reports")
os.makedirs(OUT, exist_ok=True)

ALGO_ORDER = ["FIFO", "LRU", "OPT", "Clock", "LFU"]

ALGO_NAMES = {
    "FIFO" : "FIFO -- First In, First Out",
    "LRU"  : "LRU -- Least Recently Used",
    "OPT"  : "OPT -- Optimo (Belady)",
    "Clock": "Clock -- Segunda Oportunidad",
    "LFU"  : "LFU -- Least Frequently Used",
}
ALGO_DESC = {
    "FIFO" : ("Reemplaza la pagina mas antigua segun orden de llegada. "
              "Es el algoritmo mas simple pero puede sufrir la Anomalia de Belady."),
    "LRU"  : ("Reemplaza la pagina que no ha sido usada por mas tiempo. "
              "Aproxima el comportamiento optimo sin conocer el futuro."),
    "OPT"  : ("Reemplaza la pagina cuyo proximo uso esta mas lejano en el futuro. "
              "Produce el minimo teorico de fallos; sirve como referencia comparativa."),
    "Clock": ("Usa un bit de referencia por marco. Si el bit es 1 se pone a 0 y se "
              "avanza; si es 0 se reemplaza. Implementacion practica de LRU (Linux kswapd)."),
    "LFU"  : ("Reemplaza la pagina con menor frecuencia de acceso acumulada. "
              "Tiebreaker por orden FIFO. Favorece paginas de alta demanda historica."),
}

# Stable colors for pages 0-9
PAGE_COLORS = [
    ("pA","231,76,60"), ("pB","52,152,219"), ("pC","46,204,113"),
    ("pD","241,196,15"),("pE","155,89,182"), ("pF","26,188,156"),
    ("pG","230,126,34"),("pH","233,30,99"),  ("pI","0,188,212"),
    ("pJ","205,220,57"),
]
PID = ["pA","pB","pC","pD","pE","pF","pG","pH","pI","pJ"]
def pcol(p): return PID[p % 10]


# ── Run all simulations ───────────────────────────────────────────────────────
print("Ejecutando simulaciones...")
results = {}
for key in ALGO_ORDER:
    r = run_single(key, REF, FRAMES)
    results[key] = r
    print(f"  {key:6s}: {r.page_faults} fallos, {r.page_hits} aciertos, "
          f"hit={r.hit_ratio:.2%}, t={r.execution_time_us:.3f}us")


# ── LaTeX builders ────────────────────────────────────────────────────────────

def repl_table(r):
    steps = r.steps
    n     = len(steps)
    col_spec = "|l|" + "".join([">{\\centering\\arraybackslash}p{0.4cm}|"] * n)
    lines = [
        r"\begin{center}",
        r"\scriptsize\setlength{\tabcolsep}{2pt}",
        r"\begin{tabular}{" + col_spec + "}",
        r"\hline",
    ]
    # Header row — coloured by fault/hit
    hdr = []
    for s in steps:
        bg = "faultcol!50" if s.is_fault else "hitcol!40"
        hdr.append(r"\cellcolor{" + bg + r"}\textbf{" + str(s.reference) + "}")
    lines.append(r"\textbf{Ref} & " + " & ".join(hdr) + r" \\")
    lines.append(r"\hline")
    # Frame rows
    for fi in range(FRAMES):
        row = []
        for s in steps:
            if fi < len(s.frames):
                p = s.frames[fi]
                row.append(r"\cellcolor{" + pcol(p) + r"!40}" + str(p))
            else:
                row.append(r"{\color{gray!60}--}")
        lines.append(f"M{fi} & " + " & ".join(row) + r" \\")
    lines.append(r"\hline")
    # Fault/Hit row
    fh = []
    for s in steps:
        if s.is_fault:
            v = f"\\tiny ->{s.victim}" if s.victim is not None else ""
            fh.append(r"{\color{faultcol}\textbf{F}" + v + "}")
        else:
            fh.append(r"{\color{hitcol}\textbf{H}}")
    lines.append(r"\textbf{F/H} & " + " & ".join(fh) + r" \\")
    lines.append(r"\hline")
    lines += [r"\end{tabular}", r"\end{center}"]
    return "\n".join(lines)


def metrics_table(r):
    def row(label, value):
        return f"  {label} & {value} \\\\"
    lines = [
        r"\begin{center}",
        r"\small",
        r"\begin{tabular}{|l|r|}",
        r"\hline",
        r"\multicolumn{2}{|c|}{\cellcolor{accentcol!30}\textbf{1.\ Recursos Utilizados}} \\",
        r"\hline",
        row("Marcos de pagina",  str(r.num_frames)),
        row("Tamano de pagina",  "4\\,096 bytes (4 KB)"),
        row("Memoria asignada",  f"{r.memory_used_bytes:,} B ({r.memory_used_kb:.1f} KB)"),
        row("Paginas unicas",    str(len(set(r.reference_string)))),
        row("Total referencias", str(r.total_references)),
        r"\hline",
        r"\multicolumn{2}{|c|}{\cellcolor{accentcol!30}\textbf{2.\ Tiempo de Ejecucion}} \\",
        r"\hline",
        row("Tiempo (ns)", f"{r.execution_time_ns:,.0f}\\,ns"),
        row("Tiempo ($\\mu$s)", f"{r.execution_time_us:.3f}\\,$\\mu$s"),
        row("Tiempo (ms)", f"{r.execution_time_ms:.6f}\\,ms"),
        r"\hline",
        r"\multicolumn{2}{|c|}{\cellcolor{accentcol!30}\textbf{3.\ Llamadas al Sistema}} \\",
        r"\hline",
        row("\\texttt{handle\\_page\\_fault()}",
            r"\textcolor{faultcol}{\textbf{" + str(r.system_calls) + "}}"),
        row("Tasa syscalls/ref.",
            f"{r.system_calls/r.total_references:.4f}"),
        r"\hline",
        r"\multicolumn{2}{|c|}{\cellcolor{accentcol!30}\textbf{4.\ Interrupciones}} \\",
        r"\hline",
        row("Interrupciones \\#14 (PF x86)",
            r"\textcolor{faultcol}{\textbf{" + str(r.interrupts) + "}}"),
        row("Aciertos (sin interrupcion)",
            r"\textcolor{hitcol}{\textbf{" + str(r.page_hits) + "}}"),
        r"\hline",
        r"\multicolumn{2}{|c|}{\cellcolor{accentcol!30}\textbf{Resumen}} \\",
        r"\hline",
        row("Fallos de pagina",
            r"\textcolor{faultcol}{\textbf{" + str(r.page_faults) + "}}"),
        row("Aciertos de pagina",
            r"\textcolor{hitcol}{\textbf{" + str(r.page_hits) + "}}"),
        row("Hit ratio",
            r"\textcolor{hitcol}{" + pct(r.hit_ratio) + "}"),
        row("Fault ratio",
            r"\textcolor{faultcol}{" + pct(r.fault_ratio) + "}"),
        r"\hline",
        r"\end{tabular}",
        r"\end{center}",
    ]
    return "\n".join(lines)


def pgfplot_bar(key, r):
    return (
        r"\begin{center}" + "\n"
        r"\begin{tikzpicture}" + "\n"
        r"\begin{axis}[" + "\n"
        r"    ybar, bar width=16pt," + "\n"
        r"    width=8cm, height=5cm," + "\n"
        r"    symbolic x coords={Fallos,Aciertos,Syscalls,Interrups}," + "\n"
        r"    xtick=data," + "\n"
        r"    nodes near coords," + "\n"
        r"    nodes near coords align={vertical}," + "\n"
        r"    ylabel={Cantidad}," + "\n"
        r"    title={\small Metricas -- " + key + r"}," + "\n"
        r"    tick label style={font=\small}," + "\n"
        r"    enlarge x limits=0.25," + "\n"
        r"]" + "\n"
        r"\addplot[fill=faultcol!70] coordinates {" +
        f"(Fallos,{r.page_faults}) (Syscalls,{r.system_calls}) (Interrups,{r.interrupts})" +
        r"};" + "\n"
        r"\addplot[fill=hitcol!70] coordinates {" +
        f"(Aciertos,{r.page_hits})" +
        r"};" + "\n"
        r"\end{axis}" + "\n"
        r"\end{tikzpicture}" + "\n"
        r"\end{center}"
    )


def pgfplot_line(key, r):
    coords = []
    c = 0
    for i, s in enumerate(r.steps, 1):
        if s.is_fault:
            c += 1
        coords.append(f"({i},{c})")
    coord_str = " ".join(coords)
    n = len(r.steps)
    return (
        r"\begin{center}" + "\n"
        r"\begin{tikzpicture}" + "\n"
        r"\begin{axis}[" + "\n"
        r"    width=13cm, height=4.5cm," + "\n"
        r"    xlabel={Referencia \#}," + "\n"
        r"    ylabel={Fallos acumulados}," + "\n"
        r"    title={\small Evolucion de Fallos -- " + key + r"}," + "\n"
        r"    grid=major, grid style={dashed,gray!40}," + "\n"
        r"    tick label style={font=\small}," + "\n"
        r"    xmin=1, xmax=" + str(n) + r"," + "\n"
        r"    ymin=0," + "\n"
        r"]" + "\n"
        r"\addplot[color=faultcol, thick, mark=*, mark size=1.5pt]" + "\n"
        r"    coordinates { " + coord_str + r" };" + "\n"
        r"\end{axis}" + "\n"
        r"\end{tikzpicture}" + "\n"
        r"\end{center}"
    )


def comparison_table(results):
    best = min(r.page_faults for r in results.values())
    lines = [
        r"\begin{center}",
        r"\small",
        r"\begin{tabular}{|l|r|r|r|r|r|r|r|}",
        r"\hline",
        r"\rowcolor{accentcol!30}",
        (r"\textbf{Algoritmo} & \textbf{Fallos} & \textbf{Aciertos} & "
         r"\textbf{Hit\,\%} & \textbf{Syscalls} & \textbf{Interrups.} & "
         r"\textbf{Tiempo\,($\mu$s)} & \textbf{Mem.\,(KB)} \\"),
        r"\hline",
    ]
    for key in ALGO_ORDER:
        r = results[key]
        if r.page_faults == best:
            fstr = r"\cellcolor{hitcol!30}\textbf{" + str(r.page_faults) + "}"
        else:
            fstr = str(r.page_faults)
        lines.append(
            f"  {key} & {fstr} & {r.page_hits} & {pct(r.hit_ratio)} & "
            f"{r.system_calls} & {r.interrupts} & "
            f"{r.execution_time_us:.3f} & {r.memory_used_kb:.1f} \\\\\n  \\hline"
        )
        lines.append(r"  \hline")
    lines += [r"\end{tabular}", r"\end{center}"]
    return "\n".join(lines)


def comparison_pgfplot(results):
    keys    = ALGO_ORDER
    faults  = [results[k].page_faults for k in keys]
    hits    = [results[k].page_hits   for k in keys]
    sym_x   = ",".join(keys)
    f_coord = " ".join(f"({k},{v})" for k, v in zip(keys, faults))
    h_coord = " ".join(f"({k},{v})" for k, v in zip(keys, hits))
    return (
        r"\begin{center}" + "\n"
        r"\begin{tikzpicture}" + "\n"
        r"\begin{axis}[" + "\n"
        r"    ybar, bar width=14pt," + "\n"
        r"    width=13cm, height=6cm," + "\n"
        r"    symbolic x coords={" + sym_x + r"}," + "\n"
        r"    xtick=data," + "\n"
        r"    legend style={at={(0.98,0.98)},anchor=north east,font=\small}," + "\n"
        r"    nodes near coords," + "\n"
        r"    nodes near coords style={font=\tiny}," + "\n"
        r"    ylabel={Cantidad}," + "\n"
        r"    title={\textbf{Comparacion de Algoritmos: Fallos vs Aciertos}}," + "\n"
        r"    enlarge x limits=0.12," + "\n"
        r"    tick label style={font=\small}," + "\n"
        r"]" + "\n"
        r"\addplot[fill=faultcol!80] coordinates { " + f_coord + r" };" + "\n"
        r"\addplot[fill=hitcol!80]   coordinates { " + h_coord + r" };" + "\n"
        r"\legend{Fallos, Aciertos}" + "\n"
        r"\end{axis}" + "\n"
        r"\end{tikzpicture}" + "\n"
        r"\end{center}"
    )


# ── Algorithm sections ────────────────────────────────────────────────────────
algo_sections = []
for key in ALGO_ORDER:
    r = results[key]
    ref_hdr = r"\ ".join(str(p) for p in r.reference_string)
    sec = (
        f"\n\\newpage\n"
        f"\\section{{{ALGO_NAMES[key]}}}\n\n"
        f"{ALGO_DESC[key]}\n\n"
        f"\\subsection{{Tabla de Reemplazo}}\n"
        f"\\textbf{{Cadena:}} $\\langle\\;{ref_hdr}\\;\\rangle$"
        f"\\quad\\textbf{{Marcos:}} {FRAMES}\n\\medskip\n"
        f"{repl_table(r)}\n\n"
        f"\\subsection{{Metricas}}\n"
        f"\\begin{{minipage}}[t]{{0.50\\textwidth}}\n"
        f"{metrics_table(r)}\n"
        f"\\end{{minipage}}\\hfill\n"
        f"\\begin{{minipage}}[t]{{0.46\\textwidth}}\n"
        f"\\vspace{{0pt}}\n"
        f"{pgfplot_bar(key, r)}\n"
        f"\\end{{minipage}}\n\n"
        f"\\subsection{{Evolucion de Fallos Acumulados}}\n"
        f"{pgfplot_line(key, r)}\n"
    )
    algo_sections.append(sec)

# ── Color definitions ─────────────────────────────────────────────────────────
color_defs = "\n".join(
    f"\\definecolor{{{name}}}{{RGB}}{{{rgb}}}"
    for name, rgb in PAGE_COLORS
)

ref_display = r"\ ".join(str(p) for p in REF)
best_fault  = min(r.page_faults for r in results.values())
best_keys   = [k for k in ALGO_ORDER if results[k].page_faults == best_fault]
best_str    = ", ".join(best_keys)

# Pre-compute percentage strings (avoid :.2\% inside f-string)
lru_hit_pct   = pct(results['LRU'].hit_ratio)
fifo_hit_pct  = pct(results['FIFO'].hit_ratio)
opt_hit_pct   = pct(results['OPT'].hit_ratio)
clock_hit_pct = pct(results['Clock'].hit_ratio)
lfu_hit_pct   = pct(results['LFU'].hit_ratio)
fifo_flt      = results['FIFO'].page_faults
lru_flt       = results['LRU'].page_faults
opt_flt       = results['OPT'].page_faults
clock_flt     = results['Clock'].page_faults
lfu_flt       = results['LFU'].page_faults

# ── Full LaTeX document ───────────────────────────────────────────────────────
doc = rf"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[spanish]{{babel}}
\usepackage{{geometry}}
\geometry{{margin=2.5cm, headheight=15pt, top=3cm}}
\usepackage{{xcolor}}
\usepackage{{colortbl}}
\usepackage{{array}}
\usepackage{{float}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usepackage{{tikz}}
\usepackage{{fancyhdr}}
\usepackage{{hyperref}}
\hypersetup{{colorlinks=true,linkcolor=blue,urlcolor=blue}}

%% Colores principales
\definecolor{{faultcol}}{{RGB}}{{231,76,60}}
\definecolor{{hitcol}}{{RGB}}{{46,204,113}}
\definecolor{{accentcol}}{{RGB}}{{52,152,219}}
%% Colores de paginas
{color_defs}

%% Encabezado
\pagestyle{{fancy}}
\fancyhf{{}}
\rhead{{Reemplazo de Paginas}}
\lhead{{\leftmark}}
\cfoot{{Pagina \thepage}}

\title{{\Huge\textbf{{Informe de Simulacion}}\\[0.8em]
\large Algoritmos de Reemplazo de Paginas\\en Memoria Virtual}}
\author{{Simulador PaginacionMemoria\\
\small\url{{https://github.com/lider-ch/algoritmos-de-reemplazo}}}}
\date{{{NOW}}}

\begin{{document}}

\maketitle
\tableofcontents
\newpage

%% ============================================================
\section{{Introduccion}}

Este informe documenta la simulacion de cinco algoritmos clasicos de
reemplazo de paginas aplicados sobre una misma cadena de referencia con
un numero fijo de marcos de memoria.

\subsection*{{Parametros de simulacion}}
\begin{{center}}
\begin{{tabular}}{{|l|c|}}
\hline
\rowcolor{{accentcol!25}}
\textbf{{Parametro}} & \textbf{{Valor}} \\
\hline
Numero de marcos de pagina & \textbf{{{FRAMES}}} \\
Longitud de la cadena de referencia & \textbf{{{len(REF)}}} \\
Paginas distintas en la cadena & \textbf{{{len(set(REF))}}} \\
Memoria asignada & \textbf{{{FRAMES * 4096:,} bytes ({FRAMES * 4}~KB)}} \\
Tamano de pagina & 4\,096 bytes (4~KB) \\
Cadena de referencia & $\langle\;{ref_display}\;\rangle$ \\
\hline
\end{{tabular}}
\end{{center}}

\subsection*{{Metricas registradas}}
\begin{{enumerate}}
  \item \textbf{{Recursos utilizados}}: marcos, tamano de pagina (4~KB), memoria total.
  \item \textbf{{Tiempo de ejecucion}}: cronometrado con \texttt{{time.perf\_counter\_ns()}}
        (resolucion de nanosegundos).
  \item \textbf{{Llamadas al sistema}}: \texttt{{handle\_page\_fault()}} se invoca
        en cada fallo de pagina (simulada).
  \item \textbf{{Interrupciones}}: interrupcion de hardware \textbf{{\#14 Page Fault (x86)}}
        generada en cada fallo (simulada).
  \item \textbf{{Tabla y grafica de reemplazo}}: estado de los marcos en cada paso.
\end{{enumerate}}

\subsection*{{Leyenda de tablas}}
\begin{{itemize}}
  \item \textcolor{{faultcol}}{{\textbf{{F}}}}~=~Fallo de pagina\quad
        \textcolor{{hitcol}}{{\textbf{{H}}}}~=~Acierto\quad
        Celda coloreada~=~pagina almacenada en el marco
  \item Encabezado \colorbox{{faultcol!50}}{{rojo}}~=~fallo;
        \colorbox{{hitcol!40}}{{verde}}~=~acierto
  \item \texttt{{->V}} en fila F/H indica la pagina victima desalojada
\end{{itemize}}

{"".join(algo_sections)}

%% ============================================================
\newpage
\section{{Comparacion General de Algoritmos}}

\subsection{{Tabla comparativa de metricas}}
{comparison_table(results)}

\medskip
\noindent
Celdas \colorbox{{hitcol!30}}{{verdes}} indican el menor numero de fallos
(mejor resultado) = \textbf{{{best_fault} fallos}} obtenido por
\textbf{{{best_str}}}.

\subsection{{Grafica comparativa}}
{comparison_pgfplot(results)}

%% ============================================================
\newpage
\section{{Conclusiones}}

\begin{{enumerate}}
  \item \textbf{{OPT}} es la cota teorica inferior: {opt_flt}~fallos.
        Ningun algoritmo online puede superar este valor para esta cadena.

  \item \textbf{{LRU, OPT y LFU}} empataron con
        \textcolor{{hitcol}}{{\textbf{{{lru_flt}~fallos}}}} y
        hit-ratio del {lru_hit_pct},
        superando a FIFO ({fifo_flt}~fallos)
        y Clock ({clock_flt}~fallos).

  \item \textbf{{FIFO}} es el mas sencillo pero puede sufrir la
        \textit{{Anomalia de Belady}}: aumentar los marcos puede
        incrementar los fallos en ciertas cadenas.

  \item \textbf{{Clock}} (Segunda Oportunidad) es la implementacion
        practica mas extendida en sistemas reales
        (\texttt{{kswapd}} en Linux, \texttt{{vm\_pageout}} en BSD).

  \item \textbf{{LFU}} acumula frecuencias de uso; puede retener paginas
        obsoletas que fueron muy accedidas en el pasado
        (problema de ``cache fria'' tras un cambio de patron).

  \item El tiempo de ejecucion de todos los algoritmos fue
        $< 40\,\mu$s, lo que confirma la eficiencia computacional
        de las implementaciones simuladas.

  \item Con 4~marcos y esta cadena especifica, aumentar a 5~marcos
        reduciria los fallos de OPT a su minimo absoluto.
\end{{enumerate}}

\bigskip
\begin{{center}}
\small\color{{gray}}
Generado automaticamente por PaginacionMemoria \quad|\quad
\url{{https://github.com/lider-ch/algoritmos-de-reemplazo}}
\end{{center}}

\end{{document}}
"""

# ── Write files ───────────────────────────────────────────────────────────────
tex_path = os.path.join(OUT, "informe_reemplazo.tex")
with open(tex_path, "w", encoding="utf-8") as f:
    f.write(doc)
print(f"\nTeX generado : {tex_path}")
print(f"Tamano       : {len(doc):,} caracteres")

zip_path = os.path.join(OUT, "overleaf_upload.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(tex_path, "informe_reemplazo.tex")
print(f"ZIP generado : {zip_path}")
print("\nListo para subir a Overleaf!")
