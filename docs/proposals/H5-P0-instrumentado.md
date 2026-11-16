# P0 después de H5 — PROPUESTA, NO AUTORIZADO NI EJECUTADO

Revisión 2026-09-23. Complementa y conserva como antecedente
[H4-pilotos-3h](H4-pilotos-3h.md). H5 entrega infraestructura; no aprueba
los candidatos de H4 ni los valores de SyntheticSettings para mercado.
ADR-002 v2.1, calendario Q/A/B, acción y contrato H3 permanecen adoptados.

## Entrada y autorización requerida

Antes de habilitar `scripts/run_pilot.py`, registrar un protocolo revisado con
identificador y hash, autorización explícita del investigador, configuración
íntegra y huellas H1/código/runtime. Hoy el comando devuelve `blocked` (código 2)
antes de leer el archivo de protocolo, datos o checkpoints. Un campo
`authorized=true` no levanta la guarda. Habilitarlo requiere un cambio posterior
revisado; H5 no contiene un ejecutor de entrenamiento de mercado operativo.

Condiciones técnicas entregadas: 7048 inicios H1 de entrenamiento, mu uniforme
con reemplazo; normalizador verificado sin refit; 13 componentes H3; checkpoint
completo en `after_q0` y `after_dual`; journal con revisión y bloqueo; reanudación
sintética exacta y diagnósticos por fase. Antes de mercado debe revisarse la
integración del protocolo autorizado con el mismo calendario, sin duplicarlo.
No habilitar validación ni conjunto final en ese ejecutor.

## Decisiones que debe cerrar el investigador

1. **Cota económica común d para C5 y C10**, en pérdida logarítmica a 180
   transiciones. Registrar interpretación y justificación antes de observar
   resultados. Convertir un nivel simple l con `-log(1-l)` solo cambia escala;
   no identifica el CVaR simple con el logarítmico. No derivar d de B favorable.
2. Arquitectura, tasas actor/crítico/dual, clip, épocas, minibatch, N_A/N_Q/N_B,
   K y semillas de desarrollo. Los números de H4 son candidatos para discusión;
   ninguna tasa o tamaño sintético pasa automáticamente al protocolo.
3. Umbrales y precisión: error MC tolerable, ratios/extremos/clipping,
   gradientes, saturación logística, precisión de cola, margen de tiempo/memoria
   y tratamiento de fallos. Fijar cuáles solo informan y cuáles invalidan
   técnicamente; no parar ni seleccionar por buen F_B, rho_B o Sortino.
4. Reglas de comparación de recursos, número de mediciones, orden entre
   condiciones y unidades a completar por día. Mantener emparejamiento de
   semillas y K común, incluyendo todos los auxiliares Q/B de C0.

Antes de evaluación confirmatoria quedan además réplicas, remuestras bootstrap,
semillas confirmatorias, precisión y métricas indefinidas. Se conserva Sortino
anualizado, diferencias pareadas por semillas, bootstrap unilateral centrado y
Holm, sin afirmar que Sortino superior demuestra cumplimiento CVaR.

## Límite de tres horas diarias

Se mantiene la propuesta H4: 15 minutos de preflight, hasta 135 de ejecución,
30 de auditoría/guardado/margen. Es un límite propuesto, no un tiempo medido.
Para cada condición se contabiliza
`N_Q + K*(N_A + N_Q + N_B)` trayectorias y 180 veces esa cantidad en transiciones,
más los conteos separados de pasos Adam actor/crítico. No reutilizar Q como B.

Primera calibración futura: protocolo debe aprobar una unidad inicial acotada
para obtener estimaciones de mercado; aún **no existe una estimación validada**
de una iteración. La prueba H5 solo midió carga y tres episodios con política
congelada, sin actor/crítico/dual. Sus tiempos y los sintéticos no dimensionan
el entrenamiento. No inventar una duración inicial ni adoptar 1.25 por defecto:
el factor conservador propuesto en H4 también debe ratificarse en el protocolo.

Después de medir las unidades completas autorizadas, usar estimaciones
conservadoras identificadas por perfil, configuración, máquina/hilos y versión.
Antes de Q0 o de cada iteración A→actor→crítico→Q→B→dual, comprobar que quedan
estimación más reserva. Si no caben, pausa planificada en la frontera anterior;
no cortar B, reducir horizonte ni sustituir trayectorias. El control H5 es
preventivo con reloj monotónico; no es un límite duro que interrumpa cómputo.
Un sobrepaso de reserva detectado al cerrar la unidad invalida la corrida.

La reanudación mantiene consumo temporal acumulado (y añade guardado), nunca
restablece silenciosamente las tres horas. Repartir un experimento entre días
requerirá un calendario diario explícito en el protocolo; H5 no ofrece un
interruptor para reiniciar presupuestos acumulados. Al planificar, incluir
carga/verificación y margen externo al tiempo del algoritmo, así como auditoría
final; RSS es máximo del proceso, no una atribución aislada por fase.

## Evidencias y parada

Guardar configuración autorizada, hashes, versiones, hilos, CPU, tiempos de
Q/A/B, eta, actor, crítico y auditoría/dual; memoria, trayectorias, transiciones,
actualizaciones, identidades de política/ruta/realización, consistencia logprob,
ratios y clipping, error MC, norma de gradiente sin clipping, exposición/costos,
eta/empates/masa/rho_Q/rho_B/F_B y lambda. Conservar fallos y recursos consumidos.

Finitud, continuidad, política mezclada, datos/normalizador incompatibles,
checkpoint incompleto, divergencia de logprob o reserva agotada invalidan la
corrida: sin reemplazo selectivo ni recuperación desde un estado viejo para
ocultar el fallo. Una interrupción en unidad tampoco se declara pausa válida.
Un checkpoint se guarda en carpeta nueva, con manifiesto y journal; no se elige
por rendimiento. B es parte del aprendizaje, no evaluación confirmatoria.

Salida de P0: informe de viabilidad, precisión y límites, sin seleccionar una
condición ganadora. Solicitar aprobación de P1 o cambios comunes de diseño si
no cabe una unidad. Ningún resultado de P0 abre el conjunto final.
