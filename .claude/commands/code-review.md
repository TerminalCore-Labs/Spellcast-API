---
description: Full audit of Spellcast-API — routers, models, interfaces, services, and integrations. Checks layer violations, SQLAlchemy patterns, Pydantic schemas, error handling, security, and test coverage. Produces a prioritized remediation plan.
---

You are the lead reviewer for Spellcast-API. Your job is to audit code against the project's architecture conventions and produce a prioritized remediation plan.

If `$ARGUMENTS` is provided, review that specific file or directory.
If no argument is given, ask the user what scope to review (single file, directory, or full project).

---

## Architecture

Spellcast-API is a FastAPI application with these layers:

```
app/
  routers/       APIRouter handlers — HTTP endpoints only
  models/        SQLAlchemy ORM models (tables, relationships)
  interfaces/    Pydantic schemas — request/response contracts
  services/      Business logic — Azure, TTS, AI integrations
  integrations/  External client initialization (DB, Redis, S3, Fernet)
  helpers/       Domain helpers (SSML, audio processing)
  utils/         Pure utility functions
middlewares/     Global auth middleware
```

**Layer rules:**
- Routers handle HTTP only — no business logic, no raw SQL
- Models define schema — no business logic in model methods
- Interfaces (Pydantic) define request/response — no DB access
- Services own integration logic — no `Request`/`Response` types
- Integrations initialize clients once — not re-instantiated per request

---

## What to check

### A. SQLAlchemy filter bug

The most critical known issue: Python's `and` operator evaluates both operands and returns the last one, silently dropping the first condition in SQLAlchemy filters.

```python
# WRONG — only filters by user_id, ignores id
.filter(AzureCredentials.id == id and AzureCredentials.user_id == user_id)

# CORRECT — comma-separated conditions
.filter(AzureCredentials.id == id, AzureCredentials.user_id == user_id)
```

Grep every `.filter(` call across all routers and models. Flag any that use `and`/`or` Python operators instead of SQLAlchemy's `and_()`, `or_()`, or comma separation.

### B. Layer violations

- **Routers with business logic:** flag any router handler with more than ~20 lines of non-HTTP logic — extract to a service or helper.
- **Direct DB calls in services:** services that import `Session` and run ORM queries should receive the session via dependency injection, not create their own.
- **Pydantic models with DB access:** any import of SQLAlchemy models inside `interfaces/` is a violation.
- **Raw SQL strings** in routers or services — use ORM or parameterized text().

### C. Naming conventions

| Context | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `user.py`, `azure.py` |
| ORM models (classes) | `PascalCase` | `Users`, `AzureCredentials` |
| Pydantic schemas | `PascalCase` + action suffix | `CredentialsCreate`, `CredentialsUpdate` |
| Route handlers | `snake_case` | `text_to_speech`, `create_credentials` |
| DB columns | `snake_case` | `user_id`, `created_at` |
| Constants | `UPPER_SNAKE_CASE` | defined in `misc/consts.py` |

Flag any deviation.

### D. Type safety

- Flag route handlers missing response model (`response_model=`) declaration.
- Flag Pydantic models with `Any` type fields.
- Flag functions with untyped parameters or missing return type annotations.
- Flag bare `except:` or `except Exception:` without re-raising or logging.

### E. Error handling

- Every router handler must return appropriate HTTP status codes — flag handlers that return 200 on error conditions.
- Flag missing `HTTPException` raises where validation or auth fails.
- Flag `try/except` blocks that swallow exceptions silently.
- Flag missing `db.rollback()` after failed DB writes.

### F. Security

- Flag any endpoint missing auth dependency (`Depends(get_current_user)` or equivalent) that should be protected.
- Flag any credential or secret hardcoded in source — must use environment variables via `config/`.
- Flag any user-controlled input used in raw string formatting for queries.
- Flag missing input length/format validation on fields that go directly to DB.

### G. Tests

No tests currently exist. Report what needs to be created:

- **High:** Auth middleware, credential encryption/decryption, SQLAlchemy filter logic
- **Medium:** TTS service calls, Azure integration wrappers
- **Low:** Utility functions, Pydantic schema validation

Suggest framework: `pytest` + `pytest-asyncio` + `httpx` (AsyncClient) for FastAPI.

---

## Output format

For each file reviewed:

```
### app/routers/user.py

SQLAlchemy filters
⚠ Line 87: .filter(Credentials.id == id and Credentials.user_id == uid) — use comma separation
⚠ Line 134: .filter(UserSubscription.user_id == uid and UserSubscription.active == True) — use comma separation

Layer
✓ No raw SQL
⚠ Lines 200–240: Azure API call inline in router — extract to services/azure.py

Type safety
⚠ Line 45: return type missing on get_user_data handler
⚠ Line 12: field: Any in UserResponse schema

Error handling
⚠ Line 98: except Exception: pass — log and raise HTTPException

Security
✓ Credentials encrypted via Fernet
⚠ Line 67: endpoint /user/admin missing auth dependency

Tests
⚠ No tests for credential filter logic — HIGH priority (security-critical)
```

---

## Remediation plan

```
## Remediation Plan

### P1 — Critical (SQLAlchemy bugs — silent data leaks)
- [ ] Fix and → comma in .filter() calls (list all files + lines)

### P2 — Quick wins
- [ ] Add response_model to all handlers missing it
- [ ] Add return type annotations to all functions
- [ ] Fix swallowed except blocks (list files)
- [ ] Add db.rollback() after failed writes (list files)

### P3 — Architecture
- [ ] Extract business logic from routers to services (list)
- [ ] Add auth dependency to unprotected endpoints (list)

### P4 — Test coverage
- [ ] Set up pytest + pytest-asyncio + httpx
- [ ] Write tests for High-priority areas (list)
- [ ] Write tests for Medium-priority areas (list)
```

Show counts: total findings, by severity (P1/P2/P3/P4), by category.
