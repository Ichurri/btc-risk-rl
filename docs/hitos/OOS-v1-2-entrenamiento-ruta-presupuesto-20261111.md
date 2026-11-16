# OOS v1.2: corrección de ruta y auditoría de `wf-2021`

**Fecha:** 11/11/2026, `America/La_Paz`. **Alcance:** corrección prospectiva,
auditoría de registros existentes y programación del siguiente perfil. No
se lanzó una unidad histórica durante este hito.

## Causa y corrección

El protocolo congelado almacena las tres raíces con prefijo `artifacts/`.
`CAMPAIGNS` añadía otro prefijo, por lo que el supervisor de la sesión del
11/11 tomó `artifacts/artifacts/shared-pilot-budget/global.lock`, mientras
la preparación usó `artifacts/shared-pilot-budget/global.lock`. La prueba
de regresión falló antes del cambio: mostró las tres rutas dobles y que un
segundo proceso podía adquirir el bloqueo independiente.

El código resuelve ahora cada raíz como `ROOT / nombre_congelado`. Para
`wf-2021`, una excepción **solo de lectura** reconoce el ledger ya cerrado
en su ubicación original. La excepción fija las huellas del ledger y del
último checkpoint, verifica la cadena y el estado `completed`, y permite
seleccionar `wf-2022` sin crear la raíz canónica de 2021. El comando directo
rechaza repetir ese perfil. `wf-2022` y el perfil principal usarán sus
raíces canónicas y el mismo bloqueo global que la preparación. El informe
automático reconoce la ubicación histórica sin moverla.

La nueva aprobación está en
[`OOS-v1-2-training-approval-20261111-v2.json`](../protocols/OOS-v1-2-training-approval-20261111-v2.json),
SHA-256 `ef601eb95df48e3f3376b11d61eb64328914b225c43927c7e8baa12142f5c806`.
Fija el código `1dcff09`, SHA-256
`662edcea4367ea8a6f470cbb0a64ab25f0827585f55f0ccfc1fc7d159aa70177`;
el protocolo congelado conserva SHA-256
`0651f396f3157eaa5abd6bb7faf7ec1c6463210d255fa2fbd8a932e2999870a0`.
La aprobación previa SHA-256
`2a54cf3084b366d11750790e907ae36b826778de47313de060b5a4ee6324dba2`
permanece como evidencia histórica, sin editar.

## Integridad de la sesión original

