# P2R v2 — diferencias respecto de v1 y del anexo

La [v2](P2R-protocolo-v2.md) **sustituye la lectura vigente** de la
[propuesta v1](P2R-protocolo-v1.md) y su
[anexo](P2R-infraestructura-addendum-v1.md) para revisión académica, sin
borrar esos antecedentes ni adoptar el protocolo. No altera el algoritmo ni
el diseño científico heredado de P2.

| Tema | Texto/estado anterior | Precisión v2 basada en evidencia |
| --- | --- | --- |
| Matriz P2R y P2 | V1 ya recomendaba nueve corridas nuevas y separación de P2 | Se conserva literalmente; se explicita que ni las cinco corridas P2 cerradas ni su parcial entran en denominadores P2R |
| Q0 y Q/A/B+D | V1 exigía ambas fronteras; anexo aún pedía conectarlas | La integración sintética existe, usa trabajador P2 y verifica equivalencia/reanudación en pruebas; falta ejecutor histórico train-only |
| `Linger` | Anexo informaba `Linger=no`; procedimiento de host aún indicaba no verificado | En preflight 02 se observó `Linger=yes` y gestor `running`; debe revalidarse el día de campaña |
| Logout | Anexo solo había observado salida de `systemd-run`, no logout total | Sonda 01 tuvo Q0 completa pero suspensión posterior; 02 retiró última sesión interactiva y observó 139 heartbeats sin sesión, Q0 completa y cero suspensiones hasta el reingreso |
| Heartbeat | V1 fijaba ≤5 s; anexo programaba a 4 s, pero 02 registró 174 intervalos >5 s | Corrección posterior 03 solicita con margen y rechaza intervalo medido >5 s; 6/6 intervalos de esa sonda ≤5 s. No se reinterpreta 02 como éxito temporal |
| Señal durante unidad | V1 lo requería; anexo tenía fixtures y prueba del ciclo de vida | Sondas 04/05 enviaron SIGTERM durante Q0 real bajo `systemd --user`: ledger falló, sin checkpoint nuevo. 04 detectó salida 0; 05, tras corrección, devolvió estado 1 |
| Checkpoint previo | V1 ordenaba conservar evidencia y prohibía reintentos | Q0 interrumpida carecía de checkpoint previo. El test sintético de unidad 1 conserva una unidad aceptada, pero falta auditoría explícita de huella antes/después bajo señal real en Q/A/B+D |
| Apagado | V1 distinguía servicio independiente de garantía energética | P2 se apagó, iniciador desconocido. Ninguna sonda P2R reprodujo apagado físico ni garantiza continuidad ante él; al detectar `running` huérfano, el protocolo lo clasifica como fallo |
| Presupuesto y datos | V1: 10800 s/día, tres días, train-only y d común | Sin cambios; se ordenan reglas de admisión, débitos externos, topes, reserva, saldos y brechas de permiso/huellas para futuro ejecutor |
| Evaluación | V1 conservaba criterios P2 sobre D y advertía que no eran confirmatorios | Sin cambios; se incluyen ecuaciones, denominadores y condición conjunta de 2/3 semillas por cada condición en la v2 |

La evidencia de 01–05 sigue en sus informes y manifiestos; la v2 cita sus
resultados sin reescribir ledgers, journals o artefactos. Las frases antiguas
que decían «logout pendiente», «Linger=no» o «señal no probada» describen el
momento de sus documentos, no el estado metodológico actual. Sus límites no
se borran: `Linger=yes` fue puntual, 02 incumplió cadencia, 03 fue breve y
04/05 solo interrumpieron Q0.
