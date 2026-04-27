import time
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

# Centralized selectors - single source of truth for all locators used across tests
CAR_PLATE_INPUT = "#car_plate"
SLOT_INPUT = "#slot"
SUBMIT_BTN = "input#submit"
ALERT_SUCCESS = ".alert-success"
ALERT_WARNING = ".alert-warning"
ALERT_INFO = ".alert-info"
SESSION_ROW = "table tbody tr"
END_SESSION_BTN = "button.btn-danger"


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture
def unique_plate() -> str:
    # "20" prefix guarantees the plate is never sequential, never all-same digits,
    # and never in the app's test-pattern blocklist.
    # Last 6 digits of the current timestamp make each test run unique.
    suffix = str(int(time.time()))[-6:]
    return f"20{suffix}"


@pytest.fixture
def logged_in_page(page: Page, base_url: str) -> Page:
    page.goto(f"{base_url}/login")
    page.fill("#username", ADMIN_USERNAME)
    page.fill("#password", ADMIN_PASSWORD)
    page.click("button[type=submit]")
    expect(page).to_have_url(f"{base_url}/")
    return page


def start_parking(page: Page, base_url: str, plate: str, slot: str) -> None:
    """Fill the start-parking form, submit, and assert the success flash message."""
    page.goto(f"{base_url}/")
    page.fill(CAR_PLATE_INPUT, plate)
    page.fill(SLOT_INPUT, slot)
    page.locator(SUBMIT_BTN).click()
    expect(page.locator(ALERT_SUCCESS)).to_contain_text(f"Parking started for {plate}")


def end_parking_session(page: Page, base_url: str, plate: str) -> None:
    """Navigate to dashboard, find the active session row by plate, and end it."""
    page.goto(f"{base_url}/")
    row = page.locator(SESSION_ROW, has_text=plate)
    # "סיים" is Hebrew for "End" - the button label as rendered by the template
    row.locator(END_SESSION_BTN).click()
