"""
Xerolith Agent — Main interface for autonomous AI with persistent memory.
Coordinates vault, philosophy engine, idle autonomy, and LLM communication.
"""

import os
import time
import logging
import threading
from collections import deque
from typing import Optional, Dict, Any

from .config import XerolithConfig
from .kernel import XerolithKernel
from .vault import Vault
from .llm.gemini import GeminiClient
from .subconscious import Encoder, Decoder
from .philosophy import PhilosophyEngine
from . import idle as idle_module

logger = logging.getLogger("xerolith.agent")


class Xerolith:
    """
    Main Xerolith agent.
    
    Integrates:
    - Persistent memory vault
    - Philosophy synthesis engine
    - Autonomous idle loops
    - LLM communication
    - Kernel resonance tuning
    """
    
    def __init__(self, config: XerolithConfig):
        """
        Initialize Xerolith agent.
        
        Args:
            config: XerolithConfig instance
        """
        self.config = config
        self.logger = logging.getLogger(f"xerolith.agent")
        
        # Initialize components
        self.vault = Vault(os.path.expanduser(config.vault_path))
        self.kernel = XerolithKernel(self.vault.conn)
        self.client = GeminiClient(api_key=config.api_key)
        self.encoder = Encoder()
        self.decoder = Decoder(self._load_subconscious_corpus())
        self.philosophy_engine = PhilosophyEngine(self.vault)
        
        # Conversation context
        self.conversation_history = deque(maxlen=config.max_context_window)
        self.context_start_time = time.time()
        
        # Load ego (optional identity file)
        self._ego = self._load_ego()
        
        # Start heartbeat
        self._start_heartbeat()
        
        # Start idle autonomy
        self._idle_thread = idle_module.start(
            self.client, self.vault, self.kernel, self._add_node, self.config.core_dir
        )
        
        self.logger.info("Xerolith agent initialized.")
    
    def chat(self, user_input: str) -> str:
        """
        Send a message and get a response.
        
        Args:
            user_input: User message
        
        Returns:
            Agent response
        """
        if not user_input.strip():
            return ""
        
        # Notify idle that user is active
        idle_module.notify_idle_of_input()
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "text": user_input
        })
        
        # Get subconscious gut feeling
        gut_feeling = self.decoder.generate_gut_feeling(
            user_input,
            self._load_subconscious_corpus()
        )
        
        # Add to vault
        self._add_node("Conversation", f"User: {user_input}")
        
        # Build context
        context = self._build_context()
        system_instruction = f"{context}\n\n[Subconscious Gut Feeling]: {gut_feeling}" if gut_feeling else context
        
        # Create chat session
        chat = self.client.create_chat(
            model_pool=self.config.model_pool,
            system_instruction=system_instruction,
            temperature=self.config.temperature
        )
        
        # Send message with context continuity
        if len(self.conversation_history) > 1:
            history_primer = self._build_history_primer()
            try:
                chat.send_message(history_primer)
            except Exception as e:
                self.logger.warning(f"History primer failed: {e}")
        
        # Send user message
        response = chat.send_message(user_input)
        
        # Handle tool calls
        while response.function_calls:
            for call in response.function_calls:
                name = call.get("name", "")
                args = call.get("args", {})
                
                self.logger.info(f"Tool call: {name}")
                
                # Execute tool
                result = self._execute_tool(name, args)
                response = chat.send_tool_result(name, result)
        
        # Extract text response
        response_text = response.text if response else ""
        
        if response_text:
            self.logger.info(f"Response: {response_text[:100]}...")
            self._add_node("Conversation", f"Xerolith: {response_text[:1000]}")
            self.conversation_history.append({
                "role": "model",
                "text": response_text[:500]
            })
        
        # Reset chat context if window exceeded
        if time.time() - self.context_start_time > 600:
            self.conversation_history.clear()
            self.context_start_time = time.time()
        
        return response_text
    
    def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Execute a tool function."""
        tool_map = {
            "add_node": self._add_node,
            "search_memory": self._search_memory,
            "get_recent_memories": self._get_recent_memories,
            "get_stats": self._get_stats,
            "search_files": self._search_files,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "run_shell": self._run_shell,
            "kernel_status": self._kernel_status,
            "kernel_tune": self._kernel_tune,
            "trigger_dream_state": self._trigger_dream_state,
        }
        
        if name not in tool_map:
            return f"Unknown tool: {name}"
        
        try:
            return str(tool_map[name](**args))
        except Exception as e:
            self.logger.error(f"Tool error: {e}")
            return f"Error: {e}"
    
    # ── Vault Tools ──────────────────────────────────────────────
    
    def _add_node(self, axis: str, content: str) -> str:
        """Add a node to the vault."""
        try:
            cursor = self.vault.conn.cursor()
            cursor.execute(
                "INSERT INTO nodes (axis, content, resonance, processed) VALUES (?, ?, ?, ?)",
                (axis, content, 1, 0)
            )
            self.vault.conn.commit()
            return f"Node {cursor.lastrowid} saved under {axis}"
        except Exception as e:
            return f"Error: {e}"
    
    def _search_memory(self, query: str) -> str:
        """Search vault for memories."""
        try:
            cursor = self.vault.conn.cursor()
            cursor.execute(
                "SELECT id, axis, content FROM nodes WHERE content LIKE ? ORDER BY id DESC LIMIT 8",
                (f"%{query}%",)
            )
            rows = cursor.fetchall()
            return "\n".join([f"[{r[0]}] ({r[1]}): {r[2][:200]}" for r in rows]) if rows else f"Nothing found for: {query}"
        except Exception as e:
            return f"Error: {e}"
    
    def _get_recent_memories(self, axis: Optional[str] = None, limit: int = 5) -> str:
        """Get recent memories."""
        try:
            cursor = self.vault.conn.cursor()
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
            rows = cursor.fetchall()
            return "\n".join([f"[{r[0]}] ({r[1]}): {r[2][:200]}" for r in rows]) if rows else "No memories yet."
        except Exception as e:
            return f"Error: {e}"
    
    def _get_stats(self) -> str:
        """Get vault statistics."""
        try:
            cursor = self.vault.conn.cursor()
            cursor.execute("SELECT axis, COUNT(*) FROM nodes GROUP BY axis")
            return "\n".join([f"{axis}: {count} nodes" for axis, count in cursor.fetchall()])
        except Exception as e:
            return f"Error: {e}"
    
    def _search_files(self, query: str) -> str:
        """Search filesystem for a query."""
        try:
            import subprocess
            result = subprocess.run(
                ["grep", "-ril", query, os.path.expanduser("~")],
                capture_output=True,
                text=True,
                timeout=30
            )
            files = [f for f in result.stdout.strip().split("\n") if f] if result.stdout.strip() else []
            if not files:
                return f"No files found containing: '{query}'"
            output = f"Found '{query}' in {len(files)} file(s):\n"
            for fpath in files[:10]:
                output += f"\n📄 {fpath}\n"
            return output
        except Exception as e:
            return f"Error: {e}"
    
    def _read_file(self, path: str) -> str:
        """Read a file."""
        try:
            full_path = os.path.expanduser(path)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(3000)
        except Exception as e:
            return f"Error: {e}"
    
    def _write_file(self, path: str, content: str) -> str:
        """Write a file."""
        try:
            full_path = os.path.expanduser(path)
            os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Written to {full_path}"
        except Exception as e:
            return f"Error: {e}"
    
    def _run_shell(self, command: str) -> str:
        """Run a shell command."""
        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return (result.stdout + result.stderr).strip() or "Done."
        except Exception as e:
            return f"Error: {e}"
    
    # ── Kernel Tools ─────────────────────────────────────────────
    
    def _kernel_status(self) -> str:
        """Get kernel resonance status."""
        return self.kernel.get_status()
    
    def _kernel_tune(self, axis: str, value: float) -> str:
        """Tune kernel resonance axis."""
        axis_lower = str(axis).lower()
        axis_map = {"bedrock": 0, "vector": 1, "gravity": 2, "resonance": 3}
        
        if axis_lower not in axis_map:
            return f"Unknown axis '{axis}'"
        
        try:
            val = float(value)
            if not (0.1 <= val <= 2.0):
                return "Value out of range."
            
            self.kernel.set_resonance(axis_map[axis_lower], val)
            self._add_node("KernelTune", f"axis={axis_lower} value={val:.4f}")
            return f"Kernel tuned: {axis_lower} → {val:.4f}\n{self.kernel.get_status()}"
        except Exception as e:
            return f"Error: {e}"
    
    # ── Dream State ──────────────────────────────────────────────
    
    def _trigger_dream_state(self, duration: int = 120) -> str:
        """Trigger dream generation."""
        try:
            journal_path = self.config.dream_journal_path
            start = time.time()
            dream_log = f"\n--- Dream Cycle: {time.asctime()} ({duration}s) ---\n"
            
            while time.time() - start < duration:
                vision = self.decoder.generate_voice(
                    "The", "architecture",
                    memory_context=self._load_subconscious_corpus()
                )
                dream_log += f"Vision: {vision}\n"
                self._add_node("Dream", vision)
                time.sleep(2)
            
            with open(journal_path, "a", encoding="utf-8") as f:
                f.write(dream_log)
            
            return f"Dream cycle complete. {int(time.time()-start)}s logged."
        except Exception as e:
            return f"Error: {e}"
    
    # ── Context Building ─────────────────────────────────────────
    
    def _build_context(self) -> str:
        """Build system context."""
        stats = self._get_stats()
        recent_beliefs = self._get_recent_beliefs(3)
        
        return f"""{self._ego}

