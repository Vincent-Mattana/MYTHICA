"""
Memory-efficient terrain storage system for Treasure Goblin
Uses compact data structures to minimize memory usage.
"""

import array
from typing import List, Tuple, Dict, Optional
from enum import IntEnum
from dataclasses import dataclass

class CompactTerrainType(IntEnum):
    """Compact terrain types using integers."""
    GRASS = 0
    DIRT = 1
    WATER = 2
    TREE = 3
    SHRUB = 4
    ROCK = 5
    ROAD = 6
    BRIDGE = 7

class CompactBiomeType(IntEnum):
    """Compact biome types using integers."""
    WOODLAND = 0
    FOREST = 1
    PLAINS = 2
    DESERT = 3
    MOUNTAINS = 4
    SWAMP = 5

@dataclass
class TerrainFeatures:
    """Compact feature storage using bit flags."""
    has_road: bool = False
    has_river: bool = False
    has_pond: bool = False
    has_grove: bool = False
    has_shrub: bool = False
    has_grass: bool = False
    
    def to_byte(self) -> int:
        """Convert to a single byte for storage."""
        byte_val = 0
        if self.has_road: byte_val |= 1
        if self.has_river: byte_val |= 2
        if self.has_pond: byte_val |= 4
        if self.has_grove: byte_val |= 8
        if self.has_shrub: byte_val |= 16
        if self.has_grass: byte_val |= 32
        return byte_val
    
    @classmethod
    def from_byte(cls, byte_val: int) -> 'TerrainFeatures':
        """Create from a byte value."""
        return cls(
            has_road=bool(byte_val & 1),
            has_river=bool(byte_val & 2),
            has_pond=bool(byte_val & 4),
            has_grove=bool(byte_val & 8),
            has_shrub=bool(byte_val & 16),
            has_grass=bool(byte_val & 32)
        )

