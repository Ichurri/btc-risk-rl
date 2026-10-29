# Autorización específica WF `...04` — pendiente de lanzamiento

**Estado al 29/10/2026 America/La_Paz: autorización registrada, ninguna
unidad histórica iniciada.** Santiago autorizó el estudio exclusivo
`artifacts/oos-v12-wf-cost-only-04/` conforme al perfil `ce62fed`. El
commit `232e7dc` añadió el [registro](../protocols/OOS-v1-2-wf-cost-04-approval.json)
y activó únicamente el gate `...04`. La raíz sigue ausente. Los gates y las
raíces `...01`–`...03` permanecen cerrados y congelados.

| Huella fijada | SHA-256 |
|---|---|
| Registro `...04` | `f9230d841757a3cf99ce79c81e50ad2c9794bf4615781fae3e0a4f2c1c74275d` |
| Código del ejecutor | `e7f869525309946b6c87f33149501ef5f7bc306cf11ecb582b766d5f39440ed6` |
| Perfil `...04` | `b188f93b0248d230dc4b122ed0e650be1c545dd7464184b744c69ef231772fbb` |
| Protocolo WF | `f6d81fd9f10938aee29480c701a1a52c0b84eba1db0ea42a21d2d84c3004cbe4` |
| Diseño WF | `66109d4400e04440c9450d1f1c0c7cc4332b66b9079703e3a1e62596032b5ad0` |
| Derivado H1 exclusivo de entrenamiento | `62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9` |

El registro conserva dos C10, semillas 276696733 y 498614892, cortes
2021/2022, 22 unidades en el orden original y los presupuestos fijados.
Exige `stop_after_first_accepted_q0=true` y
`not_before_day_la_paz=2026-10-30`; el código verifica ambas condiciones
además de las huellas. El 29/10, `...03` carga conservadoramente 10.800 s
del presupuesto global, por lo que **no se lanzó** `...04`.

Tras adaptar las pruebas que antes exigían aprobación ausente, las pruebas
focales dieron **19 passed** y Ruff `All checks passed!`. La prueba del día
de inicio comprueba el rechazo del 29/10 y la validez de la aprobación desde
el 30/10; otras comprueban registro falsificado y gate cerrado antes de
crear artefactos. La suite completa y el preflight vigilado **todavía no se
han ejecutado para el lanzamiento**: están reservados para el siguiente día
local disponible, inmediatamente antes de cualquier unidad.

No abrir validación 2023, prueba final ni activar evaluación v1.2. La
eliminación local previa de `.python-version` queda fuera de los commits.
