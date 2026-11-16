# P3 v1 → v1.1: diferencias para revisión

**Solo propuesta documental; P3 no está autorizado para implementación ni ejecución.**
La [v1](P3-protocolo-v1.md) permanece intacta; la [v1.1](P3-protocolo-v1-1.md)
es el texto completo a revisar. No se modificaron P2R ni sus reportes.

| Punto | v1 | v1.1 |
| --- | --- | --- |
| Benchmark cero | `MSE/(Z+10⁻¹²)≤0,95`; se decía que excluía `V=0`. | `MSE≤0,95Z`, con `Z>10⁻¹²`; equivalente a `MSE/Z≤0,95` solo cuando `Z>0`. |
| Razón estabilizada | Se usaba para reportar y decidir. | `Rε` queda como descriptiva y etiquetada; ninguna puerta depende de ella. |
| Contrastes pareados | `R_β1−R_β0` carecía de lote, ventana y denominador explícitos. | `ΔD`, `ΔD₃` y `ΔA` restan razones exactas con los targets y el `Z` propio de cada brazo de la misma semilla/condición. |
| Último tercio | Se exigía `Z` de D tardía total, que podía ocultar `Z=0` en el tercio 3. | Se exige además `Z(D,post,tardía,tercio 3,b)>10⁻¹²` en cada brazo. |
| Otras razones y sesgo | Denominadores y ceros implícitos. | `R₀=M/Z`, `B₀=media(V−G)/√Z`, brecha D−A con razones exactas; `Z=0` indefinido, `0<Z≤ε` definido pero no elegible. `n=0` o no finitos son fallo de integridad. |
| Estado con señal débil | Ambiguo. | Puerta informativa fallida con 18 corridas íntegras da `review`; no se rellena un contraste. Fallo de integridad da `not_evaluable` y parada. |

La intervención β=1, tres bloques de semilla, 18 corridas, presupuesto,
prohibición de validación/final, carácter exploratorio posterior a P2R y
requisitos prospectivos del marcador/supervisor **no cambian**. Los
umbrales no son confirmatorios y todavía requieren revisión antes de
autorizar una implementación futura.
