# Integración sintética WF: Q0 → Q/A/B+D

**Alcance:** ampliación de pruebas desde `3ee6ebc`, sin cambio del algoritmo operativo. Código de prueba en `b52f1a9`; los datos y artefactos históricos `...01`–`...03` no se abrieron para aprendizaje ni se modificaron. Los gates siguen cerrados.

## Recorrido comprobado

`tests/test_wf_permit_integration.py` usa una fuente controlada de tipo `TrainingMarket` cuya ruta de 180 transiciones procede de `SyntheticMarket`. En un directorio temporal crea un ledger y una solicitud Q0 con token, PID, hash e identidad. Para reducir el costo de la prueba, la configuración del fixture usa dos trayectorias por lote Q/A/B, red de cuatro unidades y una iteración; el trabajador conserva **D=64**, su tamaño operativo. El gate externo y la comprobación de parámetros congelados se sustituyen solo dentro del fixture, sin alterar los valores en disco.

La primera llamada a `wf_cost_replacement_03_worker.main` produce `checkpoint-0` en `after_q0`. El test **simula la transición del supervisor** a un lease de unidad 1 actualizando el ledger temporal y la solicitud, luego llama de nuevo al trabajador. No llama al método real de aceptación del supervisor. Esta segunda llamada recorre `complete_unit → load_checkpoint → SyntheticExperiment → Diagnostic.bind → run → save_checkpoint`, sin sustituir ninguna de esas funciones ni `_verify_completion`.

El checkpoint de unidad 1 termina en `after_dual_and_D`; su SHA-256 coincide con el manifiesto y pasa `_verify_completion`. El checkpoint Q0 conserva su hash. Los incrementos medidos del fixture son 6 trayectorias de aprendizaje (1.080 transiciones), 64 diagnósticas (11.520 transiciones), 2 pasos de actor y 2 de crítico. `next_iteration=1`. La marca `market_training_executed=true` resulta del perfil de tipo `TrainingMarket` fabricado y de ambos pasos; **no significa que se entrenó con mercado real**.

## Rechazos y límites

Con Q0 ya guardada, se rechazan por su causa específica: bytes alterados del checkpoint Q0, token falso, PID de supervisor distinto, semilla o condición cambiadas y ruta previa ajena. Ninguno produce `checkpoint-1` ni `unit-1.json`. La prueba previa sigue cubriendo el gate cerrado, permiso falso y raíz ajena desde Q0.

Las dos llamadas al trabajador ocurren en **el mismo proceso de prueba**. La prueba acredita lectura real del checkpoint y continuidad del algoritmo, pero no reingreso en un proceso nuevo, aceptación por el supervisor real, señales, `systemd`, recursos o presupuesto diario. Tampoco mide tiempos de los cortes históricos ni demuestra calidad del crítico. La aprobación externa se suplanta solo en memoria para poder probar la ruta con datos fabricados; el permiso operativo sigue cerrado.

## Ejecución y preservación

Prueba focal final: **14 passed en 6,52 s**. Suite completa final: **442 passed en 285,00 s**. `uv run --frozen ruff check .`: `All checks passed!`; `git diff --check`: sin salida. Las [órdenes y logs](../evidence/oos-wf-qabd-integration/COMMANDS.md) distinguen la primera suite de 441 pruebas de la repetición final tras añadir el caso de PID.

La [auditoría](../evidence/oos-wf-qabd-integration/verification.json) comparó archivo por archivo los originales con sus referencias congeladas: `...01` 15/15, `...02` 2/2, `...03` 10/10, todos idénticos. Verificó los tres gates en `False` y la huella histórica del registro `...03` (`6f877eaf18663f0427ef9f5ad9e412eeec6da761d7355bbc110563e784c6c4b4`). El SHA-256 de la auditoría es `a6c7bd49f245cec632b29c4a54b2317d4a25a32e5814438d0e0a1e4651b48704`.

**Decisión siguiente:** revisar estas pruebas y sus límites. No se preparó `...04`, se emitió permiso, se lanzó unidad histórica ni se accedió a validación o prueba final.
