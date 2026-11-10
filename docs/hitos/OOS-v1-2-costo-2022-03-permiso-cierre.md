# Cierre prospectivo del permiso WF 2022-03

El 10/11/2026, tras `d3cc54b`, el estudio independiente `2022-03` ya estaba
`completed` con 11/11 unidades. La construcción del nuevo ejecutor OOS v1.2
cambia código incluido en la huella de aprobación de WF 2022-03. Se puso
`MARKET_EXECUTION_ENABLED=False` en sus dos puertas de entrada. La huella
del JSON histórico `c72292883224c50f86f0ae6a27b2ee6e4aaeed3ee548751cd81f3ac7f7ce73d4`
se conserva para auditoría; no se modifica ni repinea para lanzar otra unidad.

Prueba focal ejecutada: `uv run --frozen pytest -q
tests/test_oos_wf_2022_03_executor.py::test_2022_profile_has_independent_pinned_approval
tests/test_oos_v12_training.py` → 20 passed. `uv run --frozen ruff check .` →
sin hallazgos. El ledger original mantiene SHA-256
`707a643073d21588cd7dab631bb3b7331946adf97714a576b5c8f0177dff7b1e`;
el último `state.pt`, SHA-256
`5740732f226667d79ede579f4be96afc71705882cb68e53c1e6eb75c5fc2ea2e`.
La nueva campaña no reutiliza este permiso, raíz ni checkpoints.
