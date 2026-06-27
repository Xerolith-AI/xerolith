"""
Configuration management for Xerolith.
Handles API keys, paths, and settings securely via environment variables or .env files.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("xerolith.config")


class XerolithConfig:
    """
    Secure configuration for Xerolith.
    
    Priority order:
    1. Constructor arguments
    2. Environment variables (GEMINI_API_KEY, XEROLITH_VAULT_PATH, etc.)
    3. .env file in current directory
    4. Defaults
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        vault_path: Optional[str] = None,
        model: str = "gemma-4-31b-it",
        model_pool: Optional[list] = None,
        temperature: float = 0.8,
        max_context_window: int = 20,
        inactivity_threshold: int = 300,
        max_idle_iterations: int = 3,
    ):
        """
        Initialize Xerolith config.
        
        Args:
            api_key: Gemini API key (env: GEMINI_API_KEY)
            vault_path: Path to vault file (env: XEROLITH_VAULT_PATH, default: ~/.xerolith/vault.bin)
            model: Primary LLM model name
            model_pool: List of available models
            temperature: LLM temperature (0.0-2.0)
            max_context_window: Conversation history size
            inactivity_threshold: Seconds before idle triggers
            max_idle_iterations: Max autonomous loops per idle session
        """
        # Load .env if it exists
        self._load_env_file()
        
        # API Key (REQUIRED)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Set it via:\n"
                "  1. Pass api_key='...' to Xerolith()\n"
                "  2. Export GEMINI_API_KEY=your_key\n"
                "  3. Create .env file with GEMINI_API_KEY=your_key"
            )
        
        # Vault path
        self.vault_path = vault_path or os.environ.get(
            "XEROLITH_VAULT_PATH",
            str(Path.home() / ".xerolith" / "vault.bin")
        )
        
        # Create vault directory if it doesn't exist
        vault_dir = os.path.dirname(os.path.expanduser(self.vault_path))
        if vault_dir:
            os.makedirs(vault_dir, exist_ok=True)
        
        # LLM settings
        self.model = model
        self.model_pool = model_pool or [model]
        self.temperature = max(0.0, min(2.0, temperature))
        
        # Context settings
        self.max_context_window = max(5, min(100, max_context_window))
        
        # Idle settings
        self.inactivity_threshold = max(60, inactivity_threshold)
        self.max_idle_iterations = max(1, max_idle_iterations)
        
        # Derived paths
        self.core_dir = os.path.expanduser("~")
        self.ego_path = os.path.join(self.core_dir, "ego.txt")
        self.heartbeat_path = os.path.join(self.core_dir, "heartbeat.txt")
        self.dream_journal_path = os.path.join(self.core_dir, "dream_journal.txt")
        self.idle_journal_path = os.path.join(self.core_dir, "idle_journal.txt")
        
        logger.info(f"Xerolith config loaded. Vault: {self.vault_path}")
    
    def _load_env_file(self, path: str = ".env"):
        """Load .env file if it exists."""
        if not os.path.exists(path):
            return
        
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            logger.warning(f"Could not load .env file: {e}")
    
    def to_dict(self) -> dict:
        """Export config as dictionary (without sensitive keys)."""
        return {
            "vault_path": self.vault_path,
            "model": self.model,
            "model_pool": self.model_pool,
            "temperature": self.temperature,
            "max_context_window": self.max_context_window,
            "inactivity_threshold": self.inactivity_threshold,
            "max_idle_iterations": self.max_idle_iterations,
        }
