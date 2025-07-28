#!/usr/bin/env python3
"""
Enemy System for Mythica Dungeon Crawler
Handles enemy types, stats, AI, and combat mechanics.
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum
import random
import math
from .character_system import StatType

class EnemyType(Enum):
    GOBLIN = "Goblin"
    ORC = "Orc"
    SKELETON = "Skeleton"
    RAT = "Giant Rat"
    SPIDER = "Spider"
    TROLL = "Troll"

class EnemyBehavior(Enum):
    PASSIVE = "Passive"      # Doesn't move unless attacked
    PATROL = "Patrol"        # Moves randomly
    AGGRESSIVE = "Aggressive" # Moves toward player when in sight
    GUARD = "Guard"          # Stands still but attacks when player is adjacent

class Enemy:
    def __init__(self, enemy_type: EnemyType, x: int, y: int):
        self.enemy_type = enemy_type
        self.x = x
        self.y = y
        self.is_alive = True
        
        # Initialize stats based on enemy type
        self._initialize_stats()
        
        # Combat state
        self.max_hp = self.hp
        self.last_damage_time = 0
        
        # AI state
        self.behavior = self._get_behavior()
        self.patrol_target = None
        self.last_move_time = 0
        self.move_cooldown = self._get_move_cooldown()
        
        # Visual state
        self.damage_flash = 0  # For damage visual feedback
    
    def _initialize_stats(self):
        """Initialize enemy stats based on type."""
        stats = {
            EnemyType.RAT: {
                'hp': 8, 'strength': 6, 'dexterity': 12, 'constitution': 8,
                'perception': 10, 'luck': 8, 'exp_value': 5
            },
            EnemyType.GOBLIN: {
                'hp': 15, 'strength': 10, 'dexterity': 14, 'constitution': 10,
                'perception': 12, 'luck': 10, 'exp_value': 15
            },
            EnemyType.SKELETON: {
                'hp': 20, 'strength': 12, 'dexterity': 8, 'constitution': 12,
                'perception': 8, 'luck': 5, 'exp_value': 20
            },
            EnemyType.SPIDER: {
                'hp': 12, 'strength': 8, 'dexterity': 16, 'constitution': 10,
                'perception': 14, 'luck': 10, 'exp_value': 18
            },
            EnemyType.ORC: {
                'hp': 30, 'strength': 16, 'dexterity': 8, 'constitution': 16,
                'perception': 10, 'luck': 8, 'exp_value': 35
            },
            EnemyType.TROLL: {
                'hp': 50, 'strength': 20, 'dexterity': 6, 'constitution': 20,
                'perception': 8, 'luck': 6, 'exp_value': 60
            }
        }
        
        enemy_stats = stats[self.enemy_type]
        self.hp = enemy_stats['hp']
        self.strength = enemy_stats['strength']
        self.dexterity = enemy_stats['dexterity']
        self.constitution = enemy_stats['constitution']
        self.perception = enemy_stats['perception']
        self.luck = enemy_stats['luck']
        self.exp_value = enemy_stats['exp_value']
    
    def _get_behavior(self) -> EnemyBehavior:
        """Get behavior pattern based on enemy type."""
        behaviors = {
            EnemyType.RAT: EnemyBehavior.PATROL,
            EnemyType.GOBLIN: EnemyBehavior.AGGRESSIVE,
            EnemyType.SKELETON: EnemyBehavior.GUARD,
            EnemyType.SPIDER: EnemyBehavior.AGGRESSIVE,
            EnemyType.ORC: EnemyBehavior.AGGRESSIVE,
            EnemyType.TROLL: EnemyBehavior.GUARD
        }
        return behaviors[self.enemy_type]
    
    def _get_move_cooldown(self) -> float:
        """Get movement speed based on dexterity."""
        base_cooldown = 1.0  # 1 second base
        dex_modifier = max(0.1, 1.0 - (self.dexterity - 10) * 0.05)
        return base_cooldown * dex_modifier
    
    def get_position(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    def move_to(self, x: int, y: int):
        """Move enemy to new position."""
        self.x = x
        self.y = y
    
    def take_damage(self, damage: int) -> bool:
        """Apply damage to enemy. Returns True if enemy dies."""
        self.hp = max(0, self.hp - damage)
        self.damage_flash = 0.5  # Flash for half a second
        
        if self.hp <= 0:
            self.is_alive = False
            return True
        return False
    
    def get_hp_percentage(self) -> float:
        """Get HP as percentage (0.0 to 1.0)."""
        return self.hp / self.max_hp if self.max_hp > 0 else 0.0
    
    def get_attack_damage(self) -> int:
        """Calculate attack damage based on strength."""
        base_damage = self.strength // 2
        variance = max(1, base_damage // 3)
        return random.randint(base_damage - variance, base_damage + variance)
    
    def can_see_player(self, player_x: int, player_y: int, max_distance: int = 8) -> bool:
        """Check if enemy can see the player."""
        distance = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        sight_range = max(3, self.perception // 2)
        return distance <= min(sight_range, max_distance)
    
    def get_distance_to_player(self, player_x: int, player_y: int) -> float:
        """Get distance to player."""
        return math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
    
    def update_ai(self, current_time: float, player_x: int, player_y: int, dungeon) -> Optional[Tuple[int, int]]:
        """Update enemy AI and return desired move position if any."""
        if not self.is_alive:
            return None
        
        # Update visual effects
        if self.damage_flash > 0:
            self.damage_flash = max(0, self.damage_flash - 0.016)  # Assuming 60 FPS
        
        # Check movement cooldown
        if current_time - self.last_move_time < self.move_cooldown:
            return None
        
        new_x, new_y = self.x, self.y
        
        if self.behavior == EnemyBehavior.PASSIVE:
            # Don't move
            pass
        
        elif self.behavior == EnemyBehavior.PATROL:
            # Random movement
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            if random.random() < 0.3:  # 30% chance to move
                dx, dy = random.choice(directions)
                new_x, new_y = self.x + dx, self.y + dy
        
        elif self.behavior == EnemyBehavior.AGGRESSIVE:
            # Move toward player if can see them
            if self.can_see_player(player_x, player_y):
                # Get distance to player
                distance = self.get_distance_to_player(player_x, player_y)
                
                # Only move if not already adjacent (distance > 1)
                if distance > 1:
                    # Simple pathfinding - move toward player
                    if player_x > self.x:
                        new_x = self.x + 1
                    elif player_x < self.x:
                        new_x = self.x - 1
                    elif player_y > self.y:
                        new_y = self.y + 1
                    elif player_y < self.y:
                        new_y = self.y - 1
        
        elif self.behavior == EnemyBehavior.GUARD:
            # Only move if player is close but not adjacent
            distance = self.get_distance_to_player(player_x, player_y)
            if 1 < distance <= 2:
                # Move toward player
                if player_x > self.x:
                    new_x = self.x + 1
                elif player_x < self.x:
                    new_x = self.x - 1
                elif player_y > self.y:
                    new_y = self.y + 1
                elif player_y < self.y:
                    new_y = self.y - 1
        
        # Validate movement
        if (new_x != self.x or new_y != self.y):
            if dungeon.can_move_to(new_x, new_y):
                self.last_move_time = current_time
                return (new_x, new_y)
        
        return None

class EnemyManager:
    def __init__(self):
        self.enemies: List[Enemy] = []
        self.enemy_positions: Dict[Tuple[int, int], Enemy] = {}
    
    def add_enemy(self, enemy: Enemy):
        """Add an enemy to the manager."""
        self.enemies.append(enemy)
        self.enemy_positions[enemy.get_position()] = enemy
    
    def remove_enemy(self, enemy: Enemy):
        """Remove an enemy from the manager."""
        if enemy in self.enemies:
            self.enemies.remove(enemy)
            pos = enemy.get_position()
            if pos in self.enemy_positions:
                del self.enemy_positions[pos]
    
    def get_enemy_at(self, x: int, y: int) -> Optional[Enemy]:
        """Get enemy at specific position."""
        return self.enemy_positions.get((x, y))
    
    def move_enemy(self, enemy: Enemy, new_x: int, new_y: int, player_x: int, player_y: int) -> bool:
        """Move an enemy to a new position."""
        old_pos = enemy.get_position()
        new_pos = (new_x, new_y)
        
        # Check if position is occupied by another enemy
        if new_pos in self.enemy_positions:
            return False
        
        # Check if position is occupied by the player
        if new_x == player_x and new_y == player_y:
            return False
        
        # Update positions
        if old_pos in self.enemy_positions:
            del self.enemy_positions[old_pos]
        
        enemy.move_to(new_x, new_y)
        self.enemy_positions[new_pos] = enemy
        return True
    
    def update_all_enemies(self, current_time: float, player_x: int, player_y: int, dungeon):
        """Update AI for all enemies."""
        enemies_to_remove = []
        
        for enemy in self.enemies[:]:  # Copy list to avoid modification during iteration
            if not enemy.is_alive:
                enemies_to_remove.append(enemy)
                continue
            
            # Update AI
            desired_move = enemy.update_ai(current_time, player_x, player_y, dungeon)
            if desired_move:
                new_x, new_y = desired_move
                # Pass player position to check for collisions
                self.move_enemy(enemy, new_x, new_y, player_x, player_y)
        
        # Remove dead enemies
        for enemy in enemies_to_remove:
            self.remove_enemy(enemy)
    
    def get_enemies_in_range(self, x: int, y: int, radius: int) -> List[Enemy]:
        """Get all enemies within a certain radius."""
        enemies_in_range = []
        for enemy in self.enemies:
            if enemy.is_alive:
                distance = math.sqrt((enemy.x - x)**2 + (enemy.y - y)**2)
                if distance <= radius:
                    enemies_in_range.append(enemy)
        return enemies_in_range
    
    def spawn_enemies_in_dungeon(self, dungeon, num_enemies: int = 15, player_start_pos: tuple = None, dungeon_level: int = 1):
        """Spawn enemies randomly throughout the dungeon with level-based difficulty."""
        spawn_attempts = 0
        enemies_spawned = 0
        max_attempts = num_enemies * 10
        
        # Use dungeon start position if player position not provided
        if player_start_pos is None:
            player_start_pos = dungeon.start_pos
        
        while enemies_spawned < num_enemies and spawn_attempts < max_attempts:
            spawn_attempts += 1
            
            # Random position
            x = random.randint(1, dungeon.width - 2)
            y = random.randint(1, dungeon.height - 2)
            
            # Check if position is valid (floor tile, not start position, not occupied, not special tiles)
            cell_type = dungeon.get_cell(x, y)
            is_special_tile = hasattr(cell_type, 'value') and cell_type.value in [3, 4, 5]  # STAIRCASE, CHEST, HP_PICKUP
            
            if (cell_type.value == 1 and  # Only spawn on FLOOR tiles
                (x, y) != player_start_pos and
                (x, y) not in self.enemy_positions and
                not is_special_tile):  # Avoid stairs, chests, and pickups
                
                # Choose enemy type based on depth/difficulty
                enemy_type = self._choose_enemy_type_by_level(dungeon_level)
                enemy = Enemy(enemy_type, x, y)
                
                # Scale enemy stats based on dungeon level
                self._scale_enemy_for_level(enemy, dungeon_level)
                
                self.add_enemy(enemy)
                enemies_spawned += 1
    
    def _choose_enemy_type_by_level(self, dungeon_level: int) -> EnemyType:
        """Choose enemy type with level-based difficulty scaling."""
        # Base weights - more dangerous enemies become more common on deeper levels
        if dungeon_level == 1:
            weights = {
                EnemyType.RAT: 40,
                EnemyType.GOBLIN: 30,
                EnemyType.SPIDER: 20,
                EnemyType.SKELETON: 10,
                EnemyType.ORC: 0,
                EnemyType.TROLL: 0
            }
        elif dungeon_level == 2:
            weights = {
                EnemyType.RAT: 25,
                EnemyType.GOBLIN: 35,
                EnemyType.SPIDER: 25,
                EnemyType.SKELETON: 15,
                EnemyType.ORC: 0,
                EnemyType.TROLL: 0
            }
        elif dungeon_level == 3:
            weights = {
                EnemyType.RAT: 15,
                EnemyType.GOBLIN: 30,
                EnemyType.SPIDER: 25,
                EnemyType.SKELETON: 20,
                EnemyType.ORC: 10,
                EnemyType.TROLL: 0
            }
        elif dungeon_level == 4:
            weights = {
                EnemyType.RAT: 10,
                EnemyType.GOBLIN: 25,
                EnemyType.SPIDER: 20,
                EnemyType.SKELETON: 25,
                EnemyType.ORC: 15,
                EnemyType.TROLL: 5
            }
        else:  # Level 5+
            weights = {
                EnemyType.RAT: 5,
                EnemyType.GOBLIN: 20,
                EnemyType.SPIDER: 15,
                EnemyType.SKELETON: 25,
                EnemyType.ORC: 25,
                EnemyType.TROLL: 10
            }
        
        enemy_types = list(weights.keys())
        enemy_weights = list(weights.values())
        
        return random.choices(enemy_types, weights=enemy_weights)[0]
    
    def _scale_enemy_for_level(self, enemy: Enemy, dungeon_level: int):
        """Scale enemy stats based on dungeon level for increased difficulty."""
        if dungeon_level <= 1:
            return  # No scaling for level 1
        
        # Calculate scaling factor: 15% increase per level past 1
        scale_factor = 1.0 + (dungeon_level - 1) * 0.15
        
        # Scale HP
        enemy.hp = int(enemy.hp * scale_factor)
        enemy.max_hp = enemy.hp
        
        # Scale stats
        enemy.strength = int(enemy.strength * scale_factor)
        enemy.dexterity = int(enemy.dexterity * scale_factor)
        enemy.constitution = int(enemy.constitution * scale_factor)
        enemy.perception = int(enemy.perception * scale_factor)
        enemy.luck = int(enemy.luck * scale_factor)
        
        # Scale experience value
        enemy.exp_value = int(enemy.exp_value * scale_factor)
    
    def _choose_enemy_type(self) -> EnemyType:
        """Choose a random enemy type with weighted probability (legacy method)."""
        return self._choose_enemy_type_by_level(1)  # Default to level 1 weights
    
    def get_living_enemies(self) -> List[Enemy]:
        """Get all living enemies."""
        return [enemy for enemy in self.enemies if enemy.is_alive]

class HealthBar:
    """Utility class for rendering health bars."""
    
    @staticmethod
    def draw_health_bar(surface, x: int, y: int, width: int, height: int, 
                       current_hp: int, max_hp: int, show_text: bool = True, is_enemy: bool = False):
        """Draw a health bar at the specified position."""
        import pygame
        
        # Calculate HP percentage
        hp_percentage = current_hp / max_hp if max_hp > 0 else 0
        
        if is_enemy:
            # Enemy health bars: High contrast red with black border for visibility
            background_color = (0, 0, 0)  # Pure black background
            border_color = (0, 0, 0)  # Black border for visibility against light backgrounds
            hp_color = (255, 0, 0)  # Bright pure red, always the same regardless of HP
        else:
            # Player health bars: Traditional color scheme
            background_color = (64, 64, 64)
            border_color = (255, 255, 255)
            low_hp_color = (200, 50, 50)
            medium_hp_color = (200, 200, 50)
            high_hp_color = (50, 200, 50)
            
            # Choose color based on HP percentage
            if hp_percentage > 0.6:
                hp_color = high_hp_color
            elif hp_percentage > 0.3:
                hp_color = medium_hp_color
            else:
                hp_color = low_hp_color
        
        if is_enemy:
            # Special rendering for enemy health bars - maximum visibility
            # Draw white outline first for visibility against any background
            pygame.draw.rect(surface, (255, 255, 255), (x-1, y-1, width+2, height+2))
            # Draw black background
            pygame.draw.rect(surface, background_color, (x, y, width, height))
            # Draw bright red HP fill
            fill_width = int(width * hp_percentage)
            if fill_width > 0:
                pygame.draw.rect(surface, hp_color, (x, y, fill_width, height))
            # Draw black border
            pygame.draw.rect(surface, border_color, (x, y, width, height), 1)
        else:
            # Normal rendering for player health bars
            # Draw background
            pygame.draw.rect(surface, background_color, (x, y, width, height))
            # Draw HP fill
            fill_width = int(width * hp_percentage)
            if fill_width > 0:
                pygame.draw.rect(surface, hp_color, (x, y, fill_width, height))
            # Draw border
            pygame.draw.rect(surface, border_color, (x, y, width, height), 2)
        
        # Draw text if requested
        if show_text:
            font = pygame.font.Font(None, 24)
            hp_text = f"{current_hp}/{max_hp}"
            text_surface = font.render(hp_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
            surface.blit(text_surface, text_rect) 