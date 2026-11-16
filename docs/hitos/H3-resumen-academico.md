# Resumen académico — H3, adopción ADR-002 v2.1

**Estado: ADR-002 v2.1 ADOPTADO; adaptación del simulador verificada.**
Base e4e2e8f; adopción 10d92fa; implementación ebb3914.
[Informe completo](H3-contrato-ADR002.md) y
[evidencia](../evidence/simulator-h3/COMMANDS.md).

Se adopta el objetivo común de 180 transiciones contiguas de 4h, gamma=1,
retorno logarítmico neto R=log(E_H/E_0), pérdida L=-R y una cota común pendiente
para C5/C10. Se preserva el calendario Q/A/B de v2.1 y sus reglas de cuantil,
congelación, auditoría, actualización dual y contabilidad de recursos.
No se implementó el agente.

El simulador H3 añade el reloj (180-j)/180 como componente 13. Al completar H,
el objetivo termina y sus máscaras de bootstrap/traza valen cero, sin liquidación
forzada. La procedencia del corte sigue separada de esta terminalidad.
Los checkpoints de recolección conservan estado, esperando completar H; los
episodios cortos se rechazan. El futuro recolector debe preservar identidad de
realización y política congelada y abortar lotes censurados sin reemplazo selectivo.

En continuo se mantiene una cartera, h=1 y exposiciones/patrimonio reales,
sin reinicios periódicos ni refit. Esto conserva la limitación de transferencia
operacional y de soporte conjunto: las pruebas no demuestran transferencia de
una política. Se mantiene Sortino anualizado como métrica primaria, con MAR=0,
retornos simples netos y desviación bajista sobre todos los períodos.
La anualización sqrt(2190) es convencional, no supone independencia temporal.
La inferencia mantiene diferencias pareadas por bloques de semillas, bootstrap
unilateral centrado sobre su media y Holm a .05 familiar. DD=0 implica ratio
indefinido. Sortino superior no demuestra cumplimiento CVaR a 30 días.

La adaptación conserva contabilidad, costos, recompensa y mercado H2.
Un puente estricto de configuración reutiliza los productos H1 originales,
sin refit ni modificación de particiones, máscaras o índices.

Verificaciones locales nuevas: Ruff pasa; 117 pruebas sintéticas aprobadas.
La auditoría sobre desarrollo verificó 7048 índices y ejecutó 31 recorridos,
7590 transiciones con acciones prefijadas. No es evaluación de una estrategia.
Todos los hashes de datos/scaler se conservaron. Las filas contables nuevas
coinciden exactamente con la evidencia histórica H2 (excepto flags).
Además, una regresión sintética ejecutó ambas versiones y obtuvo igualdad
de observaciones previas al reloj, recompensas y cuentas.

Pendientes: autorización para agentes; pruebas del recolector y Q/A/B,
equivalencia C0 bit a bit, diseño de pilotos, d común, tamaños, tasas, épocas,
arquitectura y presupuesto. Antes de confirmar: réplicas, remuestras,
semillas/bloques, precisión y gestión inferencial de indefinidos.
No entrenamientos, acceso al conjunto final ni cambios en la tesis.
