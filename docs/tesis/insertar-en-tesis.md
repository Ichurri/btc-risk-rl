# Material para el apartado 4.4.1

Análisis descriptivo posterior al cierre de la prueba confirmatoria. La numeración propuesta sigue a la Figura 13 del documento consultado.

## Métricas por condición

| Métrica | Unidad | C0 | C5 | C10 | Comprar y mantener |
| --- | --- | --- | --- | --- | --- |
| Retorno acumulado neto | % | 31,464361 ± 9,81835 | 31,469091 ± 9,766257 | 31,466029 ± 9,783154 | 106,976091 |
| Sharpe anualizado | razón | 0,68853 ± 0,154496 | 0,688755 ± 0,153527 | 0,688672 ± 0,153837 | 0,994906 |
| Sortino anualizado | razón | 0,979688 ± 0,221869 | 0,980005 ± 0,220482 | 0,979888 ± 0,22093 | 1,421389 |
| Maximum Drawdown | % | 19,553383 ± 1,845157 | 19,543921 ± 1,840883 | 19,546217 ± 1,841565 | 34,36797 |
| Calmar | razón | 0,755083 ± 0,233577 | 0,755422 ± 0,232181 | 0,755296 ± 0,2327 | 1,274299 |
| CVaR periódico al 5 % | % | 1,234195 ± 0,115014 | 1,233823 ± 0,114763 | 1,233949 ± 0,114936 | 2,489091 |
| Turnover anualizado | % por año | 4721,204829 ± 2131,128925 | 4718,660293 ± 2117,785058 | 4719,119722 ± 2122,142347 | 49,931601 |

Las celdas de C0, C5 y C10 muestran media ± desviación estándar muestral sobre 36 semillas.
Comprar y mantener BTC corresponde a un único recorrido.

## Diferencias pareadas

| Métrica | Unidad de la diferencia | C5 − C0 · media [95 %] | C10 − C0 · media [95 %] |
| --- | --- | --- | --- |
| Retorno acumulado neto | puntos porcentuales | 0,004731 [-0,039109; 0,050223] | 0,001669 [-0,021772; 0,02612] |
| Sharpe anualizado | razón | 0,000225 [-0,000456; 0,000936] | 0,000142 [-0,000223; 0,000527] |
| Sortino anualizado | razón | 0,000317 [-0,000661; 0,001336] | 0,0002 [-0,000325; 0,000753] |
| Maximum Drawdown | puntos porcentuales | -0,009462 [-0,017532; -0,002773] | -0,007166 [-0,011818; -0,003311] |
| Calmar | razón | 0,000339 [-0,000682; 0,001403] | 0,000214 [-0,000324; 0,000772] |
| CVaR periódico al 5 % | puntos porcentuales | -0,000373 [-0,000655; -0,000115] | -0,000246 [-0,000398; -0,000099] |
| Turnover anualizado | puntos porcentuales por año | -2,544535 [-12,695194; 7,443631] | -2,085107 [-7,44784; 3,049109] |

Se calcularon intervalos descriptivos percentiles del 95 % con 20.000 remuestras de
los bloques de semillas y semilla fija 912016. Los intervalos describen dispersión
entre semillas en el mismo período. El contraste confirmatorio de Sortino se conserva
en su informe separado.

## Dos párrafos de resultados

Sobre las trazas de la prueba final de 2024–2025 se calcularon métricas descriptivas después de cerrar el contraste confirmatorio. Se incluyeron las 36 semillas de cada condición. El retorno acumulado neto medio fue 31,464361 % para C0, 31,469091 % para C5 y 31,466029 % para C10. Las caídas máximas medias fueron 19,553383 %, 19,543921 % y 19,546217 %, respectivamente.

El CVaR periódico al 5 % medio fue 1,234195 % para C0, 1,233823 % para C5 y 1,233949 % para C10. La referencia de comprar y mantener BTC registró un retorno acumulado neto de 106,976091 %, una caída máxima de 34,36797 % y un Sortino anualizado de 1,421389. La comparación con la referencia fue descriptiva.

## Títulos y fuentes

Figura 14: Patrimonio durante la prueba final

Fuente: Elaboración propia 2026, con base en las trazas de la prueba final

Figura 15: Caída del patrimonio desde su máximo previo

Fuente: Elaboración propia 2026, con base en las trazas de la prueba final

Figura 16: Distribución de Sortino por condición

Fuente: Elaboración propia 2026, con base en las trazas de la prueba final

Figura 17: Exposición a BTC por condición

Fuente: Elaboración propia 2026, con base en las trazas de la prueba final

Si estas figuras se insertan antes de la sección 4.5, actualizar el diagrama C4
de Figura 14 a Figura 18, su mención en el texto y el índice de figuras.

## Frases que conviene actualizar

- **1.5.1, Alcances.** «El reporte en formato HTML previsto inicialmente se limitó a un tablero local de avance de los pilotos». Añadir el informe HTML estático de la prueba final, producido después del cierre.
- **1.5.2, Límites.** «La salida destinada a lectura humana se limitó a informes versionados y a un tablero HTML local». Añadir el informe final estático y conservar la aclaración sobre la interacción por línea de comandos.
- **3.1, Enfoque de la investigación.** «Las métricas secundarias se definieron para describir el riesgo y la actividad operativa». Añadir que se calcularon sobre las trazas finales ya aceptadas.
- **3.6, Hipótesis y operacionalización.** «CVaR, Maximum Drawdown, Calmar, Sharpe, retorno acumulado y turnover se definieron como medidas descriptivas complementarias». Indicar que se reportaron como análisis posterior al cierre y mantener la distinción entre CVaR periódico y CVaR de trayectoria.
- **3.9.1, Cálculo y presentación de métricas.** «Para las métricas secundarias se previeron definiciones de signo, escala y anualización» y «Las curvas comparativas se previeron mediante una regla de selección o agregación». Sustituir por la regla aplicada, mediana punto a punto y banda P5–P95 sobre 36 semillas. Definir turnover como cambio absoluto del peso marcado a cierre.
- **4.4.3, Discusión, limitaciones y cumplimiento de objetivos.** «La evaluación reportó únicamente la métrica primaria» y «no se calcularon sobre las trazas finales». Sustituir por la distinción entre el contraste principal y el análisis descriptivo. Revisar también «con la limitación señalada sobre las métricas secundarias» en el párrafo sobre el cuarto objetivo.
- **4.4.4, Reporte y reproducción.** Añadir las tablas secundarias, los CSV que respaldan las figuras y el HTML a los materiales reproducibles.
- **Conclusiones, primer párrafo.** «La evaluación integral prevista quedó incompleta porque no se reportaron las métricas secundarias». Indicar que se completó la caracterización descriptiva de las trazas. Mantener el alcance de la evidencia y las limitaciones del diseño ya documentadas.
- **Recomendaciones, segunda.** «Calcular y reportar las métricas secundarias sobre las trazas conservadas de la prueba final». Retirar esa tarea realizada. Si se conserva una recomendación en ese lugar, orientar el trabajo futuro a contrastar la estabilidad de estas medidas en otros períodos con un protocolo fijado de antemano.
