# TASK-0116 — M20 S22.2: File Uploads for Evidence

**Milestone:** M20
**Sprint:** S22.2
**Points:** 8
**Spec:** SPEC-0023 §S22.2
**Status:** DONE

## Objective

Add file attachment support to the Evidence system. Currently evidence supports URLs only.
This sprint adds multipart file upload with local filesystem storage.

## Acceptance Criteria

- [ ] `POST /api/v1/evidence/upload` accepts multipart form (file + metadata)
- [ ] Files stored in `data/uploads/` with UUID-based filenames
- [ ] File type whitelist enforced (images, PDFs, text, code files)
- [ ] File size limit: 10MB max
- [ ] Evidence model extended with `file_path`, `file_name`, `file_size`, `content_type` nullable fields
- [ ] Migration adds new columns to `evidence` table
- [ ] Frontend drag-and-drop upload zone in EvidenceTab
- [ ] Uploaded file downloadable via `GET /api/v1/evidence/{id}/download`
- [ ] All existing evidence tests still pass
- [ ] New upload tests: valid file, oversized, disallowed type, missing file, download

## Technical Design

### Backend

**New columns on `evidence` table:**
- `file_path` (String(512), nullable) — relative path in upload dir
- `file_name` (String(255), nullable) — original filename
- `file_size` (Integer, nullable) — bytes
- `content_type` (String(127), nullable) — MIME type

**New endpoint:** `POST /api/v1/evidence/upload`
- Form fields: `file` (UploadFile), `task_id`, `type`, `title`, `created_by_type`, `created_by_id`, optional `dod_item_id`
- Validates: whitelist, size ≤ 10MB
- Saves to `data/uploads/<uuid_hex>/<original_name>` (UUID prefix to avoid collisions)
- Creates Evidence record with file metadata + event_bus publish

**New endpoint:** `GET /api/v1/evidence/{evidence_id}/download`
- Returns file as StreamingResponse with correct content-type
- 404 if evidence has no file

**Migration:** 0021_add_evidence_file_fields

### Frontend

- Drag-and-drop zone in EvidenceTab using native HTML5 drag events
- File preview (thumbnail for images, icon for others)
- Upload progress indicator
- File type + size validation client-side

## Files to Create/Modify

- `backend/app/quality/models.py` — add file columns
- `backend/app/quality/service.py` — upload_file, download_file methods
- `backend/app/quality/schemas.py` — EvidenceUploadResponse
- `backend/app/api/v1/quality.py` — upload + download endpoints
- `backend/alembic/versions/0021_*.py` — migration
- `backend/app/shared/config.py` — UPLOAD_DIR, MAX_UPLOAD_SIZE
- `backend/tests/test_evidence_upload.py` — tests
- `frontend/src/components/project/EvidenceTab.tsx` — drag-and-drop UI
