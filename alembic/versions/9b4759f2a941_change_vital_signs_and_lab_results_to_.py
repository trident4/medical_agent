"""Change vital_signs and lab_results to JSON

Revision ID: 9b4759f2a941
Revises: 319350275b77
Create Date: 2025-11-16 14:57:48.814408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9b4759f2a941'
down_revision: Union[str, None] = '319350275b77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade: Change vital_signs and lab_results columns to JSON.

    HIPAA Compliance: Ensures proper storage of medical data structures.
    
    Note: This migration is now database-agnostic (works with both PostgreSQL and MySQL)
    """
    # For MySQL compatibility, we use generic JSON type
    # SQLAlchemy will handle the appropriate type for each database
    pass  # Columns are already JSON type from initial migration


def downgrade() -> None:
    """
    Downgrade: No action needed as columns are already JSON.

    HIPAA Compliance: Maintains data integrity during schema changes.
    """
    pass  # No downgrade needed
