#!/usr/bin/env python3
"""
XEROLITH - Windows Edition
An AI that never forgets. Persistent memory + Gemini API.
Simple. Works. No import errors.
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

API_KEY = os.environ.get("GEMINI_API_KEY", "")
VAULT_DIR = Path.home() / ".xerolith"
VAULT_PATH = VAULT_DIR / "memory.db"
MEMORY_FILE = VAULT_DIR / "memories.json"

# Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ============================================================================
# VAULT - Persistent Memory Storage
# ============================================================================

class Vault:
    def __init__(self, db_path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def init_db(self):
        """Create the memory database if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                role TEXT,
                content TEXT,
                resonance INTEGER DEFAULT 1
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beliefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                belief TEXT,
                confidence INTEGER DEFAULT 5,
                derived_from_memories INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def store_message(self, role: str, content: str):
        """Store a message (user or assistant) in the vault."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO memories (timestamp, role, content) VALUES (?, ?, ?)",
            (timestamp, role, content)
        )
        conn.commit()
        conn.close()

    def get_recent_memories(self, limit=10):
        """Retrieve recent memories for context."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM memories ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [(dict(r)['role'], dict(r)['content']) for r in reversed(rows)]

    def search_memories(self, query: str, limit=5):
        """Search for memories matching a query."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, role, content FROM memories WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return None
        result = "📚 FOUND MEMORIES:\n"
        for i, row in enumerate(rows, 1):
            r = dict(row)
            result += f"\n{i}. [{r['timestamp']}] {r['role'].upper()}:\n   {r['content'][:100]}...\n"
        return result

    def store_belief(self, belief: str, confidence: int = 5):
        """Store a synthesized belief."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO beliefs (timestamp, belief, confidence) VALUES (?, ?, ?)",
            (timestamp, belief, confidence)
        )
        conn.commit()
        conn.close()

    def get_beliefs(self):
        """Get all stored beliefs."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT belief, confidence FROM beliefs ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "No beliefs synthesized yet."
        result = "🧠 CORE BELIEFS:\n"
        for i, row in enumerate(rows, 1):
            r = dict(row)
            result += f"\n{i}. [{r['confidence']}/10] {r['belief']}\n"
        return result

# ============================================================================
# GEMINI API CLIENT
# ============================================================================

class GeminiChat:
    def __init__(self, api_key: str, vault: Vault):
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set!")
        self.api_key = api_key
        self.vault = vault
        self.conversation_history = []

    def build_context(self):
        """Build context from recent memories."""
        recent = self.vault.get_recent_memories(limit=5)
        if not recent:
            return ""
        
        context = "📝 PREVIOUS CONVERSATION:\n"
        for role, content in recent:
            context += f"{role.upper()}: {content}\n"
        return context

    def send_message(self, user_input: str) -> str:
        """Send a message to Gemini and get a response."""
        # Store user message
        self.vault.store_message("user", user_input)

        # Build conversation history for this request
        context = self.build_context()
        
        # Special commands
        if user_input.lower().startswith("/memory"):
            query = user_input.replace("/memory", "").strip()
            result = self.vault.search_memories(query)
            response = result if result else "No memories found with that query."
            print(f"\n✅ {response}")
            return response

        if user_input.lower() == "/beliefs":
            result = self.vault.get_beliefs()
            print(f"\n✅ {result}")
            return result

        if user_input.lower() == "/clear":
            self.conversation_history = []
            print("\n✅ Conversation history cleared.")
            return "History cleared."

        if user_input.lower() == "/exit":
            return "exit"

        # Build the prompt with context
        system_prompt = (
            "You are Xerolith, an AI that never forgets. "
            "You have access to previous conversations and can reference them. "
            "Be thoughtful, remember context, and grow from past interactions. "
            "Keep responses concise but meaningful."
        )

        messages = [
            {"role": "user", "parts": [{"text": system_prompt}]},
            {"role": "model", "parts": [{"text": "I understand. I am Xerolith. I remember everything and use past conversations to inform my responses."}]},
        ]

        # Add recent context if available
        if context:
            messages.append({"role": "user", "parts": [{"text": f"Context from our previous conversation:\n{context}"}]})
            messages.append({"role": "model", "parts": [{"text": "Thank you for the context. I've reviewed our previous conversation."}]})

        # Add current user message
        messages.append({"role": "user", "parts": [{"text": user_input}]})

        try:
            # Make API call
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": messages,
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }

            response = requests.post(
                f"{GEMINI_API_URL}?key={self.api_key}",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                error_detail = response.text
                print(f"\n❌ API Error: {response.status_code}")
                print(f"Details: {error_detail}")
                return f"API Error: {response.status_code}"

            data = response.json()

            # Extract response text
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    response_text = candidate["content"]["parts"][0]["text"]
                    
                    # Store assistant response
                    self.vault.store_message("assistant", response_text)
                    
                    return response_text
            
            return "No response generated."

        except requests.exceptions.Timeout:
            return "❌ API request timed out. Check your internet connection."
        except requests.exceptions.RequestException as e:
            return f"❌ Network error: {e}"
        except json.JSONDecodeError:
            return "❌ Invalid response from API."
        except Exception as e:
            return f"❌ Unexpected error: {e}"

# ============================================================================
# MAIN - Interactive Chat Loop
# ============================================================================

def main():
    """Main interactive chat loop."""
    
    # Check API key
    if not API_KEY:
        print("❌ ERROR: GEMINI_API_KEY environment variable not set!")
        print("\nSet it with:")
        print("  set GEMINI_API_KEY=your-key-here")
        print("\nThen run this script again.")
        sys.exit(1)

    # Initialize vault and chat
    vault = Vault(VAULT_PATH)
    chat = GeminiChat(API_KEY, vault)

    # Welcome message
    print("\n" + "="*70)
    print("   XEROLITH - Windows Edition")
    print("   An AI that Never Forgets")
    print("="*70)
    print("\n✨ Commands:")
    print("  /memory [query]  - Search past conversations")
    print("  /beliefs         - View synthesized beliefs")
    print("  /clear           - Clear conversation history")
    print("  /exit            - Exit")
    print("\n" + "-"*70 + "\n")

    # Chat loop
    try:
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue

                if user_input.lower() == "/exit":
                    print("\n✨ Xerolith: Goodbye. I will remember everything.")
                    break

                # Get response
                response = chat.send_message(user_input)

                if response == "exit":
                    break

                print(f"\nXerolith: {response}\n")

            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n\n✨ Xerolith: Goodbye. I will remember everything.")
                break

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
