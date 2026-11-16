"""Build the standalone final HTML and the thesis insertion notes."""

import argparse
import base64
import csv
import json
import tomllib
from html import escape
from pathlib import Path

from secondary_metrics import (
    CONDITIONS,
    EVIDENCE,
    FIGURES,
    METRICS,
    PROVENANCE,
    REFERENCE,
    ROOT,
    SCOPE,
    format_number,
    output_path,
    read_verified,
)

AUDIT = ROOT / "docs/evidence/oos-v12-evaluation-20261115/final-contrast-audit.json"
AUDIT_SHA = "09df2ef07d76739395c46db6f0ff8e0392fdfe527cd9b9239dbd3fc87d416fd9"
TRAINING = ROOT / "docs/protocols/OOS-v1-2-training-freeze-20261110.json"
TRAINING_SHA = "0651f396f3157eaa5abd6bb7faf7ec1c6463210d255fa2fbd8a932e2999870a0"
CANDIDATE = "docs/protocols/P2-infrastructure-v1.json"

STYLE = """
:root{color-scheme:light;--ink:#182b35;--accent:#14534b;--rule:#d1dad9;--soft:#eef4f2}
*{box-sizing:border-box}body{margin:0;background:#f9fbfa;color:var(--ink);
font:1rem/1.55 system-ui,sans-serif}main{max-width:980px;margin:auto;padding:2rem 1.4rem 4rem}
header{padding:2rem 0 1.3rem;border-bottom:2px solid var(--accent)}
.eyebrow{font-size:.85rem;text-transform:uppercase;letter-spacing:.09em;color:var(--accent)}
h1{font-size:clamp(2rem,5vw,3.2rem);line-height:1.12;max-width:18ch;margin:.55rem 0 1rem}
h2{font-size:1.55rem;margin-top:2.25rem;line-height:1.2}p{max-width:76ch}
nav ul{display:flex;flex-wrap:wrap;gap:.5rem 1.25rem;padding:0;list-style:none}
a{color:var(--accent)}figure{margin:0;padding:1rem;border:1px solid var(--rule);
background:white;break-inside:avoid}img{display:block;width:100%;height:auto}
figcaption{font-size:.87rem;margin-top:.75rem}.figures{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem}
.table{overflow-x:auto}table{border-collapse:collapse;width:100%;margin:.8rem 0 1.4rem;
font-variant-numeric:tabular-nums;background:white}td,th{padding:.5rem .65rem;
border-bottom:1px solid var(--rule);text-align:right}thead th{background:var(--soft)}
td:first-child,th:first-child{text-align:left}tbody tr:nth-child(even){background:#f5f8f7}
details{border:1px solid var(--rule);padding:.65rem .9rem}summary{cursor:pointer;font-weight:650}
code{overflow-wrap:anywhere;font-size:.85em}.scope{background:var(--soft);padding:1rem}
@media(max-width:730px){.figures{grid-template-columns:1fr}}
@media print{body{background:white}nav{display:none}main{padding:0}.figures{display:block}
figure{max-width:15cm;margin:0 auto 1rem}h2{break-after:avoid}}
"""


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def display(value, metric):
    if value in (None, ""):
        return "No definido"
    multiplier = 100 if METRICS[metric][1].startswith("%") else 1
    return format_number(float(value) * multiplier)


def metrics_table(summary):
    summary_by_name = {row["condition"]: row for row in summary}
    headings = ("Métrica", "Unidad", *CONDITIONS, REFERENCE)
    rows = []
    for key, (name, unit) in METRICS.items():
        cells = [name, unit]
        for condition in (*CONDITIONS, REFERENCE):
            row = summary_by_name[condition]
            value = display(row[key + "_mean"], key)
            if condition != REFERENCE and row[key + "_sd"]:
                value += " ± " + display(row[key + "_sd"], key)
            cells.append(value)
        rows.append(cells)
    return headings, rows


def paired_table(pairs):
    headings = ("Métrica", "Unidad de la diferencia", "C5 − C0 · media [95 %]",
                "C10 − C0 · media [95 %]")
    by_metric = {(r["metric"], r["contrast"]): r for r in pairs}
    rows = []
    for key, (name, unit) in METRICS.items():
        cells = [name, unit.replace("%", "puntos porcentuales")]
        for condition in CONDITIONS[1:]:
            row = by_metric[key, condition + " − C0"]
            if not row["mean"]:
                cells.append(f"No definido ({row['n_defined_pairs']}/36 pares definidos)")
            else:
                mean, low, high = (display(row[field], key)
                                   for field in ("mean", "ci95_low", "ci95_high"))
                cells.append(f"{mean} [{low}; {high}]")
        rows.append(cells)
    return headings, rows


