# Ejecutor aislado del estudio WF de costos `...02`

**Estado: infraestructura verificada solo con datos sintéticos; campaña
histórica no autorizada.** El trabajo parte de `37cc06e` y conserva la
[propuesta](../proposals/OOS-v1-2-costo-cortes-reemplazo-v1.md), el diseño de
22 unidades y el estudio parcial `...01` como antecedentes distintos.

## Contrato implementado

- `wf_cost_replacement_exec.py` fija la raíz nueva y el registro de aprobación
  independiente. `MARKET_EXECUTION_ENABLED=False` y
  `REGISTRATION_SHA256=None`: aun un JSON falsificado no habilita ejecución.
  La puerta precede la lectura de solicitud, carga del derivado y creación de
  raíz. El permiso futuro deberá fijar también la huella del protocolo,
  diseño, propuesta, código y manifiesto H1 exclusivo de entrenamiento.
- `wf_cost_replacement_units.py` usa el mismo ledger y algoritmo Q0/
  Q/A/B+D, pero su supervisor, trabajador, raíz, bitácora y registro son
  propios. La primera Q0 aceptada obliga a pausa de auditoría. Un fallo
  dentro de unidad sigue siendo irreversible; una unidad parcial no se
  acepta. El perfil histórico `...01` conserva su puerta cerrada y sus
  rutas operativas originales.
- Se heredan dos C10, semillas `276696733` y `498614892`, cortes 2021 y 2022,
  22 unidades en orden fijo, β=0, crítico de cuatro épocas, K=10, D=64,
  Q/A/B, `d=−ln(0,90)`, cotas de 120/180 s, 10.800 s globales/día con
  reserva de 2.700 s, 3.600 s propios/día, 5.400 s acumulados y dos días
  activos. Los límites se aplican por el ledger compartido, incluida la
  bitácora de sesiones y el cargo externo de otras campañas.
- Las funciones comunes de preflight y presupuesto aceptan una raíz explícita.
  Sus valores por defecto siguen apuntando a `...01`; su gate, autorización y
  artefactos no se cambiaron. La nueva identidad del ledger incluye huella
  de propuesta y ejecutor, además de fuentes por corte y procedencia.

## Verificación ejecutada

La [captura de preflight](../evidence/oos-v1-2-wf-cost-replacement-executor/preflight.json)
terminó `blocked` **solo** por ausencia de aprobación nueva. Vio alimentación
CA, batería 100 %, `Linger=yes`, gestor `running`, memoria y disco sobre
umbrales en ese instante. Contó 3.639/4.678 episodios y 5.764/7.703 filas
de ajuste para 2021/2022. La vigilancia de `open` registró los archivos
abiertos: derivado `data/processed/p2r-training-h1`, configuración,
metadatos y las cinco evidencias congeladas de `...01`; el código tiene una
huella propia en el resultado. No abrió CSV H1
compartidos, validación ni prueba final. No generó trayectorias ni pasos de
optimizador. La raíz `...02` y su registro siguen ausentes.

Las pruebas sintéticas usan raíces temporales: Q0 aceptada y checkpoint
`after_q0`, pausa, nuevo proceso y admisión de unidad 1; rechazo de roster
alterado sin cambiar Q0; bitácora que registra fallo anterior al ledger;
presupuesto que carga el ledger `...01` pero excluye el propio `...02` para
evitar doble cómputo; y rechazo de CLI/trabajador sin permiso. El
[cotejo congelado](../evidence/oos-v1-2-wf-cost-replacement-executor/frozen-artifacts-check.json)
verificó ledger `ready`/una Q0/sin `pending` y las cinco huellas originales.

Estas pruebas **no** ejecutan `systemd --user` con `...02`, no miden duración
WF Q/A/B+D real, no prueban una señal dentro de un optimizador histórico y
no autorizan entrenamiento. La propuesta de reemplazo sigue pendiente de
aprobación específica antes de cualquier campaña.

Los comandos y salidas concretas constan en
[COMMANDS.md](../evidence/oos-v1-2-wf-cost-replacement-executor/COMMANDS.md).
