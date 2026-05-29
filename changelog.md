# Task Manager — Changelog

A running log of issues encountered and fixes applied across each phase of the project.

---

## v1.0.1 — Pre-merge cleanup and hardening

**Frontend README source layout had a false auth.ts reference**
The `api/` directory only contains `tasks.ts`. The README incorrectly listed `auth.ts` as a separate file. Removed the false reference; the description now reads "task fetch helpers and SessionExpiredError".

**Documentation version drift**
`documentation.md` listed TypeScript 5 and Vite 6. Updated to TypeScript 6 and Vite 8 to match `package.json`. React version was already updated to 19 in a prior pass.

**React Fast Refresh lint error: button.tsx exported both Button and buttonVariants**
The ESLint `react-refresh/only-export-components` rule requires component files to export only components. Moved `buttonVariants` into a dedicated `frontend/src/components/ui/button-variants.ts` file. `button.tsx` now imports from there and exports only `Button`.

**React Fast Refresh lint error: AuthContext.tsx exported both AuthProvider and useAuth**
Same rule violation. Moved `useAuth` into a new `frontend/src/context/useAuth.ts` file. `AuthContext.tsx` now exports only `AuthProvider` plus the `AuthContext`, `AuthContextType`, and `AuthUser` types needed by the hook. Updated imports in `App.tsx`, `AuthPage.tsx`, and `TasksPage.tsx` to pull `useAuth` from `@/context/useAuth`.

**MongoDB unique index startup note missing from documentation**
Added a callout to `documentation.md` warning that `init_db()` creates unique indexes on `users.email` and `users.username` at startup, and that the app will fail to start if duplicate values already exist in the collection.

---

## Phase 1 — Foundation

**shadcn/ui init failed: Tailwind config not found**
shadcn expects a `tailwind.config.js` file. Tailwind v4 dropped this in favour of `@import "tailwindcss"` in the CSS file. Fixed by adding the CSS import first, then re-running `npx shadcn@latest init`.

**shadcn/ui init failed: import alias not found**
shadcn reads path aliases from the root `tsconfig.json`, but Vite scaffolds them into `tsconfig.app.json`. Fixed by copying `compilerOptions.paths` into the root config and adding `"ignoreDeprecations": "6.0"` for the TypeScript 6.x `baseUrl` deprecation warning.

**MongoDB: no default database name**
The Atlas connection string (`mongodb+srv://.../?appName=...`) has no database in the path, so `client.get_default_database()` threw `ConfigurationError`. Fixed by switching to `client[os.environ.get("DB_NAME", "taskmanager")]` and adding `DB_NAME=taskmanager` to `.env`.

**MongoDB: SSL handshake TLSV1_ALERT_INTERNAL_ERROR**
Looked like a Python 3.14 / OpenSSL 3.0.18 TLS incompatibility. Was actually MongoDB Atlas rejecting the connection because the development machine's IP was not on the Atlas Network Access whitelist — Atlas returns a TLS alert for unrecognised IPs. Fixed by whitelisting the IP in Atlas → Network Access. Network access is currently set to `0.0.0.0/0` (all IPs) for local development — must be locked down before any production deployment.

---

## Phase 3 & 4 — Task API and UI

**`/api/tasks` returning 404 after backend restart**
Six stale Flask debug-mode processes were still bound to port 5000. Flask's reloader spawns a parent+child pair — killing only the child causes the parent to respawn it immediately. Fixed by writing a PowerShell script to find all Python processes with `app.py` in their command line and kill them all at once.

**`taskkill /F` failing from Git Bash**
Git Bash interprets `/F` as a Unix file path, not a Windows flag. Fixed by writing the kill logic as a `.ps1` script and invoking it via `powershell -ExecutionPolicy Bypass -File`.

