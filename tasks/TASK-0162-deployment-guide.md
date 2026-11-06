# TASK-0162 — Deployment guide (stage/prod): единый документ процедуры

**Source:** ROADMAP_UNIFIED «After M20» п.4 (production hardening), выделено
из TASK-0160 AC6 (2026-10-31)
**Milestone:** Production hardening
**Spec:** mini-spec (AC ниже)
**Points:** 3
**Status:** pending

## Goals

Собрать единую deployment-процедуру: сейчас знание размазано по
`.gitlab-ci.yml` (deploy-джобы, FLOAT_TAG), `docs/ops/docker-compose.md`,
`docs/ops/environments.md`, `docs/ops/ci-retention.md`,
`docs/security/secure-deployment.md` (checklist), инцидентным записям
(PROJECT_STATUS: deploy health probe, tag mismatch) — единого guide нет.

## Acceptance Criteria

- [ ] AC1: `docs/ops/deployment.md` создан: model тегов (`FLOAT_TAG`:
      `:dev` на develop, `:stage` на main; `UPCP_BACKEND_IMAGE`/
      `UPCP_FRONTEND_IMAGE`; registry `registry.gitlab.local:5050`),
      pipeline-путь develop→stage, health-probe логика (`docker compose
      exec app`, exit 1 + logs при провале), ручной деплой через compose
      (`--env-file .env.stage`), rollback (previous image tag), prereqs
      (env-файлы, ports `UPCP_PORT_*`, миграции `alembic upgrade head`).
- [ ] AC2: каждый шаг guide проверен против реального `.gitlab-ci.yml` и
      compose-файлов (сверка → инструкция не расходится с кодом CI);
      расхождения — фиксировать в задаче.
- [ ] AC3: guide связан из `docs/INDEX.md`; кросс-ссылки на
      `environments.md`, `docker-compose.md`, `ci-retention.md`,
      `secure-deployment.md`.
- [ ] AC4: `docker compose --env-file .env.stage config` (и dev) проходит —
      команды из guide валидны.

## Out of scope

- Изменение CI-джоб (только документирование; баги CI — отдельной задачей).

## Verification

_(заполняется: команды сверки, вывод compose config)_
