"""Export an offline Spanish dashboard from an explicit evidence allowlist."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CROSS = "docs/evidence/p3-cross-diagnostic/results.json"
P1 = "docs/evidence/p1-execution/closure-checks.json"
CAMPAIGNS = {
    "P0": (
        "p0-approved-v1",
        27,
        "docs/hitos/P0-diagnostico.md",
        "¿Funcionan el crítico y la activación del riesgo?",
        "C0, C5 y C10 · K=2 · dos épocas del crítico",
        "El error sobre A disminuyó, pero siguió por encima del predictor cero. Las advertencias no demostraron divergencia.",
        "Motivó comparar dos y cuatro épocas en P1.",
    ),
    "P1": (
        "p1-approved-v1",
        54,
        "docs/hitos/P1-epocas-critico.md",
        "¿Cuatro épocas mejoran el ajuste inicial del crítico sobre A?",
        "Dos frente a cuatro épocas · C0/C5/C10 · K=2",
        "El criterio de reducción del 20 % se cumplió en tres bloques de semillas. Es ajuste sobre el mismo A usado para aprender.",
        "Cuatro épocas quedaron como candidata de desarrollo; no como configuración óptima.",
    ),
    "P2": (
        "p2-approved-v1",
        99,
        "docs/hitos/P2-ejecucion-interrumpida.md",
        "¿Cómo evoluciona el crítico y qué ocurre sobre D nuevo?",
        "C0/C5/C10 · K=10 · cuatro épocas · D separado",
        "Interrumpido durante una unidad. Los criterios completos no son evaluables; solo se muestran unidades aceptadas.",
        "Se conservó el fallo y se preparó supervisión independiente para P2R.",
    ),
    "P2R": (
        "p2r-approved-v2",
        99,
        "docs/hitos/P2R-ejecucion-historica-v2.md",
        "¿Cómo evoluciona el ajuste sobre A y D con supervisión durable?",
        "Nueve corridas nuevas · C0/C5/C10 · K=10",
        "Resultado numérico review. El marcador market_training_executed quedó false en los 99 reportes; la adjudicación conserva alcance descriptivo.",
        "No se convalidó el preflight retrospectivamente. Se motivó el diagnóstico del crítico de P3.",
    ),
    "P3": (
        "p3-approved-v1",
        198,
        "docs/hitos/P3-diagnostico-cruzado-D.md",
        "¿Cómo difieren ambos críticos al evaluarlos sobre el mismo lote D?",
        "β=0: MSE · β=1: MSE + mean(V²) · C0/C5/C10",
        "P3 conserva review. El signo de la diferencia entre críticos se mantiene en ambos D y entre condiciones de cada semilla.",
        "El cruce es diagnóstico de desarrollo; no cambia la regla original ni selecciona checkpoints.",
    ),
    "WF05": (
        "oos-v12-wf-cost-only-05",
        22,
        "docs/hitos/OOS-v1-2-costo-cortes-05-cierre-incomplete.md",
        "¿Cuánto cuesta entrenar los dos cortes de desarrollo?",
        "C10 · cortes 2021 y 2022 previstos",
        "Cierre metodológico incomplete. Solo se completó el corte 2021; el ledger técnico permanece ready.",
        "No reanudar WF05. El costo histórico del corte 2022 sigue pendiente en una raíz nueva.",
    ),
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def summarize_runs(state: dict, directory: str, read) -> list[dict]:
    """Use the last accepted frontier per run, never a pending unit."""
    grouped = {}
    for unit in state["units"]:
        grouped.setdefault(unit["run_id"], []).append(unit)
    result = []
    for run_id, units in grouped.items():
        latest = units[-1]
        number = int(Path(latest["checkpoint"]).name.split("-")[-1])
        relative = f"artifacts/{directory}/{run_id}/unit-{number}.json"
        payload = read(relative)
        report = payload["report"]
        expected = latest.get("report_sha256")
        if expected and digest((ROOT / relative).read_bytes()) != expected:
            raise ValueError(f"Reporte aceptado alterado: {relative}")
        settings = report["settings"]
        fixed = [
            row
            for row in report.get("stability", [])
            if row.get("phase") == "fixed_A" and row.get("measurement") == "after_critic"
        ]
        audit = report.get("audits", [])
        resources = {}
        for unit in units:
            for key, value in unit.get("resources", {}).items():
                resources[key] = resources.get(key, 0) + value
        result.append(
            dict(
                run=run_id,
                condition=report["condition"],
                seed=settings["seed"],
                settings=settings,
                beta=settings.get("critic_beta", 0),
                accepted_units=len(units),
                complete=number == settings["iterations"],
                accepted_iteration=number,
                seconds=sum(unit["seconds"] for unit in units),
                rss_mib=max(unit.get("supervisor", {}).get("rss_peak_bytes", 0) for unit in units)
                / 1024**2,
                resources=resources,
                first_utc=units[0].get("end_utc"),
                last_utc=latest.get("end_utc"),
                source=relative,
                report_hash_pinned=bool(expected),
                boundary=report.get("boundary"),
                marker=report.get("market_training_executed"),
                mse_a_post=fixed[-1]["mse"] if fixed else None,
                mse_a_iteration=fixed[-1]["iteration"] if fixed else None,
                audit={
                    key: audit[-1].get(key)
                    for key in ("iteration", "eta", "f_b", "rho_b", "lambda_before", "lambda_after")
                }
                if audit
                else {},
            )
        )
    return result


def load_data(root: Path = ROOT) -> dict:
    """Read only pinned small evidence files, accepted ledgers and accepted reports."""
    sources = {}

    def read(relative: str):
        path = root / relative
        raw = path.read_bytes()
        sources[relative] = {
            "sha256": digest(raw),
            "url": path.as_uri(),
            "commit": git("log", "-1", "--format=%h", "--", relative)
            if relative.startswith("docs/")
            else "artefacto local fuera de Git",
        }
        return json.loads(raw)

    for evidence in (
        "docs/hitos/H4-agentes-recolector.md",
        "docs/protocols/P2R-adjudicacion-metadato-v1.md",
        "docs/protocols/P0-approved-v1.json",
        "docs/hitos/H3-contrato-ADR002.md",
        "docs/hitos/H1-preparacion-segmentada.md",
        "docs/proposals/cierre-pilotos-evaluacion-fuera-muestra-v1-2.md",
        "docs/hitos/OOS-v1-2-costo-2022-orquestador-sintetico.md",
    ):
        path = root / evidence
        sources[evidence] = {
            "sha256": digest(path.read_bytes()),
            "url": path.as_uri(),
            "commit": git("log", "-1", "--format=%h", "--", evidence),
        }
    cross = read(CROSS)
    closure_path = "docs/evidence/p3-market-2026-10-13/final-closure.json"
    closure = read(closure_path)
    if sources[closure_path]["sha256"] != cross["source_hashes"]["closure_sha256"]:
        raise ValueError("El cierre P3 no coincide con el diagnóstico cruzado")
    p1 = read(P1)
    campaigns = {}
    for name, (
        directory,
        planned,
        report,
        question,
        conditions,
        result,
        decision,
    ) in CAMPAIGNS.items():
        report_path = root / report
        raw_report = report_path.read_bytes()
        sources[report] = {
            "sha256": digest(raw_report),
            "url": report_path.as_uri(),
            "commit": git("log", "-1", "--format=%h", "--", report),
        }
        path = root / "artifacts" / directory / "ledger.jsonl"
        rows = []
        runs = []
        status = "Sin evidencia disponible"
        if path.is_file():
            raw = path.read_bytes()
            state = json.loads(raw.splitlines()[-1])
            relative = str(path.relative_to(root))
            sources[relative] = {
                "sha256": digest(raw),
                "url": path.as_uri(),
                "commit": "artefacto local fuera de Git",
            }
            if name == "P3" and digest(raw) != cross["source_hashes"]["ledger_sha256"]:
                raise ValueError("Ledger P3 distinto del diagnóstico aceptado")
            if "state_hash" in state:
                payload = {k: v for k, v in state.items() if k != "state_hash"}
                if (
                    digest(json.dumps(payload, sort_keys=True, allow_nan=False).encode())
                    != state["state_hash"]
                ):
                    raise ValueError(f"Ledger corrupto: {name}")
            status = state["status"]
            for unit in state["units"]:
                seconds = unit["seconds"]
                if not math.isfinite(seconds) or seconds < 0:
                    raise ValueError("Tiempo inválido")
                rows.append(
                    {
                        "run": unit["run_id"],
                        "unit": unit.get("unit", 0 if unit["kind"] == "q0" else None),
                        "seconds": seconds,
                        "rss_mib": unit.get("supervisor", {}).get("rss_peak_bytes", 0) / 1024**2,
                    }
                )
            runs = summarize_runs(state, directory, read)
        campaigns[name] = dict(
            status=status,
            planned=planned,
            accepted=len(rows),
            rows=rows,
            runs=runs,
            source=report,
            ledger=f"artifacts/{directory}/ledger.jsonl",
            question=question,
            conditions=conditions,
            result=result,
            decision=decision,
            scope="Medición de costo" if name == "WF05" else "Piloto de desarrollo",
        )
    if campaigns["P3"]["accepted"] != closure["accepted_units"]:
        raise ValueError("Cobertura P3 incompatible con el cierre")
    for pair in cross["pairs"]:
        pair["risk"] = {}
        for arm in (0, 1):
            coverage = pair["coverage"][f"D_b{arm}"]
            if coverage["observations_evaluated"] != coverage["observations_expected"]:
                raise ValueError("D incompleto")
            report = f"artifacts/p3-approved-v1/{coverage['run_id']}/unit-10.json"
            if (root / report).exists():
                original = read(report)
                if sources[report]["sha256"] != coverage["report_sha256"]:
                    raise ValueError("Reporte P3 alterado")
                audit = original["report"]["audits"][-1]
                pair["risk"][str(arm)] = {
                    k: audit[k]
                    for k in ("iteration", "eta", "f_b", "rho_b", "lambda_before", "lambda_after")
                }
                pair["risk"][str(arm)]["source"] = report
                if original["report"]["boundary"] != "after_dual_and_D":
                    raise ValueError("Unidad P3 parcial")
        validate_pair(pair)
    return dict(
        campaigns=campaigns,
        cross=cross["pairs"],
        p3_decision=closure["decision"],
        p1=p1["independent_seeds"],
        sources=sources,
        branch=git("branch", "--show-current"),
        commit=git("rev-parse", "HEAD"),
    )


def validate_pair(pair: dict) -> None:
    """Reject incomplete cells or mixed target denominators before plotting."""
    for arm in (0, 1):
        coverage = pair["coverage"][f"D_b{arm}"]
        if coverage["observations_evaluated"] != coverage["observations_expected"]:
            raise ValueError("D incompleto")
        zero = []
        for critic in (0, 1):
            cell = pair["cells"][f"critic_b{critic}_on_D_b{arm}"]
            if cell["count"] != 34560 or not math.isclose(
                cell["mse"], cell["sse"] / cell["count"], rel_tol=1e-12
            ):
                raise ValueError("Agregación MSE incompatible")
            if not math.isclose(cell["zero_mse"], cell["target_sq"] / cell["count"], rel_tol=1e-12):
                raise ValueError("Referencia cero incompatible")
            zero.append(cell["target_sq"])
        if zero[0] != zero[1]:
            raise ValueError("Los críticos no comparten objetivos D")


def build(output: Path) -> Path:
    output = output.resolve()
    if not output.is_relative_to(ROOT / "reports"):
        raise ValueError("La salida debe quedar en reports/, fuera de los artefactos originales")
    data = load_data()
    template = Path(__file__).with_name("dashboard.html").read_text()
    html = template.replace(
        "__DATA__", json.dumps(data, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    output.with_name("datos.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    )
    return output
