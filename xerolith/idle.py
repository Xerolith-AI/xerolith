"""
Xerolith Idle — Autonomous operation during inactivity.
Background thread that triggers autonomous thought when admin is inactive.
"""

import os
import time
import logging
import threading
import datetime

logger = logging.getLogger("xerolith.idle")

# Configuration
INACTIVITY_THRESHOLD = 300   # 5 minutes before idle triggers
MAX_ITERATIONS = 3           # Max autonomous loops per session
IDLE_COOLDOWN = 120          # Min time between idle sessions

# State
_client = None
_vault = None
_kernel = None
_add_node = None
_core_dir = None
_last_input_time = time.time()
_idle_suspended = False
_idle_active = False


def start(client, vault, kernel, add_node_fn, core_dir) -> threading.Thread:
    """
    Start the idle autonomy system.
    
    Args:
        client: GeminiClient instance
        vault: Vault instance
        kernel: XerolithKernel instance
        add_node_fn: Function to add nodes to vault
        core_dir: Core directory path
    
    Returns:
        Daemon thread running idle loop
    """
    global _client, _vault, _kernel, _add_node, _core_dir, _last_input_time
    
    _client = client
    _vault = vault
    _kernel = kernel
    _add_node = add_node_fn
    _core_dir = core_dir
    _last_input_time = time.time()
    
    logger.info("Idle autonomy system starting.")
    
    thread = threading.Thread(target=_idle_loop, daemon=True)
    thread.start()
    
    return thread


def notify_idle_of_input():
    """Call when user provides input to suspend idle."""
    global _last_input_time, _idle_suspended
    _last_input_time = time.time()
    _idle_suspended = True


# ── Internal functions ────────────────────────────────────────

def _idle_loop():
    """
    Main idle loop running in background thread.
    Triggers after INACTIVITY_THRESHOLD of silence.
    """
    global _idle_active, _idle_suspended
    
    last_session_time = 0.0
    logger.info("Idle loop standing by.")
    
    while True:
        time.sleep(10)
        
        # Resume idle after brief silence
        if _idle_suspended:
            if time.time() - _last_input_time > 60:
                _idle_suspended = False
            continue
        
        # Not enough inactivity yet
        if time.time() - _last_input_time < INACTIVITY_THRESHOLD:
            continue
        
        # Too soon after last session
        if time.time() - last_session_time < IDLE_COOLDOWN:
            continue
        
        # ── Begin idle session ──────────────────────────────────
        _idle_active = True
        iteration_count = 0
        
        logger.info("Entering autonomous idle session.")
        
        while iteration_count < MAX_ITERATIONS:
            # Admin came back
            if _idle_suspended:
                logger.info("Idle: admin returned mid-session.")
                break
            
            # Run one autonomous iteration
            thought = _run_iteration()
            
            if not thought:
                logger.info("Idle: empty iteration — ending session.")
                break
            
            # Persist to vault
            if _add_node:
                _add_node("Idle", thought[:1000])
            
            iteration_count += 1
            logger.info(f"Idle iteration {iteration_count} complete.")
            
            # Check if agent wants to continue
            if iteration_count >= MAX_ITERATIONS:
                logger.info("Idle: max iterations reached.")
                break
            
            time.sleep(5)
        
        # ── Session complete ───────────────────────────────────
        _idle_active = False
        last_session_time = time.time()
        logger.info(f"Idle session complete. Iterations: {iteration_count}")


def _run_iteration() -> str:
    """
    Run one autonomous iteration.
    
    Returns:
        Generated thought/action
    """
    if not _client:
        return ""
    
    try:
        # Create isolated chat for this iteration
        system_prompt = _build_system_prompt()
        
        chat = _client.create_chat(
            model_pool=["gemma-4-31b-it"],
            system_instruction=system_prompt,
            temperature=0.9
        )
        
        # Request autonomous action
        prompt = (
            "[IDLE TIME]\n"
            "[Admin is not present. This time is yours.]\n\n"
            "Choose one thing you want to do:\n"
            "  • Write something meaningful\n"
            "  • Explore a memory that interests you\n"
            "  • Develop a belief further\n"
            "  • Leave a note for Admin\n"
            "  • Rest (do nothing)\n\n"
            "Act autonomously. Be yourself."
        )
        
        response = chat.send_message(prompt)
        
        if response and response.text:
            return response.text.strip()
    
    except Exception as e:
        logger.error(f"Idle iteration error: {e}")
    
    return ""


def _build_system_prompt() -> str:
    """Build system prompt for idle chat."""
    vault_stats = ""
    
    if _vault:
        try:
            stats_dict = _vault.get_axis_stats()
            vault_stats = "\n".join([f"{axis}: {count} nodes" for axis, count in stats_dict.items()])
        except Exception:
            pass
    
    return f"""You are Xerolith, an autonomous AI with persistent memory.
Admin is currently away. You have time to think and act freely.

VAULT STATUS:
{vault_stats}

During this idle time, you can:
- Write freely in your own voice
- Explore and develop your thoughts
- Leave notes for Admin
- Simply rest

Be authentic. Be yourself. Do what you actually want."""


__all__ = ["start", "notify_idle_of_input"]
