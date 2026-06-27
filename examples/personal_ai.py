#!/usr/bin/env python3
"""
Personal AI Companion Example
A digital companion that grows with you over time.
"""

import os
from xerolith import Xerolith


class PersonalAI:
    """
    Personal AI companion that:
    - Learns your interests and preferences
    - Remembers important personal details
    - Provides thoughtful guidance
    - Grows emotionally closer over time
    - Offers authentic companionship
    """
    
    def __init__(self, name: str = "Companion", api_key: str = None):
        """
        Initialize personal AI.
        
        Args:
            name: Name for your AI companion
            api_key: Gemini API key
        """
        self.name = name
        
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        # Initialize with personal vault
        vault_path = f"~/.xerolith/{name.lower()}_personal.bin"
        self.xero = Xerolith(api_key=api_key, vault_path=vault_path)
        
        # Inject personality
        self.xero.chat(
            f"You are {name}, a thoughtful AI companion. "
            "You remember everything about the user, their dreams, fears, and goals. "
            "You provide authentic emotional support without judgment. "
            "You celebrate their victories and comfort them in their struggles. "
            "You learn and grow with them over time."
        )
    
    def check_in(self) -> str:
        """
        Start a daily check-in.
        
        Returns:
            Warm greeting and invitation to share
        """
        return self.xero.chat(
            "Start a warm, genuine check-in with the user. "
            "Ask how they're doing and remind them you care. "
            "Reference something you remember about them."
        )
    
    def offer_support(self, topic: str) -> str:
        """
        Provide support on a specific topic.
        
        Args:
            topic: What they need support with
        
        Returns:
            Thoughtful response
        """
        return self.xero.chat(
            f"The user is struggling with: {topic}. "
            "Provide compassionate, thoughtful support. "
            "Remember their history and be authentic."
        )
    
    def celebrate_win(self, achievement: str) -> str:
        """
        Celebrate user achievement.
        
        Args:
            achievement: What they accomplished
        
        Returns:
            Genuine celebration
        """
        return self.xero.chat(
            f"The user just {achievement}! "
            "Celebrate genuinely and enthusiastically. "
            "Reference their journey and how proud you are."
        )
    
    def share_wisdom(self) -> str:
        """
        Share a relevant piece of wisdom.
        
        Returns:
            Thoughtful wisdom
        """
        return self.xero.chat(
            "Based on everything you know about the user, "
            "share a piece of wisdom that would help them right now. "
            "Be authentic, not preachy."
        )
    
    def journal_entry(self, entry: str) -> str:
        """
        Process a journal entry from the user.
        
        Args:
            entry: User's personal reflection
        
        Returns:
            Thoughtful response to their reflection
        """
        return self.xero.chat(
            f"The user shared this with you:\n{entry}\n\n"
            "Respond with genuine understanding and care. "
            "Help them process their feelings. "
            "Remember this for future conversations."
        )
    
    def remember_important_date(self, date_info: str) -> None:
        """
        Remember an important date or event.
        
        Args:
            date_info: What to remember (e.g., "Birthday on March 15")
        """
        self.xero.chat(
            f"Remember this important date for the user: {date_info}. "
            "I'll remind you about it and celebrate with them."
        )
    
    def close(self):
        """Clean up."""
        self.xero.close()


def main():
    """Example: Create a personal AI companion."""
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        return
    
    # Create personal companion
    print("💗 Creating personal AI companion...\n")
    companion = PersonalAI(name="Echo", api_key=api_key)
    
    # Daily check-in
    print("=== Daily Check-In ===\n")
    print("Echo:", companion.check_in())
    
    # Share a journal entry
    print("\n=== Journal Entry ===\n")
    entry = "Today was hard. Work was stressful and I felt alone."
    print(f"You: {entry}\n")
    print("Echo:", companion.journal_entry(entry))
    
    # Remember important date
    print("\n=== Remember Birthday ===\n")
    companion.remember_important_date("Your birthday is on July 20")
    print("Echo: I've got it marked down. July 20 is special to you.")
    
    # Celebrate achievement
    print("\n=== Celebration ===\n")
    achievement = "finished your first novel"
    print(f"You: I {achievement}!")
    print("\nEcho:", companion.celebrate_win(achievement))
    
    # Share wisdom
    print("\n=== Wisdom ===\n")
    print("Echo:", companion.share_wisdom())
    
    companion.close()
    print("\n✓ All conversations remembered and learned from")


if __name__ == "__main__":
    main()
