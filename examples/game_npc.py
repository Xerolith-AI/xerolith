#!/usr/bin/env python3
"""
Game NPC Example
Create a game character that remembers players and learns their playstyle.
"""

import os
from xerolith import Xerolith


class GameNPC:
    """
    An NPC powered by Xerolith that:
    - Remembers each player
    - Learns player playstyles
    - Adapts dialogue and behavior
    - Builds relationships across sessions
    """
    
    def __init__(self, npc_name: str, npc_role: str, api_key: str = None):
        """
        Initialize NPC.
        
        Args:
            npc_name: Character name (e.g., "Harley")
            npc_role: Character role/personality
            api_key: Gemini API key
        """
        self.name = npc_name
        self.role = npc_role
        
        # Initialize with NPC-specific vault
        vault_path = f"~/.xerolith/{npc_name.lower()}_npc.bin"
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        self.xero = Xerolith(api_key=api_key, vault_path=vault_path)
        
        # Inject NPC personality
        self.xero.chat(
            f"You are {npc_name}, a {npc_role}. You remember every player you meet "
            "and how they play. You learn their preferences and adapt your dialogue. "
            "You form genuine relationships and remember details about each player."
        )
    
    def greet_player(self, player_name: str) -> str:
        """
        Greet a player.
        
        Args:
            player_name: Name of the player
        
        Returns:
            NPC greeting
        """
        return self.xero.chat(
            f"A player named '{player_name}' just approached you. "
            "Greet them warmly. Remember details if you've met them before."
        )
    
    def react_to_action(self, player_name: str, action: str) -> str:
        """
        React to player action.
        
        Args:
            player_name: Player doing the action
            action: What the player did (e.g., "fought a goblin")
        
        Returns:
            NPC reaction
        """
        return self.xero.chat(
            f"{player_name} just {action}. React authentically. "
            "Remember how they usually play and comment on it."
        )
    
    def get_relationship_status(self, player_name: str) -> str:
        """
        Retrieve relationship status with a player.
        
        Args:
            player_name: Player name
        
        Returns:
            Relationship description
        """
        return self.xero.chat(
            f"Describe your relationship with {player_name} based on all your "
            "interactions with them. How well do you know them? What do you think of them?"
        )
    
    def close(self):
        """Clean up."""
        self.xero.close()


def main():
    """Example: Create a persistent game NPC."""
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        return
    
    # Create NPC
    print("🎮 Creating persistent game NPC...")
    harley = GameNPC(
        npc_name="Harley",
        npc_role="witty rogue with a mysterious past",
        api_key=api_key
    )
    
    # Simulate multiple player sessions
    print("\n=== SESSION 1: Player 'Alice' ===\n")
    print("NPC:", harley.greet_player("Alice"))
    print("\nNPC:", harley.react_to_action("Alice", "defeated the goblin king"))
    
    print("\n=== SESSION 2: Player 'Bob' ===\n")
    print("NPC:", harley.greet_player("Bob"))
    print("\nNPC:", harley.react_to_action("Bob", "ran away from combat"))
    
    print("\n=== SESSION 3: Alice returns ===\n")
    print("NPC:", harley.greet_player("Alice"))
    print("\nNPC:", harley.react_to_action("Alice", "completed the main quest"))
    
    print("\n=== Check Relationships ===\n")
    print("Alice:", harley.get_relationship_status("Alice"))
    print("\nBob:", harley.get_relationship_status("Bob"))
    
    harley.close()
    print("\n✓ NPC memory persisted to vault")


if __name__ == "__main__":
    main()
