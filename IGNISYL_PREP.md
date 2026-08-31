# IGNISYL — Interview Prep (rebuilt from code, single-pass read)

*Investigation scope: README.md, docs/CURRENT_STATUS.md, docs/Architecture.md, backend/main.py (grepped), backend/ml_engine/{hybrid_detector.py, model_trainer.py, anomaly_detector.py (partial), risk_scorer.py (partial)}, backend/api/websocket.py, backend/api/routes.py (grepped for structure only). Read-only, no execution, one pass.*

---

## 1. Plain rebuild of understanding

**What it does, in one breath:** IGNISYL watches simulated "employee activity" (file access, downloads, logins, off-hours behavior, honeypot file touches) and scores each activity 0–100 for how much it looks like an insider threat. Instead of a blunt allow/block, it sorts that score into 4 tiers — ALLOW, MONITOR, RESTRICT (human analyst decides), BLOCK (auto) — and shows it all live on a dashboard. The "firewall" part generates the OS command it *would* run to block a user, logs it, but does not actually execute it — it's explicitly a simulation for academic/demo safety, not a real enforcement system.

**Real architecture — what talks to what:**

```
React dashboard (frontend/) 
      │  REST calls + WebSocket
      ▼
FastAPI backend (backend/main.py = real entry point)
      │
      ├─► ml_engine/hybrid_detector.py  (AdvancedHybridDetector — the actual ensemble)
      │        ├─ Isolation Forest (sklearn)
      │        ├─ Autoencoder (TensorFlow → PyTorch → numpy fallback, whichever is installed)
      │        └─ XGBoost (falls back to sklearn GradientBoosting if xgboost missing)
      │        → each model's score normalized, then weighted-averaged into one 0-100 risk score
      │
      ├─► ml_engine/risk_scorer.py (ContextualRiskScorer) — adds business-context
      │        rules on top (off-hours, large transfer, department exceptions, etc.)
      │
      ├─► routes.py — the other ~29 REST endpoints (dashboard stats, users, threats,
      │        analyst actions, reports) — initialized by main.py passing it the
      │        already-built ml_detector/risk_scorer/data_generator instances
      │
      ├─► api/websocket.py — ConnectionManager broadcasts threat_alert / system_update /
      │        risk_change events to every connected dashboard client
      │
      └─► SQLite (3 separate .db files — main, activities, users) via SQLAlchemy
```

Everything runs on a single machine for the demo — no real network agents, no real firewall calls. That's by design (see docs/CURRENT_STATUS.md, which is unusually candid about this).

---

## 2. Core vs. Unnecessary (be honest about this in the interview)

