import pygame
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import warnings
import os

# Suppress libpng warnings about sRGB profiles
warnings.filterwarnings("ignore", ".*iCCP.*")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import json

# Initialize pygame display for image loading
pygame.init()
if not pygame.display.get_init():
    pygame.display.set_mode((1, 1), pygame.NOFRAME)

class SpriteSystem:
    """A reusable sprite management system for games"""
    
    def __init__(self, tile_size: Tuple[int, int] = (16, 24)):
        self.tile_size = tile_size
        self.sprites: Dict[str, pygame.Surface] = {}
        self.spritesheets: Dict[str, pygame.Surface] = {}
        self.tint_cache: Dict[str, pygame.Surface] = {}
        
        # Sprite overlap prevention
        self.sprite_positions: Dict[str, Tuple[int, int, int, int]] = {}  # name -> (x, y, width, height)
        self.overlap_check_enabled = True
        
    def load_spritesheet(self, name: str, file_path: Path) -> bool:
        """Load a spritesheet from file"""
        try:
            # Ensure pygame is initialized
            if not pygame.get_init():
                pygame.init()
            
            # Load image without convert_alpha to avoid display mode requirement
            image = pygame.image.load(str(file_path))
            self.spritesheets[name] = image
            return True
        except pygame.error as e:
            print(f"Error loading spritesheet {name} from {file_path}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error loading spritesheet {name} from {file_path}: {e}")
            return False
    
    def extract_sprite(self, spritesheet_name: str, x: int, y: int, 
                      sprite_name: str, width: Optional[int] = None, 
                      height: Optional[int] = None) -> bool:
        """Extract a single sprite from a spritesheet"""
        if spritesheet_name not in self.spritesheets:
            return False
            
        width = width or self.tile_size[0]
        height = height or self.tile_size[1]
        
        try:
            sprite = pygame.Surface((width, height), pygame.SRCALPHA)
            sprite.blit(self.spritesheets[spritesheet_name], (0, 0), 
                       (x, y, width, height))
            self.sprites[sprite_name] = sprite
            return True
        except Exception:
            return False
    
    def load_sprites_from_csv(self, csv_file: Path, spritesheet_name: str) -> int:
        """Load sprites from a CSV file with sprite definitions"""
        loaded_count = 0
        
        try:
            with open(csv_file, 'r') as file:
                lines = file.readlines()
                
            # Skip header
            for line in lines[1:]:
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    file_name, x, y, index, name = parts[:5]
                    
                    # Only load if it's the correct spritesheet and not empty
                    if file_name == spritesheet_name and name != '[EMPTY]':
                        # Map CSV file names to loaded spritesheet names
                        spritesheet_mapping = {
                            'Terrain.png': 'terrain',
                            'Terrain_Objects.png': 'terrain_objects',
                            'Interface.png': 'interface',
                            'Avatar.png': 'avatar',
                            'Avatar_Equipment.png': 'avatar_equipment',
                            'Monsters.png': 'monsters'
                        }
                        
                        loaded_spritesheet_name = spritesheet_mapping.get(spritesheet_name, spritesheet_name)
                        
                        if self.extract_sprite(loaded_spritesheet_name, int(x), int(y), name):
                            loaded_count += 1
                            
        except Exception as e:
            # Silently handle CSV loading errors - fallback sprites will be used
            pass
            
        return loaded_count
    
    def tint_sprite(self, sprite_name: str, tint_color: Tuple[float, float, float], 
                   cache_key: Optional[str] = None) -> Optional[pygame.Surface]:
        """Apply a tint to a sprite using proper color multiplication"""
        if sprite_name not in self.sprites:
            return None
            
        # Use cache key if provided, otherwise create one
        if cache_key is None:
            cache_key = f"{sprite_name}_{tint_color[0]:.2f}_{tint_color[1]:.2f}_{tint_color[2]:.2f}"
            
        # Check cache first
        if cache_key in self.tint_cache:
            return self.tint_cache[cache_key]
        
        # Convert tint_color from 0-1 range to 0-255 range
        r = int(tint_color[0] * 255)
        g = int(tint_color[1] * 255)
        b = int(tint_color[2] * 255)
        
        # Create a copy of the sprite
        tinted = self.sprites[sprite_name].copy()
        
        # Apply tint only to non-transparent pixels using multiply blend
        tinted.fill((r, g, b, 255), special_flags=pygame.BLEND_MULT)
        
        # Cache the result
        self.tint_cache[cache_key] = tinted
        return tinted
    
    def get_sprite(self, sprite_name: str, tint_color: Optional[Tuple[float, float, float]] = None) -> Optional[pygame.Surface]:
        """Get a sprite, optionally tinted"""
        if tint_color is None:
            return self.sprites.get(sprite_name)
        else:
            return self.tint_sprite(sprite_name, tint_color)
    
    def draw_sprite(self, surface: pygame.Surface, sprite_name: str, 
                   x: int, y: int, tint_color: Optional[Tuple[float, float, float]] = None,
                   scale: int = 1, prevent_overlap: bool = True) -> bool:
        """Draw a sprite to a surface with optional overlap prevention"""
        sprite = self.get_sprite(sprite_name, tint_color)
        if sprite is None:
            # Draw bright magenta square for missing sprites
            print(f"WARNING: Missing sprite '{sprite_name}' - drawing magenta placeholder")
            tile_width = int(self.tile_size[0] * scale)
            tile_height = int(self.tile_size[1] * scale)
            magenta_rect = pygame.Rect(x, y, tile_width, tile_height)
            pygame.draw.rect(surface, (255, 0, 255), magenta_rect)  # Bright magenta
            return False
            
        if scale != 1:
            sprite = pygame.transform.scale(sprite, 
                (sprite.get_width() * scale, sprite.get_height() * scale))
        
        # Check for overlaps if prevention is enabled
        if prevent_overlap and self.overlap_check_enabled:
            width, height = sprite.get_size()
            overlapping = self.check_overlap(x, y, width, height, sprite_name)
            
            if overlapping:
                # Try to find a non-overlapping position
                new_position = self.find_non_overlapping_position(
                    width, height, 
                    screen_width=surface.get_width(),
                    screen_height=surface.get_height()
                )
                
                if new_position:
                    x, y = new_position
                else:
                    # If no position found, draw anyway but log warning
                    print(f"Warning: Sprite '{sprite_name}' overlaps with {overlapping}")
        
        # Register sprite position for future overlap checks
        if prevent_overlap:
            width, height = sprite.get_size()
            self.register_sprite_position(sprite_name, x, y, width, height)
            
        surface.blit(sprite, (x, y))
        return True
    
    def get_sprite_size(self, sprite_name: str) -> Tuple[int, int]:
        """Get the size of a sprite"""
        if sprite_name in self.sprites:
            return self.sprites[sprite_name].get_size()
        return (0, 0)
    
    def list_sprites(self) -> List[str]:
        """Get a list of all loaded sprite names"""
        return list(self.sprites.keys())
    
    def clear_cache(self):
        """Clear the tint cache to free memory"""
        self.tint_cache.clear()
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        sprite_count = len(self.sprites)
        cache_count = len(self.tint_cache)
        
        # Estimate memory usage (rough calculation)
        sprite_memory = sum(sprite.get_width() * sprite.get_height() * 4 
                           for sprite in self.sprites.values())
        cache_memory = sum(sprite.get_width() * sprite.get_height() * 4 
                          for sprite in self.tint_cache.values())
        
        return {
            'sprites': sprite_count,
            'cached_tints': cache_count,
            'sprite_memory_bytes': sprite_memory,
            'cache_memory_bytes': cache_memory,
            'total_memory_bytes': sprite_memory + cache_memory
        }
    
    # Sprite overlap prevention methods
    def set_overlap_check(self, enabled: bool):
        """Enable or disable sprite overlap checking."""
        self.overlap_check_enabled = enabled
    
    def register_sprite_position(self, sprite_name: str, x: int, y: int, width: int, height: int):
        """Register a sprite's position for overlap checking."""
        self.sprite_positions[sprite_name] = (x, y, width, height)
    
    def unregister_sprite_position(self, sprite_name: str):
        """Remove a sprite's position from overlap checking."""
        if sprite_name in self.sprite_positions:
            del self.sprite_positions[sprite_name]
    
    def check_overlap(self, x: int, y: int, width: int, height: int, 
                     exclude_sprite: Optional[str] = None) -> List[str]:
        """Check if a position overlaps with any registered sprites."""
        if not self.overlap_check_enabled:
            return []
        
        overlapping_sprites = []
        
        for sprite_name, (sx, sy, sw, sh) in self.sprite_positions.items():
            if exclude_sprite and sprite_name == exclude_sprite:
                continue
            
            # Check for rectangle overlap
            if (x < sx + sw and x + width > sx and 
                y < sy + sh and y + height > sy):
                overlapping_sprites.append(sprite_name)
        
        return overlapping_sprites
    
    def find_non_overlapping_position(self, width: int, height: int, 
                                    max_attempts: int = 100,
                                    screen_width: int = 1024, 
                                    screen_height: int = 768) -> Optional[Tuple[int, int]]:
        """Find a position that doesn't overlap with existing sprites."""
        if not self.overlap_check_enabled:
            return (0, 0)
        
        import random
        
        for _ in range(max_attempts):
            x = random.randint(0, screen_width - width)
            y = random.randint(0, screen_height - height)
            
            if not self.check_overlap(x, y, width, height):
                return (x, y)
        
        return None  # No non-overlapping position found
    
    def get_sprite_bounds(self, sprite_name: str) -> Optional[Tuple[int, int, int, int]]:
        """Get the bounds of a registered sprite."""
        return self.sprite_positions.get(sprite_name)
    
    def clear_sprite_positions(self):
        """Clear all registered sprite positions."""
        self.sprite_positions.clear()
    
    def get_overlapping_sprites(self, x: int, y: int, width: int, height: int) -> List[str]:
        """Get all sprites that overlap with the given rectangle."""
        return self.check_overlap(x, y, width, height)
    
    def move_sprite_to_non_overlapping_position(self, sprite_name: str, 
                                             max_attempts: int = 100,
                                             screen_width: int = 1024,
                                             screen_height: int = 768) -> bool:
        """Move a sprite to a non-overlapping position."""
        if sprite_name not in self.sprite_positions:
            return False
        
        current_x, current_y, width, height = self.sprite_positions[sprite_name]
        
        # Check if current position is already non-overlapping
        if not self.check_overlap(current_x, current_y, width, height, sprite_name):
            return True
        
        # Find new position
        new_position = self.find_non_overlapping_position(
            width, height, max_attempts, screen_width, screen_height
        )
        
        if new_position:
            new_x, new_y = new_position
            self.sprite_positions[sprite_name] = (new_x, new_y, width, height)
            return True
        
        return False


