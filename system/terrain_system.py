"""
Terrain Generation System for Mythica
Handles procedural generation of different biomes and terrain features.
"""

import random
import math
from typing import List, Tuple, Dict, Set, Optional
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import array

# Try to import optional dependencies
try:
    import noise
    HAS_NOISE = True
except ImportError:
    HAS_NOISE = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

class TerrainType(Enum):
    """Types of terrain tiles."""
    GRASS = "grass"
    DIRT = "dirt"
    WATER = "water"
    TREE = "tree"
    SHRUB = "shrub"
    ROCK = "rock"
    ROAD = "road"
    BRIDGE = "bridge"

class BiomeType(Enum):
    """Types of biomes."""
    WOODLAND = "woodland"
    FOREST = "forest"
    PLAINS = "plains"
    DESERT = "desert"
    MOUNTAINS = "mountains"
    SWAMP = "swamp"

@dataclass
class TerrainTile:
    """Represents a single terrain tile."""
    terrain_type: TerrainType
    biome: BiomeType
    elevation: float = 0.0
    moisture: float = 0.0
    temperature: float = 0.0
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []

class TerrainFeatures:
    """Compact feature storage using bit flags."""
    def __init__(self, has_road=False, has_river=False, has_pond=False, 
                 has_grove=False, has_shrub=False, has_grass=False):
        self.has_road = has_road
        self.has_river = has_river
        self.has_pond = has_pond
        self.has_grove = has_grove
        self.has_shrub = has_shrub
        self.has_grass = has_grass
    
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
    
    def to_list(self) -> List[str]:
        """Convert to list of feature names for compatibility."""
        features = []
        if self.has_road: features.append("road")
        if self.has_river: features.append("river")
        if self.has_pond: features.append("pond")
        if self.has_grove: features.append("grove")
        if self.has_shrub: features.append("shrub")
        if self.has_grass: features.append("grass")
        return features
    
    def __str__(self) -> str:
        """String representation for debug logging."""
        features = self.to_list()
        return f"Features({', '.join(features) if features else 'none'})"

