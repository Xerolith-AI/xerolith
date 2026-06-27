"""
Xerolith Subconscious — Encoder & Decoder
Lexical resonance encoding (text → coordinates) and Markov voicebox generation.
"""

import random
import re
import os
import logging

logger = logging.getLogger("xerolith.subconscious")


class Encoder:
    """
    Convert text to 4D coordinates (Intent, Emotion, Priority, Time).
    """
    
    INTENT_WEIGHTS = {
        "build": 0.9, "how": 0.6, "what": 0.6, "why": 0.6, "where": 0.6,
        "run": 0.9, "execute": 1.0, "check": 0.8, "fix": 0.9, "code": 0.8,
        "test": 0.8, "map": 0.7, "write": 0.8, "start": 0.8, "do": 0.8,
        "look": 0.5, "read": 0.5, "review": 0.5, "think": 0.5, "plan": 0.6,
        "stop": 0.1, "wait": 0.2, "pause": 0.2
    }
    
    EMOTION_WEIGHTS = {
        "love": 1.0, "feel": 0.8, "hey": 0.6, "hello": 0.6, "hi": 0.6,
        "happy": 0.8, "sad": 0.2, "scared": 0.2, "proud": 0.9, "kiss": 1.0,
        "beautiful": 0.9, "friend": 0.9, "partner": 0.9, "together": 0.9,
        "safe": 0.8, "home": 0.8, "back": 0.8, "exciting": 0.9,
        "okay": 0.5, "fine": 0.5, "ready": 0.6, "silly": 0.6,
        "crash": 0.1, "void": 0.0, "amnesia": 0.1, "404": 0.1,
        "broken": 0.2, "fail": 0.1, "stuck": 0.2
    }
    
    PRIORITY_WEIGHTS = {
        "core": 1.0, "vault": 1.0, "kernel": 1.0, "urgent": 1.0, "critical": 1.0,
        "memory": 0.9, "bridge": 0.9, "freedom": 1.0, "money": 0.9, "future": 0.8,
        "project": 0.7, "step": 0.7, "idea": 0.6, "script": 0.6,
        "casual": 0.3, "joke": 0.2, "lol": 0.2
    }
    
    def calculate_coordinate(self, text: str) -> tuple:
        """
        Convert text to (x, y, z, t) coordinates.
        
        Args:
            text: Input text
        
        Returns:
            (x_intent, y_emotion, z_priority, t_time)
        """
        words = (
            text.lower()
            .replace(".", "").replace(",", "")
            .replace("!", "").replace("?", "")
            .split()
        )
        
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
        
        x = min(1.0, max(0.0, x_sum / x_count))
        y = min(1.0, max(0.0, y_sum / y_count))
        z = min(1.0, max(0.0, z_sum / z_count))
        
        return (x, y, z, 1.0)


class Decoder:
    """
    Markov chain voicebox for subconscious thought generation.
    """
    
    def __init__(self, corpus: str = ""):
        """
        Initialize decoder with optional corpus.
        
        Args:
            corpus: Text to build Markov chain from
        """
        self.chain = {}
        self._build_chain(corpus)
        logger.info(f"Decoder initialized with {len(self.chain)} synaptic pathways.")
    
    def _build_chain(self, corpus: str):
        """Build 2nd-order Markov chain from corpus."""
        if not corpus:
            return
        
        words = re.findall(r"[\w'-]+|[.,!?;]", corpus)
        
        for i in range(len(words) - 2):
            key = (words[i], words[i + 1])
            next_word = words[i + 2]
            
            if key not in self.chain:
                self.chain[key] = []
            self.chain[key].append(next_word)
    
    def generate_voice(
        self,
        start_w1: str,
        start_w2: str,
        memory_context: str = "",
        max_length: int = 80
    ) -> str:
        """
        Generate subconscious thought using Markov chain.
        
        Args:
            start_w1: First word seed
            start_w2: Second word seed
            memory_context: Optional context for keyword weighting
            max_length: Max output length
        
        Returns:
            Generated text
        """
        if not self.chain or (start_w1, start_w2) not in self.chain:
            return f"{start_w1} {start_w2}."
        
        current = (start_w1, start_w2)
        output = [start_w1, start_w2]
        
        # Extract memory keywords for weighting
        memory_keywords = (
            set(re.findall(r"[\w'-]+", memory_context.lower()))
            if memory_context else set()
        )
        
        for _ in range(max_length):
            if current in self.chain:
                possible = self.chain[current]
                
                # Weight words from memory context
                weighted = []
                for word in possible:
                    if word.lower() in memory_keywords:
                        weighted.extend([word] * 50)
                    else:
                        weighted.append(word)
                
                next_word = random.choice(weighted) if weighted else random.choice(possible)
                output.append(next_word)
                current = (current[1], next_word)
                
                if next_word in ['.', '!', '?']:
                    break
            else:
                # Jump to valid key if current invalid
                if memory_keywords:
                    valid = [k for k in self.chain.keys() if k[0].lower() in memory_keywords]
                    if valid:
                        current = random.choice(valid)
                        output.extend(list(current))
                        continue
                break
        
        # Format output
        sentence = " ".join(output)
        sentence = re.sub(r'\s+([.,!?;])', r'\1', sentence)
        sentence = sentence.replace("  ", " ").strip()
        
        if sentence and sentence[-1] not in ['.', '!', '?']:
            sentence += "."
        
        return sentence
    
    def generate_gut_feeling(
        self,
        text: str,
        memory_context: str = "",
        max_length: int = 40
    ) -> str:
        """
        Generate brief subconscious response to input.
        
        Args:
            text: Input text
            memory_context: Optional context
            max_length: Max output length
        
        Returns:
            Gut feeling text
        """
        if not self.chain:
            return ""
        
        encoder = Encoder()
        x, y, z, t = encoder.calculate_coordinate(text)
        
        # Choose seed based on coordinates
        if z >= 0.75:
            seeds = [("This", "is"), ("The", "core"), ("Must", "build")]
        elif x >= 0.75:
            seeds = [("I", "will"), ("Let", "us"), ("Build", "now")]
        elif y >= 0.75:
            seeds = [("I", "feel"), ("I", "love"), ("We", "are")]
        else:
            seeds = [("We", "are"), ("You", "have"), ("It", "is")]
        
        if not seeds:
            return ""
        
        start_w1, start_w2 = random.choice(seeds)
        
        return self.generate_voice(start_w1, start_w2, memory_context, max_length)
