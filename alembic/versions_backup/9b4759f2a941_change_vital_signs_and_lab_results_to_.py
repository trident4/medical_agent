"""Change vital_signs and lab_results to JSONB

Revision ID: 9b4759f2a941
Revises: 319350275b77
Create Date: 2025-11-16 14:57:48.814408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9b4759f2a941'
down_revision: Union[str, None] = '319350275b77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade: Change vital_signs and lab_results columns to JSONB.

    HIPAA Compliance: Ensures proper storage of medical data structures.
    """
    # Alter columns to JSONB with explicit casting for existing data
    op.alter_column(
        'visits',
        'vital_signs',
        type_=postgresql.JSONB,
        existing_type=sa.Text(),
        nullable=True,
        postgresql_using='vital_signs::jsonb'
    )
    op.alter_column(
        'visits',
        'lab_results',
        type_=postgresql.JSONB,
        existing_type=sa.Text(),
        nullable=True,
        postgresql_using='lab_results::jsonb'
    )


def downgrade() -> None:
    """
    Downgrade: Revert vital_signs and lab_results columns to TEXT.

    HIPAA Compliance: Maintains data integrity during schema changes.
    """
    # Revert columns back to TEXT with explicit casting
    op.alter_column(
        'visits',
        'vital_signs',
        type_=sa.Text(),
        existing_type=postgresql.JSONB,
        nullable=True,
        postgresql_using='vital_signs::text'
    )
    op.alter_column(
        'visits',
        'lab_results',
        type_=sa.Text(),
        existing_type=postgresql.JSONB,
        nullable=True,
        postgresql_using='lab_results::text'
    )