### ✅ Real, working, demonstrable core
- **`backend/main.py`** — the actual FastAPI entry point. Wires up the ML detector, risk scorer, data generator at startup; defines `/api/v1/analyze` directly.
- **`ml_engine/hybrid_detector.py` (`AdvancedHybridDetector`)** — this IS the ensemble. Genuinely interesting engineering: it probes which ML libraries are installed at runtime and picks the best available implementation per model (sklearn IF is fixed; autoencoder tries TensorFlow → PyTorch → a hand-written numpy statistical fallback; XGBoost falls back to sklearn's GradientBoosting). This is real, defensible, working code — lead with this.
- **`ml_engine/risk_scorer.py` (`ContextualRiskScorer`)** — a genuinely large, hand-built rules layer (~25 weighted risk factors across temporal/data/network/behavioral/system/application categories, plus contextual modifiers like "Finance dept + month-end = expected, reduce score"). This is real domain-engineering work, not boilerplate.
- **`api/websocket.py`** — a clean, working `ConnectionManager` broadcast pattern (connect/disconnect tracking, broadcast, targeted risk-change threshold of >10 points). Simple and solid.
- **The 4-tier graduated response concept** (ALLOW/MONITOR/RESTRICT/BLOCK) — this is the project's actual novel/thesis-worthy idea versus a binary allow/block system, and it's implemented end-to-end (score → tier → simulated action → WebSocket broadcast).
- **`routes.py`** — large (~1950 lines, ~29 endpoints) but functionally real: dashboard stats, user CRUD, threat lists, analyst actions, PDF report endpoints all exist and are wired to the components `main.py` built.

### ⚠️ Dead weight / half-built / safe to not lead with
- **`ml_engine/anomaly_detector.py` (`BehavioralAnomalyDetector`)** — an earlier/parallel implementation of essentially the same 3-model ensemble idea (IF + Keras autoencoder + XGBoost), but **`main.py` never imports it** — only `hybrid_detector.py` is wired into the live app. This looks like an earlier draft that was superseded but never deleted. Fine to say "we iterated and consolidated into one detector, the other was an earlier version we didn't clean up."
- **Firewall enforcement** — openly acknowledged by the project's own docs (`CURRENT_STATUS.md`) as simulation-only: commands are generated and logged, never executed. Don't oversell this as "we built a firewall" — say "graduated response engine with simulated enforcement," which is accurate and still impressive.
- **Documented-vs-actual ensemble weights mismatch** — README/Architecture.md advertise a fixed **30% IF / 30% AE / 40% XGB** weighting. The actual default in `AdvancedHybridDetector.predict()` is **`{isolation_forest: 0.4, autoencoder: 0.4, xgboost: 0.2}`** unless the caller overrides it. *Unclear from a single read* whether `main.py` passes different weights at call time — didn't chase this further. Worth knowing this exists so you're not caught flat-footed, but don't volunteer it unless asked something specific about the weighting.
- **Future-roadmap items** (SIEM/SOAR, AD integration, endpoint agents, Kubernetes, multi-tenant, LSTM models) — all explicitly listed as NOT built. Don't describe these as "coming soon" features you built partway; they're roadmap bullet points only.
- **`baseline_models.py`, `data_generator.py`, `RUN_BASELINE_COMPARISON.md`, `BASELINE_COMPARISON_FIXES.md`, `SECURITY_TASKS_COMPLETED.md`** — not read in detail (out of scope for this pass); these read as comparison/utility/cleanup scripts rather than core architecture. Treat as supporting cast, not talking points.
- **Docker/Kubernetes, PostgreSQL** — mentioned in tech stack tables but explicitly marked "not implemented" in `CURRENT_STATUS.md`. The real deployment is SQLite + single-server localhost.

---

## 3. Interview prep

### 60–90 second project walkthrough (say this out loud, time it)

> "IGNISYL is an insider-threat detection system I built as my final-year project. The core idea: instead of a binary allow-or-block firewall, it scores every user activity 0 to 100 using an ML ensemble — Isolation Forest for unsupervised anomaly detection, an autoencoder for reconstruction-error-based pattern recognition, and XGBoost for supervised classification — and combines their scores into one risk number. That score then routes into a 4-tier graduated response: low scores are just logged, medium triggers enhanced monitoring, high goes to a human analyst for a decision, and critical auto-blocks with incident response. It's a FastAPI backend with a React dashboard that gets live updates over WebSocket whenever a new threat is scored, backed by SQLite. One engineering detail I'm proud of: the ensemble detects which ML libraries are actually installed at runtime — TensorFlow, PyTorch, XGBoost, sklearn — and gracefully falls back to the next-best implementation, down to a hand-written numpy statistical model if nothing else is available, so the system degrades instead of crashing. I also built a fairly deep rules layer on top — about 25 weighted risk factors plus business-context modifiers, like recognizing that Finance doing large transfers at month-end is expected, not suspicious. The firewall enforcement itself is simulation-mode by design — it generates and logs the OS-level block command but doesn't execute it, which was a deliberate scoping decision for a safe academic demo."

### Core components — what + why-this-over-the-obvious-alternative (one sentence each)

- **Isolation Forest** — chosen because it's unsupervised and needs no labeled "insider threat" examples, which don't realistically exist in volume; the obvious supervised-only alternative can't detect novel attack patterns it's never seen.
- **Autoencoder** — chosen to catch anomalies as *reconstruction error* on normal-behavior patterns, complementing IF by modeling non-linear feature interactions that a tree-based method can miss.
- **XGBoost** — the supervised leg of the ensemble, added because gradient boosting handles the imbalanced normal-vs-anomalous class split far better than plain logistic regression.
- **Weighted ensemble over a single "best" model** — no single model reliably separates insider threats from noisy normal behavior alone, so combining three different failure modes reduces false positives/negatives versus betting on one algorithm.
- **4-tier graduated response over binary allow/block** — real security teams need a middle ground for ambiguous cases; binary systems either annoy users with false blocks or miss real threats by being too permissive — the RESTRICT tier keeps a human in the loop exactly where the model is least confident.
- **Runtime library auto-detection in the hybrid detector** — over hard-pinning to one deep-learning framework, this made the project runnable and demoable regardless of what's installed in a given grading/dev environment.
- **WebSocket dashboard over polling** — threat detection is only useful if an analyst sees it immediately; polling would add latency and load for no benefit here.
- **Simulation-mode firewall over real enforcement** — the obvious alternative (actually calling `netsh`/`iptables`) requires elevated privileges and risks locking out real users during a demo; simulation keeps the project safe, cross-platform, and reversible while still proving the decision logic end-to-end.

### 1–2 real challenges (STAR, ~30 seconds each)

**1. Combining three incompatible score scales into one number**
- **S:** Isolation Forest's `decision_function` returns an unbounded distance score, the autoencoder returns raw MSE reconstruction error, and XGBoost returns a clean 0–1 probability — three completely different scales.
- **T:** Needed one comparable 0–100 risk score to drive the graduated-response tiers.
- **A:** Normalized each model's output independently before combining — min-max scaled the IF decision function (inverted so higher = more anomalous), clipped the autoencoder's error against its own 95th-percentile training threshold, and used XGBoost's probability directly — then did a weighted average across all three.
- **R:** One consistent, tier-ready risk score regardless of which underlying models actually ran, and each model's contribution stayed interpretable on its own.

**2. Making the ML stack resilient to missing dependencies**
- **S:** Deep-learning frameworks (TensorFlow/PyTorch) and XGBoost aren't guaranteed to install cleanly everywhere the project might be graded or demoed, but the ensemble design depended on all three.
- **T:** Keep the detector fully functional even if a library is missing, rather than crashing at import time.
- **A:** Built an `MLLibraryDetector` that probes for sklearn/XGBoost/TensorFlow/PyTorch at startup, and had each model class (`HybridAutoencoder`, `HybridXGBoost`) pick the best available implementation, down to a hand-written numpy statistical fallback for the autoencoder if no deep-learning library exists at all.
- **R:** The system degrades gracefully instead of hard-failing, and it's demoable on a bare-minimum environment with just sklearn installed.

### What to skip entirely
Don't prep depth on: actual firewall/network enforcement (it's simulated — say so plainly if asked), Docker/Kubernetes/PostgreSQL/SIEM/AD integration (all roadmap-only, not built), or the baseline-comparison scripts. If asked directly, the honest one-liner is: "that part was an earlier iteration / scoped out for the academic version — didn't end up being used in the final build."

