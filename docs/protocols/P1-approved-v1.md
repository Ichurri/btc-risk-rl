# P1 aprobado — comparación de épocas del crítico

Autorización del usuario tras diagnóstico 42152c3. Configuración congelada en
P1-approved-v1.json; solo P1, no parámetros confirmatorios. La propuesta original
permanece en P0-diagnostico.md. d=-ln(.90), sin cambiar su interpretación.

18 corridas nuevas, K=2. Semilla 510031: C0,C5,C10 y brazos 2,4 dentro de cada
condición; 510047: C5,C10,C0 y brazos 4,2; 510081: C10,C0,C5 y brazos 2,4.
N_A=64/N_Q=N_B=400; actor 2 épocas; todos los demás parámetros P0 intactos.
Cada corrida: 2128 trayectorias, 383040 transiciones, 16 pasos actor; crítico
16 (brazo 2) o 32 (brazo 4). Total previsto: 38304 trayectorias, 6894720
transiciones, 288 pasos actor y 432 crítico. Auxiliares C0 incluidos.

Criterio primario: tras primera actualización, MSE post-A del brazo4 <=0.8*MSE
post-A del brazo2 en al menos dos de tres semillas, con finitud/integridad y
mismo A inicial y actor posterior idéntico. Las condiciones son controles
repetidos, no nueve réplicas. Segunda iteración secundaria, no selección.

Registrar A fijo antes/después de actor y crítico: MSE, media(G²)+1e-12,
estadísticas de V/G, hashes de lote/actor, shortfalls, lambda y coeficientes.
Minibatches rotulados como prepaso aunque se escriban después. Los diagnósticos
no deben modificar gradientes, RNG, parámetros ni criterios de parada.

Presupuesto GLOBAL 10800 s/día America/La_Paz, UTC en logs. Descontar todo consumo
registrado de otras campañas del día, con bloqueo global. Reserva 1800 s,
preflight <=900 s, trabajo <=8100 s, Q0 <=1800 s, iteración <=2700 s, RSS <=10GiB.
Estimaciones nuevas por condición/brazo: primera unidad usa tope; siguientes
1.5×máximo medido de trabajo. No usar tiempos P0 para afirmar duración de P1.
Conservar máximo tres días/sesiones por corrida y **27 sesiones de campaña** de
P0: no ampliar automáticamente para 18 corridas. Si no alcanza, estado incompleto.
Guardar fronteras Q0/dual, no reintentos selectivos ni cambio de parámetros.
Rutas artifacts/p1-approved-v1; evidencia P0/diagnóstico inmutable.

Solo entrenamiento aceptado 2018–2022. Pruebas sintéticas antes de ejecutar.
Fallo de integridad/no-finitos detiene campaña y exige diagnóstico. Advertencias
P0 conservadas, no detener por resultados favorables o desfavorables. Resultado
primario positivo solo acredita ajuste in-sample: no generalización, rentabilidad
ni CVaR, no congela automáticamente parámetros definitivos. Tesis intacta.
