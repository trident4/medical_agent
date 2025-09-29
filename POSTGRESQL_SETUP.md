# PostgreSQL Setup Guide for Medical Assistant Project

## 🐘 PostgreSQL Installation & Setup

### Step 1: Install PostgreSQL

#### Option A: Using Homebrew (Recommended)

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15
```

#### Option B: Using PostgreSQL.app (GUI Option)

1. Download from: https://postgresapp.com/
2. Install and run the app
3. Click "Initialize" to create a new server

#### Option C: Using Official Installer

1. Download from: https://www.postgresql.org/download/macosx/
2. Follow the installation wizard

### Step 2: Verify Installation

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Check PostgreSQL version
psql --version
```

### Step 3: Create Database and User

#### Method 1: Using psql command line

```bash
# Connect to PostgreSQL as superuser
psql postgres

# Inside psql prompt, run these commands:
```

```sql
-- Create a user for the medical assistant app
CREATE USER medical_user WITH PASSWORD 'secure_password_123';

-- Create the database
CREATE DATABASE doctors_assistant OWNER medical_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE doctors_assistant TO medical_user;

-- Exit psql
\q
```

#### Method 2: Using createdb command (simpler)

```bash
# Create the database directly
createdb doctors_assistant

# Create user (optional if using your system user)
psql -c "CREATE USER medical_user WITH PASSWORD 'secure_password_123';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE doctors_assistant TO medical_user;"
```

### Step 4: Update Environment Configuration

Edit your `.env` file:

```bash
# Open .env file
nano .env
```

Replace the DATABASE_URL line with:

```bash
# Using system user (simpler)
DATABASE_URL=postgresql://$(whoami)@localhost:5432/doctors_assistant

# OR using the medical_user we created
DATABASE_URL=postgresql://medical_user:secure_password_123@localhost:5432/doctors_assistant
```

### Step 5: Test Database Connection

#### Test 1: Direct psql connection

```bash
# Test connection with system user
psql -d doctors_assistant

# OR test with medical_user
psql -h localhost -U medical_user -d doctors_assistant
```

#### Test 2: Python connection test

```bash
# Run this in your project directory
/Users/chetan/Personal/HobbyProjects/doctors-assistant/.venv/bin/python -c "
import asyncpg
import asyncio

async def test_connection():
    try:
        conn = await asyncpg.connect('postgresql://$(whoami)@localhost:5432/doctors_assistant')
        version = await conn.fetchval('SELECT version()')
        print('✅ Database connection successful!')
        print(f'PostgreSQL version: {version}')
        await conn.close()
    except Exception as e:
        print(f'❌ Connection failed: {e}')

asyncio.run(test_connection())
"
```

### Step 6: Initialize Database Tables

#### Option A: Using our initialization script

```bash
# Update the init_db.py script and run it
/Users/chetan/Personal/HobbyProjects/doctors-assistant/.venv/bin/python init_db.py
```

#### Option B: Using Python directly

```bash
/Users/chetan/Personal/HobbyProjects/doctors-assistant/.venv/bin/python -c "
import asyncio
from app.database.session import engine
from app.database.base import Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Database tables created successfully!')

asyncio.run(create_tables())
"
```

### Step 7: Verify Setup

Run the development server:

```bash
/Users/chetan/Personal/HobbyProjects/doctors-assistant/.venv/bin/python -m uvicorn app.main_dev:app --reload
```

Check the status at: http://localhost:8000/api/v1/setup-status

## 🔧 Troubleshooting

### Common Issues:

#### 1. PostgreSQL not running

```bash
# Start PostgreSQL
brew services start postgresql@15

# Check status
brew services list | grep postgresql
```

#### 2. Permission denied

```bash
# Make sure you're using the correct user
whoami

# Or create database with your user as owner
createdb -O $(whoami) doctors_assistant
```

#### 3. Connection refused

```bash
# Check if PostgreSQL is listening
lsof -i :5432

# Restart PostgreSQL
brew services restart postgresql@15
```

#### 4. Database doesn't exist

```bash
# List all databases
psql -l

# Create database if missing
createdb doctors_assistant
```

### Configuration Examples:

#### For system user (recommended for development):

```bash
DATABASE_URL=postgresql://$(whoami)@localhost:5432/doctors_assistant
```

#### For custom user:

```bash
DATABASE_URL=postgresql://medical_user:secure_password_123@localhost:5432/doctors_assistant
```

#### For specific host/port:

```bash
DATABASE_URL=postgresql://username:password@127.0.0.1:5432/doctors_assistant
```

## 🎯 Quick Setup Commands

Here's the complete setup in one go:

```bash
# 1. Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# 2. Create database
createdb doctors_assistant

# 3. Update .env file
echo "DATABASE_URL=postgresql://$(whoami)@localhost:5432/doctors_assistant" > .env.tmp
grep -v "DATABASE_URL" .env >> .env.tmp
mv .env.tmp .env

# 4. Test connection
/Users/chetan/Personal/HobbyProjects/doctors-assistant/.venv/bin/python -c "
import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect('postgresql://$(whoami)@localhost:5432/doctors_assistant')
        print('✅ Database connection successful!')
        await conn.close()
    except Exception as e:
        print(f'❌ Connection failed: {e}')

asyncio.run(test())
"

# 5. Initialize tables
/Users/chetan/Personal/HobbyProjects/doctors-assistant/.venv/bin/python -c "
import asyncio
from app.database.session import engine
from app.database.base import Base

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Tables created!')

asyncio.run(init())
"
```

## ✅ Verification Checklist

- [ ] PostgreSQL installed and running
- [ ] Database `doctors_assistant` created
- [ ] `.env` file updated with correct DATABASE_URL
- [ ] Python can connect to database
- [ ] Database tables created
- [ ] Application starts without database errors

Let me know when you're ready for each step, and I'll help you through any issues! 🚀
