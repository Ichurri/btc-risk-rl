# H4 — agentes PPO/CVaR-PPO y recolector

Base H3: 8f027c53696976602260eb498698ef51ffd5d711, verificada local y remotamente.
Rama: [codex/h4-agents-collector](https://github.com/Ichurri/btc-risk-rl/tree/codex/h4-agents-collector).
El usuario autorizó implementación y actualizaciones pequeñas sobre datos sintéticos.
No autorizó entrenamiento de mercado, pilotos, evaluación confirmatoria ni test final.

## Implementación

Actor y crítico son MLP separados, con una capa oculta tanh configurable, CPU
float64. Reciben las 13 componentes H3. La arquitectura y los valores del ejecutor
sintético son de prueba; no son hiperparámetros aprobados de la tesis.

El actor devuelve mu(x) y sigma(x)=softplus(s(x))+1e-6. Muestrea
z~Normal(mu,sigma), a=sigmoid(z), con soporte (0,1), dentro de [0,1].
Los extremos tienen masa cero: la política no produce exactamente efectivo total
o BTC total, aunque el entorno sigue admitiendo esas acciones. Esta limitación
de la familia debe considerarse al estudiar factibilidad; la referencia siempre
efectivo del ADR no es una política exactamente representada por esta familia.

La logdensidad usada en recolección y actualización es:
log pi(a|x)=log Normal(logit(a);mu,sigma)-log(a)-log(1-a).
El 1e-6 parametriza una escala positiva, no recorta acciones. Si sigmoid satura
en 0/1, o hay no finitud, se aborta y registra el lote; no clipping/resampling.
El clipping del ratio de PPO es el surrogate metodológico, no clipping de acciones.

Inicialización aislada del RNG global de torch; muestreo NumPy con streams
distintos por rol, iteración e inicios/acciones. El orden de minibatches dispone
de streams propios. Los roles pueden elegir la misma ruta con reemplazo; eso
no reutiliza la realización ni crea períodos de mercado independientes.

## Recolector y persistencia

Cada realización identifica corrida/iteración/rol/réplica; por separado registra
la ruta y su huella, y generación/hash de política. El actor se copia y congela
para recolectar; la huella se verifica al cerrar fragmentos y lotes.

Los fragmentos retienen estados, acciones, logprobabilidades, recompensas, tiempos,
terminalidad y motivo de fin. El ensamblador exige 180 transiciones, contigüidad,
identidades coincidentes, reloj H3, terminalidad solo en H y ausencia de truncación.
Una frontera de segmento/partición exactamente en H es válida; antes de H censura.
El motivo de corte se conserva separado de terminalidad del objetivo.
La suma MC no aplica bootstrap, gamma=1 y lambda_GAE=1.

Arrays respaldados por bytes inmutables impiden alterar muestras guardadas.
NPZ schema h4_trajectory_v1, sin pickle y sin sobrescritura, preserva identidad y
valida al cargar; cada recompensa debe concordar con la variación de log patrimonio.
La serialización es de auditoría: no implementa replay ni reanudación de corridas.

Cualquier error invalida todo el lote/corrida, con rol, iteración, réplica, paso,
política, causa y consumo acumulado. No se devuelve un lote parcial ni se reemplaza
la trayectoria fallida. Si el fallo sucede después de actualizar, los pesos
parciales de la corrida se descartan: no se promete rollback automático.

## Calendario implementado

1. Q0 de pi0 congelada, eta0 por menor cuantil empírico con CDF>=1-alpha.
2. A_k nuevo de pi_k; crítico anterior congelado antes de A. Calcular G completo,
   ventajas G-V_old y D=ventajas-lambda/alpha*(L-eta)+ con L=-G_0.
3. Actor: PPO por minibatches de trayectorias completas, suma de sus 180 términos
   y media por trayectorias. Datos, logprob_old, G, V_old, ventajas, D, eta, lambda,
   alpha y d permanecen fijos durante épocas/minibatches.
4. Congelar actor nuevo; crítico separado después con MSE media por transición
   contra G sin penalización. No comparte parámetros ni optimizador con actor.
5. Q_(k+1) nuevo de pi_(k+1); fijar eta nuevo, sin suavizado.
6. B_(k+1) independiente con esa política, eta fijo; registrar F_B, rho_B, rho_Q,
   masas/empates y diferencias respecto de d.
7. Actualizar lambda una vez por max(0,lambda+beta*(F_B-d)) para siguiente iteración.

No entropía, normalización de ventajas, valor clipped, bootstrap, gradiente clipped
ni parada por auditoría favorable. Adam explicita betas (.9,.999), eps=1e-8,
weight_decay=0 como elecciones de implementación/prueba, pendientes para pilotos.

El cálculo empírico distribuye por igual la masa restante entre empates exactos.
El rango del cuantil usa aritmética racional para evitar un ceil incorrecto por
redondeo binario de alpha*N. F evaluada con eta_Q no se identifica con el CVaR
empírico minimizado sobre B, ni con la restricción poblacional desconocida.

C0 y C5/C10 comparten implementación. Riesgo apagado copia las ventajas y fuerza
lambda=0; Q/B se siguen recolectando y contando. K es fijo. Recursos:
N_Q+K*(N_A+N_Q+N_B) trayectorias y 180 veces esa cantidad de transiciones.
No se iguala artificialmente tiempo de cómputo entre condiciones.

## Alcance operativo y límites

PyTorch 2.8.0+cpu se fija en uv.lock desde índice CPU explícito; sin CUDA ni drivers.
[Configuración de índice según uv](https://docs.astral.sh/uv/guides/integration/pytorch/).
No se cambiaron H3, configuración de datos, características, normalizador,
particiones o productos H1. El estado histórico de investigación en initial.toml
pertenece al perfil de datos H3; la autorización H4 está en AGENTS y el perfil
SyntheticSettings. training_enabled=false permanece para mercado.

SyntheticExperiment solo admite la fuente fabricada en código. No hay adaptador
de mercado ni comando para entrenarlo, piloto o evaluar el conjunto final.
La serie sintética no representa Binance ni usa el scaler de mercado.
No se prueba transferencia, rentabilidad, convergencia o cumplimiento de CVaR.

Pendientes técnicos antes de pilotos: adaptador de índices H1 bajo autorización,
checkpoint integral/reanudación determinista, instrumentación de memoria y
diagnósticos de estabilidad. No se guardan optimizadores en el archivo de trayectoria.
La equivalencia exacta verificada se limita a la plataforma CPU determinista usada.

## Pruebas y evidencias

[Comandos/logs](../evidence/agents-h4/COMMANDS.md) y
[resultados de ejecución sintética](../evidence/agents-h4/results.json).
Casos analíticos: retornos de suma conocida, cola discreta con empates y masa
fraccionaria, F a eta fijo distinto de rho, signo dual, densidad y gradiente por
diferencias finitas independientes y reducción del surrogate.
Casos del simulador: fragmentos vs episodio completo, reloj/cartera, tres motivos
de corte, corrupción de serialización y aborto sin reemplazo.
Actualizaciones pequeñas: orden Q/A/B, política generadora, parámetros/coefs
congelados, segunda iteración con lambda>0 y equivalencia C0 en redes y Adam.
Las pruebas históricas H1/H3 se ejecutan de nuevo solo con sus fixtures sintéticos.

### Resultados locales ejecutados

- **149 pruebas pasan en 58.40 s**, 32 nuevas H4. Ruff sin errores.
- Verificador adicional sobre commit a6c391a: cinco corridas, dos iteraciones
  cada una; 95 trayectorias, 17100 transiciones y 40 pasos actor + 40 crítico.
- Equivalencia exacta C0/riesgo apagado comprobada. C5/C10 activos usan lambda
  actualizado en la siguiente iteración; no se infiere rendimiento de esos valores.
- Tiempo observado del bloque sintético: 9.983122481 s, CPU/un hilo torch;
  no extrapolable a mercado. Versiones y huellas completas en results.json.
- Revisión independiente cerrada, sin hallazgos pendientes. Se añadieron
  conservación de motivo de corte y validación de recompensa al serializar.

Commits: 31b4c87 (alcance/dependencias) y a6c391a (implementación).
El commit documental de entrega conserva esta evidencia sin alterar código.

## Siguiente paso

Revisar [propuesta concreta de pilotos bajo 3h/día](../proposals/H4-pilotos-3h.md).
Primero cerrar los pendientes técnicos y autorizar el protocolo; luego medir
tiempos reales de desarrollo para dimensionar un K común. No extrapolar los
tiempos sintéticos. La cota común y demás parámetros requieren congelación previa.
La tesis no se modificó; no se generó ZIP.