**Design review fixes**
- `space-y-1` → `space-y-1.5` on label/input wrappers for consistent vertical rhythm.
- Task name `truncate` → `line-clamp-2` to allow two lines before clipping.
- Textarea missing `transition-colors` — added to match shadcn `Input` focus animation.
- Delete button missing `self-start` — it was stretching to the full card height.
- Delete errors were shown via `alert()` — replaced with inline rendered state.

---

## Phase 5 — Task Editing

**Design review fixes**
- Create form used `space-y-1` while edit form used `space-y-1.5`. Normalised both to `space-y-1.5`.
- Edit button had a hover text change but no background change, making it visually asymmetric with the Delete button. Added `hover:bg-accent`.

---

## Phase 6 — Hardening

**Backend accepted any string as a deadline**
`"banana"` was a valid deadline. Added `_DATE_RE` regex (`^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$`) in `_validate_fields()` and a `date.fromisoformat(deadline) < date.today()` past-date check.

**No field length caps**
Unbounded strings could reach MongoDB. Added caps: username 50, email 254, password 6–128, task name 200, description 2000.

**No session expiry handling**
Mid-session 401s returned cryptic error messages. Added `SessionExpiredError` class and `apiFetch()` wrapper in `tasks.ts` — any 401 throws `SessionExpiredError`, which `handleApiError()` catches and routes to `logout()`, redirecting automatically.

---

## Phase 7 — Cloud-Readiness

**MongoClient created per request**
`get_db()` was called inside Flask's `g` (request context), opening a new connection pool on every HTTP request. Under any load this exhausts Atlas free-tier connection limits. Fixed by moving `MongoClient` to an app-level singleton initialised once in `init_db(app)` at startup.

**Hardcoded config values**
`SESSION_COOKIE_SECURE=False`, `CORS origins=["http://localhost:5173"]`, and `debug=True` were all hardcoded. Any accidental deploy would have broken sessions, blocked the frontend, and exposed the debug console. Fixed by reading all three from environment variables with safe local defaults.

---

## DevOps Step 2 - Terraform free-tier infrastructure

**Terraform infrastructure added for Azure free-tier deployment**
Added `infra/terraform/` with AzureRM provider configuration, Resource Group, Linux App Service Plan, Linux Web App, Azure Static Web App, outputs, variables, example tfvars, and Terraform-specific README documentation.

**Free-tier guardrails added**
The App Service Plan SKU is validated to `F1`, the Static Web App SKU tier and size are validated to `Free`, and the Linux Web App explicitly sets `always_on = false` because Free F1 does not support Always On.

**Local Terraform state kept intentional**
Remote state is not configured by default to avoid provisioning extra Azure Storage resources for this personal project. The Terraform docs now explain that production should use remote state with locking.

**Optional budget alert made stable**
The optional Azure resource-group budget alert uses an explicit `budget_start_date` variable instead of a dynamic timestamp, avoiding recurring Terraform diffs. Budget alert email is guarded so it cannot be empty when the alert is enabled.

**Terraform state and secrets ignored**
Updated `.gitignore` to exclude local `.terraform/`, `terraform.tfvars`, and Terraform state files so secrets and local state do not get committed.

---

## DevOps Step 1 - Backend deployment foundation

**Backend health check added**
Added a `/health` endpoint returning `{"status": "ok"}` so CI workflows and deployment smoke checks can verify the Flask API without depending on MongoDB.

**Backend test foundation added**
Added `pytest` and a health endpoint test under `backend/tests/`, with test-mode environment handling so the app can be imported without real production secrets.

**Production secret fallback removed**
The Flask `SECRET_KEY` is required outside test mode. This prevents production from silently running with a known default secret.

**Docker CI validation support added**
Added `backend/Dockerfile` using `python:3.11-slim` and Gunicorn on port 5000. This is for CI validation only; Azure deployment remains source-based App Service deployment.

**Backend environment example added**
Added `backend/.env.example` with placeholders for MongoDB, Flask secret, database name, CORS origins, production mode, and secure-cookie settings.

---
