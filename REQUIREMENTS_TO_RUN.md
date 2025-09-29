# Requirements to Run main.py Successfully

## 🔧 Current Issues

The main.py file cannot run because it's missing some required configurations. Here's what you need:

## ✅ Requirements Checklist

### 1. Environment Variables (CRITICAL)

You need to add these to your `.env` file:

```bash
# Required for AI agents
OPENAI_API_KEY=your-openai-api-key-here

# Optional (for Anthropic Claude support)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Database (can use SQLite for testing)
DATABASE_URL=postgresql://username:password@localhost:5432/doctors_assistant
# OR for testing without PostgreSQL:
# DATABASE_URL=sqlite:///./test.db
```

### 2. Database Setup (OPTIONAL for basic testing)

Currently the app tries to connect to PostgreSQL. You have two options:

#### Option A: PostgreSQL (Production)

```bash
# Install PostgreSQL
brew install postgresql

# Start PostgreSQL
brew services start postgresql

# Create database
createdb doctors_assistant

# Update .env with correct connection string
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/doctors_assistant
```

#### Option B: SQLite (Quick Testing)

```bash
# Just update .env file:
DATABASE_URL=sqlite:///./test.db
```

### 3. AI API Keys (REQUIRED)

The main issue is that PydanticAI agents are trying to initialize without API keys.

#### Get OpenAI API Key:

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add it to your `.env` file:
   ```
   OPENAI_API_KEY=sk-...your-key-here
   ```

## 🚀 Quick Fix Options

### Option 1: Add Dummy API Key (for testing)

```bash
# Add to .env file
OPENAI_API_KEY=dummy-key-for-testing
```

_Note: This will allow the app to start but AI features won't work_

### Option 2: Use main_simple.py Instead

```bash
# Run the simple version without AI agents
python -m uvicorn app.main_simple:app --reload
```

### Option 3: Modify main.py to disable AI temporarily

We can create a version that skips AI initialization.

## 📋 Current Status

### ✅ Working:

- FastAPI framework
- Basic configuration
- Database models
- API structure

### ❌ Blocking Issues:

1. **Missing OPENAI_API_KEY** - Required for PydanticAI agents
2. **Database connection** - Optional but recommended

## 🛠️ Immediate Action Items

1. **Set OpenAI API Key**:

   ```bash
   echo "OPENAI_API_KEY=your-key-here" >> .env
   ```

2. **Test with SQLite** (easier setup):

   ```bash
   echo "DATABASE_URL=sqlite:///./test.db" >> .env
   ```

3. **Run the application**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

## 💡 Alternative: Create a Development Mode

I can create a version of main.py that works without AI keys for development purposes. Would you like me to do that?
