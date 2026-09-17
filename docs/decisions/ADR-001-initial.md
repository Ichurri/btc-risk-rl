# ADR-001: especificación inicial adoptada

Estado: adoptada como configuración de trabajo; no protocolo confirmatorio.

## Invariantes metodológicos
BTC/USDT spot 4h UTC; C0/C5/C10; mismo entorno y recompensa; sin operación real,
cortos ni apalancamiento; prueba final sin selección; no entrenar en esta entrega.

## Valores adoptados
Desarrollo 2018–2023, entrenamiento 2018–2022, validación 2023, prueba reservada
2024–2025; calentamiento diciembre 2017. Fechas [inicio, fin).
10.000 USDT iniciales; comisión 0,001 y deslizamiento adverso 0,0005.
Acción exposición continua [0,1] posterior a costos; fracciones de BTC ideales,
sin mínimos de orden, llenado completo e interés cero en USDT.
Observación cierre t; ejecución apertura t+1; valoración cierre t+1.
Retorno logarítmico neto; contabilidad float64; final a mercado sin liquidar.
Diez características de mercado: retornos log de 1/6/42 barras, log(C/O),
log(H/L), log(C/SMA6), log(C/SMA42), std poblacional de retornos 6/42,
log1p(volumen BTC). Dos de cartera: peso BTC y log(E/E_inicial).
Z-score de mercado ajustado exclusivamente en entrenamiento; sin clipping.

## Provisionales hasta pilotos
Características y ventanas; horizonte 180; sensibilidad de costos; arquitectura;
descuento; cota y multiplicador; trayectorias por actualización; semillas,
presupuesto, CPCV y remuestreo. No cambiar fechas por desempeño favorable.
Fuente secundaria y ventanas de comprobación requieren verificación de acceso.

## Contrato de datos
No rellenar huecos. Duplicados iguales deduplicados con registro; conflictos fallan.
OHLCV finitos, precios positivos, volumen no negativo, velas cerradas.
Una anomalía no resuelta impide declarar el dataset apto y avanzar al simulador.
No confundir validación de código sintético con aceptación del mercado histórico.

## Hitos y capítulos
Los hitos técnicos de infraestructura/datos/simulador contribuyen a OE2.
La especificación de riesgo OE1 se documenta antes; sus pruebas de equivalencia
se completarán una vez exista PPO. Esto no elimina ni renumera los hitos académicos.

## Hardware
Información declarada por el usuario, no medida aquí. VRAM 6 GiB estimada.
Tres horas diarias. CPU suficiente para intentar datos/pruebas; rendimiento de
entrenamiento aún no medido. No se promete tiempo de entrenamiento.