La [auditoría reproducible](../evidence/oos-v12-training-root-fix-20261111/budget-audit.json)
verificó el ledger SHA-256
`811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`,
su cadena de 302 estados, 99 checkpoints, 99 reportes y 99 solicitudes.
El último `state.pt` conserva SHA-256
`864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
El JSON de auditoría tiene SHA-256
`30097f8e8e73661da0c97813fdad8af56990bdafcb2db3b2e285b586a686e827`.
Esta verificación de integridad **no equivale** a aprobar el uso analítico
de las corridas.

## Reconstrucción del presupuesto compartido

Se reprodujo la regla `required`: antes de cada unidad, 1,5 veces el máximo
de `work_seconds` previos de la misma condición y tipo, o el tope inicial
de 1.800 s para Q0 y 2.700 s para iteración. Se usó el instante `start`
del ledger, que ocurre **después** de `admit()`: si una unidad cabe incluso
en ese instante posterior, habría cabido en el instante de admisión. El
plazo contrafactual aplica 10.800 s desde el comienzo de la preparación,
menos la reserva de cierre de 2.700 s y el límite de las 09:00.

Con otros cargos registrados iguales a cero, **99/99 unidades habrían
cabido** en el presupuesto común. El menor margen de admisión fue
**1.128,211 s**, en `run-08-C5-b0`, unidad 10; el menor margen hasta el
fin de cálculo fue **1.163,955 s** y hasta el plazo de cierre,
**3.858,131 s**. La [captura del preflight](../evidence/oos-v12-training-root-fix-20261111/preflight-summary.json)
mostró cero cargos ajenos y ninguna campaña activa; el scanner final solo
mostró el cargo de 6.942,163 s de la bitácora de la propia sesión. Las 99
filas, estimaciones y márgenes figuran en el JSON, sin selección por
resultados.

**Incertidumbre:** el instante exacto de `admit()` no se registró. El uso
de `start` proporciona una cota conservadora favorable en las 99 filas,
pero el bloqueo equivocado no puede demostrar ausencia de intentos
concurrentes no registrados. La reconstrucción supone que no hubo otros
cargos registrados después del preflight; el scanner de cierre no mostró
ninguno. No se declara retrospectivamente que el bloqueo compartido se
hubiera aplicado durante la sesión original.

## Decisión de uso y continuación

`wf-2021` queda **íntegro y técnicamente completo**, con uso limitado por
ahora a descripción del entrenamiento, tiempos e integridad. Su empleo
como cumplimiento estricto del contrato de supervisión queda **pendiente
de adjudicación metodológica**. No se repiten sus nueve corridas ni se
mueven sus artefactos. El protocolo clasifica los cortes *walk-forward*
como comprobación de integridad y cobertura de desarrollo, sin selección
financiera. `wf-2022` usa otra fuente y un estado inicial propio; no carga
pesos ni checkpoints de `wf-2021`. Por ello puede continuar en el orden
congelado aun con la decisión analítica de 2021 pendiente. El contraste
confirmatorio y el acceso a 2023/2024–2025 siguen cerrados.

La [captura de programación](../evidence/oos-v12-training-root-fix-20261111/schedule.json)
registra `oos-v12-training.timer` activo para **12/11/2026 01:00** y
`oos-v12-training.service` inactivo, `Restart=no`. El servicio repetirá
suite, Ruff y preflight vigilado; solo iniciará Q0 si CA, memoria, disco,
gestor, huellas, fuente exclusiva de entrenamiento y saldo con reserva
están conformes. No se usará la captura del 11/11 para admitir una unidad
el 12/11. El timer de restauración de la suspensión sigue previsto para
16/11 a las 09:05.
Las tres evidencias JSON tienen sus huellas en
[`SHA256SUMS`](../evidence/oos-v12-training-root-fix-20261111/SHA256SUMS).

La suite ejecutada manualmente para la corrección duró 539,80 s; ese
tiempo de desarrollo no aparece en el contador automático de la sesión
histórica de 6.942,163 s. **No se interpreta el saldo automático del 11/11
como disponible para más unidades ese día.** La siguiente fecha se mide
de nuevo desde la primera comprobación.

## Comandos y resultados reales

```bash
uv run --frozen pytest -q tests/test_oos_v12_training.py::test_campaign_roots_match_frozen_paths_exactly tests/test_oos_v12_training.py::test_precheck_and_all_profile_supervisors_compete_for_one_lock
# antes: 2 failed; después: ambos passed
uv run --frozen pytest -q tests/test_oos_v12_budget_audit.py tests/test_oos_v12_training.py
# 34 passed
uv run --frozen python scripts/audit_oos_v12_2021_budget.py > docs/evidence/oos-v12-training-root-fix-20261111/budget-audit.json
# 99/99; margen mínimo 1128,211 s
uv run --frozen pytest -q
# 585 passed, 2 advertencias de fork sintético, 539,80 s
uv run --frozen ruff check .
# All checks passed!
uv run --frozen python scripts/write_oos_v12_report.py
# reconoce raíz histórica sin migración
systemctl --user enable --now oos-v12-training.timer
# siguiente disparo 12/11/2026 01:00 America/La_Paz
```

La prueba de bloqueo empleó dos procesos distintos y raíces temporales;
las tres configuraciones compitieron con el mismo `global.lock`. No usó
datos de mercado ni creó unidades históricas. La eliminación local de
`.python-version` permanece ajena a los commits.
