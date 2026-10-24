import subprocess
import tempfile

from app.api.v1.gitread import router as gitread_router
from app.api.v1.projects import router as projects_router
from app.api.v1.structure import router as structure_router
from app.gitread.adapters import LocalGitAdapter
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _test_engine as _engine

# Shared engine/session from conftest (TASK-0112 engine dedup).
from tests.conftest import _TestSession as _Session


def _override():
    s = _Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _app() -> FastAPI:
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(structure_router, prefix="/api/v1")
    app.include_router(gitread_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override
    return app


def _pid(c: TestClient) -> str:
    return c.post("/api/v1/projects", json={"name": "P"}).json()["id"]


# ── GitProvider CRUD ──


def test_create_provider() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    resp = c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "local", "provider_type": "local", "url": "/tmp/repo"},
    )
    assert resp.status_code == 201
    assert resp.json()["provider_type"] == "local"


def test_get_provider() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    gid = c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "G", "provider_type": "local", "url": "/tmp"},
    ).json()["id"]
    resp = c.get(f"/api/v1/git-providers/{gid}")
    assert resp.status_code == 200


def test_list_providers() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "A", "provider_type": "local", "url": "/a"},
    )
    c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "B", "provider_type": "local", "url": "/b"},
    )
    assert len(c.get(f"/api/v1/projects/{pid}/git-providers").json()) == 2


def test_delete_provider() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    gid = c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "X", "provider_type": "local", "url": "/x"},
    ).json()["id"]
    assert c.delete(f"/api/v1/git-providers/{gid}").status_code == 204


# ── GitLink CRUD ──


def test_create_link() -> None:
    c = TestClient(_app())
    resp = c.post(
        "/api/v1/git-links",
        json={"entity_type": "task", "entity_id": "t1", "git_type": "branch", "git_id": "b1"},
    )
    assert resp.status_code == 201
    assert resp.json()["git_type"] == "branch"


def test_list_links() -> None:
    c = TestClient(_app())
    c.post(
        "/api/v1/git-links",
        json={"entity_type": "task", "entity_id": "t1", "git_type": "branch", "git_id": "b1"},
    )
    c.post(
        "/api/v1/git-links",
        json={"entity_type": "task", "entity_id": "t1", "git_type": "commit", "git_id": "c1"},
    )
    resp = c.get("/api/v1/git-links?entity_type=task&entity_id=t1")
    assert len(resp.json()) == 2


def test_delete_link() -> None:
    c = TestClient(_app())
    lid = c.post(
        "/api/v1/git-links",
        json={"entity_type": "task", "entity_id": "t1", "git_type": "branch", "git_id": "b1"},
    ).json()["id"]
    assert c.delete(f"/api/v1/git-links/{lid}").status_code == 204


# ── LocalGitAdapter ──


def _init_git_repo(path: str, branch: str = "main") -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=path,
        capture_output=True,
        check=True,
    )


def test_local_adapter_list_branches() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        _init_git_repo(tmpdir)
        adapter = LocalGitAdapter(tmpdir)
        branches = adapter.list_branches()
        assert len(branches) >= 1
        assert any(b.is_default for b in branches)


def test_local_adapter_get_commits() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        _init_git_repo(tmpdir)
        subprocess.run(
            ["git", "-C", tmpdir, "commit", "--allow-empty", "-m", "second"],
            capture_output=True,
            check=True,
        )
        adapter = LocalGitAdapter(tmpdir)
        commits = adapter.get_commits(limit=2)
        assert len(commits) == 2
        assert commits[0].message == "second"


# ── GitHubAdapter (unit tests with mocked httpx) ──


def test_github_adapter_init() -> None:
    from app.gitread.adapters import GitHubAdapter

    adapter = GitHubAdapter("owner", "repo", token="ghp_test")
    assert adapter._base == "https://api.github.com/repos/owner/repo"
    assert "Authorization" in adapter._headers


def test_github_adapter_init_no_token() -> None:
    from app.gitread.adapters import GitHubAdapter

    adapter = GitHubAdapter("owner", "repo")
    assert "Authorization" not in adapter._headers


# ── GitProvider PATCH ──


def test_update_provider_name() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    gid = c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "Original", "provider_type": "local", "url": "/tmp/repo"},
    ).json()["id"]
    resp = c.patch(f"/api/v1/git-providers/{gid}", json={"name": "Updated"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"
    assert data["provider_type"] == "local"
    assert data["url"] == "/tmp/repo"


def test_update_provider_url() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    gid = c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "Test", "provider_type": "local", "url": "/tmp/old"},
    ).json()["id"]
    resp = c.patch(f"/api/v1/git-providers/{gid}", json={"url": "/tmp/new"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == "/tmp/new"
    assert data["name"] == "Test"


def test_update_provider_all_fields() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    gid = c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "Old", "provider_type": "local", "url": "/tmp/old"},
    ).json()["id"]
    resp = c.patch(
        f"/api/v1/git-providers/{gid}",
        json={"name": "New", "provider_type": "github", "url": "https://github.com/test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New"
    assert data["provider_type"] == "github"
    assert data["url"] == "https://github.com/test"


def test_update_provider_not_found() -> None:
    c = TestClient(_app())
    resp = c.patch("/api/v1/git-providers/nonexistent", json={"name": "Test"})
    assert resp.status_code == 404


def test_update_provider_empty_body() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    gid = c.post(
        f"/api/v1/projects/{pid}/git-providers",
        json={"name": "Test", "provider_type": "local", "url": "/tmp"},
    ).json()["id"]
    resp = c.patch(f"/api/v1/git-providers/{gid}", json={})
    assert resp.status_code == 422
