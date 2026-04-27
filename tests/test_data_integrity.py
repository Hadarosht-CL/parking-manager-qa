"""
Scenario 2 - Duplicate Car Plate Prevention (TC-07 from test-plan.md)

Why this scenario was chosen for automation:
  Data integrity bugs are silent - they don't crash the app, they just corrupt state.
  A double-booked plate means two active sessions for the same car, which breaks
  billing and operational tracking. Automating this guard ensures it never regresses
  without anyone noticing.
"""

import pytest
from playwright.sync_api import Page, expect


def test_duplicate_plate_blocked(logged_in_page: Page, unique_plate: str, base_url: str):
    page = logged_in_page

    # Step 1 - Start first parking session
    page.goto(f"{base_url}/")
    page.fill("#car_plate", unique_plate)
    page.fill("#slot", "T2")
    page.locator("input#submit").click()

    expect(page.locator(".alert-success")).to_contain_text(
        f"Parking started for {unique_plate}"
    )

    # Step 2 - Attempt a second session with the same plate on a different slot
    page.goto(f"{base_url}/")
    page.fill("#car_plate", unique_plate)
    page.fill("#slot", "T3")
    page.locator("input#submit").click()

    # Step 3 - Verify the duplicate is blocked with a warning
    expect(page.locator(".alert-warning")).to_contain_text(
        "Duplicate parking prevented"
    )

    # Step 4 - Cleanup: end the original session to leave the app in clean state
    page.goto(f"{base_url}/")
    row = page.locator("table tbody tr", has_text=unique_plate)
    row.locator("button.btn-danger").click()
