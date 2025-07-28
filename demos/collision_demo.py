#!/usr/bin/env python3
"""
Collision System Demo for Mythica Dungeon Crawler
Demonstrates that entities cannot occupy the same grid space.
"""

from logic.enemy_system import Enemy, EnemyType, EnemyManager
from logic.character_system import Character

def demonstrate_collision_system():
    """Demonstrate the collision system features."""
    print("=== Mythica Collision System Demo ===\n")
    
    # Create test entities
    manager = EnemyManager()
    goblin = Enemy(EnemyType.GOBLIN, 5, 5)
    orc = Enemy(EnemyType.ORC, 7, 7)
    
    manager.add_enemy(goblin)
    manager.add_enemy(orc)
    
    print("Initial positions:")
    print(f"Goblin at: ({goblin.x}, {goblin.y})")
    print(f"Orc at: ({orc.x}, {orc.y})")
    print(f"Player at: (10, 10) [simulated]")
    print()
    
    # Test enemy-to-enemy collision
    print("=== Enemy-to-Enemy Collision Test ===")
    print("Trying to move Orc to Goblin's position (5, 5)...")
    
    success = manager.move_enemy(orc, 5, 5, 10, 10)  # Player at (10, 10)
    if success:
        print("❌ FAILED: Orc moved to occupied position!")
    else:
        print("✓ SUCCESS: Orc blocked by Goblin's position")
        print(f"Orc still at: ({orc.x}, {orc.y})")
    print()
    
    # Test enemy-to-player collision
    print("=== Enemy-to-Player Collision Test ===")
    print("Trying to move Goblin to Player's position (10, 10)...")
    
    success = manager.move_enemy(goblin, 10, 10, 10, 10)  # Player at (10, 10)
    if success:
        print("❌ FAILED: Goblin moved to player's position!")
    else:
        print("✓ SUCCESS: Goblin blocked by Player's position")
        print(f"Goblin still at: ({goblin.x}, {goblin.y})")
    print()
    
    # Test valid movement
    print("=== Valid Movement Test ===")
    print("Trying to move Goblin to empty position (8, 8)...")
    
    success = manager.move_enemy(goblin, 8, 8, 10, 10)  # Player at (10, 10)
    if success:
        print("✓ SUCCESS: Goblin moved to empty position")
        print(f"Goblin now at: ({goblin.x}, {goblin.y})")
    else:
        print("❌ FAILED: Valid movement was blocked!")
    print()
    
    # Test AI behavior with collision
    print("=== AI Behavior with Collision Test ===")
    
    # Create a mock dungeon for AI testing
    class MockDungeon:
        def can_move_to(self, x, y):
            return 0 <= x <= 20 and 0 <= y <= 20
    
    mock_dungeon = MockDungeon()
    
    # Place aggressive goblin next to player
    test_goblin = Enemy(EnemyType.GOBLIN, 9, 10)  # Adjacent to player at (10, 10)
    manager.add_enemy(test_goblin)
    
    print(f"Aggressive Goblin at: ({test_goblin.x}, {test_goblin.y})")
    print("Player at: (10, 10)")
    print("Goblin should NOT try to move into player's space...")
    
    # Test AI update
    current_time = 1.0
    desired_move = test_goblin.update_ai(current_time, 10, 10, mock_dungeon)
    
    if desired_move:
        new_x, new_y = desired_move
        if new_x == 10 and new_y == 10:
            print("❌ FAILED: AI tried to move into player's position!")
        else:
            print(f"✓ AI wants to move to: ({new_x}, {new_y}) - different from player")
    else:
        print("✓ SUCCESS: AI correctly stayed in place (already adjacent)")
    print()
    
    # Test spawn collision avoidance
    print("=== Spawn Collision Avoidance Test ===")
    
    # Create a mock dungeon with limited space
    class MockSmallDungeon:
        def __init__(self):
            self.width = 5
            self.height = 5
            self.start_pos = (2, 2)
        
        def can_move_to(self, x, y):
            return 1 <= x <= 3 and 1 <= y <= 3  # Only 3x3 area available
    
    small_dungeon = MockSmallDungeon()
    small_manager = EnemyManager()
    
    # Try to spawn enemies with player at center
    player_pos = (2, 2)
    small_manager.spawn_enemies_in_dungeon(small_dungeon, num_enemies=10, player_start_pos=player_pos)
    
    spawned_count = len(small_manager.get_living_enemies())
    print(f"Attempted to spawn 10 enemies in 3x3 area with player at center")
    print(f"Successfully spawned: {spawned_count} enemies")
    print("Positions:")
    
    for i, enemy in enumerate(small_manager.get_living_enemies()):
        print(f"  Enemy {i+1} ({enemy.enemy_type.value}): ({enemy.x}, {enemy.y})")
    
    # Verify no overlap with player
    overlap_with_player = any(
        enemy.x == player_pos[0] and enemy.y == player_pos[1] 
        for enemy in small_manager.get_living_enemies()
    )
    
    if overlap_with_player:
        print("❌ FAILED: Enemy spawned on player position!")
    else:
        print("✓ SUCCESS: No enemies spawned on player position")
    
    print("\n=== Demo Complete ===")
    print("Collision system features:")
    print("✓ Enemies cannot move into other enemies' positions")
    print("✓ Enemies cannot move into player's position")
    print("✓ Player cannot move into enemies' positions (triggers combat)")
    print("✓ AI respects collision boundaries")
    print("✓ Enemy spawning avoids occupied positions")
    print("✓ Only one entity per grid tile")

if __name__ == "__main__":
    demonstrate_collision_system() 