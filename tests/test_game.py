#!/usr/bin/env python3
"""
Test script for Mythica Dungeon Crawler
Verifies basic functionality and game components.
"""

import sys
import pygame
from main import Game, Dungeon, Player, CellType, LineOfSight
from logic.character_system import Character, StatType, EquipmentSlot, ItemGenerator, ItemType
from logic.enemy_system import Enemy, EnemyType, EnemyManager
from logic.config_manager import ConfigManager
from logic.game_states import CharacterClass, CharacterClassData, GameStateManager
from logic.turn_system import TurnManager, ActionType, ActionCosts, WeaponType

def test_dungeon_generation():
    """Test that dungeon generates properly."""
    print("Testing dungeon generation...")
    dungeon = Dungeon(20, 20)
    
    # Check that start position is valid
    assert dungeon.can_move_to(dungeon.start_pos[0], dungeon.start_pos[1])
    print(f"✓ Start position valid: {dungeon.start_pos}")
    
    # Check that there are both walls and floors
    wall_count = 0
    floor_count = 0
    
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            cell = dungeon.get_cell(x, y)
            if cell == CellType.WALL:
                wall_count += 1
            elif cell == CellType.FLOOR:
                floor_count += 1
    
    assert wall_count > 0, "No walls found in dungeon"
    assert floor_count > 0, "No floors found in dungeon"
    print(f"✓ Dungeon has {wall_count} walls and {floor_count} floors")

def test_player_movement():
    """Test player movement mechanics."""
    print("Testing player movement...")
    dungeon = Dungeon(10, 10)
    player = Player(5, 5)
    
    # Test valid movement
    if dungeon.can_move_to(6, 5):
        player.move(1, 0)
        assert player.get_position() == (6, 5)
        print("✓ Player movement works correctly")
    else:
        print("✓ Player movement blocked correctly")

def test_line_of_sight():
    """Test line of sight functionality."""
    print("Testing line of sight system...")
    dungeon = Dungeon(10, 10)
    
    # Test visibility calculation
    visible_tiles = LineOfSight.get_visible_tiles(5, 5, dungeon, 3)
    
    # Player should always see their own position
    assert (5, 5) in visible_tiles
    print("✓ Player can see their own position")
    
    # Should have some visible tiles
    assert len(visible_tiles) > 1
    print(f"✓ Line of sight calculates {len(visible_tiles)} visible tiles")

def test_character_system():
    """Test character stats and equipment system."""
    print("Testing character system...")
    
    # Test character creation
    character = Character("Test Hero")
    assert character.name == "Test Hero"
    assert character.level == 1
    print("✓ Character creation works")
    
    # Test stats
    perception = character.stats.get_total_stat(StatType.PERCEPTION)
    assert perception >= 8  # Minimum stat value
    print(f"✓ Character has {perception} perception")
    
    # Test sight range calculation
    sight_range = character.get_sight_range()
    assert sight_range >= 6  # Base sight range
    print(f"✓ Character sight range: {sight_range}")
    
    # Test equipment
    equipment_summary = character.equipment.get_equipment_summary()
    assert len(equipment_summary) == 8  # All equipment slots
    print("✓ Equipment system works")
    
    # Test item generation
    sword = ItemGenerator.generate_random_item(ItemType.WEAPON)
    assert sword.item_type == ItemType.WEAPON
    print(f"✓ Generated item: {sword.name}")
    
    # Test HP system
    assert character.current_hp > 0
    assert character.max_hp > 0
    print(f"✓ Character has {character.current_hp}/{character.max_hp} HP")

def test_enemy_system():
    """Test enemy creation and combat system."""
    print("Testing enemy system...")
    
    # Test enemy creation
    goblin = Enemy(EnemyType.GOBLIN, 5, 5)
    assert goblin.enemy_type == EnemyType.GOBLIN
    assert goblin.is_alive
    print("✓ Enemy creation works")
    
    # Test enemy stats
    assert goblin.hp > 0
    assert goblin.max_hp > 0
    print(f"✓ Goblin has {goblin.hp}/{goblin.max_hp} HP")
    
    # Test combat damage
    damage = goblin.get_attack_damage()
    assert damage > 0
    print(f"✓ Goblin deals {damage} damage")
    
    # Test enemy manager
    manager = EnemyManager()
    manager.add_enemy(goblin)
    assert len(manager.get_living_enemies()) == 1
    print("✓ Enemy manager works")
    
    # Test collision detection
    assert not manager.move_enemy(goblin, 10, 10, 10, 10)  # Can't move into player
    assert manager.move_enemy(goblin, 6, 6, 10, 10)  # Can move to empty space
    print("✓ Collision detection works")

