import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            associate_id TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Create password resets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            token_hash TEXT PRIMARY KEY,
            associate_id TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY(associate_id) REFERENCES users(associate_id)
        )
    ''')
    
    # Pre-populate with initial user if it doesn't exist (migrating from VALID_USERS)
    cursor.execute("SELECT associate_id FROM users WHERE associate_id = '123'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash("admin@123")
        cursor.execute("INSERT INTO users (associate_id, password_hash) VALUES (?, ?)", ("123", hashed_pw))
    
    conn.commit()
    conn.close()

def check_credentials(associate_id, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE associate_id = ?", (associate_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and check_password_hash(row[0], password):
        return True
    return False

def user_exists(associate_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT associate_id FROM users WHERE associate_id = ?", (associate_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def create_reset_token(associate_id):
    # 32 bytes of secure random data -> urlsafe base64 string
    raw_token = secrets.token_urlsafe(32)
    # Hash the token before storing to prevent DB leaks from exposing valid tokens
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Expire in 30 minutes
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Optional: Delete any existing tokens for this user to invalidate old ones immediately
    cursor.execute("DELETE FROM password_resets WHERE associate_id = ?", (associate_id,))
    cursor.execute("INSERT INTO password_resets (token_hash, associate_id, expires_at) VALUES (?, ?, ?)", 
                   (token_hash, associate_id, expires_at))
    conn.commit()
    conn.close()
    
    return raw_token

def validate_reset_token(raw_token):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT associate_id, expires_at FROM password_resets WHERE token_hash = ?", (token_hash,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        associate_id, expires_at_str = row
        # Handle cases where datetime might have microseconds or not
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except ValueError:
            # Fallback parsing if needed
            expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d %H:%M:%S.%f')
            
        if datetime.utcnow() <= expires_at:
            return associate_id
    return None

def update_password(associate_id, new_password, raw_token):
    hashed_pw = generate_password_hash(new_password)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Update password
    cursor.execute("UPDATE users SET password_hash = ? WHERE associate_id = ?", (hashed_pw, associate_id))
    # Invalidate token
    cursor.execute("DELETE FROM password_resets WHERE token_hash = ?", (token_hash,))
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()
