#!/usr/bin/env python3
"""
Secure Credential Rotation Script

This script helps you rotate sensitive credentials in your .env files
without exposing them to AI assistants or logs.

Usage:
    python scripts/rotate_credentials.py

Features:
- Generates cryptographically secure SECRET_KEY (64+ characters)
- Creates backups of existing .env files
- Updates credentials safely
- No credentials printed to console
- HIPAA-compliant security practices
"""

import os
import secrets
import shutil
from datetime import datetime
from pathlib import Path


def generate_secret_key(length: int = 64) -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(length)


def backup_file(file_path: Path) -> Path:
    """Create a timestamped backup of a file."""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.name}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path.name}")
    return backup_path


def update_env_file(file_path: Path, updates: dict) -> bool:
    """
    Update environment variables in a .env file.
    
    Args:
        file_path: Path to .env file
        updates: Dictionary of {KEY: new_value}
    
    Returns:
        True if successful, False otherwise
    """
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False
    
    # Read existing content
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Update lines
    updated_lines = []
    keys_updated = set()
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith('#'):
            updated_lines.append(line)
            continue
        
        # Check if this line contains a key we want to update
        updated = False
        for key, new_value in updates.items():
            if line_stripped.startswith(f"{key}="):
                updated_lines.append(f"{key}={new_value}\n")
                keys_updated.add(key)
                updated = True
                break
        
        if not updated:
            updated_lines.append(line)
    
    # Add any keys that weren't found in the file
    for key, new_value in updates.items():
        if key not in keys_updated:
            updated_lines.append(f"{key}={new_value}\n")
            keys_updated.add(key)
    
    # Write updated content
    with open(file_path, 'w') as f:
        f.writelines(updated_lines)
    
    return True


def rotate_credentials():
    """Main credential rotation function."""
    print("🔐 Credential Rotation Script")
    print("=" * 60)
    print()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    env_docker_file = project_root / ".env_docker"
    
    # Generate new credentials
    print("🔑 Generating new cryptographically secure credentials...")
    new_secret_key_dev = generate_secret_key(64)
    new_secret_key_docker = generate_secret_key(64)
    print("✅ New SECRET_KEYs generated (64 characters each)")
    print()
    
    # Backup existing files
    print("💾 Creating backups...")
    backup_file(env_file)
    backup_file(env_docker_file)
    print()
    
    # Update .env file
    print("📝 Updating .env file...")
    if update_env_file(env_file, {"SECRET_KEY": new_secret_key_dev}):
        print("✅ .env updated successfully")
    else:
        print("❌ Failed to update .env")
    print()
    
    # Update .env_docker file
    print("📝 Updating .env_docker file...")
    if update_env_file(env_docker_file, {"SECRET_KEY": new_secret_key_docker}):
        print("✅ .env_docker updated successfully")
    else:
        print("❌ Failed to update .env_docker")
    print()
    
    # Additional recommendations
    print("=" * 60)
    print("✅ Credential rotation complete!")
    print()
    print("📋 Next Steps:")
    print("1. ✅ SECRET_KEYs have been rotated")
    print("2. ⏳ Consider rotating database passwords:")
    print("   - Update POSTGRES_PASSWORD in both .env files")
    print("   - Update the password in your PostgreSQL database")
    print("3. ⏳ Consider rotating API keys:")
    print("   - OPENAI_API_KEY (https://platform.openai.com/api-keys)")
    print("   - XAI_API_KEY (https://console.x.ai/)")
    print("   - ANTHROPIC_API_KEY (https://console.anthropic.com/)")
    print("4. ⏳ Restart your application:")
    print("   - Stop the running uvicorn server")
    print("   - Start it again to load new credentials")
    print()
    print("🔒 Security Notes:")
    print("- Backups are stored with timestamps")
    print("- Delete old backups after verifying everything works")
    print("- Never commit .env files to git")
    print("- Keep .aiignore file to prevent AI access")
    print()


if __name__ == "__main__":
    try:
        rotate_credentials()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
