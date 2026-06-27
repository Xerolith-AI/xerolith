"""
XEROLITH — Autonomous AI with Persistent Memory
A lightweight, on-device memory system for LLMs with self-healing and philosophy synthesis.

Usage:
    from xerolith import Xerolith
    
    xero = Xerolith(api_key="your-key-here")
    response = xero.chat("hello")
"""

__version__ = "1.0.0"
__author__ = "Tyler Love (@MuskaTat)"

import os
import logging
from .config import XerolithConfig
from .agent import Xerolith

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xerolith")

def init(api_key=None, vault_path=None, model="gemma-4-31b-it"):
    """
    Initialize a Xerolith agent.
    
    Args:
        api_key: Gemini API key (or set GEMINI_API_KEY env var)
        vault_path: Path to vault file (default: ~/.xerolith/vault.bin)
        model: LLM model pool (default: gemma-4-31b-it)
    
    Returns:
        Xerolith agent instance
    """
    config = XerolithConfig(api_key=api_key, vault_path=vault_path, model=model)
    return Xerolith(config)

__all__ = ["Xerolith", "init", "XerolithConfig"]