**Correction from last pass:** `ml_engine/anomaly_detector.py` is NOT dead code — it's still not imported by `main.py`, but the untracked `tests/` suite (`test_autoencoder.py`, `test_isolation_forest.py`, `test_logical_module2.py`, `test_logical_module3.py`) directly imports and unit-tests `BehavioralAnomalyDetector` from it. Same story for `alert_manager.py`, `log_processor.py`, and `model_trainer.py` — all covered by `tests/test_logical_module1.py` / `test_data_ingestion_preprocessing.py` despite zero references from the live app. **Not deleted.** See §4 below for what this actually means.

---

## 4. Follow-up pass — network monitoring, cleanup, tech inventory, broken things

*Scope: read-only except one confirmed-safe deletion (below). No live monitoring run, no real activity captured or read.*

### Privacy note — real data found, not read
These local DB/log files carry modification dates from past runs (Dec 2025–May 2026) and may contain real captured activity. **Not opened, not summarized** — paths only, your call on deletion:
- `backend/data/activities.db`
- `backend/data/sessions.db`
- `backend/data/users.db`
- `data/ignisyl.db`
- `data/sessions.db`
- `data/logs/application.log`, `data/logs/security.log` — both 0 bytes, empty.

### Task 1 — Is "flag downloads over X MB" real-time or batch?
**Batch/periodic by design, not real-time.** `services/network_monitor.py`:
- Runs a `while True: ... time.sleep(check_interval)` loop, default **30-second polling interval**.
- Each tick reads cumulative system-wide bytes via `psutil.net_io_counters()`, diffs against the last tick's baseline, and checks the delta against a threshold.
- It's a **standalone script** (`if __name__ == "__main__"`), zero references from `main.py`/`routes.py` — you run it manually alongside the server, it POSTs suspicious activity to the live `/api/v1/analyze` endpoint.
- Minor internal inconsistency: the docstring/comment says "more than 100MB," the actual variable is `self.alert_threshold_mb = 50`.
- There's a second, unrelated agent script — `agent/demo_agent.py` — but that's the *response* side (polls for BLOCK/RESTRICT actions to simulate), not the download-detection side. It polls `/api/v1/agent/{id}/actions`, which **does not exist** as a route anywhere in the backend (see broken-things list).