class SpriteRenderer:
    """A renderer for drawing sprites in scenes"""
    
    def __init__(self, sprite_system: SpriteSystem):
        self.sprite_system = sprite_system
        self.scene_data: List[List[str]] = []
        self.scene_width = 0
        self.scene_height = 0
        
    def set_scene(self, scene_data: List[List[str]], width: int, height: int):
        """Set the scene data to render"""
        self.scene_data = scene_data
        self.scene_width = width
        self.scene_height = height
        
    def draw_scene(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0,
                  scale: int = 1, tint_map: Optional[Dict[str, Tuple[float, float, float]]] = None):
        """Draw the entire scene"""
        for y, row in enumerate(self.scene_data):
            for x, sprite_name in enumerate(row):
                if sprite_name and sprite_name != '':
                    tint_color = tint_map.get(sprite_name) if tint_map else None
                    
                    screen_x = (x * self.sprite_system.tile_size[0] * scale) + offset_x
                    screen_y = (y * self.sprite_system.tile_size[1] * scale) + offset_y
                    
                    self.sprite_system.draw_sprite(surface, sprite_name, 
                                                 screen_x, screen_y, tint_color, scale)
    
    def get_sprite_at_position(self, x: int, y: int, scale: int = 1) -> Optional[str]:
        """Get the sprite name at a given screen position"""
        if not self.scene_data:
            return None
            
        tile_x = x // (self.sprite_system.tile_size[0] * scale)
        tile_y = y // (self.sprite_system.tile_size[1] * scale)
        
        if 0 <= tile_y < len(self.scene_data) and 0 <= tile_x < len(self.scene_data[tile_y]):
            return self.scene_data[tile_y][tile_x]
        return None


