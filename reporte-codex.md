# Reporte Codex — 13/11/2026 15:33 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, código `baa1a85`. Servicio inactivo; ledger `ready`, cursor **82/108**, **907/1.188 unidades**, `pending=null`. Último checkpoint completo `artifacts/oos-v12-training-main-01/run-82-C5-b0/checkpoint-4/state.pt`, SHA-256 `9ddf6f807b814fc5c1885d143353d5642e67e9be4a8f7544561fdd7f357fcde9`. Ledger SHA-256 `24a602293b16483010055a58f832acbd33cd41cabd0d31ef63627857fbb36323`.
- El 13/11 carga **45.459,199 s** globales y deja **2.240,801 s antes de la reserva de 2.700 s**. La preparación y admisión exigen al menos 2.700 s de saldo antes de reserva; además la frontera de trabajo del ledger venció a las 14:01:53. No hubo nuevo entrenamiento tras ese corte. La unidad siguiente mediría aprox. 128,696 s de admisión conservadora según `1,5 × max(C5/iteration)`, pero el límite diario impide llegar a esa admisión.
- No se aplicó ampliación prospectiva al ledger vigente: su identidad incluye la huella de código y de la enmienda, y los checkpoints exigen procedencia de código exacta. Cambiar esos archivos para este mismo ledger requeriría una migración de identidad y checkpoints probada antes de usarla. El saldo diario se renueva el 14/11 a las 00:00. El timer original de la 01:00 quedó deshabilitado; se programó solo `oos-v12-training-midnight-20261114.timer` para las **00:00 America/La_Paz**. Ejecutará el servicio supervisado existente con suite, Ruff, preflight y admisión nuevos; no hay sesión duplicada.
- Última captura: CA conectada, memoria disponible 11.312.787.456 B, disco libre 91.449.217.024 B, `Linger=yes`; son valores del momento, no guardas anticipadas para medianoche. Restan 281 unidades y 26 corridas. Validación 2023 y prueba final siguen cerradas. Próxima acción: verificar la sesión de las 00:00 y el ledger antes de otro arranque. La eliminación local previa de `.python-version` permanece sin incorporar.

---

# Estado de supervisión — 13/11/2026 13:42 America/La_Paz

- Servicio inactivo con `Result=success`. Ledger `ready`, cursor 82, **907/1.188 unidades aceptadas**, `pending=null`; 82/108 corridas completas y 27/36 ternas completas. Última unidad aceptada `run-82-C5-b0/4`, checkpoint `artifacts/oos-v12-training-main-01/run-82-C5-b0/checkpoint-4/state.pt`, SHA-256 `9ddf6f807b814fc5c1885d143353d5642e67e9be4a8f7544561fdd7f357fcde9`, comprobado contra ledger.
- La sesión `01dda98600cf48a19b1c5ae52212cd4a` pasó suite, Ruff y preflight, aceptó 20 unidades nuevas y pausó por `availability_lost_after_unit` en frontera completa. La guarda solo registró «Insufficient P2R memory or disk», sin cifra contemporánea; después del cierre se midieron 11.471.822.848 B de `MemAvailable` y CA conectada. No atribuir una causa concreta a esos valores posteriores.
- Presupuesto global de 13/11 al corte: **45.459,199 s cargados**, **2.240,801 s antes de la reserva de 2.700 s**. El trabajo de hoy tiene frontera a las 14:01:53 local. La preparación formal y la admisión mínima requieren más saldo que el disponible; no iniciar otro servicio hoy. El timer espera el 14/11 a las 01:00 y deberá repetir suite, Ruff, preflight y admisión antes de cualquier unidad.
- Faltan 281 unidades y 26 corridas para el objetivo 108/108 y 1.188/1.188. Validación 2023 y prueba final permanecen cerradas. La eliminación local de `.python-version` sigue sin incorporarse.

---

# Reporte Codex — 13/11/2026 13:39 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 907 unidades aceptadas, cursor 82, pending=False; SHA-256 ledger `24a602293b16483010055a58f832acbd33cd41cabd0d31ef63627857fbb36323`.
- `main-2018-2022`: cargo propio medido en ledger 124062.171 s; última unidad 81.412 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-82-C5-b0/checkpoint-4`; estado SHA-256 `9ddf6f807b814fc5c1885d143353d5642e67e9be4a8f7544561fdd7f357fcde9`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `b9a455a6f843adb4114bc4746968860ca2555c7de3bb21381bf6cc5f43c67500`.
- Presupuesto global del día: 45459.199 s cargados; 2240.801 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 13/11/2026 13:02 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 894 unidades aceptadas, cursor 81, pending=False; SHA-256 ledger `3d9b660b1899b9c6b0e8ed628aa690aa3d635d3bcbdb747fa1112eb127d340fd`.
- `main-2018-2022`: cargo propio medido en ledger 121868.519 s; última unidad 75.872 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-81-C0-b0/checkpoint-2`; estado SHA-256 `4dc541efa2193b5333139d1dcbe31cf77efcf2797b6b76c698ccd06c069c9b07`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `a4fdf09336c9689295662f9fc2d5b37eeecbe92f65ced7d99d47dce737b2f2bf`.
- Presupuesto global del día: 43265.546 s cargados; 4434.454 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Estado de supervisión — 13/11/2026 04:08 America/La_Paz

- `oos-v12-training.service` inactivo, `Result=success`; ledger principal `ready`, cursor 79, **874/1.188 unidades** aceptadas, `pending=null`. Última unidad `run-79-C0-b0/4`, checkpoint `artifacts/oos-v12-training-main-01/run-79-C0-b0/checkpoint-4/state.pt`, SHA-256 `d8fabb4aacc4ed90154eae5ef24ab29672a8d4503b25b44f8ba48ca6e9ee0bf6`, verificado contra ledger.
- La sesión `804ff6c092b44bdca61b9380d5d26894` pausó en frontera por `availability_lost_after_unit`; es el tercer corte de recursos de hoy, sin unidad parcial aceptada. El evento indica memoria o disco insuficiente, sin conservar la cifra exacta del instante. Después del cierre se midieron `MemAvailable=11.099.152.384 B`, CA conectada y 91.541.499.904 B de disco libre; son capturas posteriores, no explican por sí solas el mínimo durante el trabajador.
- Presupuesto global 13/11: **11.009,884 s** cargados y **36.690,116 s** antes de la reserva de 2.700 s. No hay otra campaña activa. El siguiente paso requiere liberar memoria de aplicaciones de usuario y repetir suite, Ruff, preflight y admisión antes de un solo reingreso; no se ha lanzado otra sesión tras este tercer corte. Validación 2023 y prueba final siguen cerradas.

