# Reflection - Parking Manager Assignment

## Overall Approach and Key Decisions

The starting point was source-code inspection rather than UI exploration. Reading `app.py`, `models.py`, and `forms.py` directly revealed the full contract of the system - every route, validation rule, and external dependency - before any manual testing began. This surfaced bugs that UI exploration alone would have missed entirely, such as the billing service never running and the Redis TTL leaving slots unprotected after one hour.

Playwright was chosen as the automation tool for its built-in auto-wait mechanism, which eliminates the need for manual waits and produces more stable tests. It also required no version-matching between browser and driver, which reduces setup friction for anyone running the suite.

JUnit XML reporting was added as an extra layer beyond the assignment requirements. The reasoning: a test that runs but leaves no structured record has limited reuse value. JUnit XML is built into pytest with no additional dependencies, and its output is machine-readable by CI pipelines and artifact stores - making the suite ready to plug into a real workflow without changes.

---

## Trade-offs

**`fee >= 0` instead of `fee > 0`**
A sub-second test session produces `fee = 0.0` due to rounding, which is correct application behaviour. Asserting `> 0` would cause a false failure on every fast run. The meaningful assertion is that the fee field was calculated at all - not its specific value in a time-dependent context.

**E2E browser tests vs API-level tests**
Both approaches could cover the same two scenarios. Browser tests exercise the full stack including client-side JS validation, which caught a real discrepancy (the JS blocklist is more restrictive than the server-side check). The trade-off is that browser tests are slower and more sensitive to UI changes. API-level tests would be faster and more stable, but would bypass the JS layer entirely and miss that class of bug.

**Focused scope over broad coverage**
Two well-structured scenarios were chosen over a larger number of shallow ones. The priority was tests that provide clear signal when they fail - each assertion maps to a specific, documented risk from the test plan.

---

## AI Tools & Technologies Used

| Tool / Technology | Role in the project |
|---|---|
| **Claude (Anthropic)** | Codebase exploration, bug discovery, test plan authoring, automation code |
| **Python** | Language for all test code |
| **pytest** | Test runner and reporting backbone |
| **Playwright** (`pytest-playwright`) | Browser automation for E2E scenarios |
| **Docker** | Running the application under test in an isolated, reproducible environment |
| **JUnit XML** | Structured test reporting (built into pytest) |

**Suggested addition - Applitools Eyes**
For visual regression coverage that the current suite does not provide, Applitools Eyes is worth considering. It uses AI to compare screenshots across runs and flags visual changes - layout shifts, broken styles, missing elements - without requiring explicit assertions for each one. It integrates directly with Playwright, so it could be layered on top of the existing tests with minimal changes.

---

## Reasoning Behind Tool Choices

**Python + pytest**
Python is the natural fit for a Flask application - the same language as the app under test, which made reading and reasoning about the source straightforward. pytest was chosen as the runner because it integrates natively with both `pytest-playwright` and JUnit XML output, requires no configuration boilerplate, and its fixture model (`conftest.py`) keeps shared setup cleanly separated from test logic.

**Docker**
Running the app in Docker meant every test run targets an identical environment regardless of the machine. This removes a whole class of "works on my machine" failures and makes the suite trustworthy as a regression baseline.

**Claude**
Source-code access inside the container allowed analysis that would otherwise require manual reading of dozens of files. It accelerated bug discovery (the Redis TTL issue, the missing template, the billing service never starting) and made it possible to write locator-accurate tests on the first attempt by inspecting the actual HTML templates before writing a single line of automation code. The limitation is that it cannot run tests autonomously or observe the live browser - human judgment is still needed to validate that what the tool proposes is actually correct.
