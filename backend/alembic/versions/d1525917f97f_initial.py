"""initial

Revision ID: d1525917f97f
Revises:
Create Date: 2026-07-24 15:33:14.388597

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "d1525917f97f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
