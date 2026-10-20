# TODO — Project Improvement List

Prioritized, actionable items. Mark items complete as you finish them.

---

## 🔴 P0 — Must fix (bugs / broken behavior)

- [ ] **api.py hardcodes DB credentials** — line 12 uses `dwh_user:dwh_pass` instead of env vars. Fix to use `DB_USER`/`DB_PASS` like `main.py` does. Will break if credentials change.
- [ ] **review_content comma-splitting bug** — `etl/main.py:118-127` splits all review fields by comma. Review content often contains commas, which misaligns the parallel arrays (`user_ids`, `review_ids`, `review_content`). Fix by zipping instead of indexing, or using a delimiter that won't appear in content.
- [ ] **Add `.env.example`** — no env template exists. Create one showing all required vars for ETL + API.
- [ ] **Add `.dockerignore`** — prevents accidentally copying node_modules, .git, etc. into build context.

---

## 🟡 P1 — High value, quick wins

- [ ] **Add foreign keys** in `sql/init.sql`:
  - `fact_reviews.product_id → dwh.dim_product(product_id)`
  - `fact_reviews.user_id → dwh.dim_reviewer(user_id)`
- [ ] **Add `created_at`/`updated_at` timestamps** to all three tables for incremental loads and auditing.
- [ ] **Add env vars to api.py** — `DB_HOST`, `DB_PORT`, `DB_NAME` should all come from environment, not be hardcoded.
- [ ] **Add error + loading states** to the React UI (`App.jsx`) — currently silent failures if an API endpoint returns 500.
- [ ] **Render the most-reviewed chart** — data is fetched (`/api/most-reviewed`) but never displayed in the UI.
- [ ] **Use env var for API URL** in frontend — currently hardcoded `http://localhost:8000`. Add `.env` / vite config support.
- [ ] **Add health check endpoint** to FastAPI (`GET /health`) for Docker/orchestration.

---

## 🟢 P2 — Medium priority (robustness & DX)

- [ ] **Add unit tests** for cleaning functions in `etl/main.py`:
  - `clean_price` (₹1,099 → 1099.0, edge cases)
  - `clean_pct` (64% → 64.0)
  - `clean_count` (24,269 → 24269)
  - `clean_rating` (4,2 → 4.0 locale variant)
- [ ] **Add data validation** — reject/skip rows with missing `product_id` or `product_name` before DB insert.
- [ ] **Add logging** — use `logging` module with structured output instead of bare `print()`.
- [ ] **Add pagination** to list endpoints (`top-categories`, `top-rated-products`, etc.).
- [ ] **Use SQLAlchemy models** instead of raw SQL strings in `api.py` for maintainability.
- [ ] **Add product detail page** in frontend — click a product to see its reviews.
- [ ] **Add search & filtering** in frontend (category, price range, rating).
- [ ] **Add loading skeletons** for chart rendering.

---

## 🔵 P3 — Lower priority (production readiness)

- [ ] **Incremental ETL loads** — currently full reload each run. Use `updated_at` to load only changed rows.
- [ ] **Add CI pipeline** — GitHub Actions / GitLab CI: lint, build, test on push.
- [ ] **Use non-root user** in Dockerfile for security.
- [ ] **Add database backup strategy** — pg_dump cron or Docker volume snapshots.
- [ ] **Add structured logging (JSON)** and centralization (Loki / ELK).
- [ ] **Add rate limiting** to FastAPI.
- [ ] **Add authentication** (API key / JWT) to FastAPI.
- [ ] **Add materialized views** for slow KPI queries if data grows.
- [ ] **Add ETL job scheduler** — Airflow / Prefect / cron for recurring loads.
- [ ] **Add dark mode** and **mobile responsive design** to frontend.
- [ ] **Add TypeScript** to frontend for type safety.
- [ ] **Pin dependency hashes** in requirements (pip-compile / pip-tools).

---

## ✅ Quick win checklist (do these first)

1. Fix `api.py` env vars (10 min)
2. Create `.env.example` (5 min)
3. Create `.dockerignore` (2 min)
4. Add `GET /health` endpoint (10 min)
5. Add foreign keys to `init.sql` (5 min)
6. Render the most-reviewed chart in frontend (15 min)
7. Add loading/error states to frontend (20 min)