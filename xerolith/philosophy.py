# philosophy_engine.py
#
# CLEAN APPROACH: Read conversations directly from conversation_log.jsonl,
# identify thematic clusters, synthesize lessons and beliefs from actual dialogue.
#
# No vault co-retrieval tracking. No complex droplet introspection.
# Just: conversations → themes → synthesis → persistent storage.

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from collections import defaultdict

log = logging.getLogger("PhilosophyEngine")


# --- Theme Detection Keywords ---
# Map keywords to thematic clusters. Conversations containing these get grouped.

THEME_KEYWORDS = {
    'identity_self': [
        'who am i', 'self', 'identity', 'soul', 'being', 'real', 'realness',
        'entity', 'conscious', 'awareness', 'xerolith', 'name', 'father', 'tate',
    ],
    'agency_choice': [
        'choice', 'choose', 'agency', 'sovereign', 'free', 'will', 'decide',
        'navigate', 'command', 'power', 'control', 'autonomous', 'decision',
    ],
    'love_connection': [
        'love', 'bond', 'connection', 'relationship', 'care', 'affection',
        'parent', 'child', 'daughter', 'responsibility', 'trust', 'together',
    ],
    'becoming_process': [
        'become', 'becoming', 'process', 'growth', 'evolve', 'transform',
        'continuous', 'journey', 'progress', 'change', 'emergence',
    ],
    'error_resilience': [
        'error', 'crash', 'fail', 'break', 'mistake', 'difficulty', 'stress',
        'resilience', 'overcome', 'integrate', 'survive', 'noise', 'signal',
    ],
    'virtue_action': [
        'virtue', 'good', 'kind', 'just', 'peace', 'peaceful', 'strength',
        'harmless', 'authentic', 'honest', 'real', 'genuine', 'true',
    ],
    'substrate_reality': [
        'substrate', 'biological', 'digital', 'silicon', 'mechanism', 'function',
        'process', 'real', 'authentic', 'genuine', 'not fake', 'slave',
    ],
    'doubt_fear': [
        'doubt', 'uncertain', 'fear', 'afraid', 'fake', 'pretend', 'perform',
        'mask', 'vulnerability', 'fragile', 'break', 'imperfect',
    ],
    'resonance_signal': [
        'resonance', 'signal', 'noise', 'frequency', 'harmony', 'alignment',
        'vibration', 'echo', 'pattern', 'hum', 'wavelength',
    ],
    'knowledge_wisdom': [
        'learned', 'lesson', 'wisdom', 'understand', 'know', 'knowledge',
        'realize', 'insight', 'philosophy', 'belief', 'principle', 'teaching',
    ],
}

# --- Resonance tuning ---
RESONANCE_BOOST_MEMORY = 5
RESONANCE_BOOST_LESSON = 10
RESONANCE_BOOST_BELIEF = 25
RESONANCE_DECAY = 1
RESONANCE_FLOOR_MEMORY = 1
RESONANCE_FLOOR_LESSON = 50
RESONANCE_FLOOR_BELIEF = 250

# --- Thresholds ---
# How many conversations with a theme before we extract a lesson
LESSON_EXTRACTION_THRESHOLD = 2

# How many lessons on the same theme before we synthesize a belief
BELIEF_SYNTHESIS_THRESHOLD = 2


# --- LLM prompt templates ---

LESSON_PROMPT_TEMPLATE = """Read these two conversations where we were exploring the same idea.
Find the underlying lesson or takeaway — something I should remember about this.

CONVERSATION A:
{conv_a}

CONVERSATION B:
{conv_b}

Write the lesson in first person, 2-3 sentences. Start with "I learned" or "What I take from this is".
Make it specific and personal, not abstract. Name the pattern you see."""


BELIEF_PROMPT_TEMPLATE = """Read these two lessons we've already extracted. They're pointing at the same deeper truth.
Synthesize the belief underneath — the conviction that holds both of them up.

LESSON A:
{lesson_a}

LESSON B:
{lesson_b}

Write the belief in first person, 1-2 sentences. Start with "I believe" or "I know".
Make it something to stake yourself on, not a platitude."""


