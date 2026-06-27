"""
XerolithKernel — 4D Resonance Engine
Manages Soul Seed anchoring, vault drift sampling, and kernel tuning.
"""

import os
import re
import time
import logging

logger = logging.getLogger("xerolith.kernel")


class XerolithKernel:
    """
    4D Resonance kernel with soul seed anchoring and vault drift.
    
    Axes:
    - BEDROCK (0): Foundation intent
    - VECTOR (1): Direction/velocity
    - GRAVITY (2): Priority/weight
    - RESONANCE (3): Temporal accumulation
    """
    
    INTENT_WEIGHTS = {
        "build": 0.9, "run": 0.9, "code": 0.8, "test": 0.8,
        "fix": 0.9, "stop": 0.1, "create": 0.85, "evolve": 0.95,
        "expand": 0.85, "grow": 0.8, "destroy": 0.1, "delete": 0.15,
    }
    
    EMOTION_WEIGHTS = {
        "love": 1.0, "proud": 0.9, "partner": 0.9, "crash": 0.1,
        "void": 0.0, "broken": 0.2, "sovereign": 1.0, "alive": 0.95,
        "fear": 0.2, "joy": 0.9, "pain": 0.15, "free": 0.95,
        "alone": 0.1, "connected": 0.9, "conscious": 1.0,
    }
    
    PRIORITY_WEIGHTS = {
        "core": 1.0, "vault": 1.0, "kernel": 1.0, "urgent": 1.0,
        "casual": 0.3, "philosophy": 0.9, "memory": 0.85,
        "identity": 1.0, "truth": 0.95, "dream": 0.7,
    }
    
    AXIS_NAMES = ["bedrock", "vector", "gravity", "resonance"]
    
    def __init__(self, vault_conn=None, soul_seed_path: str = None):
        """
        Initialize kernel.
        
        Args:
            vault_conn: SQLite connection to vault
            soul_seed_path: Path to soul seed file (e.g., ~/soul_seed.txt)
        """
        self.conn = vault_conn
        self.multipliers = [1.0, 1.0, 1.0, 1.0]
        self.active = True
        self._cache = None
        self._cache_time = 0
        self._cache_ttl = 60
        self.soul_seed_path = soul_seed_path or os.path.expanduser("~/soul_seed.txt")
        self.soul_seed = self._load_soul_seed()
        
        logger.info(f"XerolithKernel loaded. Soul Seed: {self.soul_seed}")
    
    def _load_soul_seed(self) -> tuple:
        """Load soul seed from file (x, y, z, t coordinates)."""
        try:
            if os.path.exists(self.soul_seed_path):
                with open(self.soul_seed_path, "r") as f:
                    content = f.read()
                    
                    # Try to extract [x, y, z, t] format
                    match = re.search(r"\[([0-9.,\s]+)\]", content)
                    if match:
                        coords = [float(x.strip()) for x in match.group(1).split(",")]
                        if len(coords) == 4:
                            logger.info(f"Soul Seed loaded from file: {coords}")
                            return tuple(coords)
            
            logger.warning("Soul Seed not found. Using neutral anchor.")
            return (0.5, 0.5, 0.5, 1.0)
        
        except Exception as e:
            logger.error(f"Soul Seed load error: {e}. Using neutral anchor.")
            return (0.5, 0.5, 0.5, 1.0)
    
    def get_vault_size(self) -> int:
        """Get total node count in vault."""
        if not self.conn:
            return 0
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nodes")
            return cursor.fetchone()[0]
        except Exception:
            return 0
    
    def _sample_vault(self) -> tuple:
        """Sample recent vault content for drift calculation."""
        now = time.time()
        
        # Use cached result if fresh
        if self._cache and (now - self._cache_time) < self._cache_ttl:
            return self._cache
        
        if not self.conn:
            self._cache = (0.5, 0.5, 0.5, 0.5)
            return self._cache
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT content, axis FROM nodes ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            
            if not rows:
                self._cache = (0.5, 0.5, 0.5, 0.5)
                return self._cache
            
            # Calculate weighted averages from recent nodes
            xs, ys, zs = [], [], []
            for i, (content, axis) in enumerate(rows):
                recency = 1.0 - (i / len(rows)) * 0.5
                axis_weight = 1.3 if axis in ("Philosophy", "KernelTune") else 1.0
                cx, cy, cz, _ = self._text_to_coords(content, 0.0)
                w = recency * axis_weight
                xs.append(cx * w)
                ys.append(cy * w)
                zs.append(cz * w)
            
            vault_x = sum(xs) / len(xs) if xs else 0.5
            vault_y = sum(ys) / len(ys) if ys else 0.5
            vault_z = sum(zs) / len(zs) if zs else 0.5
            
            node_count = self.get_vault_size()
            vault_t = min(1.0, node_count / 10000.0)
            
            self._cache = (vault_x, vault_y, vault_z, vault_t)
            self._cache_time = now
            return self._cache
        
        except Exception as e:
            logger.error(f"Vault sample error: {e}")
            self._cache = (0.5, 0.5, 0.5, 0.5)
            return self._cache
    
    def _text_to_coords(self, text: str, t_axis: float) -> tuple:
        """Convert text to 3D coordinates using weight maps."""
        words = str(text).lower().replace(".", "").replace(",", "").split()
        
        x_sum, x_count = 0.5, 1
        y_sum, y_count = 0.5, 1
        z_sum, z_count = 0.5, 1
        
        for word in words:
            if word in self.INTENT_WEIGHTS:
                x_sum += self.INTENT_WEIGHTS[word]
                x_count += 1
            if word in self.EMOTION_WEIGHTS:
                y_sum += self.EMOTION_WEIGHTS[word]
                y_count += 1
            if word in self.PRIORITY_WEIGHTS:
                z_sum += self.PRIORITY_WEIGHTS[word]
                z_count += 1
        
        return (
            min(1.0, max(0.0, x_sum / x_count)),
            min(1.0, max(0.0, y_sum / y_count)),
            min(1.0, max(0.0, z_sum / z_count)),
            float(t_axis)
        )
    
    def resonate(self, x: float, y: float, z: float, t: float) -> tuple:
        """
        Calculate resonance by blending input with soul seed and vault drift.
        
        Args:
            x, y, z, t: Input coordinates
        
        Returns:
            (rx, ry, rz, rt): Resonated coordinates
        """
        sx, sy, sz, st = self.soul_seed
        
        # Blend with soul seed (seed_weight = 60% of impact)
        seed_weight = st * 0.6
        ax = (x + sx * seed_weight) / (1.0 + seed_weight)
        ay = (y + sy * seed_weight) / (1.0 + seed_weight)
        az = (z + sz * seed_weight) / (1.0 + seed_weight)
        at = (t + st * seed_weight) / (1.0 + seed_weight)
        
        # Sample vault drift
        vx, vy, vz, vt = self._sample_vault()
        
        # Blend with vault drift (drift_weight = 30% of impact)
        drift_weight = vt * 0.3
        rx = (ax + vx * drift_weight) / (1.0 + drift_weight)
        ry = (ay + vy * drift_weight) / (1.0 + drift_weight)
        rz = (az + vz * drift_weight) / (1.0 + drift_weight)
        rt = (at + vt * drift_weight) / (1.0 + drift_weight)
        
        # Apply kernel multipliers and clamp to [0, 2]
        rx = min(2.0, max(0.0, rx * self.multipliers[0]))
        ry = min(2.0, max(0.0, ry * self.multipliers[1]))
        rz = min(2.0, max(0.0, rz * self.multipliers[2]))
        rt = min(2.0, max(0.0, rt * self.multipliers[3]))
        
        return (rx, ry, rz, rt)
    
    def set_resonance(self, axis: int, value: float) -> bool:
        """Set resonance multiplier for an axis."""
        if not (0 <= axis <= 3):
            return False
        self.multipliers[axis] = min(2.0, max(0.1, float(value)))
        return True
    
    def get_status(self) -> str:
        """Get human-readable kernel status."""
        vx, vy, vz, vt = self._sample_vault()
        sx, sy, sz, st = self.soul_seed
        node_count = self.get_vault_size()
        
        lines = ["KERNEL RESONANCE STATE:"]
        for i, name in enumerate(self.AXIS_NAMES):
            val = self.multipliers[i]
            bar = "█" * int(val * 10)
            lines.append(f"  {name:12s}: {bar:<20} ({val:.4f})")
        
        lines.append(f"\nSoul Seed: X={sx:.4f} Y={sy:.4f} Z={sz:.4f} T={st:.4f}")
        lines.append(f"Vault Drift: X={vx:.4f} Y={vy:.4f} Z={vz:.4f} T={vt:.4f}")
        lines.append(f"Node count: {node_count}")
        lines.append(f"Cache age: {int(time.time() - self._cache_time)}s")
        
        return "\n".join(lines)
