# Registro de adopción metodológica P2R v2 — 05/10/2026

**ADOPTADO COMO PROTOCOLO DE DIAGNÓSTICO DE DESARROLLO.** La revisión
académica aceptó [P2R v2](../proposals/P2R-protocolo-v2.md), precisada en
`36ed24d` antes de este registro. Su [resumen](../proposals/P2R-v2-resumen-academico.md)
y [comparación con v1](../proposals/P2R-v2-cambios.md) forman parte del
contexto de revisión. V1, el anexo y las sondas sintéticas 01–05 permanecen
como antecedentes sin modificaciones retrospectivas.

La adopción fija la **pregunta y reglas metodológicas**: repetir íntegramente
nueve corridas nuevas, separadas de P2, con semillas 610031/610047/610081,
orden rotado C0/C5/C10, K=10, Q0 y Q/A/B+D, D64 por iteración y crítico de
cuatro épocas provisional. Se conservan ADR-002, d común `−ln(0.90)`, datos
H1 exclusivamente de entrenamiento 2018–2022, normalizador fijo, las
fronteras `after_q0` y `after_dual_and_D`, y el presupuesto global de
10800 s/día America/La_Paz durante hasta tres días activos. P2 sigue
`failed`: ninguna corrida, trayectoria o checkpoint suyos se incorpora a
P2R. Las reglas de integridad, fallo irreversible, no selección de
checkpoints y criterios técnicos del documento v2 son parte de esta
adopción; no son evaluación confirmatoria.

La puerta de escala de la regla conjunta se define **por separado** para
cada semilla y condición, sobre los agregados de sus respectivas ventanas:

    Z_D,temprana > 10⁻¹²
    Z_D,tardía   > 10⁻¹²
    Z_A,tardía   > 10⁻¹²

Las ventanas temprana y tardía son, respectivamente, k={0,1,2} y
k={7,8,9}. Se agregan sumas de `G²` y conteos dentro de cada lote/ventana
antes de obtener `Z`; no se promedian razones ni se sustituye el valor de
una ventana por otro. Si cualquiera de las tres puertas falla, la condición
conjunta de esa semilla/condición **no** se cumple, aunque `R` tenga valor
numérico por el estabilizador. La regla técnica requiere todas las puertas
y demás umbrales simultáneamente en al menos dos de tres semillas de **cada**
condición, con las nueve corridas completas e íntegras. Si se completan las
nueve pero no se satisface, se informa `review`; si falta alguna corrida o
falla integridad, `not_evaluable`.

**Límite de autorización:** este registro **no** autoriza implementar el
ejecutor histórico, activar un permiso P2R, ejecutar unidades o entrenar con
mercado. Tampoco autoriza reanudar P2, acceder a validación 2023, usar la
prueba final 2024–2025 ni modificar la tesis. Para implementación y después
para campaña harán falta decisiones y permisos explícitos **separados**, con
huellas, pruebas sintéticas pendientes y preflight propios. La adopción no
convierte las sondas de logout, heartbeat o señal en garantía ante apagado
físico ni en evidencia de generalización, rentabilidad o cumplimiento
poblacional de CVaR.