---

# Reporte Codex — 13/11/2026 04:04 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 874 unidades aceptadas, cursor 79, pending=False; SHA-256 ledger `db5be93354ff975cb909a4c5b40f615ba8dfcb64434c093974a6b8e64e4591e2`.
- `main-2018-2022`: cargo propio medido en ledger 89612.859 s; última unidad 77.125 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-79-C0-b0/checkpoint-4`; estado SHA-256 `d8fabb4aacc4ed90154eae5ef24ab29672a8d4503b25b44f8ba48ca6e9ee0bf6`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `99eda70a3d46fb4e7fc16e8447b2f18ec255a8d0aa3797a3d143b9f5d08513f4`.
- Presupuesto global del día: 11009.884 s cargados; 36690.116 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 13/11/2026 03:37 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 868 unidades aceptadas, cursor 78, pending=False; SHA-256 ledger `d8f628a07733435e42e76a6d499542a2fe204b318ff5d3cb3a8e3cce731e02c7`.
- `main-2018-2022`: cargo propio medido en ledger 87981.942 s; última unidad 82.660 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-78-C10-b0/checkpoint-9`; estado SHA-256 `d7bec388854e56db47fbf2e1940470a25bb4d56d32de178ff8ab41f149e26b22`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `f484c5d1783f14f1037a963ce9fd46059317f972cfdc74e3ee5c1862f7ef908c`.
- Presupuesto global del día: 9378.971 s cargados; 38321.029 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 13/11/2026 02:01 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 809 unidades aceptadas, cursor 73, pending=False; SHA-256 ledger `a6d931189aac1d177d584d522460f24dbf52140c212edb46150dc8074b946961`.
- `main-2018-2022`: cargo propio medido en ledger 82230.912 s; última unidad 79.932 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-73-C5-b0/checkpoint-5`; estado SHA-256 `94c9abd11519078e0f972e4f7d9dda843885c4c543a281c441889a74a741bfd3`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `9aefc04c574772548fcdbf215d1c9fb60eff9167ed6d8f4da1c21d1f334f1443`.
- Presupuesto global del día: 3627.936 s cargados; 44072.064 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 13/11/2026 01:20 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 794 unidades aceptadas, cursor 72, pending=False; SHA-256 ledger `a626336120d9d70eb021238f4aa4a52b046c0884412e91e7803c117a6ac1f4d6`.
- `main-2018-2022`: cargo propio medido en ledger 79767.970 s; última unidad 78.075 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-72-C0-b0/checkpoint-1`; estado SHA-256 `7e2ada57e790c1583e73d03a32bd9efdc53d01ce978aca5cadc17da868671412`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `59a0180eceaa04824c3ca843d8f407435dee5c0c81fa4694f0b79f1ab9d33bd8`.
- Presupuesto global del día: 1164.995 s cargados; 46535.005 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 12/11/2026 16:34 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 790 unidades aceptadas, cursor 71, pending=False; SHA-256 ledger `d286e721c5cdeb101d7cb88c071edfee672aa6e05075adcbf6522404e62b920f`.
- `main-2018-2022`: cargo propio medido en ledger 79422.511 s; última unidad 90.034 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-71-C5-b0/checkpoint-8`; estado SHA-256 `bed96b4622b3c6ea3621e8f33f05a71a980eabbdfef0807cf68b618bc14f38d7`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `c186553e1c6c72e931e0fc59c1f2023a39e175ab6dbdfe6af31073bfe446a8bb`.
- Presupuesto global del día: 51223.830 s cargados; 0.000 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 12/11/2026 13:09 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 790 unidades aceptadas, cursor 71, pending=False; SHA-256 ledger `c29487f10afa325be1b51729aa78810f9336f5e852ef4e3e4b059c95aceb7a9a`.
- `main-2018-2022`: cargo propio medido en ledger 67110.774 s; última unidad 90.034 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-71-C5-b0/checkpoint-8`; estado SHA-256 `bed96b4622b3c6ea3621e8f33f05a71a980eabbdfef0807cf68b618bc14f38d7`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `bb688602ec5874fd74e1f26e335dc4ac98b6bece8d2951402a702a2f2ac3a53a`.
- Presupuesto global del día: 40074.933 s cargados; 7625.067 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 12/11/2026 02:23 America/La_Paz, reingreso tras bloqueo de memoria

- Rama `codex/oos-v12-expanded-budget`, código en `baa1a85`. La sesión de las 01:00 cerró `blocked_before_unit`: suite y Ruff `ready`, preflight bloqueado por memoria inferior a **6.026.846.208 B**; no aceptó unidades ni cambió el checkpoint. Su cargo cerrado y medido en la bitácora fue **599,478014 s** el 12/11.
- Antes del reingreso, `oos-v12-training.service` estaba inactivo, ledger principal `ready` con **215** unidades y `pending=null`; el checkpoint completo `run-19-C5-b0/checkpoint-5/state.pt` tenía SHA-256 `caf08ad45b9c1a9b57e6e38974cb79ff9dbaef90b49e30dffdbc9d41ab10b64c`. A las 02:10:58, CA=1, batería=100 %, `MemAvailable=10.198.462.464 B`, disco libre=112.317.833.216 B, gestor `running` y `Linger=yes`. El presupuesto previo era 599,478014 s cargados, con 47.100,521986 s antes de la reserva de 2.700 s.
- Se inició **una sola sesión** a las 02:11:32 mediante `systemctl --user start --no-block oos-v12-training.service`, `InvocationID=7525d016897d4d479d67a2189f6bfbfc`, `Restart=no`. Su suite formal, Ruff y preflight vigilado dieron `ready` en la bitácora de comprobaciones. El preflight midió **9.356.529.664 B** de memoria disponible, 3.329.683.456 B sobre la guarda; presupuesto global **1.156,281355 s** ya cargados al momento del preflight, incluyendo el intento de las 01:00 y la preparación de esta sesión, con **46.543,718645 s** antes de reserva. No abrió CSV H1 compartidos ni validación/final.
- Primera unidad nueva **aceptada**: `run-19-C5-b0/6`, cierre 02:22:21 local (06:22:21 UTC), 66,743389 s; ledger llegó a **216 unidades**. Checkpoint `artifacts/oos-v12-training-main-01/run-19-C5-b0/checkpoint-6/state.pt`, SHA-256 `7255880f1f9d748d15fe3daa9b9f9f01c13166e3087a8866fd64e6cc8d3b8d3b`; reporte `unit-6.json` SHA-256 `8f5ad54c53e32d02b1535f7d2c178f7e6204cc50a0d6c7763c09df9b4276e3ee`, solicitud `request-6.json` SHA-256 `573ea206567b1cb4cb16d4c22161bc95fabcbcf833c4ec303fa09eae008bc291`. Las tres huellas coinciden con el ledger.
- **Estado al corte 02:23:** la misma sesión continúa activa y el ledger estaba `running` con la unidad 7 pendiente. El presupuesto de esta sesión aún crece; los 1.156,281355 s anteriores son una captura del preflight, no el cargo final. Permanecen **6/36 ternas completas**; la corrida 19 es parcial. No hay otra sesión de entrenamiento. Próxima acción: dejar que el supervisor pause o cierre en frontera completa, luego auditar ledger, huellas y cargo final; validación 2023 y prueba final siguen cerradas.

