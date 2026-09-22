# ADR-002: contrato finito común y transferencia operacional

**Estado vigente: ADOPTADO — v2.1, 22-09-2026.**
Autorización explícita del usuario en esta tarea: adoptar v2.1 y adaptar el simulador.
No autoriza agentes, entrenamientos ni evaluación confirmatoria.

Se adopta íntegramente el contenido metodológico de
[la propuesta v2.1](../proposals/ADR-002-propuesta-v2-1.md), revisada en
`e4e2e8fada77f9b1116f3b265368e82c1e82cedd`. Su encabezado «NO ADOPTADA»
se conserva como antecedente fechado; este registro lo sucede.
V1, v2, v2.1 y sus evidencias permanecen intactas.

## Decisiones adoptadas

- Distribución inicial uniforme con reemplazo sobre índices H1 de entrenamiento;
  10000 USDT, cero BTC, H=180 transiciones contiguas de 4h, gamma=1.
  R=sum(r)=log(E_H/E_0); PPO maximiza E[R]; riesgo usa L=-R, sin clipping.
  C5/C10 usan fracciones de cola .05/.10 y una misma cota d en log pérdida.
- Observación añade h=(180-j)/180 como componente 13, sin normalización.
  Terminalidad del objetivo en H: b=c=0, valor futuro cero, sin venta forzada.
  Antes de H, b=c=1 para transiciones observadas del mismo episodio.
- Corte administrativo interno: conservar estado/reloj/identidad y política congelada,
  esperar y ensamblar H antes de construir targets o muestras de riesgo.
  Censura temprana por segmento/partición invalida el episodio y exige abortar
  y diagnosticar el lote; nunca reemplazar selectivamente ni inventar continuidad.
  El motivo de fin y la terminalidad son campos distintos.
- Monte Carlo completo, lambda_GAE=1; actor y crítico separados. Calendario Q/A/B,
  cuantil/empates/masa fraccionaria, valores congelados, auditoría y actualización
  dual exactamente como §6 de v2.1. Sin normalización de ventajas ni entropía
  en la referencia. No se implementan esos componentes en este hito.
- Evaluación continua: una cartera, h=1, w/z reales, sin reinicios periódicos,
  refit ni aprendizaje. Es transferencia operacional con desplazamiento de soporte;
  no acredita CVaR a 30 días ni elimina riesgo en interrupciones excluidas.
- Sortino anualizado primario: sqrt(2190) × S_4h, retornos simples netos,
  MAR=0 y desviación bajista sobre todos los períodos. Anualización como
  convención, sin independencia temporal; denominador cero implica indefinido.
  Diferencias pareadas por bloques de semillas, bootstrap unilateral centrado
  de la media, Holm para C5–C0/C10–C0, significancia familiar .05.
  Un Sortino superior no demuestra cumplimiento CVaR.
- C0/C5/C10 comparten objetivo, datos, reglas temporales y presupuesto incluyendo
  Q/B auxiliares. Riesgo apagado debe reproducir C0 con multiplicador exactamente cero.

## Parámetros pendientes y puntos de congelación

Antes de implementar agentes: autorización separada, diseño del recolector con
identidad de política/episodio, pruebas de ensamblaje y calendario, equivalencia
C0 y serialización versionada. La adopción no levanta estos límites.

Antes de pilotos: fijar protocolo, semillas y presupuesto del piloto y motivación
económica de d; definir cómo juzgar su factibilidad. Requieren autorización
separada y no pueden tocar la prueba final.

Antes de comparar condiciones: congelar una sola d para C5/C10, K, N_A/N_Q/N_B,
arquitecturas separadas, tasas, clip, épocas, precisión de cola, semillas y
presupuesto común; documentar criterios sin escoger ganadores retrospectivamente.
Cambios a la estructura adoptada requieren otro ADR.

Antes de evaluación confirmatoria: congelar réplicas, remuestras, bloques/semillas,
precisión numérica/Monte Carlo, tratamiento inferencial de indefinidos y bloques
incompletos, y protocolo completo. Hace falta autorización explícita y comando
separado para el conjunto final. Si validación selecciona parámetros, sus resultados
son de desarrollo. La adopción estructural no cierra estos parámetros.

## Implementación y compatibilidad

H3 versiona configuración y observación; los productos H1 se reutilizan mediante
equivalencia explícita y auditada de configuración, sin cambiar sus bytes.
Contabilidad H2, costos, recompensa, mercado y normalizador se conservan.
Véase [informe H3](../hitos/H3-contrato-ADR002.md).

---

## Historial anterior a la adopción (conservado)

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

## Propuesta para revisión — 22-09-2026

Disponible [ADR-002-propuesta](../proposals/ADR-002-propuesta.md), sobre H2
`cc913b6`: compara alternativas, recomienda retorno finito común de 180 pasos
sin descuento, distingue cortes, deriva el mecanismo de riesgo y explicita la
transferencia a validación continua. Incluye fuentes primarias y cálculos
sintéticos independientes. **No adoptada**: esta referencia no cambia el contrato
H2 ni habilita agentes, entrenamientos o acceso al conjunto final. Revisar el
objetivo finito y su regla de evaluación conjuntamente antes de aprobar cambios.

## Segunda propuesta para revisión — 22-09-2026

La versión de revisión actual es [ADR-002 v2](../proposals/ADR-002-propuesta-v2.md),
con [respuesta académica resumida](../proposals/ADR-002-v2-resumen-academico.md).
Precisa soporte conjunto reloj/cartera, alcance de Sortino continuo, separación
Q/A/B para eta/actor/auditoría, actualización dual y presupuesto de auxiliares.
V1 permanece como antecedente. **PROPUESTA PARA REVISIÓN, NO ADOPTADA**: ADR-002
sigue abierto y H2 conserva observaciones, flags y configuración operativa.

## Armonización v2.1 con la tesis — 22-09-2026

Revisión actual: [propuesta v2.1](../proposals/ADR-002-propuesta-v2-1.md) y
[resumen académico](../proposals/ADR-002-v2-1-resumen-academico.md).
**PROPUESTA PARA REVISIÓN, NO ADOPTADA.** V2 se conserva como antecedente.
Se armonizan Sortino anualizado primario y el plan comunicado por el usuario:
diferencias pareadas por bloques de semillas, bootstrap unilateral centrado
sobre la media y Holm para C5–C0/C10–C0, significancia familiar .05.
Réplicas, remuestras, semillas, precisión y tratamiento de indefinidos siguen
pendientes antes de la evaluación confirmatoria. No cambian Q/A/B, regla temporal
ni H2. Un Sortino superior no demuestra cumplimiento CVaR. ADR-002 sigue abierto.
