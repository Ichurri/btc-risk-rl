# Hito P2R — supervisor y guardas sintéticos

Base `d7f253b`; rama `codex/p2r-infrastructure`. Alcance autorizado:
infraestructura y pruebas sintéticas únicamente. El protocolo histórico P2R
continúa en propuesta. No se tocó el algoritmo Q/A/B+D, AcceptedMarket,
normalizador, datos ni checkpoints P2.

## Implementado

- `scripts/run_p2r.py` ofrece solo una sonda sintética. Los perfiles `market`,
  `validation` y `final` salen con error antes de cargar módulos de mercado o
  crear la raíz solicitada. La sonda exige una unidad `systemd --user` propia;
  no existe permiso ni ejecutor histórico P2R.
- `P2RJournal` escribe JSONL con `fsync` y cadena SHA256. Guarda inicio,
  heartbeats, señales, pausa/fallo, salida, UTC/monotónico/día La Paz, fase,
  PID/cgroup, RSS y contadores publicados por el worker. Rechaza cadena
  corrupta. El supervisor existente admite callbacks y corta el grupo del
  worker si llega una señal o una excepción de supervisión.
- `P2RSharedBudget` conserva el lock global, suma cargos externos y asigna
  10800 s a cualquier día con débito incompleto. `P2Ledger` aplica
  los topes Q0/iteración, reserva de cierre y tres días/sesiones. La conexión
  con checkpoints de las dos fronteras P2 aún está pendiente.
  La prueba de ciclo de vida admite una ventana ficticia **solo sintética**
  para evitar que la hora local de la prueba oculte el caso de señal.
- Guardas de AC, batería del sistema (ignora periféricos), memoria disponible
  ≥4 GiB y disco ≥10 GiB: batería ≥50 % en preflight y ≥40 % antes de unidad;
  sensor ausente/incoherente falla cerrado. `check_service_context` exige
  cgroup de unidad y, para un futuro perfil histórico, `Linger=yes`.

## Verificación y alcance de evidencia

Las pruebas sintéticas incluyen `SIGTERM` dentro de unidad, `SIGINT` antes de
comenzarla y señal durante la confirmación; muerte abrupta `SIGKILL`, rechazo
de reapertura, pérdida del worker al morir el padre, corrupción del journal,
perfiles prohibidos, débito incompleto, recursos, pérdida de batería dentro
de la unidad y marcadores de progreso. Una unidad transitoria real de
`systemd --user` terminó después de salir `systemd-run`; otra recibió
`SIGTERM` durante el trabajo y dejó `failed` con cero unidades aceptadas. Una
tercera midió dos gaps de heartbeat de 4.008 s. Son sondas de sueño sintético,
sin Q/A/B ni trayectorias de mercado. Comandos y resultados puntuales en
[evidencia](../evidence/p2r-infrastructure/COMMANDS.md).
Una sonda adicional el 01/10 completó con la ventana diaria real y débito
externo cero; no usó la excepción de reloj ficticio.

El host reportó `Linger=no`. No se cerró la sesión completa; por ello la
supervivencia tras logout no está verificada. Una lectura local mostró AC
conectada y batería al 90 %, pero `MemAvailable` por debajo de 4 GiB;
`check_resources` bloqueó la entrada viva. El directorio `/tmp` tampoco
alcanza 10 GiB de disco libre; la raíz del repositorio sí tenía espacio, pero
el requisito de memoria seguiría bloqueando. No se cambiaron umbrales.

## Integridad y límites

El ledger P2 original, el progreso parcial y su journal conservaron SHA256
`e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8`,
`bb2af51c8192303d062b095646a772948072e4eeb36c039f1aa8f9e0037af2b3` y
`45ef6ad0421e062a7a1b150f5711cfbf07bfec8d47e5e3a72dabf2a149f6002b`
respectivamente. La unidad parcial permanece fuera de los contadores aceptados.

La infraestructura no es todavía un ejecutor P2R histórico: falta conectar
las nueve corridas Q/A/B+D y su progreso real a esta supervisión, congelar
huellas/configuración y registrar permiso separado. También falta probar
logout completo con persistencia del gestor y repetir preflight vivo con
recursos aptos. Ninguna condición de avance científico, CVaR o rentabilidad
se evaluó. Ver [ajustes propuestos](../proposals/P2R-infraestructura-addendum-v1.md).