def test_config_system():
    """Test configuration system."""
    print("Testing configuration system...")
    
    # Test config loading
    config = ConfigManager()
    assert config is not None
    print("✓ Configuration manager created")
    
    # Test movement direction mapping
    pygame.init()  # Need this for key constants
    direction = config.get_movement_direction(pygame.K_KP8)  # Numpad 8 = North
    assert direction == (0, -1)
    print("✓ Numpad movement mapping works")
    
    # Test diagonal movement
    diag_direction = config.get_movement_direction(pygame.K_KP7)  # Numpad 7 = Northwest
    assert diag_direction == (-1, -1)
    print("✓ Diagonal movement mapping works")
    
    # Test action detection
    assert config.is_key_pressed_for_action('character_sheet', pygame.K_c)
    print("✓ Action detection works")
    
    # Test settings
    diagonal_enabled = config.get_bool_setting('Game', 'diagonal_movement_enabled', True)
    assert isinstance(diagonal_enabled, bool)
    print(f"✓ Settings loading works (diagonal: {diagonal_enabled})")

def test_character_classes():
    """Test character class system."""
    print("Testing character class system...")
    
    # Test creating characters of different classes
    warrior = CharacterClassData.create_character(CharacterClass.WARRIOR, "Test Warrior")
    assert warrior.name == "Test Warrior"
    assert warrior.stats.get_total_stat(StatType.STRENGTH) >= 15  # Warrior should be strong
    print("✓ Warrior class creation works")
    
    mage = CharacterClassData.create_character(CharacterClass.MAGE, "Test Mage")
    assert mage.stats.get_total_stat(StatType.PERCEPTION) >= 16  # Mage should be perceptive
    print("✓ Mage class creation works")
    
    # Test that classes have different stats
    warrior_str = warrior.stats.get_total_stat(StatType.STRENGTH)
    mage_str = mage.stats.get_total_stat(StatType.STRENGTH)
    assert warrior_str > mage_str  # Warrior should be stronger than mage
    print("✓ Classes have different stat distributions")
    
    # Test starting equipment
    warrior_summary = warrior.equipment.get_equipment_summary()
    equipped_items = [item for item in warrior_summary.values() if item != "Empty"]
    assert len(equipped_items) > 0  # Should have some starting equipment
    print(f"✓ Starting equipment works (warrior has {len(equipped_items)} items)")

def test_turn_system():
    """Test turn-based system."""
    print("Testing turn-based system...")
    
    # Test turn manager creation
    turn_manager = TurnManager()
    assert turn_manager is not None
    print("✓ Turn manager created")
    
    # Test action costs
    move_cost = ActionCosts.get_movement_cost(10)  # Average dexterity
    assert move_cost == 1.0  # Should be base cost
    print(f"✓ Movement cost calculation works ({move_cost}s)")
    
    fast_move_cost = ActionCosts.get_movement_cost(15)  # High dexterity
    assert fast_move_cost < move_cost  # Should be faster
    print(f"✓ Dexterity affects movement speed ({fast_move_cost}s)")
    
    # Test weapon costs
    sword_cost = ActionCosts.get_attack_cost(WeaponType.SWORD, 10)
    dagger_cost = ActionCosts.get_attack_cost(WeaponType.DAGGER, 10)
    crossbow_cost = ActionCosts.get_attack_cost(WeaponType.CROSSBOW, 10)
    
    assert dagger_cost < sword_cost < crossbow_cost
    print(f"✓ Weapon speed differences work (dagger: {dagger_cost}s, sword: {sword_cost}s, crossbow: {crossbow_cost}s)")
    
    # Test reload times
    bow_reload = ActionCosts.get_reload_cost(WeaponType.BOW, 10)
    crossbow_reload = ActionCosts.get_reload_cost(WeaponType.CROSSBOW, 10)
    sword_reload = ActionCosts.get_reload_cost(WeaponType.SWORD, 10)
    
    assert bow_reload == 0.5
    assert crossbow_reload == 2.0
    assert sword_reload == 0.0  # No reload needed
    print(f"✓ Reload times work (bow: {bow_reload}s, crossbow: {crossbow_reload}s, sword: {sword_reload}s)")
    
    # Test weapon type detection
    assert ActionCosts.get_weapon_type_from_name("Iron Sword") == WeaponType.SWORD
    assert ActionCosts.get_weapon_type_from_name("Hunter's Bow") == WeaponType.BOW
    assert ActionCosts.get_weapon_type_from_name("Steel Dagger") == WeaponType.DAGGER
    print("✓ Weapon type detection works")

def test_pygame_initialization():
    """Test that pygame initializes correctly."""
    print("Testing pygame initialization...")
    
    # This should not raise an exception
    pygame.init()
    test_surface = pygame.Surface((100, 100))
    assert test_surface is not None
    print("✓ Pygame initializes correctly")

def main():
    """Run all tests."""
    print("Running Mythica Dungeon Crawler Tests")
    print("=" * 40)
    
    try:
        test_pygame_initialization()
        test_dungeon_generation()
        test_player_movement()
        test_line_of_sight()
        test_character_system()
        test_enemy_system()
        test_config_system()
        test_character_classes()
        test_turn_system()
        
        print("\n" + "=" * 40)
        print("All tests passed! ✓")
        print("The game should run correctly.")
        print("\nTo play the game, run: python main.py")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    
    pygame.quit()

if __name__ == "__main__":
    main() 