def table_html(headers, rows):
    head = "".join(f'<th scope="col">{escape(str(x))}</th>' for x in headers)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(x))}</td>" for x in row) + "</tr>"
                   for row in rows)
    return f'<div class="table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def table_md(headers, rows):
    all_rows = [headers, ["---"] * len(headers), *rows]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in all_rows)


def primary_tables(policies):
    sortino = {(row["block"], row["seed"], row["condition"]): row["sortino"] for row in policies}
    blocks = sorted({key[:2] for key in sortino}, key=lambda row: int(row[0]))
    rows = [[block, seed, *(format_number(float(sortino[block, seed, c])) for c in CONDITIONS)]
            for block, seed in blocks]
    return table_html(("Bloque", "Semilla", *CONDITIONS), rows)


def contrast_table(audit):
    rows = []
    for condition in CONDITIONS[1:]:
        item = audit["comparisons"][condition + "_minus_C0"]
        low, high = map(format_number, item["interval_95"])
        rows.append([condition + " − C0", format_number(item["mean_difference"]),
                     f"[{low}; {high}]", format_number(item["paired_dz"]),
                     format_number(item["p_one_sided"]), format_number(item["p_holm"]),
                     "Rechazada" if item["reject_null"] else "No rechazada"])
    return table_html(("Contraste", "Diferencia media", "IC descriptivo 95 %", "d pareado",
                       "p unilateral", "p Holm", "Hipótesis nula"), rows)


