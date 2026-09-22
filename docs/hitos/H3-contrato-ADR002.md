# H3 — adopción ADR-002 v2.1 y simulador de horizonte finito

Fecha: 22-09-2026. Base revisada: e4e2e8fada77f9b1116f3b265368e82c1e82cedd.
Registro de adopción: 10d92fa. Código verificado: ebb3914.
Rama: [codex/adopt-adr002-v2-1](https://github.com/Ichurri/btc-risk-rl/tree/codex/adopt-adr002-v2-1).

## Alcance y decisión

El usuario aprobó v2.1 como contrato metodológico y autorizó adaptar el simulador.
[ADR-002](../decisions/ADR-002-risk-horizon.md) registra la adopción y los puntos
de congelación pendientes. Las propuestas v1, v2 y v2.1 y su evidencia se conservan
íntegras, con sus estados históricos; ya no representan el estado operativo.

No se implementaron agentes, recolector de políticas, optimizadores o evaluación
estadística. No hubo entrenamientos, instalaciones de PyTorch/CUDA, cambios de
drivers ni acceso al conjunto final. La tesis no se modificó.

## Contrato H3 e incompatibilidades intencionales con H2

| Elemento | H2 | H3 |
|---|---|---|
| Configuración | schema 1 | schema 2, contract_version=finite_horizon_v2 |
| Observación float64 | 12 componentes | 13: mismos primeros 12 y reloj al final |
| Índices Python | mercado 0:10, peso 10, log patrimonio 11 | iguales; reloj 12. No usar -1 para log patrimonio ni -2 para peso |
| Entrenamiento | ventana de inversión continua, descuento pendiente | objetivo finito H=180, gamma=1, reloj (180-j)/180 |
| Paso 180 de entrenamiento | terminated=False, truncated=True | terminated=True, truncated=False, reloj 0 |
| Valor posterior a H | no decidido | cero; bootstrap_mask=trace_mask=0 |
| Validación | cartera continua, truncación final | igual cartera y truncación; reloj siempre 1 |
| Mercado/normalizador | market10_portfolio2_v1 en productos H1 | versión histórica conservada; observation_version=market10_portfolio2_clock1_v2 identifica el vector nuevo |

R=sum(r)=log(E_H/E_0), pérdida L=-R. Gamma no multiplica la recompensa del entorno:
es el descuento del objetivo, fijado en configuración. El futuro agente deberá
consumirlo y usar Monte Carlo completo con lambda_GAE=1. El simulador no implementa
ventajas, crítico ni CVaR.

terminated expresa final del objetivo finito, no quiebra económica ni venta
forzada. La posición se conserva marcada al cierre; no se añade liquidación.
end_reason mantiene la procedencia de disponibilidad de H2 y puede coincidir
con un objetivo completo, sin cambiar su retorno. La observación final es real,
sin autoreset.

## Cortes y elegibilidad

| Situación | Flags Gym | Máscaras b/c y targets | Muestra de riesgo |
|---|---|---|---|
| Paso interno de entrenamiento | False/False | 1/1 para transición observada; esperar episodio completo para targets | No todavía |
| H, motivo collection_window | True/False | 0/0, V_H=0 | Completa |
| H, motivo segment_boundary | True/False | 0/0; no cruzar interrupción | Completa |
| H, motivo partition_boundary | True/False | 0/0; no incorporar validación | Completa |
| Checkpoint administrativo m<H | No emite transición Gym | None/None pendientes; esperar y ensamblar | Incompleta |
| Ruta de entrenamiento de menos de H | Error de integridad al construir entorno | No bootstrap, target cero ni continuación inventada | Rechazada |
| Validación interna/final | False/False; al final False/True | None/None, sin aprendizaje | Nunca muestra del objetivo finito |

collection_checkpoint() solo devuelve copia de observación y metadatos;
no ejecuta acción, emite recompensa, cambia reloj, resetea ni serializa estado.
Se admite entre el primer paso y el penúltimo de entrenamiento. El mismo objeto
continúa con step. collection_cut=True identifica exclusivamente ese checkpoint;
no es otro flag Gym. La prueba pausa en 60, continúa hasta 180 y obtiene exactamente
las mismas observaciones, rewards y cuentas que un recorrido sin checkpoint.

trajectory_complete y cvar_eligible describen completitud **temporal de
entrenamiento**, necesaria pero no suficiente para un lote Q/A/B válido.
El entorno no conoce la política generadora: identidad de realización y política
congelada, persistencia del buffer, ensamblaje y rechazo de lotes siguen siendo
obligaciones del futuro recolector. trajectory_start_ms, trajectory_end_ms,
partición y segmento identifican la ruta; no distinguen dos realizaciones sobre
el mismo inicio. Un fallo de trayectoria debe abortar y diagnosticar el lote,
sin reemplazo selectivo. Este hito no afirma verificar esas obligaciones futuras.

## Conservación de datos y cuentas

env/accounting.py, env/market.py y features/market.py conservan exactamente
sus bytes de H2. Comisiones, deslizamiento, acción de exposición posterior a
costos, ejecución en siguiente apertura y recompensa logarítmica neta no cambian.

El manifiesto H1 contiene la configuración completa de schema 1. El nuevo puente
no reescribe el manifiesto ni ignora diferencias: construye la única configuración
antigua admisible revirtiendo los campos aprobados y exige igualdad del documento
entero. Cambian exclusivamente schema_version, horizon_mode, los cuatro campos
nuevos del contrato y dos estados de investigación. Costos, efectivo inicial,
H, datos, fronteras, características y controles deben coincidir. Una configuración
nueva idéntica usa modo exact. Ambas rutas ejecutan la auditoría completa.

Los productos H1 y su scaler se verifican por hashes, reconstrucción de tablas y
momentos, sin fit. Se conserva su aceptación técnica bajo política B; no se vuelve
a preparar el mercado ni se modifica el índice. El informe del auditor incorpora
el modo de compatibilidad y los campos cambiados para hacer visible esta migración.

## Evaluación y límites científicos

El recorrido continuo mantiene una cartera con w/z reales y h=1, incluido el final.
No hay reset cada 180, cambio de referencia de patrimonio, refit ni actualización.
Las pruebas verifican cartera heredada con reloj uno; no prueban transferencia
de ninguna política. La discrepancia de soporte h=1 entre entrenamiento y despliegue
sigue reconocida. Un Sortino superior no acredita una restricción CVaR a 30 días.

Se preserva la métrica primaria: Sortino anualizado sqrt(2190) por S_4h, retornos
simples netos, MAR=0, desviación bajista sobre todos los períodos e indefinido si
es cero. La anualización es una convención sin independencia temporal. Se mantiene
pareamiento por bloques de semillas, bootstrap unilateral centrado de la media y
Holm (.05 familiar); no se ejecuta inferencia en este hito.

## Evidencia de esta ejecución

Véanse [comandos](../evidence/simulator-h3/COMMANDS.md),
[resumen de auditoría](../evidence/simulator-h3/simulation-summary.json) y
[comparación H2/H3](../evidence/simulator-h3/compatibility-results.json).
Los logs rojos son fallos esperados anteriores a la implementación, no fallos abiertos.
Las verificaciones nuevas se distinguen de la evidencia histórica H2 usada como
referencia. El libro completo permanece fuera de Git, identificado por SHA-256.

### Resultados locales comprobados

- Ruff sin errores; suite completa: **117 aprobadas en 23.73 s**.
  Incluye las 17 nuevas pruebas temporales/compatibilidad, los oráculos contables
  Decimal y controles causales y de acceso existentes.
- Auditoría de desarrollo: **7048 índices**, **15 segmentos utilizables**,
  **31 recorridos y 7590 transiciones** (30 episodios de entrenamiento y
  un recorrido continuo de 2190 pasos de validación, con un único reset).
  Es una prueba con acciones prefijadas, no una evaluación de un agente.
- Puente histórico H1 aplicado y auditado; **10073 observaciones de ajuste**;
  no refit. Hashes de fuentes, máscara, índices, productos y scaler intactos.
- Regresión sintética nueva: ejecución de H2 y H3 sobre 180 + 2190 transiciones,
  primeros 12 componentes, rewards y campos contables exactamente iguales.
- Comparación del libro H3 nuevo con el libro histórico H2 previamente identificado
  por hash: **7590 filas iguales** en todos los campos originales salvo flags
  temporales. No se presenta el libro H2 como una nueva ejecución de mercado.
- Revisión independiente: sin defectos accionables. Confirmó que identidad de
  política y ensamblaje de lotes pertenecen al futuro recolector.

Entorno local: Python 3.12.13, NumPy 2.5.3, pandas 2.3.3, Gymnasium 1.3.0,
pytest 9.1.1, Ruff 0.16.8; kernel Linux 6.12.107+deb13-amd64.
El resumen registra fecha UTC, commit completo, estado Git, comandos y huellas.

**Aceptación del hito:** contrato temporal implementado y verificado; datos H1
mantienen su aceptación técnica B. No constituye aceptación de agentes, control
empírico de CVaR, generalización o autorización confirmatoria.

## Próximo hito, requiere autorización

Diseñar e implementar agentes y recolector con versión de observación explícita,
Monte Carlo completo, buffers sin mezcla de políticas, roles Q/A/B y control de
recursos. Probar cuantil y empates, F a eta fijo frente a CVaR empírico,
orden/congelación de actualizaciones, equivalencia C0 bit a bit y rechazo de
fragmentos/censura. Luego acordar protocolo de pilotos y parámetros comunes.
Esta lista no es autorización para implementar agentes o entrenar.
