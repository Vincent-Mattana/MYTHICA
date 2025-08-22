"""
Sprite Management System for Mythica
Handles loading, caching, and rendering of pixel art sprites.
"""

import pygame
import os
import json
from typing import Dict, Optional, Tuple, List, Union
from enum import Enum
from pathlib import Path


class SpriteType(Enum):
    """Enumeration of different sprite categories."""
    TILES = "tiles"
    CHARACTERS = "characters"
    ENEMIES = "enemies"
    UI = "ui"
    EFFECTS = "effects"
    ITEMS = "items"  # For inventory items and equipment


class SpriteManager:
    """
    Centralized sprite loading and management system.
    Provides efficient sprite caching and rendering utilities.
    """
    
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = Path(assets_path)
        self.sprite_cache: Dict[str, pygame.Surface] = {}
        self.sprite_sheets: Dict[str, pygame.Surface] = {}
        self.sprite_mappings: Dict[str, Dict] = {}
        
        # Ensure assets directory exists
        self.assets_path.mkdir(exist_ok=True)
        for sprite_type in SpriteType:
            (self.assets_path / sprite_type.value).mkdir(exist_ok=True)
            
        # Load sprite mappings
        self._load_sprite_mappings()
    
    def load_sprite(self, sprite_name: str, sprite_type: SpriteType) -> Optional[pygame.Surface]:
        """
        Load a single sprite from the assets directory.
        
        Args:
            sprite_name: Name of the sprite file (without extension)
            sprite_type: Category of sprite (tiles, characters, etc.)
            
        Returns:
            pygame.Surface or None if loading fails
        """
        cache_key = f"{sprite_type.value}_{sprite_name}"
        
        # Return cached sprite if available
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]
        
        # Try to load sprite
        sprite_path = self.assets_path / sprite_type.value / f"{sprite_name}.png"
        
        if not sprite_path.exists():
            print(f"Warning: Sprite not found: {sprite_path}")
            return None
        
        try:
            sprite = pygame.image.load(str(sprite_path)).convert_alpha()
            self.sprite_cache[cache_key] = sprite
            return sprite
        except pygame.error as e:
            print(f"Error loading sprite {sprite_path}: {e}")
            return None
    
    def load_sprite_sheet(self, sheet_name: str, sprite_type: SpriteType, 
                         tile_size: Tuple[int, int]) -> Dict[str, pygame.Surface]:
        """
        Load a sprite sheet and split it into individual sprites.
        
        Args:
            sheet_name: Name of the sprite sheet file
            sprite_type: Category of sprites
            tile_size: Size of each sprite in the sheet (width, height)
            
        Returns:
            Dictionary mapping sprite names to surfaces
        """
        sheet_path = self.assets_path / sprite_type.value / f"{sheet_name}.png"
        
        if not sheet_path.exists():
            print(f"Warning: Sprite sheet not found: {sheet_path}")
            return {}
        
        try:
            sheet = pygame.image.load(str(sheet_path)).convert_alpha()
            sprites = {}
            
            sheet_width, sheet_height = sheet.get_size()
            tile_width, tile_height = tile_size
            
            for y in range(0, sheet_height, tile_height):
                for x in range(0, sheet_width, tile_width):
                    # Extract individual sprite
                    sprite = pygame.Surface(tile_size, pygame.SRCALPHA)
                    sprite.blit(sheet, (0, 0), (x, y, tile_width, tile_height))
                    
                    # Generate name based on position
                    sprite_name = f"{sheet_name}_{x//tile_width}_{y//tile_height}"
                    sprites[sprite_name] = sprite
                    
                    # Cache the sprite
                    cache_key = f"{sprite_type.value}_{sprite_name}"
                    self.sprite_cache[cache_key] = sprite
            
            return sprites
        except pygame.error as e:
            print(f"Error loading sprite sheet {sheet_path}: {e}")
            return {}
    
    def get_sprite(self, sprite_name: str, sprite_type: SpriteType) -> Optional[pygame.Surface]:
        """
        Retrieve a sprite, loading it if necessary.
        
        Args:
            sprite_name: Name of the sprite
            sprite_type: Category of sprite
            
        Returns:
            pygame.Surface or None if not found
        """
        return self.load_sprite(sprite_name, sprite_type)
    
    def create_fallback_sprite(self, size: Tuple[int, int], color: Tuple[int, int, int]) -> pygame.Surface:
        """
        Create a simple colored rectangle as a fallback when sprites are missing.
        
        Args:
            size: Size of the fallback sprite
            color: RGB color tuple
            
        Returns:
            pygame.Surface with the specified color
        """
        sprite = pygame.Surface(size, pygame.SRCALPHA)
        sprite.fill(color)
        return sprite
    
    def render_sprite(self, surface: pygame.Surface, sprite: pygame.Surface, 
                     position: Tuple[int, int], centered: bool = True):
        """
        Render a sprite to a surface with optional centering.
        
        Args:
            surface: Target surface to render to
            sprite: Sprite to render
            position: Position to render at
            centered: Whether to center the sprite at the position
        """
        if sprite is None:
            return
        
        if centered:
            # Center the sprite at the given position
            sprite_rect = sprite.get_rect()
            sprite_rect.center = position
            surface.blit(sprite, sprite_rect)
        else:
            # Render at exact position
            surface.blit(sprite, position)
    
    def scale_sprite(self, sprite: pygame.Surface, scale_factor: float) -> pygame.Surface:
        """
        Scale a sprite by the given factor while maintaining pixel art appearance.
        
        Args:
            sprite: Sprite to scale
            scale_factor: Scale multiplier
            
        Returns:
            Scaled pygame.Surface
        """
        if sprite is None:
            return None
        
        original_size = sprite.get_size()
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        
        # Use NEAREST filtering to maintain crisp pixel art
        return pygame.transform.scale(sprite, new_size)
    
    def clear_cache(self):
        """Clear the sprite cache to free memory."""
        self.sprite_cache.clear()
    
    def preload_common_sprites(self):
        """Preload commonly used sprites for better performance."""
        if not self.sprite_mappings:
            print("Warning: No sprite mappings loaded, skipping preload")
            return
            
        # Define common sprites to preload
        common_sprites = [
            # Tiles
            ("floor_stone", SpriteType.TILES),
            ("floor_wood", SpriteType.TILES),
            ("wall_brick", SpriteType.TILES),
            ("wall_stone", SpriteType.TILES),
            ("door_wooden", SpriteType.TILES),
            ("door_metal", SpriteType.TILES),
            ("stairs_down", SpriteType.TILES),
            ("stairs_up", SpriteType.TILES),
            ("chest_closed", SpriteType.TILES),
            ("chest_open", SpriteType.TILES),
            ("health_potion", SpriteType.TILES),
            
            # Characters and their variants
            ("warrior", SpriteType.CHARACTERS),
            ("rogue", SpriteType.CHARACTERS),
            ("mage", SpriteType.CHARACTERS),
            ("ranger", SpriteType.CHARACTERS),
            ("cleric", SpriteType.CHARACTERS),
            
            # Enemies
            ("rat", SpriteType.ENEMIES),
            ("giant_rat", SpriteType.ENEMIES),
            ("goblin", SpriteType.ENEMIES),
            ("goblin_archer", SpriteType.ENEMIES),
            ("skeleton", SpriteType.ENEMIES),
            ("skeleton_warrior", SpriteType.ENEMIES),
            ("spider", SpriteType.ENEMIES),
            ("giant_spider", SpriteType.ENEMIES),
            ("orc", SpriteType.ENEMIES),
            ("orc_warrior", SpriteType.ENEMIES),
            ("troll", SpriteType.ENEMIES),
            ("troll_berserker", SpriteType.ENEMIES),
            
            # Items
            ("sword", SpriteType.ITEMS),
            ("dagger", SpriteType.ITEMS),
            ("staff", SpriteType.ITEMS),
            ("bow", SpriteType.ITEMS),
            ("mace", SpriteType.ITEMS),
            ("armor_light", SpriteType.ITEMS),
            ("armor_medium", SpriteType.ITEMS),
            ("armor_heavy", SpriteType.ITEMS),
            ("ring", SpriteType.ITEMS),
            ("amulet", SpriteType.ITEMS),
            ("potion_health", SpriteType.ITEMS),
            ("potion_mana", SpriteType.ITEMS),
            ("scroll", SpriteType.ITEMS),
            ("gold", SpriteType.ITEMS),
            
            # UI Elements
            ("health_bar", SpriteType.UI),
            ("mana_bar", SpriteType.UI),
            ("inventory_slot", SpriteType.UI),
            ("button_normal", SpriteType.UI),
            ("button_hover", SpriteType.UI),
            ("button_pressed", SpriteType.UI),
        ]
        
        # Preload base sprites
        for sprite_name, sprite_type in common_sprites:
            sprite = self.load_oryx_sprite(sprite_name, sprite_type)
            if sprite:
                cache_key = f"{sprite_type.value}_{sprite_name}"
                self.sprite_cache[cache_key] = sprite
        
        # Preload character variants
        character_variants = {
            "warrior": ["armored", "elite"],
            "rogue": ["hooded", "assassin"],
            "mage": ["wizard", "archmage"],
            "ranger": ["hunter", "marksman"],
            "cleric": ["priest", "bishop"]
        }
        
        for char_name, variants in character_variants.items():
            for variant in variants:
                sprite = self.get_sprite_variant(char_name, SpriteType.CHARACTERS, variant)
                if sprite:
                    cache_key = f"characters_{char_name}_{variant}"
                    self.sprite_cache[cache_key] = sprite
        
        # Preload effect animations
        effect_animations = [
            "explosion",
            "magic_cast",
            "healing",
            "poison"
        ]
        
        for effect_name in effect_animations:
            frames = self.get_animation_frames(effect_name, SpriteType.EFFECTS)
            for i, frame in enumerate(frames):
                cache_key = f"effects_{effect_name}_{i}"
                self.sprite_cache[cache_key] = frame


    def _load_sprite_mappings(self):
        """Load sprite mappings from configuration file."""
        mapping_path = self.assets_path / "sprite_mappings.json"
        if not mapping_path.exists():
            print(f"Warning: Sprite mappings file not found: {mapping_path}")
            return
        
        try:
            with open(mapping_path) as f:
                self.sprite_mappings = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading sprite mappings: {e}")
        except IOError as e:
            print(f"Error reading sprite mappings file: {e}")

    def load_oryx_sprite(self, sprite_name: str, sprite_type: SpriteType) -> Optional[pygame.Surface]:
        """
        Load a sprite from the Oryx Classic Roguelike set.
        
        Args:
            sprite_name: Name of the sprite in the mapping configuration
            sprite_type: Category of sprite
            
        Returns:
            pygame.Surface or None if loading fails
        """
        if not self.sprite_mappings:
            return None
            
        sprite_type_str = sprite_type.value
        if sprite_type_str not in self.sprite_mappings["sprite_mappings"]:
            return None
            
        mappings = self.sprite_mappings["sprite_mappings"][sprite_type_str]
        if sprite_name not in mappings:
            return None
            
        oryx_name = mappings[sprite_name]
        if isinstance(oryx_name, dict):  # Handle character variants
            oryx_name = oryx_name["base"]  # Use base sprite by default
        elif isinstance(oryx_name, list):  # Handle animation frames
            oryx_name = oryx_name[0]  # Use first frame by default
            
        # Load from the Oryx assets directory
        oryx_path = self.assets_path / "Classic Roguelike" / "classic_roguelike_sliced" / f"{oryx_name}.png"
        
        try:
            sprite = pygame.image.load(str(oryx_path)).convert_alpha()
            # Scale to match the game's tile size if needed
            if "tile_size" in self.sprite_mappings:
                current_size = sprite.get_size()
                target_size = (self.sprite_mappings["tile_size"], self.sprite_mappings["tile_size"])
                if current_size != target_size:
                    sprite = pygame.transform.scale(sprite, target_size)
            return sprite
        except pygame.error as e:
            print(f"Error loading Oryx sprite {oryx_path}: {e}")
            return None

    def get_sprite_variant(self, sprite_name: str, sprite_type: SpriteType, variant: str) -> Optional[pygame.Surface]:
        """
        Get a specific variant of a sprite (e.g., different character appearances).
        
        Args:
            sprite_name: Base name of the sprite
            sprite_type: Category of sprite
            variant: Name of the variant to load
            
        Returns:
            pygame.Surface or None if variant not found
        """
        if not self.sprite_mappings:
            return None
            
        sprite_type_str = sprite_type.value
        if sprite_type_str not in self.sprite_mappings["sprite_mappings"]:
            return None
            
        mappings = self.sprite_mappings["sprite_mappings"][sprite_type_str]
        if sprite_name not in mappings or not isinstance(mappings[sprite_name], dict):
            return None
            
        sprite_data = mappings[sprite_name]
        if "variants" not in sprite_data or variant not in sprite_data["variants"]:
            return None
            
        oryx_name = sprite_data["variants"][variant]
        oryx_path = self.assets_path / "Classic Roguelike" / "classic_roguelike_sliced" / f"{oryx_name}.png"
        
        try:
            sprite = pygame.image.load(str(oryx_path)).convert_alpha()
            if "tile_size" in self.sprite_mappings:
                current_size = sprite.get_size()
                target_size = (self.sprite_mappings["tile_size"], self.sprite_mappings["tile_size"])
                if current_size != target_size:
                    sprite = pygame.transform.scale(sprite, target_size)
            return sprite
        except pygame.error as e:
            print(f"Error loading Oryx sprite variant {oryx_path}: {e}")
            return None

    def get_animation_frames(self, sprite_name: str, sprite_type: SpriteType) -> List[pygame.Surface]:
        """
        Get all animation frames for a sprite.
        
        Args:
            sprite_name: Name of the animated sprite
            sprite_type: Category of sprite
            
        Returns:
            List of pygame.Surface objects for each animation frame
        """
        if not self.sprite_mappings:
            return []
            
        sprite_type_str = sprite_type.value
        if sprite_type_str not in self.sprite_mappings["sprite_mappings"]:
            return []
            
        mappings = self.sprite_mappings["sprite_mappings"][sprite_type_str]
        if sprite_name not in mappings or not isinstance(mappings[sprite_name], list):
            return []
            
        frames = []
        for frame_name in mappings[sprite_name]:
            frame_path = self.assets_path / "Classic Roguelike" / "classic_roguelike_sliced" / f"{frame_name}.png"
            try:
                frame = pygame.image.load(str(frame_path)).convert_alpha()
                if "tile_size" in self.sprite_mappings:
                    current_size = frame.get_size()
                    target_size = (self.sprite_mappings["tile_size"], self.sprite_mappings["tile_size"])
                    if current_size != target_size:
                        frame = pygame.transform.scale(frame, target_size)
                frames.append(frame)
            except pygame.error as e:
                print(f"Error loading animation frame {frame_path}: {e}")
                
        return frames


# Global sprite manager instance
sprite_manager = SpriteManager() 