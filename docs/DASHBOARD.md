# Dashboard comparativo local

Una página HTML en español, sin servidor, bibliotecas remotas ni acceso a
modelos en ejecución. Usa únicamente documentos auditados, ledgers y reportes
aceptados. No abre CSV, datos de 2023/final, NPZ de trayectorias ni checkpoints.

Desde la raíz del repositorio, regenerar y abrir:

```bash
uv run --frozen python scripts/build_thesis_dashboard.py
xdg-open reports/avance-tesis/index.html
```

El HTML y `datos.json` se guardan en `reports/avance-tesis/`, ignorado por Git.
Los selectores funcionan con datos incrustados incluso sin conexión. Los enlaces
de evidencia apuntan a archivos locales; trasladar solo el HTML conserva los
gráficos, pero no traslada esos archivos. La exportación es una instantánea:
regenerar para incorporar nuevos cierres. El generador detecta estado y unidades
aceptadas de los ledgers disponibles y exige concordancia P3 con el cierre auditado.
Los gastos de WF05 se interpretan con su adjudicación `incomplete`, preservando el
ledger técnico `ready`. Ausencia de un ledger se rotula sin evidencia disponible;
una discrepancia de integridad P3 detiene la exportación.

## Comparaciones y fuentes

| Vista | Población y métrica | Fuente | Límite |
| --- | --- | --- | --- |
| P3, inicial | Nueve pares semilla–condición; ambos críticos sobre D de cada brazo; MSE, Z, MSE/Z y sesgo; k=7,8,9 | `docs/evidence/p3-cross-diagnostic/results.json`, commit `810926b`; ledger y 18 reportes originales verificados | Cada columna fija objetivos/observaciones; la celda cruzada puede estar fuera de distribución de política. No causalidad pura ni nueva selección. |
| P3, riesgo desplegable | Última auditoría B de cada brazo: η, función variacional F_B, CVaR empírico ρ_B, λ | `artifacts/p3-approved-v1/run-*/unit-10.json`, solo reportes aceptados y hash verificado | B forma parte del aprendizaje; no prueba cumplimiento poblacional ni activación de shortfalls A. |
| P1 | MSE post-A de primera actualización, dos y cuatro épocas, por semilla | `docs/evidence/p1-execution/closure-checks.json` e informe `811d882` | Ajuste sobre el mismo A; C0/C5/C10 repiten la comparación inicial, no nueve réplicas. |
| P0, P2, P2R, WF05 | Unidades aceptadas/previstas, suma de tiempos de unidades y pico RSS de workers | Ledger original local de cada campaña y su informe de cierre; SHA registrado en exportación | Excluye unidades parciales y gastos de preparación/cierre; no comparar como benchmark de velocidad. |

P2 se informa interrumpido. P2R conserva `review` y alcance descriptivo, sin
convalidar retrospectivamente su marcador. WF05 sigue cerrado. La medición
histórica exclusiva 2022 y la evaluación fuera de muestra siguen pendientes.
No hay curvas de patrimonio/drawdown de una evaluación compatible: se informa
«Sin evidencia disponible». Los gráficos técnicos no demuestran rentabilidad,
superioridad financiera, generalización temporal o cumplimiento CVaR.

## Procedencia de los cuatro objetivos

Se consultó en solo lectura el documento de tesis indicado por Santiago:
https://docs.google.com/document/d/1dNp8MbiV0Zqpu6S9-5u6vnL-R-v4YbYaR8g6232EBQ8/edit
el 05/11/2026. No se modificó. Extracto de sección 1.3.2:

1. Diseñar el módulo de función objetivo sensible al riesgo del agente.
2. Construir el simulador del entorno histórico del mercado de Bitcoin.
3. Implementar el protocolo experimental del agente con control de sobreajuste de backtest.
4. Evaluar el agente sensible al riesgo frente al agente neutral al riesgo.

Los estados del dashboard son una síntesis de implementación y evidencia,
no una evaluación formal del cumplimiento académico.

## Recorrido sugerido de cuatro minutos

1. **0:00–1:00, vista inicial P3.** Explicar que los dos críticos reciben
   exactamente el mismo D. Señalar MSE, predictor cero y tabla; cambiar a
   semilla 710047 para mostrar que la diferencia no tiene un signo universal.
   Recordar la limitación de política ajena y la decisión `review`.
2. **1:00–1:45, agentes y objetivos.** Distinguir PPO neutral C0 de CVaR-PPO
   C5/C10, y β de la condición de riesgo. Mostrar los cuatro objetivos:
   función y simulador implementados, protocolo en integración, evaluación pendiente.
3. **1:45–2:45, P1 y pilotos.** Seleccionar P1: cuatro épocas mejoraron ajuste
   inicial sobre A, sin demostrar desempeño financiero. Revisar P2 interrumpido
   y P2R descriptivo. No comparar tiempos de campañas como superioridad.
4. **2:45–4:00, WF05 y próximos pasos.** Mostrar 11/22 unidades y cierre
   incomplete. Distinguir orquestador sintético, costo histórico 2022 pendiente
   y futura evaluación fuera de muestra. Terminar señalando evidencia y commits.

## Verificación reproducible

```bash
uv run --frozen pytest -q tests/test_thesis_dashboard.py
uv run --frozen ruff check .
# Solo para verificar la interfaz; no es una dependencia del dashboard:
uv run --with playwright==1.64.1 python scripts/check_thesis_dashboard_browser.py
```

La última orden usa Chromium local en la ruta indicada en el script; puede
ajustarse con `DASHBOARD_CHROMIUM=/ruta/al/chrome`. No descarga un navegador.
Genera capturas `inicio.png`, `principal.png`, `p1.png` y `wf05.png` en la salida
ignorada. Se verificaron 18 selecciones P3, tres semillas P1, cuatro pilotos
operativos, valores contra fuentes auditadas, ausencia de errores JavaScript
y ancho móvil. Ver `docs/evidence/dashboard-avance/`.
