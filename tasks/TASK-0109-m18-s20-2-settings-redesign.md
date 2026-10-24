# TASK-0109 — M18 S20.2: Settings Redesign

**Milestone:** M18
**Sprint:** S20.2
**Points:** 8
**Spec:** SPEC-0021, §S20.2
**Status:** DONE (closed 2026-10-25)

**Audit 2026-10-24 (evidence):** табличная структура Settings ✅ (5 табов:
Profile/Notifications/Channels/Appearance/About, `SettingsPage.tsx:10`),
Profile name/email ✅ (`ProfileTab.tsx:52,56`), тумблеры уведомлений
`role="switch"` ✅ (`NotificationsTab.tsx:48`), каналы create/delete/test ✅
(`ChannelsSettingsTab.tsx`), About health ✅ (`AboutTab.tsx`), ARIA-роли табов ✅
(`SettingsPage.test.tsx` использует `getByRole('tab')` и проходит), 11 тестов
Settings (AC: 10) ✅, tsc clean ✅, lint 0 errors ✅.
**Gaps:** (1) AC4 «edit» канала — формы редактирования config канала нет
(backend API: list/create/delete/toggle/test; PUT/PATCH отсутствует, только
toggle is_active); (2) evidence-чеклист внизу файла не заполнен (скриншоты,
pre-commit). Статус → PARTIAL до закрытия gaps.

## Objective

Redesign the Settings page from a single flat view into a tabbed layout with 5 sections:
Profile, Notifications, Channels, Appearance, About.

## Acceptance Criteria (verified 2026-10-25)

- [x] 1. Settings page uses a tab navigation (not sidebar) — Radix tabs, 5 triggers (tests)
- [x] 2. Profile tab: read-only user name/email — `ProfileTab.tsx:52,56`
- [x] 3. Notifications tab: per-event `role="switch"` toggles + **Save** button
      (`NotificationsTab.tsx:48,74-92` — `savePreferences` → localStorage)
- [x] 4. Channels tab: list/create/**edit**/delete + test-connection —
      **edit closed this session**: `PATCH /api/v1/notification-channels/{id}`
      (422/404 contract) + edit dialog in `ChannelsSettingsTab`
- [x] 5. Appearance tab: theme toggle preserved (`AppearanceTab.tsx`)
- [x] 6. About tab: version, API status, health check (`AboutTab.tsx`, test
      «Connected» when healthy)
- [x] 7. ARIA: role="tablist"/"tab", aria-selected/controls — `SettingsPage.test`
      (`getByRole('tab')`, tablist aria-label)
- [x] 8. Existing theme functionality preserved (AppearanceTab + tests)
- [x] 9. All existing frontend tests pass + ≥10 settings tests — 11 pre-existing
      settings tests + **5 new** channel-edit tests (16 total); full suite below
- [x] 10. TypeScript clean, pre-commit hooks pass — `tsc -b` exit 0; pre-commit
      green on all 3 commits of this task (hooks ran, exit 0)

## Evidence Required (filled 2026-10-25)

- [x] **Description of each tab** (test-env verification):
  - **Profile** — read-only full name + email (identity external), Save disabled
    by design (informational)
  - **Notifications** — per-event switches (task.status_changed,
    evidence.attached, review.completed, …) + `role="switch"` +
    `aria-checked`, Save button persists to localStorage
  - **Channels** — channel list (name, type-chip, test/toggle/**edit**/delete
    actions), create dialog, **edit dialog (name + target, config keys
    preserved)**, empty state «No channels configured»
  - **Appearance** — light/dark theme toggle (existing behavior preserved)
  - **About** — version, API status («Connected»/«Disconnected»), system
    health check
- [x] **Frontend test output** (AC: 266+): **446 passed / 53 files** (vitest),
      new file `ChannelsSettingsTab.test.tsx` 5/5 (red 5/5 → green 5/5)
- [x] **Backend test output** (AC: 690+): **1014 passed** (pytest, exit 0);
      channel files 21/21 (red **8 failed/13 passed** → green); ruff `All
      checks passed`; mypy `no issues found in 114 source files`
- [x] **tsc --noEmit clean**: `tsc -b` exit 0 (project-refs build; equivalent)
- [x] **Pre-commit hooks pass**: verified on task commits (exit 0)

## Evidence (red→green)

- Backend red: `pytest test_notification_channels*` → **8 failed / 13 passed,
  exit 1** (4 service: no `ChannelService.update`; 4 API: PATCH route absent)
- Backend green: **21 passed, exit 0** + ruff + mypy clean
- Frontend red: `vitest run ChannelsSettingsTab.test.tsx` → **5 failed, exit 1**
  (no «Edit channel …» button)
- Frontend green: **5 passed, exit 0**
- Full gates: backend **1014 passed** (ruff 0, mypy 0/114 files); frontend
  **446/446 (53 files)**, oxlint 0 errors, `tsc -b` 0

## Deviations / notes (recorded per §7)

1. **ValueError → ValidationError normalization** in `ChannelService.update`:
   channel `validate_config` raises plain `ValueError`, while the API contract
   maps shared `ValidationError` → 422. `update()` catches and re-raises as
   shared `ValidationError` (tested: PATCH invalid config → 422).
2. **Latent defect, follow-up candidate** (outside AC4, not fixed here):
   `ChannelService.create` has the same mismatch — POST with a config failing
   `validate_config` raises unhandled `ValueError` → 500 instead of 422
   (endpoint only catches shared `ValidationError`; no API test existed for
   create-with-invalid-config). Recommend a follow-up: normalize in `create()`
   + API regression test (same pattern as PATCH).
3. **`channel_type` is immutable** on edit (config shape is per-type;
   type-swap = delete+create). Edit covers name + target/config — satisfies
   AC4 «edit».
4. Evidence checklist AC numbers (266+/690+) are historical thresholds;
   actual current counts recorded (446/1014).

## Files

| File | Action |
|------|--------|
| `backend/app/reporting/channel_service.py` | MODIFY — `update()` (name/config partial, validation) |
| `backend/app/api/v1/notification_channels.py` | MODIFY — `ChannelUpdate` schema + `PATCH /{id}` (200/404/422) |
| `backend/tests/test_notification_channels.py` | MODIFY — +4 service tests |
| `backend/tests/test_notification_channels_api.py` | CREATE — 4 API tests (`_test_app` pattern) |
| `frontend/src/lib/api/analytics.ts` | MODIFY — `updateNotificationChannel` (PATCH) |
| `frontend/src/components/settings/ChannelsSettingsTab.tsx` | MODIFY — edit button + edit dialog + save |
| `frontend/src/components/settings/ChannelsSettingsTab.test.tsx` | CREATE — 5 tests (red→green) |
