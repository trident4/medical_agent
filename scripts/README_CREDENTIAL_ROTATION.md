# Credential Rotation Guide

## Quick Start

```bash
# Run the credential rotation script
python scripts/rotate_credentials.py
```

This will automatically:
- ✅ Generate new 64-character SECRET_KEYs
- ✅ Backup your existing `.env` and `.env_docker` files
- ✅ Update both files with new SECRET_KEYs
- ✅ Keep all other environment variables unchanged

## What Gets Rotated

### Automatic (by script):
- `SECRET_KEY` in `.env` (development)
- `SECRET_KEY` in `.env_docker` (production)

### Manual (you need to do):
1. **Database Password** (`POSTGRES_PASSWORD`)
2. **API Keys** (OpenAI, XAI, Anthropic)
3. **Admin Password** (`ADMIN_PASSWORD`)

## Manual Rotation Steps

### 1. Rotate Database Password

```bash
# Generate a new password
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in .env and .env_docker
# Then update in PostgreSQL:
psql -U chetan -d doctors_assistant
ALTER USER chetan WITH PASSWORD 'your-new-password';
```

### 2. Rotate API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **XAI/Grok**: https://console.x.ai/
- **Anthropic**: https://console.anthropic.com/

Generate new keys and update in your `.env` files.

### 3. Rotate Admin Password

```bash
# Update ADMIN_PASSWORD in .env files
# Then recreate the admin user:
python scripts/create_admin.py
```

## After Rotation

1. **Restart your application:**
   ```bash
   # Stop current server (Ctrl+C)
   # Start again
   uvicorn app.main:app --reload
   ```

2. **Test authentication:**
   ```bash
   # Try logging in with existing credentials
   curl -X POST http://localhost:8000/api/v1/auth/login/json \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"your-password"}'
   ```

3. **Delete old backups** (after verifying everything works):
   ```bash
   rm .env.backup_*
   rm .env_docker.backup_*
   ```

## Security Best Practices

- 🔒 Never commit `.env` files to git
- 🔒 Use different credentials for dev/staging/production
- 🔒 Rotate credentials every 90 days
- 🔒 Rotate immediately after any suspected exposure
- 🔒 Keep `.aiignore` file to prevent AI access
- 🔒 Use a password manager for storing credentials

## Troubleshooting

### "Authentication failed" after rotation
- Check that you updated the correct `.env` file
- Restart the application to load new credentials
- Verify the SECRET_KEY was updated correctly

### "Database connection failed" after rotation
- Ensure POSTGRES_PASSWORD matches in both `.env` and PostgreSQL
- Check that the database user has the correct password

### Lost credentials
- Check the backup files (`.env.backup_TIMESTAMP`)
- Restore from backup if needed:
  ```bash
  cp .env.backup_20231122_120000 .env
  ```

## HIPAA Compliance Notes

This rotation process follows HIPAA security requirements:
- ✅ Cryptographically secure key generation
- ✅ No credentials logged or printed
- ✅ Automatic backup creation
- ✅ Separation of dev/production credentials
- ✅ Regular rotation schedule recommended
