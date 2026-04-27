# Test Plan - Parking Manager

## 1. Scope & Approach

### What I chose to test and why

The starting point was source-code inspection (`app.py`, `models.py`, `forms.py`) combined with live HTTP exploration of the running container. That gave a complete, authoritative map of the system before writing a single test case.

Testing was prioritized along three axes:

| Axis | Reasoning |
|---|---|
| **Business risk** | Fee calculation and session integrity involve money and data correctness. A wrong fee or a double-booked slot is a direct business failure. |
| **User-facing flows** | Login, start parking, end parking - these are the paths every real user walks. They must work reliably. |
| **Boundary & validation** | The app enforces license plate rules both in JS (client) and Python (server). Divergence between layers is a common bug source. |

Visual/cosmetic testing and load testing were explicitly de-prioritized - the scope is correctness and reliability of functional behavior.

---

### How I structured the testing approach

```
Authentication (HIGH RISK)
- login / logout correctness
- unauthenticated access to protected routes

Parking Lifecycle (CRITICAL BUSINESS FLOW)
- start session -> end session -> fee appears in history
- fee calculation correctness

Edge Cases
- duplicate car plate and slot prevention
- slot lock expiry beyond Redis TTL
- license plate validation: format, length, boundary patterns
- user management: add, delete with/without sessions
- billing service integration on end-parking
- vehicle-types CRUD
```

---

### What I considered important

**Key risks:**
- **Financial integrity** - the fee calculation and billing flow touch money. Silent failures here (billing service unreachable, wrong rate) would go unnoticed by users but cause real revenue loss.
- **Data integrity** - a slot or car plate that can be double-booked corrupts operational state silently. Operators have no way to detect it without manual DB inspection.
- **Access control** - unauthenticated routes expose private data. In a parking system, vehicle images and session records are sensitive.

**Critical user flows:**
- Login -> start parking -> end parking -> verify fee in history (the complete lifecycle every user takes)
- Admin manages users (add, delete with/without sessions)

**Edge cases specifically looked for:**
- What happens when a session runs longer than the Redis TTL (1 hour)? The slot lock silently expires.
- What happens when external services (billing, slot service) are unreachable? The app swallows errors silently.
- Does the DB enforce the same rules as the form validation? (It does not - historical data confirms this.)
- Can the same slot be taken by two cars simultaneously? Yes, after the TTL window.

---

## 2. Test Cases

> Format: ID - Title - Preconditions - Steps - Expected Result - Priority

---

### Authentication (HIGH RISK)

**TC-01 - Valid login redirects to dashboard**
- Pre: app running, credentials `admin / password`
- Steps: navigate to `/login`, submit valid credentials
- Expected: HTTP 302 -> `/`, dashboard renders with active sessions table
- Priority: **High**

---

**TC-02 - Invalid credentials stay on login page**
- Pre: app running
- Steps: submit username `admin`, password `wrongpass`
- Expected: stays on `/login`, flash message "Invalid credentials" visible, no session cookie set
- Priority: **High**

---

**TC-03 - Unauthenticated access redirects to login**
- Pre: no active session
- Steps: navigate directly to `/`, `/history`, `/users`
- Expected: each redirects to `/login` (302), not accessible
- Priority: **High**

---

### Parking Lifecycle (CRITICAL BUSINESS FLOW)

**TC-04 - Start parking - happy path**
- Pre: logged in, no active session for the plate
- Steps: submit form with plate `20304050`, slot `A1`, vehicle type `Standard`
- Expected: flash "Parking started for 20304050", row appears in dashboard table with car plate, slot, and start time
- Priority: **High**

---

**TC-05 - End parking - session moves to history with correct fee**
- Pre: TC-04 completed, session active
- Steps: click "End Parking" for the active session
- Expected: session disappears from dashboard, appears in `/history` with `end_time` set and `fee > 0` (rate = 5/hour)
- Priority: **High**

---

**TC-06 - Fee calculation accuracy**
- Pre: known start/end times (use history seed data as reference)
- Steps: calculate expected fee manually: `(end - start) in hours x 5.0`, round to 2 decimal places
- Expected: displayed fee matches formula; e.g., 2-minute session = `(2/60) x 5 = 0.17` (verify against actual)
- Priority: **High**

