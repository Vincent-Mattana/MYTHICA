"""
Terrain Renderer for Treasure Goblin
Handles rendering of terrain tiles using the sprite system.
"""

import pygame
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from .terrain_system import TerrainTile, TerrainType, BiomeType
from .sprite_system import GameSpriteManager

class TerrainRenderer:
    """Renders terrain tiles using the sprite system."""
    
    def __init__(self, tile_size: Tuple[int, int] = (32, 32), assets_path: Optional[Path] = None):
        self.tile_size = tile_size
        self.sprite_manager = GameSpriteManager()
        
        if assets_path is None:
            assets_path = Path(__file__).parent.parent / "assets"
        self.sprite_manager.load_game_assets(assets_path)
        
        # Terrain sprite mappings using actual sprite names from catalog
        self.terrain_sprites = {
            TerrainType.GRASS: "small grass",
            TerrainType.DIRT: "Wall",  # Using wall as dirt/ground
            TerrainType.WATER: "water 1",
            TerrainType.TREE: "tree - confier",
            TerrainType.SHRUB: "shrub",
            TerrainType.ROCK: "Wall",  # Using wall as rock
            TerrainType.ROAD: "stairs up",  # Using stairs as road
            TerrainType.BRIDGE: "stairs down"  # Using stairs as bridge
        }
        
        # Biome-specific sprite variations using actual sprite names
        self.biome_variations = {
            BiomeType.WOODLAND: {
                TerrainType.GRASS: ["small grass", "big grass", "grass flowers"],
                TerrainType.TREE: ["tree - confier", "tree dead"],
                TerrainType.SHRUB: ["shrub", "shrub dead"],
                TerrainType.WATER: ["water 1", "water 2"],
                TerrainType.ROCK: ["Wall", "wall dmg 1", "wall dmg 2"],
                TerrainType.DIRT: ["Wall", "wall dmg 3", "wall dmg 4"]
            }
        }
        
        # Feature sprites using actual sprite names
        self.feature_sprites = {
            "road": "stairs up",
            "river": "water 1",
            "pond": "water 2",
            "grove": "tree - confier",
            "shrub": "shrub",
            "grass": "small grass"
        }
    
    def render_terrain(self, surface: pygame.Surface, terrain: List[List[TerrainTile]], 
                      offset_x: int = 0, offset_y: int = 0, scale: int = 1) -> None:
        """Render the entire terrain map."""
        for y, row in enumerate(terrain):
            for x, tile in enumerate(row):
                self.render_tile(surface, tile, x, y, offset_x, offset_y, scale)
    
    def render_efficient_terrain(self, surface: pygame.Surface, terrain, 
                               offset_x: int = 0, offset_y: int = 0, scale: int = 1) -> None:
        """Render an efficient terrain map."""
        for y in range(terrain.height):
            for x in range(terrain.width):
                self.render_efficient_tile(surface, terrain, x, y, offset_x, offset_y, scale)
    
    def render_tile(self, surface: pygame.Surface, tile: TerrainTile, 
                   grid_x: int, grid_y: int, offset_x: int = 0, offset_y: int = 0, 
                   scale: int = 1) -> None:
        """Render a single terrain tile."""
        # Calculate screen position
        screen_x = offset_x + (grid_x * self.tile_size[0] * scale)
        screen_y = offset_y + (grid_y * self.tile_size[1] * scale)
        
        # Get sprite for terrain type
        sprite = self._get_terrain_sprite(tile)
        
        if sprite:
            # Scale sprite if needed
            if scale != 1:
                scaled_sprite = pygame.transform.scale(sprite, 
                    (self.tile_size[0] * scale, self.tile_size[1] * scale))
            else:
                scaled_sprite = sprite
            
            # Apply terrain-specific effects
            final_sprite = self._apply_terrain_effects(scaled_sprite, tile)
            
            # Render the sprite
            surface.blit(final_sprite, (screen_x, screen_y))
        
        # Features are now included in the main sprite selection
    
    def render_efficient_tile(self, surface: pygame.Surface, terrain, 
                            grid_x: int, grid_y: int, offset_x: int = 0, offset_y: int = 0, 
                            scale: int = 1) -> None:
        """Render a single efficient terrain tile."""
        # Calculate screen position
        screen_x = offset_x + (grid_x * self.tile_size[0] * scale)
        screen_y = offset_y + (grid_y * self.tile_size[1] * scale)
        
        # Get tile information
        terrain_type = terrain.get_terrain_type(grid_x, grid_y)
        elevation = terrain.get_elevation(grid_x, grid_y)
        moisture = terrain.get_moisture(grid_x, grid_y)
        features = terrain.get_features(grid_x, grid_y)
        
        # Create a mock tile object for compatibility
        class MockTile:
            def __init__(self, terrain_type, biome, elevation, moisture, features):
                self.terrain_type = terrain_type
                self.biome = biome
                self.elevation = elevation
                self.moisture = moisture
                self.features = features
        
        mock_tile = MockTile(terrain_type, terrain.biome, elevation, moisture, features)
        
        # Get sprite for terrain type
        sprite = self._get_terrain_sprite(mock_tile)
        
        if sprite:
            # Scale sprite if needed
            if scale != 1:
                scaled_sprite = pygame.transform.scale(sprite, 
                    (self.tile_size[0] * scale, self.tile_size[1] * scale))
            else:
                scaled_sprite = sprite
            
            # Apply terrain-specific effects
            final_sprite = self._apply_terrain_effects(scaled_sprite, mock_tile)
            
            # Render the sprite
            surface.blit(final_sprite, (screen_x, screen_y))
    
    def _get_terrain_sprite(self, tile: TerrainTile) -> Optional[pygame.Surface]:
        """Get the most appropriate sprite for a terrain tile based on priority."""
        # Determine the most important feature/sprite to display
        sprite_name = self._get_priority_sprite_name(tile)
        if not sprite_name:
            return None
        
        # Try to get sprite from sprite manager
        sprite = self.sprite_manager.sprite_system.get_sprite(sprite_name)
        
        # If not found, try with different naming conventions
        if not sprite:
            # Try with different prefixes
            for prefix in ["terrain_", "tile_", ""]:
                alt_name = f"{prefix}{sprite_name}"
                sprite = self.sprite_manager.sprite_system.get_sprite(alt_name)
                if sprite:
                    break
        
        return sprite
    
    def _get_priority_sprite_name(self, tile: TerrainTile) -> Optional[str]:
        """Determine the most important sprite to display based on terrain and features."""
        # Priority order for features (higher priority = more important)
        feature_priority = {
            "road": 10,      # Roads are most important for navigation
            "river": 9,       # Rivers are very visible
            "pond": 8,        # Ponds are significant water features
            "grove": 7,       # Tree groves are important landmarks
            "shrub": 6,       # Shrubs are secondary vegetation
            "grass": 5        # Basic grass is lowest priority
        }
        
        # Get all features for this tile
        features = tile.features if hasattr(tile, 'features') else []
        if hasattr(tile, 'features') and hasattr(tile.features, 'to_list'):
            features = tile.features.to_list()
        
        # Find the highest priority feature
        highest_priority = -1
        priority_feature = None
        
        for feature in features:
            if feature in feature_priority:
                priority = feature_priority[feature]
                if priority > highest_priority:
                    highest_priority = priority
                    priority_feature = feature
        
        # If we have a high-priority feature, use its sprite
        if priority_feature:
            feature_sprite = self.feature_sprites.get(priority_feature)
            if feature_sprite:
                return feature_sprite
        
        # Otherwise, use the base terrain type sprite
        base_sprite_name = self.terrain_sprites.get(tile.terrain_type)
        if not base_sprite_name:
            return None
        
        # Check for biome-specific variations
        if tile.biome in self.biome_variations:
            biome_variations = self.biome_variations[tile.biome]
            if tile.terrain_type in biome_variations:
                variations = biome_variations[tile.terrain_type]
                # Choose variation based on position (for consistency)
                variation_index = (tile.elevation * 100) % len(variations)
                base_sprite_name = variations[int(variation_index)]
        
        return base_sprite_name
    
    def _apply_terrain_effects(self, sprite: pygame.Surface, tile: TerrainTile) -> pygame.Surface:
        """Apply visual effects to terrain sprites based on tile properties."""
        # Create a copy to avoid modifying the original
        final_sprite = sprite.copy()
        
        # Apply elevation-based tinting (higher = lighter)
        if tile.elevation > 0.7:
            # High elevation - lighter tint
            tint_color = (255, 255, 255, 200)
            final_sprite.fill(tint_color, special_flags=pygame.BLEND_RGBA_MULT)
        elif tile.elevation < 0.3:
            # Low elevation - darker tint
            tint_color = (180, 180, 180, 255)
            final_sprite.fill(tint_color, special_flags=pygame.BLEND_RGBA_MULT)
        
        # Apply moisture-based effects
        if tile.moisture > 0.8:
            # High moisture - add blue tint
            moisture_tint = (200, 200, 255, 200)
            final_sprite.fill(moisture_tint, special_flags=pygame.BLEND_RGBA_MULT)
        elif tile.moisture < 0.2:
            # Low moisture - add brown tint
            dryness_tint = (255, 200, 150, 200)
            final_sprite.fill(dryness_tint, special_flags=pygame.BLEND_RGBA_MULT)
        
        return final_sprite
    
    def _render_features(self, surface: pygame.Surface, tile: TerrainTile, 
                        screen_x: int, screen_y: int, scale: int) -> None:
        """Render additional features on top of the base terrain."""
        for feature in tile.features:
            feature_sprite_name = self.feature_sprites.get(feature)
            if feature_sprite_name:
                feature_sprite = self.sprite_manager.sprite_system.get_sprite(feature_sprite_name)
                if feature_sprite:
                    # Scale feature sprite
                    if scale != 1:
                        scaled_feature = pygame.transform.scale(feature_sprite,
                            (self.tile_size[0] * scale, self.tile_size[1] * scale))
                    else:
                        scaled_feature = feature_sprite
                    
                    # Apply feature-specific effects
                    final_feature = self._apply_feature_effects(scaled_feature, feature, tile)
                    
                    # Render feature with slight offset for layering
                    feature_offset_x = screen_x + (2 * scale)
                    feature_offset_y = screen_y + (2 * scale)
                    surface.blit(final_feature, (feature_offset_x, feature_offset_y))
    
    def _apply_feature_effects(self, sprite: pygame.Surface, feature: str, tile: TerrainTile) -> pygame.Surface:
        """Apply visual effects to feature sprites."""
        final_sprite = sprite.copy()
        
        # Apply feature-specific effects
        if feature == "river":
            # Rivers get a blue tint
            river_tint = (150, 200, 255, 200)
            final_sprite.fill(river_tint, special_flags=pygame.BLEND_RGBA_MULT)
        elif feature == "pond":
            # Ponds get a darker blue tint
            pond_tint = (100, 150, 255, 200)
            final_sprite.fill(pond_tint, special_flags=pygame.BLEND_RGBA_MULT)
        elif feature == "grove":
            # Groves get a green tint
            grove_tint = (150, 255, 150, 200)
            final_sprite.fill(grove_tint, special_flags=pygame.BLEND_RGBA_MULT)
        elif feature == "road":
            # Roads get a brown tint
            road_tint = (200, 180, 150, 200)
            final_sprite.fill(road_tint, special_flags=pygame.BLEND_RGBA_MULT)
        
        return final_sprite
    
    def get_tile_at_position(self, terrain: List[List[TerrainTile]], 
                           screen_x: int, screen_y: int, offset_x: int = 0, 
                           offset_y: int = 0, scale: int = 1) -> Optional[TerrainTile]:
        """Get the terrain tile at a specific screen position."""
        # Convert screen coordinates to grid coordinates
        grid_x = (screen_x - offset_x) // (self.tile_size[0] * scale)
        grid_y = (screen_y - offset_y) // (self.tile_size[1] * scale)
        
        if 0 <= grid_y < len(terrain) and 0 <= grid_x < len(terrain[grid_y]):
            return terrain[grid_y][grid_x]
        
        return None
    
    def get_tiles_in_rect(self, terrain: List[List[TerrainTile]], 
                         screen_rect: pygame.Rect, offset_x: int = 0, 
                         offset_y: int = 0, scale: int = 1) -> List[Tuple[int, int, TerrainTile]]:
        """Get all terrain tiles within a screen rectangle."""
        tiles = []
        
        # Convert screen rectangle to grid coordinates
        start_grid_x = (screen_rect.left - offset_x) // (self.tile_size[0] * scale)
        start_grid_y = (screen_rect.top - offset_y) // (self.tile_size[1] * scale)
        end_grid_x = (screen_rect.right - offset_x) // (self.tile_size[0] * scale) + 1
        end_grid_y = (screen_rect.bottom - offset_y) // (self.tile_size[1] * scale) + 1
        
        # Clamp to terrain bounds
        start_grid_x = max(0, start_grid_x)
        start_grid_y = max(0, start_grid_y)
        end_grid_x = min(len(terrain[0]) if terrain else 0, end_grid_x)
        end_grid_y = min(len(terrain), end_grid_y)
        
        # Collect tiles
        for y in range(start_grid_y, end_grid_y):
            for x in range(start_grid_x, end_grid_x):
                if 0 <= y < len(terrain) and 0 <= x < len(terrain[y]):
                    tiles.append((x, y, terrain[y][x]))
        
        return tiles
    
    def create_minimap(self, terrain, 
                      minimap_size: Tuple[int, int] = (200, 200)) -> pygame.Surface:
        """Create a minimap of the terrain."""
        minimap = pygame.Surface(minimap_size, pygame.SRCALPHA)
        
        # Check if it's efficient terrain or regular terrain
        if hasattr(terrain, 'width') and hasattr(terrain, 'height'):
            # Efficient terrain
            terrain_width = terrain.width
            terrain_height = terrain.height
        else:
            # Regular terrain
            if not terrain or not terrain[0]:
                return minimap
            terrain_width = len(terrain[0])
            terrain_height = len(terrain)
        
        # Calculate scale factors
        scale_x = minimap_size[0] / terrain_width
        scale_y = minimap_size[1] / terrain_height
        
        # Color mapping for terrain types (matching sprite themes)
        terrain_colors = {
            TerrainType.GRASS: (34, 139, 34),      # Forest Green
            TerrainType.DIRT: (101, 67, 33),       # Brown (dirt-like)
            TerrainType.WATER: (0, 100, 200),      # Blue
            TerrainType.TREE: (0, 80, 0),          # Dark Green
            TerrainType.SHRUB: (107, 142, 35),     # Olive Drab
            TerrainType.ROCK: (80, 80, 80),        # Gray
            TerrainType.ROAD: (120, 120, 120),     # Light Gray (stone-like)
            TerrainType.BRIDGE: (100, 100, 100),   # Gray
        }
        
        # Render minimap
        for y in range(terrain_height):
            for x in range(terrain_width):
                if hasattr(terrain, 'get_terrain_type'):
                    # Efficient terrain
                    terrain_type = terrain.get_terrain_type(x, y)
                else:
                    # Regular terrain
                    terrain_type = terrain[y][x].terrain_type
                
                color = terrain_colors.get(terrain_type, (128, 128, 128))
                
                # Calculate minimap position
                minimap_x = int(x * scale_x)
                minimap_y = int(y * scale_y)
                pixel_width = max(1, int(scale_x))
                pixel_height = max(1, int(scale_y))
                
                # Draw pixel
                pygame.draw.rect(minimap, color, 
                               (minimap_x, minimap_y, pixel_width, pixel_height))
        
        return minimap
