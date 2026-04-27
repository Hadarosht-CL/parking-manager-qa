# Parking Manager QA Automation Project

## Overview

A QA automation project built around a parking lot management web application.
The goal was to demonstrate a structured testing approach - from exploration and bug discovery
through to automated test execution and reflection.

---

## Testing Approach

Testing was driven by business risk rather than feature coverage.
Source-code inspection was used alongside live exploration to uncover issues invisible from the UI alone.
Priority was given to flows where a failure causes financial loss or silent data corruption.

---

## What Was Tested

**Authentication** - gates access to everything; a broken login means the entire product is inaccessible.

**Parking lifecycle** - the core revenue flow. Fee calculation and session integrity touch money directly,
making correctness critical.

**Edge cases** - duplicate bookings, validation gaps, and integration failures tend to fail silently.
They were included specifically because they are the hardest to catch manually.

---

## Automation Scope

Two scenarios were automated:

- **Full parking lifecycle** - start session, end session, verify fee in history.
Chosen because every other feature depends on this flow working correctly.

- **Duplicate car plate prevention** - a second booking for an active plate must be blocked.
Chosen because data integrity failures are silent and easily missed without automation.

---

## How to Run

Start the application:

```bash
docker run --platform linux/amd64 -d -p 5000:5000 --name parking-manager doringber/parking-manager:3.1.0
```

For full setup and test execution instructions, see [`tests/README.md`](tests/README.md).

---

## Tech Stack

- **Python** - test language
- **pytest** - test runner
- **Playwright** - browser automation
- **Docker** - application runtime
- **JUnit XML** - test reporting

---

## Project Structure

```
test-plan.md        - risk-based test plan, structured test cases, and bug reports
tests/              - automated test suite (scenarios, fixtures, helpers, and README)
ai-reflection.md    - approach, trade-offs, and tool reasoning
```
