#!/usr/bin/env python3
"""
Enemy System Demo for Mythica Dungeon Crawler
Demonstrates the enemy types, AI behaviors, and combat mechanics.
"""

from logic.enemy_system import Enemy, EnemyType, EnemyManager, EnemyBehavior
from logic.character_system import Character
import time

def demonstrate_enemy_system():
    """Demonstrate the enemy system features."""
    print("=== Mythica Enemy System Demo ===\n")
    
    # Create different enemy types
    enemies = {}
    for enemy_type in EnemyType:
        enemy = Enemy(enemy_type, 10, 10)  # All at same position for demo
        enemies[enemy_type] = enemy
        
        print(f"=== {enemy_type.value} ===")
        print(f"HP: {enemy.hp}/{enemy.max_hp}")
        print(f"Strength: {enemy.strength}")
        print(f"Dexterity: {enemy.dexterity}")
        print(f"Constitution: {enemy.constitution}")
        print(f"Perception: {enemy.perception}")
        print(f"Behavior: {enemy.behavior.value}")
        print(f"Move Speed: {enemy.move_cooldown:.2f}s cooldown")
        print(f"Experience Value: {enemy.exp_value}")
        print(f"Attack Damage: {enemy.get_attack_damage()}")
        print()
    
    # Demonstrate combat
    print("=== Combat Demonstration ===")
    
    # Create a hero for combat testing
    hero = Character("Test Hero")
    goblin = Enemy(EnemyType.GOBLIN, 5, 5)
    
    print(f"Hero: {hero.current_hp}/{hero.max_hp} HP, Attack: {hero.get_attack_damage()}")
    print(f"Goblin: {goblin.hp}/{goblin.max_hp} HP, Attack: {goblin.get_attack_damage()}")
    print()
    
    # Simulate a fight
    round_num = 1
    while hero.is_alive() and goblin.is_alive():
        print(f"Round {round_num}:")
        
        # Hero attacks first
        hero_damage = hero.get_attack_damage()
        goblin_died = goblin.take_damage(hero_damage)
        print(f"  Hero deals {hero_damage} damage to Goblin")
        print(f"  Goblin HP: {goblin.hp}/{goblin.max_hp}")
        
        if goblin_died:
            print(f"  Goblin defeated! Hero gains {goblin.exp_value} experience.")
            break
        
        # Goblin counter-attacks
        goblin_damage = goblin.get_attack_damage()
        hero_died = hero.take_damage(goblin_damage)
        print(f"  Goblin deals {goblin_damage} damage to Hero")
        print(f"  Hero HP: {hero.current_hp}/{hero.max_hp}")
        
        if hero_died:
            print("  Hero defeated!")
            break
        
        print()
        round_num += 1
        
        # Safety check for infinite combat
        if round_num > 20:
            print("  Combat too long, ending demo...")
            break
    
    # Demonstrate AI behaviors
    print("\n=== AI Behavior Demonstration ===")
    
    # Create a simple mock dungeon for AI testing
    class MockDungeon:
        def can_move_to(self, x, y):
            # Simple bounds check
            return 0 <= x <= 20 and 0 <= y <= 20
    
    mock_dungeon = MockDungeon()
    
    # Test different enemy behaviors
    behaviors_to_test = [
        (EnemyType.RAT, "Patrol behavior - moves randomly"),
        (EnemyType.GOBLIN, "Aggressive behavior - chases player"),
        (EnemyType.SKELETON, "Guard behavior - attacks when close"),
        (EnemyType.TROLL, "Guard behavior - slow but strong")
    ]
    
    for enemy_type, description in behaviors_to_test:
        print(f"\n{enemy_type.value}: {description}")
        enemy = Enemy(enemy_type, 10, 10)
        
        # Simulate AI updates
        player_x, player_y = 12, 12  # Player nearby
        current_time = 0.0
        
        for i in range(3):
            current_time += 1.0  # Advance time
            desired_move = enemy.update_ai(current_time, player_x, player_y, mock_dungeon)
            
            if desired_move:
                new_x, new_y = desired_move
                old_x, old_y = enemy.x, enemy.y
                enemy.move_to(new_x, new_y)
                print(f"  Move {i+1}: ({old_x}, {old_y}) -> ({new_x}, {new_y})")
            else:
                print(f"  Move {i+1}: No movement")
    
    # Demonstrate enemy manager
    print("\n=== Enemy Manager Demonstration ===")
    
    manager = EnemyManager()
    
    # Add various enemies
    test_enemies = [
        Enemy(EnemyType.RAT, 5, 5),
        Enemy(EnemyType.GOBLIN, 7, 7),
        Enemy(EnemyType.SKELETON, 9, 9)
    ]
    
    for enemy in test_enemies:
        manager.add_enemy(enemy)
        print(f"Added {enemy.enemy_type.value} at ({enemy.x}, {enemy.y})")
    
    print(f"\nTotal living enemies: {len(manager.get_living_enemies())}")
    
    # Test enemy positioning
    enemy_at_5_5 = manager.get_enemy_at(5, 5)
    if enemy_at_5_5:
        print(f"Enemy at (5, 5): {enemy_at_5_5.enemy_type.value}")
    
    # Test range finding
    enemies_near_7_7 = manager.get_enemies_in_range(7, 7, 3)
    print(f"Enemies within 3 tiles of (7, 7): {len(enemies_near_7_7)}")
    
    print("\n=== Demo Complete ===")
    print("Enemy system features:")
    print("✓ 6 different enemy types with unique stats")
    print("✓ 4 different AI behavior patterns")
    print("✓ Constitution-based health system")
    print("✓ Strength-based combat damage")
    print("✓ Experience point rewards")
    print("✓ Smart enemy positioning and management")
    print("✓ Real-time AI updates and movement")

if __name__ == "__main__":
    demonstrate_enemy_system() 