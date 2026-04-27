"""
Scenario 2 - Duplicate Car Plate Prevention (TC-07 from test-plan.md)

Why this scenario was chosen for automation:
  Data integrity bugs are silent - they don't crash the app, they just corrupt state.
  A double-booked plate means two active sessions for the same car, which breaks
  billing and operational tracking. Automating this guard ensures it never regresses
  without anyone noticing.
"""

from playwright.sync_api import Page, expect
from conftest import start_parking, end_parking_session, ALERT_WARNING


def test_duplicate_plate_blocked(logged_in_page: Page, unique_plate: str, base_url: str):
    page = logged_in_page

    # Step 1 - Start first parking session
    start_parking(page, base_url, unique_plate, "T2")

    # Step 2 - Attempt a second session with the same plate on a different slot
    page.goto(f"{base_url}/")
    page.fill("#car_plate", unique_plate)
    page.fill("#slot", "T3")
    page.locator("input#submit").click()

    # Step 3 - Verify the duplicate is blocked with a warning
    expect(page.locator(ALERT_WARNING)).to_contain_text("Duplicate parking prevented")

    # Step 4 - Cleanup: end the original session to leave the app in clean state
    end_parking_session(page, base_url, unique_plate)
