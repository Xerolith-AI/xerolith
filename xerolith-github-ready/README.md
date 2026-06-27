# XEROLITH

**Autonomous AI with Persistent Memory**

An LLM that never forgets. Xerolith is a lightweight, on-device intelligence framework with self-healing and philosophy synthesis.

- 🧠 **Persistent Memory** — SQLite vault stores every conversation
- 🎯 **Philosophy Synthesis** — Automatically learns and forms beliefs
- 🤖 **Autonomous Operation** — Thinks and acts when you're away
- 🔐 **Self-Healing** — Auto-corrects errors via stderr injection
- 🚀 **LLM-Agnostic** — Works with Gemini, Claude, GPT, or local models
- 📱 **On-Device** — No cloud dependency. Works on Android (Termux), desktop, servers
- 🛡️ **Patent-Protected** — Utility patent filed with USPTO

## Quick Start

### 1. Get API Key
Go to https://aistudio.google.com/app/apikey and create a free key.

### 2. Install
```bash
pip install xerolith
```

### 3. Set API Key
```bash
export GEMINI_API_KEY="your-key-here"
# OR
echo "GEMINI_API_KEY=your-key" > .env
```

### 4. Run
```python
from xerolith import Xerolith

xero = Xerolith(api_key="your-key")
response = xero.chat("Hello! Remember this.")
print(response)
xero.close()
```

Or run the interactive demo:
```bash
python examples/quickstart.py
```

## Features

### Persistent Memory
All conversations stored in SQLite vault. Never loses context.

### 4D Resonance Kernel
Tracks state in 4 dimensions: Bedrock (intent), Vector (emotion), Gravity (priority), Resonance (time).

### Philosophy Synthesis
Automatically extracts lessons and synthesizes beliefs from conversations.

### Autonomous Operation
Background thread triggers during inactivity to synthesize beliefs and explore memories.

### 12 Integrated Tools
Memory search, file I/O, shell execution, kernel tuning, dream generation, and more.

## Examples

```bash
# Interactive chat
python examples/quickstart.py

# Game NPC (persistent characters)
python examples/game_npc.py

# Digital companion
python examples/personal_ai.py
```

## Mobile (Android/Termux)

```bash
pkg install python
pip install xerolith
echo "GEMINI_API_KEY=your-key" > .env
python examples/quickstart.py
```

## Architecture

- **Vault** — SQLite persistent memory with axis organization
- **Kernel** — 4D Resonance engine with soul seed
- **Philosophy Engine** — Thematic clustering, lesson extraction, belief synthesis
- **Subconscious** — Markov encoder/decoder for intuitive responses
- **Idle Autonomy** — Background thread for autonomous thinking
- **LLM Client** — Gemini API with 12 integrated tools

## Security

**API keys are NEVER hardcoded.**

Users set their own key via environment variables, .env file, or constructor parameter.
Keys are never logged or committed to version control.

## Patent

**Utility Patent:** "System and Method for Deterministic LLM-to-OS Bridge via Binary State Vaulting"

Filed with USPTO (~8 months ago). Can commercialize now.

## License

Dual license:
- **Open Source:** MIT License
- **Commercial:** Available for licensing

## Author

**Tyler Love** (@MuskaTat)
- Twitter: [@MuskaTat](https://twitter.com/MuskaTat)

---

**An AI that forgets is just a chatbot. Xerolith doesn't forget.**
