# TASK-0165 — Attention e2e strict-mode collision: section titles vs empty states

**Source:** инцидент 2026-10-31: schedule quality-gate пайплайн **#515**
(develop @ 185f1b8c, source=schedule) — `quality:gate` failed,
`RCs: e2e=0 e2e_fe=1 chaos=0 security=0 perf=0`
**Milestone:** CI/CD reliability (класс TASK-0159)
**Spec:** mini-spec (AC ниже)
**Points:** 2
**Status:** DONE (2026-10-31 — AC1-AC4 закрыты; инцидент #515 закрыт зелёным develop-гейтом #519)

## Investigation (2026-10-31, evidence — лог джобы 3935)

2 теста `frontend/e2e/dashboard.spec.ts` «Dashboard — Attention Sections»:

```
✘ dashboard.spec.ts:150 › open questions section shows pending clarifications
  Error: locator.scrollIntoViewIfNeeded: strict mode violation:
  getByText('Open Questions') resolved to 2 elements
✘ dashboard.spec.ts:157 › blocked tasks section shows blocked items
  (analogous: getByText('Blocked Tasks') → 2 elements)
```

Root cause: `getByText(str)` — case-insensitive substring; при пустой секции
заголовок CardTitle («Open Questions») и empty-state («No open questions»)
дают 2 совпадения. Секция пуста, когда моки attention не успевают/не
применяются (гонка регистрации) — spec-комментарий в первом тесте describe
сам предупреждает об этой ловушке, но 3 теста в том же describe написаны
без `exact: true`. На том же SHA 2026-10-25 (#514) гейт был зелёным →
данные/тайминг-зависимая флаки-уязвимость locator'а, не продукт-регрессия
(код фронта не менялся с 2026-10-25).

## Goals

1. Сделать attention-e2e детерминированными для обоих состояний секции
   (с данными / пустой) — unambiguous locators.
2. Закрепить empty-state поведение регрессионным тестом.

## Acceptance Criteria

- [x] AC1: все тесты attention (3 существующих + «shows Needs Attention
      section») используют card-scoped locator `attentionTitle()`
      (`[data-slot="card"] filter hasText` → `[data-slot="card-title"]` +
      `toContainText`) — валиден и с count-badge («Open Questions 2»), и с
      empty-state («No open questions»); чистый substring и чистый exact
      непригодны (обоснование в комментариях кода).
- [x] AC2: регрессионный тест «empty sections…»: секции принудительно пустые
      (beforeGoto-mock, LIFO поверх workflow-моков) → canary
      `getByText('Open Questions')` `toHaveCount(2)` пинит саму ловушку #515,
      `attentionTitle()` → ровно 1 заголовок, empty-state отображается.
- [x] AC3: локально `npx playwright test e2e/dashboard.spec.ts` → **16/16
      green (×2 прогона)**. Полный сьют локально: 24 failed — **23 из них
      воспроизводятся на baseline без правок** (comprehensive-ui требует
      живой backend; в CI с `VITE_API_URL` на app эти тесты зелёные — в #515
      падали только attention-тесты).
- [x] AC4: MR !100 pipeline **#518 success**; пост-merge develop **#519
      quality:gate success** — `RCs: e2e=0 e2e_fe=0 chaos=0 security=0
      perf=0`, `quality gate exit: 0` (job 3985, develop @ a958d9a) →
      инцидент #515 закрыт.

## Verification

- Red (CI, permanent): schedule pipeline **#515**, job `quality:gate`
  (3935): `RCs: e2e=0 e2e_fe=1 chaos=0 security=0 perf=0`; лог:
  `strict mode violation: getByText('Open Questions') resolved to 2 elements`
  (dashboard.spec.ts:150) и аналогично 'Blocked Tasks' (:157); «2 failed».
- Локальный red как есть невоспроизводим (гонка моков: секции успевают
  наполниться) — потому тест и был флаки-уязвим; trap закреплён
  canary-ассертом в новом тесте.
- Green: `npx playwright test e2e/dashboard.spec.ts` → 16 passed (21.7s),
  повторный прогон — 16 passed; baseline-stash прогоны подтвердили, что
  прочие локальные падения (comprehensive-ui ×23) существуют и без правок.
- Наблюдение: `EmptyState.title` рендерится как `<h3>`, а `CardTitle` как
  `<div>` — role-based locator неприменим (heading-роль у пустого
  состояния, а не у заголовка секции).
