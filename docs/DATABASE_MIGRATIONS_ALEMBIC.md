# Database Migrations with Alembic - Complete Guide

A comprehensive guide to understanding and managing database schema changes in the Medical Assistant project.

---

## Table of Contents

1. [What Are Database Migrations?](#what-are-database-migrations)
2. [Why We Need Alembic](#why-we-need-alembic)
3. [How Alembic Works](#how-alembic-works)
4. [Project Setup](#project-setup)
5. [Creating Migrations](#creating-migrations)
6. [Running Migrations](#running-migrations)
7. [Common Migration Scenarios](#common-migration-scenarios)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Topics](#advanced-topics)

---

## What Are Database Migrations?

### The Problem

Imagine you're building your medical assistant app:

**Week 1:** You create a `patients` table:

```sql
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR,
    name VARCHAR,
    date_of_birth DATE
);
```

**Week 3:** You need to add email and phone:

```sql
-- How do you add these without losing existing data?
ALTER TABLE patients ADD COLUMN email VARCHAR;
ALTER TABLE patients ADD COLUMN phone VARCHAR;
```

**Week 5:** You realize you need to split name into first/last:

```sql
-- How do you migrate existing data?
ALTER TABLE patients ADD COLUMN first_name VARCHAR;
ALTER TABLE patients ADD COLUMN last_name VARCHAR;
-- What about the existing 'name' column data?
```

**The Challenge:**

- 🤔 How to track what changes were made?
- 🤔 How to apply changes to production database?
- 🤔 How to rollback if something breaks?
- 🤔 How to keep team members' databases in sync?
- 🤔 How to migrate existing data safely?

### The Solution: Database Migrations

**Database Migrations = Version Control for Your Database Schema**

Just like Git tracks code changes, migrations track database changes:

```
Migration 001: Create patients table
Migration 002: Add email and phone columns
Migration 003: Split name into first_name and last_name
Migration 004: Create visits table
Migration 005: Add vital_signs column to visits
```

Each migration is:

- ✅ **Versioned** - Has a unique identifier
- ✅ **Reversible** - Can be applied (upgrade) or rolled back (downgrade)
- ✅ **Documented** - Shows what changed and why
- ✅ **Reproducible** - Can be applied to any database

---

## Why We Need Alembic

### What is Alembic?

**Alembic** is a database migration tool for SQLAlchemy (Python ORM).

Think of it as **Git for your database schema**:

| Git               | Alembic                       |
| ----------------- | ----------------------------- |
| `git commit`      | `alembic revision`            |
| `git push`        | `alembic upgrade`             |
| `git revert`      | `alembic downgrade`           |
| `git log`         | `alembic history`             |
| `.git/` directory | `alembic/versions/` directory |

### Benefits of Alembic

1. **Automatic Migration Generation**

   ```bash
   # Alembic compares your models with the database
   # and generates migration automatically
   alembic revision --autogenerate -m "Add email column"
   ```

2. **Safe Schema Changes**

   ```python
   # Alembic ensures changes happen in correct order
   # and handles dependencies automatically
   ```

3. **Team Collaboration**

   ```bash
   # Team member pulls your code
   git pull

   # Applies your database changes automatically
   alembic upgrade head
   ```

4. **Production Deployment**

   ```bash
   # Deploy to production
   git pull
   alembic upgrade head  # Safe, versioned updates
   ```

5. **Disaster Recovery**
   ```bash
   # Something broke? Rollback!
   alembic downgrade -1  # Go back one version
   ```

---

## How Alembic Works

### Architecture Overview

```
┌─────────────────────────────────────────┐
│      Your SQLAlchemy Models             │
│   (app/models/patient.py, etc.)         │
└──────────────┬──────────────────────────┘
               │
               │ Alembic compares
               ↓
┌──────────────────────────────────────────┐
│      Current Database Schema             │
│      (PostgreSQL tables)                 │
└──────────────┬──────────────────────────┘
               │
               │ Generates diff
               ↓
┌──────────────────────────────────────────┐
│      Migration File                      │
│   (alembic/versions/xxx_add_email.py)    │
│   - upgrade() - Apply changes            │
│   - downgrade() - Revert changes         │
└──────────────────────────────────────────┘
```

### Migration Lifecycle

```
1. Define Models (SQLAlchemy)
   ↓
2. Generate Migration (alembic revision --autogenerate)
   ↓
3. Review Migration (check generated SQL)
   ↓
4. Apply Migration (alembic upgrade head)
   ↓
5. Database Updated ✅
```

### Version Tracking

Alembic maintains a special table in your database:

```sql
-- alembic_version table
CREATE TABLE alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);

-- Example data
SELECT * FROM alembic_version;
-- version_num
-- 'abc123def456'  ← Current migration version
```

This table tells Alembic:

- What version the database is currently at
- Which migrations have been applied
- Which migrations still need to be applied

---

## Project Setup

### 1. Installation

```bash
# Install Alembic
pip install alembic

# Or if using poetry
poetry add alembic
```

### 2. Initialize Alembic

```bash
# Initialize Alembic in your project
alembic init alembic

# This creates:
# alembic/                  ← Migration directory
#   ├── versions/           ← Individual migration files go here
#   ├── env.py              ← Alembic environment config
#   ├── script.py.mako      ← Template for new migrations
#   └── README
# alembic.ini               ← Alembic configuration file
```

### 3. Configure Alembic

**File: `alembic.ini`**

```ini
# filepath: alembic.ini

# Database connection string
# Don't hardcode credentials! Use environment variables
sqlalchemy.url = postgresql://user:password@localhost/medical_assistant

# Or better, leave blank and set in env.py
# sqlalchemy.url =

# Migration file format
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# Logging
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

**File: `alembic/env.py`**

```python
# filepath: alembic/env.py
"""
Alembic environment configuration.
This file is run whenever alembic is invoked.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add your project to the path so we can import models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your application's base and models
from app.database.base import Base
from app.models.patient import Patient
from app.models.visit import Visit
# Import all models so Alembic can detect them

# Get database URL from environment variable (secure!)
from app.config import settings

# This is the Alembic Config object
config = context.config

# Override sqlalchemy.url with environment variable
config.set_main_option('sqlalchemy.url', str(settings.DATABASE_URL))

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata from your Base
# This is how Alembic knows about your models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Important: Include schema if you use multiple schemas
            # include_schemas=True,

            # Compare types to detect column type changes
            compare_type=True,

            # Compare server defaults
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Key Configuration Points:**

1. **Import All Models**: Must import all SQLAlchemy models so Alembic can detect them
2. **Set target_metadata**: Points to your Base.metadata
3. **Database URL**: Load from environment variable (secure)
4. **Compare Options**: Enable type and default comparison

---

## Creating Migrations

### Automatic Migration Generation (Recommended)

**Step 1: Modify Your Models**

```python
# filepath: app/models/patient.py
from sqlalchemy import Column, Integer, String, Date, Text

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)

    # Add new columns
    first_name = Column(String, nullable=False)  # ← NEW
    last_name = Column(String, nullable=False)   # ← NEW
    email = Column(String, unique=True)          # ← NEW
    phone = Column(String)                       # ← NEW

    date_of_birth = Column(Date, nullable=False)
    gender = Column(String)
```

**Step 2: Generate Migration**

```bash
# Alembic will detect the changes automatically
alembic revision --autogenerate -m "Add patient contact information"

# Output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.ddl.postgresql] Detected added column 'patients.first_name'
# INFO  [alembic.ddl.postgresql] Detected added column 'patients.last_name'
# INFO  [alembic.ddl.postgresql] Detected added column 'patients.email'
# INFO  [alembic.ddl.postgresql] Detected added column 'patients.phone'
# Generating /path/to/alembic/versions/20251108_1430_abc123_add_patient_contact_information.py
```

**Step 3: Review Generated Migration**

```python
# filepath: alembic/versions/20251108_1430_abc123_add_patient_contact_information.py
"""Add patient contact information

Revision ID: abc123def456
Revises: previous_revision_id
Create Date: 2025-11-08 14:30:00.123456
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision: str = 'abc123def456'
down_revision: Union[str, None] = 'previous_revision_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema - apply changes."""
    # Add new columns
    op.add_column('patients', sa.Column('first_name', sa.String(), nullable=False))
    op.add_column('patients', sa.Column('last_name', sa.String(), nullable=False))
    op.add_column('patients', sa.Column('email', sa.String(), nullable=True))
    op.add_column('patients', sa.Column('phone', sa.String(), nullable=True))

    # Create unique index on email
    op.create_index('ix_patients_email', 'patients', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade database schema - revert changes."""
    # Remove in reverse order
    op.drop_index('ix_patients_email', table_name='patients')
    op.drop_column('patients', 'phone')
    op.drop_column('patients', 'email')
    op.drop_column('patients', 'last_name')
    op.drop_column('patients', 'first_name')
```

**Important**: Always review auto-generated migrations! Sometimes they need manual adjustments.

### Manual Migration Creation

For complex changes, create migrations manually:

```bash
# Create empty migration
alembic revision -m "complex data migration"
```

**Example: Data Migration**

```python
# filepath: alembic/versions/xxx_migrate_name_to_first_last.py
"""Migrate name column to first_name and last_name

Revision ID: xyz789
Revises: abc123def456
Create Date: 2025-11-08 15:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision = 'xyz789'
down_revision = 'abc123def456'


def upgrade():
    """Split 'name' into 'first_name' and 'last_name'."""

    # Step 1: Add new columns (nullable for now)
    op.add_column('patients', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('patients', sa.Column('last_name', sa.String(), nullable=True))

    # Step 2: Migrate existing data
    # Create a temporary table reference
    patients_table = table('patients',
        column('id', sa.Integer),
        column('name', sa.String),
        column('first_name', sa.String),
        column('last_name', sa.String)
    )

    # Get connection
    connection = op.get_bind()

    # Fetch all patients
    patients = connection.execute(
        sa.select(patients_table.c.id, patients_table.c.name)
    ).fetchall()

    # Split names and update
    for patient_id, full_name in patients:
        if full_name:
            parts = full_name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''

            connection.execute(
                patients_table.update()
                .where(patients_table.c.id == patient_id)
                .values(first_name=first_name, last_name=last_name)
            )

    # Step 3: Make columns non-nullable
    op.alter_column('patients', 'first_name', nullable=False)
    op.alter_column('patients', 'last_name', nullable=False)

    # Step 4: Drop old column
    op.drop_column('patients', 'name')


def downgrade():
    """Combine 'first_name' and 'last_name' back to 'name'."""

    # Step 1: Add back name column
    op.add_column('patients', sa.Column('name', sa.String(), nullable=True))

    # Step 2: Migrate data back
    patients_table = table('patients',
        column('id', sa.Integer),
        column('name', sa.String),
        column('first_name', sa.String),
        column('last_name', sa.String)
    )

    connection = op.get_bind()
    patients = connection.execute(
        sa.select(patients_table.c.id, patients_table.c.first_name, patients_table.c.last_name)
    ).fetchall()

    for patient_id, first_name, last_name in patients:
        full_name = f"{first_name} {last_name}".strip()
        connection.execute(
            patients_table.update()
            .where(patients_table.c.id == patient_id)
            .values(name=full_name)
        )

    # Step 3: Make name non-nullable and drop new columns
    op.alter_column('patients', 'name', nullable=False)
    op.drop_column('patients', 'last_name')
    op.drop_column('patients', 'first_name')
```

---

## Running Migrations

### Basic Commands

```bash
# 1. Check current version
alembic current

# Output:
# abc123def456 (head)

# 2. View migration history
alembic history

# Output:
# abc123def456 -> xyz789 (head), Add patient contact information
# previous_id -> abc123def456, Create patients table
# <base> -> previous_id, Initial migration

# 3. Show pending migrations
alembic heads

# 4. Apply all pending migrations (most common)
alembic upgrade head

# Output:
# INFO  [alembic.runtime.migration] Running upgrade abc123 -> xyz789, Add patient contact information
# INFO  [alembic.runtime.migration] Running upgrade xyz789 -> efg012, Create visits table

# 5. Apply specific number of migrations
alembic upgrade +1    # Apply next migration
alembic upgrade +2    # Apply next 2 migrations

# 6. Upgrade to specific revision
alembic upgrade xyz789

# 7. Downgrade one version
alembic downgrade -1

# 8. Downgrade to specific revision
alembic downgrade abc123

# 9. Downgrade all the way (dangerous!)
alembic downgrade base

# 10. Show SQL without executing (dry run)
alembic upgrade head --sql

# 11. Generate SQL for migration
alembic upgrade head --sql > migration.sql
```

### Migration Workflow

**Development Environment:**

```bash
# 1. Pull latest code
git pull origin main

# 2. Apply any new migrations
alembic upgrade head

# 3. Make changes to models
# Edit app/models/patient.py

# 4. Generate migration
alembic revision --autogenerate -m "Add email to patients"

# 5. Review generated migration
cat alembic/versions/20251108_*_add_email.py

# 6. Apply migration
alembic upgrade head

# 7. Test your changes
pytest tests/

# 8. Commit migration file
git add alembic/versions/20251108_*_add_email.py
git commit -m "Add email column to patients"
git push
```

**Production Deployment:**

```bash
# 1. Backup database first!
pg_dump medical_assistant > backup_$(date +%Y%m%d).sql

# 2. Pull latest code
git pull origin main

# 3. Check what migrations will run
alembic current
alembic heads

# 4. Apply migrations
alembic upgrade head

# 5. Verify application works
curl http://localhost:8000/health

# 6. If something breaks, rollback
alembic downgrade -1

# 7. Restore from backup if needed
psql medical_assistant < backup_20251108.sql
```

---

## Common Migration Scenarios

### Scenario 1: Add a New Table

**Models:**

```python
# filepath: app/models/prescription.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.database.base import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True)
    prescription_id = Column(String, unique=True, index=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"))
    medication_name = Column(String, nullable=False)
    dosage = Column(String)
    frequency = Column(String)
    created_at = Column(DateTime)
```

**Generate Migration:**

```bash
alembic revision --autogenerate -m "Create prescriptions table"
```

**Generated Migration:**

```python
def upgrade():
    op.create_table(
        'prescriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prescription_id', sa.String(), nullable=True),
        sa.Column('patient_id', sa.String(), nullable=True),
        sa.Column('medication_name', sa.String(), nullable=False),
        sa.Column('dosage', sa.String(), nullable=True),
        sa.Column('frequency', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prescriptions_prescription_id', 'prescriptions', ['prescription_id'], unique=True)

def downgrade():
    op.drop_index('ix_prescriptions_prescription_id', table_name='prescriptions')
    op.drop_table('prescriptions')
```

### Scenario 2: Add Column with Default Value

**Models:**

```python
# Add status column to visits
class Visit(Base):
    __tablename__ = "visits"
    # ... existing columns ...
    status = Column(String, default="completed", nullable=False)  # NEW
```

**Manual Migration (Better Control):**

```python
def upgrade():
    # Add column as nullable first
    op.add_column('visits', sa.Column('status', sa.String(), nullable=True))

    # Set default value for existing rows
    op.execute("UPDATE visits SET status = 'completed' WHERE status IS NULL")

    # Now make it non-nullable
    op.alter_column('visits', 'status', nullable=False)

def downgrade():
    op.drop_column('visits', 'status')
```

### Scenario 3: Rename Column

```python
def upgrade():
    # Rename column
    op.alter_column('patients', 'name', new_column_name='full_name')

def downgrade():
    op.alter_column('patients', 'full_name', new_column_name='name')
```

### Scenario 4: Change Column Type

```python
def upgrade():
    # Change patient_id from Integer to String
    # Step 1: Add new column
    op.add_column('patients', sa.Column('patient_id_new', sa.String(), nullable=True))

    # Step 2: Copy data
    op.execute("UPDATE patients SET patient_id_new = CAST(patient_id AS VARCHAR)")

    # Step 3: Drop old column
    op.drop_column('patients', 'patient_id')

    # Step 4: Rename new column
    op.alter_column('patients', 'patient_id_new', new_column_name='patient_id')

def downgrade():
    # Reverse process
    op.add_column('patients', sa.Column('patient_id_new', sa.Integer(), nullable=True))
    op.execute("UPDATE patients SET patient_id_new = CAST(patient_id AS INTEGER)")
    op.drop_column('patients', 'patient_id')
    op.alter_column('patients', 'patient_id_new', new_column_name='patient_id')
```

### Scenario 5: Add Foreign Key Constraint

```python
def upgrade():
    # Add foreign key
    op.create_foreign_key(
        'fk_visits_patient_id',  # Constraint name
        'visits',  # Source table
        'patients',  # Target table
        ['patient_id'],  # Source column
        ['patient_id']  # Target column
    )

def downgrade():
    op.drop_constraint('fk_visits_patient_id', 'visits', type_='foreignkey')
```

### Scenario 6: Create Index

```python
def upgrade():
    # Create index for faster queries
    op.create_index(
        'ix_visits_patient_date',  # Index name
        'visits',  # Table name
        ['patient_id', 'visit_date']  # Columns
    )

def downgrade():
    op.drop_index('ix_visits_patient_date', table_name='visits')
```

---

## Best Practices

### 1. Always Review Auto-Generated Migrations

```bash
# After generating
alembic revision --autogenerate -m "description"

# ALWAYS review the file before applying
cat alembic/versions/latest_migration.py

# Check for:
# - Correct column types
# - Proper indexes
# - Foreign key constraints
# - Data that needs migration
```

### 2. Test Migrations on Development First

```bash
# Development workflow
alembic upgrade head    # Apply migration
pytest tests/           # Run tests
alembic downgrade -1    # Test rollback
alembic upgrade head    # Reapply

# Only after successful testing:
git commit -m "Add migration"
```

### 3. Backup Before Production Migrations

```bash
# ALWAYS backup before production migrations
pg_dump -Fc medical_assistant > backup_$(date +%Y%m%d_%H%M%S).dump

# Then migrate
alembic upgrade head

# If problems occur
pg_restore -d medical_assistant backup_20251108_143000.dump
```

### 4. Make Migrations Atomic

```python
# Good: Single focused change
def upgrade():
    op.add_column('patients', sa.Column('email', sa.String()))

# Bad: Multiple unrelated changes
def upgrade():
    op.add_column('patients', sa.Column('email', sa.String()))
    op.create_table('prescriptions', ...)
    op.alter_column('visits', 'status', ...)
```

### 5. Write Descriptive Migration Messages

```bash
# Good
alembic revision --autogenerate -m "Add email and phone columns to patients table"

# Bad
alembic revision --autogenerate -m "update"
alembic revision --autogenerate -m "changes"
```

### 6. Handle Data Migration Safely

```python
def upgrade():
    # Good: Check for existing data
    connection = op.get_bind()
    result = connection.execute("SELECT COUNT(*) FROM patients")
    count = result.scalar()

    if count > 0:
        # Migrate existing data
        op.execute("UPDATE patients SET status = 'active' WHERE status IS NULL")

    # Then add constraint
    op.alter_column('patients', 'status', nullable=False)
```

### 7. Keep Migrations Reversible

```python
# Every upgrade should have a working downgrade
def upgrade():
    op.add_column('patients', sa.Column('email', sa.String()))

def downgrade():
    op.drop_column('patients', 'email')
```

### 8. Document Complex Migrations

```python
"""Add patient email with validation

This migration:
1. Adds email column
2. Migrates data from contact_info JSON
3. Creates unique index
4. Adds check constraint for email format

Revision ID: abc123
Revises: xyz789
Create Date: 2025-11-08 14:30:00
"""

def upgrade():
    # Step 1: Add column
    op.add_column('patients', sa.Column('email', sa.String()))

    # Step 2: Migrate data
    # ... detailed explanation in comments ...
```

---

## Troubleshooting

### Problem 1: "Target database is not up to date"

```bash
# Error message:
# FAILED: Target database is not up to date.

# Solution: Apply pending migrations
alembic upgrade head
```

### Problem 2: "Can't locate revision identified by 'xyz'"

```bash
# Error: Migration file missing

# Solution: Pull latest migrations from Git
git pull origin main

# Or regenerate from models
alembic revision --autogenerate -m "Regenerate migration"
```

### Problem 3: Migration Conflicts

```bash
# Two people created migrations simultaneously
# You have: abc123 -> xyz789
# They have: abc123 -> def456

# Solution: Merge migrations
alembic merge xyz789 def456 -m "Merge migrations"

# This creates a new migration that depends on both
```

### Problem 4: Failed Migration (Partially Applied)

```bash
# Migration failed halfway through

# Solution 1: Manual cleanup
psql medical_assistant

# Check what was applied
SELECT * FROM alembic_version;

# Manually revert changes if needed
DROP TABLE IF EXISTS new_table;

# Mark migration as not applied
DELETE FROM alembic_version WHERE version_num = 'abc123';

# Solution 2: Force version
alembic stamp xyz789  # Mark as specific version
```

### Problem 5: Auto-Generate Detects No Changes

```bash
# Running --autogenerate but no changes detected

# Possible causes:
# 1. Models not imported in env.py
# 2. Database already up to date
# 3. Models and database are identical

# Solution: Check env.py imports
# Make sure all models are imported
from app.models.patient import Patient
from app.models.visit import Visit
# ... import all models ...
```

---

## Advanced Topics

### Branching and Merging

**Scenario: Multiple developers create migrations on different branches**

```bash
# Developer A creates migration on feature-email branch
git checkout -b feature-email
# ... create migration abc123 ...
git commit -m "Add email column"

# Developer B creates migration on feature-phone branch
git checkout -b feature-phone
# ... create migration def456 ...
git commit -m "Add phone column"

# Both merge to main - conflict!
# Alembic will detect two heads

# Solution: Merge migrations
alembic merge abc123 def456 -m "Merge email and phone migrations"

# This creates a new migration ghi789 that depends on both
```

### Conditional Migrations

```python
def upgrade():
    """Apply migration only if condition is met."""
    connection = op.get_bind()

    # Check if column exists
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('patients')]

    if 'email' not in columns:
        op.add_column('patients', sa.Column('email', sa.String()))
```

### Custom Migration Scripts

```python
def upgrade():
    """Run custom Python code during migration."""
    from app.services.data_migration_service import migrate_legacy_data

    # Run custom migration logic
    connection = op.get_bind()
    migrate_legacy_data(connection)
```

### Migrations with Multiple Databases

```python
# alembic/env.py
def run_migrations_online():
    """Run migrations on multiple databases."""

    # Primary database
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    # Analytics database (if applicable)
    analytics_engine = create_engine(settings.ANALYTICS_DATABASE_URL)
    with analytics_engine.connect() as connection:
        context.configure(connection=connection, target_metadata=analytics_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

---

## Summary

### Key Concepts

1. **Migrations = Version Control for Database**

   - Track schema changes over time
   - Apply changes consistently across environments
   - Rollback when needed

2. **Alembic Commands**

   ```bash
   alembic revision --autogenerate  # Create migration
   alembic upgrade head              # Apply migrations
   alembic downgrade -1              # Rollback
   alembic current                   # Check version
   alembic history                   # View history
   ```

3. **Migration Lifecycle**

   ```
   Modify Models → Generate Migration → Review → Test → Apply → Commit
   ```

4. **Best Practices**
   - Always review auto-generated migrations
   - Test on development first
   - Backup before production migrations
   - Keep migrations atomic and focused
   - Write reversible migrations
   - Document complex changes

### Common Workflow

```bash
# Daily development workflow
git pull                                    # Get latest code
alembic upgrade head                        # Apply migrations
# ... make changes to models ...
alembic revision --autogenerate -m "desc"   # Generate migration
alembic upgrade head                        # Apply migration
pytest                                      # Test
git add alembic/versions/*                  # Stage migration
git commit -m "Add migration"               # Commit
git push                                    # Share with team
```

### When to Use Manual Migrations

- Complex data transformations
- Multi-step migrations
- Conditional logic
- Performance-critical changes
- Migrations that need transaction control

### Remember

- 🔒 **Always backup before production migrations**
- 📝 **Review auto-generated migrations**
- 🧪 **Test migrations thoroughly**
- 🔄 **Keep migrations reversible**
- 📚 **Document complex migrations**
- 🤝 **Coordinate with team on migration conflicts**

---

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)
- [Database Migration Best Practices](https://www.prisma.io/dataguide/types/relational/what-are-database-migrations)

---

_This guide provides comprehensive coverage of database migrations with Alembic in your Medical Assistant project. Keep it handy as a reference when working with database schema changes!_
