# Test Plan - Parking Manager

## 1. Scope & Approach

### What I chose to test and why

My starting point was source-code inspection (`app.py`, `models.py`, `forms.py`) combined with live HTTP exploration of the running container. That gave me a complete, authoritative map of the system before writing a single test case.

I prioritized testing along three axes:

| Axis | Reasoning |
|---|---|
| **Business risk** | Fee calculation and session integrity involve money and data correctness. A wrong fee or a double-booked slot is a direct business failure. |
| **User-facing flows** | Login, start parking, end parking - these are the paths every real user walks. They must work reliably. |
| **Boundary & validation** | The app enforces license plate rules both in JS (client) and Python (server). Divergence between layers is a common bug source. |

I explicitly de-prioritized visual/cosmetic testing and load testing - the scope is correctness and reliability of functional behavior.

---

### How I structured the testing approach

```
Authentication
- login / logout correctness

Core Parking Flow (happy path)
- start session -> end session -> fee appears in history

Data Integrity
- duplicate car plate prevention
- duplicate slot prevention
- slot lock expiry edge case

Input Validation
- license plate: format, length, edge cases
- server-side vs client-side divergence

User Management
- add user, delete user, delete user with sessions

System & Integration
- billing service call on end-parking
- vehicle-types CRUD
- unauthenticated access to protected routes
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

**Edge cases I specifically looked for:**
- What happens when a session runs longer than the Redis TTL (1 hour)? The slot lock silently expires.
- What happens when external services (billing, slot service) are unreachable? The app swallows errors silently.
- Does the DB enforce the same rules as the form validation? (It does not - historical data confirms this.)
- Can the same slot be taken by two cars simultaneously? Yes, after the TTL window.

---

## 2. Test Cases

> Format: ID - Title - Preconditions - Steps - Expected Result - Priority

---

### Authentication

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

### Core Parking Flow

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

### Data Integrity

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

### Input Validation

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

### User Management

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

### System & Integration

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

**Severity: Critical**

**Impact:** Any attempt to manage vehicle types (add new types, adjust rates) crashes with a 500. The feature is fully inaccessible, meaning pricing cannot be updated through the UI. Confirmed live.

**Root cause (two compounding issues):**
1. `VehicleTypeForm` in `forms.py` is missing the `rate_per_hour` field - `app.py` calls `form.rate_per_hour.data` on submit, which would raise `AttributeError`
2. The template `vehicle_types.html` does not exist in `/app/templates/`, so even the GET request crashes with `TemplateNotFound`

**Steps to reproduce:**
1. Log in as admin
2. Navigate to `http://localhost:5000/vehicle-types`
3. Observe HTTP 500

**Expected:** Page renders with existing vehicle types and an add form
**Actual:** `jinja2.exceptions.TemplateNotFound: vehicle_types.html`

---

### BUG-02 - Slot double-booking possible after Redis TTL expires

**Severity: High**

**Impact:** A parking slot can be booked by a second car while the original car is still actively parked, if the session exceeds 1 hour. This leads to two active sessions for the same physical slot - a direct operational failure.

**Root cause:** Redis slot lock uses `expire(slot_key, 3600)` (1 hour TTL). There is no DB-level uniqueness check on `slot` for active sessions (`end_time IS NULL`). Once the Redis key expires, the guard is gone.

**Steps to reproduce:**
1. Start parking for car `A` in slot `42`
2. Wait for Redis key `slot:42` to expire (or delete it manually: `docker exec parking-manager redis-cli del slot:42`)
3. Start parking for car `B` in slot `42`
4. Both sessions now show as active for the same slot

**Expected:** Second booking rejected at all times while slot is occupied
**Actual:** Second booking succeeds after Redis TTL

---

### BUG-03 - Billing service never runs; all charges silently fail

**Severity: High**

**Impact:** Every "End Parking" action results in billing status `"error"`. No charges are ever processed. The feature appears to work (flash message is shown) but no billing occurs. This is a silent data-integrity failure with financial consequence.

**Root cause:** `app.py` calls `http://localhost:5002/charge` on end-parking. `billing_service.py` is a separate Flask process that is not started inside the container. The `except` block swallows the `ConnectionRefusedError` and defaults to `"error"`.

**Steps to reproduce:**
1. Start and end any parking session
2. Observe flash: "Fee: X.XX (billing: error)"
3. `docker exec parking-manager curl http://localhost:5002/charge` -> connection refused

**Expected:** Billing service processes the charge and returns `"paid"`
**Actual:** Always returns `"error"`; charge is never recorded

---

### BUG-04 - Uploaded images served without authentication

**Severity: High**

**Impact:** Any uploaded car image is publicly accessible by URL without logging in. An attacker who knows or guesses filenames can access vehicle image data - a privacy and compliance risk.

**Root cause:** `@app.route('/uploads/<filename>')` in `app.py` is missing `@login_required`.

**Steps to reproduce:**
1. Start a parking session with an uploaded image
2. Log out
3. Navigate to `http://localhost:5000/uploads/<filename>`
4. Image is served with HTTP 200

**Expected:** Redirect to `/login`
**Actual:** File served to unauthenticated user

---

### BUG-05 - Input validation inconsistency: invalid plates exist in DB, valid plates get rejected

**Severity: Medium**

**Impact (two-sided):**
- **Over-blocking:** Plates like `12345678` are rejected by `validate_israeli_license_plate` as "test patterns" even though they could be legitimate plates. Users with real vehicles are blocked.
- **Under-enforcing:** The history table contains plates such as `dvdsvd`, `21341243252465234645`, `88`, `123` - all violating current validation rules. This confirms validation was either added retroactively or can be bypassed, and the DB has no constraints to enforce the rules at the data layer.

**Root cause:**
- `forms.py` applies validation only at form submission (client-side + server-side). No DB-level column constraint enforces plate format.
- The "test pattern" blocklist (`12345678`, `87654321`, sequential numbers) is overly aggressive.

**Steps to reproduce (over-blocking):**
1. Log in, submit plate `12345678`
2. Observe: "This appears to be a test license plate"

**Expected:** Plate accepted (it's a valid 8-digit number)
**Actual:** Rejected

---

## 4. Out of Scope

- Performance / load testing
- Cross-browser UI rendering
- Mobile responsiveness
- Security penetration testing (beyond the auth observation in BUG-04)
- Slot service microservice (`parking_redis_service.py`) - not running in this deployment
