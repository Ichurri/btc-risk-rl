import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
url = (root / "reports/avance-tesis/index.html").as_uri()
with sync_playwright() as p:
    b = p.chromium.launch(
        executable_path=os.environ.get(
            "DASHBOARD_CHROMIUM",
            str(Path.home() / ".cache/ms-playwright/chromium-1248/chrome-linux64/chrome"),
        ),
        headless=True,
        args=["--no-sandbox"],
    )
    page = b.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url)
    page.screenshot(path=str(root / "reports/avance-tesis/inicio.png"))
    page.screenshot(path=str(root / "reports/avance-tesis/principal.png"), full_page=True)
    assert page.locator("#content").inner_text().find("Dos críticos") >= 0
    for seed in ["710031", "710047", "710081"]:
        page.select_option("#seed", seed)
        for condition in ["C0", "C5", "C10"]:
            page.select_option("#condition", condition)
            for arm in ["0", "1"]:
                page.select_option("#dataset", arm)
                data = page.evaluate("DATA.cross")
                pair = next(
                    x for x in data if str(x["seed"]) == seed and x["condition"] == condition
                )
                expected = pair["cells"][f"critic_b0_on_D_b{arm}"]["mse"]
                actual = page.locator("#content tbody tr").first.locator("td").nth(1).inner_text()
                assert abs(float(actual.replace(",", ".")) - expected) < 5e-9, (actual, expected)
    page.select_option("#pilot", "P1")
    for seed in ["510031", "510047", "510081"]:
        page.select_option("#seed", seed)
        assert "Cuatro épocas" in page.locator("#content").inner_text()
    page.screenshot(path=str(root / "reports/avance-tesis/p1.png"))
    for pilot in ["P0", "P2", "P2R", "WF05"]:
        page.select_option("#pilot", pilot)
        assert page.locator("#seed").is_disabled()
        assert "Unidades aceptadas" in page.locator("#content").inner_text()
    page.screenshot(path=str(root / "reports/avance-tesis/wf05.png"))
    page.select_option("#pilot", "P3")
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors, errors
    print(
        json.dumps(
            {
                "browser": "Chromium 1248",
                "p3_combinations": 18,
                "p1_seeds": 3,
                "other_pilots": 4,
                "page_errors": errors,
                "mobile_no_overflow": True,
            }
        )
    )
    b.close()
