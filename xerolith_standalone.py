#!/usr/bin/env python3
"""
XEROLITH — Standalone Single File Version
Autonomous AI with Persistent Memory
Copy this entire file and run it on mobile.
"""

import os
import sqlite3
import logging
import requests
import json
from pathlib import Path
from collections import deque
from dotenv import load_dotenv

# Load .env if exists
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xerolith")

# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

class Config:
    """Secure configuration - gets API key from environment or .env"""
    
    def __init__(self):
        # Get API key from environment
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not set!\n"
                "Set it via: export GEMINI_API_KEY='your-key-here'\n"
                "Or create .env file with: GEMINI_API_KEY=your-key-here"
            )
        
        # Vault path
        self.vault_path = os.path.expanduser("~/.xerolith/vault.bin")
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
        
        # Settings
        self.model = "gemma-4-31b-it"
        self.temperature = 0.8
        
        logger.info(f"Config loaded. Vault: {self.vault_path}")

# ════════════════════════════════════════════════════════════════
# VAULT - Persistent Memory
# ════════════════════════════════════════════════════════════════

class Vault:
    """SQLite-backed persistent memory"""
    
    def __init__(self, path):
        self.path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create table
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                axis TEXT NOT NULL,
                content TEXT NOT NULL,
                resonance REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        logger.info(f"Vault opened: {self.path}")
    
    def add(self, axis, content):
        """Add to vault"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO nodes (axis, content, resonance) VALUES (?, ?, ?)",
            (axis, content, 1.0)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def search(self, query, limit=10):
        """Search vault"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, axis, content FROM nodes WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        return cursor.fetchall()
    
    def stats(self):
        """Get vault statistics"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT axis, COUNT(*) FROM nodes GROUP BY axis")
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def close(self):
        self.conn.close()

# ════════════════════════════════════════════════════════════════
# LLM CLIENT - Gemini API
# ════════════════════════════════════════════════════════════════

class GeminiClient:
    """Google Gemini API client"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    
    def create_chat(self, model="gemma-4-31b-it", system="", temperature=0.8):
        return Chat(self, model, system, temperature)

class Chat:
    """Single chat session"""
    
    def __init__(self, client, model, system, temperature):
        self.client = client
        self.model = model
        self.messages = []
        self.temperature = temperature
        
        if system:
            self.messages.append({"role": "user", "content": system})
            self.messages.append({"role": "assistant", "content": "Ready."})
    
    def send(self, message):
        """Send message and get response"""
        self.messages.append({"role": "user", "content": message})
        
        try:
            response = requests.post(
                f"{self.client.base_url}chat/completions",
                headers=self.client.headers,
                json={
                    "model": f"models/{self.model}",
                    "messages": self.messages,
                    "temperature": self.temperature
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0].get("message", {}).get("content", "")
            self.messages.append({"role": "assistant", "content": content})
            
            return content
        except Exception as e:
            logger.error(f"API error: {e}")
            return f"[Error: {e}]"

# ════════════════════════════════════════════════════════════════
# XEROLITH - Main Agent
# ════════════════════════════════════════════════════════════════

class Xerolith:
    """Autonomous AI with persistent memory"""
    
    def __init__(self, api_key=None):
        """Initialize Xerolith"""
        
        # Config
        config = Config()
        
        # Components
        self.vault = Vault(config.vault_path)
        self.client = GeminiClient(config.api_key)
        self.config = config
        
        # Context
        self.history = deque(maxlen=20)
        
        logger.info("✅ Xerolith initialized and ready!")
    
    def chat(self, user_input):
        """Chat with Xerolith"""
        
        if not user_input.strip():
            return ""
        
        # Add to history
        self.history.append({"role": "user", "text": user_input})
        
        # Add to vault
        self.vault.add("Conversation", f"User: {user_input}")
        
        # Build context
        stats = self.vault.stats()
        stats_text = "\n".join([f"{k}: {v} nodes" for k, v in stats.items()])
        
        system = f"""You are Xerolith, an AI with persistent memory.
You never forget conversations.

VAULT STATUS:
{stats_text}

Respond naturally. Remember everything."""
        
        # Chat
        chat = self.client.create_chat(
            model=self.config.model,
            system=system,
            temperature=self.config.temperature
        )
        
        response = chat.send(user_input)
        
        # Store response
        self.vault.add("Conversation", f"Xerolith: {response[:1000]}")
        self.history.append({"role": "assistant", "text": response})
        
        return response
    
    def memory(self, query):
        """Search memory"""
        results = self.vault.search(query, limit=5)
        if not results:
            return "No memories found."
        return "\n".join([f"[{r[0]}] {r[2][:100]}" for r in results])
    
    def status(self):
        """Get vault status"""
        stats = self.vault.stats()
        total = sum(stats.values())
        return f"Vault: {total} total nodes\n" + "\n".join([f"  {k}: {v}" for k, v in stats.items()])
    
    def close(self):
        """Close vault"""
        self.vault.close()
        logger.info("Xerolith closed.")

# ════════════════════════════════════════════════════════════════
# MAIN - Interactive Chat
# ════════════════════════════════════════════════════════════════

def main():
    """Run interactive Xerolith"""
    
    print("\n" + "="*60)
    print("🧠 XEROLITH — Autonomous AI with Persistent Memory")
    print("="*60)
    print("Type 'exit' to quit, 'memory <query>' to search\n")
    
    try:
        xero = Xerolith()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    try:
        while True:
            user = input("You: ").strip()
            
            if not user:
                continue
            
            if user.lower() == "exit":
                print("\nGoodbye!")
                break
            
            if user.lower().startswith("memory "):
                query = user[7:]
                print(f"\nMemories: {xero.memory(query)}\n")
                continue
            
            if user.lower() == "status":
                print(f"\n{xero.status()}\n")
                continue
            
            print("\nXerolith: ", end="", flush=True)
            response = xero.chat(user)
            print(response + "\n")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    
    finally:
        xero.close()

if __name__ == "__main__":
    main()
