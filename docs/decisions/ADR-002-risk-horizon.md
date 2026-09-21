# ADR-002: compatibilidad riesgo, PPO y horizonte

Estado: ABIERTO; bloquea implementación de PPO/CVaR-PPO y entrenamientos.

Actualización H2 (21-09-2026): el simulador devuelve `truncated=True` al acabar
una ventana o disponibilidad de datos, conserva la posición y devuelve el estado
real final. `terminated=False` expresa que no se modeló una terminación económica.
Se distingue corte de ventana, segmento o partición. Esto **no decide** si habrá
bootstrap, qué descuento usar ni cómo tratar una interrupción al estimar valor;
no se debe inferir esa autorización de los flags de Gymnasium. Ver
../hitos/H2-simulador.md. Los criterios de cierre siguientes siguen pendientes.

El simulador inicial representa inversión continua. Una ventana de 180 pasos
es una truncación de recolección y no un final económico. No liquida al terminar.
Su recompensa es r_t=log(E_{t+1}/E_t), común a C0/C5/C10.
Para una ventana completa, sum(r)=log(E_fin/E_inicio).

Esta identidad NO autoriza elegir gamma=0,99 por defecto ni aplicar CVaR a
ventajas o retornos bootstrapeados como si fueran retornos financieros observados.

## Decisión que debe resolverse antes del agente
Comparar y adoptar explícitamente una formulación coherente:
1. Objetivo finito no descontado: J=E[sum_0^{H-1} r], CVaR sobre la misma suma,
   gamma=1. Horizonte H terminal para el objetivo, no bootstrap de valor después
   de H. Requiere modelar el tiempo restante y justificar su relación con la
   evaluación continua. Cambia el contrato de horizonte actual: ADR y pruebas.
2. Objetivo continuo con PPO y restricción sobre ventanas finitas: gamma y
   bootstrap explícitos para PPO, CVaR sobre sumas observadas de H pasos sin
   bootstrap. No afirmar que ambos optimizan idéntico retorno; derivar el
   objetivo mixto, su estimador de gradiente y el muestreo de ventanas. Es una
   adaptación propia, no una réplica automática de CPPO publicado.

No se ha adoptado ninguna de esas alternativas para entrenamiento. El entorno
puede verificarse sin resolver el estimador del agente. La configuración carece
intencionalmente de gamma numérico, N, cota y presupuesto.

## Criterios de cierre obligatorio
- Escribir J, variable aleatoria de riesgo, horizonte, descuento y unidades de cota.
- Fijar tratamiento de truncaciones, terminales y cortes del recolector; ventanas
  parciales nunca cuentan como trayectorias completas de cola.
- Mostrar consistencia del gradiente de riesgo; pruebas con caso analítico pequeño.
- C0/C5/C10 comparten horizonte/descuento y presupuesto; mecanismo riesgo apagado
  equivale a C0 con multiplicador fijo cero.
- Diferenciar gamma de GAE-lambda y del multiplicador lagrangiano.
- Pilotos de desarrollo con semillas separadas; sin uso de prueba final.

Fuentes de referencia:
https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/
https://www.ijcai.org/proceedings/2022/0510.pdf
