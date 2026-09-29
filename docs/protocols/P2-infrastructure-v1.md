# P2: contrato de infraestructura y separación de permisos

**DISEÑO ACEPTADO. SOLO IMPLEMENTACIÓN Y VERIFICACIÓN SINTÉTICA AUTORIZADAS.
MERCADO NO AUTORIZADO.** Base revisada: `7357aa1`; las propuestas originales y
P0/P1 se conservan intactos. La autorización del usuario acepta los valores de
[P2 v1](../proposals/P2-protocolo-v1.md), incluyendo sus secciones 3–8. Este registro
no cambia ADR-002 ni crea un permiso P2 en los registros P0/P1.

[Configuración registrada](P2-infrastructure-v1.json): nueve corridas, K=10,
semillas 610031/610047/610081, órdenes C0/C5/C10, C5/C10/C0, C10/C0/C5; cuatro épocas
provisionales del crítico, D=64 cada iteración. N_A=64, N_Q=N_B=400, tasas,
arquitectura, actor, d=-ln(.90), H180/gamma1, costos y Q/A/B permanecen iguales.
Ventanas {0,1,2}/{7,8,9} y umbrales conjuntos §7 aceptados para P2. No son criterios
confirmatorios, pruebas de hipótesis ni garantías poblacionales de CVaR.

D se genera después de dual con la copia de pi_k que generó A_k, no pi_(k+1).
Ambos críticos se evalúan sobre exactamente los mismos retornos restantes MC,
sin bootstrap. El crítico posterior está alineado con la política de ajuste;
el anterior incluye desfase de política. Los generadores D usan coordenadas
[semilla,7002,k,0/1]; Q/A/B conserva sus coordenadas. D no actualiza redes, Adam,
eta, lambda, gradientes ni aleatoriedad de aprendizaje. No existe selección
por desempeño ni parada por las advertencias.

Fronteras P2: `after_q0` y `after_dual_and_D`. El fallo de D invalida la unidad
Q/A/B+D completa. No existe checkpoint reanudable en `after_dual` para esta ruta.
No se regeneran D completados. Las copias de pi_k/phi_k viven hasta terminar D;
no se requieren en la siguiente frontera, pero sus hashes y los archivos D quedan
registrados. Se conservan fragmentos/estado parcial como evidencia no reanudable.

Presupuesto: 3 horas globales por día America/La_Paz, UTC en registros; hasta
3 días activos, 3 sesiones por corrida y 27 de campaña. Reserva1800s,
preflight900s/trabajo8100s; Q0 inicial1800s, unidad Q/A/B+D2700s con subtope D900s.
Admisión posterior 1.5×máximo medido de la misma condición/perfil. El ledger
acumula recursos y conserva fronteras/checkpoints; el bloqueo global descuenta
otras campañas. Las medidas sintéticas no habilitan estimaciones de mercado.

## Perfiles y futuro comando

`P2SyntheticSettings` permite pruebas pequeñas y K hasta10 exclusivamente con
`SyntheticMarket`. El ejercitador secuencial usa N_A=1,N_Q=N_B=2,D=2, ocultas4,
actor1época/crítico4, no la configuración económica de mercado. Los tests también
verifican D64 sintético. Los parámetros pequeños son fixtures, nunca una reducción
automática del diseño aprobado. No hay un `P2Permit` de mercado.

Comando previsto para futura campaña, **NO EJECUTADO como campaña**:

```bash
uv run --frozen python scripts/run_p2.py --profile market --protocol docs/protocols/P2-infrastructure-v1.json
```

Hoy devuelve exit2 antes de cargar configuración/datos o crear salidas, incluso
si el JSON dice autorizado. Los tests prueban ese rechazo con rutas inexistentes.
Una autorización posterior requerirá registrar el permiso y conectar el perfil de
mercado aprobado al supervisor; no bastará cambiar una bandera del JSON. Validación
y final no tendrán acceso por ese permiso. No se ejecutó ningún piloto P2 histórico.