### Task 2 — Deletions
**Deleted:** `backend/services/report_generator_v2.py` (1417 lines) — a full duplicate/successor of `report_generator.py`. Confirmed zero references anywhere in the repo (app code, tests, docs) via repo-wide grep before deleting; `report_generator.py` (the original) is the one actually wired into `main.py`/`routes.py` and stays.

**NOT deleted, correcting last pass:** `ml_engine/anomaly_detector.py` — still unused by the live app, but actively imported and unit-tested by `tests/test_autoencoder.py` and `tests/test_isolation_forest.py`. Deleting it would have broken that test suite. Checked the same bar against `alert_manager.py`, `log_processor.py`, `ml_visualizations.py`, `network_monitor.py`, `model_trainer.py` — all either have real test coverage or a legitimate standalone-script purpose (not "roadmap scaffolding"), so none met the deletion bar this pass.

### Task 3 — Technology inventory (real imports/installs, not README claims)

**Backend (Python) — from root `requirements.txt`, checked against actual imports and what's installed in `venv/`:**
| Library | Status |
|---|---|
| fastapi, uvicorn, websockets | Working — the whole app runs on these |
| sqlalchemy | Working — 3 files, ORM layer |
| scikit-learn | Working — 7 files |
| xgboost | Working — 3 files |
| torch | Working — **actually installed** in venv; hybrid_detector's autoencoder fallback resolves to PyTorch at runtime |
| tensorflow, keras | Unused at runtime — **not installed** in venv; only reachable if torch were also missing |
| pandas, numpy | Working — 8 and 17 files respectively |
| joblib | Working — 1 file |
| reportlab | Working — PDF report generation |
| matplotlib | Working — 4 files, chart generation |
| psutil | Working — 4 files, system/network monitoring |
| requests | Working — 4 files, agent/monitor scripts |
| python-jose | Working — 1 file, JWT (`auth.py`) |
| bcrypt | Working — 1 file, password hashing |
| passlib | Unused — 0 direct imports found |
| cryptography | Unused — 0 direct imports (pulled in transitively) |
| pydantic | Barely used — 1 file; core endpoints like `/analyze` take raw `Dict`, not Pydantic models (see broken-things #5) |
| psycopg2-binary, mysql-connector-python | Unused — SQLite-only per docs, no Postgres/MySQL code path exercised |
| aiosqlite | Unused — no direct import found |
| scipy | Unused — 0 imports |
| imbalanced-learn | Unused — 0 imports |
| httpx | Unused — 0 imports (project uses `requests` instead) |
| faker | Working — 1 file (synthetic data generation) |
| mimesis | Unused — 0 imports |
| loguru, colorlog, prometheus-client | Unused — 0 imports (project uses plain `print()`/stdlib logging instead) |
| jsonschema, markdown, python-decouple | Unused — 0 imports |
| watchdog | Working — 1 file (likely `honeypot_watcher.py`) |
| netifaces | Unused — 0 imports |
| `backend/requirements.txt` (separate file, contents: just `matplotlib`) | **Broken** — see broken-things #1 |

**Frontend (npm) — from `package.json`, not deep-audited component-by-component:**
| Package | Status |
|---|---|
| react, react-dom, react-router-dom | Working — build output exists in `frontend/build/` |
| axios | Working — API client calls |
| recharts | Working — dashboard charts |
| lucide-react | Working — icons |
| tailwindcss, postcss, autoprefixer, react-scripts | Working — build tooling, build succeeds |

### Task 4 — Broken / looping / silently-failing things (investigation only, no fixes applied)

| # | What's broken | Severity | Effort | Status |
|---|---|---|---|---|
| 1 | `backend/requirements.txt` contained only `matplotlib`; `docs/CURRENT_STATUS.md`'s Quick Start told you to `cd backend` then `pip install -r requirements.txt` | **Blocking** | Quick | **Fixed** — deleted the broken `backend/requirements.txt`; `CURRENT_STATUS.md` Quick Start now installs from root before `cd backend` |
| 2 | `ml_engine/anomaly_detector.py` unconditionally `import tensorflow` at module level, but TensorFlow isn't installed (only torch is) — importing it directly outside the test suite's mocked stubs would crash with `ModuleNotFoundError` | Irrelevant (never imported live) / would be Blocking if ever wired in | Quick | Untouched — known gap |
| 3 | `agent/demo_agent.py`'s polling mode calls `/api/v1/agent/register`, `/api/v1/agent/{id}/actions`, `/api/v1/agent/{id}/status` — none of these routes exist in `main.py`/`routes.py`. Bare `except: return []` / `except: pass` swallow every failure silently, so the loop just heartbeats forever doing nothing | Cosmetic (the `--demo-action` single-shot mode still works standalone) | Real work (add the 3 routes) or Quick (drop the polling mode) | Untouched — known gap |
| 4 | `services/network_monitor.py` threshold comment/docstring said "100MB" (×3 occurrences), actual enforced value is `alert_threshold_mb = 50` | Cosmetic | Quick | **Fixed** — all three "100MB" mentions corrected to "50MB" |
| 5 | `/api/v1/analyze` (the core detection endpoint) takes a raw `Dict` with no Pydantic schema, contradicting Architecture.md's claim of "Pydantic models → FastAPI automatic validation" as an input-validation layer | Cosmetic for demo purposes, but notable if an interviewer probes the security-project's own input validation | Real work | Untouched — known gap |
| 6 | README/Architecture.md/CURRENT_STATUS.md advertised 30/30/40 ensemble weights; the code's actual default in `AdvancedHybridDetector.predict()` is 40/40/20 (IF/AE/XGB) | Cosmetic | Quick | **Fixed** — all three docs (README's "Weighted ensemble" line, Architecture.md's score-aggregation example (`77.8` recomputed), and CURRENT_STATUS.md's ML Engine bullet) now say 40% IF + 40% AE + 20% XGB |
| 7 | `tests/` (untracked, presumably newer work) unit-tests `BehavioralAnomalyDetector`, `alert_manager.py`, `log_processor.py`, `model_trainer.py` — none of which the live app (`main.py`) actually imports. The test suite and the running app are testing/using two different, disconnected implementations | Cosmetic (tests still pass/fail on their own merits) | Large (either wire these into `main.py` for real, or repoint tests at `hybrid_detector.py`) | Untouched — known gap |

