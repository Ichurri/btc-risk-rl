# P2R — contrato de producto exclusivo de entrenamiento H1

**Estado:** infraestructura implementada; derivado histórico y su registro
**pendientes de revisión**. Este documento no autoriza exportar datos,
activar el permiso P2R ni ejecutar la campaña.

## Dependencia comprobada

El H1 aceptado en `data/processed/segmented-B-h1` mezcla las particiones
en `bars.csv`, `observations.csv`, `features.csv`, `episodes.csv` y
`transitions.csv`. El cargador anterior verificaba el SHA-256 de cada CSV
completo antes de extraer el prefijo de entrenamiento; por eso leyó bytes
de 2023 en el preflight anterior aunque no materializó observaciones de
validación. Es imposible volver a verificar el hash **completo** de esos
CSV sin leerlos. P2R ahora rechaza la entrada mientras no exista un
derivado exclusivo de entrenamiento registrado. P0/P1/P2 conservan su
cargador original y sus artefactos.

## Formato y verificaciones del futuro derivado

La ruta separada `data/processed/p2r-training-h1` deberá contener un
`manifest.json` con `schema_version=p2r_training_shard_v1`, estado
`accepted_for_p2r_training_only`, la huella del manifiesto H1 aceptado,
el mapa de huellas de sus productos, los límites `[2018-01-01,
2023-01-01)` y SHA-256 individuales de siete archivos: los cinco CSV
anteriores, `scaler.json` y `audit.json`. Los CSV contendrán solo filas
anteriores a 2023; las observaciones de calentamiento de 2017 necesarias
para las primeras rutas se conservan. `scaler.json` y `audit.json` serán
copias byte a byte de los productos H1 aceptados.

El cargador P2R verifica primero una huella **registrada en código** del
manifiesto derivado. Solo abre el manifiesto H1 (metadatos), el manifiesto
derivado y sus siete archivos. Contrasta padre, configuración, límites,
huellas individuales, coincidencia exacta de scaler/audit con H1, 7048
índices, horizonte 180, pertenencia a entrenamiento, momentos del
normalizador y observaciones normalizadas. Rechaza enlaces simbólicos y
enlaces duros a los cinco CSV compartidos antes de abrirlos. La identidad
de checkpoint incorpora tanto el ancla H1 como la huella del derivado.

La mera declaración de `parent_h1_file_sha256` en un manifiesto nuevo
**no demuestra** que sus CSV sean el prefijo exacto de H1. Antes de fijar
su huella en código, un procedimiento de exportación separado deberá:

1. Verificar los hashes originales contra el manifiesto H1 aceptado y
   producir un prefijo byte a byte por los límites temporales acordados.
   Ese procedimiento sí requerirá acceso a los CSV compartidos y **no se
   ejecutó ni está autorizado en este hito**.
2. Verificar cada fila y la igualdad del prefijo, la cobertura de los
   7048 índices, las exclusiones, segmentos y rutas completas, y que no
   haya filas de 2023 en el producto derivado. Guardar código, comandos,
   hashes, recuentos y un informe de exportación auditable.
3. Revisar el derivado y fijar `TRAIN_SHARD_MANIFEST_SHA256` en un commit
   independiente. Repetir el preflight con vigilancia de aperturas. La
   autorización posterior de campaña y su registro siguen siendo otro
   paso separado.

Este diseño preserva las huellas H1 y añade hashes del derivado, pero no
puede verificar nuevamente los CSV originales en cada ejecución sin
incumplir la barrera física. La confianza en la derivación dependerá del
informe de exportación revisado y del ancla fijada antes de una campaña.
No se generó el derivado histórico ahora.
