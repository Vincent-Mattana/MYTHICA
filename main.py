#!/usr/bin/env python3
"""
Mythica - A Grid-Based Dungeon Crawler
A procedurally generated dungeon exploration game with minimap.
"""

import pygame
import sys
import time
from typing import Tuple, List, Set
from enum import Enum
import random
import math
from logic import (
    Character, CharacterStats, Equipment, StatType, EquipmentSlot,
    PerkSystem, CharacterPerks,
    Enemy, EnemyManager, EnemyType,
    TurnManager, ActionCosts, ActionType,
    GameStateManager, CharacterClassData, CharacterClass,
    ConfigManager,
    InteractiveCharacterScreen, Inventory, InventoryAction,
    sprite_manager, SpriteType,
    SpriteFont
)
from logic.config_manager import config
from logic.game_states import GameState
from logic.enemy_system import HealthBar

# Initialize pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
SIDEBAR_WIDTH = 250  # Width of the right sidebar
GAME_AREA_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH  # Game area takes remaining width
GRID_SIZE = 24  # Match Oryx sprite size
DUNGEON_WIDTH = 50
DUNGEON_HEIGHT = 50
VIEWPORT_WIDTH = GAME_AREA_WIDTH // GRID_SIZE  # Viewport fits in game area
VIEWPORT_HEIGHT = WINDOW_HEIGHT // GRID_SIZE   # Full height for game area
MINIMAP_SIZE = 200
FPS = 60

# Colours (UK spelling as requested)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
DARK_GREY = (64, 64, 64)
BROWN = (139, 69, 19)
BLUE = (0, 100, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (255, 255, 0)

class CellType(Enum):
    WALL = 0
    FLOOR = 1
    DOOR = 2
    STAIRCASE = 3
    CHEST = 4
    HP_PICKUP = 5
    WATER = 6
    ITEM = 7  # For items dropped on ground

class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)
    NORTHWEST = (-1, -1)
    NORTHEAST = (1, -1)
    SOUTHWEST = (-1, 1)
    SOUTHEAST = (1, 1)