---

# Reporte Codex — 12/11/2026 01:10 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `baa1a85`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 215 unidades aceptadas, cursor 19, pending=False; SHA-256 ledger `1245b4299103401bbc066f9044278ffeabd55606687ac3ddab0bfb5c712c5749`.
- `main-2018-2022`: cargo propio medido en ledger 28198.681 s; última unidad 74.080 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-19-C5-b0/checkpoint-5`; estado SHA-256 `caf08ad45b9c1a9b57e6e38974cb79ff9dbaef90b49e30dffdbc9d41ab10b64c`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `2ff89ff9d3a3e09741b865b47710fcdd5d9e331a93c56562e97b8e1561a1c30f`.
- Presupuesto global del día: 599.478 s cargados; 47100.522 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 11/11/2026 21:37 America/La_Paz, cierre auditado

- Rama `codex/oos-v12-expanded-budget`; servicio `oos-v12-training.service` ahora `inactive/dead`, `Result=success`, `InvocationID=9d306358db424a7c87ac4abe8c2cacba`. Supervisor: `paused_at_complete_boundary`. El timer espera el **12/11 a la 01:00**; no se lanzó otra sesión.
- Principal: ledger `ready`, cursor **19/108**, **215 unidades aceptadas**, `pending=null`: **6/36 ternas completas**. SHA-256 ledger `1245b4299103401bbc066f9044278ffeabd55606687ac3ddab0bfb5c712c5749`. Auditoría independiente: 653 estados y 645 huellas de checkpoint/reporte/solicitud correctas. Último checkpoint íntegro `artifacts/oos-v12-training-main-01/run-19-C5-b0/checkpoint-5/state.pt`, SHA-256 `caf08ad45b9c1a9b57e6e38974cb79ff9dbaef90b49e30dffdbc9d41ab10b64c`. El parcial no cuenta como corrida completa. `wf-2022` auxiliar permanece 99/99.
- **Entrenamiento hasta 16/11 09:00:** seis ternas midieron media **2.273,757 s** de unidades. Las 30 restantes exigen **68.212,696 s (18,948 h) extrapolados** de unidades, más suite, Ruff, preflight, carga, auditoría y cierre. Cuatro fechas completas 12–15/11 dispondrían como máximo de 47.700 s productivos cada una, sujeto a guardas y otros cargos. Cierre hacia el 13/11 es escenario condicional, no garantía.
- **Evaluación separada:** metadatos H1 identifican cobertura 2023 2.190/2.190 sin exclusiones; no hay fuente local final 2024–2025 identificada. Sondas sintéticas extrapolan 769,680 s para 108 recorridos 2023 y 764,640 s para 108 finales (**25,57 min combinados**), sin adquisición/exportación/auditoría histórica. Faltan las 36 ternas completas, supervisor verificado, armonización de la tesis, permisos separados y fuente final auditada. No hace falta que ubique un archivo por ahora; el descargador interno sigue apagado.
- **Presupuesto 11/11:** cargo protocolario conservado **47.008,738 s**, saldo **691,262 s antes de la reserva de 2.700 s**: insuficiente para suite y Q0 hoy. La unión efectivamente medida de cinco sesiones fue **30.349,585 s**; más el ajuste conservador previo de 3.857,837 s daría 34.207,422 s. El ledger cobró adicionalmente el hueco inactivo de **12.801,316 s** entre sesiones del mismo día. No es cómputo ni un exceso del tope. No se alteró el ledger ni se reutilizó ese saldo teórico. Ver [informe y evidencia reproducible](docs/hitos/OOS-v1-2-sesion-02-20261111.md).
- Próxima acción: el 12/11 la sesión programada deberá pasar suite formal, Ruff, preflight vigilado, CA/batería/memoria y admisión nuevas; solo entonces continuará desde `checkpoint-5`. Validación y final permanecen cerradas.

---

# Reporte Codex — 11/11/2026 21:31 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `e5a5469`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 215 unidades aceptadas, cursor 19, pending=False; SHA-256 ledger `1245b4299103401bbc066f9044278ffeabd55606687ac3ddab0bfb5c712c5749`.
- `main-2018-2022`: cargo propio medido en ledger 28198.681 s; última unidad 74.080 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-19-C5-b0/checkpoint-5`; estado SHA-256 `caf08ad45b9c1a9b57e6e38974cb79ff9dbaef90b49e30dffdbc9d41ab10b64c`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `c73253ca368652ca240a91956f38ae3b18c4b327fc7d334b3ab59c8e56d6ca6d`.
- Presupuesto global del día: 47008.738 s cargados; 691.262 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 11/11/2026 21:11 America/La_Paz, proyecciones separadas

- Servicio `oos-v12-training.service` activo con `InvocationID=9d306358db424a7c87ac4abe8c2cacba`; a este corte el ledger principal estaba `running`, cursor 17, 196 unidades aceptadas y `run-17-C5-b0/9` pendiente. **5/36 ternas completas**. No hubo sesión duplicada.
- **Entrenamiento:** cinco ternas cerradas midieron una media de 2.271,805 s de unidades. Las 31 restantes representan **70.425,961 s (19,563 h) extrapolados** de unidades, más suite, Ruff, preflight, auditoría y cierre. El último cargo global cerrado del 11/11 fue 31.675,357 s, con 16.024,643 s antes de reserva; la sesión actual lo incrementa. Si sostienen tasa, recursos y admisión, el entrenamiento podría cerrar alrededor del 13/11, antes del 16/11 09:00; no es garantía.
- **Evaluación:** por inventario permitido, H1 declara 2.190/2.190 velas de 2023 sin exclusiones; **no se identificó archivo local final 2024–2025**. La extrapolación de sonda sintética es 769,680 s para 108 recorridos de 2023 y 764,640 s para 108 finales, 1.534,320 s (25,57 min) sumados; faltan adquisición/exportación/auditoría y tiempo histórico real. Antes de abrir datos se requieren 36 ternas cerradas, supervisor verificado, armonización académica, permisos separados y fuente final auditada. No hace falta que ubique un archivo ahora; el descargador interno aún está apagado y se intentará solo tras el permiso final.
- Detalle y límites: [proyección versionada](docs/hitos/OOS-v1-2-proyeccion-20261111.md). Validación y final permanecen cerrados. Próxima acción: esperar pausa o cierre de la sesión activa, auditar ledger/huellas/cargo y reingresar solo desde frontera válida con guardas nuevas.

