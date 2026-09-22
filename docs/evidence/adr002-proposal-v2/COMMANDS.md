# Evidencia local — propuesta ADR-002 v2

Fecha UTC: 22-09-2026. HEAD inicial: `082db3e3eff143999c1ab6e03db8c59d1d090a4b`.
Base del simulador: `cc913b629694641543e2b54375dbda5d55130544`.
Único cambio local previo: ` D .python-version`; se conserva fuera del commit.

## Lectura y revisión

Se leyeron AGENTS, README, HANDOFF, configuración, ADR-002, propuesta v1,
checks.py/results.json/COMMANDS.md de v1 y contrato env/trading.py. Fuentes
primarias y limitaciones de consulta están en §11 de v2. El DOI de Sortino/Price
respondió 403: no se afirmó haber leído su texto. La reproducción académica
coincidente fue comunicada por el usuario; no se presenta como ejecución propia.

## Comandos ejecutados

Desde la raíz del repositorio:

```bash
git status --short
git log -2 --oneline
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/adr002-proposal-v2/checks.py > docs/evidence/adr002-proposal-v2/results.json
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check . > docs/evidence/adr002-proposal-v2/ruff.log
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest > docs/evidence/adr002-proposal-v2/pytest.log
git diff --check
```

El comprobador ejecuta checks.py v1 como subproceso, guarda v1-reproduction.json
y compara sus resultados numéricos con results.json original (sin sobrescribirlo).
V1: seis grupos coincidentes. V2 añade **seis grupos**, tres algebraicos y tres
de especificación. Se repitieron checks y Ruff tras ampliar los ejemplos de
cortes para los tres roles y hacer explícita la muestra Q del ejemplo dual.
No cambió código H2 ni se justificó repetir su suite por esos cambios documentales.

## Alcance de las comprobaciones

- Algebra: cuantil/empates/masa fraccionaria; enumeración exacta poblacional frente
  a CVaR empírico/F con eta fijo; fórmula operacional de Sortino.
- Especificación: estados conjuntos y contraejemplo de funciones; coeficientes
  congelados/dual/riesgo apagado; roles, orden, cortes A/Q/B y recursos. Son
  ejemplos de reglas propuestas, no ejecución de recolector, agente o política.
- H2: suite existente de fixtures sintéticos, sin modificaciones. **100 passed
  in 21.72s**, salida 0. No prueba transferencia ni cumplimiento de riesgo.
- Ruff: `All checks passed!`, salida 0.
- Cálculos sintéticos: salida 0; JSON registra Python, plataforma, hora, HEAD,
  hashes y grupos. Comparación byte a byte con H2 de src/configs/tests/scripts,
  pyproject y lock, heredada del verificador v1. No carga datos de mercado.

Las pruebas de cortes v1 se preservan como antecedente: su opción parcial de
bootstrap no es la referencia de v2, que espera completar H sin target parcial.
Los ejemplos v2 lo distinguen. No hubo agentes, entrenamientos, instalaciones,
consulta de validación ni acceso al conjunto final. Propuesta no adoptada.

## Entrega

El paquete académico incluye el snapshot Git del commit documental, Git bundle
para reconstruir el historial, LEEME-ACADEMICO.md y DELIVERY.json con hashes.
No incluye datos de mercado ni artifacts anteriores. Comandos de empaquetado,
huellas y verificación de integridad quedan en el descriptor y recibo junto al ZIP.
Los logs históricos que incluye el snapshot conservan su atribución original;
los resultados nuevos de esta tarea están exclusivamente en esta carpeta v2.

Empaquetado reproducible después del commit documental:

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/adr002-proposal-v2/package_delivery.py
```

El script ejecuta `git archive --format=zip HEAD`, crea y verifica un bundle de
HEAD, comprueba CRC y todos los hashes internos del ZIP y escribe un recibo JSON
externo con tamaño, commit y SHA-256. Rechaza destinos existentes y rutas de datos
de mercado; no exporta cambios locales sin commit. Ruff se repitió al añadir
este script documental de empaquetado, sin cambios en H2.

El control previo al commit detectó una línea vacía adicional al final de
results.json. Se corrigió la salida del comprobador y se repitieron los cálculos
y Ruff; fue un ajuste de formato, sin cambios en H2 ni en las reglas propuestas.
