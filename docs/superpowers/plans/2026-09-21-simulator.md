# H2 — simulador causal: diseño y plan

Alcance autorizado: ADR-001, política B aceptada y solicitud local del usuario.
Sin entrenamiento, agentes ni conjunto final. Se trabaja en el repositorio abierto;
la eliminación preexistente de .python-version se conserva fuera del commit.

## Contrato

Precio de referencia p = apertura siguiente. Patrimonio antes de negociar
V = cash + btc*p. Precio ejecutado p*(1+s) al comprar y p*(1-s) al vender;
comisión f*abs(delta_btc)*precio_ejecutado, pagada en USDT. Valoración posterior
con p sin deslizamiento. La acción w es btc_post*p / patrimonio_post_costos.
No se usa el cierre siguiente para resolver la orden.

La compra resuelve delta=(w*cash-(1-w)*btc*p)/(p*(1+w*k_buy)),
k_buy=(1+s)*(1+f)-1. La venta resuelve cantidad=((1-w)*btc*p-w*cash)
/(p*(1-w*k_sell)), k_sell=1-(1-s)*(1-f). Las fórmulas de saldos usan expresiones
no negativas equivalentes para evitar cancelación en w=0/1, sin clipping.
Se verifica conservación de efectivo, BTC y patrimonio con tolerancia de redondeo
float64 proporcional a las magnitudes, sin ocultar saldos inválidos.

Observación float64: FEATURES en orden vigente y peso BTC al cierre, log(E/E0).
Al reset: 10000 USDT, cero BTC. Cada step: acción válida, ejecución en apertura
siguiente, valoración al cierre siguiente; recompensa log(E_nuevo)-log(E_previo).
Incluye el movimiento de cierre a apertura de la posición heredada y los costos.

Una ventana de entrenamiento utiliza exactamente el índice aceptado de 180
transiciones. Validación recorre todas las transiciones de 2023 desde una sola
cartera. Los cortes son truncated=True, terminated=False, sin venta forzada;
se informa si el corte es ventana, segmento o partición. El último estado es real,
no se genera otra transición. No se prescribe bootstrap; ADR-002 permanece abierto.

## Estructura

- env/accounting.py: rebalanceo puro y libro de costos, sin acceso a datos futuros.
- env/market.py: carga solo tras aceptación y auditoría H1; selección por índice,
  trayectorias inmutables y guardas temporales/partición.
- env/trading.py: interfaz Gymnasium reset/step, estado de cartera y observación.
- tests/test_simulator.py: precios sintéticos, oráculo Decimal por bisección sobre
  flujos de caja, casos manuales, gap, causalidad, extremos, costos, truncaciones,
  aislamiento, guardas y validación completa.
- scripts/verify_simulator.py: prueba funcional local sin aprendizaje, acciones
  deterministas prefijadas; auditoría de carga, todos los índices, episodios
  representativos por segmento y validación continua. Registra trazas y versiones.

## Ejecución

1. Escribir y ejecutar pruebas que fallen antes de implementar cada capa.
2. Implementar contabilidad y entorno; ejecutar casos independientes.
3. Conectar datos aceptados: ningún salto entre segmentos, ninguna transición fuera
   de la partición; la primera observación puede ser contexto anterior contiguo.
4. Ruff, pytest completo y auditoría funcional real; conservar comandos, logs,
   huellas de fuentes y escalador antes/después. No elegir políticas por resultados.
5. Revisión independiente de código; corregir defectos verificables y repetir
   únicamente las verificaciones afectadas.
6. Informe H2, HANDOFF y precisión de ADR-002 sin resolverlo, commit y ZIP con
   código, historia, evidencia y datos exclusivamente de desarrollo; verificar hashes.

La autorización vigente cubre estas decisiones de implementación. La comprobación
no busca rendimiento de una estrategia ni habilita campañas de aprendizaje.
