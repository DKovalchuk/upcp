# TASK-0167 — Public GitHub export: release-mirror workflow + pre-publish hygiene

**Source:** Дмитрий 2026-11-01: «Я хочу выложить код проекта в паблик в моем
GitHub... цель — портфолио... давай определяться, что надо сделать». Решения
согласованы на сессии 2026-11-01.
**Milestone:** infra/processes (не релизный)
**Spec:** mini-spec (Gherkin ниже)
**Points:** 5
**Status:** IN PROGRESS

## Context

UPCP публикуется как публичная репа **DKovalchuk/upcp** (portfolio: архитектор,
лид агентов, разработчик). Согласованные решения:

- **GitLab остаётся source of truth**; GitHub — release-mirror. Публикуется
  **только `main`**: мерж develop→main + собранные docker-образы → push в
  публичную репу, автоматом как CI-job `publish:github`.
- **Полная, но вычищенная история при каждом экспорте**: mirror-clone →
  детерминированный `git filter-repo --replace-text` → gitleaks-гейт → push.
  Локальный репозиторий и история GitLab не переписываются.
- **MIT**; portfolio README EN/RU с навигацией; **базовый GitHub Actions CI**
  (backend/frontend lint+tests) для зелёного бейджа.
- Мерж develop→main — отдельным решением Дмитрия после ревью; эта задача
  только настраивает инфраструктуру и процессы. Первый seed публикует
  **текущий** `main` (2026-08-17).

Результаты аудита секретов (gitleaks 8.30.1, 2026-11-01): 15 находок в
истории; живые в HEAD — хардкод `UPCP_SECRET_KEY` в `.env.stage:4` и
`docker-compose.stage.yml:54`, протухшие локальные JWT в
`tests/security/reports/security_*.md` и `tests/security/results/authz_*`.
`.env`, `.qwen/settings.json` (локальный GitLab PAT), `tests/e2e/.auth/` —
не отслеживаются и в историю не попадали. Исторические находки в
`docs/agent/agent-onboarding.md` — фикстурные примеры (`upcp_agt_a1b2c3d4e5f6...`),
не секреты → baseline гейта, не scrub. Фикстуры `test_llm_redaction.py` и
fuzz-теста намеренно фейковые → `gitleaks:allow`/baseline.

## Goals

1. Вычистить секреты в HEAD (interpolation вместо хардкода, untrack
   `.env.stage`, redact JWT в отчётах) — с падающими сначала
   контракт-тестами (red→green).
2. LICENSE (MIT) + portfolio README.md (EN) / README.ru.md (RU) с
   двусторонней навигацией.
3. `scripts/export-public.sh`: mirror → filter-repo scrub → gitleaks-гейт →
   push; детерминированный, smoke-прогнанный на локальном toy-mirror.
4. CI-обвязка: job `publish:github` (main-only, после build) в
   `.gitlab-ci.yml` + `.github/workflows/ci.yml` (lint+test).
5. Ноль регрессий: ruff/mypy/pytest зелёные, стеки запускаются.

## Gherkin (mini-spec)

