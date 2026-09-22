# ADR-002 v2 — respuesta a la revisión académica

**PROPUESTA PARA REVISIÓN, NO ADOPTADA.** Base técnica H2 `cc913b6`;
antecedente documental v1 `082db3e`. [Documento completo](ADR-002-propuesta-v2.md).

## Observación 1: reloj y cartera fuera del soporte de entrenamiento

Se reconoce una diferencia estructural: en entrenamiento h=1 implica peso BTC=0
y log patrimonio=0; en despliegue h=1 puede acompañar exposición y ganancias o
pérdidas acumuladas. Haber visto esas carteras con otro reloj no prueba que la
red generalice a esa combinación. Se añaden cinco estados contables sintéticos
y dos funciones que coinciden en el soporte de entrenamiento pero difieren fuera
de él. No son pruebas de una política entrenada.

Recomendación previa a resultados: conservar H=180 y gamma=1 para entrenamiento,
y conservar la evaluación continua con horizonte móvil, una cartera y sin resets
periódicos, **solo como transferencia operacional**. Reloj cíclico, reloj agotado,
carteras iniciales aleatorias y formulación continua tienen otros problemas o
cambian la pregunta; no se presentan como soluciones automáticas.

El contraste principal de Sortino compara los procedimientos completos bajo esa
regla de despliegue. Una mejora no prueba cumplimiento CVaR a 30 días ni atribuye
la diferencia exclusivamente al control de cola. El cambio de soporte puede
interactuar con el mecanismo de riesgo. Se propone explícitamente Sortino sobre
retornos simples netos de 4 h, MAR=0, denominador con todos los períodos, sin
anualización automática; DD=0 se informa indefinido. Esa convención y el protocolo
inferencial aún requieren revisión y congelación antes del contraste. Una
validación utilizada para selección no constituye prueba confirmatoria.

## Observación 2: eta, multiplicador y reutilización

Se elige separación de lotes, sin dejar opciones abiertas:

1. Q_0 bajo política inicial estima eta_0 mediante cuantil inferior empírico.
2. A_k bajo política congelada pi_k calcula retornos completos, ventajas y
   shortfalls con eta_k/lambda_k fijos; actualiza actor mediante épocas PPO.
3. Se congela el actor nuevo; se ajusta después el crítico separado usando A_k
   y targets fijados antes del actor.
4. Q_(k+1) nuevo bajo pi_(k+1) estima eta_(k+1), con empates y masa fraccionaria.
5. B_(k+1) nuevo bajo la misma política audita con eta_(k+1) fijo; se registran
   CVaR empírico y función variacional, distinguiéndolos de CVaR poblacional.
6. Se actualiza una vez lambda para la iteración siguiente con F_B(eta)−d.

El pseudocódigo completo y las ecuaciones están en §6 del documento. A se reutiliza
para épocas y crítico; Q aporta eta, sin replay de sus trayectorias al actor;
B aporta auditoría y señal dual, por lo que no es un conjunto confirmatorio
independiente del aprendizaje. La separación evita el ajuste de eta sobre el
mismo lote del actor, pero no elimina error de eta, aproximación PPO ni sesgo
histórico. No hay garantía poblacional a partir de una auditoría favorable.

La cota d es común a C5/C10 y no se elige retrospectivamente. Todas las condiciones,
incluido C0, contabilizan Q_0 y K(N_A+N_Q+N_B) trayectorias. C0 obtiene Q/B solo
para diagnóstico, con streams separados, sin modificar actor, parada ni RNG de A.
Con riesgo apagado D es exactamente la ventaja C0 y lambda permanece cero.

## Evidencia y estado

[Evidencia local v2](../evidence/adr002-proposal-v2/COMMANDS.md): reproducción de
los seis grupos v1 y seis grupos nuevos, separados en tres algebraicos y tres de
especificación. Ruff pasa; **100 pruebas H2 pasan en 21.72 s**, en ejecución nueva.
Código, observaciones, flags, configuración y pruebas H2 permanecen intactos.
No se implementaron agentes, no se entrenó y no se accedió a datos de mercado.
La reproducción del chat académico es un resultado comunicado por el usuario,
separado de los logs locales adjuntos. ADR-002 permanece abierto.

Siguiente paso: revisar esta v2, especialmente el alcance del contraste Sortino
y el calendario Q/A/B, antes de cambiar el contrato H2.
