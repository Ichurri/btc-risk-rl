"""Offline, read-only report of accepted pilot units and audited closures.

This module deliberately does not import the training or market-data loaders.
Only the five named artifact ledgers, their accepted unit JSON reports, and
small versioned closure JSON files are opened.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

CAMPAIGNS = {
    "P0": ("p0-approved-v1", 9, 2, "p0-execution/campaign-results/results.json"),
    "P1": ("p1-approved-v1", 18, 2, "p1-execution/campaign-results/results.json"),
    "P2": ("p2-approved-v1", 9, 10, "p2-execution/campaign-results/results.json"),
    "P2R": ("p2r-approved-v2", 9, 10, "p2r-market-2026-10-07/results.json"),
    "P3": ("p3-approved-v1", 18, 10, None),
}
RUN_RE = re.compile(r"^run-(\d\d)-(C0|C5|C10)(?:-e[24]|-b[01])?$")
RISK_BOUND = -math.log(0.90)


@dataclass
class Campaign:
    name: str
    root: Path
    state: dict
    ledger_sha256: str
    closure: dict | None
    closure_path: str | None
    units: list[dict]
    reports: dict[str, dict]
    records: list[dict]
    sources: list[str]
    checks: list[str]

    @property
    def complete_runs(self) -> int:
        k = CAMPAIGNS[self.name][2]
        return sum(run.get("next_unit") == k + 1 for run in self.state["runs"].values())


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _ledger(path: Path) -> tuple[dict, str, list[str]]:
    raw = path.read_bytes()
    if not raw.endswith(b"\n"):
        raise ValueError(f"ledger incompleto: {path}")
    lines = raw.splitlines()
    if not lines:
        raise ValueError(f"ledger vacío: {path}")
    prev = None
    checks = [f"ledger: {len(lines)} estados, SHA-256 {_sha(raw)}"]
    for line in lines:
        state = json.loads(line)
        if "state_hash" in state:
            actual = _sha(json.dumps(
                {k: v for k, v in state.items() if k != "state_hash"},
                sort_keys=True, allow_nan=False,
            ).encode())
            if state["previous_hash"] != prev or state["state_hash"] != actual:
                raise ValueError(f"cadena de huellas inválida: {path}")
            prev = actual
        elif prev is not None:
            raise ValueError(f"cadena de huellas incompleta: {path}")
    if prev:
        checks.append("cadena state_hash completa verificada")
    return state, _sha(raw), checks


def _run_index(run_id: str) -> int:
    match = RUN_RE.fullmatch(run_id)
    if match is None:
        raise ValueError(f"identificador de corrida inesperado: {run_id}")
    return int(match.group(1))


def load_campaign(source_root: Path, name: str) -> Campaign:
    """Read one immutable ledger snapshot; never scan unaccepted unit files."""
    if name not in CAMPAIGNS:
        raise ValueError(f"campaña desconocida: {name}")
    folder, _, _, evidence = CAMPAIGNS[name]
    root = Path(source_root)
    artifact = root / "artifacts" / folder
    state, ledger_sha, checks = _ledger(artifact / "ledger.jsonl")
    closure_path = f"docs/evidence/{evidence}" if evidence else None
    closure = _json(root / closure_path) if closure_path else None
    if closure and closure.get("ledger_sha256") != ledger_sha:
        raise ValueError(f"huella del cierre distinta del ledger: {name}")
    if closure:
        checks.append("huella ledger = cierre auditado")
    if name == "P3":
        for relative in ("docs/evidence/p3-market-2026-10-08/session01-closure.json",
                         "docs/evidence/p3-market-2026-10-09/preflight-blocked.json"):
            path = root / relative
            if path.is_file():
                payload = path.read_bytes()
                json.loads(payload)
                checks.append(f"evidencia de sesión anterior: {relative}, SHA-256 {_sha(payload)}")
    if not isinstance(state.get("units"), list) or not isinstance(state.get("runs"), dict):
        raise ValueError(f"ledger sin unidades/corridas: {name}")
    if state.get("cursor", 0) > CAMPAIGNS[name][1]:
        raise ValueError(f"cursor fuera de protocolo: {name}")
    by_run: dict[str, list[dict]] = {}
    sources = [f"artifacts/{folder}/ledger.jsonl"]
    if closure_path:
        sources.append(closure_path)
    if name == "P3":
        sources.extend(relative for relative in (
            "docs/evidence/p3-market-2026-10-08/session01-closure.json",
            "docs/evidence/p3-market-2026-10-09/preflight-blocked.json",
        ) if (root / relative).is_file())
    for unit in state["units"]:
        run_id = unit["run_id"]
        if run_id not in state["runs"] or _run_index(run_id) >= CAMPAIGNS[name][1]:
            raise ValueError(f"unidad ajena al ledger: {name}/{run_id}")
        by_run.setdefault(run_id, []).append(unit)
    for run_id, run in state["runs"].items():
        indices = sorted(item["unit"] for item in by_run.get(run_id, []))
        if indices != list(range(run.get("next_unit", 0))):
            raise ValueError(f"unidades aceptadas discontinuas: {name}/{run_id}")
    if state["cursor"] != sum(
        run.get("next_unit") == CAMPAIGNS[name][2] + 1 for run in state["runs"].values()
    ):
        raise ValueError(f"cursor y corridas completas discordantes: {name}")
    reports = {}
    records = []
    for run_id, accepted in by_run.items():
        last = max(accepted, key=lambda item: item["unit"])
        path = artifact / run_id / f"unit-{last['unit']}.json"
        content = path.read_bytes()
        if last.get("report_sha256") and _sha(content) != last["report_sha256"]:
            raise ValueError(f"huella de reporte inválida: {path}")
        payload = json.loads(content)
        if payload.get("checkpoint_sha256") != last.get("checkpoint_sha256"):
            raise ValueError(f"huella de checkpoint discordante: {path}")
        report = payload.get("report", {})
        reports[run_id] = report
        sources.append(f"artifacts/{folder}/{run_id}/{path.name}")
        accepted_iterations = {u["unit"] - 1 for u in accepted if u["kind"] == "iteration"}
        for record in report.get("diagnostic", {}).get("records", []):
            if record["iteration"] in accepted_iterations:
                records.append({**record, "run_id": run_id})
    checks.append(f"{len(state['units'])} unidades aceptadas; {len(reports)} reportes finales de corrida")
    return Campaign(name, root, state, ledger_sha, closure, closure_path,
                    state["units"], reports, records, sources, checks)


def p3_pairs(campaign: Campaign) -> list[dict]:
    """Pair only accepted complete iterations in matching seed and condition."""
    if campaign.name != "P3":
        return []
    roster = campaign.state.get("identity", {}).get("roster")
    if roster is None:
        raise ValueError("P3 sin roster fijado")
    by_key = {}
    for record in campaign.records:
        run_id = record["run_id"]
        index = _run_index(run_id)
        if index >= len(roster):
            raise ValueError("índice P3 fuera de roster")
        seed, condition, beta = roster[index]
        if condition != RUN_RE.fullmatch(run_id)[2] or beta != int(run_id[-1]):
            raise ValueError("roster P3 y corrida discordantes")
        metric = record.get("D", {}).get("post", {})
        if not _finite(metric.get("mse")) or not _finite(metric.get("z")):
            continue
        key = (seed, condition, record["iteration"])
        by_key.setdefault(key, {})[beta] = metric
    pairs = []
    for (seed, condition, iteration), arms in sorted(by_key.items()):
        if 0 in arms and 1 in arms:
            pairs.append({"seed": seed, "condition": condition, "iteration": iteration,
                          "mse_b0": arms[0]["mse"], "mse_b1": arms[1]["mse"],
                          "z_b0": arms[0]["z"], "z_b1": arms[1]["z"],
                          "delta_mse": arms[1]["mse"] - arms[0]["mse"]})
    return pairs


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _num(value: float, digits: int = 3) -> str:
    return f"{value:,.{digits}f}".replace(",", " ")


def _figure(title: str, svg: str, *, metric: str, unit: str, population: str,
            n: str, source: str, limit: str = "") -> str:
    caveat = f'<p class="chart-limit">{_esc(limit)}</p>' if limit else ""
    return (f'<figure><h4>{_esc(title)}</h4>{svg}<figcaption>'
            f'<p class="chart-facts"><b>Métrica:</b> {_esc(metric)} '
            f'· <b>unidad:</b> {_esc(unit)}</p>'
            f'<p class="chart-context"><b>Lote:</b> {_esc(population)} '
            f'· <b>n:</b> {_esc(n)}</p>'
            f'<p class="chart-source"><b>origen:</b> <code>{_esc(source)}</code></p>'
            f'{caveat}</figcaption></figure>')


def _bars(rows: list[tuple[str, float]], *, max_value: float | None = None,
          color: str = "#227a87", suffix: str = "") -> str:
    if not rows:
        return '<p class="missing">Datos no disponibles.</p>'
    width = 545
    top = max_value or max(value for _, value in rows) or 1
    digits = 4 if top < 1 else (0 if top >= 1000 else 1)
    out = [f'<svg viewBox="0 0 760 {len(rows) * 48 + 18}" role="img" aria-label="Gráfico de barras">']
    for i, (label, value) in enumerate(rows):
        y = i * 48 + 9
        bar = max(0, min(width, width * value / top))
        inside = bar > 460
        text_x = 660 if inside else 148 + bar
        anchor = "end" if inside else "start"
        value_class = "value-in" if inside else "value"
        out.append(f'<text x="0" y="{y + 20}" class="axis">{_esc(label)}</text>'
                   f'<rect x="135" y="{y}" width="{width}" height="28" rx="5" fill="#e5ebe9"/>'
                   f'<rect x="135" y="{y}" width="{bar:.1f}" height="28" rx="5" fill="{color}"/>'
                   f'<text x="{text_x:.1f}" y="{y + 20}" text-anchor="{anchor}" '
                   f'class="{value_class}">'
                   f'{_esc(_num(value, digits) + suffix)}</text>')
    out.append("</svg>")
    return "".join(out)


def _line(points: list[tuple[int, float]], *, color: str = "#227a87") -> str:
    if not points:
        return '<p class="missing">Datos no disponibles.</p>'
    hi = max(v for _, v in points) or 1
    xhi = max(x for x, _ in points) or 1
    coords = " ".join(f"{70 + 600*x/xhi:.1f},{190 - 145*v/hi:.1f}" for x, v in points)
    dots = "".join(f'<circle cx="{70 + 600*x/xhi:.1f}" cy="{190 - 145*v/hi:.1f}" '
                   f'r="6" fill="{color}"/>' for x, v in points)
    return (f'<svg viewBox="0 0 760 235" role="img" aria-label="Evolución por iteración">'
            '<line x1="70" y1="190" x2="680" y2="190" stroke="#758785"/>'
            '<line x1="70" y1="35" x2="70" y2="190" stroke="#758785"/>'
            f'<text x="0" y="43" class="axis">{_esc(_num(hi, 3))}</text>'
            f'<text x="70" y="220" class="axis">0</text><text x="645" y="220" '
            f'class="axis">k={xhi}</text><polyline points="{coords}" fill="none" '
            f'stroke="{color}" stroke-width="4"/>{dots}</svg>')


def _paired_bars(pairs: list[dict]) -> str:
    top = max(max(p["mse_b0"], p["mse_b1"]) for p in pairs) or 1
    out = [f'<svg viewBox="0 0 760 {len(pairs) * 76 + 20}" role="img" '
           'aria-label="MSE D pareada por semilla y condición">']
    for index, pair in enumerate(pairs):
        y = 12 + index * 76
        label = f'{pair["seed"]}/{pair["condition"]} k{pair["iteration"]}'
        out.append(f'<text x="0" y="{y + 30}" class="axis">{_esc(label)}</text>')
        for offset, arm, color in ((0, "mse_b0", "#227a87"), (31, "mse_b1", "#bb6c38")):
            value = pair[arm]
            width = 390 * value / top
            out.append(f'<rect x="165" y="{y + offset}" width="{width:.1f}" height="24" '
                       f'rx="4" fill="{color}"/><text x="{175 + width:.1f}" '
                       f'y="{y + offset + 18}" class="value">β={0 if arm.endswith("0") else 1} '
                       f'{_num(value, 5)}</text>')
    out.append("</svg>")
    return "".join(out)


def _median_series(campaign: Campaign, batch: str, value: str,
                   arm: int | None = None) -> tuple[list[tuple[int, float]], int]:
    grouped: dict[int, list[float]] = {}
    runs = set()
    for record in campaign.records:
        if arm is not None and not record["run_id"].endswith(f"-b{arm}"):
            continue
        entry = record.get(batch, {}).get("post", {})
        metric = entry.get(value)
        if _finite(metric):
            grouped.setdefault(record["iteration"], []).append(metric)
            runs.add(record["run_id"])
    return [(k, statistics.median(values)) for k, values in sorted(grouped.items())], len(runs)


def _status_label(status: str) -> str:
    return {
        "completed": "completado",
        "failed": "interrumpido",
        "ready": "en pausa",
        "running": "en curso",
        "incomplete": "incompleto",
    }.get(status, status)


def _overview(campaigns: list[Campaign]) -> str:
    labels = {
        "P0": ("Piloto inicial de infraestructura Q/A/B", "Corridas técnicas completas; no evalúa rentabilidad."),
        "P1": ("Comparó 2 y 4 épocas del crítico", "Reducción post-A en 3/3 semillas sobre el mismo lote; no prueba generalización."),
        "P2": ("Introdujo D independiente durante más iteraciones", "Interrumpido; no hay decisión global evaluable."),
        "P2R": ("Repitió P2 con supervisor persistente", "Resultado numérico review; solo diagnóstico descriptivo por discrepancia de metadato."),
        "P3": ("Compara pérdida del crítico β=0 frente a β=1", "Diagnóstico de desarrollo; su estado se lee del ledger al generar."),
    }
    cards = []
    for c in campaigns:
        title, message = labels[c.name]
        status = _status_label(c.state["status"])
        if c.name == "P2R":
            status += f' · {c.closure["numerical_technical_decision"]} numérico'
        cards.append(f'<article class="card"><span class="tag">{c.name}</span><h3>{_esc(title)}</h3>'
                     f'<p class="status">{_esc(status)} · {c.complete_runs}/{CAMPAIGNS[c.name][1]} '
                     f'corridas completas</p><p>{_esc(message)}</p></article>')
    return '<section id="inicio" aria-label="Resumen de campañas"><div class="cards">' + "".join(cards) + (
        '</div><p class="callout">Estos pilotos usan entrenamiento 2018–2022. No demuestran '
        'rentabilidad, superioridad frente a C0, generalización temporal ni cumplimiento '
        'poblacional de CVaR. No se muestran resultados fuera de muestra.</p></section>')


def _campaign_section(c: Campaign) -> str:
    folder, planned, _, _ = CAMPAIGNS[c.name]
    prefix = f"artifacts/{folder}"
    source = f"{prefix}/ledger.jsonl"
    units = c.units
    duration = [u.get("seconds", 0) for u in units]
    total_s = sum(duration)
    learning = sum(u.get("resources", {}).get("trajectories", 0) for u in units)
    diagnostic = sum(u.get("resources", {}).get("diagnostic_trajectories", 0) for u in units)
    progress = _figure("Avance de corridas", _bars([("completas", c.complete_runs),
                       ("previstas", planned)], max_value=planned), metric="corridas completas",
                       unit="corridas", population="ledger de campaña",
                       n=f"{c.complete_runs}/{planned}", source=source,
                       limit="una corrida parcial no cuenta como completa")
    time = _figure("Tiempo por unidad aceptada", _bars([("mediana", statistics.median(duration) if duration else 0),
                   ("máximo", max(duration, default=0))], color="#bb6c38"),
                   metric="segundos de unidad aceptada", unit="s", population="unidades aceptadas",
                   n=f"{len(units)} unidades; {c.complete_runs} corridas completas", source=source,
                   limit=f"suma aceptada: {_num(total_s, 1)} s; no equivale al cargo global diario")
    resources = _figure("Trayectorias registradas", _bars([("aprendizaje", learning),
                        ("D", diagnostic)], color="#645f9b"),
                        metric="trayectorias registradas", unit="trayectorias",
                        population="unidades aceptadas, entrenamiento 2018–2022",
                        n=f"{len(units)} unidades; {c.complete_runs} corridas completas", source=source,
                        limit="D es diagnóstico de desarrollo; no actualiza pesos")
    content = [progress, time, resources]
    telemetry = [item for report in c.reports.values()
                 for item in report.get("telemetry", []) if item.get("status") == "complete"]
    rss = [item["rss_peak_bytes"] / (1024**2) for item in telemetry
           if _finite(item.get("rss_peak_bytes"))]
    if rss:
        content.append(_figure("Memoria de proceso observada",
                       _bars([("mediana", statistics.median(rss)), ("máximo", max(rss))],
                             color="#645f9b"),
                       metric="RSS máximo por fase", unit="MiB",
                       population="fases completas de unidades aceptadas",
                       n=f"{len(telemetry)} fases; {len(c.reports)} corridas con reporte",
                       source=f"{prefix}/<run>/unit-<última aceptada>.json → report.telemetry",
                       limit="RSS del proceso; no equivale a memoria disponible del host"))
    d_times = [item["wall_seconds"] for item in telemetry if item.get("phase") == "D"
               and _finite(item.get("wall_seconds"))]
    if d_times:
        content.append(_figure("Costo de D por unidad", _bars([
            ("mediana", statistics.median(d_times)), ("máximo", max(d_times))],
            color="#bb6c38"), metric="tiempo de fase D completa", unit="s",
            population="D de entrenamiento, trayectoria diagnóstica",
            n=f"{len(d_times)} fases D en {len(c.reports)} corridas",
            source=f"{prefix}/<run>/unit-<última aceptada>.json → report.telemetry",
            limit="medición local; no extrapolar automáticamente a otra máquina"))
    if c.name == "P1" and c.closure:
        seeds = c.closure.get("primary", {}).get("seeds", [])
        if seeds:
            rows = [(str(s["seed"]), 100 * s["reduction"]) for s in seeds]
            content.append(_figure("Crítico: reducción post-A con 4 vs 2 épocas",
                           _bars(rows, max_value=100, color="#44806b", suffix=" %"),
                           metric="(MSE₂ − MSE₄)/MSE₂", unit="%",
                           population="A completo fijo, primera actualización, mismos targets",
                           n=f"{len(seeds)} bloques de semilla independientes",
                           source=c.closure_path or "", limit="C0/C5/C10 repiten el mismo contraste inicial"))
    if c.name in {"P0", "P1"}:
        grouped: dict[str, dict[int, list[float]]] = {}
        for run_id, report in c.reports.items():
            arm = run_id[-2:] if c.name == "P1" else "all"
            for entry in report.get("stability", []):
                if c.name == "P0":
                    eligible = entry.get("phase") == "targets"
                    value = entry.get("critic_mc_mse_before")
                else:
                    eligible = (entry.get("phase") == "fixed_A"
                                and entry.get("measurement") == "after_critic"
                                and entry.get("scope") == "full_A_fixed_targets")
                    value = entry.get("mse")
                if eligible and _finite(value):
                    grouped.setdefault(arm, {}).setdefault(entry["iteration"], []).append(value)
        for arm, values_by_k in sorted(grouped.items()):
            series = [(k, statistics.median(values)) for k, values in
                      sorted(values_by_k.items())]
            n_arm = sum(run_id.endswith(f"-{arm}") for run_id in c.reports) if arm != "all" \
                else len(c.reports)
            title_arm = f" ({arm})" if arm != "all" else ""
            population_arm = f", brazo {arm}" if arm != "all" else ""
            content.append(_figure(f"Crítico: MSE sobre A por iteración{title_arm}",
                           _line(series),
                           metric="MSE MC antes de ajustar" if c.name == "P0" else
                           "MSE MC después de ajustar", unit="retorno logarítmico²",
                           population=f"A de entrenamiento{population_arm}; "
                           + ("pre-ajuste" if c.name == "P0" else "post-ajuste, A fijo"),
                           n=f"{n_arm} corridas con reporte",
                           source=f"{prefix}/<run>/unit-<última aceptada>.json → report.stability",
                           limit="P0 pre y P1 post son momentos distintos; P1 k≥1 puede usar rutas diferentes"))
    if c.name in {"P2", "P2R", "P3"}:
        for arm in ((0, 1) if c.name == "P3" else (None,)):
            for batch in ("A", "D"):
                for metric in ("mse", "z"):
                    series, n = _median_series(c, batch, metric, arm)
                    label = f" β={arm}" if arm is not None else ""
                    content.append(_figure(f"Crítico {batch}{label}: {metric.upper()} post actualización",
                               _line(series, color="#227a87" if batch == "A" else "#bb6c38"),
                               metric="MSE" if metric == "mse" else "MSE del predictor cero (Z)",
                               unit="retorno logarítmico²",
                               population=(f"{batch} de entrenamiento"
                                           if batch == "A" else "D nuevo del histórico de entrenamiento")
                               + (f", brazo β={arm}, política propia" if arm is not None else ""),
                               n=f"{n} corridas con unidades completas",
                               source=f"{prefix}/<run>/unit-<última aceptada>.json → report.diagnostic.records",
                               limit="mediana por iteración; composición de corridas puede variar"))
        missing = ('La comparación A vs D no es un contraste pareado sobre los mismos '
                   'objetivos: son lotes distintos. Se muestran por separado.')
        content.append(f'<p class="note">{missing}</p>')
    else:
        content.append('<p class="missing">No hay lote D en esta campaña. No se dibuja una '
                       'comparación A–D.</p>')
    risk_rows = []
    risk_groups = {}
    for run_id, report in c.reports.items():
        match = RUN_RE.fullmatch(run_id)
        group = match[2] + (f" β={run_id[-1]}" if c.name == "P3" else "")
        for audit in report.get("audits", []):
            if _finite(audit.get("f_b")):
                risk_rows.append(audit)
                risk_groups.setdefault(group, []).append(audit)
    if risk_rows:
        f_rows = [(group, statistics.median(a["f_b"] for a in audits))
                  for group, audits in sorted(risk_groups.items())]
        lambda_rows = [(group, statistics.median(a["lambda_after"] for a in audits
                       if _finite(a.get("lambda_after"))))
                       for group, audits in sorted(risk_groups.items())]
        content.append(_figure("Riesgo: auditoría B frente a cota",
                       _bars([*f_rows, ("cota d", RISK_BOUND)], color="#a45365"),
                       metric="F_B(η_Q) y d", unit="pérdida logarítmica",
                       population="B de entrenamiento, por condición/brazo",
                       n=f"{len(c.reports)} corridas con reporte; {len(risk_rows)} auditorías",
                       source=f"{prefix}/<run>/unit-<última aceptada>.json → report.audits",
                       limit="mediana descriptiva; no establece restricción poblacional"))
        content.append(_figure("Riesgo: multiplicador posterior",
                       _bars(lambda_rows, color="#7b5e9b"),
                       metric="λ posterior a B", unit="multiplicador sin dimensión",
                       population="auditorías B de entrenamiento, por condición/brazo",
                       n=f"{len(risk_rows)} auditorías en {len(c.reports)} corridas",
                       source=f"{prefix}/<run>/unit-<última aceptada>.json → report.audits",
                       limit="no compartir escala con pérdida logarítmica"))
    else:
        content.append('<p class="missing">Sin auditorías B completas; no se dibuja riesgo.</p>')
    if c.name == "P3":
        pairs = p3_pairs(c)
        latest: dict[tuple[int, str], dict] = {}
        for pair in pairs:
            key = (pair["seed"], pair["condition"])
            if key not in latest or pair["iteration"] > latest[key]["iteration"]:
                latest[key] = pair
        if latest:
            selected = list(latest.values())
            content.append(_figure("P3: MSE D en pares completos", _paired_bars(selected),
                           metric="MSE D post por brazo", unit="retorno logarítmico²",
                           population="D independiente de cada brazo; última iteración común",
                           n=f"{len(selected)} pares semilla-condición",
                           source=f"{prefix}/<run-b0,b1>/unit-<aceptada>.json → diagnostic.records",
                           limit="políticas y objetivos propios desde k≥1; no es contraste causal"))
            rows = []
            for pair in selected:
                tag = f"{pair['seed']}/{pair['condition']} k{pair['iteration']}"
                rows.append(f'<tr><td>{_esc(tag)}</td><td>{_num(pair["mse_b0"], 5)}</td>'
                            f'<td>{_num(pair["mse_b1"], 5)}</td>'
                            f'<td>{_num(pair["delta_mse"], 5)}</td></tr>')
            table = ('<table><thead><tr><th>Semilla/condición/iteración</th><th>β=0</th>'
                     '<th>β=1</th><th>Δ=β1−β0</th></tr></thead><tbody>' + "".join(rows)
                     + '</tbody></table>')
            content.append(_figure("P3: pares disponibles, última iteración común", table,
                           metric="MSE D post; diferencia β1−β0", unit="retorno logarítmico²",
                           population="D de cada brazo, políticas y objetivos propios desde k≥1",
                           n=f"{len(latest)} pares semilla-condición; {len(pairs)} pares-iteración",
                           source=f"{prefix}/<run-b0,b1>/unit-<aceptada>.json → diagnostic.records",
                           limit="solo unidades completas; parear identidad no iguala trayectorias ni prueba causalidad"))
        else:
            content.append('<p class="missing">Comparación pareada no disponible: faltan '
                           'ambas unidades completas para la misma semilla, condición e iteración.</p>')
    if c.name == "P2":
        content.append('<p class="callout">P2 quedó interrumpido. Las unidades aceptadas son '
                       'descriptivas; la unidad parcial y la campaña no tienen resultado global evaluable.</p>')
    if c.name == "P2R":
        decision = _esc(c.closure["numerical_technical_decision"])
        content.append(f'<p class="callout">Decisión numérica: <b>{decision}</b>. Los 99 reportes '
                       'conservan <code>market_training_executed=false</code>; faltó la verificación '
                       'previa exigida. Solo diagnóstico descriptivo de desarrollo.</p>')
    provenance = "".join(f"<li><code>{_esc(s)}</code></li>" for s in c.sources)
    checks = "".join(f"<li>{_esc(s)}</li>" for s in c.checks)
    heading = (f'<section id="{c.name.lower()}" class="campaign"><div class="section-head">'
               f'<span class="tag">{c.name}</span><h2>{c.name} · {_esc(_status_label(c.state["status"]))}'
               f'</h2></div><p class="meta">Ledger SHA-256: <code>{c.ledger_sha256}</code> '
               f'· corte UTC: {_esc(c.state.get("updated_utc", "—"))}</p>')
    return (heading + '<div class="grid">' + "".join(content) + '</div>'
            f'<details id="sources-{c.name.lower()}"><summary>Procedencia e integridad '
            f'({len(c.sources)} archivos)</summary><ul>{provenance}</ul>'
            f'<ul>{checks}</ul></details></section>')


def render_report(campaigns: list[Campaign]) -> str:
    cut = max((str(c.state.get("updated_utc", "")) for c in campaigns), default="")
    css = """
    :root{font-family:system-ui,DejaVu Sans,sans-serif;color:#19312e;background:#f5f6f2}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-size:1rem;line-height:1.55}
    header{background:#123c3c;color:#fff;padding:2rem 1.5rem 1.7rem}
    .header-inner{max-width:1280px;margin:auto}
    header h1{font-size:clamp(2.3rem,3.5vw,3.2rem);line-height:1.12;margin:0 0 .55rem}
    header p{max-width:74ch;line-height:1.6;margin:.3rem 0;color:#eef5ef}
    header .cut{font-size:.9rem;color:#c8dfd9;margin-top:.75rem}
    nav{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1.15rem}
    nav a{color:#fff;text-decoration:none;background:#245b58;padding:.35rem .8rem;border-radius:7px;font-weight:650}
    nav a:hover,nav a:focus-visible{background:#3b746c;outline:2px solid #cde9dc}
    main{max-width:1280px;margin:auto;padding:1.5rem}
    section{margin:1.5rem 0 3rem}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:1rem}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.4rem;align-items:stretch}
    .grid>.note,.grid>.missing,.grid>.callout{align-self:start}
    .card,figure,details{background:#fff;border:1px solid #cbd8d1;border-radius:12px;padding:1.5rem;box-shadow:0 2px 8px #15342b0a}
    .card h3{font-size:1.35rem;line-height:1.25;margin:.75rem 0}.card p{margin:.7rem 0;line-height:1.55}
    .tag{display:inline-block;background:#d8e7d6;color:#154735;padding:.24rem .6rem;border-radius:5px;font-weight:750}
    .status{font-weight:750;color:#84452b;font-variant-numeric:tabular-nums}
    .callout{background:#fff2d8;border-left:5px solid #bc742f;padding:1.1rem 1.3rem;line-height:1.6}
    .note,.missing{background:#e8eef0;padding:1.1rem;border-radius:8px;line-height:1.6}
    .missing{border:1px dashed #79949b}
    .section-head{display:flex;align-items:center;gap:1rem}.section-head h2{margin:0;font-size:1.8rem}
    .campaign{border-top:2px solid #c9d9ce;padding-top:2.1rem}
    .meta{overflow-wrap:anywhere;color:#4b6059;font-size:.93rem;margin:.5rem 0 1.25rem}
    figure{margin:0;min-width:0}figure h4{font-size:1.25rem;line-height:1.3;margin:0 0 1.2rem}
    svg{display:block;width:100%;height:auto;overflow:visible}
    .axis{font-size:19px;fill:#304744}.value{font-size:18px;fill:#19312e;font-weight:750}
    .value-in{font-size:18px;fill:#fff;font-weight:750}
    figcaption{color:#344b44;margin-top:1.1rem;overflow-wrap:anywhere;line-height:1.55}
    figcaption p{margin:.4rem 0}.chart-facts{font-size:1rem;color:#19312e}
    .chart-context{font-size:.96rem}.chart-source{font-size:.9rem;border-top:1px solid #dce5de;padding-top:.65rem}
    .chart-limit{font-size:.92rem;color:#52625b}
    code{overflow-wrap:anywhere;font-size:.92em}details{margin-top:1.2rem}summary{font-weight:650;cursor:pointer}
    table{border-collapse:collapse;width:100%;font-size:.96rem;font-variant-numeric:tabular-nums}
    td,th{text-align:left;border-bottom:1px solid #dce4dc;padding:.65rem .5rem}
    th{background:#edf3ed}td{white-space:nowrap}
    @media(max-width:900px){.grid{grid-template-columns:1fr}main{padding:1rem}}
    @media(max-width:600px){.cards{grid-template-columns:1fr}.card,figure,details{padding:1.1rem}table{font-size:.82rem}}
    @media print{header{padding:1rem}main{padding:.5rem}.card,figure,details{break-inside:avoid;box-shadow:none}}
    """
    nav = "".join(f'<a href="#{c.name.lower()}">{c.name}</a>' for c in campaigns)
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Resultados experimentales · tesis BTC</title><style>' + css +
            '</style></head><body><header><div class="header-inner">'
            '<h1>Resultados experimentales</h1><p>Pilotos P0–P3 sobre entrenamiento '
            '2018–2022. Son diagnósticos de desarrollo, sin evaluación fuera de muestra.</p>'
            f'<p class="cut">Corte máximo de ledger UTC {_esc(cut)}</p>'
            f'<nav aria-label="Campañas"><a href="#inicio">Resumen</a>{nav}</nav>'
            '</div></header><main>' + _overview(campaigns) +
            "".join(_campaign_section(c) for c in campaigns) +
            '</main></body></html>')


def build(source_root: Path, output: Path) -> list[Campaign]:
    source_root = Path(source_root).resolve()
    output = Path(output).resolve()
    if output.is_relative_to(source_root / "artifacts") or output.is_relative_to(source_root / "docs/evidence"):
        raise ValueError("la salida debe estar fuera de los artefactos originales")
    campaigns = [load_campaign(source_root, name) for name in CAMPAIGNS]
    document = render_report(campaigns)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    temp.write_text(document, encoding="utf-8")
    temp.replace(output)
    return campaigns
