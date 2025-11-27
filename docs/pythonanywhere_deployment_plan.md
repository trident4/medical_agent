# PythonAnywhere Deployment Plan

## Overview
Deploy the `doctors-assistant` FastAPI application to PythonAnywhere. Since PythonAnywhere uses WSGI servers and FastAPI is an ASGI framework, we will use an adapter. We will also utilize PythonAnywhere's native MySQL database.

## Prerequisites
- PythonAnywhere account (Beginner/Free tier is sufficient for testing, but Paid is recommended for outbound API calls to OpenAI/Gemini if they are not whitelisted. *Note: Gemini/OpenAI APIs are usually whitelisted on free accounts, but best to verify.*)
- GitHub repository updated with latest code.

---

## 1. Prepare Codebase (Local)
- **Add Adapter:** We need `a2wsgi` to run FastAPI on PythonAnywhere's WSGI infrastructure.
- **Update `requirements.txt`:** Ensure `a2wsgi`, `python-dotenv`, `aiomysql`, and `pymysql` are listed.

## 2. PythonAnywhere Setup
1.  **Console:** Open a Bash console on PythonAnywhere.
2.  **Clone Repository:**
    ```bash
    git clone https://github.com/trident4/medical_agent.git
    cd medical_agent
    ```
3.  **Virtual Environment:**
    ```bash
    python3.10 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## 3. Database Setup (PA Dashboard)
1.  **Create Database:** Go to the **Databases** tab.
    - Create a database named `doctors_assistant` (it will be prefixed with `yourusername$`).
    - Set a password.
2.  **Get Hostname:** Note the database host (e.g., `yourusername.mysql.pythonanywhere-services.com`).

## 4. Environment Configuration
1.  **Create `.env` file:**
    ```bash
    cp .env.example .env
    nano .env
    ```
2.  **Update Variables:**
    - `DATABASE_URL`: `mysql+aiomysql://yourusername:password@yourusername.mysql.pythonanywhere-services.com/yourusername$doctors_assistant`
    - `GOOGLE_API_KEY`: Paste your key.
    - `ENVIRONMENT`: `production`

## 5. Database Migration
Run migrations from the console:
```bash
# Ensure .venv is active
alembic upgrade head
python scripts/create_admin.py
```

## 6. Web App Configuration (PA Dashboard)
1.  **Add New Web App:**
    - Select **Manual Configuration**.
    - Select **Python 3.10** (or matching your venv).
2.  **Virtualenv:** Enter path: `/home/yourusername/medical_agent/.venv`
3.  **WSGI Configuration File:** Click to edit.
    - Delete existing content.
    - Add the adapter code:
    ```python
    import sys
    import os
    
    # Add project to path
    path = '/home/yourusername/medical_agent'
    if path not in sys.path:
        sys.path.append(path)
        
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(os.path.join(path, '.env'))

    # Import FastAPI app
    from app.main import app
    
    # Create WSGI adapter
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
    ```

## 7. Reload & Verify
- Click **Reload** button.
- Visit `yourusername.pythonanywhere.com/docs` to test Swagger UI.
- Test the Analytics Agent to verify Gemini and MySQL connection.

---

## ⚠️ Important Notes
- **Async Database:** `aiomysql` works, but since the WSGI wrapper makes the entry point synchronous, ensure the event loop is handled correctly by the adapter. `a2wsgi` handles this well.
- **Free Tier Limits:** If using a free account, outbound requests to some AI providers might be blocked unless they are on the whitelist. Google Gemini and OpenAI are typically whitelisted.