def render(source, summary, pairs, policies, meta):
    audit = json.loads(read_verified(AUDIT, AUDIT_SHA))
    if audit["final_ledger_sha256"] != meta["ledger_sha256"]:
        raise ValueError("El contraste auditado y las métricas tienen distinto ledger")
    freeze = json.loads(read_verified(TRAINING, TRAINING_SHA))
    design = freeze["design"]
    settings = json.loads(read_verified(
        ROOT / CANDIDATE, freeze["inputs_sha256"][CANDIDATE]
    ))["training_candidate"]
    config = tomllib.loads(read_verified(
        ROOT / "configs/initial.toml", freeze["inputs_sha256"]["configs/initial.toml"]
    ).decode())
    env = config["environment"]
    figures = []
    for name, title in FIGURES.items():
        image = base64.b64encode((source / (name + ".png")).read_bytes()).decode("ascii")
        figures.append(f'<figure><img src="data:image/png;base64,{image}" alt="{escape(title)}">'
                       f'<figcaption>{escape(PROVENANCE)}.</figcaption></figure>')
    primary = table_html(("Condición", "Sortino anualizado medio"), [
        (c, format_number(audit["mean_sortino_by_condition"][c])) for c in CONDITIONS
    ])
    hyperparameters = [
        ("Entrenamiento", "2018–2022 · derivado H1 de entrenamiento"),
        ("Prueba final", "BTC/USDT · 2024–2025 · 4.386 transiciones de cuatro horas"),
        ("Capital y costos", f"{format_number(env['initial_cash'])} USDT · "
         f"comisión {format_number(100 * env['commission'])} % · "
         f"deslizamiento {format_number(100 * env['slippage'])} %"),
        ("Valoración", "Una cartera continua por política, valoración a cierre y sin liquidación final"),
        ("Checkpoint y acción", "K10, after_dual_and_D · sigmoid(μ) determinista · reloj h = 1"),
        ("Normalizador", "Ajustado en entrenamiento y congelado durante la prueba final"),
        ("Arquitectura", f"Actor y crítico separados · {settings['hidden']} unidades ocultas"),
        ("Horizonte y descuento", f"{design['horizon']} transiciones · γ = {design['gamma']}"),
        ("Aprendizaje", f"K={design['iterations']} · β={design['beta']} · "
         f"{settings['actor_epochs']} épocas del actor · {design['critic_epochs']} del crítico"),
        ("Lotes", f"Q={settings['n_q']} / A={settings['n_a']} / B={settings['n_b']} / "
         f"D={design['diagnostic_trajectories']} trayectorias · "
         f"minilote A de {settings['minibatch_trajectories']} trayectorias"),
        ("Tasas y recorte PPO", f"actor {format_number(settings['actor_lr'])} · "
         f"crítico {format_number(settings['critic_lr'])} · dual {format_number(settings['dual_lr'])} · "
         f"recorte {format_number(settings['clip'])}"),
        ("Condiciones", f"C0 neutral · C5/C10 con CVaR de cola 5 %/10 % y d={format_number(design['risk_bound'])}"),
    ]
    hold = next(row for row in summary if row["condition"] == REFERENCE)
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evaluación final de las políticas BTC/USDT</title><style>{STYLE}</style></head>
<body><main><header><span class="eyebrow">BTC/USDT · 2024–2025</span>
<h1>Evaluación final de las políticas de trading</h1><p>{SCOPE} Se incluyeron las 108 políticas y los 36 bloques pareados.</p></header>
<nav aria-label="Secciones del informe"><ul>
<li><a href="#configuracion">Configuración</a></li><li><a href="#primaria">Sortino</a></li>
<li><a href="#contraste">Contraste auditado</a></li><li><a href="#metricas">Métricas descriptivas</a></li>
<li><a href="#figuras">Figuras</a></li><li><a href="#referencia">Comprar y mantener</a></li>
<li><a href="#alcance">Alcance</a></li></ul></nav>
<section id="configuracion"><h2>Configuración utilizada</h2>{table_html(("Componente", "Configuración"), hyperparameters)}</section>
<section id="primaria"><h2>Métrica primaria</h2><p>Sortino anualizado con retornos simples netos de cuatro horas, MAR = 0 y desviación bajista sobre todos los períodos.</p>
{primary}<details><summary>Sortino por bloque y semilla (36 ternas)</summary>{primary_tables(policies)}</details></section>
<section id="contraste"><h2>Contraste pareado auditado</h2>
<p>Valores leídos del cierre auditado. El efecto mínimo predefinido fue +0,50 unidades de Sortino y el nivel familiar fue 0,05.</p>{contrast_table(audit)}</section>
<section id="metricas"><h2>Métricas descriptivas</h2><p>Media ± desviación estándar muestral de 36 políticas por condición. La referencia es un recorrido único.</p>
{table_html(*metrics_table(summary))}
<h3>Diferencias pareadas descriptivas</h3><p>Media e intervalo percentil 95 % de 20.000 remuestras de los bloques de semilla. Semilla del remuestreo 912016.</p>
{table_html(*paired_table(pairs))}</section>
<section id="figuras"><h2>Curvas y distribución de Sortino</h2><div class="figures">{''.join(figures)}</div></section>
<section id="referencia"><h2>Comprar y mantener BTC</h2><p>Una compra en la primera apertura, con comisión y deslizamiento, y mantenimiento hasta la valoración final. El retorno neto fue {display(hold['return_net_mean'], 'return_net')} % y el Sortino anualizado fue {display(hold['sortino_mean'], 'sortino')}.</p></section>
<section id="alcance"><h2>Alcance y trazabilidad</h2>
<p class="scope">Los resultados corresponden a una simulación en un único período histórico. No constituyen una recomendación de inversión. El CVaR de retornos de cuatro horas difiere del CVaR de trayectorias de 180 transiciones.</p>
<p>Las bandas muestran la dispersión entre políticas en cada fecha y los intervalos descriptivos reflejan variación entre bloques de semillas sobre el mismo período. La anualización es una convención de reporte.</p>
<p>Turnover se define como la media de los cambios absolutos en la exposición marcada al cierre, multiplicada por 2.190. Incluye la entrada desde efectivo y la deriva por precios. Un porcentaje de 100 % por año equivale a una unidad de exposición por año.</p>
<p>108 trazas y reportes verificados antes de calcular. Ledger final SHA-256 <code>{meta['ledger_sha256']}</code>. Auditoría del contraste SHA-256 <code>{AUDIT_SHA}</code>.</p>
</section></main></body></html>
"""


def thesis_notes(summary, pairs):
    by_condition = {row["condition"]: row for row in summary}
    passive = by_condition[REFERENCE]
    returns = [display(by_condition[c]["return_net_mean"], "return_net") for c in CONDITIONS]
    drawdowns = [display(by_condition[c]["max_drawdown_mean"], "max_drawdown") for c in CONDITIONS]
    tail = [display(by_condition[c]["cvar_05_mean"], "cvar_05") for c in CONDITIONS]
    figure_text = "\n\n".join(f"Figura {i}: {title}\n\nFuente: {PROVENANCE}"
                             for i, title in enumerate(FIGURES.values(), 14))
    return f"""# Material para el apartado 4.4.1

{SCOPE} La numeración propuesta sigue a la Figura 13 del documento consultado.

## Métricas por condición

{table_md(*metrics_table(summary))}

Las celdas de C0, C5 y C10 muestran media ± desviación estándar muestral sobre 36 semillas.
Comprar y mantener BTC corresponde a un único recorrido.

## Diferencias pareadas

{table_md(*paired_table(pairs))}