class EfficientTerrain:
    """Memory-efficient terrain storage using arrays."""
    
    def __init__(self, width: int, height: int, biome: BiomeType = BiomeType.WOODLAND):
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
            self.terrain_types[i] = list(TerrainType).index(TerrainType.GRASS)
            self.elevations[i] = 32768  # 0.5 * 65535
            self.moistures[i] = 32768   # 0.5 * 65535
    
    def get_tile_index(self, x: int, y: int) -> int:
        """Get array index for tile coordinates."""
        return y * self.width + x
    
    def set_terrain_type(self, x: int, y: int, terrain_type: TerrainType):
        """Set terrain type for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            self.terrain_types[index] = list(TerrainType).index(terrain_type)
    
    def get_terrain_type(self, x: int, y: int) -> TerrainType:
        """Get terrain type for a tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self.get_tile_index(x, y)
            return list(TerrainType)[self.terrain_types[index]]
        return TerrainType.GRASS
    
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
            terrain_type = list(TerrainType)[self.terrain_types[i]]
            terrain_name = terrain_type.value
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
    
    def debug_log_tile(self, x: int, y: int) -> str:
        """Generate debug log message for a specific tile."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return f"DEBUG: Invalid tile coordinates ({x}, {y}) - out of bounds"
        
        terrain_type = self.get_terrain_type(x, y)
        elevation = self.get_elevation(x, y)
        moisture = self.get_moisture(x, y)
        features = self.get_features(x, y)
        
        return (f"DEBUG: Tile({x}, {y}) = {terrain_type.value} | "
                f"Elevation: {elevation:.3f} | Moisture: {moisture:.3f} | "
                f"{features}")
    
    def debug_log_region(self, x1: int, y1: int, x2: int, y2: int) -> List[str]:
        """Generate debug log messages for a rectangular region."""
        logs = []
        logs.append(f"DEBUG: Region ({x1}, {y1}) to ({x2}, {y2})")
        
        for y in range(max(0, y1), min(self.height, y2 + 1)):
            for x in range(max(0, x1), min(self.width, x2 + 1)):
                logs.append(self.debug_log_tile(x, y))
        
        return logs
    
    def debug_log_terrain_summary(self) -> str:
        """Generate debug log summary of entire terrain."""
        stats = self.get_terrain_statistics()
        memory = self.get_memory_usage()
        
        summary = f"DEBUG: Terrain Summary - {self.width}x{self.height} tiles\n"
        summary += f"  Biome: {self.biome.value}\n"
        summary += f"  Memory: {memory['total_kb']:.1f} KB ({memory['bytes_per_tile']} bytes/tile)\n"
        summary += "  Terrain Distribution:\n"
        
        for terrain_type, count in stats.items():
            percentage = (count / (self.width * self.height)) * 100
            summary += f"    {terrain_type}: {count} tiles ({percentage:.1f}%)\n"
        
        return summary

class TerrainGenerator:
    """Main terrain generation system with enhanced randomization."""
    
    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**32 - 1)
        
        # Set up multiple random generators for different aspects
        self._setup_random_generators()
        
        # Terrain generation parameters (now seed-dependent)
        self.scale = 30.0 + (self.seed % 40)  # Noise scale varies by seed
        self.octaves = 4 + (self.seed % 4)    # Octaves vary by seed
        self.persistence = 0.4 + (self.seed % 30) / 100.0
        self.lacunarity = 1.8 + (self.seed % 40) / 100.0
        
        # Biome parameters
        self.biome_scale = 80.0 + (self.seed % 40)
        
        # Feature generation parameters (seed-dependent for variety)
        self.road_width = 2 + (self.seed % 3)
        self.river_width = 1 + (self.seed % 3)
        self.grove_min_size = 4 + (self.seed % 4)
        self.grove_max_size = 12 + (self.seed % 8)
        self.pond_min_size = 2 + (self.seed % 3)
        self.pond_max_size = 6 + (self.seed % 4)
        
        # Feature density parameters (seed-dependent)
        self.road_density = 0.3 + (self.seed % 20) / 100.0
        self.river_density = 0.2 + (self.seed % 15) / 100.0
        self.grove_density = 0.4 + (self.seed % 30) / 100.0
        self.pond_density = 0.1 + (self.seed % 10) / 100.0
        
        # Terrain feature seeds for consistent placement
        self.feature_seeds = {
            'roads': self.seed + 1000,
            'rivers': self.seed + 2000,
            'ponds': self.seed + 3000,
            'groves': self.seed + 4000,
            'shrubs': self.seed + 5000
        }
    
    def _setup_random_generators(self):
        """Set up separate random generators for different terrain aspects."""
        # Main random generator
        random.seed(self.seed)
        if HAS_NUMPY:
            np.random.seed(self.seed)
        
        # Create separate generators for different features
        self.height_rng = random.Random(self.seed + 100)
        self.moisture_rng = random.Random(self.seed + 200)
        self.feature_rng = random.Random(self.seed + 300)
        self.placement_rng = random.Random(self.seed + 400)
        
    def generate_terrain(self, biome: BiomeType = BiomeType.WOODLAND) -> List[List[TerrainTile]]:
        """Generate a complete terrain map."""
        # Initialize base terrain
        terrain = self._initialize_terrain(biome)
        
        # Generate base height and moisture maps
        height_map = self._generate_height_map()
        moisture_map = self._generate_moisture_map()
        
        # Apply biome-specific generation
        if biome == BiomeType.WOODLAND:
            terrain = self._generate_woodland(terrain, height_map, moisture_map)
        
        # Add features
        terrain = self._add_roads(terrain)
        terrain = self._add_rivers(terrain, height_map)
        terrain = self._add_ponds(terrain, height_map, moisture_map)
        terrain = self._add_groves(terrain, height_map, moisture_map)
        terrain = self._add_grass_and_shrubs(terrain, height_map, moisture_map)
        
        return terrain
    
    def generate_efficient_terrain(self, biome: BiomeType = BiomeType.WOODLAND) -> EfficientTerrain:
        """Generate a memory-efficient terrain map."""
        # Create efficient terrain storage
        terrain = EfficientTerrain(self.width, self.height, biome)
        
        # Generate base height and moisture maps
        height_map = self._generate_height_map()
        moisture_map = self._generate_moisture_map()
        
        # Apply biome-specific generation
        if biome == BiomeType.WOODLAND:
            self._generate_woodland_efficient(terrain, height_map, moisture_map)
        
        # Add features
        self._add_roads_efficient(terrain)
        self._add_rivers_efficient(terrain, height_map)
        self._add_ponds_efficient(terrain, height_map, moisture_map)
        self._add_groves_efficient(terrain, height_map, moisture_map)
        self._add_grass_and_shrubs_efficient(terrain, height_map, moisture_map)
        
        return terrain
    
    def _initialize_terrain(self, biome: BiomeType) -> List[List[TerrainTile]]:
        """Initialize the base terrain grid."""
        terrain = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(TerrainTile(
                    terrain_type=TerrainType.GRASS,
                    biome=biome
                ))
            terrain.append(row)
        return terrain
    
    def _generate_height_map(self) -> List[List[float]]:
        """Generate a height map using Perlin noise or fallback method."""
        height_map = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if HAS_NOISE:
                    # Generate noise value using external library
                    noise_val = noise.pnoise2(
                        x / self.scale,
                        y / self.scale,
                        octaves=self.octaves,
                        persistence=self.persistence,
                        lacunarity=self.lacunarity,
                        base=self.seed
                    )
                    # Normalize to 0-1 range
                    height = (noise_val + 1) / 2
                else:
                    # Fallback: use simple pseudo-random noise
                    height = self._simple_noise(x, y, self.scale, self.seed)
                row.append(height)
            height_map.append(row)
        return height_map
    
    def _generate_moisture_map(self) -> List[List[float]]:
        """Generate a moisture map using Perlin noise or fallback method."""
        moisture_map = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if HAS_NOISE:
                    # Generate moisture with different scale for variation
                    moisture_val = noise.pnoise2(
                        x / (self.scale * 0.8),
                        y / (self.scale * 0.8),
                        octaves=4,
                        persistence=0.6,
                        lacunarity=2.0,
                        base=self.seed + 1000
                    )
                    # Normalize to 0-1 range
                    moisture = (moisture_val + 1) / 2
                else:
                    # Fallback: use simple pseudo-random noise with different seed
                    moisture = self._simple_noise(x, y, self.scale * 0.8, self.seed + 1000)
                row.append(moisture)
            moisture_map.append(row)
        return moisture_map
    
    def _simple_noise(self, x: int, y: int, scale: float, seed: int) -> float:
        """Simple pseudo-random noise fallback when external libraries aren't available."""
        # Use a simple hash-based pseudo-random function
        # This creates smooth-ish noise by interpolating between grid points
        x0 = int(x / scale)
        y0 = int(y / scale)
        x1 = x0 + 1
        y1 = y0 + 1
        
        # Get noise values at grid points
        n00 = self._hash_noise(x0, y0, seed)
        n01 = self._hash_noise(x0, y1, seed)
        n10 = self._hash_noise(x1, y0, seed)
        n11 = self._hash_noise(x1, y1, seed)
        
        # Interpolate
        fx = (x / scale) - x0
        fy = (y / scale) - y0
        
        # Smooth interpolation
        fx = fx * fx * (3.0 - 2.0 * fx)
        fy = fy * fy * (3.0 - 2.0 * fy)
        
        n0 = n00 * (1 - fx) + n10 * fx
        n1 = n01 * (1 - fx) + n11 * fx
        noise_val = n0 * (1 - fy) + n1 * fy
        
        return noise_val
    
    def _hash_noise(self, x: int, y: int, seed: int) -> float:
        """Generate a pseudo-random value based on coordinates and seed."""
        # Simple hash function
        hash_val = (x * 374761393 + y * 668265263 + seed) & 0x7FFFFFFF
        hash_val = (hash_val ^ (hash_val >> 13)) * 1274126177
        hash_val = hash_val ^ (hash_val >> 16)
        
        # Convert to 0-1 range
        return (hash_val % 10000) / 10000.0
    
    def _generate_woodland(self, terrain: List[List[TerrainTile]], 
                          height_map: List[List[float]], 
                          moisture_map: List[List[float]]) -> List[List[TerrainTile]]:
        """Generate woodland-specific terrain features."""
        for y in range(self.height):
            for x in range(self.width):
                height = height_map[y][x]
                moisture = moisture_map[y][x]
                
                # Determine base terrain type based on height and moisture
                if height < 0.3:
                    # Low areas - more likely to be water or wet grass
                    if moisture > 0.7:
                        terrain[y][x].terrain_type = TerrainType.WATER
                    else:
                        terrain[y][x].terrain_type = TerrainType.GRASS
                elif height < 0.6:
                    # Mid-level areas - grass or dirt
                    if moisture > 0.5:
                        terrain[y][x].terrain_type = TerrainType.GRASS
                    else:
                        terrain[y][x].terrain_type = TerrainType.DIRT
                else:
                    # High areas - more likely to be rocky
                    if moisture < 0.3:
                        terrain[y][x].terrain_type = TerrainType.ROCK
                    else:
                        terrain[y][x].terrain_type = TerrainType.DIRT
                
                # Set elevation, moisture, and temperature
                terrain[y][x].elevation = height
                terrain[y][x].moisture = moisture
                terrain[y][x].temperature = 0.5 + (height * 0.3)  # Warmer at higher elevations
        
        return terrain
    
    def _add_roads(self, terrain: List[List[TerrainTile]]) -> List[List[TerrainTile]]:
        """Add road networks to the terrain with congruent placement."""
        # Use feature-specific random generator for consistent placement
        road_rng = random.Random(self.feature_seeds['roads'])
        
        # Determine number of roads based on density and terrain size
        max_roads = max(2, int(self.width * self.height * self.road_density / 1000))
        num_roads = road_rng.randint(2, max_roads)
        
        # Generate road network with strategic placement
        road_network = self._generate_road_network(road_rng, num_roads)
        
        for road in road_network:
            self._place_road(terrain, road)
        
        return terrain
    
    def _generate_road_network(self, rng: random.Random, num_roads: int) -> List[Dict]:
        """Generate a coherent road network with strategic placement."""
        roads = []
        
        # Always place at least one main road (horizontal or vertical)
        main_direction = rng.choice(['horizontal', 'vertical'])
        
        if main_direction == 'horizontal':
            # Main horizontal road
            y = rng.randint(self.height // 4, 3 * self.height // 4)
            start_x = rng.randint(0, self.width // 4)
            end_x = rng.randint(3 * self.width // 4, self.width - 1)
            roads.append({
                'type': 'horizontal',
                'y': y,
                'start_x': start_x,
                'end_x': end_x,
                'width': self.road_width
            })
        else:
            # Main vertical road
            x = rng.randint(self.width // 4, 3 * self.width // 4)
            start_y = rng.randint(0, self.height // 4)
            end_y = rng.randint(3 * self.height // 4, self.height - 1)
            roads.append({
                'type': 'vertical',
                'x': x,
                'start_y': start_y,
                'end_y': end_y,
                'width': self.road_width
            })
        
        # Add connecting roads
        for _ in range(num_roads - 1):
            road_type = rng.choice(['horizontal', 'vertical', 'diagonal'])
            
            if road_type == 'horizontal':
                y = rng.randint(0, self.height - 1)
                start_x = rng.randint(0, self.width // 3)
                end_x = rng.randint(2 * self.width // 3, self.width - 1)
                roads.append({
                    'type': 'horizontal',
                    'y': y,
                    'start_x': start_x,
                    'end_x': end_x,
                    'width': self.road_width
                })
            elif road_type == 'vertical':
                x = rng.randint(0, self.width - 1)
                start_y = rng.randint(0, self.height // 3)
                end_y = rng.randint(2 * self.height // 3, self.height - 1)
                roads.append({
                    'type': 'vertical',
                    'x': x,
                    'start_y': start_y,
                    'end_y': end_y,
                    'width': self.road_width
                })
            else:  # diagonal
                # Create a diagonal road with some meandering
                start_x = rng.randint(0, self.width // 2)
                start_y = rng.randint(0, self.height // 2)
                end_x = rng.randint(self.width // 2, self.width - 1)
                end_y = rng.randint(self.height // 2, self.height - 1)
                roads.append({
                    'type': 'diagonal',
                    'start_x': start_x,
                    'start_y': start_y,
                    'end_x': end_x,
                    'end_y': end_y,
                    'width': self.road_width
                })
        
        return roads
    
    def _place_road(self, terrain: List[List[TerrainTile]], road: Dict) -> None:
        """Place a single road on the terrain."""
        if road['type'] == 'horizontal':
            for x in range(road['start_x'], road['end_x'] + 1):
                for dy in range(-road['width'] // 2, road['width'] // 2 + 1):
                    road_y = road['y'] + dy
                    if 0 <= road_y < self.height and 0 <= x < self.width:
                        terrain[road_y][x].terrain_type = TerrainType.ROAD
                        terrain[road_y][x].features.append("road")
        
        elif road['type'] == 'vertical':
            for y in range(road['start_y'], road['end_y'] + 1):
                for dx in range(-road['width'] // 2, road['width'] // 2 + 1):
                    road_x = road['x'] + dx
                    if 0 <= road_x < self.width and 0 <= y < self.height:
                        terrain[y][road_x].terrain_type = TerrainType.ROAD
                        terrain[y][road_x].features.append("road")
        
        elif road['type'] == 'diagonal':
            # Create diagonal road with some meandering
            path = self._generate_diagonal_path(
                road['start_x'], road['start_y'],
                road['end_x'], road['end_y']
            )
            for x, y in path:
                for dx in range(-road['width'] // 2, road['width'] // 2 + 1):
                    for dy in range(-road['width'] // 2, road['width'] // 2 + 1):
                        road_x = x + dx
                        road_y = y + dy
                        if 0 <= road_x < self.width and 0 <= road_y < self.height:
                            terrain[road_y][road_x].terrain_type = TerrainType.ROAD
                            terrain[road_y][road_x].features.append("road")
    
    def _generate_diagonal_path(self, start_x: int, start_y: int, end_x: int, end_y: int) -> List[Tuple[int, int]]:
        """Generate a diagonal path with some meandering."""
        path = []
        current_x, current_y = start_x, start_y
        
        # Use feature-specific random generator
        path_rng = random.Random(self.feature_seeds['roads'] + start_x + start_y)
        
        while current_x != end_x or current_y != end_y:
            path.append((current_x, current_y))
            
            # Move towards target with some randomness
            if current_x < end_x:
                current_x += 1
            elif current_x > end_x:
                current_x -= 1
            
            if current_y < end_y:
                current_y += 1
            elif current_y > end_y:
                current_y -= 1
            
            # Add some meandering
            if path_rng.random() < 0.3:  # 30% chance to meander
                if path_rng.choice([True, False]):
                    current_x += path_rng.choice([-1, 1])
                else:
                    current_y += path_rng.choice([-1, 1])
        
        path.append((end_x, end_y))
        return path
    
    def _add_rivers(self, terrain: List[List[TerrainTile]], 
                   height_map: List[List[float]]) -> List[List[TerrainTile]]:
        """Add rivers to the terrain with congruent placement."""
        # Use feature-specific random generator for consistent placement
        river_rng = random.Random(self.feature_seeds['rivers'])
        
        # Determine number of rivers based on density and terrain size
        max_rivers = max(1, int(self.width * self.height * self.river_density / 2000))
        num_rivers = river_rng.randint(1, max_rivers)
        
        # Generate river network with strategic placement
        river_network = self._generate_river_network(river_rng, num_rivers, height_map)
        
        for river in river_network:
            self._place_river(terrain, river)
        
        return terrain
    
    def _generate_river_network(self, rng: random.Random, num_rivers: int, 
                               height_map: List[List[float]]) -> List[Dict]:
        """Generate a coherent river network with strategic placement."""
        rivers = []
        
        # Find suitable starting points (high elevation areas)
        high_points = self._find_high_elevation_points(height_map, 5)
        
        for i in range(num_rivers):
            if not high_points:
                break
                
            # Choose a starting point
            start_point = rng.choice(high_points)
            high_points.remove(start_point)  # Avoid duplicate starts
            
            # Determine river direction based on terrain
            direction = self._determine_river_direction(start_point, height_map, rng)
            
            # Generate river path
            river_path = self._generate_river_path(start_point, direction, height_map, rng)
            
            rivers.append({
                'path': river_path,
                'width': self.river_width,
                'start_point': start_point
            })
        
        return rivers
    
    def _find_high_elevation_points(self, height_map: List[List[float]], num_points: int) -> List[Tuple[int, int]]:
        """Find high elevation points suitable for river sources."""
        high_points = []
        
        for y in range(self.height):
            for x in range(self.width):
                if height_map[y][x] > 0.7:  # High elevation threshold
                    high_points.append((x, y))
        
        # Sort by elevation and return top points
        high_points.sort(key=lambda pos: height_map[pos[1]][pos[0]], reverse=True)
        return high_points[:num_points]
    
    def _determine_river_direction(self, start_point: Tuple[int, int], 
                                  height_map: List[List[float]], rng: random.Random) -> str:
        """Determine the best direction for a river to flow."""
        x, y = start_point
        
        # Check elevation gradients in each direction
        gradients = {}
        
        # Check horizontal flow
        if x < self.width - 1:
            right_gradient = height_map[y][x] - height_map[y][x + 1]
            gradients['east'] = right_gradient
        
        if x > 0:
            left_gradient = height_map[y][x] - height_map[y][x - 1]
            gradients['west'] = left_gradient
        
        # Check vertical flow
        if y < self.height - 1:
            down_gradient = height_map[y][x] - height_map[y + 1][x]
            gradients['south'] = down_gradient
        
        if y > 0:
            up_gradient = height_map[y][x] - height_map[y - 1][x]
            gradients['north'] = up_gradient
        
        # Choose direction with strongest gradient, with some randomness
        if gradients:
            # Weight by gradient strength
            weighted_directions = []
            for direction, gradient in gradients.items():
                weight = max(0.1, gradient + 0.1)  # Ensure positive weight
                weighted_directions.extend([direction] * int(weight * 10))
            
            if weighted_directions:
                return rng.choice(weighted_directions)
        
        # Fallback to random direction
        return rng.choice(['east', 'west', 'south', 'north'])
    
    def _generate_river_path(self, start_point: Tuple[int, int], direction: str,
                            height_map: List[List[float]], rng: random.Random) -> List[Tuple[int, int]]:
        """Generate a river path that follows elevation gradients."""
        path = [start_point]
        current_x, current_y = start_point
        
        # Direction vectors
        direction_vectors = {
            'east': (1, 0),
            'west': (-1, 0),
            'south': (0, 1),
            'north': (0, -1)
        }
        
        dx, dy = direction_vectors[direction]
        
        # Generate path following elevation gradient
        for _ in range(max(self.width, self.height)):  # Maximum path length
            # Move in primary direction
            next_x = current_x + dx
            next_y = current_y + dy
            
            # Check if we can continue in this direction
            if (0 <= next_x < self.width and 0 <= next_y < self.height and
                height_map[next_y][next_x] < height_map[current_y][current_x]):
                current_x, current_y = next_x, next_y
                path.append((current_x, current_y))
            else:
                # Try to find a better direction
                best_direction = self._find_best_river_direction(
                    current_x, current_y, height_map, rng
                )
                if best_direction:
                    dx, dy = direction_vectors[best_direction]
                    next_x = current_x + dx
                    next_y = current_y + dy
                    if (0 <= next_x < self.width and 0 <= next_y < self.height):
                        current_x, current_y = next_x, next_y
                        path.append((current_x, current_y))
                    else:
                        break
                else:
                    break
        
        return path
    
    def _find_best_river_direction(self, x: int, y: int, height_map: List[List[float]], 
                                  rng: random.Random) -> Optional[str]:
        """Find the best direction for river to continue flowing."""
        directions = ['east', 'west', 'south', 'north']
        direction_vectors = {
            'east': (1, 0), 'west': (-1, 0),
            'south': (0, 1), 'north': (0, -1)
        }
        
        valid_directions = []
        
        for direction in directions:
            dx, dy = direction_vectors[direction]
            next_x, next_y = x + dx, y + dy
            
            if (0 <= next_x < self.width and 0 <= next_y < self.height and
                height_map[next_y][next_x] < height_map[y][x]):
                valid_directions.append(direction)
        
        return rng.choice(valid_directions) if valid_directions else None
    
    def _place_river(self, terrain: List[List[TerrainTile]], river: Dict) -> None:
        """Place a single river on the terrain."""
        for x, y in river['path']:
            for dx in range(-river['width'] // 2, river['width'] // 2 + 1):
                for dy in range(-river['width'] // 2, river['width'] // 2 + 1):
                    water_x = x + dx
                    water_y = y + dy
                    if (0 <= water_x < self.width and 0 <= water_y < self.height):
                        terrain[water_y][water_x].terrain_type = TerrainType.WATER
                        terrain[water_y][water_x].features.append("river")
    
    def _generate_meandering_path(self, start: int, end: int, base_coord: int, is_horizontal: bool) -> List[Tuple[int, int]]:
        """Generate a meandering path for rivers."""
        path = []
        current = start
        current_offset = 0
        max_offset = 3
        
        while current <= end:
            if is_horizontal:
                path.append((current, base_coord + current_offset))
            else:
                path.append((base_coord + current_offset, current))
            
            # Add some randomness to the path
            if random.random() < 0.3:
                offset_change = random.randint(-1, 1)
                current_offset = max(-max_offset, min(max_offset, current_offset + offset_change))
            
            current += 1
        
        return path
    
    def _add_ponds(self, terrain: List[List[TerrainTile]], 
                  height_map: List[List[float]], 
                  moisture_map: List[List[float]]) -> List[List[TerrainTile]]:
        """Add ponds to the terrain."""
        num_ponds = random.randint(2, 5)
        
        for _ in range(num_ponds):
            # Find suitable location (low elevation, high moisture)
            best_x, best_y = 0, 0
            best_score = float('inf')
            
            # Try multiple random locations
            for _ in range(10):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                
                # Score based on low elevation and high moisture
                score = height_map[y][x] - moisture_map[y][x]
                if score < best_score:
                    best_score = score
                    best_x, best_y = x, y
            
            # Generate pond
            pond_size = random.randint(self.pond_min_size, self.pond_max_size)
            self._create_pond(terrain, best_x, best_y, pond_size)
        
        return terrain
    
    def _create_pond(self, terrain: List[List[TerrainTile]], center_x: int, center_y: int, size: int):
        """Create a pond at the specified location."""
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                x = center_x + dx
                y = center_y + dy
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Check if within pond radius
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance <= size:
                        terrain[y][x].terrain_type = TerrainType.WATER
                        terrain[y][x].features.append("pond")
    
    def _add_groves(self, terrain: List[List[TerrainTile]], 
                   height_map: List[List[float]], 
                   moisture_map: List[List[float]]) -> List[List[TerrainTile]]:
        """Add groves of trees to the terrain with congruent placement."""
        # Use feature-specific random generator for consistent placement
        grove_rng = random.Random(self.feature_seeds['groves'])
        
        # Determine number of groves based on density and terrain size
        max_groves = max(3, int(self.width * self.height * self.grove_density / 500))
        num_groves = grove_rng.randint(3, max_groves)
        
        # Find suitable locations for groves
        grove_locations = self._find_grove_locations(height_map, moisture_map, num_groves, grove_rng)
        
        for location in grove_locations:
            x, y, size = location
            self._create_grove(terrain, x, y, size, grove_rng)
        
        return terrain
    
    def _find_grove_locations(self, height_map: List[List[float]], 
                             moisture_map: List[List[float]], 
                             num_groves: int, rng: random.Random) -> List[Tuple[int, int, int]]:
        """Find suitable locations for groves based on terrain characteristics."""
        locations = []
        
        # Create a grid of potential locations
        potential_locations = []
        
        for y in range(0, self.height, 5):  # Sample every 5th tile
            for x in range(0, self.width, 5):
                height = height_map[y][x]
                moisture = moisture_map[y][x]
                
                # Score based on suitability for groves
                if 0.2 <= height <= 0.8:  # Moderate elevation
                    score = moisture * (1 - abs(height - 0.5)) * (1 - abs(moisture - 0.6))
                    if score > 0.3:  # Minimum suitability threshold
                        potential_locations.append((x, y, score))
        
        # Sort by score and select best locations
        potential_locations.sort(key=lambda loc: loc[2], reverse=True)
        
        # Select locations ensuring minimum distance between groves
        min_distance = 15  # Minimum distance between grove centers
        
        for x, y, score in potential_locations:
            if len(locations) >= num_groves:
                break
                
            # Check distance from existing groves
            too_close = False
            for existing_x, existing_y, _ in locations:
                distance = math.sqrt((x - existing_x)**2 + (y - existing_y)**2)
                if distance < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                # Determine grove size based on score and random variation
                base_size = self.grove_min_size + int((score - 0.3) * 10)
                size = rng.randint(base_size, min(self.grove_max_size, base_size + 3))
                locations.append((x, y, size))
        
        return locations
    
    def _create_grove(self, terrain: List[List[TerrainTile]], center_x: int, center_y: int, size: int, rng: random.Random):
        """Create a grove of trees at the specified location."""
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                x = center_x + dx
                y = center_y + dy
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Check if within grove radius
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance <= size:
                        # Probability of tree decreases with distance from center
                        tree_prob = 1.0 - (distance / size)
                        tree_prob *= 0.7  # Overall density factor
                        
                        if rng.random() < tree_prob:
                            # Only place trees on suitable terrain
                            if terrain[y][x].terrain_type in [TerrainType.GRASS, TerrainType.DIRT]:
                                terrain[y][x].terrain_type = TerrainType.TREE
                                terrain[y][x].features.append("grove")
    
    def _add_grass_and_shrubs(self, terrain: List[List[TerrainTile]], 
                            height_map: List[List[float]], 
                            moisture_map: List[List[float]]) -> List[List[TerrainTile]]:
        """Add grass and shrubs to suitable areas."""
        for y in range(self.height):
            for x in range(self.width):
                tile = terrain[y][x]
                
                # Only modify grass and dirt tiles
                if tile.terrain_type in [TerrainType.GRASS, TerrainType.DIRT]:
                    # Add shrubs based on moisture
                    if moisture_map[y][x] > 0.6 and random.random() < 0.3:
                        tile.terrain_type = TerrainType.SHRUB
                        tile.features.append("shrub")
                    # Ensure grass areas have grass feature
                    elif tile.terrain_type == TerrainType.GRASS:
                        tile.features.append("grass")
        
        return terrain
    
    def get_terrain_at(self, terrain: List[List[TerrainTile]], x: int, y: int) -> Optional[TerrainTile]:
        """Get terrain tile at specific coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return terrain[y][x]
        return None
    
    def get_terrain_in_radius(self, terrain: List[List[TerrainTile]], 
                            center_x: int, center_y: int, radius: int) -> List[TerrainTile]:
        """Get all terrain tiles within a radius of the center point."""
        tiles = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x = center_x + dx
                y = center_y + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance <= radius:
                        tiles.append(terrain[y][x])
        return tiles
    
    def get_terrain_statistics(self, terrain: List[List[TerrainTile]]) -> Dict[str, int]:
        """Get statistics about the generated terrain."""
        stats = {}
        for row in terrain:
            for tile in row:
                terrain_type = tile.terrain_type.value
                stats[terrain_type] = stats.get(terrain_type, 0) + 1
        return stats
    
    # Efficient terrain generation methods
    def _generate_woodland_efficient(self, terrain: EfficientTerrain, 
                                   height_map: List[List[float]], 
                                   moisture_map: List[List[float]]) -> None:
        """Generate woodland-specific terrain features using efficient storage."""
        for y in range(self.height):
            for x in range(self.width):
                height = height_map[y][x]
                moisture = moisture_map[y][x]
                
                # Determine base terrain type based on height and moisture
                if height < 0.3:
                    # Low areas - more likely to be water or wet grass
                    if moisture > 0.7:
                        terrain.set_terrain_type(x, y, TerrainType.WATER)
                    else:
                        terrain.set_terrain_type(x, y, TerrainType.GRASS)
                elif height < 0.6:
                    # Mid-level areas - grass or dirt
                    if moisture > 0.5:
                        terrain.set_terrain_type(x, y, TerrainType.GRASS)
                    else:
                        terrain.set_terrain_type(x, y, TerrainType.DIRT)
                else:
                    # High areas - more likely to be rocky
                    if moisture < 0.3:
                        terrain.set_terrain_type(x, y, TerrainType.ROCK)
                    else:
                        terrain.set_terrain_type(x, y, TerrainType.DIRT)
                
                # Set elevation, moisture
                terrain.set_elevation(x, y, height)
                terrain.set_moisture(x, y, moisture)
    
    def _add_roads_efficient(self, terrain: EfficientTerrain) -> None:
        """Add road networks to the efficient terrain."""
        num_roads = random.randint(2, 4)
        
        for _ in range(num_roads):
            # Choose road direction
            if random.choice([True, False]):
                # Horizontal road
                y = random.randint(0, self.height - 1)
                start_x = random.randint(0, self.width // 3)
                end_x = random.randint(2 * self.width // 3, self.width - 1)
                
                for x in range(start_x, end_x):
                    for dy in range(-self.road_width // 2, self.road_width // 2 + 1):
                        road_y = y + dy
                        if 0 <= road_y < self.height:
                            terrain.set_terrain_type(x, road_y, TerrainType.ROAD)
                            terrain.add_feature(x, road_y, "road")
            else:
                # Vertical road
                x = random.randint(0, self.width - 1)
                start_y = random.randint(0, self.height // 3)
                end_y = random.randint(2 * self.height // 3, self.height - 1)
                
                for y in range(start_y, end_y):
                    for dx in range(-self.road_width // 2, self.road_width // 2 + 1):
                        road_x = x + dx
                        if 0 <= road_x < self.width:
                            terrain.set_terrain_type(y, road_x, TerrainType.ROAD)
                            terrain.add_feature(y, road_x, "road")
    
    def _add_rivers_efficient(self, terrain: EfficientTerrain, 
                            height_map: List[List[float]]) -> None:
        """Add rivers to the efficient terrain."""
        num_rivers = random.randint(1, 3)
        
        for _ in range(num_rivers):
            # Choose river direction
            if random.choice([True, False]):
                # Horizontal river
                y = random.randint(0, self.height - 1)
                start_x = 0
                end_x = self.width - 1
                
                # Add some meandering
                river_path = self._generate_meandering_path(start_x, end_x, y, True)
                
                for x, river_y in river_path:
                    for dy in range(-self.river_width // 2, self.river_width // 2 + 1):
                        water_y = river_y + dy
                        if 0 <= water_y < self.height and 0 <= x < self.width:
                            terrain.set_terrain_type(x, water_y, TerrainType.WATER)
                            terrain.add_feature(x, water_y, "river")
            else:
                # Vertical river
                x = random.randint(0, self.width - 1)
                start_y = 0
                end_y = self.height - 1
                
                # Add some meandering
                river_path = self._generate_meandering_path(start_y, end_y, x, False)
                
                for y, river_x in river_path:
                    for dx in range(-self.river_width // 2, self.river_width // 2 + 1):
                        water_x = river_x + dx
                        if 0 <= water_x < self.width and 0 <= y < self.height:
                            terrain.set_terrain_type(y, water_x, TerrainType.WATER)
                            terrain.add_feature(y, water_x, "river")
    
    def _add_ponds_efficient(self, terrain: EfficientTerrain, 
                           height_map: List[List[float]], 
                           moisture_map: List[List[float]]) -> None:
        """Add ponds to the efficient terrain."""
        num_ponds = random.randint(2, 5)
        
        for _ in range(num_ponds):
            # Find suitable location (low elevation, high moisture)
            best_x, best_y = 0, 0
            best_score = float('inf')
            
            # Try multiple random locations
            for _ in range(10):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                
                # Score based on low elevation and high moisture
                score = height_map[y][x] - moisture_map[y][x]
                if score < best_score:
                    best_score = score
                    best_x, best_y = x, y
            
            # Generate pond
            pond_size = random.randint(self.pond_min_size, self.pond_max_size)
            self._create_pond_efficient(terrain, best_x, best_y, pond_size)
    
    def _create_pond_efficient(self, terrain: EfficientTerrain, center_x: int, center_y: int, size: int):
        """Create a pond at the specified location using efficient storage."""
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                x = center_x + dx
                y = center_y + dy
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Check if within pond radius
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance <= size:
                        terrain.set_terrain_type(x, y, TerrainType.WATER)
                        terrain.add_feature(x, y, "pond")
    
    def _add_groves_efficient(self, terrain: EfficientTerrain, 
                            height_map: List[List[float]], 
                            moisture_map: List[List[float]]) -> None:
        """Add groves of trees to the efficient terrain with congruent placement."""
        # Use feature-specific random generator for consistent placement
        grove_rng = random.Random(self.feature_seeds['groves'])
        
        # Determine number of groves based on density and terrain size
        max_groves = max(3, int(self.width * self.height * self.grove_density / 500))
        num_groves = grove_rng.randint(3, max_groves)
        
        # Find suitable locations for groves
        grove_locations = self._find_grove_locations(height_map, moisture_map, num_groves, grove_rng)
        
        for location in grove_locations:
            x, y, size = location
            self._create_grove_efficient(terrain, x, y, size, grove_rng)
    
    def _create_grove_efficient(self, terrain: EfficientTerrain, center_x: int, center_y: int, size: int, rng: random.Random):
        """Create a grove of trees at the specified location using efficient storage."""
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                x = center_x + dx
                y = center_y + dy
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Check if within grove radius
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance <= size:
                        # Probability of tree decreases with distance from center
                        tree_prob = 1.0 - (distance / size)
                        tree_prob *= 0.7  # Overall density factor
                        
                        if rng.random() < tree_prob:
                            # Only place trees on suitable terrain
                            current_type = terrain.get_terrain_type(x, y)
                            if current_type in [TerrainType.GRASS, TerrainType.DIRT]:
                                terrain.set_terrain_type(x, y, TerrainType.TREE)
                                terrain.add_feature(x, y, "grove")
    
    def _add_grass_and_shrubs_efficient(self, terrain: EfficientTerrain, 
                                      height_map: List[List[float]], 
                                      moisture_map: List[List[float]]) -> None:
        """Add grass and shrubs to suitable areas using efficient storage."""
        for y in range(self.height):
            for x in range(self.width):
                current_type = terrain.get_terrain_type(x, y)
                moisture = moisture_map[y][x]
                
                # Only modify grass and dirt tiles
                if current_type in [TerrainType.GRASS, TerrainType.DIRT]:
                    # Add shrubs based on moisture
                    if moisture > 0.6 and random.random() < 0.3:
                        terrain.set_terrain_type(x, y, TerrainType.SHRUB)
                        terrain.add_feature(x, y, "shrub")
                    # Ensure grass areas have grass feature
                    elif current_type == TerrainType.GRASS:
                        terrain.add_feature(x, y, "grass")