class LineOfSight:
    @staticmethod
    def get_visible_tiles(player_x: int, player_y: int, dungeon: 'Dungeon', 
                         sight_range: int = 8) -> Set[Tuple[int, int]]:
        """Calculate which tiles are visible from the player's position using raycasting."""
        visible = set()
        visible.add((player_x, player_y))  # Player can always see their own tile
        
        # Cast rays in a circle around the player
        num_rays = 360  # One ray per degree for smooth visibility
        
        for i in range(num_rays):
            angle = (i * 2 * math.pi) / num_rays
            dx = math.cos(angle)
            dy = math.sin(angle)
            
            # Cast ray from player position
            for step in range(1, sight_range + 1):
                ray_x = player_x + dx * step
                ray_y = player_y + dy * step
                
                # Round to get grid coordinates
                grid_x = int(round(ray_x))
                grid_y = int(round(ray_y))
                
                # Check bounds
                if (grid_x < 0 or grid_x >= dungeon.width or 
                    grid_y < 0 or grid_y >= dungeon.height):
                    break
                
                # Add tile to visible set
                visible.add((grid_x, grid_y))
                
                # Stop if we hit a wall
                if dungeon.get_cell(grid_x, grid_y) == CellType.WALL:
                    break
        
        return visible
    
    @staticmethod
    def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
        """Generate points along a line using Bresenham's algorithm."""
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        
        x, y = x0, y0
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        
        error = dx - dy
        
        while True:
            points.append((x, y))
            
            if x == x1 and y == y1:
                break
                
            error2 = 2 * error
            
            if error2 > -dy:
                error -= dy
                x += x_inc
                
            if error2 < dx:
                error += dx
                y += y_inc
        
        return points

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Mythica - Dungeon Crawler")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state management
        self.state_manager = GameStateManager(self.screen)
        
        # Game components (initialized when starting a game)
        self.dungeon = None
        self.player = None
        self.camera = None
        self.minimap = None
        self.enemy_manager = None
        
        # Load character portraits
        self.class_portraits = {}
        portrait_sheet = pygame.image.load(str(sprite_manager.assets_path / "oryx_roguelike_2.0" / "oryx_roguelike_2.0" / "Interface_Portraits.png")).convert_alpha()
        # Portrait positions in the sheet (x, y)
        portrait_positions = {
            CharacterClass.WARRIOR: (0, 0),    # First portrait - warrior
            CharacterClass.ROGUE: (48, 0),     # Second portrait - rogue/thief
            CharacterClass.MAGE: (96, 0),      # Third portrait - mage/wizard
            CharacterClass.RANGER: (144, 0),   # Fourth portrait - ranger/archer
            CharacterClass.CLERIC: (192, 0)    # Fifth portrait - cleric/priest
        }
        for char_class, pos in portrait_positions.items():
            portrait = pygame.Surface((48, 48), pygame.SRCALPHA)
            portrait.blit(portrait_sheet, (0, 0), (pos[0], pos[1], 48, 48))
            self.class_portraits[char_class] = portrait
            
        # Load and cache the slash sprite
        self.slash_sprite = pygame.image.load(str(sprite_manager.assets_path / "Classic Roguelike" / "classic_roguelike_sliced" / "classic_roguelike_134.png")).convert_alpha()
        
        # Game state
        self.explored = set()  # All tiles the player has ever seen
        self.visible = set()   # Currently visible tiles
        self.los = LineOfSight()
        self.game_start_time = time.time()
        
        # Turn-based system
        self.turn_manager = TurnManager()
        
        # UI state
        self.show_character_sheet = False
        self.player_is_dead = False
        
        # Interactive character screen/inventory
        self.interactive_character_screen = InteractiveCharacterScreen(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.show_interactive_inventory = False
        
        # Continuous movement state
        self.movement_timer = 0  # Timer to control movement speed when holding keys
        self.movement_delay = config.get_float_setting('Game', 'continuous_movement_delay', 0.15)  # Seconds between movements when holding key
        self.key_hold_start_time = {}  # Track when keys were first pressed
        self.continuous_hold_delay = config.get_float_setting('Game', 'continuous_hold_delay', 0.3)  # How long to hold before continuous movement starts
        self.last_manual_move_time = 0  # Track manual moves to prevent overlap
        
        # Auto-explore state
        self.auto_explore_active = False
        self.auto_explore_path = []  # Queue of positions to move to
        
        # Level navigation state
        self.level_history = {}  # Store dungeon states for each level
        self.current_level = 1
        
        # Treasure and pickup system
        self.chests = {}  # {(x, y): {'opened': bool, 'contents': [items]}}
        self.hp_pickups = set()  # {(x, y)} - positions of HP pickups
        
        # Game log for sidebar
        self.game_log = []
        self.max_log_entries = 8  # Number of log entries to show in sidebar
    
    def add_to_log(self, message: str, color: Tuple[int, int, int] = WHITE):
        """Add a message to the game log."""
        self.game_log.append((message, color))
        # Keep only the most recent entries
        if len(self.game_log) > self.max_log_entries:
            self.game_log.pop(0)
        
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # Special case for F5 - reload config
                if event.key == pygame.K_F5:
                    config.reload_config()
                    print("Configuration reloaded!")
                elif self.state_manager.current_state == GameState.PLAYING:
                    # Check if interactive inventory is open
                    if self.show_interactive_inventory:
                        if (config.is_key_pressed_for_action('quit_game', event.key) or 
                            config.is_key_pressed_for_action('inventory', event.key)):
                            self.show_interactive_inventory = False
                    else:
                        self.handle_player_input(event.key)
                else:
                    # Handle menu/game over input
                    continue_game, character = self.state_manager.handle_input(event)
                    if not continue_game:
                        self.running = False
                    elif character:
                        self.start_new_game(character)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse clicks for interactive inventory
                if (self.state_manager.current_state == GameState.PLAYING and 
                    self.show_interactive_inventory and self.player):
                    message = self.interactive_character_screen.handle_mouse_click(
                        event.pos, self.player.character, self.player.character.inventory)
                    if message:
                        self.add_to_log(message, WHITE)
            elif event.type == pygame.MOUSEMOTION:
                # Handle mouse hover for tooltips
                if (self.state_manager.current_state == GameState.PLAYING and 
                    self.show_interactive_inventory and self.player):
                    self.interactive_character_screen.handle_mouse_hover(
                        event.pos, self.player.character, self.player.character.inventory)
    
    def handle_player_input(self, key):
        # Check for special actions first
        if config.is_key_pressed_for_action('character_sheet', key):
            self.show_character_sheet = not self.show_character_sheet
            if self.show_character_sheet:
                self.show_interactive_inventory = False  # Close inventory if open
            return
        
        if config.is_key_pressed_for_action('inventory', key):
            self.show_interactive_inventory = not self.show_interactive_inventory
            if self.show_interactive_inventory:
                self.show_character_sheet = False  # Close old sheet if open
            return
        
        if config.is_key_pressed_for_action('quit_game', key):
            self.running = False
            return
        
        if config.is_key_pressed_for_action('wait_turn', key):
            # Wait/rest turn  
            if not self.player_is_dead and self.turn_manager.can_player_act():
                dexterity = self.player.character.stats.get_total_stat(StatType.DEXTERITY)
                self.turn_manager.schedule_player_action(ActionType.WAIT, dexterity=dexterity)
                print("Waiting...")
            return
        
        if config.is_key_pressed_for_action('auto_explore', key):
            # Toggle auto-explore
            if not self.player_is_dead:
                self.toggle_auto_explore()
            return
        
        if config.is_key_pressed_for_action('go_down_stairs', key):
            # Go down stairs
            print("']' key pressed - attempting to go down stairs")
            if not self.player_is_dead:
                self.handle_stair_navigation('down')
            return
        
        if config.is_key_pressed_for_action('go_up_stairs', key):
            # Go up stairs
            print("'[' key pressed - attempting to go up stairs")
            if not self.player_is_dead:
                self.handle_stair_navigation('up')
            return
        
        # Check for movement
        dx, dy = config.get_movement_direction(key)
        
        if dx != 0 or dy != 0:
            if self.player_is_dead or not self.turn_manager.can_player_act():
                return  # Player cannot act yet or is dead
            
            # Record this as a manual move to prevent continuous movement overlap
            import time
            self.last_manual_move_time = time.time()
            
            # Cancel auto-explore on manual movement
            if self.auto_explore_active:
                self.auto_explore_active = False
                self.auto_explore_path = []
                self.add_to_log("Auto-explore cancelled", WHITE)
                
            new_x = self.player.x + dx
            new_y = self.player.y + dy
            
            # Check if the target position is a valid floor tile
            if not self.dungeon.can_move_to(new_x, new_y):
                return  # Can't move into walls
            
            # Check for enemy at target position
            enemy_at_target = self.enemy_manager.get_enemy_at(new_x, new_y)
            if enemy_at_target and enemy_at_target.is_alive:
                # Combat! Schedule attack action
                dexterity = self.player.character.stats.get_total_stat(StatType.DEXTERITY)
                self.turn_manager.schedule_player_action(
                    ActionType.ATTACK, 
                    target_pos=(new_x, new_y),
                    target_id=f"enemy_{enemy_at_target.x}_{enemy_at_target.y}",
                    dexterity=dexterity
                )
            else:
                # Schedule movement action
                dexterity = self.player.character.stats.get_total_stat(StatType.DEXTERITY)
                self.turn_manager.schedule_player_action(
                    ActionType.MOVE, 
                    target_pos=(new_x, new_y),
                    dexterity=dexterity
                )
    
    def update(self):
        # Only update game logic when actually playing
        if self.state_manager.current_state == GameState.PLAYING and self.player:
            # Process continuous movement from held keys
            self.process_continuous_movement()
            
            # Process auto-explore if active
            self.process_auto_explore()
            
            # Process turn-based actions
            self.process_turn_actions()
            
            # Update camera to follow player
            self.camera.update(self.player.x, self.player.y)
            
            # Update minimap with new explored areas and visibility
            self.minimap.update_explored(self.explored)
            self.minimap.update_visible(self.visible)
    
    def update_visibility(self):
        """Update what tiles are currently visible and add to explored set."""
        sight_range = self.player.get_sight_range()
        self.visible = self.los.get_visible_tiles(
            self.player.x, self.player.y, self.dungeon, sight_range
        )
        # Add all visible tiles to the explored set
        self.explored.update(self.visible)
    
    def process_continuous_movement(self):
        """Process movement when direction keys are held down for a sustained period."""
        # Skip if player is dead, inventory is open, or can't act
        if (self.player_is_dead or 
            self.show_interactive_inventory or 
            not self.turn_manager.can_player_act()):
            return
        
        # Skip if auto-explore is active (let auto-explore handle movement)
        if self.auto_explore_active:
            return
        
        import time
        current_time = time.time()
        
        # Don't do continuous movement too soon after a manual move
        if current_time - self.last_manual_move_time < 0.1:
            return
        
        # Update movement timer
        if current_time - self.movement_timer < self.movement_delay:
            return  # Not enough time has passed for next movement
        
        # Check for held keys
        keys = pygame.key.get_pressed()
        
        # Track key hold times and find currently pressed movement keys
        currently_held_actions = []
        for direction_action in ['move_north', 'move_south', 'move_west', 'move_east',
                               'move_northwest', 'move_northeast', 'move_southwest', 'move_southeast']:
            if config.is_action_currently_pressed(direction_action, keys):
                # Key is currently pressed
                if direction_action not in self.key_hold_start_time:
                    # Key just started being pressed
                    self.key_hold_start_time[direction_action] = current_time
                elif current_time - self.key_hold_start_time[direction_action] >= self.continuous_hold_delay:
                    # Key has been held long enough for continuous movement
                    currently_held_actions.append(direction_action)
            else:
                # Key is not pressed, remove from tracking
                if direction_action in self.key_hold_start_time:
                    del self.key_hold_start_time[direction_action]
        
        # Only proceed if we have keys held long enough for continuous movement
        if not currently_held_actions:
            return
        
        # Calculate movement direction from held keys
        dx, dy = 0, 0
        for direction_action in currently_held_actions:
            movement_dx, movement_dy = config.get_movement_direction_for_action(direction_action)
            dx += movement_dx
            dy += movement_dy
        
        if dx != 0 or dy != 0:
            # Normalize diagonal movement (prevent faster diagonal movement)
            if abs(dx) > 1:
                dx = 1 if dx > 0 else -1
            if abs(dy) > 1:
                dy = 1 if dy > 0 else -1
            
            new_x = self.player.x + dx
            new_y = self.player.y + dy
            
            # Check if the target position is a valid floor tile
            if not self.dungeon.can_move_to(new_x, new_y):
                return  # Can't move into walls
            
            # Check for enemy at target position
            enemy_at_target = self.enemy_manager.get_enemy_at(new_x, new_y)
            if enemy_at_target and enemy_at_target.is_alive:
                # Combat! Schedule attack action
                dexterity = self.player.character.stats.get_total_stat(StatType.DEXTERITY)
                self.turn_manager.schedule_player_action(
                    ActionType.ATTACK, 
                    target_pos=(new_x, new_y),
                    target_id=f"enemy_{enemy_at_target.x}_{enemy_at_target.y}",
                    dexterity=dexterity
                )
            else:
                # Schedule movement action
                dexterity = self.player.character.stats.get_total_stat(StatType.DEXTERITY)
                self.turn_manager.schedule_player_action(
                    ActionType.MOVE, 
                    target_pos=(new_x, new_y),
                    dexterity=dexterity
                )
            
            # Update movement timer to prevent moving too fast
            self.movement_timer = current_time
    
    def toggle_auto_explore(self):
        """Toggle auto-explore mode on/off."""
        if self.auto_explore_active:
            self.auto_explore_active = False
            self.auto_explore_path = []
            self.add_to_log("Auto-explore disabled", WHITE)
            print("Auto-explore disabled")
        else:
            # Check if there are enemies visible
            if self.are_enemies_visible():
                self.add_to_log("Cannot auto-explore: enemies nearby!", RED)
                print("Cannot auto-explore: enemies visible")
                return
            
            self.auto_explore_active = True
            self.auto_explore_path = []
            self.add_to_log("Auto-explore enabled", BLUE)
            print("Auto-explore enabled")
    
    def are_enemies_visible(self) -> bool:
        """Check if any living enemies are currently visible."""
        for enemy in self.enemy_manager.get_living_enemies():
            if (enemy.x, enemy.y) in self.visible:
                return True
        return False
    
    def find_nearest_unexplored_area(self) -> Tuple[int, int]:
        """Find the nearest unexplored walkable tile using BFS."""
        from collections import deque
        
        start_x, start_y = self.player.x, self.player.y
        queue = deque([(start_x, start_y, 0)])  # (x, y, distance)
        visited = {(start_x, start_y)}
        
        # Only use orthogonal directions
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        # Track the closest unexplored tile we've found
        closest_target = None
        closest_dist = float('inf')
        
        while queue and (closest_target is None or queue[0][2] < closest_dist):
            x, y, dist = queue.popleft()
            
            # Check each direction from current position
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                
                # Skip if out of bounds
                if (new_x < 0 or new_x >= self.dungeon.width or 
                    new_y < 0 or new_y >= self.dungeon.height):
                    continue
                    
                # Skip if already visited
                if (new_x, new_y) in visited:
                    continue
                    
                # Skip if not walkable
                if not self.dungeon.can_move_to(new_x, new_y):
                    continue
                    
                visited.add((new_x, new_y))
                
                # If this tile is unexplored and closer than our current best
                if (new_x, new_y) not in self.explored and dist < closest_dist:
                    # Found a closer unexplored tile
                    closest_target = (new_x, new_y)
                    closest_dist = dist
                
                # Only add to queue if we haven't found a target or this path might lead to a closer one
                if dist + 1 < closest_dist:
                    queue.append((new_x, new_y, dist + 1))
        
        return closest_target
    
    def find_path_to_target(self, target_x: int, target_y: int) -> List[Tuple[int, int]]:
        """Find shortest path to target using optimized A* pathfinding."""
        import heapq
        
        start_x, start_y = self.player.x, self.player.y
        
        # If we're already at the target, no path needed
        if start_x == target_x and start_y == target_y:
            return []
        
        # Priority queue: (f_score, x, y)
        open_set = [(0, start_x, start_y)]
        # Keep track of where we came from and the g_scores
        came_from = {}
        g_scores = {(start_x, start_y): 0}
        
        # Only use orthogonal directions for faster pathfinding
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        def heuristic(x1: int, y1: int) -> int:
            """Manhattan distance heuristic."""
            return abs(x1 - target_x) + abs(y1 - target_y)
        
        while open_set:
            _, x, y = heapq.heappop(open_set)
            current = (x, y)
            
            # Found the target
            if x == target_x and y == target_y:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path
            
            # Explore neighbors
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                neighbor = (new_x, new_y)
                
                # Skip if out of bounds
                if (new_x < 0 or new_x >= self.dungeon.width or 
                    new_y < 0 or new_y >= self.dungeon.height):
                    continue
                    
                # Skip if not walkable
                if not self.dungeon.can_move_to(new_x, new_y):
                    continue
                
                # Skip if there's an enemy at this position
                if self.enemy_manager.get_enemy_at(new_x, new_y):
                    continue
                
                # Calculate tentative g_score
                tentative_g_score = g_scores[current] + 1
                
                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:
                    # This path is better than any previous one
                    came_from[neighbor] = current
                    g_scores[neighbor] = tentative_g_score
                    f_score = tentative_g_score + heuristic(new_x, new_y)
                    heapq.heappush(open_set, (f_score, new_x, new_y))
        
        # No path found
        return []
    
    def process_auto_explore(self):
        """Process auto-explore movement."""
        if not self.auto_explore_active or self.player_is_dead:
            return
        
        # Check if we can act
        if not self.turn_manager.can_player_act():
            return
        
        # Check for visible enemies and stop if found
        if self.are_enemies_visible():
            self.auto_explore_active = False
            self.auto_explore_path = []
            self.add_to_log("Auto-explore stopped: enemy detected!", RED)
            print("Auto-explore stopped: enemy detected")
            return
        
        # If we don't have a path, find one
        if not self.auto_explore_path:
            target = self.find_nearest_unexplored_area()
            if target is None:
                # No more unexplored areas
                self.auto_explore_active = False
                self.add_to_log("Auto-explore complete: all areas explored!", GREEN)
                print("Auto-explore complete: all areas explored")
                return
            
            # Find path to target
            path = self.find_path_to_target(target[0], target[1])
            if not path:
                # Can't reach target, stop auto-explore
                self.auto_explore_active = False
                self.add_to_log("Auto-explore stopped: cannot reach target", YELLOW)
                print("Auto-explore stopped: cannot reach target")
                return
            
            self.auto_explore_path = path
        
        # Execute next move in path
        if self.auto_explore_path:
            # Get next position from path
            next_pos = self.auto_explore_path[0]
            self.auto_explore_path = self.auto_explore_path[1:]  # Remove the step we're taking
            
            # Calculate movement direction
            dx = next_pos[0] - self.player.x
            dy = next_pos[1] - self.player.y
            
            # Schedule movement action
            dexterity = self.player.character.stats.get_total_stat(StatType.DEXTERITY)
            self.turn_manager.schedule_player_action(
                ActionType.MOVE,
                target_pos=next_pos,
                dexterity=dexterity
            )
    
    def is_on_staircase(self) -> bool:
        """Check if player is currently standing on a staircase."""
        player_pos = (self.player.x, self.player.y)
        cell_type = self.dungeon.get_cell(*player_pos)
        print(f"Checking if on staircase at {player_pos}, cell type: {cell_type}")
        return cell_type == CellType.STAIRCASE
    
    def handle_stair_navigation(self, direction: str):
        """Handle going up or down stairs."""
        print(f"Handling stair navigation: {direction}")
        if not self.is_on_staircase():
            if direction == 'down':
                self.add_to_log("No staircase here to go down", RED)
            else:
                self.add_to_log("No staircase here to go up", RED)
            print(f"Player tried to go {direction} stairs but not on staircase")
            return
        
        print(f"Player is on staircase, proceeding with {direction}")
        if direction == 'down':
            self.go_down_stairs()
        else:
            self.go_up_stairs()
    
    def go_down_stairs(self):
        """Descend to the next dungeon level."""
        # Cancel auto-explore if active
        if self.auto_explore_active:
            self.auto_explore_active = False
            self.auto_explore_path = []
        
        # Store current level state
        current_state = {
            'dungeon': self.dungeon,
            'explored': self.explored.copy(),
            'player_pos': (self.player.x, self.player.y),
            'enemies': self.enemy_manager.enemies.copy() if hasattr(self.enemy_manager, 'enemies') else [],
            'chests': self.chests.copy(),
            'hp_pickups': self.hp_pickups.copy(),
            'ground_items': self.ground_items.copy()
        }
        self.level_history[self.current_level] = current_state
        
        # Move to next level
        self.current_level += 1
        self.add_to_log(f"Descending to dungeon level {self.current_level}...", YELLOW)
        print(f"Player descends to level {self.current_level}")
        
        # Generate new dungeon level
        self.create_new_level()
    
    def go_up_stairs(self):
        """Ascend to the previous dungeon level."""
        if self.current_level <= 1:
            self.add_to_log("You are already on the top level", YELLOW)
            print("Player tried to go up from level 1")
            return
        
        # Cancel auto-explore if active
        if self.auto_explore_active:
            self.auto_explore_active = False
            self.auto_explore_path = []
        
        # Move to previous level
        previous_level = self.current_level - 1
        
        if previous_level in self.level_history:
            # Restore previous level
            self.restore_level(previous_level)
        else:
            # This shouldn't happen, but generate a new level as fallback
            self.current_level = previous_level
            self.create_new_level()
        
        self.add_to_log(f"Ascending to dungeon level {self.current_level}...", YELLOW)
        print(f"Player ascends to level {self.current_level}")
    
    def create_new_level(self):
        """Create a new dungeon level."""
        # Generate new dungeon
        self.dungeon = DungeonWithStairs(DUNGEON_WIDTH, DUNGEON_HEIGHT, self.current_level)
        
        # Place player at start position
        self.player.x, self.player.y = self.dungeon.start_pos
        
        # Reset exploration
        self.explored = set()
        self.visible = set()
        
        # Update camera and minimap
        self.camera = Camera()
        self.minimap = Minimap(self.dungeon)
        
        # Spawn new enemies
        self.enemy_manager = EnemyManager()
        self.enemy_manager.spawn_enemies_in_dungeon(
            self.dungeon,
            player_start_pos=self.player.get_position(),
            dungeon_level=self.current_level
        )
        
        # Set up enemy weapons in turn manager
        for enemy in self.enemy_manager.get_living_enemies():
            enemy_id = f"enemy_{enemy.x}_{enemy.y}"
            enemy_weapon = self.get_enemy_weapon_name(enemy.enemy_type)
            self.turn_manager.set_entity_weapon(enemy_id, enemy_weapon)
        
        # Update visibility
        self.update_visibility()
        
        # Schedule initial enemy actions
        self.schedule_enemy_actions()
        
        # Initialize treasure system
        self.initialize_level_treasures()
    
    def restore_level(self, level_num: int):
        """Restore a previously visited level."""
        if level_num not in self.level_history:
            return
        
        state = self.level_history[level_num]
        self.current_level = level_num
        
        # Restore dungeon
        self.dungeon = state['dungeon']
        
        # Find staircase position to place player
        staircase_pos = None
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                if self.dungeon.get_cell(x, y) == CellType.STAIRCASE:
                    staircase_pos = (x, y)
                    break
            if staircase_pos:
                break
        
        # Place player on staircase or start position
        if staircase_pos:
            self.player.x, self.player.y = staircase_pos
        else:
            self.player.x, self.player.y = self.dungeon.start_pos
        
        # Restore exploration state
        self.explored = state['explored'].copy()
        
        # Restore treasure state
        self.chests = state.get('chests', {}).copy()
        self.hp_pickups = state.get('hp_pickups', set()).copy()
        self.ground_items = state.get('ground_items', {}).copy()
        
        # Update camera and minimap
        self.camera = Camera()
        self.minimap = Minimap(self.dungeon)
        
        # Restore enemies (they may have moved or been killed)
        self.enemy_manager = EnemyManager()
        if 'enemies' in state and state['enemies']:
            self.enemy_manager.enemies = state['enemies'].copy()
            # Update enemy positions in the position tracking
            self.enemy_manager.enemy_positions.clear()
            for enemy in self.enemy_manager.enemies:
                if enemy.is_alive:
                    self.enemy_manager.enemy_positions.add((enemy.x, enemy.y))
        
        # Set up enemy weapons in turn manager
        for enemy in self.enemy_manager.get_living_enemies():
            enemy_id = f"enemy_{enemy.x}_{enemy.y}"
            enemy_weapon = self.get_enemy_weapon_name(enemy.enemy_type)
            self.turn_manager.set_entity_weapon(enemy_id, enemy_weapon)
        
        # Update visibility
        self.update_visibility()
        
        # Schedule enemy actions
        self.schedule_enemy_actions()
        
        # Initialize treasure system for restored level
        self.initialize_level_treasures()
    
    def initialize_level_treasures(self):
        """Initialize chests and HP pickups for the current level."""
        # Clear existing treasures
        self.chests = {}
        self.hp_pickups = set()
        
        # Find and initialize chests
        chest_count = 0
        pickup_count = 0
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                cell_type = self.dungeon.get_cell(x, y)
                if cell_type == CellType.CHEST:
                    self.chests[(x, y)] = {
                        'opened': False,
                        'contents': self.generate_chest_contents()
                    }
                    chest_count += 1
                elif cell_type == CellType.HP_PICKUP:
                    self.hp_pickups.add((x, y))
                    pickup_count += 1
        print(f"Initialized {chest_count} chests and {pickup_count} HP pickups")
    
    def generate_chest_contents(self) -> List:
        """Generate random contents for a chest based on character's LUCK."""
        from logic.character_system import ItemGenerator, ItemType, StatType
        
        contents = []
        
        # Get character's luck stat (from player's character)
        luck = self.player.character.stats.get_total_stat(StatType.LUCK) if self.player else 10  # Default to 10 if no player
        
        # Base number of items (1-3) influenced by luck
        # LUCK 10 (base): 60% 1 item, 30% 2 items, 10% 3 items
        # LUCK 20 (high): 30% 1 item, 50% 2 items, 20% 3 items
        # LUCK 30 (max): 10% 1 item, 60% 2 items, 30% 3 items
        luck_factor = (luck - 10) / 20  # 0.0 at LUCK 10, 1.0 at LUCK 30
        luck_factor = max(0.0, min(1.0, luck_factor))  # Clamp between 0 and 1
        
        # Adjust probabilities based on luck
        one_item_chance = 0.6 - (0.5 * luck_factor)  # Decreases with luck
        three_items_chance = 0.1 + (0.2 * luck_factor)  # Increases with luck
        two_items_chance = 1.0 - one_item_chance - three_items_chance
        
        # Determine number of items
        roll = random.random()
        if roll < one_item_chance:
            num_items = 1
        elif roll < one_item_chance + two_items_chance:
            num_items = 2
        else:
            num_items = 3
        
        # Generate items
        for _ in range(num_items):
            # Higher luck slightly improves item quality
            quality_bonus = int(luck_factor * 2)  # 0-2 bonus to quality based on luck
            quality = min(5, max(1, self.current_level + quality_bonus))
            
            item_type = random.choice(list(ItemType))
            item = ItemGenerator.generate_random_item(item_type, quality)
            if item:
                contents.append(item)
        
        return contents
    
    def handle_chest_interaction(self, x: int, y: int):
        """Handle player interaction with a chest."""
        chest_pos = (x, y)
        print(f"Checking chest at {chest_pos}, available chests: {list(self.chests.keys())}")
        
        if chest_pos not in self.chests:
            # Double check the cell type directly
            cell_type = self.dungeon.get_cell(x, y)
            if cell_type == CellType.CHEST:
                # Create a new chest entry if it wasn't tracked
                self.chests[chest_pos] = {
                    'opened': False,
                    'contents': self.generate_chest_contents()
                }
                print(f"Added missing chest at {chest_pos}")
            else:
                print(f"No chest found at {chest_pos}")
                return
        
        chest = self.chests[chest_pos]
        if chest['opened']:
            self.add_to_log("This chest is already empty", GREY)
            return
        
        # Open the chest
        chest['opened'] = True
        contents = chest['contents']
        
        if contents:
            # Scatter items around the chest
            for item in contents:
                # Find a valid position to drop the item
                drop_positions = []
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue  # Skip chest's position
                        new_x, new_y = x + dx, y + dy
                        if (0 <= new_x < self.dungeon.width and 
                            0 <= new_y < self.dungeon.height and
                            self.dungeon.get_cell(new_x, new_y) == CellType.FLOOR and
                            not self.is_position_occupied(new_x, new_y)):
                            drop_positions.append((new_x, new_y))
                
                if drop_positions:
                    # Choose a random valid position
                    drop_x, drop_y = random.choice(drop_positions)
                    # Store item in the dungeon
                    if not hasattr(self, 'ground_items'):
                        self.ground_items = {}
                    self.ground_items[(drop_x, drop_y)] = item
                    # Mark cell as containing an item
                    self.dungeon.grid[drop_y][drop_x] = CellType.ITEM
                    self.add_to_log(f"A {item.name} falls to the ground!", YELLOW)
                else:
                    # If no valid position found, add to inventory as fallback
                    if self.player.character.inventory.add_item(item):
                        self.add_to_log(f"Found: {item.name} (added to inventory)", GREEN)
                    else:
                        self.add_to_log(f"Found: {item.name} (inventory full, item lost)", RED)
        else:
            self.add_to_log("The chest is empty", GREY)
        
        # Change chest to floor so it appears opened
        self.dungeon.grid[y][x] = CellType.FLOOR
        print(f"Chest opened at {chest_pos}, contents: {[item.name for item in contents]}")
    
    def find_suitable_equipment_slot(self, item):
        """Find a suitable equipment slot for an item."""
        from logic.character_system import ItemType, EquipmentSlot
        
        # Map item types to equipment slots (only using valid enum values)
        slot_mapping = {
            ItemType.WEAPON: [EquipmentSlot.WEAPON_1, EquipmentSlot.WEAPON_2],
            ItemType.ARMOUR: [EquipmentSlot.TORSO],
            ItemType.HELMET: [EquipmentSlot.HEAD],
            ItemType.BOOTS: [EquipmentSlot.LEGS],
            ItemType.RING: [EquipmentSlot.RING_1, EquipmentSlot.RING_2],
            ItemType.AMULET: [EquipmentSlot.NECK]
        }
        
        possible_slots = slot_mapping.get(item.item_type, [])
        
        # Find the first available slot
        for slot in possible_slots:
            current_item = self.player.character.equipment.get_equipped_item(slot)
            if current_item is None:
                return slot
        
        # If no empty slot, return the first slot (will replace existing item)
        if possible_slots:
            return possible_slots[0]
        
        return None
    
    def handle_item_pickup(self, x: int, y: int):
        """Handle player picking up an item from the ground."""
        item_pos = (x, y)
        if item_pos in self.ground_items:
            item = self.ground_items[item_pos]
            if self.player.character.inventory.add_item(item):
                self.add_to_log(f"Picked up: {item.name}", GREEN)
                del self.ground_items[item_pos]
                self.dungeon.grid[y][x] = CellType.FLOOR
            else:
                self.add_to_log("Inventory is full!", RED)
    
    def handle_hp_pickup(self, x: int, y: int):
        """Handle player picking up an HP pickup."""
        pickup_pos = (x, y)
        print(f"Checking HP pickup at {pickup_pos}, available pickups: {self.hp_pickups}")
        
        # Check if this position has an HP pickup
        if pickup_pos not in self.hp_pickups:
            # Double check the cell type directly
            cell_type = self.dungeon.get_cell(x, y)
            if cell_type == CellType.HP_PICKUP:
                # Add it to our tracking set if it wasn't there
                self.hp_pickups.add(pickup_pos)
                print(f"Added missing HP pickup at {pickup_pos}")
            else:
                print(f"No HP pickup found at {pickup_pos}")
                return
        
        # Remove the pickup
        self.hp_pickups.remove(pickup_pos)
        self.dungeon.grid[y][x] = CellType.FLOOR
        
        # Heal the player
        heal_amount = random.randint(5, 15)  # Random healing amount
        old_hp = self.player.character.current_hp
        self.player.character.heal(heal_amount)
        actual_heal = self.player.character.current_hp - old_hp
        
        if actual_heal > 0:
            self.add_to_log(f"Picked up health potion! Healed {actual_heal} HP", GREEN)
        else:
            self.add_to_log("Picked up health potion, but you're already at full health", YELLOW)
        
        print(f"HP pickup collected at {pickup_pos}, healed {actual_heal} HP")
    
    def render(self):
        if self.state_manager.current_state == GameState.PLAYING and self.player:
            self.screen.fill(BLACK)
            
            # Render the dungeon viewport
            self.render_dungeon()
            
            # Render enemies
            self.render_enemies()
            
            # Render the player
            self.render_player()
            
            # Render UI elements
            self.render_ui()
            
            # Render health bars
            self.render_health_bars()
            
            # Render character sheet if toggled
            if self.show_character_sheet:
                self.render_character_sheet()
            
            # Render interactive inventory if toggled
            if self.show_interactive_inventory:
                self.interactive_character_screen.render(
                    self.screen, self.player.character, self.player.character.inventory)
        else:
            # Render menu/game over screens
            self.state_manager.render()
        
        pygame.display.flip()
    
    def render_dungeon(self):
        start_x = max(0, self.camera.x - VIEWPORT_WIDTH // 2)
        end_x = min(DUNGEON_WIDTH, start_x + VIEWPORT_WIDTH)
        start_y = max(0, self.camera.y - VIEWPORT_HEIGHT // 2)
        end_y = min(DUNGEON_HEIGHT, start_y + VIEWPORT_HEIGHT)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if (x, y) in self.explored:
                    screen_x = int((x - start_x) * GRID_SIZE)
                    screen_y = int((y - start_y) * GRID_SIZE)
                    
                    cell_type = self.dungeon.get_cell(x, y)
                    is_visible = (x, y) in self.visible
                    
                    # Get appropriate sprite based on cell type
                    sprite = None
                    if cell_type == CellType.FLOOR:
                        sprite = sprite_manager.load_oryx_sprite("floor_stone", SpriteType.TILES)
                        if sprite:
                            # Create a copy to tint
                            tinted_sprite = sprite.copy()
                            # Apply green tint for level 1, brown tint for level 2+
                            if self.current_level == 1:
                                tinted_sprite.fill((0, 255, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)  # Green for grass
                            else:
                                tinted_sprite.fill((139, 69, 19, 128), special_flags=pygame.BLEND_RGBA_MULT)  # Brown for dirt/cave
                            sprite = tinted_sprite
                    elif cell_type == CellType.WATER:
                        sprite = sprite_manager.load_oryx_sprite("water", SpriteType.TILES)
                        if sprite:
                            # Create a copy to tint
                            tinted_sprite = sprite.copy()
                            # Apply blue tint
                            tinted_sprite.fill((0, 0, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
                            sprite = tinted_sprite
                    elif cell_type == CellType.WALL:
                        if self.current_level == 1:
                            # Level 1: Trees with dark green tint
                            sprite = sprite_manager.load_oryx_sprite("tree", SpriteType.TILES)
                            if sprite:
                                tinted_sprite = sprite.copy()
                                tinted_sprite.fill((0, 100, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
                                sprite = tinted_sprite
                        else:
                            # Level 2+: Hash symbol with dark brown tint
                            sprite = sprite_manager.load_oryx_sprite("hash", SpriteType.TILES)
                            if sprite:
                                tinted_sprite = sprite.copy()
                                tinted_sprite.fill((65, 40, 15, 128), special_flags=pygame.BLEND_RGBA_MULT)  # Very dark brown
                                sprite = tinted_sprite
                    elif cell_type == CellType.DOOR:
                        sprite = sprite_manager.load_oryx_sprite("door_wooden", SpriteType.TILES)
                    elif cell_type == CellType.STAIRCASE:
                        sprite = sprite_manager.load_oryx_sprite("stairs_down", SpriteType.TILES)
                    elif cell_type == CellType.CHEST:
                        sprite = sprite_manager.load_oryx_sprite("chest", SpriteType.TILES)
                    elif cell_type == CellType.HP_PICKUP:
                        sprite = sprite_manager.load_oryx_sprite("health_potion", SpriteType.TILES)
                        if sprite:
                            # Create a copy to tint
                            tinted_sprite = sprite.copy()
                            # Apply red tint
                            tinted_sprite.fill((255, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
                            sprite = tinted_sprite
                    elif cell_type == CellType.ITEM:
                        # Get item at this position
                        item = self.ground_items.get((x, y))
                        if item:
                            # Choose sprite based on item type
                            sprite_map = {
                                'Sword': 'sword',
                                'Axe': 'axe',
                                'Shield': 'shield',
                                'Staff': 'staff',
                                'Bow': 'bow',
                                'Robe': 'robe',
                                'Ring': 'ring',
                                'Helmet': 'helmet'
                            }
                            sprite_name = sprite_map.get(item.name.split()[0], 'sword')  # Default to sword if unknown
                            sprite = sprite_manager.load_oryx_sprite(sprite_name, SpriteType.TILES)
                            if sprite:
                                # Create a copy to tint gold
                                tinted_sprite = sprite.copy()
                                # Apply gold tint (RGB: 255, 215, 0)
                                tinted_sprite.fill((255, 215, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
                                sprite = tinted_sprite
                    
                    if sprite:
                        # Render the sprite
                        self.screen.blit(sprite, (screen_x, screen_y))
                        
                        # Add a subtle overlay for non-visible explored areas
                        if not is_visible:
                            overlay = pygame.Surface((GRID_SIZE, GRID_SIZE))
                            overlay.set_alpha(150)  # Semi-transparent
                            overlay.fill(BLACK)
                            self.screen.blit(overlay, (screen_x, screen_y))
    
    def render_player(self):
        # Calculate player position on screen
        start_x = max(0, self.camera.x - VIEWPORT_WIDTH // 2)
        start_y = max(0, self.camera.y - VIEWPORT_HEIGHT // 2)
        
        screen_x = int((self.player.x - start_x) * GRID_SIZE)
        screen_y = int((self.player.y - start_y) * GRID_SIZE)
        
        # Calculate center position for the tile
        center_x = screen_x + GRID_SIZE // 2
        center_y = screen_y + GRID_SIZE // 2
        
        # Use the @ symbol sprite for the player
        sprite = sprite_manager.load_oryx_sprite("player", SpriteType.TILES)
        
        if sprite:
            # Create a copy to tint
            tinted_sprite = sprite.copy()
            # Apply yellow tint
            tinted_sprite.fill((255, 255, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Center the sprite in the tile
            sprite_rect = tinted_sprite.get_rect(center=(center_x, center_y))
            self.screen.blit(tinted_sprite, sprite_rect)
        
        # Flash red if recently damaged
        if hasattr(self.player.character, 'last_damage_time') and self.player.character.last_damage_time < 0.5:
            self.player.character.last_damage_time += 0.016  # Assuming 60 FPS
            flash_surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            flash_surface.fill((255, 0, 0, 150))  # Red with alpha
            flash_rect = flash_surface.get_rect(center=(center_x, center_y))
            self.screen.blit(flash_surface, flash_rect)
    
    def render_ui(self):
        """Render the main UI - now just calls sidebar rendering."""
        self.render_sidebar()
    
    def render_text(self, text: str, font_size: str, color: tuple, x: int, y: int) -> int:
        """
        Render text using sprite font and return the new y position.
        
        Args:
            text: Text to render
            font_size: One of 'title', 'header', 'text', or 'small'
            color: RGB color tuple
            x: X position
            y: Y position
            
        Returns:
            New Y position after rendering
        """
        surface = self.sprite_fonts[font_size].render_text(text.upper(), color)
        rect = surface.get_rect(topleft=(x, y))
        self.screen.blit(surface, rect)
        return y + rect.height
    
    def render_sidebar(self):
        """Render the game information sidebar."""
        # Sidebar background
        sidebar_rect = pygame.Rect(GAME_AREA_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 40), sidebar_rect)  # Dark blue-grey background
        pygame.draw.line(self.screen, WHITE, (GAME_AREA_WIDTH, 0), (GAME_AREA_WIDTH, WINDOW_HEIGHT), 2)
        
        # Sprite Fonts
        if not hasattr(self, 'sprite_fonts'):
            self.sprite_fonts = {
                'title': SpriteFont(scale=1.5),  # Larger scale for title
                'header': SpriteFont(scale=1.0),  # Medium scale for headers
                'text': SpriteFont(scale=0.75),   # Normal scale for text
                'small': SpriteFont(scale=0.5)    # Smaller scale for details
            }
        
        # Starting positions
        x = GAME_AREA_WIDTH + 10
        y = 10
        section_spacing = 20  # Increased spacing between sections
        
        # Create an extra small font for logs
        if not hasattr(self, 'log_font'):
            self.log_font = SpriteFont(scale=0.35)  # Even smaller than small font
        
        # === PLAYER INFO SECTION ===
        if hasattr(self.player, 'character'):
            char_data = self.player.character.get_character_summary()
            
            # Character portrait at the top (25% larger)
            portrait = self.class_portraits[self.player.character.character_class]
            scaled_portrait = pygame.transform.scale(portrait, (60, 60))  # 48 * 1.25 = 60
            portrait_rect = scaled_portrait.get_rect(topleft=(x, y))
            self.screen.blit(scaled_portrait, portrait_rect)
            y += 60 + 10  # Portrait height + small gap
            
            # Player name and level
            y = self.render_text("ADVENTURER", 'text', WHITE, x, y)
            y = self.render_text(f"LEVEL {char_data['level']}", 'header', WHITE, x, y)
            y += section_spacing
            
            # Health text
            current_hp, max_hp = char_data['hp']
            hp_color = GREEN if current_hp > max_hp * 0.7 else YELLOW if current_hp > max_hp * 0.3 else RED
            y = self.render_text("HP", 'text', hp_color, x, y)
            
            # HP numbers with slash
            hp_text = f"{current_hp}/{max_hp}"  # Removed spaces around slash since we have built-in spacing
            hp_surface = self.sprite_fonts['header'].render_text(hp_text, hp_color)
            hp_rect = hp_surface.get_rect(topleft=(x, y))
            self.screen.blit(hp_surface, hp_rect)
            y += 24  # Height of header font
            
            # Health bar (no numbers)
            bar_width = SIDEBAR_WIDTH - 20  # Wider health bar
            bar_height = 8  # Thinner health bar
            # Draw background
            bar_rect = pygame.Rect(x, y, bar_width, bar_height)
            pygame.draw.rect(self.screen, RED, bar_rect)
            # Draw health portion
            health_width = int(bar_width * (current_hp / max_hp))
            health_rect = pygame.Rect(x, y, health_width, bar_height)
            pygame.draw.rect(self.screen, hp_color, health_rect)
            y += bar_height + 10  # Small gap before XP bar
            
            # XP bar
            from logic.perk_system import PerkSystem
            perk_system = PerkSystem()
            current_exp = char_data['experience']
            next_level_exp = perk_system.calculate_experience_required(char_data['level'] + 1)
            
            # XP text
            y = self.render_text("XP", 'text', YELLOW, x, y)
            
            # XP numbers
            xp_text = f"{current_exp}/{next_level_exp}"
            xp_surface = self.sprite_fonts['header'].render_text(xp_text, YELLOW)
            xp_rect = xp_surface.get_rect(topleft=(x, y))
            self.screen.blit(xp_surface, xp_rect)
            y += 24  # Height of header font
            
            # XP bar
            xp_bar_rect = pygame.Rect(x, y, bar_width, bar_height)
            pygame.draw.rect(self.screen, (100, 100, 0), xp_bar_rect)  # Dark gold background
            
            # Calculate XP progress
            xp_progress = current_exp / next_level_exp if next_level_exp > 0 else 1.0
            xp_width = int(bar_width * xp_progress)
            xp_fill_rect = pygame.Rect(x, y, xp_width, bar_height)
            pygame.draw.rect(self.screen, YELLOW, xp_fill_rect)  # Bright gold fill
            # Draw border
            pygame.draw.rect(self.screen, WHITE, bar_rect, 1)
            y += bar_height + section_spacing
        
        # Player status (only show DEAD)
        if self.player_is_dead:
            status_text = "DEAD"
            status_surface = self.sprite_fonts['text'].render_text(status_text, RED)
            status_rect = status_surface.get_rect(topleft=(x, y))
            self.screen.blit(status_surface, status_rect)
            y += 30  # Fixed spacing after status
        
        y += section_spacing
        
        # === GAME LOG SECTION ===
        y += section_spacing  # Extra space before log section
        y = self.render_text("LOG", 'header', YELLOW, x, y)
        y += section_spacing  # More space after the title
        
        # Calculate available height for log entries
        available_height = WINDOW_HEIGHT - MINIMAP_SIZE - 20 - y  # 20px buffer
        
        # Render game log entries
        for message, color in self.game_log:
            # Stop if we're getting too close to the minimap
            if y > WINDOW_HEIGHT - MINIMAP_SIZE - 40:  # 40px buffer
                break
                
            # Wrap long messages if needed
            if len(message) > 25:  # Approximate character limit for sidebar width
                words = message.split(' ')
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + word) > 25:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word + " "
                    else:
                        current_line += word + " "
                if current_line:
                    lines.append(current_line.strip())
                
                for line in lines:
                    if y > WINDOW_HEIGHT - MINIMAP_SIZE - 40:
                        break
                    log_surface = self.log_font.render_text(line, color)
                    log_rect = log_surface.get_rect(topleft=(x, y))
                    self.screen.blit(log_surface, log_rect)
                    y += 10  # Tighter spacing for smaller font
            else:
                log_surface = self.log_font.render_text(message, color)
                log_rect = log_surface.get_rect(topleft=(x, y))
                self.screen.blit(log_surface, log_rect)
                y += 10  # Tighter spacing for smaller font
        
        # === MINIMAP ===
        # Always render minimap at bottom of sidebar
        minimap_y = WINDOW_HEIGHT - MINIMAP_SIZE - 10
        
        self.minimap.render(self.screen, self.player.get_position(), (GAME_AREA_WIDTH + 25, minimap_y))
    
    def get_cell_colour(self, cell_type: CellType, is_visible: bool = True) -> Tuple[int, int, int]:
        if cell_type == CellType.WALL:
            base_colour = GREY
        elif cell_type == CellType.FLOOR:
            base_colour = WHITE
        elif cell_type == CellType.DOOR:
            base_colour = BROWN
        elif cell_type == CellType.STAIRCASE:
            base_colour = YELLOW  # Bright yellow for visibility
        elif cell_type == CellType.CHEST:
            base_colour = (139, 69, 19)  # Brown for chests
        elif cell_type == CellType.HP_PICKUP:
            base_colour = (255, 100, 100)  # Light red for HP pickups
        else:
            base_colour = BLACK
        
        # Dim colours for non-visible explored areas
        if not is_visible:
            return tuple(max(0, int(c * 0.4)) for c in base_colour)
        
        return base_colour
    
    def process_turn_actions(self):
        """Process queued turn-based actions."""
        # Process all queued actions
        actions_processed = 0
        max_actions_per_frame = 10  # Prevent infinite loops
        player_acted = False
        
        while actions_processed < max_actions_per_frame:
            next_action = self.turn_manager.process_next_action()
            if not next_action:
                break
                
            completion_time, action = next_action
            self.execute_action(action)
            actions_processed += 1
            
            # Track if player acted this frame
            if action.actor_id == "player":
                player_acted = True
        
        # Schedule enemy actions if player just acted
        if player_acted:
            self.schedule_enemy_actions()
    
    def execute_action(self, action):
        """Execute a specific action."""
        if action.action_type == ActionType.MOVE:
            self.execute_move_action(action)
        elif action.action_type == ActionType.ATTACK:
            self.execute_attack_action(action)
        elif action.action_type == ActionType.WAIT:
            self.execute_wait_action(action)
        elif action.action_type == ActionType.RELOAD:
            self.execute_reload_action(action)
    
    def execute_move_action(self, action):
        """Execute a movement action."""
        if action.actor_id == "player":
            # Don't execute player actions if dead
            if self.player_is_dead:
                return
            new_x, new_y = action.target_pos
            old_explored_count = len(self.explored)
            self.player.move(new_x - self.player.x, new_y - self.player.y)
            self.update_visibility()
            
            # Check for interactions with chests, items, and HP pickups
            cell_type = self.dungeon.get_cell(new_x, new_y)
            print(f"Player moved to ({new_x}, {new_y}), cell type: {cell_type}")
            if cell_type == CellType.CHEST:
                print("Triggering chest interaction")
                self.handle_chest_interaction(new_x, new_y)
            elif cell_type == CellType.HP_PICKUP:
                print("Triggering HP pickup interaction")
                self.handle_hp_pickup(new_x, new_y)
            elif cell_type == CellType.ITEM:
                print("Triggering item pickup")
                self.handle_item_pickup(new_x, new_y)
            elif cell_type == CellType.STAIRCASE:
                print("Player is now standing on a staircase! Press '>' to go down or '<' to go up.")
                self.add_to_log("Standing on stairs. Press '>' to descend or '<' to ascend", YELLOW)
            
            # Log exploration progress
            new_explored_count = len(self.explored)
            if new_explored_count > old_explored_count:
                new_tiles = new_explored_count - old_explored_count
                if new_tiles >= 5:
                    self.add_to_log("Exploring new areas...", BLUE)
            
            print(f"Player moves to ({new_x}, {new_y})")
            
            # Process regeneration after player movement
            regen_amount = self.player.character.process_regeneration()
            if regen_amount > 0:
                self.add_to_log(f"Regenerated {regen_amount} HP", GREEN)
        else:
            # Enemy movement
            enemy = self.find_enemy_by_id(action.actor_id)
            if enemy and action.target_pos:
                new_x, new_y = action.target_pos
                self.enemy_manager.move_enemy(enemy, new_x, new_y, self.player.x, self.player.y)
                print(f"{enemy.enemy_type.value} moves to ({new_x}, {new_y})")
    
    def execute_attack_action(self, action):
        """Execute an attack action."""
        if action.actor_id == "player":
            # Don't execute player actions if dead
            if self.player_is_dead:
                return
            # Player attacking enemy
            enemy = self.enemy_manager.get_enemy_at(*action.target_pos)
            if enemy and enemy.is_alive:
                self.handle_combat(self.player, enemy)
                # Fire weapon if it's a ranged weapon
                self.turn_manager.fire_weapon("player")
                
                # Process regeneration after combat
                regen_amount = self.player.character.process_regeneration()
                if regen_amount > 0:
                    self.add_to_log(f"Regenerated {regen_amount} HP", GREEN)
        else:
            # Enemy attacking player
            enemy = self.find_enemy_by_id(action.actor_id)
            if enemy and action.target_id == "player":
                # Check if enemy is adjacent to player
                distance = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                if distance <= 1:
                    self.handle_combat_enemy_attacks_player(enemy, self.player)
    
    def execute_wait_action(self, action):
        """Execute a wait action."""
        if action.actor_id == "player":
            # Don't execute player actions if dead
            if self.player_is_dead:
                return
            self.add_to_log("You wait and listen...", GREY)
            print("Player waits...")
            
            # Process regeneration after waiting
            regen_amount = self.player.character.process_regeneration()
            if regen_amount > 0:
                self.add_to_log(f"Regenerated {regen_amount} HP", GREEN)
        else:
            enemy = self.find_enemy_by_id(action.actor_id)
            if enemy:
                print(f"{enemy.enemy_type.value} waits...")
    
    def execute_reload_action(self, action):
        """Execute a reload action."""
        if action.actor_id == "player" and self.player_is_dead:
            return
        self.turn_manager.reload_weapon(action.actor_id)
        if action.actor_id == "player":
            print("Player reloads weapon")
        else:
            enemy = self.find_enemy_by_id(action.actor_id)
            if enemy:
                print(f"{enemy.enemy_type.value} reloads weapon")
    
    def find_enemy_by_id(self, enemy_id: str):
        """Find an enemy by their ID."""
        # Extract position from enemy ID (format: "enemy_x_y")
        try:
            parts = enemy_id.split("_")
            if len(parts) >= 3:
                x, y = int(parts[1]), int(parts[2])
                return self.enemy_manager.get_enemy_at(x, y)
        except:
            pass
        return None
    
    def schedule_enemy_actions(self):
        """Schedule actions for all enemies that can act."""
        # Don't schedule enemy actions if player is dead
        if self.player_is_dead:
            return
            
        living_enemies = self.enemy_manager.get_living_enemies()
        enemies_scheduled = 0
        for enemy in living_enemies:
            enemy_id = f"enemy_{enemy.x}_{enemy.y}"
            
            if self.turn_manager.scheduler.can_entity_act(enemy_id):
                enemies_scheduled += 1
                
                # Simple AI: move toward player or attack if adjacent
                distance = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                
                if distance == 1:
                    # Adjacent to player - attack
                    self.turn_manager.schedule_enemy_action(
                        enemy_id, ActionType.ATTACK,
                        target_id="player",
                        dexterity=enemy.dexterity
                    )
                elif distance <= 8 and enemy.can_see_player(self.player.x, self.player.y):
                    # Can see player - move toward them
                    target_x, target_y = self.get_enemy_move_target(enemy)
                    if target_x != enemy.x or target_y != enemy.y:
                        self.turn_manager.schedule_enemy_action(
                            enemy_id, ActionType.MOVE,
                            target_pos=(target_x, target_y),
                            dexterity=enemy.dexterity
                        )
                    else:
                        # Can't move - wait
                        self.turn_manager.schedule_enemy_action(
                            enemy_id, ActionType.WAIT,
                            dexterity=enemy.dexterity
                        )
                else:
                    # Random movement or wait
                    if random.random() < 0.3:  # 30% chance to move
                        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                        dx, dy = random.choice(directions)
                        new_x, new_y = enemy.x + dx, enemy.y + dy
                        
                        if (self.dungeon.can_move_to(new_x, new_y) and 
                            not self.enemy_manager.get_enemy_at(new_x, new_y) and
                            (new_x, new_y) != (self.player.x, self.player.y)):
                            
                            self.turn_manager.schedule_enemy_action(
                                enemy_id, ActionType.MOVE,
                                target_pos=(new_x, new_y),
                                dexterity=enemy.dexterity
                            )
                        else:
                            self.turn_manager.schedule_enemy_action(
                                enemy_id, ActionType.WAIT,
                                dexterity=enemy.dexterity
                            )
                    else:
                        self.turn_manager.schedule_enemy_action(
                            enemy_id, ActionType.WAIT,
                            dexterity=enemy.dexterity
                        )
        
        # Only print summary if enemies were scheduled
        if enemies_scheduled > 0:
            print(f"Scheduled {enemies_scheduled} enemy actions")
    
    def get_enemy_move_target(self, enemy) -> Tuple[int, int]:
        """Get the target position for an enemy to move toward the player."""
        # Simple pathfinding toward player
        dx = 0
        dy = 0
        
        if self.player.x > enemy.x:
            dx = 1
        elif self.player.x < enemy.x:
            dx = -1
            
        if self.player.y > enemy.y:
            dy = 1
        elif self.player.y < enemy.y:
            dy = -1
        
        target_x = enemy.x + dx
        target_y = enemy.y + dy
        
        # Check if target position is valid
        if (self.dungeon.can_move_to(target_x, target_y) and 
            not self.enemy_manager.get_enemy_at(target_x, target_y) and
            (target_x, target_y) != (self.player.x, self.player.y)):
            return target_x, target_y
        
        # Try just moving in one direction
        if dx != 0:
            alt_x = enemy.x + dx
            if (self.dungeon.can_move_to(alt_x, enemy.y) and 
                not self.enemy_manager.get_enemy_at(alt_x, enemy.y) and
                (alt_x, enemy.y) != (self.player.x, self.player.y)):
                return alt_x, enemy.y
        
        if dy != 0:
            alt_y = enemy.y + dy
            if (self.dungeon.can_move_to(enemy.x, alt_y) and 
                not self.enemy_manager.get_enemy_at(enemy.x, alt_y) and
                (enemy.x, alt_y) != (self.player.x, self.player.y)):
                return enemy.x, alt_y
        
        # Can't move toward player
        return enemy.x, enemy.y
    
    def handle_combat_enemy_attacks_player(self, enemy, player):
        """Handle combat when an enemy attacks the player."""
        enemy_damage = enemy.get_attack_damage()
        player_died = player.character.take_damage(enemy_damage)
        
        if player_died:
            self.player_is_dead = True
            self.turn_manager.remove_entity("player")  # Cancel any pending actions
            self.add_to_log(f"{enemy.enemy_type.value} deals fatal blow!", RED)
            self.add_to_log("You have died!", RED)
            self.add_to_log("GAME OVER", RED)
            self.add_to_log("Press ESC to exit", GREY)
            print(f"{enemy.enemy_type.value} deals {enemy_damage} damage! You died!")
        else:
            self.add_to_log(f"{enemy.enemy_type.value} hits you for {enemy_damage} damage!", RED)
            print(f"{enemy.enemy_type.value} deals {enemy_damage} damage to you!")
    
    def render_enemies(self):
        """Render all visible enemies."""
        start_x = max(0, self.camera.x - VIEWPORT_WIDTH // 2)
        start_y = max(0, self.camera.y - VIEWPORT_HEIGHT // 2)
        
        for enemy in self.enemy_manager.get_living_enemies():
            # Only render if enemy is in visible area
            if (enemy.x, enemy.y) in self.visible:
                screen_x = int((enemy.x - start_x) * GRID_SIZE)
                screen_y = int((enemy.y - start_y) * GRID_SIZE)
                
                # Skip if enemy is off screen
                if (screen_x < -GRID_SIZE or screen_x > WINDOW_WIDTH or 
                    screen_y < -GRID_SIZE or screen_y > WINDOW_HEIGHT - 150):
                    continue
                
                # Get enemy sprite based on type
                enemy_sprite_map = {
                    EnemyType.CHICKEN: "chicken",
                    EnemyType.FROG: "frog",
                    EnemyType.SNAKE: "snake",
                    EnemyType.BIRD: "bird",
                    EnemyType.SPIDER: "spider",
                    EnemyType.GOBLIN: "goblin"  # Added goblin sprite mapping
                }
                
                sprite_name = enemy_sprite_map.get(enemy.enemy_type, "goblin")  # Default to goblin instead of rat
                sprite = sprite_manager.load_oryx_sprite(sprite_name, SpriteType.TILES)
                
                if sprite:
                    # Create a copy for tinting if needed
                    if enemy.enemy_type == EnemyType.GOBLIN:
                        # Apply bright green tint for goblins
                        tinted_sprite = sprite.copy()
                        tinted_sprite.fill((0, 255, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)  # Bright Green
                        sprite = tinted_sprite

                    # Center the sprite in the tile
                    center_x = screen_x + GRID_SIZE // 2
                    center_y = screen_y + GRID_SIZE // 2
                    sprite_rect = sprite.get_rect(center=(center_x, center_y))
                    self.screen.blit(sprite, sprite_rect)
                    
                    # Flash red if recently damaged
                    if enemy.damage_flash > 0:
                        flash_surface = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
                        flash_surface.fill((255, 0, 0, 150))  # Red with alpha
                        flash_rect = flash_surface.get_rect(center=(center_x, center_y))
                        self.screen.blit(flash_surface, flash_rect)
    
    def get_enemy_colour(self, enemy_type: EnemyType) -> Tuple[int, int, int]:
        """Get colour for enemy based on type."""
        colours = {
            EnemyType.RAT: (139, 69, 19),      # Brown
            EnemyType.GOBLIN: (34, 139, 34),   # Forest Green
            EnemyType.SKELETON: (211, 211, 211), # Light Grey
            EnemyType.SPIDER: (75, 0, 130),    # Indigo
            EnemyType.ORC: (220, 20, 60),      # Crimson
            EnemyType.TROLL: (85, 107, 47)     # Dark Olive Green
        }
        return colours.get(enemy_type, WHITE)
    
    def render_health_bars(self):
        """Render health bars for visible enemies."""
        # Enemy health bars removed for cleaner look
        pass
    
    def handle_combat(self, player, enemy):
        """Handle combat between player and enemy."""
        # Player attacks enemy
        player_damage = player.character.get_attack_damage()
        enemy_died = enemy.take_damage(player_damage)
        
        # Log player attack
        self.add_to_log(f"You hit {enemy.enemy_type.value} for {player_damage} damage!", WHITE)
        
        if enemy_died:
            # Grant experience using new system
            level_up_messages = player.character.gain_experience(enemy.exp_value)
            
            self.add_to_log(f"Defeated {enemy.enemy_type.value}!", GREEN)
            self.add_to_log(f"Gained {enemy.exp_value} experience", YELLOW)
            
            # Add level up messages to log
            for message in level_up_messages:
                self.add_to_log(message, YELLOW)
            
            print(f"Defeated {enemy.enemy_type.value}! Gained {enemy.exp_value} experience.")
            if level_up_messages:
                for message in level_up_messages:
                    print(message)
        else:
            # Enemy counter-attacks
            enemy_damage = enemy.get_attack_damage()
            player_died = player.character.take_damage(enemy_damage)
            
            if player_died:
                self.player_is_dead = True
                self.turn_manager.remove_entity("player")  # Cancel any pending actions
                self.add_to_log("You have died!", RED)
                self.add_to_log("GAME OVER", RED)
                self.add_to_log("Press ESC to exit", GREY)
                print("You died! Game Over.")
            else:
                self.add_to_log(f"{enemy.enemy_type.value} hits you for {enemy_damage} damage!", RED)
                print(f"Combat! You deal {player_damage} damage, enemy deals {enemy_damage} damage.")
    
    def is_position_occupied(self, x: int, y: int) -> bool:
        """Check if a position is occupied by player or enemy."""
        # Check if player is at this position
        if self.player.x == x and self.player.y == y:
            return True
        
        # Check if any enemy is at this position
        enemy_at_pos = self.enemy_manager.get_enemy_at(x, y)
        return enemy_at_pos is not None and enemy_at_pos.is_alive
    
    def render_character_sheet(self):
        """Display character information including perks."""
        if not self.show_character_sheet:
            return
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Character sheet background
        sheet_width = 600
        sheet_height = 500
        sheet_x = (WINDOW_WIDTH - sheet_width) // 2
        sheet_y = (WINDOW_HEIGHT - sheet_height) // 2
        
        sheet_surface = pygame.Surface((sheet_width, sheet_height))
        sheet_surface.fill(DARK_GREY)
        pygame.draw.rect(sheet_surface, WHITE, (0, 0, sheet_width, sheet_height), 2)
        
        # Fonts
        title_font = pygame.font.Font(None, 32)
        text_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        # Get character summary
        summary = self.player.character.get_character_summary()
        
        # Title
        title_text = title_font.render(f"{summary['name']} - Level {summary['level']}", True, YELLOW)
        title_rect = title_text.get_rect(centerx=sheet_width // 2, y=10)
        sheet_surface.blit(title_text, title_rect)
        
        # Experience and perk points
        exp_text = text_font.render(f"Experience: {summary['experience']} ({summary['experience_to_next']} to next level)", True, WHITE)
        sheet_surface.blit(exp_text, (20, 50))
        
        perk_points_text = text_font.render(f"Perk Points: {summary['perk_points']}", True, YELLOW)
        sheet_surface.blit(perk_points_text, (20, 75))
        
        # Health
        hp_current, hp_max = summary['hp']
        hp_text = text_font.render(f"Health: {hp_current}/{hp_max}", True, GREEN if hp_current > hp_max * 0.5 else RED)
        sheet_surface.blit(hp_text, (20, 100))
        
        # Stats section
        stats_y = 130
        stats_text = text_font.render("Stats:", True, WHITE)
        sheet_surface.blit(stats_text, (20, stats_y))
        
        stats_data = summary['stats']
        y_offset = stats_y + 25
        for stat, (base, bonus, total) in stats_data.items():
            stat_display = f"{stat.value.title()}: {base}"
            if bonus != 0:
                stat_display += f" + {bonus} = {total}"
            stat_text = small_font.render(stat_display, True, WHITE)
            sheet_surface.blit(stat_text, (40, y_offset))
            y_offset += 20
        
        # Equipment section
        equipment_y = y_offset + 10
        equipment_text = text_font.render("Equipment:", True, WHITE)
        sheet_surface.blit(equipment_text, (300, stats_y))
        
        equipment_data = summary['equipment']
        y_offset = stats_y + 25
        for slot, item_name in equipment_data.items():
            if item_name != "Empty":
                equipment_display = f"{slot.replace('_', ' ').title()}: {item_name}"
                eq_text = small_font.render(equipment_display, True, WHITE)
                sheet_surface.blit(eq_text, (320, y_offset))
                y_offset += 20
        
        # Perk bonuses section (if any)
        if summary.get('perk_bonuses'):
            perk_bonus_y = equipment_y + 20
            perk_title = text_font.render("Active Perk Bonuses:", True, YELLOW)
            sheet_surface.blit(perk_title, (20, perk_bonus_y))
            
            y_offset = perk_bonus_y + 25
            for bonus_type, value in summary['perk_bonuses'].items():
                if value != 0:
                    bonus_display = f"{bonus_type.replace('_', ' ').title()}: +{value}"
                    bonus_text = small_font.render(bonus_display, True, GREEN)
                    sheet_surface.blit(bonus_text, (40, y_offset))
                    y_offset += 20
        
        # Sight range
        sight_range_text = text_font.render(f"Sight Range: {summary['sight_range']}", True, WHITE)
        sheet_surface.blit(sight_range_text, (300, equipment_y + 50))
        
        # Instructions
        instructions = [
            "Press 'C' to close",
            "Press 'P' to open perk tree (Coming Soon!)"
        ]
        
        for i, instruction in enumerate(instructions):
            instruction_text = small_font.render(instruction, True, YELLOW)
            instruction_rect = instruction_text.get_rect(centerx=sheet_width // 2, y=sheet_height - 60 + i * 20)
            sheet_surface.blit(instruction_text, instruction_rect)
        
        # Blit the character sheet to screen
        self.screen.blit(sheet_surface, (sheet_x, sheet_y))
    
    def start_new_game(self, character: Character):
        """Start a new game with the given character."""
        # Initialize game components
        self.current_level = 1
        self.pending_level_transition = False
        self.dungeon = DungeonWithStairs(DUNGEON_WIDTH, DUNGEON_HEIGHT, self.current_level)
        self.player = Player(self.dungeon.start_pos[0], self.dungeon.start_pos[1])
        self.player.character = character  # Use the selected character
        self.camera = Camera()
        self.minimap = Minimap(self.dungeon)
        self.enemy_manager = EnemyManager()
        
        # Reset game state
        self.explored = set()
        self.visible = set()
        self.game_start_time = time.time()
        self.show_character_sheet = False
        self.player_is_dead = False
        
        # Reset auto-explore state
        self.auto_explore_active = False
        self.auto_explore_path = []
        
        # Reset level navigation state
        self.level_history = {}
        
        # Reset treasure system
        self.chests = {}
        self.hp_pickups = set()
        self.ground_items = {}  # Initialize ground items tracking
        
        # Initialize turn-based system
        self.turn_manager = TurnManager()
        
        # Set up player weapon
        weapon_name = "Unarmed"
        weapon_item = character.equipment.get_equipped_item(EquipmentSlot.WEAPON_1)
        if weapon_item:
            weapon_name = weapon_item.name
        self.turn_manager.set_entity_weapon("player", weapon_name)
        
        # Initialize enemies and visibility
        self.enemy_manager.spawn_enemies_in_dungeon(
            self.dungeon, 
            player_start_pos=self.player.get_position(),
            dungeon_level=self.current_level
        )
        
        # Set up enemy weapons
        for enemy in self.enemy_manager.get_living_enemies():
            enemy_id = f"enemy_{enemy.x}_{enemy.y}"
            enemy_weapon = self.get_enemy_weapon_name(enemy.enemy_type)
            self.turn_manager.set_entity_weapon(enemy_id, enemy_weapon)
        
        self.update_visibility()
        
        # Schedule initial enemy actions
        self.schedule_enemy_actions()
        
        # Initialize game log with welcome messages
        self.game_log = []
        self.add_to_log(f"{character.name} enters the dungeon!", YELLOW)
        enemy_count = len(self.enemy_manager.get_living_enemies())
        self.add_to_log(f"You sense {enemy_count} enemies lurking...", RED)
        self.add_to_log("Adventure begins!", GREEN)
        self.add_to_log("Press ESC to exit", GREY)
        
        print(f"Started new game as {character.name}! Turn-based combat enabled.")
        print(f"Spawned {len(self.enemy_manager.get_living_enemies())} enemies")
    
    def get_enemy_weapon_name(self, enemy_type: EnemyType) -> str:
        """Get the weapon name for an enemy type."""
        weapon_names = {
            EnemyType.CHICKEN: "Beak",
            EnemyType.FROG: "Tongue",
            EnemyType.SNAKE: "Fangs",
            EnemyType.BIRD: "Talons",
            EnemyType.SPIDER: "Fangs"
        }
        return weapon_names.get(enemy_type, "Claws")
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        # Create character with default class (Warrior)
        self.character = CharacterClassData.create_character(CharacterClass.WARRIOR, "Adventurer")
    
    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy
    
    def get_position(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    def get_sight_range(self) -> int:
        return self.character.get_sight_range()

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
    
    def update(self, target_x: int, target_y: int):
        self.x = target_x
        self.y = target_y

class Dungeon:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[CellType.WALL for _ in range(width)] for _ in range(height)]
        self.start_pos = (width // 2, height // 2)
        
        # Generate the dungeon
        self.generate()
    
    def generate(self):
        """Generate a dungeon using a simple room and corridor algorithm."""
        # Start with all walls
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = CellType.WALL
        
        # Generate rooms
        rooms = []
        max_rooms = 15
        room_attempts = 50
        
        # Add some water features (ponds and streams)
        self.add_water_features()
        
        for _ in range(room_attempts):
            if len(rooms) >= max_rooms:
                break
                
            # Random room size
            room_width = random.randint(4, 10)
            room_height = random.randint(4, 10)
            
            # Random position
            x = random.randint(1, self.width - room_width - 1)
            y = random.randint(1, self.height - room_height - 1)
            
            # Check if room overlaps with existing rooms
            new_room = Room(x, y, room_width, room_height)
            if not any(new_room.intersects(room) for room in rooms):
                rooms.append(new_room)
                
                # Carve out the room
                for room_y in range(y, y + room_height):
                    for room_x in range(x, x + room_width):
                        self.grid[room_y][room_x] = CellType.FLOOR
        
        # Connect rooms with corridors
        for i in range(len(rooms) - 1):
            self.create_corridor(rooms[i], rooms[i + 1])
        
        # Set start position in the first room
        if rooms:
            first_room = rooms[0]
            self.start_pos = (first_room.center_x, first_room.center_y)
    
    def create_corridor(self, room1: 'Room', room2: 'Room'):
        """Create a corridor between two rooms."""
        # Get centers of rooms
        x1, y1 = room1.center_x, room1.center_y
        x2, y2 = room2.center_x, room2.center_y
        
        # Create L-shaped corridor
        if random.choice([True, False]):
            # Horizontal first, then vertical
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.grid[y1][x] = CellType.FLOOR
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.grid[y][x2] = CellType.FLOOR
        else:
            # Vertical first, then horizontal
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.grid[y][x1] = CellType.FLOOR
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.grid[y2][x] = CellType.FLOOR
    
    def can_move_to(self, x: int, y: int, can_swim: bool = False) -> bool:
        """Check if the player can move to the given position."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        cell = self.grid[y][x]
        if cell == CellType.WATER:
            return can_swim
        return cell in [CellType.FLOOR, CellType.DOOR, CellType.STAIRCASE, CellType.CHEST, CellType.HP_PICKUP, CellType.ITEM]
    
    def get_cell(self, x: int, y: int) -> CellType:
        """Get the cell type at the given position."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return CellType.WALL
        return self.grid[y][x]
        
    def add_water_features(self):
        """Add water features like ponds and streams to the dungeon."""
        if self.level == 1:  # Natural water features for forest level
            self._add_forest_water_features()
        elif self.level == 2:  # Underground water for cavern level
            self._add_cavern_water_features()
        # Level 3 has no water (goblin warren)
    
    def _add_forest_water_features(self):
        """Add natural forest water features - meandering streams and natural ponds."""
        feature_type = random.choice(['stream', 'ponds'])
        
        if feature_type == 'stream':
            # Create one major meandering stream
            # Start from a random edge
            if random.choice([True, False]):
                # West to East
                x = 2
                y = random.randint(10, self.height - 10)
                dx = 1
                dy = 0
            else:
                # North to South
                x = random.randint(10, self.width - 10)
                y = 2
                dx = 0
                dy = 1
            
            # Create meandering path
            points = []
            while 0 < x < self.width - 1 and 0 < y < self.height - 1:
                points.append((x, y))
                
                # Randomly adjust direction while maintaining general flow
                if random.random() < 0.3:  # 30% chance to meander
                    if dx != 0:  # Moving horizontally
                        y += random.choice([-1, 0, 0, 1])  # Bias towards straight
                    else:  # Moving vertically
                        x += random.choice([-1, 0, 0, 1])  # Bias towards straight
                
                x += dx
                y += dy
            
            # Widen the stream and add some natural variation
            for px, py in points:
                # Main stream
                self.grid[py][px] = CellType.WATER
                
                # Add some width variation
                if random.random() < 0.7:  # 70% chance for width at each point
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = px + dx, py + dy
                        if (0 < nx < self.width - 1 and 0 < ny < self.height - 1 and
                            self.grid[ny][nx] != CellType.WATER):
                            if random.random() < 0.3:  # 30% chance for each adjacent tile
                                self.grid[ny][nx] = CellType.WATER
        
        else:  # ponds
            # Create 2-3 natural ponds with irregular shapes
            num_ponds = random.randint(2, 3)
            for _ in range(num_ponds):
                # Choose pond center away from edges
                center_x = random.randint(10, self.width - 10)
                center_y = random.randint(10, self.height - 10)
                
                # Create irregular pond shape using cellular automata-like approach
                pond_tiles = set([(center_x, center_y)])
                size = random.randint(15, 25)  # Target pond size
                
                while len(pond_tiles) < size:
                    # Expand from existing water tiles
                    new_tiles = set()
                    for wx, wy in pond_tiles:
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = wx + dx, wy + dy
                            if (0 < nx < self.width - 1 and 0 < ny < self.height - 1 and
                                (nx, ny) not in pond_tiles and
                                random.random() < 0.6):  # 60% chance to expand
                                new_tiles.add((nx, ny))
                    pond_tiles.update(new_tiles)
                
                # Apply the pond to the grid
                for px, py in pond_tiles:
                    self.grid[py][px] = CellType.WATER
    
    def _add_cavern_water_features(self):
        """Add underground water features - small pools and narrow streams."""
        # Add a few small underground pools
        num_pools = random.randint(3, 5)
        for _ in range(num_pools):
            center_x = random.randint(5, self.width - 6)
            center_y = random.randint(5, self.height - 6)
            radius = random.randint(1, 2)
            
            for y in range(center_y - radius, center_y + radius + 1):
                for x in range(center_x - radius, center_x + radius + 1):
                    if (0 <= x < self.width and 0 <= y < self.height and
                        ((x - center_x) ** 2 + (y - center_y) ** 2) <= radius ** 2):
                        self.grid[y][x] = CellType.WATER


class DungeonWithStairs(Dungeon):
    """Extended dungeon class that places staircases for level progression."""
    
    def __init__(self, width: int, height: int, level: int = 1):
        self.level = level
        super().__init__(width, height)
    
    def generate(self):
        """Generate dungeon with staircase placement."""
        # Call parent generation
        super().generate()
        
        # Place staircase in a suitable location
        self.place_staircase()
        
        # Place chests and HP pickups
        self.place_treasures()
    
    def place_staircase(self):
        """Place a staircase in the dungeon."""
        # Find all floor tiles that are not too close to start position
        start_x, start_y = self.start_pos
        candidates = []
        
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == CellType.FLOOR:
                    # Calculate distance from start position
                    distance = abs(x - start_x) + abs(y - start_y)
                    
                    # Must be reasonably far from start and have space around it
                    if distance > 10:
                        # Check that it's not in a narrow corridor
                        open_neighbors = 0
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                if dx == 0 and dy == 0:
                                    continue
                                nx, ny = x + dx, y + dy
                                if (0 <= nx < self.width and 0 <= ny < self.height and 
                                    self.grid[ny][nx] == CellType.FLOOR):
                                    open_neighbors += 1
                        
                        # Prefer locations with some open space (room centers)
                        if open_neighbors >= 3:
                            candidates.append((x, y, distance))
        
        if candidates:
            # Sort by distance and pick from the farthest third
            candidates.sort(key=lambda c: c[2], reverse=True)
            top_third = candidates[:max(1, len(candidates) // 3)]
            stair_x, stair_y, _ = random.choice(top_third)
            self.grid[stair_y][stair_x] = CellType.STAIRCASE
            print(f"Placed staircase at ({stair_x}, {stair_y}) for level {self.level}")
            return  # Make sure we only place one staircase
        else:
            # Fallback: place in any floor tile far from start
            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    if self.grid[y][x] == CellType.FLOOR:
                        distance = abs(x - start_x) + abs(y - start_y)
                        if distance > 5:
                            self.grid[y][x] = CellType.STAIRCASE
                            print(f"Placed fallback staircase at ({x}, {y})")
                            return
    
    def place_treasures(self):
        """Place chests and HP pickups throughout the dungeon."""
        # Find all rooms from the generation process
        rooms = self._find_rooms()
        
        # Place chests (max 2 per room)
        for room in rooms:
            self._place_chests_in_room(room)
        
        # Place HP pickups randomly throughout dungeon
        self._place_hp_pickups()
    
    def _find_rooms(self):
        """Find room areas in the generated dungeon."""
        rooms = []
        visited = set()
        
        # Find rectangular room areas
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if (x, y) not in visited and self.grid[y][x] == CellType.FLOOR:
                    # Try to find a room starting from this point
                    room = self._discover_room(x, y, visited)
                    if room and room.width >= 4 and room.height >= 4:  # Only consider sizeable rooms
                        rooms.append(room)
        
        return rooms
    
    def _discover_room(self, start_x: int, start_y: int, visited: set):
        """Discover a room's boundaries starting from a floor tile."""
        # Find the bounds of this floor area
        min_x = max_x = start_x
        min_y = max_y = start_y
        
        # Expand to find room boundaries
        floor_tiles = set()
        to_check = [(start_x, start_y)]
        
        while to_check:
            x, y = to_check.pop()
            if (x, y) in visited or self.grid[y][x] != CellType.FLOOR:
                continue
                
            visited.add((x, y))
            floor_tiles.add((x, y))
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            
            # Check adjacent tiles
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    (nx, ny) not in visited):
                    to_check.append((nx, ny))
        
        # Create room if it's a reasonable size
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        if len(floor_tiles) >= 12:  # Minimum floor tiles for a room
            return Room(min_x, min_y, width, height)
        return None
    
    def _place_chests_in_room(self, room):
        """Place 0-2 chests in a room."""
        # 70% chance of having at least one chest
        if random.random() > 0.7:
            return
        
        # Determine number of chests (1-2)
        num_chests = 1 if random.random() < 0.7 else 2
        
        # Find suitable locations in the room (not too close to center or edges)
        candidates = []
        for y in range(room.y + 1, room.y + room.height - 1):
            for x in range(room.x + 1, room.x + room.width - 1):
                if (self.grid[y][x] == CellType.FLOOR and 
                    abs(x - room.center_x) > 1 and abs(y - room.center_y) > 1):
                    candidates.append((x, y))
        
        # Place chests
        for _ in range(min(num_chests, len(candidates))):
            if candidates:
                chest_pos = random.choice(candidates)
                candidates.remove(chest_pos)
                self.grid[chest_pos[1]][chest_pos[0]] = CellType.CHEST
                print(f"Placed chest at {chest_pos} in room ({room.x}, {room.y}) size {room.width}x{room.height}")
    
    def _place_hp_pickups(self):
        """Place HP pickups randomly throughout the dungeon."""
        floor_tiles = []
        
        # Find all floor tiles
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == CellType.FLOOR:
                    floor_tiles.append((x, y))
        
        # Place HP pickups (roughly 1 per 50 floor tiles)
        num_pickups = max(1, len(floor_tiles) // 50)
        
        for _ in range(num_pickups):
            if floor_tiles:
                pickup_pos = random.choice(floor_tiles)
                floor_tiles.remove(pickup_pos)
                self.grid[pickup_pos[1]][pickup_pos[0]] = CellType.HP_PICKUP
                print(f"Placed HP pickup at {pickup_pos}")

class Room:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center_x = x + width // 2
        self.center_y = y + height // 2
    
    def intersects(self, other: 'Room') -> bool:
        """Check if this room intersects with another room."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

class Minimap:
    def __init__(self, dungeon: Dungeon):
        self.dungeon = dungeon
        self.explored = set()
        self.visible = set()
        self.surface = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE))
        
    def update_explored(self, explored: set):
        self.explored = explored
    
    def update_visible(self, visible: set):
        self.visible = visible
    
    def render(self, screen: pygame.Surface, player_pos: Tuple[int, int], pos: Tuple[int, int] = None):
        """Render minimap at specified position or default location."""
        self.surface.fill(BLACK)
        
        # Calculate scale factor
        scale_x = MINIMAP_SIZE / self.dungeon.width
        scale_y = MINIMAP_SIZE / self.dungeon.height
        
        # Render explored areas
        for (x, y) in self.explored:
            mini_x = int(x * scale_x)
            mini_y = int(y * scale_y)
            
            cell_type = self.dungeon.get_cell(x, y)
            is_visible = (x, y) in self.visible
            
            if cell_type == CellType.FLOOR:
                base_colour = GREEN  # Changed to match main view
            elif cell_type == CellType.WALL:
                base_colour = GREY
            elif cell_type == CellType.WATER:
                base_colour = BLUE  # Water tiles in blue
            elif cell_type == CellType.STAIRCASE:
                base_colour = YELLOW
            elif cell_type == CellType.CHEST:
                base_colour = (139, 69, 19)  # Brown
            elif cell_type == CellType.HP_PICKUP:
                base_colour = (255, 100, 100)  # Light red
            else:
                base_colour = BROWN
            
            # Dim colour for non-visible explored areas
            if not is_visible:
                colour = tuple(max(0, int(c * 0.5)) for c in base_colour)
            else:
                colour = base_colour
            
            pygame.draw.rect(self.surface, colour, 
                           (mini_x, mini_y, max(1, int(scale_x)), max(1, int(scale_y))))
        
        # Render player position
        player_mini_x = int(player_pos[0] * scale_x)
        player_mini_y = int(player_pos[1] * scale_y)
        pygame.draw.circle(self.surface, RED, 
                         (player_mini_x, player_mini_y), 3)
        
        # Draw minimap border
        pygame.draw.rect(self.surface, WHITE, (0, 0, MINIMAP_SIZE, MINIMAP_SIZE), 2)
        
        # Blit to main screen at specified position or default
        if pos is None:
            pos = (WINDOW_WIDTH - MINIMAP_SIZE - 10, 10)
        screen.blit(self.surface, pos)

if __name__ == "__main__":
    game = Game()
    game.run() 