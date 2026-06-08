# Story: US-019 — Model Settings Configuration

**Lane:** normal
**Status:** done
**Created:** 2026-06-08

## Context

User wants to be able to configure LLM providers (Cliproxy, OpenAI, Google Gemini) via a Settings screen in the Admin Panel to dynamically change the models used for disease detection.

Affected files:
- [models.py](file:///mnt/nvme/leaf/backend/app/database/models.py)
- [admin.py](file:///mnt/nvme/leaf/backend/app/routers/admin.py)
- [vlm.py](file:///mnt/nvme/leaf/backend/app/models/vlm.py)
- [prediction.py](file:///mnt/nvme/leaf/backend/app/routers/prediction.py)
- [AdminView.jsx](file:///mnt/nvme/leaf/frontend/src/AdminView.jsx)

## Acceptance Criteria

- [x] New `Setting` database model created.
- [x] Endpoints `GET /api/v1/admin/settings` and `PUT /api/v1/admin/settings` implemented.
- [x] LLM API Key is masked in the GET response, and PUT preserves masked key values.
- [x] `predict_vlm` reads settings from database and supports Cliproxy, OpenAI, and Gemini (via native generateContent).
- [x] A settings page is added to the Admin Panel in frontend to configure the model details.

## Validation

| Type | Status | Command |
|---|---|---|
| Unit | ⬜ | N/A |
| Integration | ⬜ | Manual verification of API endpoints and VLM calls |
| E2E | ⬜ | Manual testing of Model Settings save and prediction |

## Files Changed

- `backend/app/database/models.py` — Added Setting model
- `backend/app/routers/admin.py` — Settings GET/PUT APIs
- `backend/app/models/vlm.py` — Refactor VLM logic with dynamic config
- `backend/app/routers/prediction.py` — Pass db session to predict_vlm
- `frontend/src/AdminView.jsx` — Add Model Settings tab & form

## Notes

None.
