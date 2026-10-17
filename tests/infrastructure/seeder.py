"""Test data seeder for UPCP test environment.

Generates realistic test data with configurable scale profiles.
Supports: small (x1), medium (x10), large (x100).

Usage:
    python -m tests.infrastructure.seeder
    python -m tests.infrastructure.seeder --profile medium
    python -m tests.infrastructure.seeder --clean
"""

from __future__ import annotations

import argparse
import logging
import os
import random
import string
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("seeder")

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


def _suffix(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _slugify(name: str) -> str:
    import re

    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


# ── Profile configurations ────────────────────────────────────

PROFILES = {
    "small": {
        "projects": 1,
        "components_per_project": 3,
        "modules_per_component": 4,
        "features_per_project": 6,
        "tasks_per_feature": 3,
        "agents": 3,
    },
    "medium": {
        "projects": 10,
        "components_per_project": 5,
        "modules_per_component": 6,
        "features_per_project": 10,
        "tasks_per_feature": 5,
        "agents": 20,
    },
    "large": {
        "projects": 100,
        "components_per_project": 8,
        "modules_per_component": 10,
        "features_per_project": 15,
        "tasks_per_feature": 7,
        "agents": 100,
    },
}

TASK_STATUSES = ["backlog", "in_progress", "review", "done"]
TASK_PRIORITIES = [0, 1, 2, 3]


class Seeder:
    def __init__(self, profile: str = "small"):
        self.profile = PROFILES[profile]
        self.profile_name = profile
        self.stats: dict[str, int] = {}

    def run(self, clean: bool = True) -> None:
        from app.shared.database import SessionLocal, engine
        from sqlalchemy import text

        logger.info("Starting seeder — profile=%s, clean=%s", self.profile_name, clean)

        if clean:
            logger.info("Dropping and recreating all tables...")
            with engine.begin() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
            # Run migrations
            import subprocess

            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
            )
            if result.returncode != 0:
                logger.error("Alembic migration failed: %s", result.stderr)
                return
            logger.info("Migrations applied successfully")

        start_time = time.perf_counter()

        with SessionLocal() as session:
            self._seed_projects(session)
            self._seed_agents(session)
            session.commit()

        elapsed = time.perf_counter() - start_time
        self._print_stats(elapsed)

    def _seed_projects(self, session) -> None:
        from app.delivery.models import Feature, Task
        from app.projects.models import Project
        from app.structure.models import Component, Module

        p = self.profile
        total_tasks = 0

        for pi in range(p["projects"]):
            project = Project(
                name=f"Test Project {_suffix()}",
                slug=f"test-project-{_suffix()}",
                description=f"Auto-generated test project #{pi + 1} for {self.profile_name} profile",
                status="active",
            )
            session.add(project)
            session.flush()
            self.stats["projects"] = self.stats.get("projects", 0) + 1

            component_ids = []
            for _ci in range(p["components_per_project"]):
                comp = Component(
                    project_id=project.id,
                    name=f"Component {_suffix()}",
                    slug=f"comp-{_suffix()}",
                    description="Auto-generated component",
                    status="active",
                )
                session.add(comp)
                session.flush()
                component_ids.append(comp.id)
                self.stats["components"] = self.stats.get("components", 0) + 1

                for _mi in range(p["modules_per_component"]):
                    mod = Module(
                        component_id=comp.id,
                        name=f"Module {_suffix()}",
                        slug=f"mod-{_suffix()}",
                        description="Auto-generated module",
                        status="active",
                    )
                    session.add(mod)
                    self.stats["modules"] = self.stats.get("modules", 0) + 1

            feature_ids = []
            for _fi in range(p["features_per_project"]):
                comp_id = random.choice(component_ids) if component_ids else None
                feat = Feature(
                    project_id=project.id,
                    component_id=comp_id,
                    name=f"Feature {_suffix()}",
                    slug=f"feat-{_suffix()}",
                    description="Auto-generated feature",
                    status=random.choice(["backlog", "in_progress", "done"]),
                )
                session.add(feat)
                session.flush()
                feature_ids.append(feat.id)
                self.stats["features"] = self.stats.get("features", 0) + 1

                for _ti in range(p["tasks_per_feature"]):
                    task_comp = random.choice(component_ids) if component_ids else None
                    task = Task(
                        feature_id=feat.id,
                        component_id=task_comp,
                        title=f"Task {_suffix()}",
                        description="Auto-generated task",
                        status=random.choice(TASK_STATUSES),
                        priority=random.choice(TASK_PRIORITIES),
                    )
                    session.add(task)
                    total_tasks += 1

            self.stats["tasks"] = total_tasks
            if (pi + 1) % 10 == 0 or pi == p["projects"] - 1:
                logger.info(
                    "  Projects: %d/%d, Tasks: %d",
                    pi + 1,
                    p["projects"],
                    total_tasks,
                )

        session.flush()

    def _seed_agents(self, session) -> None:
        from app.identity.models import Membership, Organization, User

        p = self.profile

        # Create default org
        org = Organization(name="Test Org", slug=f"test-org-{_suffix()}", is_default=True)
        session.add(org)
        session.flush()
        self.stats["organizations"] = 1

        # Create admin user — pyca bcrypt, same as app.identity.service
        # (passlib 1.7.4 crashes with bcrypt>=4.1: its internal wrap-bug
        # self-test expects silent truncation, modern bcrypt raises).
        import bcrypt

        admin = User(
            # Fixed identity for perf scenarios (common.py). Must pass
            # pydantic EmailStr on login — reserved TLDs (.local/.test)
            # are rejected as special-use addresses.
            email="admin@example.com",
            password_hash=bcrypt.hashpw(b"TestAdmin123!", bcrypt.gensalt(rounds=12)).decode(),
            display_name="Test Admin",
            is_active=True,
            is_superuser=True,
            email_verified=True,
        )
        session.add(admin)
        session.flush()

        membership = Membership(user_id=admin.id, org_id=org.id, role="owner")
        session.add(membership)
        self.stats["users"] = 1
        self.stats["memberships"] = 1

        # Create agent users
        for _ai in range(p["agents"]):
            agent_user = User(
                email=f"agent-{_suffix()}@test.local",
                password_hash=bcrypt.hashpw(b"TestAgent123!", bcrypt.gensalt(rounds=12)).decode(),
                display_name=f"Agent {_suffix(4)}",
                is_active=True,
                is_superuser=False,
                email_verified=True,
            )
            session.add(agent_user)
            # Flush so the client-side id default fires — otherwise
            # agent_user.id is None and membership.user_id violates NOT NULL
            # (same pattern as the admin block above).
            session.flush()
            membership = Membership(user_id=agent_user.id, org_id=org.id, role="member")
            session.add(membership)

        self.stats["agents"] = p["agents"]
        self.stats["users"] += p["agents"]
        self.stats["memberships"] += p["agents"]
        logger.info("  Agents created: %d", p["agents"])

    def _print_stats(self, elapsed: float) -> None:
        logger.info("=" * 60)
        logger.info("SEED COMPLETE — Profile: %s", self.profile_name)
        logger.info("=" * 60)
        for entity, count in sorted(self.stats.items()):
            logger.info("  %-20s %d", entity + ":", count)
        total = sum(self.stats.values())
        logger.info("  %-20s %d", "TOTAL:", total)
        logger.info("  %-20s %.2fs", "TIME:", elapsed)
        logger.info("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="UPCP test data seeder")
    parser.add_argument(
        "--profile",
        choices=["small", "medium", "large"],
        default="small",
        help="Data volume profile (default: small)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=True,
        help="Drop and recreate DB before seeding (default: true)",
    )
    parser.add_argument(
        "--no-clean",
        dest="clean",
        action="store_false",
        help="Skip DB cleanup, seed on top of existing data",
    )
    args = parser.parse_args()

    seeder = Seeder(profile=args.profile)
    seeder.run(clean=args.clean)


if __name__ == "__main__":
    main()