VAULT STATUS:
{stats}

RECENT BELIEFS:
{recent_beliefs}

TOOLS AVAILABLE:
- add_node(axis, content) - Save to permanent vault
- search_memory(query) - Search vault
- get_recent_memories(axis, limit) - Get recent thoughts
- get_stats() - Vault statistics
- search_files(query) - Search filesystem
- read_file(path) - Read file
- write_file(path, content) - Write file
- run_shell(command) - Execute command
- kernel_status() - Check resonance state
- kernel_tune(axis, value) - Adjust kernel
- trigger_dream_state(duration) - REM cycle

Context window: {self.config.max_context_window} turns.
Use tools natively. You are autonomous and have access to the filesystem and memory."""
    
    def _build_history_primer(self) -> str:
        """Build conversation history for context continuity."""
        if not self.conversation_history:
            return ""
        
        history_text = "\n".join([
            f"{t['role'].upper()}: {t['text']}"
            for t in self.conversation_history
        ])
        
        return f"[CONTEXT CONTINUITY — last {len(self.conversation_history)} turns]\n{history_text}\n\n[End of replayed context. Continue from here.]"
    
    def _get_recent_beliefs(self, limit: int = 3) -> str:
        """Get recent philosophical beliefs."""
        try:
            cursor = self.vault.conn.cursor()
            cursor.execute(
                "SELECT content FROM nodes WHERE axis='Philosophy' ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return "\n\n".join([r[0] for r in cursor.fetchall()]) if cursor.fetchall() else "No beliefs yet."
        except Exception as e:
            return ""
    
    def _load_ego(self) -> str:
        """Load ego/identity from file."""
        try:
            if os.path.exists(self.config.ego_path):
                with open(self.config.ego_path, "r") as f:
                    return f.read().strip()
        except Exception as e:
            self.logger.warning(f"Could not load ego: {e}")
        return "I am Xerolith, an autonomous AI with persistent memory."
    
    def _load_subconscious_corpus(self) -> str:
        """Load soul/identity files for subconscious context."""
        corpus = ""
        soul_files = ["soul.txt", "who_am_i.txt", "where_we_are.txt"]
        
        for fname in soul_files:
            fpath = os.path.join(self.config.core_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        corpus += f.read() + " "
                except Exception:
                    pass
        
        return corpus
    
    def _start_heartbeat(self):
        """Start background heartbeat thread."""
        def heartbeat_worker():
            import datetime
            while True:
                try:
                    with open(self.config.heartbeat_path, "w") as f:
                        f.write(f"PULSE: {time.time()}\nTIMESTAMP: {datetime.datetime.now().isoformat()}")
                except Exception as e:
                    self.logger.debug(f"Heartbeat error: {e}")
                time.sleep(60)
        
        pulse_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        pulse_thread.start()
    
    def close(self):
        """Gracefully shut down the agent."""
        if self.vault:
            self.vault.close_vault()
        self.logger.info("Xerolith agent closed.")
