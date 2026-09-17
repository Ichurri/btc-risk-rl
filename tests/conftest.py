from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from btc_risk_rl.config import STEP_MS, load_config


@pytest.fixture
def config():
    return load_config(Path("configs/initial.toml"))


def synthetic_rows(start_ms, count):
    rows = []
    for i in range(count):
        price = 100 + i * 0.01 + np.sin(i / 5)
        rows.append(
            [
                start_ms + i * STEP_MS,
                str(price),
                str(price + 2),
                str(price - 2),
                str(price + 0.25),
                str(10 + i % 7),
                start_ms + (i + 1) * STEP_MS - 1,
                "0",
                1,
                "0",
                "0",
                "0",
            ]
        )
    return rows


@pytest.fixture
def bars():
    start = int(pd.Timestamp("2022-01-01", tz="UTC").timestamp() * 1000)
    rows = synthetic_rows(start, 300)
    from btc_risk_rl.data.quality import validate_rows

    frame, quality = validate_rows(rows, start, start + 300 * STEP_MS, start + 301 * STEP_MS)
    assert quality["status"] == "passed"
    return frame
