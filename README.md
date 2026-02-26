# PaginaciónMemoria – Simulador de Algoritmos de Reemplazo de Páginas

Simulador interactivo en Python de los cinco algoritmos clásicos de reemplazo de páginas en memoria virtual.

## Algoritmos implementados

| # | Algoritmo | Descripción |
|---|-----------|-------------|
| 1 | **FIFO** | First In, First Out – reemplaza la página más antigua |
| 2 | **LRU** | Least Recently Used – reemplaza la menos usada recientemente |
| 3 | **OPT** | Óptimo (Bélády) – reemplaza la que se usará más tarde en el futuro |
| 4 | **Clock** | Segunda Oportunidad – aproximación eficiente de LRU |
| 5 | **LFU** | Least Frequently Used – reemplaza la menos frecuentemente usada |

## Métricas capturadas

1. **Recursos utilizados** – marcos, tamaño de página (4 KB), memoria asignada
2. **Tiempo de ejecución** – nanosegundos / microsegundos / milisegundos
3. **Llamadas al sistema** – `handle_page_fault()` por cada fallo de página
4. **Interrupciones** – interrupción #14 (Page Fault x86) por cada fallo
5. **Tabla y gráfica de reemplazo** – estado de los marcos en cada paso

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/PaginacionMemoria.git
cd PaginacionMemoria

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

> **Nota:** las dependencias también se instalan automáticamente al arrancar `main.py` si alguna falta.

## Estructura del proyecto

```
PaginacionMemoria/
├── main.py                  # Punto de entrada y menú principal
├── algorithms/
│   ├── base.py              # Clase base y dataclass SimulationResult
│   ├── fifo.py
│   ├── lru.py
│   ├── opt.py
│   ├── clock.py
│   └── lfu.py
├── core/
│   ├── simulator.py         # Orquestador de ejecución
│   └── metrics.py           # Visualización de métricas (Rich)
├── ui/
│   ├── menu.py              # Menú interactivo (Rich)
│   └── display.py           # Tabla de reemplazo (Rich)
├── reports/
│   ├── graph.py             # Gráficas Matplotlib
│   └── latex_builder.py     # Generador de informe LaTeX
├── git_integration/
│   └── repo_manager.py      # Gestión Git (GitPython)
├── output/
│   ├── graphs/              # PNGs generados
│   └── reports/             # informe.tex / informe.pdf
└── requirements.txt
```

## Salidas

- **Terminal**: tabla de reemplazo colorida + métricas en tiempo real
- **Gráficas PNG**: mapa de calor de reemplazo, evolución de fallos, comparación, pie chart
- **Informe LaTeX**: `output/reports/informe.tex` (+ PDF si pdflatex está instalado)

## Compilar informe PDF manualmente

```bash
cd output/reports
pdflatex informe.tex
pdflatex informe.tex   # segunda pasada para la tabla de contenidos
```

O subir `informe.tex` a [Overleaf](https://www.overleaf.com) para compilación en línea.

## Licencia

MIT