---

### Edge Cases

**TC-07 - Duplicate car plate is blocked**
- Pre: plate `20304050` already has an active session
- Steps: submit start-parking form again with the same plate
- Expected: flash "Duplicate parking prevented: this car is already parked.", no new DB row
- Priority: **High**

---

**TC-08 - Duplicate slot is blocked**
- Pre: slot `A1` already occupied (active session)
- Steps: submit start-parking form with a different plate but same slot `A1`
- Expected: flash "This slot is already occupied.", no new DB row
- Priority: **High**

---

**TC-09 - Slot lock survives beyond 1 hour (Redis TTL edge case)**
- Pre: active session in slot `A1` (or simulate by letting Redis key expire)
- Steps: wait for/manually expire the Redis key for `slot:A1` (TTL = 3600s); attempt to park a new car in `A1` while original session still active
- Expected: new booking is still rejected (DB-level slot check should prevent it)
- Actual: **booking succeeds** - the DB has no slot uniqueness check; only Redis enforced it *(known bug)*
- Priority: **High**

---

**TC-10 - License plate shorter than 8 digits is rejected**
- Pre: logged in
- Steps: submit plate `1234567` (7 digits)
- Expected: validation error "License plate must be exactly 8 digits long", no session created
- Priority: **Medium**

---

**TC-11 - Non-numeric license plate is rejected**
- Pre: logged in
- Steps: submit plate `ABCD1234`
- Expected: validation error "License plate must contain only numbers", no session created
- Priority: **Medium**

---

**TC-12 - Blank slot field is rejected**
- Pre: logged in
- Steps: submit form with valid plate but empty slot field
- Expected: form validation error, no session created
- Priority: **Medium**

---

**TC-13 - Overly restrictive validation rejects valid-looking plates**
- Pre: logged in
- Steps: submit plate `12345678` (sequential, flagged as test pattern)
- Expected (per spec): should be a valid plate
- Actual: **rejected** - `validate_israeli_license_plate` blocks it as a "test license plate" *(known bug)*
- Priority: **Medium**

---

**TC-14 - Add new user**
- Pre: logged in as admin
- Steps: navigate to `/users/add`, submit username `testuser`, password `testpass`
- Expected: flash "User created", `testuser` appears in users list
- Priority: **Medium**

---

**TC-15 - Delete user without sessions**
- Pre: `testuser` exists with no parking sessions
- Steps: click Delete for `testuser`
- Expected: flash "User deleted", user removed from list
- Priority: **Medium**

---

**TC-16 - Delete user with parking sessions is blocked**
- Pre: a user has at least one parking session (active or historical)
- Steps: attempt to delete that user
- Expected: flash "Cannot delete user with parking sessions.", user remains in list
- Priority: **Medium**

---

**TC-17 - Vehicle-types page loads without error**
- Pre: logged in
- Steps: navigate to `/vehicle-types`
- Expected: page renders, shows list of vehicle types and an add form
- Actual: **HTTP 500** - `vehicle_types.html` template missing, `rate_per_hour` field missing from form *(known bug)*
- Priority: **High**

---

**TC-18 - Uploaded image is not accessible without authentication**
- Pre: a parking session with an uploaded image exists
- Steps: log out; navigate directly to `/uploads/<filename>`
- Expected: redirect to `/login`
- Actual: **file is served publicly** - no `@login_required` on the route *(known bug)*
- Priority: **High**

---

**TC-19 - Billing status reported on end-parking**
- Pre: active session exists
- Steps: end parking, observe flash message
- Expected: fee displayed with billing confirmation
- Actual: billing service unreachable -> status always `"error"` *(known bug)*
- Priority: **Medium**

---

## 3. Bug Report

### Severity Levels

| Severity | Meaning |
|---|---|
| **Critical** | Core feature broken or causes data loss; normal use is blocked |
| **High** | Significant functional or security issue with direct user/business impact; no practical workaround |
| **Medium** | Impacts edge cases or secondary features; a workaround exists but the behavior is clearly wrong |
| **Low** | Cosmetic or minor UX issue; no functional impact |