Se calcularon intervalos descriptivos percentiles del 95 % con 20.000 remuestras de
los bloques de semillas y semilla fija 912016. Los intervalos describen dispersión
entre semillas en el mismo período. El contraste confirmatorio de Sortino se conserva
en su informe separado.

## Dos párrafos de resultados

Sobre las trazas de la prueba final de 2024–2025 se calcularon métricas descriptivas después de cerrar el contraste confirmatorio. Se incluyeron las 36 semillas de cada condición. El retorno acumulado neto medio fue {returns[0]} % para C0, {returns[1]} % para C5 y {returns[2]} % para C10. Las caídas máximas medias fueron {drawdowns[0]} %, {drawdowns[1]} % y {drawdowns[2]} %, respectivamente.

El CVaR periódico al 5 % medio fue {tail[0]} % para C0, {tail[1]} % para C5 y {tail[2]} % para C10. La referencia de comprar y mantener BTC registró un retorno acumulado neto de {display(passive['return_net_mean'], 'return_net')} %, una caída máxima de {display(passive['max_drawdown_mean'], 'max_drawdown')} % y un Sortino anualizado de {display(passive['sortino_mean'], 'sortino')}. La comparación con la referencia fue descriptiva.

## Títulos y fuentes

{figure_text}

Si estas figuras se insertan antes de la sección 4.5, actualizar el diagrama C4
de Figura 14 a Figura 18, su mención en el texto y el índice de figuras.

## Frases que conviene actualizar

- **1.5.1, Alcances.** «El reporte en formato HTML previsto inicialmente se limitó a un tablero local de avance de los pilotos». Añadir el informe HTML estático de la prueba final, producido después del cierre.
- **1.5.2, Límites.** «La salida destinada a lectura humana se limitó a informes versionados y a un tablero HTML local». Añadir el informe final estático y conservar la aclaración sobre la interacción por línea de comandos.
- **3.1, Enfoque de la investigación.** «Las métricas secundarias se definieron para describir el riesgo y la actividad operativa». Añadir que se calcularon sobre las trazas finales ya aceptadas.
- **3.6, Hipótesis y operacionalización.** «CVaR, Maximum Drawdown, Calmar, Sharpe, retorno acumulado y turnover se definieron como medidas descriptivas complementarias». Indicar que se reportaron como análisis posterior al cierre y mantener la distinción entre CVaR periódico y CVaR de trayectoria.
- **3.9.1, Cálculo y presentación de métricas.** «Para las métricas secundarias se previeron definiciones de signo, escala y anualización» y «Las curvas comparativas se previeron mediante una regla de selección o agregación». Sustituir por la regla aplicada, mediana punto a punto y banda P5–P95 sobre 36 semillas. Definir turnover como cambio absoluto del peso marcado a cierre.
- **4.4.3, Discusión, limitaciones y cumplimiento de objetivos.** «La evaluación reportó únicamente la métrica primaria» y «no se calcularon sobre las trazas finales». Sustituir por la distinción entre el contraste principal y el análisis descriptivo. Revisar también «con la limitación señalada sobre las métricas secundarias» en el párrafo sobre el cuarto objetivo.
- **4.4.4, Reporte y reproducción.** Añadir las tablas secundarias, los CSV que respaldan las figuras y el HTML a los materiales reproducibles.
- **Conclusiones, primer párrafo.** «La evaluación integral prevista quedó incompleta porque no se reportaron las métricas secundarias». Indicar que se completó la caracterización descriptiva de las trazas. Mantener el alcance de la evidencia y las limitaciones del diseño ya documentadas.
- **Recomendaciones, segunda.** «Calcular y reportar las métricas secundarias sobre las trazas conservadas de la prueba final». Retirar esa tarea realizada. Si se conserva una recomendación en ese lugar, orientar el trabajo futuro a contrastar la estabilidad de estas medidas en otros períodos con un protocolo fijado de antemano.
"""


def build(source, report, thesis):
    for path in (report, source / "index.html", thesis):
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)
    summary = read_csv(source / "summary-by-condition.csv")
    pairs = read_csv(source / "paired-differences.csv")
    policies = read_csv(source / "metrics-by-policy.csv")
    meta = json.loads((source / "integrity.json").read_bytes())
    html = render(source, summary, pairs, policies, meta)
    for path, content in ((report, html), (source / "index.html", html),
                          (thesis, thesis_notes(summary, pairs))):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--report", type=Path, default=ROOT / "reports/evaluacion-final/index.html")
    parser.add_argument("--thesis", type=Path, default=ROOT / "docs/tesis/insertar-en-tesis.md")
    args = parser.parse_args()
    build(*(output_path(ROOT, p) for p in (args.evidence, args.report, args.thesis)))
