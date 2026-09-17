from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from btc_risk_rl.config import Config, guard_development, load_config, utc_ms


def test_adopted_configuration():
    c = load_config(Path("configs/initial.toml"))
    assert c.environment.initial_cash == 10000
    assert c.environment.commission == 0.001
    assert not c.research.training_enabled
    assert c.data.final_test_locked


def test_no_unlock_by_configuration():
    data = load_config(Path("configs/initial.toml")).model_dump()
    data["data"]["final_test_locked"] = False
    with pytest.raises(ValidationError):
        Config.model_validate(data)


def test_no_training_by_configuration():
    data = load_config(Path("configs/initial.toml")).model_dump()
    data["research"]["training_enabled"] = True
    with pytest.raises(ValidationError):
        Config.model_validate(data)


def test_guard_exclusive_final_boundary():
    end = utc_ms(datetime(2024, 1, 1, tzinfo=timezone.utc))
    guard_development(end - 14400000, end)
    with pytest.raises(ValueError, match="reserved"):
        guard_development(end, end + 14400000)
