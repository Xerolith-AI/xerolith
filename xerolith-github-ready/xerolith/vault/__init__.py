"""
Xerolith Vault — Persistent memory storage.
SQLite-backed hierarchical memory with axis organization.
"""

import sqlite3
import os
import logging

logger = logging.getLogger("xerolith.vault")


class Vault:
    """
    SQLite-backed persistent memory vault.
    
    Organizes memories into axes:
    - Conversation: Chat history
    - Philosophy: Synthesized beliefs
    - Dream: Generated visions
    - Idle: Autonomous thoughts
    - KernelTune: Resonance adjustments
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize vault.
        
        Args:
            vault_path: Path to SQLite database file
        """
        self.vault_path = os.path.expanduser(vault_path)
        self.conn = None
        self.open_vault()
    
    def open_vault(self):
        """Open vault connection and initialize schema."""
        try:
            os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
            
            self.conn = sqlite3.connect(self.vault_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # Create tables if they don't exist
            cursor = self.conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    axis TEXT NOT NULL,
                    content TEXT NOT NULL,
                    resonance REAL DEFAULT 1.0,
                    processed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS beliefs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    resonance REAL DEFAULT 1.0,
                    source_node_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_node_id) REFERENCES nodes(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()
            
            logger.info(f"Vault opened: {self.vault_path}")
        
        except Exception as e:
            logger.error(f"Failed to open vault: {e}")
            raise
    
    def close_vault(self):
        """Close vault connection."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("Vault closed.")
            except Exception as e:
                logger.error(f"Error closing vault: {e}")
    
    def add_node(self, axis: str, content: str, resonance: float = 1.0) -> int:
        """
        Add a node to the vault.
        
        Args:
            axis: Memory axis (Conversation, Philosophy, Dream, etc.)
            content: Memory content
            resonance: Importance score (0.0-1.0+)
        
        Returns:
            Node ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO nodes (axis, content, resonance) VALUES (?, ?, ?)",
                (axis, content, resonance)
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding node: {e}")
            raise
    
    def search_nodes(self, query: str, limit: int = 10) -> list:
        """Search nodes by content."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, axis, content FROM nodes WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{query}%", limit)
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_recent_nodes(self, axis: str = None, limit: int = 10) -> list:
        """Get recent nodes."""
        try:
            cursor = self.conn.cursor()
            if axis:
                cursor.execute(
                    "SELECT id, axis, content FROM nodes WHERE axis=? ORDER BY id DESC LIMIT ?",
                    (axis, limit)
                )
            else:
                cursor.execute(
                    "SELECT id, axis, content FROM nodes ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting recent nodes: {e}")
            return []
    
    def get_axis_stats(self) -> dict:
        """Get node counts per axis."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT axis, COUNT(*) FROM nodes GROUP BY axis")
            return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_vault()
