# P2R: sonda sintética 06 con checkpoint Q0 previo y SIGTERM en unidad 1

**Estado:** cerrada con el fallo esperado. Base `d840d6a`; unidad
`p2r-signal-qabd-review-06.service`, `InvocationID`
`797f0e422bac4b138c13a0829261a752`. Se usó exclusivamente el perfil
sintético bajo `systemd --user`, una sola vez, en raíces nuevas. No se usó
histórico de mercado, validación ni conjunto final.

| Evento | UTC 06/10/2026 | Evidencia |
| --- | --- | --- |
| Preflight listo | 05:03:00.680498 | `prelaunch.txt` |
| Q0 empieza | 05:03:26.143489 | `supervisor.jsonl` |
| Q0 completa `after_q0` | 05:04:43.534302 | ledger, manifest, journal |
| Primera Q/A/B+D empieza | 05:04:43.671064 | `supervisor.jsonl` |
| Huellas y estado antes de señal | 05:05:15.523865 | `before-signal.json` |
| SIGTERM al proceso principal | 05:05:29.096722 | journal systemd |
| Supervisor registra señal/fallo | 05:05:29.203924 / 05:05:29.214919 | `supervisor.jsonl` |
| Supervisor termina | 05:05:29.219796 | `supervisor.jsonl` |
| Lectura de cierre | 05:06:26.282321 | `after-signal.json` |

La señal exacta fue `systemctl --user kill --kill-whom=main --signal=SIGTERM
p2r-signal-qabd-review-06.service`. El ledger final es `failed` por
`interrupted_supervisor_or_unit`, con `pending.unit=1` y solo Q0 en la lista
de unidades aceptadas. Systemd informa `Result=exit-code`,
`ExecMainStatus=1`. No existen `checkpoint-1`, `unit-1.json` ni
`closing-1.json`; no hubo `unit_completed` de la unidad 1. Q0 registró dos
trayectorias sintéticas y 360 transiciones; ninguna actualización del actor
ni del crítico. Los 19 heartbeats de Q0 y 12 de la unidad 1 tuvieron 18 y 11
intervalos, respectivamente; máximos observados 4.147761 y 4.173003 s.

El `state.pt` de `checkpoint-0` conservó antes y después SHA-256
`1de2699ae55e1f1d1e8686adada3d9b05fda2193b52adfeb24b2403a511aa157`;
su `manifest.json` conservó
`b80d404a94b744f2fc680367476d51d4a67e0c314ff644dd7b63f775d954e96a`.
El manifest declara `after_q0` y la misma huella de estado que el ledger y el
journal. Se verificaron las cadenas de hash de ambos registros. El
[manifiesto](../evidence/p2r-signal-qabd-06/SHA256SUMS.txt) cubre los 25
archivos originales de la sonda; los resultados de la comprobación de solo
lectura están en [results.json](../evidence/p2r-signal-qabd-06/results.json).
Se versionaron copias byte a byte del [journal de systemd](../evidence/p2r-signal-qabd-06/systemd-journal.txt)
y de las lecturas [previa](../evidence/p2r-signal-qabd-06/before-signal.json)
y [posterior](../evidence/p2r-signal-qabd-06/after-signal.json).
Las raíces 01–05 mantuvieron sus huellas verificadas.

**Alcance de la prueba:** la señal cayó durante la espera sintética
supervisada de la unidad 1, antes de ejecutar los cálculos Q/A/B+D
(`worker-1.log` vacío). Demuestra que una interrupción en esa unidad marca
fallida la campaña, rechaza la unidad incompleta y preserva exactamente el
checkpoint anterior. No demuestra interrupción durante un optimizador,
apagado físico, ni seguridad de una campaña histórica. Conservar el
checkpoint anterior como evidencia **no autoriza reanudar** esta campaña
fallida.

Se ejecutaron tres pruebas pytest sintéticas dirigidas (3 pasadas en
22.49 s), el verificador de artefactos, las comprobaciones de huellas y
Ruff (`All checks passed!`). La suite completa también pasó: 267 pruebas en
202.83 s. Estas pruebas no son nuevas sondas systemd ni entrenamiento
histórico.
Comandos exactos y captura original: [COMMANDS.md](../evidence/p2r-signal-qabd-06/COMMANDS.md).
Esta sonda no cambia el contrato Q/A/B+D ni el estado metodológico P2R v2;
el ejecutor histórico, permisos propios y preflight de campaña siguen
pendientes de autorización separada. P2 fallido permanece intacto.