---

### BUG-01 - `/vehicle-types` route is completely broken (500 error)

**Steps to reproduce:**
1. Log in as admin
2. Navigate to `http://localhost:5000/vehicle-types`
3. Observe HTTP 500

**Expected:** Page renders with existing vehicle types and an add form

**Actual:** `jinja2.exceptions.TemplateNotFound: vehicle_types.html`

**Impact:** Pricing management is completely inaccessible. Vehicle type rates cannot be added or updated through the UI. Any business change to pricing requires a code-level fix, not an admin action. Two compounding issues cause this: `vehicle_types.html` template does not exist, and `VehicleTypeForm` is missing the `rate_per_hour` field that `app.py` expects on submit.

**Severity: Critical**

---

### BUG-02 - Slot double-booking possible after Redis TTL expires

**Steps to reproduce:**
1. Start parking for car `A` in slot `42`
2. Delete the Redis key manually: `docker exec parking-manager redis-cli del slot:42` (simulates TTL expiry after 1 hour)
3. Start parking for car `B` in slot `42`
4. Observe both sessions active for the same slot

**Expected:** Second booking rejected at all times while the slot is occupied

**Actual:** Second booking succeeds once the Redis key expires

**Impact:** Two cars can be assigned the same physical slot simultaneously. This produces conflicting active sessions, broken billing records, and an operational state that cannot be resolved without direct DB intervention. The failure is silent - the dashboard shows both sessions as valid with no warning. Any session exceeding 1 hour is vulnerable.

**Severity: High**

---

### BUG-03 - Billing service never runs; all charges silently fail

**Steps to reproduce:**
1. Start and end any parking session
2. Observe the flash message shows billing status `"error"`
3. Confirm: `docker exec parking-manager curl http://localhost:5002/charge` -> connection refused

**Expected:** Billing service processes the charge and returns `"paid"`

**Actual:** Every end-parking action silently fails billing; status is always `"error"` and no charge is recorded

**Impact:** No parking session has ever been billed since deployment. The `billing_service.py` is a separate Flask process that is never started inside the container. The `except` block in `app.py` swallows the `ConnectionRefusedError` without alerting the user or logging a visible error, making this invisible in normal use. The financial loss scales directly with the number of sessions.

**Severity: High**

---

### BUG-04 - Uploaded images served without authentication

**Steps to reproduce:**
1. Start a parking session and upload an image
2. Log out of the application
3. Navigate directly to `http://localhost:5000/uploads/<filename>`
4. Observe the image is served with HTTP 200

**Expected:** Request redirects to `/login`

**Actual:** Image file is served to any unauthenticated user who knows or guesses the filename

**Impact:** Vehicle images are personally identifiable data. Exposing them without authentication violates user privacy and may breach data protection regulations. Filenames are generated from the original upload name via `secure_filename()`, making them guessable for common naming patterns. The fix is a single missing `@login_required` decorator.

**Severity: High**

---

### BUG-05 - Input validation inconsistency: invalid plates exist in DB, valid plates get rejected

**Steps to reproduce (over-blocking):**
1. Log in, submit plate `12345678`
2. Observe: "This appears to be a test license plate" - submission rejected

**Expected:** Plate `12345678` accepted as a valid 8-digit number

**Actual:** Rejected by the `validate_israeli_license_plate` blocklist

**Impact:** Two-sided failure. Users with legitimate plates matching the blocklist patterns (`12345678`, sequential numbers) are permanently blocked from using the system with no clear remedy. At the same time, the history table contains plates like `dvdsvd`, `21341243252465234645`, and `88` - all violating current rules - proving the DB has no constraints to back up the form validation. The validation layer is both too strict for legitimate users and too weak to guarantee data integrity.

**Severity: Medium**

---

## 4. Out of Scope

- Performance / load testing
- Cross-browser UI rendering
- Mobile responsiveness
- Security penetration testing (beyond the auth observation in BUG-04)
- Slot service microservice (`parking_redis_service.py`) - not running in this deployment
