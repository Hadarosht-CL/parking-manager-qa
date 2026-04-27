"""
Scenario 1 - Full Parking Lifecycle (TC-04 + TC-05 + TC-06 from test-plan.md)

Why this scenario was chosen for automation:
  This is the single most critical user journey in the application.
  Every other feature (history, billing, duplicate prevention) depends on
  this flow working correctly. If it breaks, the product is broken.
  Automating it catches regressions on the happy path immediately.
"""

from playwright.sync_api import Page, expect
from conftest import start_parking, end_parking_session, ALERT_INFO, SESSION_ROW


def test_full_parking_lifecycle(logged_in_page: Page, unique_plate: str, base_url: str):
    page = logged_in_page
    slot = "T1"

    # Step 1 - Start parking session
    start_parking(page, base_url, unique_plate, slot)

    # Step 2 - Verify active session appears in the dashboard table
    dashboard_table = page.locator("table tbody")
    expect(dashboard_table.locator(f"tr:has-text('{unique_plate}')")).to_be_visible()
    expect(dashboard_table.locator(f"tr:has-text('{slot}')")).to_be_visible()

    # Step 3 - End the parking session
    end_parking_session(page, base_url, unique_plate)
    expect(page.locator(ALERT_INFO)).to_contain_text(unique_plate)

    # Step 4 - Verify session appears in history with a calculated fee
    page.goto(f"{base_url}/history")
    history_row = page.locator(SESSION_ROW, has_text=unique_plate)
    expect(history_row).to_be_visible()

    # Fee is the 5th column (index 4, zero-based).
    # We assert it is a parseable float and not the null placeholder "-".
    # A test that starts and ends in under 7 seconds will produce fee=0.0 due to
    # rounding (round(seconds/3600 * 5, 2)), which is correct app behaviour -
    # not a bug. The meaningful assertion here is that the fee field was populated
    # at all, proving the calculation ran.
    fee_text = history_row.locator("td").nth(4).inner_text().strip()
    assert fee_text != "-", "Fee was not calculated (null value in history)"
    fee = float(fee_text)
    assert fee >= 0, f"Fee must be non-negative, got {fee}"
