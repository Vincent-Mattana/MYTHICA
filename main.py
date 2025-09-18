#!/usr/bin/env python3
"""
Treasure Goblin - Main Game
A town-to-dungeon adventure game using the sprite system.
"""

import pygame
import sys
import random
import math
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum

# Import game systems
from system import (
    Character, CharacterStats, StatType, EquipmentSlot, ItemType, Equipment,
    Enemy, EnemyManager, EnemyType, 
    GameStateManager, GameState, CharacterClass,
    TurnManager, ActionType, ActionCosts,
    SpriteFont, GameSpriteManager
)

# Suppress pygame welcome message
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

class CellType(Enum):
    """Types of cells in the game world."""
    WALL = 0
    FLOOR = 1
    DOOR = 2
    STAIRCASE = 3
    CHEST = 4
    HP_PICKUP = 5
    TOWN_FLOOR = 6
    TOWN_WALL = 7
    TOWN_DOOR = 8
    TOWN_BUILDING = 9
    DUNGEON_ENTRANCE = 10

class GameArea(Enum):
    """Different areas of the game world."""
    TOWN = "town"
    DUNGEON = "dungeon"

class NPC:
    """Represents a non-player character in the town."""
    
    def __init__(self, name: str, x: int, y: int, npc_type: str, dialogue: List[str]):
        self.name = name
        self.x = x
        self.y = y
        self.npc_type = npc_type  # "shopkeeper", "innkeeper", "blacksmith", "priest"
        self.dialogue = dialogue
        self.current_dialogue = 0
    
    def get_dialogue(self) -> str:
        """Get current dialogue line."""
        if self.dialogue:
            dialogue = self.dialogue[self.current_dialogue]
            self.current_dialogue = (self.current_dialogue + 1) % len(self.dialogue)
            return dialogue
        return f"Hello, I'm {self.name}."

class Town:
    """Represents the starting town area."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[CellType.TOWN_WALL for _ in range(width)] for _ in range(height)]
        self.dungeon_entrance = (width // 2, height - 2)  # Bottom center
        self.npcs = []
        self.painted_sprites = {}  # (x, y) -> sprite_name
        self._generate_town()
        self._place_npcs()
    
    def _generate_town(self):
        """Generate the town layout with buildings and paths."""
        # Create main paths
        for x in range(1, self.width - 1):
            self.grid[1][x] = CellType.TOWN_FLOOR  # Top path
            self.grid[self.height - 2][x] = CellType.TOWN_FLOOR  # Bottom path
        
        for y in range(1, self.height - 1):
            self.grid[y][1] = CellType.TOWN_FLOOR  # Left path
            self.grid[y][self.width - 2] = CellType.TOWN_FLOOR  # Right path
        
        # Create central plaza
        center_x, center_y = self.width // 2, self.height // 2
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                x, y = center_x + dx, center_y + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = CellType.TOWN_FLOOR
        
        # Create buildings around the plaza
        buildings = [
            (center_x - 4, center_y - 2, 3, 3),  # Shop
            (center_x + 2, center_y - 2, 3, 3),  # Inn
            (center_x - 4, center_y + 2, 3, 3),  # Blacksmith
            (center_x + 2, center_y + 2, 3, 3),  # Temple
        ]
        
        for bx, by, bw, bh in buildings:
            for dy in range(bh):
                for dx in range(bw):
                    x, y = bx + dx, by + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        if dy == 0 or dy == bh - 1 or dx == 0 or dx == bw - 1:
                            self.grid[y][x] = CellType.TOWN_WALL
                        else:
                            self.grid[y][x] = CellType.TOWN_BUILDING
        
        # Add doors to buildings
        for bx, by, bw, bh in buildings:
            # Front door
            door_x = bx + bw // 2
            door_y = by - 1
            if 0 <= door_x < self.width and 0 <= door_y < self.height:
                self.grid[door_y][door_x] = CellType.TOWN_DOOR
        
        # Place dungeon entrance
        dx, dy = self.dungeon_entrance
        self.grid[dy][dx] = CellType.DUNGEON_ENTRANCE
        self.grid[dy - 1][dx] = CellType.TOWN_FLOOR  # Path to entrance
    
    def _place_npcs(self):
        """Place NPCs in the town."""
        center_x, center_y = self.width // 2, self.height // 2
        
        # Shopkeeper in the shop
        self.npcs.append(NPC(
            "Marcus the Merchant", center_x - 2, center_y - 1, "shopkeeper",
            [
                "Welcome to my shop! I have the finest goods in town.",
                "Adventuring gear? You've come to the right place!",
                "Be careful in that dungeon - it's dangerous down there."
            ]
        ))
        
        # Innkeeper in the inn
        self.npcs.append(NPC(
            "Elena the Innkeeper", center_x + 2, center_y - 1, "innkeeper",
            [
                "Welcome to the Golden Dragon Inn!",
                "Need a place to rest? We have the best beds in town.",
                "The dungeon entrance is just south of here."
            ]
        ))
        
        # Blacksmith
        self.npcs.append(NPC(
            "Thorin the Blacksmith", center_x - 2, center_y + 1, "blacksmith",
            [
                "I forge the finest weapons and armour!",
                "That old dungeon has been there for centuries.",
                "Need your gear repaired? I'm your man!"
            ]
        ))
        
        # Priest
        self.npcs.append(NPC(
            "Father Benedict", center_x + 2, center_y + 1, "priest",
            [
                "May the light guide your path, adventurer.",
                "The dungeon below holds ancient secrets and dangers.",
                "I can bless your equipment if you need divine protection."
            ]
        ))
    
    def get_npc_at(self, x: int, y: int) -> Optional[NPC]:
        """Get NPC at specific position."""
        for npc in self.npcs:
            if npc.x == x and npc.y == y:
                return npc
        return None
    
    def get_cell(self, x: int, y: int) -> CellType:
        """Get cell type at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return CellType.TOWN_WALL
    
    def can_move_to(self, x: int, y: int) -> bool:
        """Check if player can move to position."""
        cell = self.get_cell(x, y)
        return cell in [CellType.TOWN_FLOOR, CellType.TOWN_DOOR, CellType.DUNGEON_ENTRANCE]

class Room:
    """Represents a room in the dungeon."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center_x = x + width // 2
        self.center_y = y + height // 2
        self.connected = False

class Dungeon:
    """Represents a dungeon level with improved procedural generation."""
    
    def __init__(self, width: int, height: int, level: int = 1):
        self.width = width
        self.height = height
        self.level = level
        self.grid = [[CellType.WALL for _ in range(width)] for _ in range(height)]
        self.start_pos = None  # Will be set after generation
        self.staircase_pos = None
        self.staircase_up_pos = None  # Position of staircase going up
        self.rooms = []
        self.chests = []
        self.health_pickups = []
        self._generate_dungeon()
    
    def _generate_dungeon(self):
        """Generate a procedural dungeon with rooms and corridors."""
        # Generate rooms
        self._generate_rooms()
        
        # Connect rooms with corridors
        self._connect_rooms()
        
        # Set start position to the center of the first room
        self._set_start_position()
        
        # Place staircase up (where player entered)
        self._place_staircase_up()
        
        # Place special items
        self._place_special_items()
        
        # Place staircase (down to next level)
        if self.level < 5:  # Only add stairs if not the deepest level
            self._place_staircase()
    
    def _generate_rooms(self):
        """Generate rooms for the dungeon."""
        num_rooms = random.randint(5, 8) + self.level  # More rooms on deeper levels
        min_room_size = 4
        max_room_size = 8
        
        for _ in range(num_rooms * 3):  # Try multiple times to fit rooms
            if len(self.rooms) >= num_rooms:
                break
                
            width = random.randint(min_room_size, max_room_size)
            height = random.randint(min_room_size, max_room_size)
            x = random.randint(1, self.width - width - 1)
            y = random.randint(1, self.height - height - 1)
            
            room = Room(x, y, width, height)
            
            # Check if room overlaps with existing rooms
            if not self._room_overlaps(room):
                self.rooms.append(room)
                self._carve_room(room)
        
        # Ensure we have at least one room
        if not self.rooms:
            # Create a simple room in the center
            center_x = self.width // 2 - 3
            center_y = self.height // 2 - 3
            room = Room(center_x, center_y, 6, 6)
            self.rooms.append(room)
            self._carve_room(room)
    
    def _room_overlaps(self, room: Room) -> bool:
        """Check if a room overlaps with existing rooms."""
        for existing_room in self.rooms:
            if (room.x < existing_room.x + existing_room.width and
                room.x + room.width > existing_room.x and
                room.y < existing_room.y + existing_room.height and
                room.y + room.height > existing_room.y):
                return True
        return False
    
    def _carve_room(self, room: Room):
        """Carve out a room in the dungeon grid."""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = CellType.FLOOR
    
    def _connect_rooms(self):
        """Connect rooms with corridors."""
        if len(self.rooms) < 2:
            return
        
        # Connect each room to the next one
        for i in range(len(self.rooms) - 1):
            room1 = self.rooms[i]
            room2 = self.rooms[i + 1]
            self._create_corridor(room1, room2)
        
        # Connect the last room back to the first to ensure connectivity
        if len(self.rooms) > 2:
            self._create_corridor(self.rooms[-1], self.rooms[0])
    
    def _create_corridor(self, room1: Room, room2: Room):
        """Create a corridor between two rooms."""
        # Start from center of room1
        x1, y1 = room1.center_x, room1.center_y
        x2, y2 = room2.center_x, room2.center_y
        
        # Create L-shaped corridor
        # First horizontal
        start_x = min(x1, x2)
        end_x = max(x1, x2)
        for x in range(start_x, end_x + 1):
            if 0 <= x < self.width and 0 <= y1 < self.height:
                self.grid[y1][x] = CellType.FLOOR
        
        # Then vertical
        start_y = min(y1, y2)
        end_y = max(y1, y2)
        for y in range(start_y, end_y + 1):
            if 0 <= x2 < self.width and 0 <= y < self.height:
                self.grid[y][x2] = CellType.FLOOR
    
    def _place_special_items(self):
        """Place chests and health pickups in the dungeon."""
        # Place chests in some rooms
        for room in self.rooms[1:]:  # Skip the first room (start room)
            if random.random() < 0.3:  # 30% chance per room
                chest_x = room.x + random.randint(1, room.width - 2)
                chest_y = room.y + random.randint(1, room.height - 2)
                if 0 <= chest_x < self.width and 0 <= chest_y < self.height:
                    self.grid[chest_y][chest_x] = CellType.CHEST
                    self.chests.append((chest_x, chest_y))
        
        # Place health pickups
        for room in self.rooms:
            if random.random() < 0.2:  # 20% chance per room
                pickup_x = room.x + random.randint(1, room.width - 2)
                pickup_y = room.y + random.randint(1, room.height - 2)
                if 0 <= pickup_x < self.width and 0 <= pickup_y < self.height:
                    self.grid[pickup_y][pickup_x] = CellType.HP_PICKUP
                    self.health_pickups.append((pickup_x, pickup_y))
    
    def _place_staircase(self):
        """Place the staircase to the next level."""
        if self.rooms:
            # Place staircase in the last room
            last_room = self.rooms[-1]
            self.staircase_pos = (last_room.center_x, last_room.center_y)
            self.grid[self.staircase_pos[1]][self.staircase_pos[0]] = CellType.STAIRCASE
    
    def _set_start_position(self):
        """Set the start position to the center of the first room."""
        if self.rooms:
            first_room = self.rooms[0]
            self.start_pos = (first_room.center_x, first_room.center_y)
        else:
            # Fallback to center if no rooms
            self.start_pos = (self.width // 2, self.height // 2)
    
    def _place_staircase_up(self):
        """Place staircase going up (where player entered)."""
        if self.rooms and len(self.rooms) > 0:
            # Place staircase up in the first room, near the start position
            first_room = self.rooms[0]
            # Find a position near the start but not on it
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    x = first_room.center_x + dx
                    y = first_room.center_y + dy
                    if (0 <= x < self.width and 0 <= y < self.height and 
                        self.grid[y][x] == CellType.FLOOR and 
                        (x, y) != self.start_pos):
                        self.staircase_up_pos = (x, y)
                        self.grid[y][x] = CellType.STAIRCASE
                        return
    
    def get_cell(self, x: int, y: int) -> CellType:
        """Get cell type at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return CellType.WALL
    
    def can_move_to(self, x: int, y: int) -> bool:
        """Check if player can move to position."""
        cell = self.get_cell(x, y)
        return cell in [CellType.FLOOR, CellType.DOOR, CellType.STAIRCASE]

class Player:
    """Represents the player character."""
    
    def __init__(self, character: Character, x: int, y: int):
        self.character = character
        self.x = x
        self.y = y
        self.last_move_time = 0
        self.move_cooldown = 0.1  # 100ms between moves
    
    def can_move(self, current_time: float) -> bool:
        """Check if player can move now."""
        return current_time - self.last_move_time >= self.move_cooldown
    
    def move_to(self, x: int, y: int, current_time: float):
        """Move player to new position."""
        self.x = x
        self.y = y
        self.last_move_time = current_time

