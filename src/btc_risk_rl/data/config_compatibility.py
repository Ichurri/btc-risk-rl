"""Narrow, read-only schema bridge; every data/accounting field must still match."""

from copy import deepcopy

from btc_risk_rl.config import Config

# Reverse the approved changes to construct the ONLY permissible old config.
# No wildcard stripping of fields, no mutation of the persisted manifest.
ENV_ADDITIONS = ("contract_version", "observation_version", "gamma", "validation_clock")
CHANGES = (
    "schema_version",
    "environment.horizon_mode",
    *(f"environment.{key}" for key in ENV_ADDITIONS),
    "research.risk_contract_status",
    "research.ppo_discount_status",
)


def audit_config_compatibility(recorded: dict, config: Config) -> dict:
    current = config.model_dump(mode="json")
    if recorded == current:
        return {"mode": "exact", "changed_fields": []}
    legacy = deepcopy(current)
    legacy["schema_version"] = 1
    for key in ENV_ADDITIONS:
        del legacy["environment"][key]
    legacy["environment"]["horizon_mode"] = "continuing_window_truncation"
    legacy["research"]["risk_contract_status"] = "blocked_pending_ADR_002"
    legacy["research"]["ppo_discount_status"] = "must_resolve_before_agent_implementation"
    if recorded != legacy:
        raise ValueError("Configuration mismatch outside the approved H1/H3 schema bridge")
    return {"mode": "h1_schema1_to_adr002_v2_1", "changed_fields": list(CHANGES)}
