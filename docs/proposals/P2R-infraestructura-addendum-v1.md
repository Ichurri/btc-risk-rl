# P2R: ajustes de infraestructura para revisión

**PROPUESTA PARA REVISIÓN; NO AUTORIZA P2R HISTÓRICO.** Complementa, sin
reemplazar, [P2R-protocolo-v1.md](P2R-protocolo-v1.md). La autorización actual
cubre implementación y verificación sintéticas. El contrato científico de la
propuesta v1 permanece intacto.

1. **Independencia de sesión.** La entrada sintética exige cgroup de una unidad
   `p2r-*.service` de `systemd --user` e `INVOCATION_ID`. Un servicio transitorio
   sobrevivió a la salida de `systemd-run` y completó la sonda. Eso no prueba
   continuidad tras cerrar toda la sesión de usuario: `loginctl` devolvió
   `Linger=no`. Para un permiso histórico futuro, exigir `Linger=yes`, verificar
   el gestor tras logout real y conservar el journal de la unidad. La
   infraestructura no habilita linger ni ejecuta logout de forma implícita.
2. **Heartbeat.** Se programa cada 4 s, dejando margen al límite de ≤5 s de
   la propuesta. Se escriben UTC, monotónico, día La Paz, fase, PID/cgroup,
   RSS y último progreso publicado por el worker. Un retraso del sistema
   operativo todavía puede superar 5 s; el cierre debe informar gaps reales
   y tratarlos como incidencia de integridad si aparecen en mercado.
3. **Débito incompleto.** Cualquier ledger externo sin cargo diario o con
   cargo cero, y cualquier `failed`/`incomplete` con unidad pendiente, consume
   conservadoramente 10800 s del día. El 30/09/2026 La Paz está excluido para
   la futura P2R. La sonda sintética puede usar una ventana ficticia para probar señales
   cerca de medianoche; nunca puede abrir un perfil de mercado.
4. **Interrupciones.** `SIGTERM`/`SIGINT` antes de comenzar la unidad dejan
   pausa y cero trabajo; dentro de la unidad invalidan la campaña. Una muerte
   sin manejador deja `running`; el siguiente intento la marca `failed` sin
   reintentar. El worker recibe señal de muerte del padre. Pérdida de AC o
   batería <40 % durante la sonda se registra; el watchdog sigue limitando la
   unidad y se anota pausa después de completarla. El futuro runner deberá
   aplicar esa pausa antes de iniciar otra unidad. La raíz P2 original se
   conserva intocable.
5. **Pendiente para un permiso histórico.** La sonda de ciclo de vida no
   contiene un ejecutor de nueve corridas ni carga AcceptedMarket. Antes de
   un permiso separado se debe integrar este supervisor con las unidades
   P2 Q0/Q/A/B+D, contadores reales, checkpoint `after_q0` y
   `after_dual_and_D`, guardas vivas de memoria/disco/alimentación y
   presupuesto de campaña; repetir las pruebas sintéticas de equivalencia y
   reanudación. La disponibilidad real de ≥4 GiB RAM y ≥10 GiB disco, junto
   con AC/batería y `Linger=yes`, es condición de entrada, no ajuste del
   umbral por conveniencia.

La prueba de cierre de sesión realizada cubre **salida del lanzador**, no
logout completo ni apagado físico. Una prueba de apagado físico no se hizo y
no puede garantizar continuidad. Las sondas no son evidencia de entrenamiento
de mercado ni de cumplimiento de los umbrales científicos P2R.
