# TASK-0109 — M18 S20.2: Settings Redesign

**Milestone:** M18
**Sprint:** S20.2
**Points:** 8
**Status:** IN PROGRESS
**Spec:** SPEC-0021, §S20.2

## Objective

Redesign the Settings page from a single flat view into a tabbed layout with 5 sections:
Profile, Notifications, Channels, Appearance, About.

## Acceptance Criteria

1. Settings page uses a tab navigation (not sidebar)
2. **Profile tab**: display user name, email (read-only for now, as identity is external)
3. **Notifications tab**: per-event-type toggle switches (task.status_changed, evidence.attached, review.completed, etc.), with a save button
4. **Channels tab**: list notification channels (email/webhook), create/edit/delete with test connection button
5. **Appearance tab**: theme toggle (existing light/dark mode)
6. **About tab**: version, API status, system health check
7. All tabs have proper ARIA attributes (role="tablist", role="tab", aria-selected, aria-controls)
8. Existing theme functionality preserved
9. All existing frontend tests pass + 10 new settings tests
10. TypeScript clean, pre-commit hooks pass

## Design Decisions

- Use Radix UI Tabs (already a dependency) for the tab component
- Profile tab is informational only for now (identity is handled by external auth)
- Notification preferences stored in localStorage (backend preference API is future work)
- Channels tab connects to existing M16 backend endpoints if available

## Files to Create/Modify

### Backend (minimal)
- `backend/app/api/v1/settings.py` — GET/PUT notification preferences, GET/POST/DELETE channels, GET /health

### Frontend
- `frontend/src/components/settings/SettingsPage.tsx` — rewrite with tabs
- `frontend/src/components/settings/ProfileTab.tsx` — new
- `frontend/src/components/settings/NotificationsTab.tsx` — new
- `frontend/src/components/settings/ChannelsTab.tsx` — new
- `frontend/src/components/settings/AppearanceTab.tsx` — new
- `frontend/src/components/settings/AboutTab.tsx` — new

### Tests
- `frontend/src/components/settings/__tests__/SettingsPage.test.tsx` — new
- `backend/tests/test_settings.py` — new

## Evidence Required

- [ ] Screenshot or description of each tab
- [ ] Frontend test output (266+ pass)
- [ ] Backend test output (690+ pass)
- [ ] tsc --noEmit clean
- [ ] Pre-commit hooks pass
