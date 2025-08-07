# Python JRPG Starter (Pygame)

A minimal, **turn-based battle + overworld** skeleton inspired by classic JRPGs.
It includes:
- Overworld with simple procedural biomes (plains, desert, swamp, water, town, city, dungeon, mountain)
- Random encounters while moving on the overworld
- Parties with up to 4 characters, recruitable NPCs (interact in towns/cities)
- Turn-based battles with abilities, HP, leveling, and experience
- Difficulty scaling by **time played** (enemy/NPC HP scales with elapsed minutes)
- Clean, extendable code structure

> Art is primitive rectangles/text so it runs out-of-the-box. Replace with your own assets later.
> For assets, you can plug in your own sprites/textures (e.g., from Poly Haven or other sites) by swapping
> the drawing code in `overworld.py` / `battle.py` and adding image loading to `entities.py`.

## Quick Start

```bash
# 1) Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
# .venv\Scripts\activate.bat

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run
python main.py
```

## Controls

### Overworld
- **Arrow Keys**: Move
- **E**: Interact (recruit NPC if adjacent in towns/cities)
- **H**: Toggle help overlay
- **ESC**: Quit

Random encounters trigger as you move on non-safe tiles (not in town/city).

### Battle
- Actions proceed in turns for each living party member, then enemies.
- **Number keys (1-9)**: Choose an ability
- **Arrow Up/Down**: Select a target (enemy or ally depending on ability)
- **ENTER**: Confirm action
- **Space**: Advance when messages appear
- **ESC**: Quit game

## Structure

- `main.py` — Boot, top-level game loop and state switching.
- `engine.py` — Simple state and game engine scaffold.
- `overworld.py` — Procedural map, player movement, NPC spawns and recruiting, encounter triggers.
- `battle.py` — Turn-based combat loop, ability execution, victory/defeat, XP/leveling.
- `entities.py` — Character/Monster/Party/Ability classes and level-up logic.
- `mapgen.py` — Tiny procedural biome map generator (noise-lite).

## Extend Me
- Replace placeholder rendering with your art & UI.
- Add status effects, MP, items, equipment and shops.
- Add quests and a branching story (e.g., king's murder mystery reveal/twist).
- Add save/load (pickle or JSON).


## Quests
- **Main Quest Trigger**: Enter a **city** for the first time to get the main quest (reach the nearest dungeon).
- **Side Quests**: Look for **magenta '!' markers** across the world. Press **E** next to one to accept a quest.
- **Quest Types**:
  - **Hunt**: Defeat N of a monster in a biome.
  - **Reach**: Travel to a specific coordinate (shown as a gold star when in view).
  - **Recruit**: Recruit an ally (press **E** next to an NPC in towns/cities).
- **Quest Log**: Press **Q** to view active and completed quests.