class Game:
    """Main game class."""
    
    def __init__(self, god_mode=False):
        pygame.init()
        
        # Window settings
        self.window_width = 1024
        self.window_height = 768
        self.fullscreen = False
        self.resizable = True
        
        # Create resizable window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Treasure Goblin")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # God mode flag
        self.god_mode = god_mode
        
        # Game state
        self.current_area = GameArea.TOWN
        self.dungeon_level = 1
        self.max_dungeon_level = 5
        self.custom_town_data = None  # Initialize custom town data
        
        # Auto-explore state
        self.auto_explore_active = False
        self.auto_explore_path = []
        self.auto_explore_target = None
        self.auto_explore_attack_mode = False  # New mode that attacks enemies
        self.auto_explore_failed_attempts = 0  # Track failed attempts to prevent infinite loops
        
        # Light flickering effect
        self.light_flicker_timer = 0.0
        self.light_flicker_intensity = 1.0
        self.flicker_enabled = True  # Toggle for flickering effect
        self.light_source_type = "torch"  # Type of light source
        
        # Click navigation
        self.click_path = []
        self.click_target = None
        self.click_navigation_active = False
        
        # Death and scoring
        self.is_dead = False
        self.final_score = 0
        self.high_scores = self._load_high_scores()
        
        # Pause state
        self.is_paused = False
        
        # Skill point allocation
        self.skill_popup_open = False
        self.selected_stat = None
        
        # Log popup
        self.log_popup_open = False
        self.log_popup_scroll = 0
        
        # Initialize sprite system
        self.sprite_manager = GameSpriteManager()
        assets_path = Path(__file__).parent / "assets"
        if not self.sprite_manager.load_game_assets(assets_path):
            print("Warning: Could not load all game assets")
        
        # Initialize game areas
        self.town = self._create_town()
        self.dungeon = Dungeon(50, 40, self.dungeon_level)
        
        # Initialize player
        self.player = None
        self.enemy_manager = EnemyManager()
        
        # Game state manager
        self.state_manager = GameStateManager(self.screen, self)
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = 16  # Sprite width
        self.tile_height = 24  # Sprite height
        
        # UI
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Game log
        self.log_messages = []
        self.max_log_messages = 10
        
        # Turn system
        self.turn_manager = TurnManager()
        
        # Targeting system
        self.targeting_mode = False
        self.targeting_x = 0
        self.targeting_y = 0
        self.targeting_valid = False
        
        # Fog of war system
        self.explored_tiles = set()  # Set of (x, y) tuples for explored tiles
        self.visible_tiles = set()   # Set of (x, y) tuples for currently visible tiles
        
        # Sprite consistency system
        self.tile_sprites = {}  # Cache for consistent tile sprites (x, y) -> sprite_name
        
        # Last known positions system
        self.last_known_positions = {}  # entity_id -> (x, y, timestamp)
        
        # Level persistence system
        self.saved_levels = {}  # level_number -> level_data
        self.saved_town_data = None  # town_data
    
    def _clear_level_data(self):
        """Clear level-specific data when changing levels."""
        # Clear fog of war data
        self.explored_tiles.clear()
        self.visible_tiles.clear()
        
        # Clear last known positions
        self.last_known_positions.clear()
        
        # Clear sprite cache
        self.tile_sprites.clear()
    
    def _clear_level_data_for_new_level(self):
        """Clear level-specific data for a completely new level."""
        # Clear fog of war data
        self.explored_tiles.clear()
        self.visible_tiles.clear()
        
        # Clear last known positions
        self.last_known_positions.clear()
        
        # Clear sprite cache for new level
        self.tile_sprites.clear()
    
    def _save_level_data(self, level_number: int):
        """Save current level data."""
        level_data = {
            'explored_tiles': self.explored_tiles.copy(),
            'visible_tiles': self.visible_tiles.copy(),
            'last_known_positions': self.last_known_positions.copy(),
            'tile_sprites': self.tile_sprites.copy(),
            'dungeon': self.dungeon,
            'enemies': self.enemy_manager.get_living_enemies().copy()
        }
        self.saved_levels[level_number] = level_data
    
    def _restore_level_data(self, level_number: int):
        """Restore level data if it exists."""
        if level_number in self.saved_levels:
            level_data = self.saved_levels[level_number]
            self.explored_tiles = level_data['explored_tiles'].copy()
            self.visible_tiles = level_data['visible_tiles'].copy()
            self.last_known_positions = level_data['last_known_positions'].copy()
            self.tile_sprites = level_data['tile_sprites'].copy()
            self.dungeon = level_data['dungeon']
            
            # Restore enemies
            self.enemy_manager.enemies = level_data['enemies'].copy()
            
            return True
        return False
    
    def _save_town_data(self):
        """Save current town data."""
        self.saved_town_data = {
            'explored_tiles': self.explored_tiles.copy(),
            'visible_tiles': self.visible_tiles.copy(),
            'last_known_positions': self.last_known_positions.copy(),
            'tile_sprites': self.tile_sprites.copy()
        }
    
    def _restore_town_data(self):
        """Restore town data if it exists."""
        if self.saved_town_data:
            self.explored_tiles = self.saved_town_data['explored_tiles'].copy()
            self.visible_tiles = self.saved_town_data['visible_tiles'].copy()
            self.last_known_positions = self.saved_town_data['last_known_positions'].copy()
            self.tile_sprites = self.saved_town_data['tile_sprites'].copy()
            return True
        return False
    
    def _update_light_flicker(self, delta_time: float):
        """Update the light flickering effect."""
        if not self.flicker_enabled:
            self.light_flicker_intensity = 1.0
            return
            
        import random
        import math
        
        self.light_flicker_timer += delta_time
        
        # Create a more subtle flickering pattern based on light source type
        if self.light_source_type == "torch":
            # Torch: moderate flickering
            base_flicker = math.sin(self.light_flicker_timer * 6.0) * 0.04  # Moderate flicker
            slow_flicker = math.sin(self.light_flicker_timer * 1.5) * 0.02  # Slow variation
            random_flicker = (random.random() - 0.5) * 0.06  # Small random variation
            min_intensity = 0.85
            max_intensity = 1.0
        elif self.light_source_type == "candle":
            # Candle: more pronounced flickering
            base_flicker = math.sin(self.light_flicker_timer * 8.0) * 0.06  # Faster flicker
            slow_flicker = math.sin(self.light_flicker_timer * 2.0) * 0.03  # Slow variation
            random_flicker = (random.random() - 0.5) * 0.08  # More random variation
            min_intensity = 0.8
            max_intensity = 1.0
        elif self.light_source_type == "lamp":
            # Lamp: very subtle flickering
            base_flicker = math.sin(self.light_flicker_timer * 4.0) * 0.02  # Gentle flicker
            slow_flicker = math.sin(self.light_flicker_timer * 1.0) * 0.01  # Very slow variation
            random_flicker = (random.random() - 0.5) * 0.03  # Minimal random variation
            min_intensity = 0.92
            max_intensity = 1.0
        elif self.light_source_type == "magic":
            # Magic: no flickering
            base_flicker = 0.0
            slow_flicker = 0.0
            random_flicker = 0.0
            min_intensity = 1.0
            max_intensity = 1.0
        else:
            # Default: subtle flickering
            base_flicker = math.sin(self.light_flicker_timer * 5.0) * 0.03  # Gentle flicker
            slow_flicker = math.sin(self.light_flicker_timer * 1.2) * 0.015  # Slow variation
            random_flicker = (random.random() - 0.5) * 0.04  # Small random variation
            min_intensity = 0.88
            max_intensity = 1.0
        
        # Combine all flicker effects
        total_flicker = base_flicker + slow_flicker + random_flicker
        
        # Clamp the intensity based on light source type
        self.light_flicker_intensity = max(min_intensity, min(max_intensity, 1.0 + total_flicker))
    
    def set_light_source_type(self, source_type: str):
        """Set the type of light source to determine flickering behavior."""
        valid_types = ["torch", "candle", "lamp", "magic", "none"]
        if source_type in valid_types:
            self.light_source_type = source_type
            if source_type == "magic" or source_type == "none":
                self.flicker_enabled = False
            else:
                self.flicker_enabled = True
            print(f"Light source set to: {source_type}")
        else:
            print(f"Invalid light source type. Valid types: {valid_types}")
    
    def toggle_flicker(self):
        """Toggle the light flickering effect on/off."""
        self.flicker_enabled = not self.flicker_enabled
        print(f"Light flickering {'enabled' if self.flicker_enabled else 'disabled'}")
    
    def set_flicker_enabled(self, enabled: bool):
        """Set whether light flickering is enabled."""
        self.flicker_enabled = enabled
        print(f"Light flickering {'enabled' if enabled else 'disabled'}")
    
    def get_light_source_info(self) -> dict:
        """Get current light source information."""
        return {
            "type": self.light_source_type,
            "flicker_enabled": self.flicker_enabled,
            "intensity": self.light_flicker_intensity
        }
    
    def _update_fog_of_war(self):
        """Update fog of war based on player position and sight range."""
        if not self.player:
            return
            
        # Clear current visible tiles
        self.visible_tiles.clear()
        
        # Get player position and sight range
        player_x, player_y = self.player.x, self.player.y
        base_sight_range = self.player.character.get_sight_range() if self.player.character else 6
        
        # Apply flickering effect to sight range
        sight_range = int(base_sight_range * self.light_flicker_intensity)
        
        # Always make the player's current position visible
        self.visible_tiles.add((player_x, player_y))
        self.explored_tiles.add((player_x, player_y))
        
        # Always make adjacent tiles visible (for movement)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                self.visible_tiles.add((player_x + dx, player_y + dy))
                self.explored_tiles.add((player_x + dx, player_y + dy))
        
        # Cast rays in all directions for better wall discovery
        for angle in range(0, 360, 3):  # Cast rays every 3 degrees for better coverage
            self._cast_visibility_ray(player_x, player_y, angle, sight_range)
        
        # Also do grid-based ray casting for comprehensive coverage
        for dx in range(-sight_range, sight_range + 1):
            for dy in range(-sight_range, sight_range + 1):
                # Skip if outside sight range
                if dx * dx + dy * dy > sight_range * sight_range:
                    continue
                    
                # Cast ray from player to this position
                if self._is_visible(player_x, player_y, player_x + dx, player_y + dy):
                    self.visible_tiles.add((player_x + dx, player_y + dy))
                    self.explored_tiles.add((player_x + dx, player_y + dy))
                else:
                    # Even if not visible, mark walls along the line as explored
                    self._mark_walls_along_line(player_x, player_y, player_x + dx, player_y + dy)
        
        # Update last known positions of visible entities
        self._update_last_known_positions()
    
    def _cast_visibility_ray(self, start_x, start_y, angle, max_distance):
        """Cast a visibility ray in a specific direction."""
        import math
        
        # Convert angle to radians
        angle_rad = math.radians(angle)
        
        # Calculate direction vector
        dx = math.cos(angle_rad)
        dy = math.sin(angle_rad)
        
        # Cast ray step by step
        for distance in range(1, max_distance + 1):
            # Calculate position along ray
            x = int(start_x + dx * distance)
            y = int(start_y + dy * distance)
            
            # Check bounds
            if self.current_area == GameArea.TOWN:
                if (x < 0 or x >= self.town.width or y < 0 or y >= self.town.height):
                    break
                cell = self.town.get_cell(x, y)
            else:
                if (x < 0 or x >= self.dungeon.width or y < 0 or y >= self.dungeon.height):
                    break
                cell = self.dungeon.get_cell(x, y)
            
            # Mark this tile as explored
            self.explored_tiles.add((x, y))
            
            # Check if this is a wall or building
            if self.current_area == GameArea.TOWN:
                if cell in [CellType.TOWN_WALL, CellType.TOWN_BUILDING]:
                    # Wall blocks further vision
                    self.visible_tiles.add((x, y))
                    break
                else:
                    # Floor or door - can see through
                    self.visible_tiles.add((x, y))
            else:
                if cell == CellType.WALL:
                    # Wall blocks further vision
                    self.visible_tiles.add((x, y))
                    break
                else:
                    # Floor or door - can see through
                    self.visible_tiles.add((x, y))
    
    def _is_visible(self, start_x, start_y, end_x, end_y):
        """Check if a position is visible using ray casting."""
        # Simple line-of-sight check
        dx = end_x - start_x
        dy = end_y - start_y
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            return True
            
        # Check each step along the line
        for i in range(1, steps + 1):
            x = start_x + (dx * i) // steps
            y = start_y + (dy * i) // steps
            
            # Check if we hit a wall
            if self.current_area == GameArea.TOWN:
                if self.town.get_cell(x, y) in [CellType.TOWN_WALL, CellType.TOWN_BUILDING]:
                    return False
            else:
                if self.dungeon.get_cell(x, y) == CellType.WALL:
                    return False
                    
        return True
    
    def _is_tile_visible(self, x, y):
        """Check if a tile is currently visible to the player."""
        return (x, y) in self.visible_tiles
    
    def _is_tile_explored(self, x, y):
        """Check if a tile has been explored before."""
        return (x, y) in self.explored_tiles
    
    def _mark_walls_along_line(self, start_x, start_y, end_x, end_y):
        """Mark walls along a line as explored."""
        dx = end_x - start_x
        dy = end_y - start_y
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            return
            
        # Check each step along the line
        for i in range(1, steps + 1):
            x = start_x + (dx * i) // steps
            y = start_y + (dy * i) // steps
            
            # Check bounds
            if self.current_area == GameArea.TOWN:
                if (x < 0 or x >= self.town.width or y < 0 or y >= self.town.height):
                    break
                cell = self.town.get_cell(x, y)
                if cell in [CellType.TOWN_WALL, CellType.TOWN_BUILDING]:
                    self.explored_tiles.add((x, y))
                    break  # Stop at first wall
            else:
                if (x < 0 or x >= self.dungeon.width or y < 0 or y >= self.dungeon.height):
                    break
                cell = self.dungeon.get_cell(x, y)
                if cell == CellType.WALL:
                    self.explored_tiles.add((x, y))
                    break  # Stop at first wall
    
    def _update_last_known_positions(self):
        """Update last known positions of visible entities."""
        import time
        current_time = time.time()
        
        # Update enemies
        for i, enemy in enumerate(self.enemy_manager.get_living_enemies()):
            if self._is_tile_visible(enemy.x, enemy.y):
                enemy_id = f"enemy_{i}_{enemy.enemy_type.name}_{enemy.x}_{enemy.y}"
                self.last_known_positions[enemy_id] = (enemy.x, enemy.y, current_time)
        
        # Update NPCs
        for npc in self.town.npcs:
            if self._is_tile_visible(npc.x, npc.y):
                npc_id = f"npc_{npc.name}_{npc.x}_{npc.y}"
                self.last_known_positions[npc_id] = (npc.x, npc.y, current_time)
    
    def _create_town(self):
        """Create town, loading custom data if available."""
        # Only load custom town if we don't have custom_town_data set to None (restart case)
        if self.custom_town_data is None and self._load_custom_town():
            print("Loaded custom town from saved_town.json")
            return self._create_town_from_data()
        elif self.custom_town_data is not None:
            print("Using existing custom town data")
            return self._create_town_from_data()
        else:
            print("Using generated town layout")
            return Town(40, 30)
    
    def _load_custom_town(self):
        """Load custom town data from file."""
        try:
            with open("saved_town.json", 'r') as f:
                self.custom_town_data = json.load(f)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error loading custom town: {e}")
            return False
    
    def _create_town_from_data(self):
        """Create town from custom data."""
        if not hasattr(self, 'custom_town_data'):
            return Town(40, 30)
        
        data = self.custom_town_data
        width = data.get("width", 40)
        height = data.get("height", 30)
        
        # Create town with custom dimensions
        town = Town(width, height)
        
        # Load custom tiles
        for key, cell_value in data.get("tiles", {}).items():
            x, y = map(int, key.split(','))
            if 0 <= x < width and 0 <= y < height:
                town.grid[y][x] = CellType(cell_value)
        
        # Find the actual dungeon entrance position in the loaded town
        for y in range(height):
            for x in range(width):
                if town.grid[y][x] == CellType.DUNGEON_ENTRANCE:
                    town.dungeon_entrance = (x, y)
                    print(f"Found dungeon entrance at ({x}, {y}) in loaded town")
                    break
            if town.dungeon_entrance != (width // 2, height - 2):
                break
        
        # Load custom NPCs
        town.npcs = []
        for npc_data in data.get("npcs", []):
            npc = NPC(
                name=npc_data["type"].title(),
                x=npc_data["x"],
                y=npc_data["y"],
                npc_type=npc_data["type"],
                dialogue=self._get_npc_dialogue(npc_data["type"])
            )
            town.npcs.append(npc)
        
        # Load painted sprites
        town.painted_sprites = {}
        for key, sprite in data.get("painted_sprites", {}).items():
            x, y = map(int, key.split(','))
            town.painted_sprites[(x, y)] = sprite
        
        return town
    
    def _get_npc_dialogue(self, npc_type):
        """Get dialogue for NPC type."""
        dialogues = {
            "shopkeeper": ["Welcome to my shop!", "What can I get for you today?"],
            "innkeeper": ["Need a place to rest?", "The rooms are clean and safe."],
            "blacksmith": ["I forge the finest weapons!", "Need something sharp?"],
            "priest": ["May the gods bless you!", "Need healing or guidance?"]
        }
        return dialogues.get(npc_type, ["Hello there!"])
    
    def start_game(self, character: Character):
        """Start the game with a character."""
        # Reset all game state flags
        self.is_dead = False
        self.is_paused = False
        self.final_score = 0
        
        # Apply god mode effects if enabled
        if self.god_mode:
            character.inventory.gold = 10000
            character.god_mode = True  # Set god mode flag on character
            self.add_to_log("GOD MODE ENABLED: Invincible + 10000 gold!", (255, 255, 0))
        
        self.player = Player(character, self.town.width // 2, self.town.height // 2)
        self.current_area = GameArea.TOWN
        self.update_camera()
        self.add_to_log(f"Welcome to Treasure Goblin, {character.name}!", (100, 255, 100))
        self.add_to_log("Explore the town and find the dungeon entrance!", (255, 255, 100))
    
    def add_to_log(self, message: str, color: Tuple[int, int, int] = (255, 255, 255)):
        """Add a message to the game log."""
        self.log_messages.append((message, color))
        if len(self.log_messages) > self.max_log_messages:
            self.log_messages.pop(0)
        
        # Also print to terminal
        print(f"LOG: {message}")
    
    def get_viewport_offset(self):
        """Calculate viewport offset to center the game content."""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # For now, let's use a simpler approach - always use full window
        # This ensures elements are drawn relative to actual window edges
        return 0, 0
    
    def update_camera(self):
        """Update camera position to follow player."""
        if self.player:
            # Calculate available gameplay area (screen height - 60 pixels for bottom frame)
            gameplay_height = self.screen.get_height() - 60
            
            # Center camera on player
            self.camera_x = self.player.x - self.screen.get_width() // (2 * self.tile_size)
            self.camera_y = self.player.y - gameplay_height // (2 * self.tile_height)
            
            # Keep camera within bounds
            if self.current_area == GameArea.TOWN:
                max_camera_x = max(0, self.town.width - self.screen.get_width() // self.tile_size)
                max_camera_y = max(0, self.town.height - gameplay_height // self.tile_height)
            else:
                max_camera_x = max(0, self.dungeon.width - self.screen.get_width() // self.tile_size)
                max_camera_y = max(0, self.dungeon.height - gameplay_height // self.tile_height)
            
            self.camera_x = max(0, min(self.camera_x, max_camera_x))
            self.camera_y = max(0, min(self.camera_y, max_camera_y))
    
    def handle_input(self, event):
        """Handle input events."""
        if event.type == pygame.KEYDOWN:
            if self.state_manager.current_state == GameState.PLAYING:
                self._handle_game_input(event.key)
            else:
                # Handle menu input
                continue_game, character = self.state_manager.handle_input(event)
                if not continue_game:
                    self.running = False
                elif character:
                    self.start_game(character)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.state_manager.current_state == GameState.PLAYING:
                    self._handle_mouse_click(event.pos)
        elif event.type == pygame.VIDEORESIZE:
            self._handle_window_resize(event)
        elif event.type == pygame.QUIT:
            self.running = False
    
    def _handle_game_input(self, key):
        """Handle input during gameplay."""
        if not self.player:
            return
        
        # Handle popup input first
        if self.skill_popup_open:
            self._handle_skill_popup_input(key)
            return
        elif self.log_popup_open:
            self._handle_log_popup_input(key)
            return
        
        current_time = pygame.time.get_ticks() / 1000.0
        
        # Movement (numpad only)
        if key == pygame.K_UP:
            self._try_move_player(0, -1, current_time)
        elif key == pygame.K_DOWN:
            self._try_move_player(0, 1, current_time)
        elif key == pygame.K_LEFT:
            self._try_move_player(-1, 0, current_time)
        elif key == pygame.K_RIGHT:
            self._try_move_player(1, 0, current_time)
        
        # Diagonal movement
        elif key == pygame.K_KP7:  # Northwest
            self._try_move_player(-1, -1, current_time)
        elif key == pygame.K_KP8:  # North
            self._try_move_player(0, -1, current_time)
        elif key == pygame.K_KP9:  # Northeast
            self._try_move_player(1, -1, current_time)
        elif key == pygame.K_KP4:  # West
            self._try_move_player(-1, 0, current_time)
        elif key == pygame.K_KP5:  # Wait (numpad 5)
            self.add_to_log("You wait...", (200, 200, 200))
        elif key == pygame.K_KP6:  # East
            self._try_move_player(1, 0, current_time)
        elif key == pygame.K_KP1:  # Southwest
            self._try_move_player(-1, 1, current_time)
        elif key == pygame.K_KP2:  # South
            self._try_move_player(0, 1, current_time)
        elif key == pygame.K_KP3:  # Southeast
            self._try_move_player(1, 1, current_time)
        
        # Actions
        elif key == pygame.K_c:  # Character sheet
            self._show_character_sheet()
        elif key == pygame.K_i:  # Inventory
            self._show_inventory()
        elif key == pygame.K_ESCAPE:
            self.running = False
        
        # Level transitions
        elif key == pygame.K_RETURN:  # Enter/activate
            self._try_activate()
        elif key == pygame.K_t:  # Return to town
            self._return_to_town()
        elif key == pygame.K_PERIOD:  # Shift+. - Go down stairs
            self._try_go_down_stairs()
        elif key == pygame.K_COMMA:  # Shift+, - Go up stairs
            self._try_go_up_stairs()
        elif key == pygame.K_o:  # Auto-explore toggle
            self._toggle_auto_explore()
        elif key == pygame.K_TAB:  # Auto-explore with attack
            self._toggle_auto_explore_attack()
        elif key == pygame.K_f:  # Attack adjacent enemies
            self._try_attack_adjacent()
        elif key == pygame.K_SPACE:  # Pause/unpause game
            self._toggle_pause()
        elif key == pygame.K_s:  # Skill point allocation
            self._toggle_skill_popup()
        elif key == pygame.K_l:  # Log popup
            self._toggle_log_popup()
        elif key == pygame.K_r:  # Restart game
            self._restart_game()
        elif key == pygame.K_F11:  # Toggle fullscreen
            self._toggle_fullscreen()
        elif key == pygame.K_F10:  # Toggle resizable
            self._toggle_resizable()
    
    def _try_move_player(self, dx: int, dy: int, current_time: float):
        """Try to move the player."""
        if not self.player or not self.player.can_move(current_time) or self.is_dead:
            return
        
        # Cancel auto-explore on manual movement
        if self.auto_explore_active:
            self.auto_explore_active = False
            self.auto_explore_attack_mode = False
            self.auto_explore_path = []
            self.auto_explore_target = None
            self.add_to_log("Auto-explore cancelled", (255, 255, 255))
        
        # Cancel click navigation on manual movement
        if self.click_navigation_active:
            self.click_navigation_active = False
            self.click_path = []
            self.click_target = None
            self.add_to_log("Click navigation cancelled", (255, 255, 255))
        
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # Check if movement is valid
        can_move = False
        if self.current_area == GameArea.TOWN:
            can_move = self.town.can_move_to(new_x, new_y)
        else:
            can_move = self.dungeon.can_move_to(new_x, new_y)
        
        if can_move:
            # Check for enemy at destination
            enemy_at_destination = self._get_enemy_at_position(new_x, new_y)
            if enemy_at_destination:
                # Attack the enemy
                self._attack_enemy(enemy_at_destination)
            else:
                # Normal movement
                self.player.move_to(new_x, new_y, current_time)
                self.update_camera()
                
                # Check for special interactions
                self._check_special_tiles(new_x, new_y)
        else:
            self.add_to_log("You can't move there!", (255, 100, 100))
    
    def _try_attack_adjacent(self):
        """Try to attack an adjacent enemy."""
        if not self.player or self.current_area != GameArea.DUNGEON or self.is_dead:
            return
        
        # Check all 8 adjacent positions for enemies
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                enemy = self._get_enemy_at_position(self.player.x + dx, self.player.y + dy)
                if enemy:
                    self._attack_enemy(enemy)
                    return
        
        # No adjacent enemies found
        self.add_to_log("No enemies adjacent to attack!", (255, 255, 100))
    
    def _try_activate(self):
        """Try to activate something at current position."""
        if not self.player:
            return
        
        x, y = self.player.x, self.player.y
        
        if self.current_area == GameArea.TOWN:
            cell = self.town.get_cell(x, y)
            if cell == CellType.DUNGEON_ENTRANCE:
                self._enter_dungeon()
            elif cell == CellType.TOWN_DOOR:
                self.add_to_log("You enter the building.", (255, 255, 100))
            
            # Check for NPC interaction
            npc = self.town.get_npc_at(x, y)
            if npc:
                self._talk_to_npc(npc)
        else:
            cell = self.dungeon.get_cell(x, y)
            if cell == CellType.STAIRCASE:
                self._go_down_stairs()
            elif cell == CellType.CHEST:
                self._open_chest()
    
    def _enter_dungeon(self):
        """Enter the dungeon from town."""
        self.add_to_log("You descend into the dark dungeon...", (200, 200, 200))
        
        # Save town data before entering dungeon
        self._save_town_data()
        
        self.current_area = GameArea.DUNGEON
        self.dungeon_level = 1
        
        # Try to restore level 1 data, if not found create new level
        if not self._restore_level_data(self.dungeon_level):
            # Clear level-specific data for new dungeon
            self._clear_level_data_for_new_level()
            
        self.dungeon = Dungeon(50, 40, self.dungeon_level)
        
        # Place player at staircase up position (stairs going up)
        if self.dungeon.staircase_up_pos:
            self.player.x, self.player.y = self.dungeon.staircase_up_pos
            print(f"DEBUG: EMERGED at stairs up: ({self.player.x}, {self.player.y})")
            self.add_to_log(f"EMERGED at stairs up: ({self.player.x}, {self.player.y})", (0, 255, 255))
        else:
            # Fallback to start position
            self.player.x, self.player.y = self.dungeon.start_pos
            print(f"DEBUG: EMERGED at start pos: ({self.player.x}, {self.player.y})")
            self.add_to_log(f"EMERGED at start pos: ({self.player.x}, {self.player.y})", (255, 255, 0))
        self.update_camera()
        
        # Spawn enemies
        self.enemy_manager.spawn_enemies_in_dungeon(
            self.dungeon, 
            player_start_pos=self.dungeon.start_pos,
            dungeon_level=self.dungeon_level
        )
        
        self.add_to_log(f"Entered dungeon level {self.dungeon_level}!", (255, 200, 100))
        self.add_to_log("The air is thick with danger...", (255, 100, 100))
        self.add_to_log("Find the stairs to go deeper!", (255, 255, 100))
    
    def _go_down_stairs(self):
        """Go down to the next dungeon level."""
        if self.dungeon_level >= self.max_dungeon_level:
            self.add_to_log("You have reached the deepest level!", (255, 255, 100))
            self.add_to_log("The final boss awaits...", (255, 100, 100))
            return
        
        self.add_to_log("You descend deeper into the dungeon...", (200, 200, 200))
        
        # Save current level data
        self._save_level_data(self.dungeon_level)
        
        self.dungeon_level += 1
        
        # Try to restore level data, if not found create new level
        if not self._restore_level_data(self.dungeon_level):
            # Clear level-specific data for new level
            self._clear_level_data_for_new_level()
            
        self.dungeon = Dungeon(50, 40, self.dungeon_level)
        
        # Place player at staircase up position (stairs going up)
        if self.dungeon.staircase_up_pos:
            self.player.x, self.player.y = self.dungeon.staircase_up_pos
            print(f"DEBUG: DESCENDED to stairs up: ({self.player.x}, {self.player.y})")
            self.add_to_log(f"DESCENDED to stairs up: ({self.player.x}, {self.player.y})", (0, 255, 255))
        else:
            # Fallback to start position
            self.player.x, self.player.y = self.dungeon.start_pos
            print(f"DEBUG: DESCENDED to start pos: ({self.player.x}, {self.player.y})")
            self.add_to_log(f"DESCENDED to start pos: ({self.player.x}, {self.player.y})", (255, 255, 0))
        self.update_camera()
        
        # Spawn enemies
        self.enemy_manager.spawn_enemies_in_dungeon(
            self.dungeon,
            player_start_pos=self.dungeon.start_pos,
            dungeon_level=self.dungeon_level
        )
        
        self.add_to_log(f"Descended to dungeon level {self.dungeon_level}!", (255, 200, 100))
        self.add_to_log("The darkness grows deeper...", (100, 100, 200))
        
        # Level-specific messages
        if self.dungeon_level == 2:
            self.add_to_log("You hear the skittering of spiders...", (150, 100, 150))
        elif self.dungeon_level == 3:
            self.add_to_log("Goblin warrens stretch ahead...", (100, 150, 100))
        elif self.dungeon_level == 4:
            self.add_to_log("Ancient magic permeates the air...", (200, 100, 200))
        elif self.dungeon_level == 5:
            self.add_to_log("You have reached the deepest depths!", (255, 100, 100))
    
    def _try_go_down_stairs(self):
        """Try to go down stairs - only works if standing on stairs."""
        if self.current_area == GameArea.TOWN:
            # Check if standing on dungeon entrance in town
            cell = self.town.get_cell(self.player.x, self.player.y)
            if cell == CellType.DUNGEON_ENTRANCE:
                print(f"DEBUG: Using village stairs at ({self.player.x}, {self.player.y}) to enter dungeon")
                self._enter_dungeon()
            else:
                self.add_to_log("You need to stand on the dungeon entrance!", (255, 255, 100))
        elif self.current_area == GameArea.DUNGEON:
            # Check if standing on stairs down in dungeon
            if (self.dungeon.staircase_pos and 
                (self.player.x, self.player.y) == self.dungeon.staircase_pos):
                print(f"DEBUG: Using dungeon stairs down at ({self.player.x}, {self.player.y}) to go to level {self.dungeon_level + 1}")
                self._go_down_stairs()
            else:
                self.add_to_log("You need to stand on the stairs down to go down!", (255, 255, 100))
        else:
            self.add_to_log("You can only use stairs in town or dungeon!", (255, 255, 100))
    
    def _try_go_up_stairs(self):
        """Try to go up stairs - only works if standing on stairs up."""
        if self.current_area != GameArea.DUNGEON:
            self.add_to_log("You can only use stairs in the dungeon!", (255, 255, 100))
            return
            
        # Check if standing on staircase up position
        if (self.dungeon.staircase_up_pos and 
            (self.player.x, self.player.y) == self.dungeon.staircase_up_pos):
            if self.dungeon_level <= 1:
                print(f"DEBUG: Using dungeon stairs up at ({self.player.x}, {self.player.y}) to return to village")
            else:
                print(f"DEBUG: Using dungeon stairs up at ({self.player.x}, {self.player.y}) to go to level {self.dungeon_level - 1}")
            self._go_up_stairs()
        else:
            self.add_to_log("You need to stand on the stairs up to go up!", (255, 255, 100))
    
    def _go_up_stairs(self):
        """Go up to the previous dungeon level or return to town."""
        if self.dungeon_level <= 1:
            # Going up from level 1 returns to town
            self.add_to_log("You climb up to the surface...", (200, 200, 200))
            
            # Save current level data
            self._save_level_data(self.dungeon_level)
            
            # Clear level-specific data and return to town
            self._clear_level_data()
            self.current_area = GameArea.TOWN
            
            # Restore town data
            self._restore_town_data()
            
            # Place player exactly on dungeon entrance stairs
            stairs_x, stairs_y = self.town.dungeon_entrance
            self.player.x, self.player.y = stairs_x, stairs_y
            self.update_camera()
            self.add_to_log("Welcome back to town!", (100, 255, 100))
            print(f"DEBUG: Standing on stairs at ({stairs_x}, {stairs_y})")
            self.add_to_log(f"Standing on stairs at ({stairs_x}, {stairs_y})", (255, 255, 0))
            return
        
        self.add_to_log("You climb up to the previous level...", (200, 200, 200))
        
        # Save current level data
        self._save_level_data(self.dungeon_level)
        
        self.dungeon_level -= 1
        
        # Restore level data (should always exist for going up)
        if self._restore_level_data(self.dungeon_level):
            # Restored level, place player at staircase position (coming from below)
            if self.dungeon.staircase_pos:
                self.player.x, self.player.y = self.dungeon.staircase_pos
                print(f"DEBUG: ASCENDED to stairs down: ({self.player.x}, {self.player.y})")
                self.add_to_log(f"ASCENDED to stairs down: ({self.player.x}, {self.player.y})", (0, 255, 255))
            else:
                # Fallback to start position
                self.player.x, self.player.y = self.dungeon.start_pos
                print(f"DEBUG: ASCENDED to start pos: ({self.player.x}, {self.player.y})")
                self.add_to_log(f"ASCENDED to start pos: ({self.player.x}, {self.player.y})", (255, 255, 0))
            self.update_camera()
        else:
            # Fallback: create new level (shouldn't happen)
            self._clear_level_data_for_new_level()
            self.dungeon = Dungeon(50, 40, self.dungeon_level)
            
            # Place player at staircase position (stairs going down)
            if self.dungeon.staircase_pos:
                self.player.x, self.player.y = self.dungeon.staircase_pos
                print(f"DEBUG: ASCENDED to stairs down: ({self.player.x}, {self.player.y})")
                self.add_to_log(f"ASCENDED to stairs down: ({self.player.x}, {self.player.y})", (0, 255, 255))
            else:
                # Fallback to start position
                self.player.x, self.player.y = self.dungeon.start_pos
                print(f"DEBUG: ASCENDED to start pos: ({self.player.x}, {self.player.y})")
                self.add_to_log(f"ASCENDED to start pos: ({self.player.x}, {self.player.y})", (255, 255, 0))
            self.update_camera()
            
            # Spawn enemies
            self.enemy_manager.spawn_enemies_in_dungeon(
                self.dungeon,
                player_start_pos=self.dungeon.start_pos,
                dungeon_level=self.dungeon_level
            )
        
        self.add_to_log(f"Ascended to dungeon level {self.dungeon_level}!", (255, 200, 100))
        self.add_to_log("The air feels lighter here...", (100, 200, 100))
    
    def _return_to_town(self):
        """Return to town from the dungeon."""
        if self.current_area == GameArea.DUNGEON:
            self.add_to_log("You make your way back to town...", (200, 200, 200))
            
            # Save current level data before leaving
            self._save_level_data(self.dungeon_level)
            
            # Clear level-specific data (preserve town data)
            self._clear_level_data()
            
            self.current_area = GameArea.TOWN
            
            # Restore town data
            self._restore_town_data()
            
            # Place player exactly on dungeon entrance stairs
            stairs_x, stairs_y = self.town.dungeon_entrance
            self.player.x, self.player.y = stairs_x, stairs_y
            self.update_camera()
            self.add_to_log("Welcome back to town!", (100, 255, 100))
            print(f"DEBUG: Standing on stairs at ({stairs_x}, {stairs_y})")
            self.add_to_log(f"Standing on stairs at ({stairs_x}, {stairs_y})", (255, 255, 0))
        else:
            self.add_to_log("You're already in town!", (255, 255, 100))
    
    def _open_chest(self):
        """Open a chest and get loot."""
        # Simple loot generation
        loot_types = ["gold", "health potion", "weapon", "armour"]
        loot = random.choice(loot_types)
        
        if loot == "gold":
            amount = random.randint(10, 50)
            self.add_to_log(f"Found {amount} gold!", (255, 255, 100))
        elif loot == "health potion":
            self.player.character.heal(20)
            self.add_to_log("Found a health potion! +20 HP", (100, 255, 100))
        else:
            self.add_to_log(f"Found {loot}!", (200, 200, 255))
    
    def _talk_to_npc(self, npc: NPC):
        """Talk to an NPC."""
        dialogue = npc.get_dialogue()
        self.add_to_log(f"{npc.name}: {dialogue}", (255, 255, 200))
        
        # Special NPC actions
        if npc.npc_type == "shopkeeper":
            self.add_to_log("(Shop functionality coming soon!)", (200, 200, 200))
        elif npc.npc_type == "innkeeper":
            self.add_to_log("(Rest functionality coming soon!)", (200, 200, 200))
        elif npc.npc_type == "blacksmith":
            self.add_to_log("(Repair functionality coming soon!)", (200, 200, 200))
        elif npc.npc_type == "priest":
            self.add_to_log("(Blessing functionality coming soon!)", (200, 200, 200))
    
    def _check_special_tiles(self, x: int, y: int):
        """Check for special tile interactions."""
        if self.current_area == GameArea.DUNGEON:
            cell = self.dungeon.get_cell(x, y)
            if cell == CellType.HP_PICKUP:
                self.player.character.heal(10)
                self.add_to_log("Found health pickup! +10 HP", (100, 255, 100))
                # Remove the pickup
                self.dungeon.grid[y][x] = CellType.FLOOR
    
    def _show_character_sheet(self):
        """Show character information."""
        if self.player:
            char = self.player.character
            self.add_to_log(f"=== {char.name} (Level {char.level}) ===", (255, 255, 100))
            self.add_to_log(f"HP: {char.current_hp}/{char.max_hp}", (255, 100, 100))
            self.add_to_log(f"Experience: {char.experience}", (100, 100, 255))
    
    def _show_inventory(self):
        """Show inventory."""
        if self.player:
            char = self.player.character
            self.add_to_log("=== Inventory ===", (255, 255, 100))
            if char.inventory.items:
                for item in char.inventory.items[:5]:  # Show first 5 items
                    self.add_to_log(f"- {item.name}", (200, 200, 200))
            else:
                self.add_to_log("Empty", (150, 150, 150))
    
    def update(self, dt: float):
        """Update game state."""
        if self.state_manager.current_state != GameState.PLAYING:
            return
        
        # Don't update game logic when paused
        if self.is_paused:
            print("DEBUG: Game is paused, skipping update")
            return
        
        # Update light flickering effect
        self._update_light_flicker(dt)
        
        # Update fog of war
        self._update_fog_of_war()
        
        # Update auto-explore
        self._update_auto_explore()
        
        # Update click navigation
        self._update_click_navigation()
        
        # Update enemies
        if self.current_area == GameArea.DUNGEON and self.player:
            current_time = pygame.time.get_ticks() / 1000.0
            attacking_enemies = self.enemy_manager.update_all_enemies(
                current_time, 
                self.player.x, 
                self.player.y, 
                self.dungeon
            )
            
            # Handle enemy attacks
            for enemy in attacking_enemies:
                self._enemy_attack_player(enemy)
    
    def render(self):
        """Render the game."""
        if self.state_manager.current_state != GameState.PLAYING:
            self.state_manager.render()
            return
        
        # Clear screen - red on black theme
        self.screen.fill((0, 0, 0))
        
        # Draw frame around gameplay area
        self._render_game_frame()
        
        if self.current_area == GameArea.TOWN:
            self._render_town()
        else:
            self._render_dungeon()
        
        # Render player
        if self.player:
            self._render_player()
        
        # Render enemies
        if self.current_area == GameArea.DUNGEON:
            self._render_enemies()
        
        # Render NPCs
        if self.current_area == GameArea.TOWN:
            self._render_npcs()
            self._render_painted_sprites()
        
        # Render UI
        self._render_ui()
        
        # Render XP bar
        self._render_xp_bar()
        
        # Render skill popup
        if self.skill_popup_open:
            self._render_skill_popup()
        
        # Render log popup
        if self.log_popup_open:
            self._render_log_popup()
        
        # Render pause overlay
        if self.is_paused:
            self._render_pause_overlay()
    
    def _render_game_frame(self):
        """Render a frame around the gameplay area."""
        frame_color = (100, 100, 100)
        frame_thickness = 2
        
        # Use full screen dimensions
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        gameplay_height = screen_height - 60
        
        # Draw frame around gameplay area
        pygame.draw.rect(self.screen, frame_color, 
                        (0, 0, screen_width, gameplay_height), 
                        frame_thickness)
        
        # Draw bottom frame area
        pygame.draw.rect(self.screen, (40, 40, 50), 
                        (0, gameplay_height, screen_width, 60))
    
    def _render_town(self):
        """Render the town using sprites."""
        # Calculate available gameplay area (screen height - 60 pixels for bottom frame)
        gameplay_height = self.screen.get_height() - 60
        
        for y in range(self.town.height):
            for x in range(self.town.width):
                # Only render if tile is visible or explored
                if not (self._is_tile_visible(x, y) or self._is_tile_explored(x, y)):
                    continue
                    
                screen_x = (x - self.camera_x) * self.tile_size
                screen_y = (y - self.camera_y) * self.tile_height
                
                if (screen_x >= -self.tile_size and screen_x < self.screen.get_width() + self.tile_size and
                    screen_y >= -self.tile_height and screen_y < gameplay_height + self.tile_height):
                    
                    cell = self.town.get_cell(x, y)
                    # Always show walls if explored, even if not currently visible
                    if cell in [CellType.TOWN_WALL, CellType.TOWN_BUILDING] and self._is_tile_explored(x, y):
                        self._render_cell_with_sprite(cell, screen_x, screen_y, x, y, dimmed=not self._is_tile_visible(x, y))
                    elif self._is_tile_visible(x, y):
                        self._render_cell_with_sprite(cell, screen_x, screen_y, x, y)
                    elif self._is_tile_explored(x, y):
                        # Show explored areas as dimmed
                        self._render_cell_with_sprite(cell, screen_x, screen_y, x, y, dimmed=True)
        
        # Render click navigation path
        self._render_click_path()
    
    def _render_dungeon(self):
        """Render the dungeon using sprites."""
        # Calculate available gameplay area (screen height - 60 pixels for bottom frame)
        gameplay_height = self.screen.get_height() - 60
        
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                # Only render if tile is visible or explored
                if not (self._is_tile_visible(x, y) or self._is_tile_explored(x, y)):
                    continue
                    
                screen_x = (x - self.camera_x) * self.tile_size
                screen_y = (y - self.camera_y) * self.tile_height
                
                if (screen_x >= -self.tile_size and screen_x < self.screen.get_width() + self.tile_size and
                    screen_y >= -self.tile_height and screen_y < gameplay_height + self.tile_height):
                    
                    cell = self.dungeon.get_cell(x, y)
                    # Always show walls if explored, even if not currently visible
                    if cell == CellType.WALL and self._is_tile_explored(x, y):
                        self._render_cell_with_sprite(cell, screen_x, screen_y, x, y, dimmed=not self._is_tile_visible(x, y))
                    elif self._is_tile_visible(x, y):
                        self._render_cell_with_sprite(cell, screen_x, screen_y, x, y)
                    elif self._is_tile_explored(x, y):
                        # Show explored areas as dimmed
                        self._render_cell_with_sprite(cell, screen_x, screen_y, x, y, dimmed=True)
        
        # Render click navigation path
        self._render_click_path()
    
    def _render_cell_with_sprite(self, cell: CellType, screen_x: int, screen_y: int, x: int = None, y: int = None, dimmed: bool = False):
        """Render a cell using sprites or fallback to colors."""
        # Try to use sprites first
        sprite_name = self._get_cell_sprite(cell, x, y)
        if sprite_name and self.sprite_manager.sprite_system.get_sprite(sprite_name):
            # Draw sprite without centering offsets for tighter layout
            # Dim the sprite if requested
            if dimmed:
                # Apply darker tinting for fog of war
                tint_color = self._get_fog_of_war_tint()
            else:
                # Apply light flickering effect to visible sprites
                base_tint = self._get_dungeon_level_tint()
                if base_tint:
                    # Adjust tint based on flicker intensity
                    flicker_factor = self.light_flicker_intensity
                    tint_color = tuple(c * flicker_factor for c in base_tint)
                else:
                    # If no base tint, apply flicker directly
                    flicker_factor = self.light_flicker_intensity
                    tint_color = (flicker_factor, flicker_factor, flicker_factor)
            self.sprite_manager.sprite_system.draw_sprite(
                self.screen, sprite_name, screen_x, screen_y, 
                scale=1, prevent_overlap=False, tint_color=tint_color
            )
        else:
            # Fallback to color rendering
            color = self._get_cell_color(cell)
            if dimmed:
                # Reduce all RGB values by 30% (70% of original) to match sprite tinting
                color = self._darken_color(color, 0.7)
            else:
                # Apply light flickering effect to visible colours
                flicker_factor = self.light_flicker_intensity
                color = tuple(int(c * flicker_factor) for c in color)
            pygame.draw.rect(self.screen, color, 
                           (screen_x, screen_y, self.tile_size, self.tile_height))
    
    def _get_cell_sprite(self, cell: CellType, x: int = None, y: int = None) -> Optional[str]:
        """Get sprite name for a cell type."""
        # Use cached sprite if available
        if x is not None and y is not None and (x, y) in self.tile_sprites:
            return self.tile_sprites[(x, y)]
        
        # Get sprite for cell type (random for walls and floors)
        if cell in [CellType.WALL, CellType.TOWN_WALL, CellType.TOWN_BUILDING]:
            sprite_name = self._get_random_wall_sprite()
        elif cell in [CellType.FLOOR, CellType.TOWN_FLOOR]:
            sprite_name = self._get_random_floor_sprite()
        else:
            # Static sprites for other cell types
            base_sprites = {
            CellType.DOOR: "window",
                CellType.STAIRCASE: self._get_stair_sprite(x, y),
            CellType.CHEST: "prison gate",  # Use prison gate as chest
            CellType.HP_PICKUP: "bubbles 1",  # Use bubbles as health pickup
            CellType.TOWN_DOOR: "window",
            CellType.DUNGEON_ENTRANCE: "stairs down",
        }
            sprite_name = base_sprites.get(cell)
        
        # Cache the sprite for consistency
        if x is not None and y is not None and sprite_name:
            self.tile_sprites[(x, y)] = sprite_name
            
        return sprite_name
    
    def _get_random_wall_sprite(self) -> str:
        """Get a random wall sprite."""
        wall_sprites = ["Wall", "wall dmg 1", "wall dmg 2", "wall dmg 3", "wall dmg 4", "wall dmg 5", "wall dmg 6"]
        return random.choice(wall_sprites)
    
    def _get_random_floor_sprite(self) -> str:
        """Get a random floor sprite."""
        floor_sprites = ["floor", "floor2"]
        return random.choice(floor_sprites)
    
    def _get_stair_sprite(self, x: int, y: int) -> str:
        """Get the appropriate stair sprite based on position."""
        if not self.dungeon:
            return "stairs down"  # Default fallback
        
        # Check if this is the staircase going up (where player entered)
        if (self.dungeon.staircase_up_pos and 
            (x, y) == self.dungeon.staircase_up_pos):
            return "stairs up"
        
        # Check if this is the staircase going down (to next level)
        if (self.dungeon.staircase_pos and 
            (x, y) == self.dungeon.staircase_pos):
            return "stairs down"
        
        # Default to stairs down if we can't determine
        return "stairs down"
    
    def _get_dungeon_level_tint(self) -> Optional[Tuple[float, float, float]]:
        """Get tint color based on dungeon level."""
        if self.current_area != GameArea.DUNGEON:
            return None  # No tint for town
        
        # Brown-ish tint for level 1
        if self.dungeon_level == 1:
            return (1.0, 0.7, 0.5)  # Brown-ish tint (red boost, green/blue reduce)
        elif self.dungeon_level == 2:
            return (0.7, 0.7, 1.0)  # Blue-ish tint for level 2
        elif self.dungeon_level == 3:
            return (0.5, 1.0, 0.5)  # Green-ish tint for level 3
        elif self.dungeon_level == 4:
            return (1.0, 0.5, 1.0)  # Purple-ish tint for level 4
        elif self.dungeon_level == 5:
            return (0.3, 0.3, 0.3)  # Dark tint for deepest level
        
        return None  # No tint for other levels
    
    def _get_cell_color(self, cell: CellType) -> Tuple[int, int, int]:
        """Get color for a cell type (fallback when sprites not available)."""
        colors = {
            CellType.WALL: (100, 100, 100),
            CellType.FLOOR: (50, 50, 50),
            CellType.DOOR: (139, 69, 19),
            CellType.STAIRCASE: (200, 200, 100),
            CellType.CHEST: (255, 215, 0),
            CellType.HP_PICKUP: (255, 100, 100),
            CellType.TOWN_FLOOR: (100, 150, 100),
            CellType.TOWN_WALL: (150, 100, 100),
            CellType.TOWN_DOOR: (139, 69, 19),
            CellType.TOWN_BUILDING: (120, 80, 80),
            CellType.DUNGEON_ENTRANCE: (100, 50, 150),
        }
        return colors.get(cell, (0, 0, 0))
    
    def _darken_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Darken a colour by reducing all RGB values by the given factor."""
        return tuple(int(c * factor) for c in color)
    
    def _get_fog_of_war_tint(self) -> Tuple[float, float, float]:
        """Get tint colour for fog of war - use a more neutral darkening approach."""
        return (0.4, 0.4, 0.4)  # Lighter tint to preserve more of the original colour
    
    def _render_player(self):
        """Render the player using sprites."""
        # Calculate available gameplay area (screen height - 60 pixels for bottom frame)
        gameplay_height = self.screen.get_height() - 60
        
        screen_x = (self.player.x - self.camera_x) * self.tile_size
        screen_y = (self.player.y - self.camera_y) * self.tile_height
        
        if (screen_x >= -self.tile_size and screen_x < self.screen.get_width() + self.tile_size and
            screen_y >= -self.tile_height and screen_y < gameplay_height + self.tile_height):
            
            # Try to use player sprite
            player_sprite = self._get_player_sprite()
            if player_sprite and self.sprite_manager.sprite_system.get_sprite(player_sprite):
                # Apply darker tint if player is in fog of war (explored but not visible)
                tint_color = None
                if self._is_tile_explored(self.player.x, self.player.y) and not self._is_tile_visible(self.player.x, self.player.y):
                    tint_color = self._get_fog_of_war_tint()
                
                # Draw player sprite without centering offsets
                self.sprite_manager.sprite_system.draw_sprite(
                    self.screen, player_sprite, screen_x, screen_y, 
                    scale=1, prevent_overlap=False, tint_color=tint_color
                )
            else:
                # Fallback to colored circle
                center_x = screen_x + self.tile_size // 2
                center_y = screen_y + self.tile_height // 2
                # Apply darker colour for fog of war
                if self._is_tile_explored(self.player.x, self.player.y) and not self._is_tile_visible(self.player.x, self.player.y):
                    color = self._darken_color((100, 150, 255), 0.7)  # Reduce blue by 30%
                else:
                    color = (100, 150, 255)  # Normal blue
                pygame.draw.circle(self.screen, color, (center_x, center_y), self.tile_size // 3)
    
    
    def _get_player_sprite(self) -> str:
        """Get player sprite - same avatar for all character classes."""
        return "avatar left"
    
    def _render_enemies(self):
        """Render enemies using sprites."""
        # Calculate available gameplay area (screen height - 60 pixels for bottom frame)
        gameplay_height = self.screen.get_height() - 60
        
        for i, enemy in enumerate(self.enemy_manager.get_living_enemies()):
            enemy_id = f"enemy_{i}_{enemy.enemy_type.name}_{enemy.x}_{enemy.y}"
            # Render if enemy is visible or has a last known position
            if not self._is_tile_visible(enemy.x, enemy.y) and enemy_id not in self.last_known_positions:
                continue
                
            # Use current position if visible, otherwise use last known position
            if self._is_tile_visible(enemy.x, enemy.y):
                render_x, render_y = enemy.x, enemy.y
            else:
                render_x, render_y, _ = self.last_known_positions[enemy_id]
            
            screen_x = (render_x - self.camera_x) * self.tile_size
            screen_y = (render_y - self.camera_y) * self.tile_height
            
            if (screen_x >= -self.tile_size and screen_x < self.screen.get_width() + self.tile_size and
                screen_y >= -self.tile_height and screen_y < gameplay_height + self.tile_height):
                
                # Try to use enemy sprite
                enemy_sprite = self._get_enemy_sprite(enemy.enemy_type)
                if enemy_sprite and self.sprite_manager.sprite_system.get_sprite(enemy_sprite):
                    # Draw enemy sprite without centering offsets
                    # Dim the sprite if using last known position
                    tint_color = self._get_fog_of_war_tint() if not self._is_tile_visible(enemy.x, enemy.y) else None
                    
                    # Add damage flash effect
                    if hasattr(enemy, 'damage_flash') and enemy.damage_flash > 0:
                        flash_intensity = enemy.damage_flash
                        if tint_color:
                            tint_color = (1.0, 0.3, 0.3)  # Red flash
                        else:
                            tint_color = (1.0, 0.3, 0.3)  # Red flash
                    
                    self.sprite_manager.sprite_system.draw_sprite(
                        self.screen, enemy_sprite, screen_x, screen_y, 
                        scale=1, prevent_overlap=False, tint_color=tint_color
                    )
                else:
                    # Fallback to colored circle
                    center_x = screen_x + self.tile_size // 2
                    center_y = screen_y + self.tile_height // 2
                    # Dim the circle if using last known position
                    color = self._darken_color((255, 100, 100), 0.7) if not self._is_tile_visible(enemy.x, enemy.y) else (255, 100, 100)
                    
                    # Add damage flash effect
                    if hasattr(enemy, 'damage_flash') and enemy.damage_flash > 0:
                        flash_intensity = enemy.damage_flash
                        color = (255, int(100 * (1 - flash_intensity)), int(100 * (1 - flash_intensity)))
                    
                    pygame.draw.circle(self.screen, color, (center_x, center_y), self.tile_size // 4)
    
    def _get_enemy_sprite(self, enemy_type: EnemyType) -> str:
        """Get enemy sprite based on enemy type."""
        enemy_sprites = {
            EnemyType.CHICKEN: "bird",  # Use bird sprite for chicken
            EnemyType.FROG: "frog",
            EnemyType.SNAKE: "snake",
            EnemyType.BIRD: "bird",
            EnemyType.SPIDER: "spider",
            EnemyType.GOBLIN: "goblin"
        }
        return enemy_sprites.get(enemy_type, "slime")  # Use slime as fallback
    
    def _render_npcs(self):
        """Render NPCs in the town."""
        # Calculate available gameplay area (screen height - 60 pixels for bottom frame)
        gameplay_height = self.screen.get_height() - 60
        
        for npc in self.town.npcs:
            npc_id = f"npc_{npc.name}_{npc.x}_{npc.y}"
            # Render if NPC is visible or has a last known position
            if not self._is_tile_visible(npc.x, npc.y) and npc_id not in self.last_known_positions:
                continue
                
            # Use current position if visible, otherwise use last known position
            if self._is_tile_visible(npc.x, npc.y):
                render_x, render_y = npc.x, npc.y
            else:
                render_x, render_y, _ = self.last_known_positions[npc_id]
                
            screen_x = (render_x - self.camera_x) * self.tile_size
            screen_y = (render_y - self.camera_y) * self.tile_height
            
            if (screen_x >= -self.tile_size and screen_x < self.screen.get_width() + self.tile_size and
                screen_y >= -self.tile_height and screen_y < gameplay_height + self.tile_height):
                
                # Try to use NPC sprite
                npc_sprite = self._get_npc_sprite(npc.npc_type)
                if npc_sprite and self.sprite_manager.sprite_system.get_sprite(npc_sprite):
                    # Draw NPC sprite without centering offsets
                    # Dim the sprite if using last known position
                    tint_color = self._get_fog_of_war_tint() if not self._is_tile_visible(npc.x, npc.y) else None
                    self.sprite_manager.sprite_system.draw_sprite(
                        self.screen, npc_sprite, screen_x, screen_y, 
                        scale=1, prevent_overlap=False, tint_color=tint_color
                    )
                else:
                    # Fallback to colored circle
                    center_x = screen_x + self.tile_size // 2
                    center_y = screen_y + self.tile_height // 2
                    # Dim the circle if using last known position
                    color = self._darken_color((255, 255, 100), 0.7) if not self._is_tile_visible(npc.x, npc.y) else (255, 255, 100)
                    pygame.draw.circle(self.screen, color, (center_x, center_y), self.tile_size // 4)
    
    def _render_painted_sprites(self):
        """Render painted sprites in the town."""
        # Calculate available gameplay area (screen height - 60 pixels for bottom frame)
        gameplay_height = self.screen.get_height() - 60
        
        for (grid_x, grid_y), sprite_name in self.town.painted_sprites.items():
            screen_x = (grid_x - self.camera_x) * self.tile_size
            screen_y = (grid_y - self.camera_y) * self.tile_height
            
            if (screen_x >= -self.tile_size and screen_x < self.screen.get_width() + self.tile_size and
                screen_y >= -self.tile_height and screen_y < gameplay_height + self.tile_height):
                
                if self.sprite_manager.sprite_system.get_sprite(sprite_name):
                    # Apply fog of war dimming if not visible
                    tint_color = None
                    if not self._is_tile_visible(grid_x, grid_y):
                        tint_color = self._get_fog_of_war_tint()
                    
                    # Draw painted sprite without centering offsets
                    self.sprite_manager.sprite_system.draw_sprite(
                        self.screen, sprite_name, screen_x, screen_y, 
                        scale=1, prevent_overlap=False, tint_color=tint_color
                    )
    
    def _get_npc_sprite(self, npc_type: str) -> str:
        """Get NPC sprite based on NPC type."""
        npc_sprites = {
            "shopkeeper": "big grass",
            "innkeeper": "grass flowers", 
            "blacksmith": "shrub",
            "priest": "lily pad 2"
        }
        return npc_sprites.get(npc_type, "big grass")
    
    def _render_ui(self):
        """Render the user interface."""
        # UI positioning relative to actual window edges
        ui_base_x = 10
        ui_base_y = self.screen.get_height() - 60
        
        # Player stats and health bar
        if self.player:
            char = self.player.character
            stats_text = f"Level: {char.level} | Area: {self.current_area.value.title()}"
            if self.current_area == GameArea.DUNGEON:
                stats_text += f" | Dungeon Level: {self.dungeon_level}"
            
            text = self.font.render(stats_text, True, (255, 255, 255))
            self.screen.blit(text, (ui_base_x, ui_base_y))
            
            # Health bar
            self._render_health_bar(char.current_hp, char.max_hp, ui_base_x, ui_base_y + 20)
            
            # Mana bar
            self._render_mana_bar(char.current_mana, char.max_mana, ui_base_x + 210, ui_base_y + 20)
        
        # Game log in bottom bar
        self._render_log_panel()
    
    def _render_health_bar(self, current_hp: int, max_hp: int, x: int, y: int):
        """Render a health bar."""
        bar_width = 200
        bar_height = 20
        
        # Background (red)
        pygame.draw.rect(self.screen, (100, 0, 0), (x, y, bar_width, bar_height))
        
        # Health (green)
        health_percentage = current_hp / max_hp if max_hp > 0 else 0
        health_width = int(bar_width * health_percentage)
        pygame.draw.rect(self.screen, (0, 255, 0), (x, y, health_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)
        
        # Text
        hp_text = f"HP: {current_hp}/{max_hp}"
        text = self.small_font.render(hp_text, True, (255, 255, 255))
        text_x = x + (bar_width - text.get_width()) // 2
        text_y = y + (bar_height - text.get_height()) // 2
        self.screen.blit(text, (text_x, text_y))
    
    def _render_mana_bar(self, current_mana: int, max_mana: int, x: int, y: int):
        """Render a mana bar."""
        bar_width = 200
        bar_height = 20
        
        # Background (dark blue)
        pygame.draw.rect(self.screen, (0, 0, 100), (x, y, bar_width, bar_height))
        
        # Mana (blue)
        mana_percentage = current_mana / max_mana if max_mana > 0 else 0
        mana_width = int(bar_width * mana_percentage)
        pygame.draw.rect(self.screen, (0, 150, 255), (x, y, mana_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)
        
        # Text
        mana_text = f"MP: {current_mana}/{max_mana}"
        text = self.small_font.render(mana_text, True, (255, 255, 255))
        text_x = x + (bar_width - text.get_width()) // 2
        text_y = y + (bar_height - text.get_height()) // 2
        self.screen.blit(text, (text_x, text_y))
    
    def _render_xp_bar(self):
        """Render XP bar at the top of the bottom border, just below play area."""
        if not self.player or not self.player.character:
            return
        
        from system.perk_system import PerkSystem
        perk_system = PerkSystem()
        
        # Calculate XP progress
        current_level = self.player.character.level
        current_exp = self.player.character.experience
        current_level_exp = perk_system.calculate_experience_required(current_level)
        next_level_exp = perk_system.calculate_experience_required(current_level + 1)
        
        # XP progress within current level
        exp_in_level = current_exp - current_level_exp
        exp_needed = next_level_exp - current_level_exp
        
        # Bar dimensions - span the full width, positioned at top of bottom border
        bar_height = 12
        # Position just below the play area (above the 60px bottom border)
        bar_y = self.screen.get_height() - 60 - bar_height
        
        # Background (dark)
        pygame.draw.rect(self.screen, (50, 50, 50), (0, bar_y, self.screen.get_width(), bar_height))
        
        # XP progress (white)
        if exp_needed > 0:
            xp_percentage = exp_in_level / exp_needed
            xp_width = int(self.screen.get_width() * xp_percentage)
            pygame.draw.rect(self.screen, (255, 255, 255), (0, bar_y, xp_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, (200, 200, 200), (0, bar_y, self.screen.get_width(), bar_height), 1)
        
        # XP text
        xp_text = f"XP: {exp_in_level}/{exp_needed} (Level {current_level})"
        text = self.small_font.render(xp_text, True, (255, 255, 255))
        text_x = (self.screen.get_width() - text.get_width()) // 2
        text_y = bar_y + (bar_height - text.get_height()) // 2
        self.screen.blit(text, (text_x, text_y))
    
    def _render_log_panel(self):
        """Render the game log panel in the bottom bar - right side extending to edge."""
        if not self.log_messages:
            return
        
        # Log panel dimensions - right third extending to the actual edge
        panel_width = self.screen.get_width() // 3  # Right third of actual screen width
        panel_height = 60  # Full height of bottom border
        panel_x = self.screen.get_width() - panel_width  # Right side extending to actual edge
        panel_y = self.screen.get_height() - 60
        
        # Dark background
        pygame.draw.rect(self.screen, (30, 30, 30), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, (100, 100, 100), (panel_x, panel_y, panel_width, panel_height), 1)
        
        # Show most recent messages at top, limit to 6 messages
        total_messages = len(self.log_messages)
        max_visible = 6  # Limit to 6 messages
        start_index = max(0, total_messages - max_visible)
        
        # Render log messages (most recent first, with fading saturation)
        y_offset = panel_y + 5
        for i in range(total_messages - 1, start_index - 1, -1):  # Reverse order - newest first
            if i >= 0 and i < len(self.log_messages):
                message, original_color = self.log_messages[i]
                
                # Calculate saturation fade based on position (0 = most recent, 5 = oldest)
                position = total_messages - 1 - i
                saturation_factor = max(0.3, 1.0 - (position * 0.12))  # Fade from 100% to 30%
                
                # Apply saturation fade to color
                faded_color = tuple(int(c * saturation_factor) for c in original_color)
                
                # Truncate long messages based on available width
                max_chars = (panel_width - 10) // 8  # Approximate character width
                if len(message) > max_chars:
                    message = message[:max_chars-3] + "..."
                
                text = self.small_font.render(message, True, faded_color)
                self.screen.blit(text, (panel_x + 5, y_offset))
                y_offset += 10  # Slightly tighter spacing for 6 messages
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            # Handle events
            for event in pygame.event.get():
                self.handle_input(event)
            
            # Update game
            self.update(dt)
            
            # Render
            self.render()
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def _handle_mouse_click(self, pos):
        """Handle mouse click for pathfinding and log scrolling."""
        if not self.player or self.is_dead:
            return
        
        
        # Convert screen coordinates to tile coordinates
        tile_x, tile_y = self._screen_to_tile_coords(pos[0], pos[1])
        
        # Debug logging
        print(f"DEBUG: Click at screen ({pos[0]}, {pos[1]}) -> tile ({tile_x}, {tile_y})")
        
        # Check if the click is within valid bounds
        if self.current_area == GameArea.TOWN:
            if not (0 <= tile_x < self.town.width and 0 <= tile_y < self.town.height):
                self.add_to_log("Click outside town bounds!", (255, 100, 100))
                return
        elif self.current_area == GameArea.DUNGEON:
            if not (0 <= tile_x < self.dungeon.width and 0 <= tile_y < self.dungeon.height):
                self.add_to_log("Click outside dungeon bounds!", (255, 100, 100))
                return
        
        # Don't check walkability here - let pathfinding handle it
        
        # Cancel auto-explore if active
        if self.auto_explore_active:
            self.auto_explore_active = False
            self.auto_explore_path = []
            self.auto_explore_target = None
            self.add_to_log("Auto-explore cancelled", (255, 255, 255))
        
        # Set up click navigation
        self.click_target = (tile_x, tile_y)
        self.click_navigation_active = True
        
        # Calculate path to target
        start = (self.player.x, self.player.y)
        target = (tile_x, tile_y)
        
        # Check if target is walkable and explored
        can_reach_exact_target = False
        if self.current_area == GameArea.TOWN:
            can_reach_exact_target = (self.town.can_move_to(tile_x, tile_y) and 
                                    self._is_tile_explored(tile_x, tile_y))
        else:
            can_reach_exact_target = (self.dungeon.can_move_to(tile_x, tile_y) and 
                                    self._is_tile_explored(tile_x, tile_y))
        
        print(f"DEBUG: Target ({tile_x}, {tile_y}) - Walkable: {can_reach_exact_target}")
        
        # Try pathfinding with explored areas only first
        if self.current_area == GameArea.TOWN:
            self.click_path = self._find_path_town(start, target)
        else:
            self.click_path = self._find_path(start, target)
        
        # If no path found with explored areas, try allowing unexplored areas
        if not self.click_path:
            print(f"DEBUG: No path with explored areas only, trying with unexplored areas allowed")
            if self.current_area == GameArea.TOWN:
                self.click_path = self._find_path_unified(start, target, allow_unexplored=True)
            else:
                self.click_path = self._find_path_unified(start, target, allow_unexplored=True)
        
        if not self.click_path:
            # Try to find nearest reachable position
            nearest_target = self._find_nearest_reachable_target(start, target)
            if nearest_target and nearest_target != target:
                print(f"DEBUG: No path to exact target ({tile_x}, {tile_y}), trying nearest reachable ({nearest_target[0]}, {nearest_target[1]})")
                if self.current_area == GameArea.TOWN:
                    self.click_path = self._find_path_town(start, nearest_target)
                else:
                    self.click_path = self._find_path(start, nearest_target)
                self.click_target = nearest_target
        
        if not self.click_path:
            self.add_to_log("No path found to target!", (255, 100, 100))
            self.click_navigation_active = False
            self.click_target = None
        else:
            final_target = self.click_path[-1] if self.click_path else target
            path_length = len(self.click_path)
            
            # Provide clear feedback about the path
            if final_target == target:
                self.add_to_log(f"Pathing to ({final_target[0]}, {final_target[1]}) - {path_length} steps", (100, 255, 100))
            else:
                self.add_to_log(f"Pathing to nearest reachable ({final_target[0]}, {final_target[1]}) - {path_length} steps", (255, 255, 100))
            
            print(f"DEBUG: Final target ({final_target[0]}, {final_target[1]}) with {path_length} steps")
    
    def _screen_to_tile_coords(self, screen_x, screen_y):
        """Convert screen coordinates to tile coordinates with improved precision."""
        # Account for camera offset
        world_x = screen_x + self.camera_x * self.tile_size
        world_y = screen_y + self.camera_y * self.tile_height
        
        # Convert to tile coordinates with proper rounding for better accuracy
        tile_x = round(world_x / self.tile_size)
        tile_y = round(world_y / self.tile_height)
        
        return tile_x, tile_y
    
    def _find_nearest_reachable_target(self, start, target):
        """Find the nearest reachable position to the target."""
        import math
        
        # Get the area dimensions
        if self.current_area == GameArea.TOWN:
            width, height = self.town.width, self.town.height
        else:
            width, height = self.dungeon.width, self.dungeon.height
        
        # Search in expanding circles around the target
        max_search_radius = min(width, height) // 2
        
        for radius in range(max_search_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx * dx + dy * dy != radius * radius:
                        continue
                    
                    test_x = target[0] + dx
                    test_y = target[1] + dy
                    
                    # Check bounds
                    if not (0 <= test_x < width and 0 <= test_y < height):
                        continue
                    
                    # Check if position is walkable and explored
                    is_walkable = False
                    if self.current_area == GameArea.TOWN:
                        cell = self.town.get_cell(test_x, test_y)
                        is_walkable = (cell in [CellType.TOWN_FLOOR, CellType.TOWN_DOOR] and 
                                     self._is_tile_explored(test_x, test_y))
                    else:
                        cell = self.dungeon.get_cell(test_x, test_y)
                        is_walkable = (cell in [CellType.FLOOR, CellType.DOOR] and 
                                     self._is_tile_explored(test_x, test_y))
                    
                    if is_walkable:
                        return (test_x, test_y)
        
        return None
    
    def _find_path_unified(self, start, target, allow_unexplored=False, depth=0):
        """Unified A* pathfinding for all cases."""
        if start == target or depth > 50:  # Prevent infinite recursion
            return []
        
        import heapq
        
        def heuristic(pos):
            """Distance heuristic."""
            # Always use Euclidean distance (treat town as dungeon)
            dx = abs(pos[0] - target[0])
            dy = abs(pos[1] - target[1])
            return (dx * dx + dy * dy) ** 0.5
        
        def get_neighbors(pos):
            """Get valid neighboring positions."""
            x, y = pos
            # Always use 8-directional movement (treat town as dungeon)
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            
            neighbors = []
            
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                new_pos = (new_x, new_y)
                
                # Check bounds and walkability (treat town as dungeon)
                # Determine which area we're in
                if self.current_area == GameArea.TOWN:
                    # For town, use dungeon-style pathfinding
                    if (0 <= new_x < self.town.width and 
                        0 <= new_y < self.town.height):
                        # Check if tile is walkable (regardless of exploration when allow_unexplored=True)
                        cell = self.town.get_cell(new_x, new_y)
                        is_walkable = cell in [CellType.TOWN_FLOOR, CellType.TOWN_DOOR]
                        
                        if is_walkable:
                            # Always allow movement when allow_unexplored is True
                            if allow_unexplored:
                                neighbors.append(new_pos)
                            elif self._is_tile_explored(new_x, new_y):
                                neighbors.append(new_pos)
                else:
                    if (0 <= new_x < self.dungeon.width and 
                        0 <= new_y < self.dungeon.height):
                        # Check if tile is walkable (regardless of exploration when allow_unexplored=True)
                        cell = self.dungeon.get_cell(new_x, new_y)
                        is_walkable = cell in [CellType.FLOOR, CellType.DOOR]
                        
                        if is_walkable:
                            # Always allow movement when allow_unexplored is True
                            if allow_unexplored:
                                neighbors.append(new_pos)
                            elif self._is_tile_explored(new_x, new_y):
                                neighbors.append(new_pos)
            
            return neighbors
        
        def get_move_cost(current, neighbor):
            """Get cost of moving from current to neighbor."""
            # Always use dungeon-style movement costs (treat town as dungeon)
            dx = abs(neighbor[0] - current[0])
            dy = abs(neighbor[1] - current[1])
            return 1.4 if dx == 1 and dy == 1 else 1.0
        
        # A* algorithm
        open_set = [(0, start)]  # Priority queue: (f_score, position)
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start)}
        visited = set()
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current in visited:
                continue
                
            visited.add(current)
            
            if current == target:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]
            
            for neighbor in get_neighbors(current):
                if neighbor in visited:
                    continue
                
                move_cost = get_move_cost(current, neighbor)
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # If we can't reach the exact target, try to find the closest reachable tile
        if not allow_unexplored:
            return self._find_closest_reachable_tile(start, target, depth=depth + 1)
        
        return []
    
    def _find_closest_reachable_tile(self, start, target, depth=0):
        """Find the closest reachable tile to the target using expanding radius search."""
        # Prevent infinite recursion
        if depth > 2:
            return []
        target_x, target_y = target
        
        # Search in expanding radius around target
        for radius in range(1, 4):  # Search up to 3 tiles away
            candidates = []
            
            # Check all tiles within radius
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Skip if outside radius
                    if abs(dx) + abs(dy) > radius:
                        continue
                    
                    check_x = target_x + dx
                    check_y = target_y + dy
                    
                    # Check bounds (treat town as dungeon)
                    if self.current_area == GameArea.TOWN:
                        if not (0 <= check_x < self.town.width and 0 <= check_y < self.town.height):
                            continue
                        can_move = (self.town.can_move_to(check_x, check_y) and 
                                  self._is_tile_explored(check_x, check_y))
                    else:
                        if not (0 <= check_x < self.dungeon.width and 0 <= check_y < self.dungeon.height):
                            continue
                        can_move = (self.dungeon.can_move_to(check_x, check_y) and 
                                  self._is_tile_explored(check_x, check_y))
                    
                    if can_move:
                        # Calculate distance to original target
                        distance = abs(check_x - target_x) + abs(check_y - target_y)
                        candidates.append(((check_x, check_y), distance))
            
            # If we found candidates at this radius, pick the closest one
            if candidates:
                # Sort by distance to original target
                candidates.sort(key=lambda x: x[1])
                best_tile = candidates[0][0]
                
                # Try to path to this tile (with depth limit to prevent recursion)
                path = self._find_path_unified(start, best_tile, allow_unexplored=False, depth=depth + 1)
                if path:
                    return path
        
        return []
    
    def _find_path_town(self, start, target):
        """Find path in town using unified pathfinding."""
        return self._find_path_unified(start, target, allow_unexplored=False, depth=0)
    
    
    def _get_enemy_at_position(self, x: int, y: int):
        """Get enemy at specific position, if any."""
        if self.current_area != GameArea.DUNGEON:
            return None
        
        for enemy in self.enemy_manager.enemies:
            if enemy.is_alive and enemy.x == x and enemy.y == y:
                return enemy
        return None
    
    def _attack_enemy(self, enemy):
        """Attack an enemy."""
        if not self.player or not self.player.character:
            return
        
        # Calculate damage
        damage, is_critical = self.player.character.get_attack_damage()
        
        # Apply damage
        enemy.hp -= damage
        enemy.damage_flash = 1.0  # Flash effect
        
        # Combat message
        if is_critical:
            self.add_to_log(f"Critical hit! You deal {damage} damage to {enemy.enemy_type.value}!", (255, 255, 0))
        else:
            self.add_to_log(f"You deal {damage} damage to {enemy.enemy_type.value}!", (255, 200, 100))
        
        # Check if enemy dies
        if enemy.hp <= 0:
            enemy.is_alive = False
            self.add_to_log(f"You killed the {enemy.enemy_type.value}!", (100, 255, 100))
            
            # Give experience
            if self.player.character:
                exp_gained = enemy.exp_value
                level_up_messages = self.player.character.gain_experience(exp_gained)
                self.add_to_log(f"Gained {exp_gained} experience!", (100, 255, 255))
                
                # Display level up messages
                for message in level_up_messages:
                    self.add_to_log(message, (255, 255, 0))
                
                # Show skill point notification if available
                if hasattr(self.player.character, 'attribute_points') and self.player.character.attribute_points > 0:
                    self.add_to_log(f"Press S to allocate {self.player.character.attribute_points} attribute points!", (100, 255, 100))
                if hasattr(self.player.character, 'skill_points') and self.player.character.skill_points > 0:
                    self.add_to_log(f"Press S to allocate {self.player.character.skill_points} skill points!", (100, 255, 100))
        else:
            # Enemy counter-attacks
            self._enemy_attack_player(enemy)
    
    def _enemy_attack_player(self, enemy):
        """Enemy attacks the player."""
        if not self.player or not self.player.character:
            return
        
        # Calculate enemy damage
        enemy_damage = enemy.get_attack_damage()
        
        # Apply damage to player
        self.player.character.take_damage(enemy_damage)
        
        # Combat message
        self.add_to_log(f"{enemy.enemy_type.value} deals {enemy_damage} damage to you!", (255, 100, 100))
        
        # Check if player dies
        if self.player.character.current_hp <= 0:
            self._trigger_death()
    
    def _trigger_death(self):
        """Trigger player death and game over."""
        if self.is_dead:
            return  # Already dead
        
        self.is_dead = True
        self.final_score = self._calculate_score()
        
        # Add to high scores
        self._add_high_score(self.final_score)
        
        # Set game state to game over
        self.state_manager.current_state = GameState.GAME_OVER
        
        self.add_to_log("You have been defeated!", (255, 0, 0))
        self.add_to_log(f"Final Score: {self.final_score}", (255, 255, 0))
        self.add_to_log("Press R to restart or ESC to quit", (255, 255, 255))
    
    def _calculate_score(self) -> int:
        """Calculate final score based on player progress."""
        if not self.player or not self.player.character:
            return 0
        
        char = self.player.character
        score = 0
        
        # Base score from level
        score += char.level * 100
        
        # Score from dungeon level reached
        score += self.dungeon_level * 50
        
        # Score from experience gained
        score += char.experience
        
        # Score from remaining HP (survival bonus)
        if char.current_hp > 0:
            score += char.current_hp * 2
        
        # Score from enemies defeated (approximate)
        # This is a rough estimate based on level and dungeon depth
        estimated_enemies = (char.level - 1) * 3 + self.dungeon_level * 2
        score += estimated_enemies * 25
        
        return max(0, score)
    
    def _load_high_scores(self) -> list:
        """Load high scores from file."""
        import json
        try:
            with open("high_scores.json", 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_high_scores(self):
        """Save high scores to file."""
        import json
        try:
            with open("high_scores.json", 'w') as f:
                json.dump(self.high_scores, f, indent=2)
        except Exception as e:
            print(f"Error saving high scores: {e}")
    
    def _add_high_score(self, score: int):
        """Add a new high score."""
        if not self.player or not self.player.character:
            return
        
        # Create score entry
        score_entry = {
            "score": score,
            "level": self.player.character.level,
            "dungeon_level": self.dungeon_level,
            "class": self.player.character.character_class.value if hasattr(self.player.character, 'character_class') else "Unknown",
            "name": getattr(self.player.character, 'name', 'Unknown')
        }
        
        # Add to high scores
        self.high_scores.append(score_entry)
        
        # Sort by score (highest first) and keep top 10
        self.high_scores.sort(key=lambda x: x["score"], reverse=True)
        self.high_scores = self.high_scores[:10]
        
        # Save to file
        self._save_high_scores()
    
    def _toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            # Get the current display mode
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            self.window_width = info.current_w
            self.window_height = info.current_h
            self.add_to_log("Fullscreen mode enabled", (100, 255, 100))
        else:
            # Return to windowed mode
            self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
            self.add_to_log("Windowed mode enabled", (100, 255, 100))
        
        # Update camera and background
        self.update_camera()
        if hasattr(self, 'state_manager') and self.state_manager:
            self.state_manager.screen = self.screen
            if hasattr(self.state_manager, 'original_background') and self.state_manager.original_background:
                self.state_manager._resize_background()
    
    def _toggle_resizable(self):
        """Toggle resizable window mode."""
        self.resizable = not self.resizable
        
        if self.resizable:
            self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
            self.add_to_log("Resizable window enabled", (100, 255, 100))
        else:
            self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.NOFRAME)
            self.add_to_log("Fixed window enabled", (100, 255, 100))
    
    def _handle_window_resize(self, event):
        """Handle window resize events."""
        if event.type == pygame.VIDEORESIZE:
            self.window_width = event.w
            self.window_height = event.h
            self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
            self.update_camera()
            
            # Update state manager if it exists
            if hasattr(self, 'state_manager') and self.state_manager:
                self.state_manager.screen = self.screen
                if hasattr(self.state_manager, 'original_background') and self.state_manager.original_background:
                    self.state_manager._resize_background()
            
            self.add_to_log(f"Window resized to {self.window_width}x{self.window_height}", (100, 255, 100))
    
    def _restart_game(self):
        """Restart the game from the beginning."""
        if self.state_manager.current_state != GameState.GAME_OVER:
            return
        
        # Reset game state
        self.is_dead = False
        self.final_score = 0
        self.current_area = GameArea.TOWN
        self.dungeon_level = 1
        
        # Clear level data
        self._clear_level_data()
        
        # Clear custom town data to force regeneration
        self.custom_town_data = None
        
        # Reset player
        self.player = None
        
        # Reset auto-explore
        self.auto_explore_active = False
        self.auto_explore_path = []
        self.auto_explore_target = None
        
        # Go back to class selection
        self.state_manager.current_state = GameState.CLASS_SELECTION
        
        self.add_to_log("Starting new game...", (100, 255, 100))
    
    def _toggle_pause(self):
        """Toggle pause state."""
        if self.is_dead:
            return  # Can't pause when dead
        
        self.is_paused = not self.is_paused
        print(f"DEBUG: Pause toggled - is_paused: {self.is_paused}")
        if self.is_paused:
            self.add_to_log("Game paused - press SPACE to resume", (255, 255, 100))
        else:
            self.add_to_log("Game resumed", (100, 255, 100))
    
    def _toggle_skill_popup(self):
        """Toggle skill point allocation popup."""
        if not self.player or not self.player.character:
            return
        
        # Check if player has points to allocate
        has_attribute_points = hasattr(self.player.character, 'attribute_points') and self.player.character.attribute_points > 0
        has_skill_points = hasattr(self.player.character, 'skill_points') and self.player.character.skill_points > 0
        
        if not has_attribute_points and not has_skill_points:
            self.add_to_log("No points to allocate!", (255, 100, 100))
            return
        
        self.skill_popup_open = not self.skill_popup_open
        if self.skill_popup_open:
            self.add_to_log("Skill allocation opened - press S to close", (100, 255, 100))
        else:
            self.add_to_log("Skill allocation closed", (100, 255, 100))
    
    def _toggle_log_popup(self):
        """Toggle log popup window."""
        self.log_popup_open = not self.log_popup_open
        if self.log_popup_open:
            self.log_popup_scroll = 0  # Reset scroll to top
            self.add_to_log("Log popup opened - press L to close", (100, 255, 100))
        else:
            self.add_to_log("Log popup closed", (100, 255, 100))
    
    def _handle_skill_popup_input(self, key):
        """Handle input for skill popup."""
        if not self.player or not self.player.character:
            return
        
        char = self.player.character
        from system.character_system import StatType
        
        # Close popup
        if key == pygame.K_s:
            self.skill_popup_open = False
            self.selected_stat = None
            self.add_to_log("Skill allocation closed", (100, 255, 100))
            return
        
        # Select attribute (1-5)
        if key == pygame.K_1:
            self.selected_stat = 0  # STRENGTH
        elif key == pygame.K_2:
            self.selected_stat = 1  # DEXTERITY
        elif key == pygame.K_3:
            self.selected_stat = 2  # CONSTITUTION
        elif key == pygame.K_4:
            self.selected_stat = 3  # PERCEPTION
        elif key == pygame.K_5:
            self.selected_stat = 4  # MANA
        
        # Allocate/deallocate points
        if key == pygame.K_PLUS or key == pygame.K_KP_PLUS:
            self._allocate_attribute_point(1)
        elif key == pygame.K_MINUS or key == pygame.K_KP_MINUS:
            self._allocate_attribute_point(-1)
    
    def _allocate_attribute_point(self, amount):
        """Allocate or deallocate attribute points."""
        if not self.player or not self.player.character:
            return
        
        char = self.player.character
        from system.character_system import StatType
        
        if self.selected_stat is None:
            self.add_to_log("Select an attribute first (1-5)", (255, 100, 100))
            return
        
        if not hasattr(char, 'attribute_points') or char.attribute_points <= 0:
            self.add_to_log("No attribute points available!", (255, 100, 100))
            return
        
        # Map selected stat to StatType
        attributes = [StatType.STRENGTH, StatType.DEXTERITY, StatType.CONSTITUTION, StatType.PERCEPTION, StatType.MANA]
        if self.selected_stat >= len(attributes):
            return
        
        stat = attributes[self.selected_stat]
        
        if amount > 0:  # Allocating points
            if char.attribute_points >= amount:
                char.stats.increase_base_stat(stat, amount)
                char.attribute_points -= amount
                char._update_equipment_bonuses()  # Update HP/mana
                self.add_to_log(f"Allocated {amount} point(s) to {stat.value}", (100, 255, 100))
            else:
                self.add_to_log("Not enough attribute points!", (255, 100, 100))
        else:  # Deallocating points
            current_base = char.stats.base_stats[stat]
            if current_base > 8:  # Minimum base stat is 8
                deallocate_amount = min(abs(amount), current_base - 8)
                char.stats.base_stats[stat] -= deallocate_amount
                char.attribute_points += deallocate_amount
                char._update_equipment_bonuses()  # Update HP/mana
                self.add_to_log(f"Deallocated {deallocate_amount} point(s) from {stat.value}", (100, 255, 100))
            else:
                self.add_to_log(f"Cannot reduce {stat.value} below 8!", (255, 100, 100))
    
    def _handle_log_popup_input(self, key):
        """Handle input for log popup."""
        # Close popup
        if key == pygame.K_l:
            self.log_popup_open = False
            self.add_to_log("Log popup closed", (100, 255, 100))
            return
        
        # Scroll up
        if key == pygame.K_UP:
            if self.log_popup_scroll > 0:
                self.log_popup_scroll -= 1
        # Scroll down
        elif key == pygame.K_DOWN:
            total_messages = len(self.log_messages)
            lines_per_page = 340 // 15  # Approximate lines that fit
            max_scroll = max(0, total_messages - lines_per_page)
            if self.log_popup_scroll < max_scroll:
                self.log_popup_scroll += 1
    
    def _toggle_auto_explore(self):
        """Toggle auto-explore mode."""
        if not self.player:
            return
        
        # Check if enemies are visible
        if self._are_enemies_visible():
            self.add_to_log("Cannot auto-explore: enemies nearby!", (255, 100, 100))
            return
        
        if self.auto_explore_active:
            self.auto_explore_active = False
            self.auto_explore_path = []
            self.auto_explore_target = None
            self.auto_explore_failed_attempts = 0
            self.add_to_log("Auto-explore disabled", (255, 255, 255))
        else:
            self.auto_explore_active = True
            self.auto_explore_failed_attempts = 0
            self._find_next_exploration_target()
            if self.auto_explore_target:
                self.add_to_log("Auto-explore enabled", (100, 150, 255))
            else:
                self.add_to_log("Auto-explore complete: all areas explored!", (100, 255, 100))
                self.auto_explore_active = False
    
    def _toggle_auto_explore_attack(self):
        """Toggle auto-explore mode with attack capability."""
        if not self.player:
            return
        
        # Check if enemies are visible
        if self._are_enemies_visible():
            # In attack mode, check if we can attack adjacent enemies
            closest_enemy = self._get_closest_enemy()
            if closest_enemy:
                # Only attack if adjacent (no ranged attacks)
                distance = abs(closest_enemy.x - self.player.x) + abs(closest_enemy.y - self.player.y)
                if distance == 1:
                    self.add_to_log(f"Attacking adjacent enemy: {closest_enemy.enemy_type.value}!", (255, 100, 100))
                    self._attack_enemy(closest_enemy)
                    return
                else:
                    # Enemy not adjacent, enable attack mode to move towards enemies
                    self.add_to_log(f"Enemy detected: {closest_enemy.enemy_type.value} - moving to attack!", (255, 100, 100))
                    # Enable attack mode to move towards the enemy
                    self.auto_explore_attack_mode = True
                    self.auto_explore_active = True
                    return
            else:
                self.add_to_log("No enemies to attack!", (255, 255, 100))
                return
        
        if self.auto_explore_active and self.auto_explore_attack_mode:
            # Disable attack mode
            self.auto_explore_attack_mode = False
            self.auto_explore_active = False
            self.auto_explore_path = []
            self.auto_explore_target = None
            self.add_to_log("Auto-explore attack mode disabled", (255, 255, 255))
        else:
            # Enable attack mode
            self.auto_explore_attack_mode = True
            self.auto_explore_active = True
            self._find_next_exploration_target()
            if self.auto_explore_target:
                self.add_to_log("Auto-explore attack mode enabled", (255, 100, 100))
            else:
                self.add_to_log("Auto-explore complete: all areas explored!", (100, 255, 100))
                self.auto_explore_active = False
                self.auto_explore_attack_mode = False
    
    def _get_closest_enemy(self):
        """Get the closest visible enemy to the player."""
        if not self.player or self.current_area != GameArea.DUNGEON:
            return None
        
        closest_enemy = None
        closest_distance = float('inf')
        
        for enemy in self.enemy_manager.enemies:
            if enemy.is_alive and (enemy.x, enemy.y) in self.visible_tiles:
                distance = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = enemy
        
        return closest_enemy
    
    def _move_towards_enemy(self, enemy):
        """Move towards a specific enemy."""
        if not self.player or not enemy:
            return
        
        # Calculate direction to enemy
        dx = 0
        dy = 0
        
        if enemy.x > self.player.x:
            dx = 1
        elif enemy.x < self.player.x:
            dx = -1
        
        if enemy.y > self.player.y:
            dy = 1
        elif enemy.y < self.player.y:
            dy = -1
        
        # Try to move towards enemy
        current_time = pygame.time.get_ticks() / 1000.0
        self._try_move_player(dx, dy, current_time)
    
    def _are_enemies_visible(self):
        """Check if any enemies are visible to the player."""
        if not self.player:
            return False
        
        player_x, player_y = self.player.x, self.player.y
        
        # Check all enemies
        for enemy in self.enemy_manager.enemies:
            if enemy.is_alive:
                # Check if enemy is in visible tiles
                if (enemy.x, enemy.y) in self.visible_tiles:
                    return True
        
        return False
    
    def _find_next_exploration_target(self):
        """Smart A* exploration strategy for large levels."""
        if not self.player:
            return
        
        player_x, player_y = self.player.x, self.player.y
        
        # Get the current area
        if self.current_area == GameArea.TOWN:
            width, height = self.town.width, self.town.height
            get_cell = self.town.get_cell
        else:
            width, height = self.dungeon.width, self.dungeon.height
            get_cell = self.dungeon.get_cell
        
        # Count total unexplored tiles
        total_unexplored = 0
        for y in range(height):
            for x in range(width):
                if (x, y) not in self.explored_tiles:
                    total_unexplored += 1
        
        print(f"DEBUG: Total unexplored tiles: {total_unexplored}")
        
        # If all tiles explored, we're done
        if total_unexplored == 0:
            self.auto_explore_target = None
            return
        
        # Strategy 1: Try to explore nearby tiles first (within walking distance)
        nearby_target = self._find_nearby_exploration_target(player_x, player_y, width, height, get_cell)
        if nearby_target:
            print(f"DEBUG: Found nearby target: {nearby_target}")
            self.auto_explore_target = nearby_target
            return
        
        # Strategy 2: Use A* to find the closest reachable unexplored area
        print("DEBUG: No nearby targets, using A* to find closest reachable unexplored area")
        self.auto_explore_target = self._find_closest_reachable_unexplored_area(player_x, player_y, width, height, get_cell)
    
    def _find_nearby_exploration_target(self, player_x, player_y, width, height, get_cell):
        """Find unexplored tiles within walking distance (radius 3)."""
        for radius in range(1, 4):  # Check radius 1-3
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    
                    check_x, check_y = player_x + dx, player_y + dy
                    
                    # Check bounds
                    if 0 <= check_x < width and 0 <= check_y < height:
                        if (check_x, check_y) not in self.explored_tiles:
                            cell = get_cell(check_x, check_y)
                            
                            # For any unexplored tile, find a walkable tile we can reach to see it
                            if cell in [CellType.FLOOR, CellType.DOOR, CellType.TOWN_FLOOR, CellType.TOWN_DOOR]:
                                # Direct walkable tile - path to it
                                test_path = self._find_path_unified((player_x, player_y), (check_x, check_y), allow_unexplored=True, depth=0)
                                if test_path:
                                    return (check_x, check_y)
                            else:
                                # Wall or other tile - find adjacent walkable tile to see it from
                                has_adjacent_walkable = False
                                for adj_dx, adj_dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                    adj_x, adj_y = check_x + adj_dx, check_y + adj_dy
                                    if (0 <= adj_x < width and 0 <= adj_y < height):
                                        adj_cell = get_cell(adj_x, adj_y)
                                        if adj_cell in [CellType.FLOOR, CellType.DOOR, CellType.TOWN_FLOOR, CellType.TOWN_DOOR]:
                                            # Test if we can reach this adjacent walkable tile
                                            test_path = self._find_path_unified((player_x, player_y), (adj_x, adj_y), allow_unexplored=True, depth=0)
                                            if test_path:
                                                return (check_x, check_y)  # Target the unexplored tile, path to adjacent walkable
                                            has_adjacent_walkable = True
                                
                                # Skip isolated walls that have no adjacent walkable tiles
                                if not has_adjacent_walkable:
                                    continue
        return None
    
    def _find_closest_reachable_unexplored_area(self, player_x, player_y, width, height, get_cell):
        """Find closest reachable unexplored area using straight-line distance + A*."""
        # Find all unexplored tiles with straight-line distances
        unexplored_candidates = []
        for y in range(height):
            for x in range(width):
                if (x, y) not in self.explored_tiles:
                    cell = get_cell(x, y)
                    
                    # Skip isolated walls that have no adjacent walkable tiles
                    if cell in [CellType.WALL, CellType.TOWN_WALL]:
                        has_adjacent_walkable = False
                        for adj_dx, adj_dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            adj_x, adj_y = x + adj_dx, y + adj_dy
                            if (0 <= adj_x < width and 0 <= adj_y < height):
                                adj_cell = get_cell(adj_x, adj_y)
                                if adj_cell in [CellType.FLOOR, CellType.DOOR, CellType.TOWN_FLOOR, CellType.TOWN_DOOR]:
                                    has_adjacent_walkable = True
                                    break
                        if not has_adjacent_walkable:
                            continue  # Skip this isolated wall
                    
                    # Calculate straight-line distance
                    straight_distance = math.sqrt((x - player_x)**2 + (y - player_y)**2)
                    unexplored_candidates.append(((x, y), straight_distance))
        
        if not unexplored_candidates:
            return None
        
        # Sort by straight-line distance (fastest first)
        unexplored_candidates.sort(key=lambda x: x[1])
        
        # Test A* pathfinding for the closest candidates only
        max_candidates_to_test = min(10, len(unexplored_candidates))  # Test up to 10 closest
        
        closest_path_distance = float('inf')
        closest_tile = None
        
        for i, (target, straight_distance) in enumerate(unexplored_candidates[:max_candidates_to_test]):
            target_x, target_y = target
            cell = get_cell(target_x, target_y)
            print(f"DEBUG: Testing candidate {i+1}: {target} (cell: {cell}, straight distance: {straight_distance:.1f})")
            
            # For any unexplored tile, find a walkable position we can reach to see it
            if cell in [CellType.FLOOR, CellType.DOOR, CellType.TOWN_FLOOR, CellType.TOWN_DOOR]:
                # Direct walkable tile - path to it
                path = self._find_path_unified((player_x, player_y), target, allow_unexplored=True, depth=0)
                if path:
                    path_distance = len(path)
                    print(f"DEBUG: Found direct path to {target} with {path_distance} steps")
                    if path_distance < closest_path_distance:
                        closest_path_distance = path_distance
                        closest_tile = target
                else:
                    print(f"DEBUG: No direct path to walkable {target}")
            else:
                # Wall or other tile - find adjacent walkable tile to see it from
                print(f"DEBUG: {target} is {cell}, looking for adjacent walkable tile")
                found_adjacent = False
                for adj_dx, adj_dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    adj_x, adj_y = target_x + adj_dx, target_y + adj_dy
                    if (0 <= adj_x < width and 0 <= adj_y < height):
                        adj_cell = get_cell(adj_x, adj_y)
                        if adj_cell in [CellType.FLOOR, CellType.DOOR, CellType.TOWN_FLOOR, CellType.TOWN_DOOR]:
                            print(f"DEBUG: Found adjacent walkable tile at ({adj_x}, {adj_y})")
                            # Test if we can reach this adjacent walkable tile
                            path = self._find_path_unified((player_x, player_y), (adj_x, adj_y), allow_unexplored=True, depth=0)
                            if path:
                                path_distance = len(path)
                                print(f"DEBUG: Found path to adjacent tile ({adj_x}, {adj_y}) with {path_distance} steps")
                                if path_distance < closest_path_distance:
                                    closest_path_distance = path_distance
                                    closest_tile = target  # Target the unexplored tile, path to adjacent walkable
                                found_adjacent = True
                                break  # Found one adjacent tile, no need to check others
                            else:
                                print(f"DEBUG: No path to adjacent tile ({adj_x}, {adj_y})")
                if not found_adjacent:
                    print(f"DEBUG: No adjacent walkable tile found for {target}")
        
        print(f"DEBUG: Closest reachable unexplored area: {closest_tile} (path distance: {closest_path_distance})")
        return closest_tile
    
    def _calculate_auto_explore_path(self):
        """Calculate path to the auto-explore target using unified pathfinding."""
        if not self.auto_explore_target or not self.player:
            self.auto_explore_path = []
            if not self.auto_explore_target:
                self.add_to_log("Auto-explore complete: all areas explored!", (100, 255, 100))
                self.auto_explore_active = False
            return
        
        start = (self.player.x, self.player.y)
        target = self.auto_explore_target
        
        # Check if target is walkable - if not, find adjacent walkable tile to path to
        target_x, target_y = target
        if self.current_area == GameArea.TOWN:
            cell = self.town.get_cell(target_x, target_y)
        else:
            cell = self.dungeon.get_cell(target_x, target_y)
        
        print(f"DEBUG: Calculating path from {start} to target {target} (cell: {cell})")
        
        if cell in [CellType.FLOOR, CellType.DOOR, CellType.TOWN_FLOOR, CellType.TOWN_DOOR]:
            # Target is walkable, path directly to it
            print(f"DEBUG: Target is walkable, pathing directly to {target}")
            self.auto_explore_path = self._find_path_unified(start, target, allow_unexplored=True, depth=0)
        else:
            # Target is not walkable (wall, etc.) - find adjacent walkable tile to see it from
            print(f"DEBUG: Target is not walkable, looking for adjacent walkable tile")
            for adj_dx, adj_dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                adj_x, adj_y = target_x + adj_dx, target_y + adj_dy
                if self.current_area == GameArea.TOWN:
                    if (0 <= adj_x < self.town.width and 0 <= adj_y < self.town.height):
                        adj_cell = self.town.get_cell(adj_x, adj_y)
                        if adj_cell in [CellType.TOWN_FLOOR, CellType.TOWN_DOOR]:
                            # Path to the adjacent walkable tile
                            print(f"DEBUG: Found adjacent walkable tile at ({adj_x}, {adj_y}), pathing to it")
                            self.auto_explore_path = self._find_path_unified(start, (adj_x, adj_y), allow_unexplored=True, depth=0)
                            break
                else:
                    if (0 <= adj_x < self.dungeon.width and 0 <= adj_y < self.dungeon.height):
                        adj_cell = self.dungeon.get_cell(adj_x, adj_y)
                        if adj_cell in [CellType.FLOOR, CellType.DOOR]:
                            # Path to the adjacent walkable tile
                            print(f"DEBUG: Found adjacent walkable tile at ({adj_x}, {adj_y}), pathing to it")
                            self.auto_explore_path = self._find_path_unified(start, (adj_x, adj_y), allow_unexplored=True, depth=0)
                            break
        
        print(f"DEBUG: Calculated path: {len(self.auto_explore_path) if self.auto_explore_path else 0} steps")
        
        if not self.auto_explore_path:
            self.add_to_log("Auto-explore stopped: cannot reach target", (255, 255, 100))
            self.auto_explore_active = False
    
    def _find_path(self, start, target):
        """Find path using unified pathfinding."""
        return self._find_path_unified(start, target, allow_unexplored=False, depth=0)
    
    
    
    
    def _update_auto_explore(self):
        """Update auto-explore movement."""
        if not self.auto_explore_active or not self.player:
            return
        
        current_time = pygame.time.get_ticks() / 1000.0
        
        # Check if enemies are visible (only for normal auto-explore, not attack mode)
        if self._are_enemies_visible() and not self.auto_explore_attack_mode:
            # Normal auto-explore stops when enemies are visible
            self.add_to_log("Auto-explore stopped: enemy detected!", (255, 100, 100))
            self.auto_explore_active = False
            self.auto_explore_path = []
            self.auto_explore_target = None
            return
        
        # In attack mode, check for enemies to attack
        if self.auto_explore_attack_mode and self._are_enemies_visible():
            closest_enemy = self._get_closest_enemy()
            if closest_enemy:
                # Check if we can attack (adjacent only - no ranged attacks)
                distance = abs(closest_enemy.x - self.player.x) + abs(closest_enemy.y - self.player.y)
                if distance == 1:
                    # Attack the enemy
                    self.add_to_log(f"Auto-attacking {closest_enemy.enemy_type.value}!", (255, 100, 100))
                    self._attack_enemy(closest_enemy)
                    return
                else:
                    # Move towards the enemy
                    self._move_towards_enemy(closest_enemy)
                    return
        
        # Check if we have a path
        if not self.auto_explore_path:
            self._find_next_exploration_target()
            if not self.auto_explore_target:
                self.add_to_log("Auto-explore complete: all areas explored!", (100, 255, 100))
                self.auto_explore_active = False
                self.auto_explore_failed_attempts = 0
                return
            
            # Generate path to target using proper path calculation
            self._calculate_auto_explore_path()
            
            if not self.auto_explore_path:
                # No path found, skip this target
                self.auto_explore_failed_attempts += 1
                self.auto_explore_target = None
                
                # Safety check: if we've failed too many times, stop auto-explore
                if self.auto_explore_failed_attempts >= 10:
                    self.add_to_log("Auto-explore stopped: too many failed attempts", (255, 100, 100))
                    self.auto_explore_active = False
                    self.auto_explore_failed_attempts = 0
                return
        
        # Move to next position in path
        if self.player.can_move(current_time):
            next_pos = self.auto_explore_path[0]
            dx = next_pos[0] - self.player.x
            dy = next_pos[1] - self.player.y
            
            # Move player
            self.player.move_to(next_pos[0], next_pos[1], current_time)
            self.update_camera()
            
            # Reset failed attempts counter on successful movement
            self.auto_explore_failed_attempts = 0
            
            # Remove the position we just moved to
            self.auto_explore_path.pop(0)
            
            # Check for special interactions
            self._check_special_tiles(next_pos[0], next_pos[1])
            
            # Update fog of war
            self._update_fog_of_war()
    
    def _update_click_navigation(self):
        """Update click navigation movement."""
        if not self.click_navigation_active or not self.click_path or not self.player:
            return
        
        # Check if player can move
        current_time = pygame.time.get_ticks() / 1000.0
        if not self.player.can_move(current_time):
            return
        
        # Get next position in path
        next_pos = self.click_path[0]
        
        # Check if there's an enemy at the destination
        enemy_at_destination = self._get_enemy_at_position(next_pos[0], next_pos[1])
        if enemy_at_destination:
            # Attack the enemy instead of moving
            self._attack_enemy(enemy_at_destination)
            self.click_navigation_active = False
            self.click_path = []
            self.click_target = None
            return
        
        # Move to next position
        dx = next_pos[0] - self.player.x
        dy = next_pos[1] - self.player.y
        
        # Check if movement is valid
        can_move = False
        if self.current_area == GameArea.TOWN:
            can_move = self.town.can_move_to(next_pos[0], next_pos[1])
        elif self.current_area == GameArea.DUNGEON:
            can_move = self.dungeon.can_move_to(next_pos[0], next_pos[1])
        
        if can_move:
            # Check if we're already at the next position (shouldn't happen, but safety check)
            if next_pos[0] == self.player.x and next_pos[1] == self.player.y:
                print(f"DEBUG: Already at next position ({next_pos[0]}, {next_pos[1]}), removing from path")
                self.click_path.pop(0)
                return
            
            self.player.move_to(next_pos[0], next_pos[1], current_time)
            self.update_camera()
            
            # Remove the completed step from path
            self.click_path.pop(0)
            
            # Check if we've reached the target
            if not self.click_path:
                self.click_navigation_active = False
                self.click_target = None
                self.add_to_log("Reached destination!", (100, 255, 100))
            else:
                # Check for special interactions
                self._check_special_tiles(next_pos[0], next_pos[1])
        else:
            # Path is blocked, try to recalculate path
            print(f"DEBUG: Movement blocked at ({next_pos[0]}, {next_pos[1]}), attempting to recalculate path")
            
            # Try to recalculate path from current position
            start = (self.player.x, self.player.y)
            target = self.click_target
            
            if target:
                if self.current_area == GameArea.TOWN:
                    new_path = self._find_path_town(start, target)
                else:
                    new_path = self._find_path(start, target)
                
                if new_path:
                    self.click_path = new_path
                    self.add_to_log("Path recalculated", (255, 255, 100))
                else:
                    # No new path found, cancel navigation
                    self.click_navigation_active = False
                    self.click_path = []
                    self.click_target = None
                    self.add_to_log("Path blocked and no alternative found!", (255, 100, 100))
            else:
                # No target, cancel navigation
                self.click_navigation_active = False
                self.click_path = []
                self.add_to_log("Path blocked!", (255, 100, 100))
    
    def _render_click_path(self):
        """Render the click navigation path."""
        if not self.click_navigation_active or not self.click_path:
            return
        
        # Calculate available gameplay area (screen height - 60 pixels for bottom frame)
        gameplay_height = self.screen.get_height() - 60
        
        # Render path as a series of connected dots
        for i, (x, y) in enumerate(self.click_path):
            screen_x = (x - self.camera_x) * self.tile_size
            screen_y = (y - self.camera_y) * self.tile_height
            
            # Check if the tile is on screen
            if (screen_x >= -self.tile_size and screen_x < self.screen.get_width() + self.tile_size and
                screen_y >= -self.tile_height and screen_y < gameplay_height + self.tile_height):
                
                # Calculate center of tile
                center_x = screen_x + self.tile_size // 2
                center_y = screen_y + self.tile_height // 2
                
                # Draw path indicator
                if i == 0:
                    # Start of path - green circle
                    pygame.draw.circle(self.screen, (0, 255, 0), (center_x, center_y), 4)
                elif i == len(self.click_path) - 1:
                    # End of path - red circle
                    pygame.draw.circle(self.screen, (255, 0, 0), (center_x, center_y), 4)
                else:
                    # Middle of path - blue circle
                    pygame.draw.circle(self.screen, (0, 100, 255), (center_x, center_y), 3)
                
        # Draw line to next point
        if i < len(self.click_path) - 1:
            next_x, next_y = self.click_path[i + 1]
            next_screen_x = (next_x - self.camera_x) * self.tile_size
            next_screen_y = (next_y - self.camera_y) * self.tile_height
            next_center_x = next_screen_x + self.tile_size // 2
            next_center_y = next_screen_y + self.tile_height // 2
            
            # Only draw line if both points are on screen
            if (next_screen_x >= -self.tile_size and next_screen_x < self.screen.get_width() + self.tile_size and
                next_screen_y >= -self.tile_height and next_screen_y < gameplay_height + self.tile_height):
                pygame.draw.line(self.screen, (0, 150, 255), (center_x, center_y), (next_center_x, next_center_y), 2)
    
    def _render_pause_overlay(self):
        """Render pause overlay."""
        # Create semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause text
        pause_text = self.font.render("PAUSED", True, (255, 255, 100))
        pause_rect = pause_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 20))
        self.screen.blit(pause_text, pause_rect)
        
        # Draw instruction text
        instruction_text = self.small_font.render("Press SPACE to resume", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 20))
        self.screen.blit(instruction_text, instruction_rect)
    
    def _render_skill_popup(self):
        """Render skill point allocation popup."""
        if not self.player or not self.player.character:
            return
        
        from system.character_system import StatType
        
        # Create semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Popup dimensions
        popup_width = 400
        popup_height = 300
        popup_x = (self.screen.get_width() - popup_width) // 2
        popup_y = (self.screen.get_height() - popup_height) // 2
        
        # Draw popup background
        pygame.draw.rect(self.screen, (50, 50, 50), (popup_x, popup_y, popup_width, popup_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (popup_x, popup_y, popup_width, popup_height), 2)
        
        # Title
        title_text = self.font.render("Skill Point Allocation", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(popup_x + popup_width // 2, popup_y + 30))
        self.screen.blit(title_text, title_rect)
        
        # Available points
        char = self.player.character
        attribute_points = getattr(char, 'attribute_points', 0)
        skill_points = getattr(char, 'skill_points', 0)
        
        points_text = f"Attribute Points: {attribute_points} | Skill Points: {skill_points}"
        points_surface = self.small_font.render(points_text, True, (200, 200, 200))
        points_rect = points_surface.get_rect(center=(popup_x + popup_width // 2, popup_y + 60))
        self.screen.blit(points_surface, points_rect)
        
        # Attribute allocation section
        if attribute_points > 0:
            attr_title = self.small_font.render("Attributes (1-5 keys to allocate):", True, (255, 255, 100))
            self.screen.blit(attr_title, (popup_x + 20, popup_y + 90))
            
            # List of attributes
            attributes = [
                (StatType.STRENGTH, "1"),
                (StatType.DEXTERITY, "2"), 
                (StatType.CONSTITUTION, "3"),
                (StatType.PERCEPTION, "4"),
                (StatType.MANA, "5")
            ]
            
            y_offset = 120
            for i, (stat, key) in enumerate(attributes):
                current_value = char.stats.get_total_stat(stat)
                stat_text = f"{key}. {stat.value}: {current_value}"
                color = (255, 255, 255) if i == self.selected_stat else (200, 200, 200)
                stat_surface = self.small_font.render(stat_text, True, color)
                self.screen.blit(stat_surface, (popup_x + 30, popup_y + y_offset))
                y_offset += 25
        
        # Instructions
        instruction_text = "Press S to close | 1-5 to select attribute | + to allocate | - to deallocate"
        instruction_surface = self.small_font.render(instruction_text, True, (150, 150, 150))
        instruction_rect = instruction_surface.get_rect(center=(popup_x + popup_width // 2, popup_y + popup_height - 30))
        self.screen.blit(instruction_surface, instruction_rect)
    
    def _render_log_popup(self):
        """Render the full log popup window."""
        if not self.log_messages:
            return
        
        # Create semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Popup dimensions
        popup_width = 600
        popup_height = 400
        popup_x = (self.screen.get_width() - popup_width) // 2
        popup_y = (self.screen.get_height() - popup_height) // 2
        
        # Draw popup background
        pygame.draw.rect(self.screen, (50, 50, 50), (popup_x, popup_y, popup_width, popup_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (popup_x, popup_y, popup_width, popup_height), 2)
        
        # Title
        title_text = self.font.render("Game Log", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(popup_x + popup_width // 2, popup_y + 30))
        self.screen.blit(title_text, title_rect)
        
        # Log content area
        content_x = popup_x + 10
        content_y = popup_y + 60
        content_width = popup_width - 20
        content_height = popup_height - 100
        
        # Draw content background
        pygame.draw.rect(self.screen, (30, 30, 30), (content_x, content_y, content_width, content_height))
        
        # Calculate which messages to show based on scroll
        total_messages = len(self.log_messages)
        lines_per_page = content_height // 15  # Approximate lines that fit
        max_scroll = max(0, total_messages - lines_per_page)
        
        # Clamp scroll to valid range
        self.log_popup_scroll = max(0, min(self.log_popup_scroll, max_scroll))
        
        start_index = self.log_popup_scroll
        end_index = min(total_messages, start_index + lines_per_page)
        
        # Render log messages
        y_offset = content_y + 5
        for i in range(start_index, end_index):
            if i < len(self.log_messages):
                message, color = self.log_messages[i]
                # Truncate long messages
                max_chars = (content_width - 10) // 8
                if len(message) > max_chars:
                    message = message[:max_chars-3] + "..."
                
                text = self.small_font.render(message, True, color)
                self.screen.blit(text, (content_x + 5, y_offset))
                y_offset += 15
        
        # Scroll indicator
        if total_messages > lines_per_page:
            scroll_text = f"Log: {self.log_popup_scroll + 1}-{min(total_messages, self.log_popup_scroll + lines_per_page)}/{total_messages}"
            scroll_surface = self.small_font.render(scroll_text, True, (150, 150, 150))
            self.screen.blit(scroll_surface, (content_x, content_y + content_height - 20))
        
        # Instructions
        instruction_text = "Press L to close | UP/DOWN arrows to scroll | Mouse wheel to scroll"
        instruction_surface = self.small_font.render(instruction_text, True, (150, 150, 150))
        instruction_rect = instruction_surface.get_rect(center=(popup_x + popup_width // 2, popup_y + popup_height - 20))
        self.screen.blit(instruction_surface, instruction_rect)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Treasure Goblin')
    parser.add_argument('-g', '--god-mode', action='store_true', 
                       help='Enable god mode: invincible + 10000 gold')
    
    args = parser.parse_args()
    
    game = Game(god_mode=args.god_mode)
    game.run()

if __name__ == "__main__":
    main()
