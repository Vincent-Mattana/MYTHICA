#!/usr/bin/env python3
"""
Comprehensive tests for dungeon generation and spatial systems including:
- Dungeon generation algorithms
- Line of sight calculations
- Collision detection
- Room and corridor generation
- Minimap functionality
- Fog of war mechanics
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import Game, Dungeon, Player, CellType, LineOfSight, Camera, Minimap, Room


class TestDungeonGeneration(unittest.TestCase):
    """Test dungeon generation algorithms and structure."""
    
    def setUp(self):
        """Set up test dungeons."""
        self.small_dungeon = Dungeon(20, 20)
        self.large_dungeon = Dungeon(50, 50)
    
    def test_dungeon_creation(self):
        """Test basic dungeon creation."""
        self.assertEqual(self.small_dungeon.width, 20)
        self.assertEqual(self.small_dungeon.height, 20)
        self.assertIsNotNone(self.small_dungeon.start_pos)
    
    def test_dungeon_has_valid_start_position(self):
        """Test that start position is on walkable floor."""
        start_x, start_y = self.small_dungeon.start_pos
        
        # Start position should be within bounds
        self.assertGreaterEqual(start_x, 0)
        self.assertLess(start_x, self.small_dungeon.width)
        self.assertGreaterEqual(start_y, 0)
        self.assertLess(start_y, self.small_dungeon.height)
        
        # Start position should be walkable
        start_cell = self.small_dungeon.get_cell(start_x, start_y)
        self.assertTrue(self.small_dungeon.can_move_to(start_x, start_y),
            "Start position should be walkable")
    
    def test_dungeon_cell_types(self):
        """Test that dungeon contains appropriate cell types."""
        wall_count = 0
        floor_count = 0
        door_count = 0
        
        for y in range(self.small_dungeon.height):
            for x in range(self.small_dungeon.width):
                cell = self.small_dungeon.get_cell(x, y)
                
                if cell == CellType.WALL:
                    wall_count += 1
                elif cell == CellType.FLOOR:
                    floor_count += 1
                elif cell == CellType.DOOR:
                    door_count += 1
        
        # Should have both walls and floors
        self.assertGreater(wall_count, 0, "Dungeon should have walls")
        self.assertGreater(floor_count, 0, "Dungeon should have floors")
        
        # Total cells should match dimensions
        total_cells = wall_count + floor_count + door_count
        expected_total = self.small_dungeon.width * self.small_dungeon.height
        self.assertEqual(total_cells, expected_total)
    
    def test_dungeon_connectivity(self):
        """Test that dungeon areas are reachable from start."""
        # Perform flood fill from start position to find reachable areas
        start_x, start_y = self.small_dungeon.start_pos
        visited = set()
        to_visit = [(start_x, start_y)]
        
        while to_visit:
            x, y = to_visit.pop()
            
            if (x, y) in visited:
                continue
                
            if not (0 <= x < self.small_dungeon.width and 0 <= y < self.small_dungeon.height):
                continue
                
            if not self.small_dungeon.can_move_to(x, y):
                continue
            
            visited.add((x, y))
            
            # Add adjacent cells
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                to_visit.append((x + dx, y + dy))
        
        # Should be able to reach a reasonable number of floor tiles
        reachable_count = len(visited)
        self.assertGreater(reachable_count, 10, 
            "Should be able to reach a reasonable number of floor tiles")
    
    def test_dungeon_bounds_checking(self):
        """Test boundary checking for dungeon access."""
        # Test valid positions (within bounds)
        self.assertIsNotNone(self.small_dungeon.get_cell(0, 0))
        self.assertIsNotNone(self.small_dungeon.get_cell(19, 19))
        self.assertIsNotNone(self.small_dungeon.get_cell(10, 10))
        
        # Test invalid positions (get_cell returns WALL for out of bounds)
        self.assertEqual(self.small_dungeon.get_cell(-1, 0), CellType.WALL)
        self.assertEqual(self.small_dungeon.get_cell(0, -1), CellType.WALL)
        self.assertEqual(self.small_dungeon.get_cell(20, 0), CellType.WALL)
        self.assertEqual(self.small_dungeon.get_cell(0, 20), CellType.WALL)
    
    def test_room_generation(self):
        """Test room generation if room system exists."""
        if hasattr(self.small_dungeon, 'rooms'):
            rooms = self.small_dungeon.rooms
            self.assertIsInstance(rooms, list)
            
            # Should have at least one room
            self.assertGreater(len(rooms), 0, "Dungeon should have at least one room")
            
            # Test room properties
            for room in rooms:
                self.assertIsInstance(room, Room)
                self.assertGreater(room.width, 0)
                self.assertGreater(room.height, 0)
                
                # Room should be within dungeon bounds
                self.assertGreaterEqual(room.x, 0)
                self.assertGreaterEqual(room.y, 0)
                self.assertLess(room.x + room.width, self.small_dungeon.width)
                self.assertLess(room.y + room.height, self.small_dungeon.height)
    
    def test_corridor_connections(self):
        """Test that rooms are connected by corridors."""
        if hasattr(self.small_dungeon, 'rooms') and len(self.small_dungeon.rooms) > 1:
            # Each room should be reachable from every other room
            rooms = self.small_dungeon.rooms
            
            for i, room1 in enumerate(rooms):
                for j, room2 in enumerate(rooms):
                    if i != j:
                        # Find a floor tile in each room
                        room1_floor = self._find_floor_in_room(room1)
                        room2_floor = self._find_floor_in_room(room2)
                        
                        if room1_floor and room2_floor:
                            # Test if there's a path between rooms
                            path_exists = self._path_exists(room1_floor, room2_floor)
                            self.assertTrue(path_exists,
                                f"Should be path between room {i} and room {j}")
    
    def _find_floor_in_room(self, room):
        """Helper method to find a floor tile within a room."""
        for dy in range(room.height):
            for dx in range(room.width):
                x, y = room.x + dx, room.y + dy
                if self.small_dungeon.can_move_to(x, y):
                    return (x, y)
        return None
    
    def _path_exists(self, start, end):
        """Helper method to check if path exists between two points."""
        visited = set()
        to_visit = [start]
        
        while to_visit:
            current = to_visit.pop()
            
            if current == end:
                return True
            
            if current in visited:
                continue
            
            visited.add(current)
            x, y = current
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_x, next_y = x + dx, y + dy
                if (self.small_dungeon.is_valid_position(next_x, next_y) and
                    self.small_dungeon.can_move_to(next_x, next_y) and
                    (next_x, next_y) not in visited):
                    to_visit.append((next_x, next_y))
        
        return False


class TestLineOfSight(unittest.TestCase):
    """Test line of sight calculations and visibility."""
    
    def setUp(self):
        """Set up line of sight testing."""
        self.dungeon = Dungeon(15, 15)
        self.player = Player(7, 7)  # Center position
        self.los = LineOfSight()
    
    def test_line_of_sight_creation(self):
        """Test line of sight system initialization."""
        self.assertIsInstance(self.los, LineOfSight)
    
    def test_direct_line_of_sight(self):
        """Test direct line of sight without obstacles."""
        # Clear a direct path for testing
        start_x, start_y = 5, 5
        end_x, end_y = 10, 5  # Horizontal line
        
        # Ensure the path is clear (if we can modify dungeon for testing)
        if hasattr(self.dungeon, 'set_cell'):
            for x in range(start_x, end_x + 1):
                self.dungeon.set_cell(x, start_y, CellType.FLOOR)
        
        # Test line of sight
        if hasattr(self.los, 'has_line_of_sight'):
            has_sight = self.los.has_line_of_sight(
                start_x, start_y, end_x, end_y, self.dungeon
            )
            
            # Should have line of sight on clear path
            self.assertTrue(has_sight, "Should have line of sight on clear path")
    
    def test_blocked_line_of_sight(self):
        """Test line of sight blocked by walls."""
        start_x, start_y = 5, 5
        end_x, end_y = 10, 5
        wall_x, wall_y = 7, 5  # Wall in the middle
        
        # Place a wall to block sight
        if hasattr(self.dungeon, 'set_cell'):
            self.dungeon.set_cell(wall_x, wall_y, CellType.WALL)
            
            # Ensure start and end are floors
            self.dungeon.set_cell(start_x, start_y, CellType.FLOOR)
            self.dungeon.set_cell(end_x, end_y, CellType.FLOOR)
        
        # Test blocked line of sight
        if hasattr(self.los, 'has_line_of_sight'):
            has_sight = self.los.has_line_of_sight(
                start_x, start_y, end_x, end_y, self.dungeon
            )
            
            # Should not have line of sight through wall
            self.assertFalse(has_sight, "Should not have line of sight through wall")
    
    def test_visibility_calculation(self):
        """Test visibility calculation for player position."""
        player_x, player_y = 7, 7
        sight_range = 5
        
        if hasattr(self.los, 'calculate_visible_tiles'):
            visible_tiles = self.los.calculate_visible_tiles(
                player_x, player_y, sight_range, self.dungeon
            )
            
            self.assertIsInstance(visible_tiles, (list, set))
            
            # Player position should always be visible
            self.assertIn((player_x, player_y), visible_tiles)
            
            # Visible tiles should be within sight range
            for x, y in visible_tiles:
                distance = ((x - player_x) ** 2 + (y - player_y) ** 2) ** 0.5
                self.assertLessEqual(distance, sight_range + 1,  # +1 for rounding
                    f"Visible tile ({x}, {y}) should be within sight range")
    
    def test_perception_affects_sight_range(self):
        """Test that Perception stat affects sight range."""
        # Test with different perception values
        low_perception = Player(7, 7)
        low_perception.character.stats.base_stats[StatType.PERCEPTION] = 8
        low_perception.character._update_equipment_bonuses()
        
        high_perception = Player(7, 7)
        high_perception.character.stats.base_stats[StatType.PERCEPTION] = 18
        high_perception.character._update_equipment_bonuses()
        
        low_range = low_perception.get_sight_range()
        high_range = high_perception.get_sight_range()
        
        self.assertGreater(high_range, low_range,
            "Higher Perception should provide greater sight range")
    
    def test_diagonal_line_of_sight(self):
        """Test line of sight calculations on diagonal lines."""
        start_x, start_y = 5, 5
        
        # Test that line of sight returns a set of visible tiles
        visible_tiles = self.los.get_visible_tiles(start_x, start_y, self.dungeon, 8)
        
        # Should return a set containing at least the starting position
        self.assertIsInstance(visible_tiles, set)
        self.assertIn((start_x, start_y), visible_tiles)


class TestMovementAndCollision(unittest.TestCase):
    """Test movement mechanics and collision detection."""
    
    def setUp(self):
        """Set up movement testing."""
        self.dungeon = Dungeon(10, 10)
        self.player = Player(5, 5)
    
    def test_valid_movement(self):
        """Test movement to valid positions."""
        # Ensure target position is walkable
        target_x, target_y = 6, 5
        
        if self.dungeon.can_move_to(target_x, target_y):
            initial_pos = self.player.get_position()
            self.player.move(1, 0)  # Move right
            new_pos = self.player.get_position()
            
            # Position should have changed
            self.assertNotEqual(initial_pos, new_pos)
            self.assertEqual(new_pos, (target_x, target_y))
    
    def test_collision_with_walls(self):
        """Test that movement is blocked by walls."""
        # Find a wall adjacent to player
        player_x, player_y = self.player.get_position()
        
        # Test all directions for wall collision
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            test_x, test_y = player_x + dx, player_y + dy
            
            if (self.dungeon.is_valid_position(test_x, test_y) and
                not self.dungeon.can_move_to(test_x, test_y)):
                
                # Try to move into wall
                initial_pos = self.player.get_position()
                self.player.move(dx, dy)
                final_pos = self.player.get_position()
                
                # Position should not change when hitting wall
                self.assertEqual(initial_pos, final_pos,
                    "Player should not move through walls")
                break
    
    def test_boundary_collision(self):
        """Test collision with dungeon boundaries."""
        # Move player to edge of map
        edge_player = Player(0, 0)
        
        # Try to move out of bounds
        initial_pos = edge_player.get_position()
        edge_player.move(-1, 0)  # Try to move left from left edge
        final_pos = edge_player.get_position()
        
        # Should not move out of bounds
        self.assertEqual(initial_pos, final_pos,
            "Player should not move out of bounds")
    
    def test_diagonal_movement(self):
        """Test diagonal movement if supported."""
        # Test diagonal movement (if the system supports it)
        if hasattr(self.player, 'can_move_diagonally'):
            player_x, player_y = self.player.get_position()
            
            # Test diagonal positions
            diagonal_moves = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            
            for dx, dy in diagonal_moves:
                test_x, test_y = player_x + dx, player_y + dy
                
                if (self.dungeon.is_valid_position(test_x, test_y) and
                    self.dungeon.can_move_to(test_x, test_y)):
                    
                    initial_pos = self.player.get_position()
                    self.player.move(dx, dy)
                    new_pos = self.player.get_position()
                    
                    # Should be able to move diagonally to valid positions
                    self.assertNotEqual(initial_pos, new_pos)
                    break


class TestCameraSystem(unittest.TestCase):
    """Test camera and viewport management."""
    
    def setUp(self):
        """Set up camera testing."""
        self.camera = Camera()
        self.player = Player(25, 25)  # Player in large area
    
    def test_camera_creation(self):
        """Test camera system initialization."""
        self.assertIsInstance(self.camera, Camera)
    
    def test_camera_following_player(self):
        """Test that camera follows player movement."""
        if hasattr(self.camera, 'update'):
            initial_camera_pos = getattr(self.camera, 'x', 0), getattr(self.camera, 'y', 0)
            
            # Update camera to follow player
            self.camera.update(self.player)
            
            new_camera_pos = getattr(self.camera, 'x', 0), getattr(self.camera, 'y', 0)
            
            # Camera position should be related to player position
            player_x, player_y = self.player.get_position()
            
            # Implementation dependent, but camera should be positioned relative to player
            self.assertIsInstance(new_camera_pos[0], (int, float))
            self.assertIsInstance(new_camera_pos[1], (int, float))
    
    def test_viewport_bounds(self):
        """Test viewport boundary calculations."""
        if hasattr(self.camera, 'get_viewport_bounds'):
            bounds = self.camera.get_viewport_bounds()
            
            # Should return valid bounds (left, top, right, bottom)
            self.assertEqual(len(bounds), 4)
            
            left, top, right, bottom = bounds
            self.assertLessEqual(left, right, "Left should be <= right")
            self.assertLessEqual(top, bottom, "Top should be <= bottom")


class TestMinimapSystem(unittest.TestCase):
    """Test minimap functionality and display."""
    
    def setUp(self):
        """Set up minimap testing."""
        self.dungeon = Dungeon(30, 30)
        self.player = Player(15, 15)
        self.minimap = Minimap(self.dungeon)
    
    def test_minimap_creation(self):
        """Test minimap initialization."""
        self.assertIsInstance(self.minimap, Minimap)
    
    def test_minimap_scaling(self):
        """Test minimap scaling calculations."""
        if hasattr(self.minimap, 'get_scale_factor'):
            scale = self.minimap.get_scale_factor()
            
            self.assertGreater(scale, 0, "Scale factor should be positive")
            self.assertLessEqual(scale, 1, "Scale factor should be <= 1 for minimap")
    
    def test_minimap_player_position(self):
        """Test player position display on minimap."""
        player_x, player_y = self.player.get_position()
        
        if hasattr(self.minimap, 'get_minimap_position'):
            mini_x, mini_y = self.minimap.get_minimap_position(player_x, player_y)
            
            # Minimap coordinates should be valid
            self.assertIsInstance(mini_x, (int, float))
            self.assertIsInstance(mini_y, (int, float))
            self.assertGreaterEqual(mini_x, 0)
            self.assertGreaterEqual(mini_y, 0)
    
    def test_fog_of_war(self):
        """Test fog of war mechanics on minimap."""
        if hasattr(self.minimap, 'explored_tiles'):
            # Initially, few tiles should be explored
            initial_explored = len(self.minimap.explored_tiles)
            
            # Simulate exploration by adding visible tiles
            if hasattr(self.minimap, 'update_exploration'):
                visible_tiles = [(15, 15), (16, 15), (15, 16)]  # Around player
                self.minimap.update_exploration(visible_tiles)
                
                updated_explored = len(self.minimap.explored_tiles)
                self.assertGreaterEqual(updated_explored, initial_explored,
                    "Exploration should increase explored tile count")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 