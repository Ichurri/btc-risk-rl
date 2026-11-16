# Resumen para Ingeniería del Proyecto — estudio de costos por cortes

Se autorizó una medición aislada del costo de entrenamiento en los cortes de
desarrollo 2021 y 2022, con dos corridas C10 y 22 unidades previstas. El
preflight vigilado verificó recursos, presupuesto y huellas del derivado H1
exclusivo de entrenamiento. La primera sesión `systemd --user` completó y
auditó `wf-2021/Q0`: 400 trayectorias, 72.000 transiciones, 26,373 s de
pared entre inicio y aceptación y 358.670.336 B de RSS máximo del trabajador.
No hubo pasos del actor ni del crítico, como corresponde a Q0. El checkpoint
`after_q0`, el reporte y las cadenas del ledger y journal pasaron la
auditoría; la sesión pausó intencionalmente para revisión.

La segunda sesión falló antes de iniciar Q/A/B+D porque la identidad del
roster persistida como lista JSON se comparó con una tupla Python. La causa
se reprodujo por lectura: todos los demás campos coinciden y ambas
identidades son iguales tras normalización JSON. El ledger permanece
`ready` con 1/22 unidades y sin `pending`, pero la campaña quedó detenida
operativamente y el permiso de código se cerró. No hubo unidad 1 parcial,
entrenamiento adicional ni acceso a validación 2023 o prueba final. El
registro de autorización y Q0 siguen intactos para auditoría.

La medición solo aporta el costo de Q0 del primer corte. No proporciona
tiempos de Q/A/B+D, del corte 2022 ni una estimación válida para aprobar el
presupuesto de la propuesta fuera de muestra v1.2. Un futuro estudio tendría
que corregir y probar sintéticamente la reanudación desde Q0, fijar una raíz
y autorización nuevas, y medir también el gasto de preflight y de fallos
anteriores a la apertura del ledger. No se reinició ni sustituyó esta corrida.
