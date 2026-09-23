# Agentes H4 — verificación sintética exclusivamente

Actor y crítico separados CPU float64, observación H3 de 13 componentes.
Distribución logística-normal en (0,1), densidad con jacobiano y rechazo de
saturación numérica, sin clipping ni remuestreo de acciones.

- models.py: redes, snapshot, fingerprint y objetivo PPO.
- risk.py: MC completo, cuantil inferior, masa fraccionaria, F y dual.
- collector.py: identidades, fragmentos, ensamblaje, aborto de lote y NPZ v1.
- synthetic.py: rutas fabricadas y valores de pruebas, sin lectura de mercado.
- trainer.py: calendario Q/A/B y actualizaciones pequeñas autorizadas.

SyntheticExperiment requiere SyntheticMarket y SyntheticSettings. No se admite
AcceptedMarket, carga de trayectorias como replay, entrenamiento de mercado ni
configuración de pilotos. Un fallo invalida la corrida, sin reanudación/reemplazo.
Las trayectorias serializadas sirven para auditoría, no para reanudar optimizadores.

Véase docs/hitos/H4-agentes-recolector.md y docs/proposals/H4-pilotos-3h.md.