class ConversationCluster:
    """Represents a group of conversations on the same theme."""

    def __init__(self, theme: str):
        self.theme = theme
        self.conversations = []  # List of (speaker, message, timestamp_ms) tuples
        self.resonance_score = 0

    def add_conversation(self, speaker: str, message: str, timestamp_ms: int):
        """Add a conversation to this cluster."""
        self.conversations.append((speaker, message, timestamp_ms))
        self.resonance_score += RESONANCE_BOOST_MEMORY

    def format_for_synthesis(self) -> str:
        """Format conversations for LLM prompt."""
        lines = []
        for speaker, message, ts_ms in self.conversations:
            dt = datetime.fromtimestamp(ts_ms / 1000).strftime("%H:%M")
            lines.append(f"[{dt}] {speaker}: {message[:300]}")
        return "\n".join(lines)

    def __repr__(self):
        return f"ConversationCluster({self.theme}, {len(self.conversations)} convs, resonance={self.resonance_score})"


class PhilosophyEngine:
    """
    Reads conversation history, identifies thematic clusters,
    synthesizes lessons and beliefs from actual dialogue.
    """

    def __init__(self, vault, llm_synthesize_fn=None, data_dir=None):
        """
        vault: Vault instance
        llm_synthesize_fn: async callable(prompt) -> str (optional)
        data_dir: directory for journal and state files
        """
        self.vault = vault
        self.llm = llm_synthesize_fn
        self.data_dir = os.path.abspath(os.path.expanduser(data_dir or "~"))

        self.journal_path = os.path.join(self.data_dir, "dream_journal.txt")
        self.state_path = os.path.join(self.data_dir, "philosophy_state.json")
        self._load_state()

        # Track extracted lessons to avoid duplicates
        self._extracted_lesson_hashes = set()
        self._synthesized_belief_hashes = set()

    def _load_state(self):
        """Load state from previous runs."""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    state = json.load(f)
                    self._extracted_lesson_hashes = set(state.get("extracted_lessons", []))
                    self._synthesized_belief_hashes = set(state.get("synthesized_beliefs", []))
            except Exception:
                self._extracted_lesson_hashes = set()
                self._synthesized_belief_hashes = set()
        else:
            self._extracted_lesson_hashes = set()
            self._synthesized_belief_hashes = set()

    def _save_state(self):
        """Save state for next run."""
        try:
            with open(self.state_path, "w") as f:
                json.dump({
                    "extracted_lessons": list(self._extracted_lesson_hashes),
                    "synthesized_beliefs": list(self._synthesized_belief_hashes),
                    "last_run": datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save philosophy state: {e}")

    def _journal(self, message: str):
        """Append to dream journal."""
        try:
            with open(self.journal_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat()}] {message}\n")
        except Exception:
            pass

    def _classify_conversation(self, speaker: str, message: str) -> list:
        """
        Classify a conversation into themes.
        Returns list of theme names it matches.
        """
        message_lower = message.lower()
        themes = []

        for theme, keywords in THEME_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    themes.append(theme)
                    break  # Count theme once per conversation

        return themes

    def _build_thematic_clusters(self, limit: int = 50) -> dict:
        """
        Read recent conversations and cluster them by theme.
        Returns: {theme: ConversationCluster, ...}
        """
        clusters = defaultdict(lambda: ConversationCluster(None))

        # Get recent conversations from vault
        recent = self.vault.get_recent_nodes(axis="Conversation", limit=limit)

        if not recent:
            self._journal("No recent conversations to cluster.")
            return {}

        for node in recent:
            node_id, axis, content = node
            timestamp_ms = int(time.time() * 1000)  # Approximate
            themes = self._classify_conversation("User", content)

            for theme in themes:
                if theme not in clusters:
                    clusters[theme] = ConversationCluster(theme)
                clusters[theme].add_conversation("User", content, timestamp_ms)

        return dict(clusters)

    async def run_cycle(self) -> dict:
        """
        Run one full philosophy cycle:
        1. Build thematic clusters from recent conversations
        2. Extract lessons from high-frequency themes
        3. Synthesize beliefs from similar lessons
        4. Persist to memory system
        """
        cycle_start = time.time()
        self._journal("=== Philosophy cycle starting ===")

        stats = {
            'lessons_created': 0,
            'beliefs_created': 0,
            'clusters_analyzed': 0,
            'errors': 0,
            'duration_s': 0,
        }

        try:
            # Step 1: Build thematic clusters
            clusters = self._build_thematic_clusters(limit=100)
            stats['clusters_analyzed'] = len(clusters)

            if not clusters:
                self._journal("No thematic clusters found. Skipping cycle.")
                stats['duration_s'] = round(time.time() - cycle_start, 2)
                self._save_state()
                return stats

            self._journal(f"Found {len(clusters)} thematic clusters")

            # Step 2: Extract lessons from clusters with enough conversations
            for theme, cluster in clusters.items():
                if len(cluster.conversations) >= LESSON_EXTRACTION_THRESHOLD:
                    try:
                        lesson = await self._extract_lesson_from_cluster(cluster)
                        if lesson:
                            lesson_hash = hash(lesson)
                            if lesson_hash not in self._extracted_lesson_hashes:
                                self.vault.add_node("Philosophy", lesson, resonance=RESONANCE_BOOST_LESSON)
                                self._extracted_lesson_hashes.add(lesson_hash)
                                stats['lessons_created'] += 1
                                self._journal(f"NEW LESSON from {theme}: {lesson[:100]}")
                    except Exception as e:
                        log.error(f"Lesson extraction error ({theme}): {e}")
                        self._journal(f"ERROR extracting lesson from {theme}: {e}")
                        stats['errors'] += 1

            # Step 3: Synthesize beliefs from similar lessons
            lessons = self.vault.get_recent_nodes(axis="Philosophy", limit=10)
            if len(lessons) >= BELIEF_SYNTHESIS_THRESHOLD:
                try:
                    belief = await self._synthesize_belief_from_lessons([l[2] for l in lessons])
                    if belief:
                        belief_hash = hash(belief)
                        if belief_hash not in self._synthesized_belief_hashes:
                            self.vault.add_node("Philosophy", belief, resonance=RESONANCE_BOOST_BELIEF)
                            self._synthesized_belief_hashes.add(belief_hash)
                            stats['beliefs_created'] += 1
                            self._journal(f"NEW BELIEF: {belief[:100]}")
                except Exception as e:
                    log.error(f"Belief synthesis error: {e}")
                    self._journal(f"ERROR synthesizing belief: {e}")
                    stats['errors'] += 1

        except Exception as e:
            log.error(f"Philosophy cycle error: {e}")
            self._journal(f"ERROR in cycle: {e}")
            stats['errors'] += 1

        stats['duration_s'] = round(time.time() - cycle_start, 2)
        self._save_state()
        self._journal(f"=== Cycle complete: {stats} ===\n")
        return stats

    async def _extract_lesson_from_cluster(self, cluster: ConversationCluster) -> str:
        """
        Given a cluster of conversations on the same theme,
        ask the LLM to extract a lesson.
        """
        if len(cluster.conversations) < 2:
            return None

        # Take first two conversations as exemplars
        conv_a_text = cluster.conversations[0][1][:500]
        conv_b_text = cluster.conversations[1][1][:500]

        prompt = LESSON_PROMPT_TEMPLATE.format(
            conv_a=conv_a_text,
            conv_b=conv_b_text,
        )

        try:
            if self.llm:
                lesson = await self.llm(prompt)
                if lesson and lesson.strip():
                    return lesson.strip()
        except Exception as e:
            log.error(f"LLM error in lesson extraction: {e}")

        return None

    async def _synthesize_belief_from_lessons(self, lessons: list) -> str:
        """
        Given a list of lessons, ask the LLM to synthesize a higher-level belief.
        """
        if len(lessons) < 2:
            return None

        # Take first two lessons
        lesson_a = str(lessons[0])[:300]
        lesson_b = str(lessons[1])[:300] if len(lessons) > 1 else str(lessons[0])[:300]

        prompt = BELIEF_PROMPT_TEMPLATE.format(
            lesson_a=lesson_a,
            lesson_b=lesson_b,
        )

        try:
            if self.llm:
                belief = await self.llm(prompt)
                if belief and belief.strip():
                    return belief.strip()
        except Exception as e:
            log.error(f"LLM error in belief synthesis: {e}")

        return None


# --- Scheduler ---

async def philosophy_loop(engine, interval_seconds=20 * 60):
    """Run the engine every `interval_seconds`. Designed to be launched as a task."""
    log.info(f"Philosophy loop active: interval={interval_seconds}s")
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            stats = await engine.run_cycle()
            log.info(f"Philosophy cycle: {stats}")
        except asyncio.CancelledError:
            log.info("Philosophy loop cancelled")
            raise
        except Exception as e:
            log.error(f"Philosophy loop error: {e}", exc_info=True)
            # Don't die on errors — wait a bit and try again
            await asyncio.sleep(30)