---

# Reporte Codex — 11/11/2026 21:02 America/La_Paz

- Se inició **una sola nueva sesión** `oos-v12-training.service` a las 20:49, `InvocationID=9d306358db424a7c87ac4abe8c2cacba`, `Restart=no`. Antes: CA=1, batería=50 % y cargando, MemAvailable=6.352.928.768 B, disco libre=113.509.847.040 B, gestor `running`, `Linger=yes`; presupuesto `ok=true`, 16.024,643 s antes de reserva. El servicio realizó suite, Ruff y preflight vigilado, los tres `ready` con el mismo `InvocationID`.
- A las 21:02 el ledger estaba `running`, cursor 17, 188 unidades aceptadas, unidad `run-17-C5-b0/1` pendiente. Esto **no** completa la sexta terna; siguen 5/36 ternas cerradas. No se lanzó evaluación ni otra campaña en paralelo.
- Siguiente acción: dejar que el supervisor pause o cierre en frontera; después cotejar cadena, checkpoint, cargos y estado `systemd`. El timer del 12/11 01:00 repetirá guardas si corresponde. Validación 2023 y prueba final siguen cerradas.

---

# Reporte Codex — 11/11/2026 20:44 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit publicado `977bf53`; la eliminación local previa de `.python-version` permanece fuera de Git.
- La sesión `oos-v12-training.service` terminó `Result=success` y está `inactive/dead` con `InvocationID=097bd51bfa774984a3913721e364f67e`. El supervisor informó `paused_at_complete_boundary`; no hay segunda sesión de entrenamiento activa. El timer sigue programado para 12/11 01:00.
- `wf-2022` auxiliar: `completed`, 99/99 unidades. Perfil principal: ledger `ready`, cursor 16, 186 unidades aceptadas, `pending=null`: **cinco ternas completas de 36** y la corrida 16 en checkpoint 9. Ninguna de las unidades de la sexta terna se interpreta como terna completa.
- Ledger principal SHA-256 `d0d4562da56e585f081c8bc7558f9c8db8b66c78fbcf216290cd5cbab1bf0b44`. Se verificaron los 562 estados encadenados y las huellas de 186 checkpoints, 186 reportes y 186 solicitudes. Último checkpoint completo: `artifacts/oos-v12-training-main-01/run-16-C0-b0/checkpoint-9`, estado SHA-256 `c33ff5961c1cbff19e81bb159155d31bf59957e03e7faa66ef287417878153a8`.
- Tiempos medidos de las cinco ternas: 2.258,869; 2.246,075; 2.266,412; 2.329,475 y 2.258,195 s de unidades. Media 2.271,805 s. Para las 31 ternas restantes, **70.425,961 s (19,563 h) de unidades son una extrapolación**, sin suite, preflight, auditoría, admisión y cierre. No es fecha comprometida de evaluación.
- Presupuesto compartido del 11/11 a las 20:44: **31.675,357 s cargados**, 16.024,643 s antes de la reserva obligatoria de 2.700 s; `read_budget` devuelve `ok=true` y sin campaña activa. El cargo incorpora la corrección conservadora previa y la unión de bitácora y ledgers; no sumar de nuevo el tiempo de servicio.
- La última unidad aceptada registró `availability_lost=AC not connected`; a las 20:44 la CA era `1` y BAT1 estaba `Charging` al **44 %**. La nueva sesión sigue bloqueada por el mínimo de **50 %** de batería. MemAvailable era 6.622.724.096 B, disco libre 113.470.808.064 B, gestor `running` y `Linger=yes`; son mediciones del momento. **No se lanzó otra sesión.**
- Próxima acción: repetir las guardas actuales al alcanzar batería ≥50 %. Solo con suite formal, Ruff, preflight vigilado `ready`, saldo y tiempo antes de medianoche suficientes, iniciar una única sesión desde la frontera aceptada. El timer del 12/11 también exige sus propias comprobaciones. Validación 2023 y final 2024–2025 siguen cerradas.

---

# Reporte Codex — 11/11/2026 17:16 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `977bf53`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`.
- `wf-2022`: cargo propio medido en ledger 6846.916 s; última unidad 79.841 s.
- Último checkpoint `wf-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- `main-2018-2022`: ledger `ready`, 186 unidades aceptadas, cursor 16, pending=False; SHA-256 ledger `d0d4562da56e585f081c8bc7558f9c8db8b66c78fbcf216290cd5cbab1bf0b44`.
- `main-2018-2022`: cargo propio medido en ledger 12865.297 s; última unidad 78.920 s.
- Último checkpoint `main-2018-2022`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-v12-training-main-01/run-16-C0-b0/checkpoint-9`; estado SHA-256 `c33ff5961c1cbff19e81bb159155d31bf59957e03e7faa66ef287417878153a8`.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `0e49dcb508f9d3131156bd011508f080e61dbba3ec60c9987a3011f69a81261a`.
- Presupuesto global del día: 31675.357 s cargados; 16024.643 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Tres ternas principales aceptadas — 11/11/2026 15:35 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, servicio original todavía activo,
  `InvocationID=097bd51bfa774984a3913721e364f67e`. No se lanzó otro.
  `wf-2022` permanece cerrado y auditado: 99/99 unidades, 3/3 ternas.
- Principal al corte: **9/108 corridas, 3/36 ternas y 99 unidades de esas
  ternas completas**. La captura de ledger tenía 100 unidades aceptadas
  porque el bloque 3 había comenzado; no se cuenta como terna.
  SHA-256 de esa captura:
  `07a750e4bc5f068032223f5b40f66c879ecf2061c05b9840bd5366621df19bc9`.
  Auditoría: 99 checkpoints, 99 reportes y 99 solicitudes cotejados;
  [informe](docs/hitos/OOS-v1-2-tres-ternas-principales-20261111.md),
  [resultado](docs/evidence/oos-v12-main-three-triplets-20261111/audit.json).
- Tiempos medidos de unidades por terna: **2.258,869 / 2.246,075 /
  2.266,412 s**; media 2.257,119 s. El mayor RSS de trabajador fue
  672.030.720 B. A las 15:35:50 el débito global observado era
  **25.650,515 s**, saldo **22.049,485 s antes de la reserva** de 2.700 s;
  seguirá cambiando mientras la sesión esté abierta.
