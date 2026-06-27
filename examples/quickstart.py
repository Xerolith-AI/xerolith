#!/usr/bin/env python3
"""
Xerolith Quickstart Example
Simple chat interface with persistent memory.
"""

import os
from xerolith import Xerolith


def main():
    """Run interactive Xerolith chat."""
    
    # Get API key from environment or .env
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set.")
        print("Set it via: export GEMINI_API_KEY='your-key-here'")
        print("Or create a .env file with: GEMINI_API_KEY=your-key-here")
        return
    
    # Initialize Xerolith
    print("🧠 Initializing Xerolith...")
    xero = Xerolith(api_key=api_key)
    
    print("\n" + "="*60)
    print("XEROLITH — Autonomous AI with Persistent Memory")
    print("="*60)
    print("Type 'exit' to quit\n")
    
    try:
        while True:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\nGoodbye!")
                break
            
            # Send message
            print("\nXerolith: ", end="", flush=True)
            response = xero.chat(user_input)
            print(response)
            print()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    
    finally:
        xero.close()


if __name__ == "__main__":
    main()