class EfficientTerrain:
    """Memory-efficient terrain storage using arrays."""
    
    def __init__(self, width: int, height: int, biome: CompactBiomeType = CompactBiomeType.WOODLAND):
        self.width = width
        self.height = height
        self.biome = biome
        
        # Use arrays for compact storage
        # Each tile uses: 1 byte terrain_type + 1 byte features + 2 bytes elevation + 2 bytes moisture = 6 bytes total
        self.terrain_types = array.array('B', [0] * (width * height))  # 1 byte per tile
        self.features = array.array('B', [0] * (width * height))       # 1 byte per tile
        self.elevations = array.array('H', [0] * (width * height))     # 2 bytes per tile (0-65535)
        self.moistures = array.array('H', [0] * (width * height))      # 2 bytes per tile (0-65535)
        
        # Initialize with default values
        for i in range(width * height):
            self.terrain_types[i] = CompactTerrainType.GRASS
            self.elevations[i] = 32768  # 0.5 * 65535
            self.moistures[i] = 32768   # 0.5 * 65535
    
    def get_tile_index(self, x: int, y: int) -> int:
        """Get array index for tile coordinates."""
        return y * self.width + x
    
    def set_terrain_type(self, x: int, y: int, terrain_type: CompactTerrainType):
        """Set terrain type for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            self.terrain_types[index] = terrain_type
    
    def get_terrain_type(self, x: int, y: int) -> CompactTerrainType:
        """Get terrain type for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            return CompactTerrainType(self.terrain_types[index])
        return CompactTerrainType.GRASS
    
    def set_elevation(self, x: int, y: int, elevation: float):
        """Set elevation (0.0 to 1.0) for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            # Convert float to 16-bit integer (0-65535)
            self.elevations[index] = int(elevation * 65535)
    
    def get_elevation(self, x: int, y: int) -> float:
        """Get elevation (0.0 to 1.0) for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            return self.elevations[index] / 65535.0
        return 0.5
    
    def set_moisture(self, x: int, y: int, moisture: float):
        """Set moisture (0.0 to 1.0) for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            # Convert float to 16-bit integer (0-65535)
            self.moistures[index] = int(moisture * 65535)
    
    def get_moisture(self, x: int, y: int) -> float:
        """Get moisture (0.0 to 1.0) for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            return self.moistures[index] / 65535.0
        return 0.5
    
    def set_features(self, x: int, y: int, features: TerrainFeatures):
        """Set features for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            self.features[index] = features.to_byte()
    
    def get_features(self, x: int, y: int) -> TerrainFeatures:
        """Get features for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            return TerrainFeatures.from_byte(self.features[index])
        return TerrainFeatures()
    
    def add_feature(self, x: int, y: int, feature_name: str):
        """Add a specific feature to a tile."""
        features = self.get_features(x, y)
        
        if feature_name == "road":
            features.has_road = True
        elif feature_name == "river":
            features.has_river = True
        elif feature_name == "pond":
            features.has_pond = True
        elif feature_name == "grove":
            features.has_grove = True
        elif feature_name == "shrub":
            features.has_shrub = True
        elif feature_name == "grass":
            features.has_grass = True
        
        self.set_features(x, y, features)
    
    def get_tile_info(self, x: int, y: int) -> Dict:
        """Get complete tile information as a dictionary."""
        return {
            'terrain_type': self.get_terrain_type(x, y),
            'biome': self.biome,
            'elevation': self.get_elevation(x, y),
            'moisture': self.get_moisture(x, y),
            'features': self.get_features(x, y)
        }
    
    def get_terrain_statistics(self) -> Dict[str, int]:
        """Get statistics about the terrain."""
        stats = {}
        for i in range(self.width * self.height):
            terrain_type = CompactTerrainType(self.terrain_types[i])
            terrain_name = terrain_type.name.lower()
            stats[terrain_name] = stats.get(terrain_name, 0) + 1
        return stats
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics."""
        total_tiles = self.width * self.height
        
        # Calculate bytes used by each array
        terrain_bytes = len(self.terrain_types) * self.terrain_types.itemsize
        features_bytes = len(self.features) * self.features.itemsize
        elevation_bytes = len(self.elevations) * self.elevations.itemsize
        moisture_bytes = len(self.moistures) * self.moistures.itemsize
        
        total_bytes = terrain_bytes + features_bytes + elevation_bytes + moisture_bytes
        
        return {
            'total_tiles': total_tiles,
            'bytes_per_tile': total_bytes // total_tiles,
            'total_bytes': total_bytes,
            'total_kb': total_bytes / 1024,
            'terrain_types_bytes': terrain_bytes,
            'features_bytes': features_bytes,
            'elevations_bytes': elevation_bytes,
            'moistures_bytes': moisture_bytes
        }
    
    def get_tiles_in_radius(self, center_x: int, center_y: int, radius: int) -> List[Tuple[int, int, Dict]]:
        """Get all tiles within a radius of the center point."""
        tiles = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x = center_x + dx
                y = center_y + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    distance = (dx * dx + dy * dy) ** 0.5
                    if distance <= radius:
                        tile_info = self.get_tile_info(x, y)
                        tiles.append((x, y, tile_info))
        return tiles

def compare_memory_usage():
    """Compare memory usage between old and new systems."""
    from .terrain_system import TerrainGenerator, BiomeType
    
    width, height = 60, 50
    
    # Old system
    old_generator = TerrainGenerator(width, height, seed=42)
    old_terrain = old_generator.generate_terrain(BiomeType.WOODLAND)
    
    # New system
    new_terrain = EfficientTerrain(width, height, CompactBiomeType.WOODLAND)
    
    # Fill new terrain with some sample data
    for y in range(height):
        for x in range(width):
            new_terrain.set_terrain_type(x, y, CompactTerrainType.GRASS)
            new_terrain.set_elevation(x, y, 0.5)
            new_terrain.set_moisture(x, y, 0.5)
    
    # Calculate memory usage
    old_memory = width * height * 200  # Rough estimate for TerrainTile objects
    new_memory = new_terrain.get_memory_usage()
    
    print(f"Memory Usage Comparison for {width}x{height} terrain:")
    print(f"Old system (estimated): {old_memory / 1024:.1f} KB")
    print(f"New system: {new_memory['total_kb']:.1f} KB")
    print(f"Memory reduction: {((old_memory - new_memory['total_bytes']) / old_memory) * 100:.1f}%")
    print(f"Bytes per tile - Old: ~200, New: {new_memory['bytes_per_tile']}")

if __name__ == "__main__":
    compare_memory_usage()
