# TASK-0116 — M20 S22.2: File Uploads for Evidence

**Milestone:** M20
**Sprint:** S22.2
**Points:** 8
**Spec:** SPEC-0023 §S22.2
**Status:** DUPLICATE — see `TASK-0116-m20-s22-2-file-uploads-evidence.md` (the real task file, Status: DONE). This file was auto-created by a6e49d5 and never used.

## Objective

Add file attachment support to evidence (currently URLs only).

## Acceptance Criteria

- [ ] `POST /api/v1/evidence/upload` accepts multipart form data
- [ ] Files stored in `data/uploads/` (local) with configurable S3 adapter for production
- [ ] File type whitelist: pdf, png, jpg, jpeg, gif, webp, txt, csv, json
- [ ] Size limit: 10MB per file
- [ ] Frontend: drag-and-drop upload zone in EvidenceTab
- [ ] Evidence model extended with `file_path`, `file_name`, `file_size` (nullable, for file attachments)
- [ ] Migration 0023_add_evidence_file_fields
- [ ] All existing tests still pass
- [ ] New tests: upload endpoint, file validation, storage adapter

## Technical Design

### Backend — Upload Endpoint

```python
# app/quality/router.py
@router.post("/evidence/upload")
async def upload_evidence_file(
    file: UploadFile,
    task_id: UUID = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    # Validate file type and size
    # Store via StorageAdapter
    # Create Evidence record with file metadata
    # Return Evidence response
```

### Storage Adapter

```python
# app/shared/storage.py
class StorageAdapter(Protocol):
    async def save(self, file: UploadFile, path: str) -> str: ...
    async def delete(self, path: str) -> None: ...

class LocalStorageAdapter:
    def __init__(self, base_dir: str = "data/uploads"): ...

class S3StorageAdapter:
    def __init__(self, bucket: str, region: str): ...
```

### Frontend — Upload Zone

Add drag-and-drop zone to `EvidenceTab` using native HTML5 drag events:

```tsx
<div
  onDrop={handleDrop}
  onDragOver={handleDragOver}
  className="border-2 border-dashed rounded-lg p-6 text-center"
>
  <p>Drop files here or click to browse</p>
  <input type="file" onChange={handleFileSelect} multiple />
</div>
```

### Evidence Model Extension

Add nullable columns to `evidence` table:

```python
file_path = Column(String, nullable=True)
file_name = Column(String, nullable=True)
file_size = Column(Integer, nullable=True)
```

URL-based evidence remains unchanged (file_path is null).
