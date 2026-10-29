# WF de costos `...03`: fallo de la primera Q0

**Estado: campaña fallida, permiso cerrado, sin unidades aceptadas.** El 29/10/2026 se autorizó el perfil aislado `...03` en `7c74176` y se inició una sola sesión `systemd --user`. No se reanuda esta raíz. El registro de aprobación se conserva para auditoría; el gate se cerró prospectivamente en `05adff0`.

## Preparación y admisión

- Se esperó a CA conectada y batería ≥50 %. La batería pasó de 45 % a 48 %, 49 % y 50 % antes de la suite. El preflight inmediato registró CA conectada y 56 %.
- Antes del lanzamiento, `uv run --frozen pytest` dio **428 passed** en 289,88 s; `uv run --frozen ruff check .` dio `All checks passed!`. Son pruebas de código, no unidades históricas.
- El [preflight vigilado](../evidence/oos-v1-2-wf-cost-03-campaign/preflight-launch.json), a las 15:23:21 UTC, dio `status=ready`, sin bloqueos, con memoria disponible 4.767.477.760 B, disco libre 151.900.192.768 B, `Linger=yes`, gestor `running`, saldo global 8.100 s antes de reserva y raíz `...03` ausente. Las huellas del perfil, código, derivado exclusivo de entrenamiento y cortes coincidieron. Registró 44 rutas pertinentes, ningún CSV H1 compartido ni archivo protegido; cero trayectorias y cero pasos de optimizador. SHA-256 del preflight: `370b2904d79f26191082e28fc8c8158baa11ade3d01ccada0111488221de94db`.
- La aprobación independiente tiene SHA-256 `6f877eaf18663f0427ef9f5ad9e412eeec6da761d7355bbc110563e784c6c4b4`; la huella de código con gate activo era `b450b981f96674456d417d0391551fa8090c36d7781e7aac36745645228c09c8`. Los gates `...01` y `...02` permanecieron cerrados.

## Sesión y fallo observado

Se lanzó **solo** `oos-wf-cost-20261029-03-session-01.service`, con `Type=exec`, `Restart=no` y `RuntimeMaxSec=3600`. Su `InvocationID` fue `d763be02a01a49b7b4ef2c88069009ca`. El journal de systemd muestra inicio a las 15:23:52 UTC y salida a las 15:23:57 UTC, `Result=exit-code`, `ExecMainStatus=1`, 472.948.736 B de memoria pico y 6,179805 s de CPU del servicio. La bitácora durable de sesión registra 15:23:53.406101–15:23:56.716545 UTC, 3,310445 s medidos y estado `failed`. El ledger contabilizó 2,024549 s de intervalo abierto en su día local. Son relojes de alcance distinto y no se suman.

El [log original del trabajador](../evidence/oos-v1-2-wf-cost-03-campaign/worker-0-error.log) termina en `PermissionError: WF cost market unit requires registered lease` dentro de `complete_unit`, antes de crear el experimento o ejecutar un paso de optimizador. La causa es verificable en código: `wf_cost_replacement_03_exec.WFCostPermit` hereda de `wf_cost.WFCostPermit`, pero `p2_runner.complete_unit` exige `type(permit) is WFCostPermit`. Esa igualdad rechaza la subclase. La suite sintética anterior no atravesaba conjuntamente el trabajador real y esta guarda.

El ledger final conserva `status=failed`, Q0 pendiente e **índice de unidades aceptadas vacío**. No existe `checkpoint-0`, `unit-0.json` ni checkpoint posterior. La salida del servicio no equivale a Q0 aceptada. No se inició la unidad 1. El supervisor atribuye `child_failure`, `returncode=1`, sin señal. El resumen reproducible de huellas está en [audit-failure.json](../evidence/oos-v1-2-wf-cost-03-campaign/audit-failure.json); el SHA-256 del ledger original es `e03fc4d2b54b2d5d9513d42d59c9a845156e7e76a350b145271a5c75087bb1f3`, el de la bitácora `8188fa36c51efe369a9e15f71c9afa0e9475d02f51ed3ab4df808ea44e0432d5`.

La admisión futura aplica el cargo conservador para una unidad fallida pendiente: **10.800 s del presupuesto global del 29/10**, saldo cero ese día. Ese cargo no es tiempo de cómputo medido. La sesión fallida de `...02` pertenece al 27/10 y no se duplica el 29/10.

## Preservación y alcance

El gate `...03` está cerrado; el registro y todos los archivos de la raíz fallida se mantienen intactos. La comparación archivo por archivo con `docs/evidence/oos-v1-2-wf-first-start-fix/hashes-before.json` dio 15/15 archivos idénticos para `...01` y 2/2 para `...02`. Sus gates siguen cerrados. La eliminación local previa de `.python-version` no se incorporó.

El preflight vigiló aperturas **antes** del lanzamiento. No hubo traza de aperturas a nivel de sistema del trabajador; por ello no se atribuye al log una lista completa de archivos abiertos durante Q0. El permiso y la ruta fallaron antes de cualquier actualización de aprendizaje; este intento no aporta costo de Q0 aceptada ni del ciclo de entrenamiento por cortes. Validación 2023 y prueba final quedaron fuera del alcance.

La corrección debe ser **prospectiva**: definir un contrato de permiso específico de perfil que conserve la validación del lease sin aceptar tipos arbitrarios, y probar la ruta real `worker → complete_unit` antes de otra autorización. Harían falta raíz y registro nuevos. No corregir ni reintentar `...03`.
