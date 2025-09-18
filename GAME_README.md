# Treasure Goblin

A town-to-dungeon adventure game built with Python and Pygame, featuring the existing sprite system.

## Features

### 🏘️ Town System
- **Interactive Town**: Explore a procedurally generated town with buildings and NPCs
- **NPCs with Dialogue**: Talk to shopkeepers, innkeepers, blacksmiths, and priests
- **Building Types**: Shop, Inn, Blacksmith, Temple, and Dungeon Entrance
- **Character Classes**: Choose from Warrior, Rogue, Mage, Ranger, or Cleric

### 🏰 Dungeon System
- **Multi-Level Dungeons**: 5 levels of increasing difficulty
- **Procedural Generation**: Each level is uniquely generated with rooms and corridors
- **Enemy Spawning**: Level-appropriate enemies spawn throughout the dungeon
- **Loot System**: Find chests with gold, health potions, weapons, and armour
- **Health Pickups**: Discover health potions scattered throughout the dungeon

### 🎮 Gameplay
- **Turn-Based Movement**: Strategic movement with WASD or arrow keys
- **Character Progression**: Level up and gain experience from defeating enemies
- **Equipment System**: Equip weapons, armour, and accessories
- **Inventory Management**: Store and manage items
- **Combat System**: Fight enemies with melee and ranged attacks

### 🎨 Visual System
- **Sprite Integration**: Uses the existing sprite system with fallback to colored shapes
- **Camera System**: Smooth camera following the player
- **UI Elements**: Game log, character stats, and control hints
- **Visual Feedback**: Different colors and sprites for different elements

## Controls

### Movement
- **WASD** or **Arrow Keys**: 4-directional movement
- **Numpad 1-9**: 8-directional movement (including diagonals)
- **Space**: Wait/rest turn

### Actions
- **Enter**: Activate/interact with objects
- **C**: Show character sheet
- **I**: Show inventory
- **T**: Return to town (from dungeon)
- **ESC**: Quit game

## How to Play

1. **Start the Game**: Run `python main.py`
2. **Choose Character Class**: Select from 5 different classes with unique stats
3. **Explore Town**: Talk to NPCs and find the dungeon entrance
4. **Enter Dungeon**: Descend into the dungeon to fight enemies and find loot
5. **Progress Deeper**: Find stairs to go to deeper, more dangerous levels
6. **Return to Town**: Use 'T' key to return to town for rest and supplies

## Game Areas

### Town
- **Central Plaza**: Main gathering area with buildings around it
- **Shop**: Buy and sell items (coming soon)
- **Inn**: Rest and recover health (coming soon)
- **Blacksmith**: Repair and upgrade equipment (coming soon)
- **Temple**: Get blessings and divine protection (coming soon)
- **Dungeon Entrance**: Stairs leading down to the dungeon

### Dungeon Levels
- **Level 1**: Forest creatures (Chickens, Frogs, Birds)
- **Level 2**: Spider caverns with dangerous arachnids
- **Level 3**: Goblin warrens with aggressive humanoids
- **Level 4**: Ancient ruins with magical creatures
- **Level 5**: Deepest depths with the most dangerous enemies

## Character Classes

### Warrior
- **Focus**: Strength and Constitution
- **Starting Equipment**: Iron Sword, Chain Mail, Iron Helm
- **Playstyle**: Tank and melee combat specialist

### Rogue
- **Focus**: Dexterity and Luck
- **Starting Equipment**: Steel Dagger, Leather Armour, Lucky Ring
- **Playstyle**: Fast and sneaky with high critical hit chance

### Mage
- **Focus**: Perception and Intelligence
- **Starting Equipment**: Magic Staff, Mage Robes, Wise Pendant
- **Playstyle**: Magic and ranged combat specialist

### Ranger
- **Focus**: Dexterity and Perception
- **Starting Equipment**: Hunter's Bow, Wooden Arrows, Leather Armour, Swift Boots
- **Playstyle**: Ranged combat and wilderness survival

### Cleric
- **Focus**: Constitution and Luck
- **Starting Equipment**: Holy Mace, Blessed Mail, Divine Symbol
- **Playstyle**: Support and divine magic specialist

## Technical Features

- **Modular Architecture**: Clean separation of game systems
- **Sprite System Integration**: Uses existing sprite management system
- **Procedural Generation**: Dungeons are generated algorithmically
- **Enemy AI**: Different enemy types with unique behaviors
- **Turn-Based System**: Strategic gameplay with timing considerations
- **Save System Ready**: Architecture supports save/load functionality

## Requirements

- Python 3.7+
- Pygame
- Existing sprite assets in the `assets/` directory

## Installation

1. Ensure you have Python 3.7+ installed
2. Install Pygame: `pip install pygame`
3. Run the game: `python main.py`

## Future Enhancements

- **Combat System**: Full turn-based combat with animations
- **Shop System**: Buy and sell items with NPCs
- **Save/Load**: Persistent game state
- **Sound Effects**: Audio feedback for actions
- **More Sprites**: Additional visual variety
- **Quest System**: NPCs with quests and objectives
- **Magic System**: Spells and magical abilities
- **Boss Fights**: Special encounters on deeper levels

Enjoy exploring the depths of Treasure Goblin!
