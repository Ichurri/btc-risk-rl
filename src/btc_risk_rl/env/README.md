# Simulador de desarrollo

- `accounting.py`: rebalanceo spot a exposición posterior a costos, float64.
- `market.py`: carga auditada de H1 e índices contiguos aceptados.
- `trading.py`: observaciones de cierre, ejecución a apertura siguiente,
  recompensa logarítmica neta y truncaciones sin liquidación.

Contrato y evidencia: `docs/hitos/H2-simulador.md`. Sin agentes ni entrenamientos.
ADR-002 permanece pendiente; no inferir descuento o bootstrap de los flags Gymnasium.
