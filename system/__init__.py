"""
Logic module for Treasure Goblin - contains core game systems.

This module provides the fundamental game logic components including:
- Character system with stats, equipment, and leveling
- Perk system with specialization trees
- Enemy system with AI and combat
- Turn-based action system with timing
- Game state management and character classes
- Configuration management
"""

from .character_system import (
    Character, CharacterStats, Equipment, Item, ItemGenerator,
    StatType, EquipmentSlot, ItemType
)
# Import CellType from main for use in other modules
try:
    from main import CellType
except ImportError:
    # Define CellType locally if main module not available
    from enum import Enum
    class CellType(Enum):
        WALL = 0
        FLOOR = 1
        DOOR = 2
        STAIRCASE = 3
        CHEST = 4
        HP_PICKUP = 5
from .perk_system import (
    PerkSystem, CharacterPerks, Perk, PerkCategory, PerkType, PerkEffect
)
from .enemy_system import Enemy, EnemyManager, EnemyType
from .turn_system import TurnManager, ActionCosts, ActionType
from .game_states import GameStateManager, CharacterClassData, CharacterClass, GameState
from .config_manager import ConfigManager

# Import sprite font system
from .sprite_font import SpriteFont

# Import sprite system
from .sprite_system import GameSpriteManager

# Import inventory system
from .inventory_system import Inventory, InteractiveCharacterScreen, InventoryAction

__all__ = [
    # Character System
    'Character', 'CharacterStats', 'Equipment', 'Item', 'ItemGenerator',
    'StatType', 'EquipmentSlot', 'ItemType',
    
    # Perk System
    'PerkSystem', 'CharacterPerks', 'Perk', 'PerkCategory', 'PerkType', 'PerkEffect',
    
    # Enemy System
    'Enemy', 'EnemyManager', 'EnemyType',
    
    # Turn System
    'TurnManager', 'ActionCosts', 'ActionType',
    
    # Game States
    'GameStateManager', 'CharacterClassData', 'CharacterClass', 'GameState',
    
    # Configuration
    'ConfigManager',
    
    # Sprite System
    'SpriteFont', 'GameSpriteManager',
    
    # Inventory System
    'Inventory', 'InteractiveCharacterScreen', 'InventoryAction'
] 