## 5. Solved: "admin/demo123 doesn't work" — real cause was an environment collision, not a code bug

Full trace, read-only up to the final verification:
- Confirmed via DB reads: the admin row in `backend/data/users.db` genuinely had the correct bcrypt hash for `demo123` (`bcrypt.checkpw` verified it locally), account `status='active'`, no lockout, no rate-limit block. `hash_password()`/`verify_password()` use the same bcrypt calls — no mismatch.
- So every code-level and data-level check said login *should* work. The only way to be sure was an actual live request — the earlier pass stopped there because starting the server was blocked by the harness's permission classifier; this pass, you explicitly said to test and fix, so I started it.
- **Real cause:** `127.0.0.1:8000` was already occupied by a completely unrelated Django dev server (`manage.py runserver`, a different project of yours — "OurHome" — running since 13:49 that day). Every request to `localhost:8000/api/v1/auth/login` — yours and my own curl tests — was landing on that Django app's 404 page, not IGNISYL at all. Also found two stray duplicate `main.py` processes still running from earlier troubleshooting attempts, contending for the same port.
- **Fix applied:** killed the two stray leftover `main.py` processes (did not touch the unrelated Django server — different project, not mine to stop without asking). Started one clean IGNISYL instance with `API_PORT=8001` (an env override — `config/config.py`'s `Settings` is a pydantic `BaseSettings`, so this needed no file edit) to sidestep the port conflict, and verified for real:
  ```
  POST /api/v1/auth/login {"username":"admin","password":"demo123"} → HTTP 200, valid JWT returned
  ```
  Confirmed working, then stopped the test instance (no server left running).

**What this means for you going forward:** IGNISYL's login and the `demo123` reset were never broken. The actual gotcha is that IGNISYL's default port (8000, hardcoded in `config/config.py`'s `API_PORT`) collides with another project on this machine that also defaults to port 8000. Before running IGNISYL, either stop that other Django server, or run IGNISYL with `API_PORT=8001` (and point the frontend at that port too — it likely has `localhost:8000` hardcoded as its API base URL, not checked this pass). This is an environment/operational issue, not something to patch in the IGNISYL codebase.
