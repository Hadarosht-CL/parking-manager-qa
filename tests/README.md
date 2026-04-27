# Tests - Parking Manager Automation

## Prerequisites

- Python 3.11+
- The parking-manager Docker container must be running on `http://localhost:5000`

---

## Setup

Install Python dependencies:

```bash
pip install -r tests/requirements.txt
```

Install the Playwright browser (Chromium):

```bash
playwright install chromium
```

---

## Running the Tests

Run all tests:

```bash
pytest tests/ -v
```

Run a single test file:

```bash
pytest tests/test_parking_flow.py -v
pytest tests/test_data_integrity.py -v
```

Run in headed mode (watch the browser):

```bash
pytest tests/ --headed -v
```

---

## Test Report

> **Additional feature:** JUnit XML reporting was not required by the assignment.
> It was added because a test that runs but leaves no structured record of its outcome
> has limited value in a real automation workflow. From an automation perspective,
> the report is what makes a test suite actionable - it answers "did anything break
> since last time?" without requiring someone to watch the terminal. JUnit XML is the
> industry-standard format for this: it integrates with CI pipelines, artifact stores,
> and dashboards out of the box, turning a one-off script into a traceable, repeatable
> process.

pytest has built-in JUnit XML report generation - no extra tools or installs needed.

```bash
pytest tests/ -v --junitxml=reports/report.xml
```

This produces `reports/report.xml`, a structured file that can be opened in any browser
or ingested by CI systems (GitHub Actions, Jenkins, GitLab CI) and artifact stores like Artifactory.

### What each report captures

| Label | XML location | Description |
|---|---|---|
| **Test unique name** | `<testcase classname="..." name="...">` | Module path + function name - unique per test |
| **Test name** | `name` attribute | The test function name |
| **Date / timestamp** | `timestamp` on `<testsuite>` | When the test run started |
| **Status** | Absence or presence of `<failure>` / `<error>` / `<skipped>` | Pass, Fail, Error, or Skip |
| **Duration** | `time` attribute on `<testcase>` | Execution time in seconds |
| **Failure detail** | `<failure message="...">` body | Full error message and traceback on failure |
| **Total counts** | `tests`, `failures`, `errors` on `<testsuite>` | Suite-level summary |

### Example report structure

```xml
<testsuite name="pytest" tests="2" failures="0" errors="0" timestamp="2026-04-27T22:00:00">
  <testcase classname="tests.test_parking_flow" name="test_full_parking_lifecycle[chromium]" time="1.42"/>
  <testcase classname="tests.test_data_integrity" name="test_duplicate_plate_blocked[chromium]" time="1.31"/>
</testsuite>
```

---

## Scenario Choices

### Scenario 1 - Full Parking Lifecycle (`test_parking_flow.py`)

Covers: login -> start parking -> end parking -> verify fee in history.

This is the core happy path. If this flow breaks, the product is broken. It also
validates fee calculation correctness, which is the most business-critical output of the system.

### Scenario 2 - Duplicate Car Plate Prevention (`test_data_integrity.py`)

Covers: starting a session for a plate that is already actively parked is blocked.

Data integrity bugs are silent - they don't crash the app, they silently corrupt state.
A double-booked plate means two billing records and two active dashboard entries for the same car.
Automating this guard ensures it never regresses undetected.

---

## Stability and Reliability Notes

- **No `sleep()` calls** - all waits use Playwright's `expect()` which auto-retries until the condition is met or the timeout (30s default) is exceeded.
- **Unique test data** - each test generates a plate like `20xxxxxx` using the current timestamp suffix. This avoids state collision between test runs.
- **Locators use IDs and stable classes** - `#car_plate`, `#slot`, `.btn-danger`, `.alert-success` are tied to the app's structure, not to positional CSS paths that break on layout changes.
- **Cleanup step** - `test_data_integrity.py` ends the parking session it created, leaving the app in a clean state for the next run.