```gherkin
Feature: Pre-publish hygiene — no live secrets in tracked files

  Scenario: stage compose uses interpolation, not a hardcoded secret
    Given the tracked file docker-compose.stage.yml
    When I inspect the app service environment
    Then UPCP_SECRET_KEY is interpolated as ${UPCP_SECRET_KEY:?<hint>}
    And no base64-looking literal value is present in the file

  Scenario: .env.stage is untracked, an example file is tracked
    Given a fresh clone of the repository
    When I list tracked files matching .env.stage
    Then it is absent from the index
    And .gitignore contains .env.stage
    And .env.stage.example is tracked and contains no valid secret value

  Scenario: security reports contain no JWT-shaped strings
    Given the tracked files under tests/security/reports/ and tests/security/results/
    When I apply the JWT pattern eyJ<...>.<...>.<...>
    Then there are no matches

  Scenario: stage stack refuses to start without a key (negative)
    Given an empty UPCP_SECRET_KEY
    When I run docker compose --env-file <env with empty key> config
    Then it fails with the interpolation hint, not with a runtime default

  Scenario: stage stack starts with a provided key (positive)
    Given .env.stage with a generated UPCP_SECRET_KEY
    When I run docker compose --env-file .env.stage config
    Then it succeeds

Feature: Export pipeline — scrubbed full history to GitHub

  Scenario: export scrubs literal secrets and JWTs from full history
    Given a mirror clone whose history contains the stage secret literal and report JWTs
    When scripts/export-public.sh runs the filter-repo stage
    Then neither pattern occurs anywhere in the exported history
    And a re-run produces identical commit hashes (deterministic)

  Scenario: gitleaks gate blocks unknown findings (negative)
    Given an exported history with a finding outside the baseline
    When the gitleaks gate runs
    Then the script exits non-zero and does not push

  Scenario: gate passes the audited baseline (positive)
    Given the exported history matching the committed baseline
    When the gitleaks gate runs
    Then it exits zero and the push proceeds

Feature: Public repo presentation

  Scenario: bilingual README with navigation
    Given the public repository root
    Then README.md (English) and README.ru.md (Russian) exist,
      cross-link each other, carry a table of contents and link [MIT](LICENSE)
    And no copyright/attribution lines are present in the READMEs

  Scenario: GitHub Actions badge CI
    Given .github/workflows/ci.yml
    Then the workflow is valid YAML and defines backend and frontend
      lint/test jobs triggered on push and pull_request
```

## Acceptance Criteria

- [ ] AC1 (hygiene): контракт-тесты red→green; `docker-compose.stage.yml` —
      только `${UPCP_SECRET_KEY:?...}`; `.env.stage` untracked + в
      `.gitignore`; `.env.stage.example` трекается; в
      `tests/security/reports|results` нет JWT-паттерна;
      `docker compose --env-file .env.stage config` проходит с ключом и
      падает с `:?`-подсказкой без него.
- [ ] AC2 (presentation): `LICENSE` (MIT) + `README.md` (EN) +
      `README.ru.md` (RU): TOC, стек, архитектура, метрики, quickstart,
      навигация EN↔RU, ссылка `[MIT](LICENSE)`, без копирайт-строк.
- [ ] AC3 (export): `scripts/export-public.sh` прогонен на toy-mirror:
      scrub литералов+JWT подтверждён поиском по всей истории,
      gitleaks-гейт с baseline (exit 0), повторный прогон даёт идентичные
      hash'и, `shellcheck` чист.
- [ ] AC4 (CI wiring): job `publish:github` — только `main`,
      `needs: [build:backend, build:frontend]`, читает
      `GITHUB_PUB_TOKEN`; `.github/workflows/ci.yml` — валидный YAML,
      backend+frontend lint/test jobs.
- [ ] AC5 (no regressions): `make lint typecheck test` зелёные;
      `docker compose --env-file .env.ci config --quiet` проходит;
      существующие стеки не сломаны; docs (deployment/mcp-setup) синхронизированы.

## Decomposition

| # | Item | Depends on |
|---|---|---|
| 1 | Contract tests (red) + scrub HEAD (compose, .env.stage untrack, JWT redact) | — |
| 2 | LICENSE + README EN/RU | — |
| 3 | `scripts/export-public.sh` + replace-text config + gitleaks baseline + smoke | 1 |
| 4 | `publish:github` job + `.github/workflows/ci.yml` | 3 |
| 5 | Docs sync + PROJECT_STATUS + evidence | 1–4 |

## Setup prerequisites (human, GitLab/GitHub side)

- [ ] Masked CI variable `UPCP_SECRET_KEY` в GitLab (Settings → CI/CD →
      Variables) — без неё `deploy:stage` будет fail-fast на `:?`.
- [ ] GitHub token с scopes `repo`+`workflow` → masked CI variable
      `GITHUB_PUB_TOKEN`.

## Verification

(заполняется по мере закрытия AC)
