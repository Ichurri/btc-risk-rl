# Resumen académico — barrera de datos y fallo durante cálculo P2R

Se corrigió la dependencia de preflight que, al verificar SHA-256 de
productos H1 completos, leía bytes de 2023 aunque usara únicamente
observaciones de entrenamiento. El ejecutor P2R ahora exige un derivado
exclusivo de 2018–2022, con huellas propias y ancla al manifiesto H1.
Las pruebas con datos fabricados muestran los archivos abiertos y el
rechazo de enlaces hacia CSV compartidos. El derivado histórico aún no
existe: su exportación, auditoría de igualdad con H1 y registro requieren
revisión separada. Por ello no hay preflight histórico positivo ni permiso
de campaña activo.

Una sonda sintética interrumpió Q/A/B+D después de `backward()`, durante
un cálculo repetido de norma del gradiente dentro de la actualización del
actor. El ledger terminó `failed`, solo Q0 quedó aceptada, no se publicó
checkpoint de la unidad interrumpida y las huellas del checkpoint Q0 no
cambiaron. La primera raíz mostró un error del envoltorio de prueba en
su código de salida; la repetición con raíz nueva corrigió solo ese
envoltorio y devolvió 1. Se conservan ambas evidencias.

Esto verifica una propiedad de integridad e interrupción de la
infraestructura sintética. No demuestra comportamiento de Adam durante
una actualización real, continuidad de `systemd --user` en esta sonda,
apagado físico, aprendizaje histórico, evolución del crítico,
generalización temporal ni cumplimiento poblacional de CVaR. P2R sigue
bloqueado y la tesis no se modificó.
