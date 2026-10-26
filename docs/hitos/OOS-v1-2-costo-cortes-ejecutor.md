# Ejecutor aislado para medir el costo de dos cortes de desarrollo

**Infraestructura implementada; estudio histórico no autorizado ni ejecutado.**
Rama `codex/oos-wf-cost-executor`. La propuesta de 22 unidades en
[`OOS-v1-2-costo-entrenamiento-cortes-v1.md`](../proposals/OOS-v1-2-costo-entrenamiento-cortes-v1.md)
permanece sin adoptar. La campaña fuera de muestra v1.2 también permanece
sin adoptar. P0, P1, P2, P2R y P3 conservan sus artefactos originales.

## Contrato implementado

- Identidades fijas: `wf-2021`, semilla `276696733`, y `wf-2022`, semilla
  `498614892`; ambas C10, β=0, crítico de cuatro épocas, K=10 y D=64.
  Cada corrida exige Q0 más diez Q/A/B+D, en ese orden. El código valida
  los 22 puestos y los parámetros frente al candidato existente.
- La fuente de cada corte se reconstruye **en memoria** desde el derivado H1
  exclusivo de entrenamiento. Se comprueban todas sus huellas, se corta
  antes del 02/12/2020 o 02/12/2021, se regeneran características dentro de
  los segmentos existentes y se reajusta el normalizador solo con el prefijo.
  Los manifiestos propios con huellas de las tablas serializadas se crearían
  en la raíz aislada **solo después de una autorización futura y antes de la
  primera trayectoria**. Los productos de calibración de octubre no se
  aceptan como manifiestos de entrenamiento.
- El supervisor usa una raíz fija nueva, un ledger encadenado, token y PID
  padre por unidad, solicitudes con hash, checkpoints atómicos y auditoría
  del reporte/checkpoint antes de aceptar cada frontera. El worker exige el
  permiso específico antes de leer la solicitud. El permiso está fijado en
  `False` y sin hash de registro; editar un JSON o invocar el comando público
  no lo habilita.
- La admisión exige la cota completa Q0=120 s o iteración=180 s dentro de
  10.800 s globales/día con 2.700 s de reserva, 3.600 s propios/día,
  5.400 s propios acumulados y como máximo dos días activos. Se descuentan
  las campañas previas registradas, con débito conservador para un fallo
  parcial. Un corte dentro de una unidad deja `failed` irreversible; el
  checkpoint completo anterior se conserva como evidencia, sin permitir
  reanudar una campaña fallida. El presupuesto compartido de P2R/P3 también
  reconoce el ledger de este estudio si alguna vez se autoriza.

## Preflight de solo lectura y límites

El comando `uv run --frozen python scripts/audit_oos_wf_cost_preflight.py`
no crea la raíz ni recolecta trayectorias. Registra los archivos abiertos y
rechaza inmediatamente cualquier intento de abrir CSV H1 compartidos. Los
dos cortes dieron 3.639/4.678 inicios H180 y 5.764/7.703 observaciones de
ajuste. No se abrieron datos de validación ni del conjunto final.

En la medición local del 26/10/2026 el preflight quedó **bloqueado** por:
`systemd --user` en estado `degraded` (`swaync.service` falló) y ausencia de
permiso de campaña. CA conectada, batería 95 %, `Linger=yes`, memoria
disponible superior a 4 GiB y disco libre superior a 20 GiB eran mediciones
del momento, no una certificación futura. La raíz y sus manifiestos aún no
existen por diseño; se generan únicamente tras autorización y un nuevo
preflight. Ninguna unidad histórica ni sintética de aprendizaje se lanzó.

El código de ejecución histórica, incluidas sus ramas de señal y cálculo de
optimizador, **no puede verificarse de extremo a extremo sin una unidad**.
Las pruebas actuales ejercitan el rechazo público/worker, el plan exacto,
los dos cortes de solo lectura, el ledger sintético de 22 fronteras,
presupuesto compartido, reportes falsificados y corrupción. Una autorización
posterior requerirá volver a medir recursos y gestor, inspeccionar la nueva
raíz y auditar la primera unidad antes de proseguir. La prueba actual no mide
tiempos de entrenamiento en 2021/2022 ni cambia la conclusión condicional
del presupuesto de 20 días de la v1.2.

Se ejecutaron 16 pruebas focales y la suite completa (376 aprobadas), además
de Ruff. El preflight versionado tiene SHA-256
`79e9b0a0b3d7633b62b51e5d2895be573fd4b6f1df24503b295fe992cfa176eb`.
La raíz P3 conservó la huella agregada
`73949350733bf3f8e3939e2dfcf7a28920668e738b0e5d910bd070a010fdcbec`;
los cinco ledgers P0/P1/P2/P2R/P3 y el manifiesto del derivado H1 coincidieron
con sus huellas previas.

## Evidencia y comandos

Consultar [`COMMANDS.md`](../evidence/oos-v1-2-wf-cost-executor/COMMANDS.md)
y [`preflight.json`](../evidence/oos-v1-2-wf-cost-executor/preflight.json).
Este informe recoge únicamente comprobaciones realmente ejecutadas; las
huellas y resultados finales se fijan en la evidencia versionada.
