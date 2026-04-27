import time
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"


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
