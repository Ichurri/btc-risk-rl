# Propuesta de pilotos después de H4 — NO AUTORIZADA NI EJECUTADA

Este plan no aprueba hiperparámetros ni habilita mercado. Requiere autorización
separada. Se usaría exclusivamente entrenamiento anterior a 2023, con índices H1,
normalizador persistido y H3 intactos. No usar validación para elegir reloj,
cota, fórmula o configuración ganadora; conjunto final bloqueado.

## Objetivo y límite diario

Medir costo, estabilidad numérica y precisión de cola; no demostrar rendimiento
fuera de muestra. Presupuesto máximo: **180 minutos diarios de cómputo**.

| Bloque diario propuesto | Límite |
|---|---:|
| Preflight, huellas y reserva de arranque | 15 min |
| Ejecución de unidades completas planificadas | 135 min |
| Auditoría, guardado y margen de cierre | 30 min |

No se conoce todavía el tiempo de una iteración de mercado. Los tiempos sintéticos
de H4 no se extrapolan a mercado, convergencia ni GPU. CPU es la única plataforma
verificada; no se propone instalar CUDA ni usar la estimación de VRAM como medición.

## P0 — calibración técnica previa, con autorización futura

Crear primero un comando de piloto separado y con alcance explícito; el ejecutor
actual solo admite la fuente sintética. Integrar un adaptador de índices aceptados
que conserve sus guardas, y probar serialización de actor, crítico, optimizadores,
eta, multiplicador, generación, streams, presupuesto y protocolo para reanudación.
H4 solo serializa trayectorias; no permite reanudar corridas. Estas son condiciones
de entrada, no capacidades ya entregadas.

Tras autorización, medir por separado Q inicial, A, actor, crítico, Q nuevo y B
con CPU, registro de tiempo monotónico y memoria máxima. Usar tres mediciones
completas por configuración; registrar versiones/hilos, fallos y dispersión.
Un fallo invalida la corrida; no reiniciar hasta obtener una cola favorable.

Propuesta inicial para dimensionar (no hiperparámetros aprobados):
N_A=64, N_Q=N_B=400, una capa oculta de 32 unidades, épocas actor/crítico=2,
minibatches de 16 trayectorias completas. Masa esperada de cola Q/B: 20 para C5
y 40 para C10, precisión todavía por comprobar. No constituyen 400 períodos
económicos independientes: los inicios H1 se solapan.

Con esa estructura, cada condición consume:
N_tray=400+864K; N_trans=72000+155520K. Incluye Q0 y ambos auxiliares, también C0.

Sea t0 el máximo observado para Q0 y t_i el máximo para una iteración completa
en las configuraciones/condiciones a comparar. Planificar con margen:
t0_seguro=1.25*t0, t_iter_seguro=1.25*t_i.
Elegir K común tal que t0_seguro+K*t_iter_seguro <= 135 minutos.
Si no cabe una iteración completa, no ejecutar el piloto: proponer reducción
común del diseño y volver a aprobarla. No acortar H, descartar B o parar por
señal de riesgo para encajar en el horario.

El reloj de seguridad puede abortar una corrida por límite técnico, dejando sus
recursos y estado registrados; no la convierte en réplica válida parcial.
Antes de lanzar una nueva unidad, verificar presupuesto restante. La reanudación,
si se implementa, solo sería en fronteras completas con estado/RNG íntegros.

## P1 — calibración metodológica acotada

Antes de ejecutar P1, fijar una **cota económica común d** en log pérdida de
30 días. Solicitar al investigador el nivel aceptable y registrar su justificación.
Por ejemplo, convertir un nivel simple l mediante -log(1-l) expresa ese nivel
en escala logarítmica, pero no convierte CVaR simple en CVaR logarítmico.
No elegir d para favorecer C5 o C10 después de ver resultados. Con d>=0,
mantener efectivo es referencia factible del simulador; no prueba que PPO
encuentre factibilidad.

Propuesta de candidatos controlados, sin búsqueda factorial:
- Referencia técnica: ancho 32, clip .2, tasas actor 1e-4 / crítico 1e-3 /
  dual .1, 2 épocas. Son candidatos para discusión, no defaults validados.
- Si hay inestabilidad de actualización: comparar una sola alternativa común
  con tasas divididas por tres; no cambiar simultáneamente d o la regla temporal.
- Si hay insuficiencia del crítico: proponer ancho 64 como comparación separada.
- Si cola imprecisa: ampliar N_Q/N_B de 400 a 800 para **todas** las condiciones,
  recalcular presupuesto incluyendo auxiliares y repetir la calibración temporal.

Usar tres bloques de semillas de desarrollo, fijados y publicados antes de ejecutar
(los valores concretos deben elegirse fuera de las semillas sintéticas H4).
Cada bloque ejecuta C0/C5/C10 con igual K y presupuesto; rotar orden entre bloques.
Un bloque puede ocupar varios días; preservar emparejamiento y registrar día,
hilos, máquina y tiempos. No asignar más K a C0 por ser más barato.

Diagnósticos: finitud, consistencia de logprobabilidades y ratios, fracción de
clipping PPO, error del crítico frente a MC, norma de gradiente sin clipping,
exposición/costos, eta, masa y empates, rho_Q, rho_B, F_B(eta_Q), diferencias
respecto de d, lambda y recursos. Bootstrap diagnóstico de precisión de cola
debe reconocer mu sobre histórico fijo; no presentarlo como incertidumbre
sobre todos los regímenes económicos.

No seleccionar checkpoints por B ni detener al primer cumplimiento. B pertenece
al aprendizaje vía multiplicador; sus resultados no son confirmatorios.
Los criterios cuantitativos de precisión/estabilidad y la regla de selección
común deberán aprobarse antes de P1, sin comparar ganadores por Sortino.

## Puerta de salida

Congelar arquitectura, tasas, clip, épocas, N_A/N_Q/N_B, K, d común, semillas y
presupuesto antes del contraste entre condiciones. Separadamente, antes de una
campaña confirmatoria, cerrar réplicas, remuestras, precisión e indefinidos.
Conservar Sortino anualizado, bootstrap pareado centrado y Holm del ADR.
Ningún piloto autoriza por sí mismo el conjunto final ni acredita CVaR poblacional.