class GameSpriteManager:
    """High-level sprite manager for games"""
    
    def __init__(self, tile_size: Tuple[int, int] = (16, 24)):
        self.sprite_system = SpriteSystem(tile_size)
        self.renderer = SpriteRenderer(self.sprite_system)
        self.tint_presets: Dict[str, Tuple[float, float, float]] = {}
        
    def load_game_assets(self, assets_path: Path) -> bool:
        """Load all game assets from a directory"""
        success = True
        
        # Load spritesheets
        spritesheet_files = {
            'terrain': assets_path / "oryx_roguelike" / "Terrain.png",
            'terrain_objects': assets_path / "oryx_roguelike" / "Terrain_Objects.png",
            'interface': assets_path / "oryx_roguelike" / "Interface.png",
            'avatar': assets_path / "oryx_roguelike" / "Avatar.png",
            'avatar_equipment': assets_path / "oryx_roguelike" / "Avatar_Equipment.png",
            'monsters': assets_path / "oryx_roguelike" / "Monsters.png"
        }
        
        for name, path in spritesheet_files.items():
            if not self.sprite_system.load_spritesheet(name, path):
                success = False
                
        # Load sprites from CSV
        csv_file = assets_path / "oryx_roguelike" / "sprite_names.csv"
        
        if csv_file.exists():
            # Map spritesheet names to CSV file names
            csv_spritesheet_mapping = {
                'terrain': 'Terrain.png',
                'terrain_objects': 'Terrain_Objects.png',
                'interface': 'Interface.png',
                'avatar': 'Avatar.png',
                'avatar_equipment': 'Avatar_Equipment.png',
                'monsters': 'Monsters.png'
            }
            
            for spritesheet_name, csv_name in csv_spritesheet_mapping.items():
                self.sprite_system.load_sprites_from_csv(csv_file, csv_name)
        else:
            # Try in the system directory as fallback
            csv_file = assets_path.parent / "system" / "sprite_names.csv"
            
            if csv_file.exists():
                csv_mapping = {
                    'terrain': 'Terrain.png',
                    'terrain_objects': 'Terrain_Objects.png', 
                    'interface': 'Interface.png',
                    'avatar': 'Avatar.png',
                    'avatar_equipment': 'Avatar_Equipment.png'
                }
                
                for spritesheet_name, csv_name in csv_mapping.items():
                    if spritesheet_name in spritesheet_files:
                        self.sprite_system.load_sprites_from_csv(csv_file, csv_name)
        
        return success
    
    def set_tint_preset(self, name: str, color: Tuple[float, float, float]):
        """Set a tint preset for easy reuse"""
        self.tint_presets[name] = color
        
    def get_tint_preset(self, name: str) -> Optional[Tuple[float, float, float]]:
        """Get a tint preset by name"""
        return self.tint_presets.get(name)
    
    def create_scene(self, width: int, height: int, 
                    generator_func: Optional[callable] = None) -> List[List[str]]:
        """Create a scene using a generator function"""
        if generator_func:
            return generator_func(width, height, self.sprite_system.list_sprites())
        else:
            return [[''] * width for _ in range(height)]
    
    # Overlap prevention methods (delegated to sprite_system)
    def set_overlap_check(self, enabled: bool):
        """Enable or disable sprite overlap checking."""
        self.sprite_system.set_overlap_check(enabled)
    
    def register_sprite_position(self, sprite_name: str, x: int, y: int, width: int, height: int):
        """Register a sprite's position for overlap checking."""
        self.sprite_system.register_sprite_position(sprite_name, x, y, width, height)
    
    def unregister_sprite_position(self, sprite_name: str):
        """Remove a sprite's position from overlap checking."""
        self.sprite_system.unregister_sprite_position(sprite_name)
    
    def check_overlap(self, x: int, y: int, width: int, height: int, 
                     exclude_sprite: Optional[str] = None) -> List[str]:
        """Check if a position overlaps with any registered sprites."""
        return self.sprite_system.check_overlap(x, y, width, height, exclude_sprite)
    
    def find_non_overlapping_position(self, width: int, height: int, 
                                    max_attempts: int = 100,
                                    screen_width: int = 1024, 
                                    screen_height: int = 768) -> Optional[Tuple[int, int]]:
        """Find a position that doesn't overlap with existing sprites."""
        return self.sprite_system.find_non_overlapping_position(
            width, height, max_attempts, screen_width, screen_height
        )
    
    def draw_sprite_safe(self, surface: pygame.Surface, sprite_name: str, 
                        x: int, y: int, tint_color: Optional[Tuple[float, float, float]] = None,
                        scale: int = 1, prevent_overlap: bool = True) -> bool:
        """Draw a sprite with overlap prevention."""
        return self.sprite_system.draw_sprite(
            surface, sprite_name, x, y, tint_color, scale, prevent_overlap
        )
    
    def clear_sprite_positions(self):
        """Clear all registered sprite positions."""
        self.sprite_system.clear_sprite_positions()
    
    def get_overlapping_sprites(self, x: int, y: int, width: int, height: int) -> List[str]:
        """Get all sprites that overlap with the given rectangle."""
        return self.sprite_system.get_overlapping_sprites(x, y, width, height)
    
    def render_scene(self, surface: pygame.Surface, scene_data: List[List[str]], 
                    offset_x: int = 0, offset_y: int = 0, scale: int = 1,
                    tint_preset: Optional[str] = None, tint_map: Optional[Dict[str, Tuple[float, float, float]]] = None):
        """Render a scene with optional tinting"""
        if tint_map is None and tint_preset and tint_preset in self.tint_presets:
            # Apply the same tint to all sprites
            tint_color = self.tint_presets[tint_preset]
            tint_map = {sprite: tint_color for sprite in self.sprite_system.list_sprites()}
        
        self.renderer.set_scene(scene_data, len(scene_data[0]) if scene_data else 0, len(scene_data))
        self.renderer.draw_scene(surface, offset_x, offset_y, scale, tint_map)
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        memory_stats = self.sprite_system.get_memory_usage()
        return {
            'loaded_sprites': len(self.sprite_system.list_sprites()),
            'tint_presets': len(self.tint_presets),
            'memory_usage': memory_stats
        }