- Proyección de **entrenamiento**: 33 ternas × media = **74.484,917 s
  (20,690 h) de unidades**, más verificaciones y cierre. Si continúan
  ritmo, recursos y admisión, cierre posible alrededor del 13/11; no es
  promesa. La evaluación 2023/final tiene ruta sintética preparada en el
  worktree aislado, pero carece de permisos, fuente final auditada y costo
  histórico completo. No hay comparación financiera fuera de muestra.
- Próxima acción: esperar la pausa/cierre del mismo servicio; verificar
  ledger, huellas, presupuesto conciliado y última frontera antes de otra
  sesión. `failed`/`incomplete` no se reanudan. Validación y final cerrados.

---

# Primera terna principal aceptada — 11/11/2026 14:20 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, sesión original `oos-v12-training.service` aún activa con `InvocationID=097bd51bfa774984a3913721e364f67e`. No hay segundo lanzamiento; el supervisor pasó a la siguiente semilla.
- `wf-2022` permanece cerrado: 99/99 unidades, 9/9 corridas y 3/3 ternas auxiliares, con auditoría publicada. En el perfil principal hay **3/108 corridas, 1/36 ternas y 33 unidades completas** al corte; la siguiente unidad puede estar en marcha. Los K10 de la semilla `1869792951` son C0 `1ecc4be37436f2db928511a1346e0f08383b145c5342f7fc44f95ff3d3a5c4fd`, C5 `638113d2df49d70613daf4f950553fd13de75e0117c88b43ebe5324114004de4` y C10 `2aaee9fe8610635ca14e8e39e136a7e427f33d01e782aecebddb2de841ad0c4f` (SHA-256 de `state.pt`). Los tres actores cargaron en modo de solo lectura desde los checkpoints fijados.
- Tiempo **medido de unidades**: C0 772,220 s; C5 748,023 s; C10 738,626 s; terna 2.258,869 s. Auditoría: cadena de 107 estados en la captura y 33/33 huellas de cada tipo (checkpoint, reporte y solicitud). [Informe y comandos](docs/hitos/OOS-v1-2-primera-terna-principal-20261111.md); [resultado](docs/evidence/oos-v12-main-first-triplet-20261111/audit.json). [Tabla y gráfico](https://github.com/Ichurri/btc-risk-rl/tree/7f0b582/docs/evidence/oos-v12-main-progress-20261111) publicados en rama aislada.
- Presupuesto capturado a las 14:20:18: **21.118,462 s** globales del día, **26.581,538 s** restantes antes de la reserva de 2.700 s. Es una instantánea de sesión abierta, no el débito final. La sesión sigue ocupando el bloqueo; `blocked_for_other_session=true` es esperado.
- Extrapolación condicionada: 35 ternas restantes × 2.258,869 s = **79.060,411 s de unidades**, más futuras suites, carga, preflights, auditorías y cierres. A este ritmo el **entrenamiento** podría terminar alrededor del 13/11, sujeto a guardas y presupuesto. La evaluación 2023/final carece de permiso y costo histórico extremo a extremo; su fecha no está garantizada. No hay fuentes finales 2024–2025 identificadas en la lista local de archivos.
- Próxima acción: dejar continuar esta única sesión; al cerrar, auditar ledger, huellas, cargo conciliado y estado `ready/completed/failed`. El timer apunta al 12/11 01:00, pero otra sesión requiere cierre previo, suite, Ruff, preflight vigilado y admisión nuevos. Validación 2023 y final 2024–2025 siguen cerradas.

---

# Cierre del corte auxiliar wf-2022 — 11/11/2026 13:33 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit base `89f3d38`. Una sola sesión `oos-v12-training.service` (`InvocationID=097bd51bfa774984a3913721e364f67e`) sigue activa; terminó `wf-2022` y entró en la suite formal del perfil principal. No iniciar otra sesión.
- `wf-2022`: ledger `completed`, cursor 9, `pending=null`, **99/99 unidades, 9/9 corridas y 3/3 ternas C0/C5/C10**. La auditoría comprobó 302 estados encadenados y las huellas de los 99 checkpoints, 99 reportes y 99 solicitudes. Ledger SHA-256 `01b9da874d41cd22dac89e7976c7f0fe644094bfe687236536eb02d5cae85082`. Último checkpoint K10 `artifacts/oos-v12-training-wf-2022-01/run-08-C5-b0/checkpoint-10/state.pt`, SHA-256 `65f1d14d83800702fc3be627b463c1b1a020d35187a8af47bc56b6733171c1e7`.
- Tiempo **medido de unidades**: 6.832,147 s; cargo propio del ledger para el corte: 6.846,916 s. La diferencia comprende gastos supervisados fuera de los tiempos de unidades; no sumar ambos. La primera sesión OOS de hoy conserva su débito anterior de 10.800 s, compuesto de 6.942,163 s medidos y 3.857,837 s conservadores.
- Instantánea de presupuesto a las 13:33 con el token activo del nuevo preflight: 18.297,464 s de cargo global y 29.402,536 s antes de la reserva de 2.700 s. La sesión principal está haciendo suite; esas cifras seguirán aumentando y no son saldo de cierre. Evidencia: `docs/evidence/oos-v12-wf2022-closure-20261111/audit.json`, SHA-256 `ad948736bc852b146c017614af988e5cd58c7d343438828dac671a14e75fee39`.
- Entrenamiento principal: todavía sin ledger ni unidad aceptada a esta hora. Próxima acción: verificar que suite, Ruff, preflight y admisión pasen; dejar avanzar una única sesión, auditar la primera terna principal y actualizar la proyección de tiempos. La evaluación histórica 2023/final sigue cerrada.

---

# Avance en ejecución — 11/11/2026 12:15 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit base `496834c`; `.python-version` sigue eliminado solo localmente. Una sola sesión `oos-v12-training.service`, `InvocationID=097bd51bfa774984a3913721e364f67e`, permanece activa. No iniciar otra.
- La suite formal interna, Ruff y el preflight vigilado pasaron antes de Q0. En `wf-2022`, la primera terna auxiliar C0/C5/C10 está completa: 33/99 unidades aceptadas, 3/9 corridas y 1/3 ternas. El siguiente run `run-03-C5-b0` ya empezó; la captura posterior tenía 34 unidades aceptadas y unidad 1 activa.
- Tiempos **medidos de unidades** en la terna: C0 725,139 s; C5 730,349 s; C10 761,859 s. Total 2.217,347 s, sin incluir suite, carga, auditoría ni cierre. Las tres huellas K10 cotejadas con ledger son `ce1d9760b42e8b863d7deef83b9557097f724747a9111fffa4e18a3782f84091`, `fc690584dcde2d0a36fe7388c44036a4ebe92a3fbe8e7f9d3e37e7e29c8d0c29` y `a746d15ac1d6d82949ea2ad524453e46efc231b5e014e72bce1cd70edd2d8545`, respectivamente. La cadena del ledger pasó 107 estados en la captura de la primera terna; su SHA-256 entonces era `4fda19d572644d73612c2819148e75be42c7ebc2f868fa1ec90dec84ace0a0ba` y seguirá cambiando mientras la sesión avance.
- Instantánea de presupuesto a las 12:15: **13.655,430 s** cargados globalmente y **34.044,570 s** antes de la reserva de 2.700 s. Incluye 10.800 s anteriores conservadores y tiempo nuevo de la sesión, sin llamar a la captura saldo final. La consulta externa marca otra campaña como activa por diseño; la admisión la hace el supervisor bajo su propio token y bloqueo.
- Próxima acción: dejar avanzar la misma sesión, auditar su cierre y los checkpoints completos, actualizar tiempos/cargos y conservar el próximo arranque programado solo si el ledger queda `ready`. `wf-2021` permanece íntegro como diagnóstico descriptivo; su exclusividad original no está demostrada. Validación 2023 y final 2024–2025 siguen cerradas.

---

# Avance de sesión — 11/11/2026 11:51 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit de método `5fcdf75` y permiso `8860fb9`; la sesión `oos-v12-training.service`, `InvocationID=097bd51bfa774984a3913721e364f67e`, sigue activa. Timer siguiente: 12/11 01:00, sin sesión duplicada.
- La suite formal **interna** pasó en 554,642 s, Ruff pasó en 0,032 s y preflight vigilado `ready` en 1,424 s. `wf-2022/C0`, semilla 57739409, primera corrida: Q0 + 10 actualizaciones aceptadas en 725,139 s de unidades; checkpoint K10 `artifacts/oos-v12-training-wf-2022-01/run-00-C0-b0/checkpoint-10/state.pt`, SHA-256 `ce1d9760b42e8b863d7deef83b9557097f724747a9111fffa4e18a3782f84091` cotejado. El ledger pasó a la siguiente corrida; no hay fallo registrado.
- A las 11:50 local, el débito global OOS era 12.168,398 s y el saldo antes de reservar 2.700 s era 35.531,602 s. Esta es una instantánea con la sesión activa, no saldo final. El cargo conservador anterior de 10.800 s incluye los 6.942,163 s medidos del primer bloque 2021 y un ajuste de 3.857,837 s.
- Proyección **solo de entrenamiento**: 116 corridas restantes × 725,139 s de primera corrida 2022 ≈ 84.116 s de unidades, más comprobaciones, cargas y cierres. Con el presupuesto ampliado y sin bloqueos podría terminar hacia el 13/11; la evaluación histórica no está instrumentada ni medida y **no tiene fecha garantizada**. La metodología de inferencia se fijó antes de abrir 2023/final; esos datos siguen cerrados.
- Próxima acción: dejar al supervisor admitir unidades completas hasta su pausa/cierre, comprobar ledger, checkpoints, memoria y presupuesto; mantener la exclusividad de la sesión. Un ledger `failed` no se reanuda.

---

# Estado en ejecución — 11/11/2026 11:30 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `fef5d74`; enmienda `b86ea47`, código `20c3e96`, permiso v3 `8860fb9`.
- Suite manual: 587 passed en 570,02 s; Ruff correcto. Preflight manual vigilado `ready`, CA conectada, batería 98 %, `MemAvailable=6.868.131.840 B`, 4.678 rutas `wf-2022`, sin aperturas protegidas. Evidencia: `docs/evidence/oos-v12-expanded-20261111/preflight.json`.
- Una sesión `oos-v12-training.service` inició el 11/11 a las 11:28:14, `InvocationID=097bd51bfa774984a3913721e364f67e`, `Restart=no`. A las 11:29 estaba en la suite formal interna, sin ledger ni Q0 de `wf-2022`. No duplicar el lanzamiento.
- Presupuesto ampliado: 50.400 s globales por fecha y 2.700 s de reserva; hoy se cargan 10.800 s previos conservadores (6.942,163 s medidos + 3.857,837 s de ajuste). Antes de esta sesión quedaban 36.900 s productivos; la bitácora cobrará su tiempo nuevo.
- `wf-2021`: 99/99 unidades y 9/9 corridas íntegras, raíz histórica conservada; exclusividad del bloqueo original no demostrada. `wf-2022`: 0/99 al iniciar; principal: 0/1188.
- Próxima acción: esperar suite, Ruff y preflight internos; auditar Q0, unidades, ledger y checkpoint al cierre. Si bloquea recursos, no iniciar unidad; si falla dentro de una unidad, no reanudar. Timer diario siguiente 12/11 01:00.
- Validación 2023 y prueba final 2024–2025 siguen cerradas.

---

# Continuación preparada — 11/11/2026, 08:50 America/La_Paz

- Rama `codex/oos-v12-training-root-fix`; código `1dcff09`, nueva
  aprobación `dbffdf6`. `.python-version` sigue eliminada solo localmente.
- Se corrigieron las tres raíces para que coincidan con el protocolo y
  preparación/supervisor compitan por el mismo `global.lock`. Las dos
  pruebas de regresión fallaron antes del cambio y pasaron después;
  suite completa **585 passed en 539,80 s**, dos advertencias de `fork`
  sintético, Ruff sin errores. Permiso v2 SHA-256
  `ef601eb95df48e3f3376b11d61eb64328914b225c43927c7e8baa12142f5c806`;
  huella de código `662edcea4367ea8a6f470cbb0a64ab25f0827585f55f0ccfc1fc7d159aa70177`.
- `wf-2021`: ledger original en `artifacts/artifacts/` **intacto**,
  9/9 corridas, 3/3 ternas, 99/99 unidades; cadena y las 99 huellas de
  checkpoints/reportes/solicitudes verificadas. Último checkpoint:
  `artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10/state.pt`,
  SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
  Las 99 unidades habrían cabido con la reserva en la reconstrucción
  conservadora; margen mínimo 1.128,211 s. **Integridad aceptada, uso como
  prueba de cumplimiento estricto del supervisor pendiente de revisión.**
  No repetir ni migrar el corte.
- `wf-2022`: ninguna unidad iniciada; es independiente de los pesos y
  checkpoints de 2021. El selector lo identifica como próximo perfil.
  Timer habilitado para **12/11/2026 01:00 America/La_Paz**, servicio ahora
  inactivo, `Restart=no`. Suite, Ruff, preflight vigilado y admisión con
  saldo/reserva se repetirán en esa ventana; si falla una puerta, no se
  inicia Q0. El contador automático del 11/11 no incluye la suite manual
  posterior de 539,80 s ni todo el trabajo de desarrollo: no usarlo para
  admitir más unidades hoy.
- Informe, comandos y evidencia:
  `docs/hitos/OOS-v1-2-entrenamiento-ruta-presupuesto-20261111.md` y
  `docs/evidence/oos-v12-training-root-fix-20261111/`.
  **Próxima acción:** auditar el servicio del 12/11, ledger y último
  checkpoint completo; conservar 2023 y la prueba final cerrados.

---

# Reporte automático — 11/11/2026 08:47 America/La_Paz

- Rama `codex/oos-v12-training-root-fix`, commit `dbffdf6`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: sin ledger; no se inició una unidad.
- `main-2018-2022`: sin ledger; no se inició una unidad.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `f372dc56f36e41e8e3948ecccc4d45ebf8f251d32c4ff1f13d39034fed3a915d`.
- Presupuesto global del día: 6942.163 s cargados; 1157.837 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Cierre auditado — 11/11/2026, 02:56 America/La_Paz

- Rama `codex/oos-v12-training-prep`, base publicada `a5eef29`, código
  `1ce1382` y permiso `cbd11de`. La eliminación local de `.python-version`
  permanece fuera de los commits.
- `oos-v12-training.service` terminó `Result=success` a las 02:55:46,
  `InvocationID=67732d86aae44562a2e68a34d14b2124`. No queda servicio
  de entrenamiento activo. Suite formal, Ruff y preflight vigilado pasaron;
  este último confirmó CA, 9.254.907.904 B de memoria disponible, 3.639
  rutas 2021 y ninguna apertura protegida.
- `wf-2021`: **9/9 corridas, 3/3 ternas C0/C5/C10 y 99/99 unidades**;
  ledger `completed`, `pending=null`. La cadena de 302 estados y las 99
  huellas de checkpoints, reportes y solicitudes coincidieron. Último
  checkpoint válido:
  `artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10/state.pt`,
  SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
  Ledger SHA-256 `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
  `wf-2022` y el perfil principal siguen sin iniciar.
- Cargo global del 11/11: **6.942,163 s**, incluidos preparación y unidades
  sin duplicar los 6.401,296 s del ledger. Saldo antes de la reserva de
  2.700 s: **1.157,837 s**. A las 02:55 se bloqueó el comienzo de `wf-2022`
  porque no cabían suite, Q0 y cierre; no fue un fallo de unidad.
- **Desviación de ruta:** el protocolo fija `artifacts/oos-v12-training-*`,
  pero el código escribió el corte 2021 en `artifacts/artifacts/oos-v12-training-*`.
  Por ello el supervisor de unidades usó otro bloqueo/presupuesto compartido.
  La bitácora principal sí midió la sesión completa y el cargo quedó dentro
  del límite global, pero la admisión por unidad no fue la ruta congelada.
  Se deshabilitó el timer nocturno, sin interrumpir esta sesión. Los artefactos
  originales se conservan; **no repetir ni migrar el corte 2021**.
- **Siguiente acción:** adjudicar la desviación, corregir prospectivamente
  ruta/contabilidad con pruebas y nueva huella de permiso, y solo entonces
  reactivar el timer para una ventana futura con preflight nuevo. Validación
  2023 y prueba final 2024–2025 siguen cerradas. Detalle y comandos:
  `docs/hitos/OOS-v1-2-entrenamiento-sesion-20261111.md`.

---

# Reporte automático — 11/11/2026 02:55 America/La_Paz

- Rama `codex/oos-v12-training-prep`, commit `a5eef29`.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: sin ledger; no se inició una unidad.
- `main-2018-2022`: sin ledger; no se inició una unidad.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `f372dc56f36e41e8e3948ecccc4d45ebf8f251d32c4ff1f13d39034fed3a915d`.
- Presupuesto global del día: 6942.163 s cargados; 1157.837 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 10/11/2026, 10:57 America/La_Paz

- Rama `codex/oos-v12-training-prep`; código `1ce1382`, permiso de
  entrenamiento exclusivo `cbd11de`. `.python-version` sigue borrada solo
  localmente y fuera de los commits.
- La suite final pasó **576 pruebas en 573,22 s** (dos advertencias del
  `fork` sintético); Ruff pasó. Comprobación de fuentes de solo lectura:
  3.639/4.678/7.048 inicios, solo derivado H1 de entrenamiento y
  manifiesto H1 compartido. No se generaron trayectorias ni se entrenó.
- Timer `oos-v12-training.timer` habilitado, próximo disparo
  **11/11/2026 01:00 America/La_Paz**; servicio `oos-v12-training.service`
  inactivo y tres raíces de campaña ausentes. No hay unidad OOS aceptada.
  El servicio tiene `Restart=no` e inhibición de sueño; con CA se cambió la
  preferencia GNOME de suspensión automática de `suspend` a `nothing`.
  El timer `oos-v12-restore-power.timer` restaurará `suspend` el
  **16/11 a las 09:05** (`Persistent=true`); verificar el cierre.
- Captura 10:57: CA=1, batería 98 %, `MemAvailable=5.536.272.384 B`
  frente al mínimo inicial 6.026.846.208 B, disco 125,79 GB,
  `systemd --user=running`, `Linger=yes`. La memoria debe volver a superar
  el umbral en el preflight nocturno; con la captura actual se bloquearía.
- Presupuesto medido 10/11: WF 2022-03 cargó **1.247,845 s**; saldo antes
  de reserva 6.852,155 s. Para 11–16/11 hay como máximo 48.600 s
  productivos suponiendo saldo íntegro. Extrapolación: 16 ternas como
  techo sin gasto adicional, 14/13 con 500/900 s diarios supuestos. No
  implica que estén entrenadas; el roster conserva las 36 previstas.
- Evidencia: `docs/hitos/OOS-v1-2-entrenamiento-preparacion.md`,
  `docs/evidence/oos-v12-training-prep-20261110/`,
  `docs/protocols/OOS-v1-2-training-freeze-20261110.json` y aprobación
  `docs/protocols/OOS-v1-2-training-approval-20261110.json`.
- Siguiente acción: a la 01:00, el servicio repite suite, Ruff y preflight
  vigilado; solo con `ready`, CA, memoria, presupuesto y admisión inicia
  Q0. Tras la sesión, auditar ledger, journal y checkpoint. Un estado
  `failed`/`incomplete` no se reanuda. Validación 2023 y prueba final
  2024–2025 permanecen cerradas.

---

# Reporte anterior — 10/11/2026, 02:10 America/La_Paz

- Rama `codex/oos-wf-2022-03`, base publicada `69aaf80` al iniciar. `.python-version` sigue eliminada solo localmente.
- El timer de 01:00 desapareció tras reinicio a 01:39:29; no produjo intento ni Q0. Tras liberar memoria se repitieron guardas (8.927.092.736 B en captura inicial; 9.362.132.992 B en preflight formal; mínimo 6.026.846.208 B).
- Una sola sesión `oos-wf-cost-2022-03-session-02.service`, `InvocationID=367e1c7feaad4a268a3f31069f35bfe7`, se inició 01:43:56 y terminó 02:04:46 con `Result=success`, `Restart=no`. No hay proceso WF activo.
- Suite formal **549 passed en 527,07 s**, Ruff y preflight vigilado `ready`. Ledger `completed`, **11/11** unidades, `pending=null`: Q0 y diez Q/A/B+D. Los 11 checkpoints y 11 reportes coinciden con las huellas del ledger. Último checkpoint `artifacts/oos-v12-wf-cost-only-2022-03/wf-2022/checkpoint-10`, estado SHA-256 `5740732f226667d79ede579f4be96afc71705882cb68e53c1e6eb75c5fc2ea2e`.
- Preparación 531,643 s, segunda fase 716,202 s; cargo total reconciliado **1.247,845 s**, saldo global **6.852,155 s antes de la reserva de 2.700 s**. Servicio: pared 20 min 50,189 s, pico de memoria 2,1 GiB. No sumar la duración del servicio ni el ledger otra vez al cargo de la bitácora.
- Evidencia: `docs/hitos/OOS-v1-2-costo-2022-03-cierre.md`, `docs/evidence/oos-wf-2022-03-relaunch-20261110/` y artefactos originales en `artifacts/oos-v12-wf-cost-only-2022-03/`. No se abrió validación ni prueba final.
- Siguiente acción: recalcular el calendario de evaluación v1.2 con el costo medido y resolver la prórroga y los cambios académicos antes de congelar el protocolo. La evaluación confirmatoria sigue cerrada; WF05, `2022-01` y `2022-02` no se reanudan.

---

# Reporte anterior — 09/11/2026, 13:06 America/La_Paz

- Rama `codex/oos-wf-2022-03`. Base `85a08b9`; diagnóstico `6548215`, perfil `9ba423f`, primer permiso sin uso `d0f024c`, corrección `87c544c`, permiso final `3aa8aeb`. La eliminación local de `.python-version` sigue fuera de los commits.
- `2022-02` permanece `failed`: Q0 e iteraciones 1–7 aceptadas (8/11), unidad 8 parcial por `MemAvailable=4.278.210.560 B` (<4 GiB). Último checkpoint completo `artifacts/oos-v12-wf-cost-only-2022-02/wf-2022/checkpoint-7`, estado SHA-256 `618f9b45c42cf7e0976c1b8d6caadde39fddcfe1586a1173f3a5506295c9b0e1`. Ledger, sesión y supervisor conservaron sus huellas; no se reanuda ni repite. WF05 y `2022-01` siguen cerrados.
- Sondas sintéticas de memoria de duración representativa: 04 cruzó 4 GiB durante suite; 05 duró 1127,131 s y sostuvo mínimo 4.870.426.624 B, solo 38.588.416 B sobre 4 GiB + 512 MiB. La causa externa exacta de la caída histórica sigue desconocida. Informe: `docs/hitos/OOS-v1-2-costo-2022-02-memoria-diagnostico.md`.
- Perfil nuevo `2022-03`: una C10, semilla 498614892, Q0 + diez Q/A/B+D, raíz exclusiva `artifacts/oos-v12-wf-cost-only-2022-03/` aún **ausente**. Puerta inicial de memoria 6.026.846.208 B; guarda de 4 GiB durante unidades sin cambio. La aprobación final SHA-256 es `c72292883224c50f86f0ae6a27b2ee6e4aaeed3ee548751cd81f3ac7f7ce73d4`, código `89f9aae6490778170a50aa65596b836ab9dd507447bc526ca34be4adab61bf33`.
- Pruebas realmente ejecutadas: suite completa bajo `systemd --user`/bloqueo global/inhibición de sueño **549 passed en 534,82 s**, focal con permiso final **44 passed en 97,88 s**, `uv run --frozen ruff check .` correcto. Dos suites sintéticas intermedias se detuvieron al detectar guardas incompletas; sus journals se conservan. No hubo entrenamiento `2022-03` ni acceso a validación o prueba final.
- Presupuesto: 09/11 tiene 10.800/10.800 s globales cargados conservadoramente por el fallo `2022-02`, saldo 0. Para 10/11, la instantánea de solo lectura muestra 0 s externos y 8.100 s antes de reserva, sujeto a comprobación nueva. Límites `2022-03`: 3.600 s propios/día, 4.800 s acumulados, dos días activos, reservas propias/globales 600/2.700 s; ventana 01:00–09:00 La Paz.
- Estado de sesión: timer `oos-wf-cost-2022-03-session-01.timer` **active/waiting** para 10/11/2026 01:00 La Paz; servicio `Restart=no`, aún sin `InvocationID` ni unidades. La captura `docs/evidence/oos-wf-2022-03-memory/timer-scheduled-20261109.txt` tiene SHA-256 `2ca6c3e4c789d3f9150ff044b9057ad6cb16b7d063e4b1cd50136b06c0e328b1`. El equipo debe permanecer encendido y sin suspensión hasta el disparo; el servicio inhibe suspensión después.
- Captura de recursos de 09/11 13:04: CA=1, batería=94 %, gestor `running`, `Linger=yes`, `MemAvailable=5.054.701.568 B` (inferior a la nueva guarda inicial), disco disponible 126.937.419.776 B. No anticipa los valores de la noche. Si la memoria sigue baja o alguna puerta falla, no se inicia una unidad de mercado.
- Siguiente acción: al disparar el timer, `--prepare` abre bitácora y ejecuta suite, Ruff, preflight vigilado y admisión con reservas; solo después `--run` puede comenzar Q0. Auditar `systemctl --user show oos-wf-cost-2022-03-session-01.service`, su journal, `artifacts/shared-pilot-budget/wf-2022-only-03-{attempts,checks}.jsonl` y, si existe, el ledger/checkpoint. Un estado `failed` no se reanuda. La evaluación v1.2 sigue sin adoptar; validación 2023 y prueba final permanecen cerradas.
