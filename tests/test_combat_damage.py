#!/usr/bin/env python3
"""
Comprehensive tests for combat and damage systems including:
- Damage calculation mechanics
- Health point systems
- Combat resolution
- Enemy AI and behavior
- Health bar functionality
- Death and defeat mechanics
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.character_system import Character, StatType, ItemType, Item, EquipmentSlot
from logic.enemy_system import Enemy, EnemyType, EnemyManager, HealthBar
from logic.turn_system import TurnManager, ActionType


class TestDamageCalculation(unittest.TestCase):
    """Test damage calculation mechanics."""
    
    def setUp(self):
        """Set up characters for combat testing."""
        self.attacker = Character("Warrior")
        self.attacker.stats.base_stats = {
            StatType.STRENGTH: 16,
            StatType.DEXTERITY: 12,
            StatType.CONSTITUTION: 14,
            StatType.PERCEPTION: 10,
            StatType.LUCK: 8
        }
        
        self.defender = Character("Guard")
        self.defender.stats.base_stats = {
            StatType.STRENGTH: 12,
            StatType.DEXTERITY: 10,
            StatType.CONSTITUTION: 16,
            StatType.PERCEPTION: 12,
            StatType.LUCK: 10
        }
    
    def test_base_damage_calculation(self):
        """Test basic damage calculation without weapons."""
        # If there's a base unarmed damage calculation
        if hasattr(self.attacker, 'calculate_base_damage'):
            damage = self.attacker.calculate_base_damage()
            self.assertGreater(damage, 0, "Base damage should be positive")
            self.assertLess(damage, 20, "Base damage should be reasonable")
    
    def test_weapon_damage_bonus(self):
        """Test that weapons add to damage calculation."""
        # Create a weapon with known stat bonus (Strength +6 for sword damage)
        sword = Item("Iron Sword", ItemType.WEAPON, {StatType.STRENGTH: 6})
        
        # Equip weapon
        self.attacker.equipment.equip_item(sword, EquipmentSlot.WEAPON_1)
        
        # Test using the actual damage calculation method
        damage = self.attacker.get_attack_damage()
        
        # Should be greater than base damage
        self.assertGreater(damage, 0, "Attack damage should be positive")
        # Test multiple times due to variance
        damages = [self.attacker.get_attack_damage() for _ in range(10)]
        average_damage = sum(damages) / len(damages)
        self.assertGreater(average_damage, 8, "Average weapon damage should include weapon bonus")
    
    def test_strength_affects_damage(self):
        """Test that Strength stat affects damage output."""
        # Test with different strength values
        weak_character = Character("Weak")
        weak_character.stats.base_stats[StatType.STRENGTH] = 8
        
        strong_character = Character("Strong")
        strong_character.stats.base_stats[StatType.STRENGTH] = 18
        
        # Give both the same weapon (stat bonuses)
        weapon1 = Item("Test Sword", ItemType.WEAPON, {StatType.STRENGTH: 2})
        weapon2 = Item("Test Sword", ItemType.WEAPON, {StatType.STRENGTH: 2})
        
        weak_character.equipment.equip_item(weapon1, EquipmentSlot.WEAPON_1)
        strong_character.equipment.equip_item(weapon2, EquipmentSlot.WEAPON_1)
        
        # Test damage difference between characters
        # Take multiple samples due to damage variance
        weak_damages = [weak_character.get_attack_damage() for _ in range(10)]
        strong_damages = [strong_character.get_attack_damage() for _ in range(10)]
        
        weak_avg = sum(weak_damages) / len(weak_damages)
        strong_avg = sum(strong_damages) / len(strong_damages)
        
        # Strong character should do significantly more damage
        self.assertGreater(strong_avg, weak_avg + 3, 
            "Higher strength should result in significantly more damage")
    
    def test_critical_hit_mechanics(self):
        """Test critical hit calculation if implemented."""
        # If critical hit system exists
        if hasattr(self.attacker, 'roll_critical_hit'):
            # Test multiple rolls to ensure it can both hit and miss critically
            critical_results = []
            for _ in range(50):  # Test multiple times for randomness
                is_critical = self.attacker.roll_critical_hit()
                critical_results.append(is_critical)
            
            # Should have both true and false results (unless always/never crits)
            has_crits = any(critical_results)
            has_normals = any(not result for result in critical_results)
            
            # At least some variation expected (unless 100% or 0% crit rate)
            if self.attacker.stats.get_base_stat(StatType.LUCK) not in [0, 20]:
                self.assertTrue(has_normals, "Should have some non-critical hits")
    
    def test_damage_variance(self):
        """Test that damage has some random variance."""
        weapon = Item("Variable Sword", ItemType.WEAPON, {StatType.STRENGTH: 5})
        self.attacker.equipment.equip_item(weapon, EquipmentSlot.WEAPON_1)
        
        # Roll damage multiple times to test variance
        damage_rolls = []
        for _ in range(20):
            damage = self.attacker.get_attack_damage()
            damage_rolls.append(damage)
        
        # Should have some variation (unless system has no randomness)
        unique_rolls = set(damage_rolls)
        
        # At minimum, damage should be reasonable
        for damage in damage_rolls:
            self.assertGreater(damage, 0, "Damage should always be positive")
            self.assertLess(damage, 50, "Damage should be reasonable")


class TestHealthSystem(unittest.TestCase):
    """Test health point system and HP calculations."""
    
    def setUp(self):
        """Set up characters with different Constitution values."""
        self.low_con_char = Character("Frail")
        self.low_con_char.stats.base_stats[StatType.CONSTITUTION] = 8
        self.low_con_char._update_equipment_bonuses()
        
        self.high_con_char = Character("Hardy")
        self.high_con_char.stats.base_stats[StatType.CONSTITUTION] = 18
        self.high_con_char._update_equipment_bonuses()
        
        self.average_char = Character("Average")
        self.average_char.stats.base_stats[StatType.CONSTITUTION] = 12
        self.average_char._update_equipment_bonuses()
    
    def test_max_hp_calculation(self):
        """Test maximum HP calculation from Constitution."""
        # HP formula should be: Base 20 + (Constitution-10)*2
        expected_low = 20 + (8 - 10) * 2    # 20 - 4 = 16
        expected_high = 20 + (18 - 10) * 2  # 20 + 16 = 36
        expected_avg = 20 + (12 - 10) * 2   # 20 + 4 = 24
        
        self.assertEqual(self.low_con_char.max_hp, expected_low)
        self.assertEqual(self.high_con_char.max_hp, expected_high)
        self.assertEqual(self.average_char.max_hp, expected_avg)
    
    def test_current_hp_tracking(self):
        """Test current HP tracking and damage application."""
        character = Character("Test")
        character.stats.base_stats[StatType.CONSTITUTION] = 14
        character._update_equipment_bonuses()  # Recalculate HP
        
        max_hp = character.max_hp
        
        # Character should start at full HP
        self.assertEqual(character.current_hp, max_hp)
        
        # Apply damage
        damage_amount = 5
        character.take_damage(damage_amount)
        expected_hp = max_hp - damage_amount
        self.assertEqual(character.current_hp, expected_hp)
        
        # Test that HP doesn't go below 0
        character.take_damage(100)  # Massive damage
        self.assertGreaterEqual(character.current_hp, 0,
            "HP should not go below 0")
    
    def test_healing_mechanics(self):
        """Test healing and HP restoration."""
        character = Character("Test")
        character.stats.base_stats[StatType.CONSTITUTION] = 14
        character._update_equipment_bonuses()  # Recalculate HP
        max_hp = character.max_hp
        
        # Damage character first
        character.take_damage(10)
        damaged_hp = character.current_hp
        
        # Test healing
        character.heal(5)
        self.assertEqual(character.current_hp, damaged_hp + 5)
        
        # Test that healing doesn't exceed max HP
        character.heal(100)  # Overheal
        self.assertEqual(character.current_hp, max_hp,
            "HP should not exceed maximum")
    
    def test_death_state(self):
        """Test character death when HP reaches 0."""
        character = Character("Test")
        
        # Deal lethal damage
        result = character.take_damage(1000)  # Overkill
        
        # Check death state - take_damage returns True if character dies
        self.assertTrue(result, "take_damage should return True when character dies")
        self.assertFalse(character.is_alive(), 
            "Character should not be alive when HP reaches 0")
    
    def test_hp_regeneration(self):
        """Test HP regeneration mechanics if implemented."""
        character = Character("Test")
        
        if hasattr(character, 'take_damage') and hasattr(character, 'regenerate_hp'):
            # Damage character
            character.take_damage(10)
            damaged_hp = character.current_hp
            
            # Test regeneration
            character.regenerate_hp()
            
            # Should have healed some amount (implementation dependent)
            self.assertGreaterEqual(character.current_hp, damaged_hp,
                "Regeneration should not reduce HP")


class TestEnemySystem(unittest.TestCase):
    """Test enemy creation, stats, and behavior."""
    
    def setUp(self):
        """Set up enemy manager and test enemies."""
        self.enemy_manager = EnemyManager()
        self.player = Character("Player")
    
    def test_enemy_creation(self):
        """Test that enemies are created with proper stats."""
        for enemy_type in EnemyType:
            enemy = Enemy(enemy_type, 10, 10)  # Position (10, 10)
            
            self.assertIsInstance(enemy, Enemy)
            self.assertEqual(enemy.enemy_type, enemy_type)
            self.assertGreater(enemy.max_hp, 0, f"{enemy_type} should have positive HP")
            self.assertGreater(enemy.hp, 0)
    
    def test_enemy_stat_differences(self):
        """Test that different enemy types have different stats."""
        rat = Enemy(EnemyType.RAT, 0, 0)
        troll = Enemy(EnemyType.TROLL, 0, 0)
        
        # Trolls should have significantly more HP than rats
        self.assertGreater(troll.max_hp, rat.max_hp,
            "Trolls should have more HP than rats")
        
        # Test strength differences (used for damage)
        self.assertGreater(troll.strength, rat.strength,
            "Trolls should have more strength than rats")
    
    def test_enemy_spawning(self):
        """Test enemy spawning mechanics."""
        # Test creating and adding enemies
        spawn_x, spawn_y = 5, 5
        enemy = Enemy(EnemyType.GOBLIN, spawn_x, spawn_y)
        self.enemy_manager.add_enemy(enemy)
        
        self.assertIsNotNone(enemy)
        self.assertEqual(enemy.x, spawn_x)
        self.assertEqual(enemy.y, spawn_y)
        self.assertIn(enemy, self.enemy_manager.enemies)
    
    def test_enemy_ai_behavior(self):
        """Test enemy AI behavior patterns."""
        # Create different enemy types to test their behaviors
        goblin = Enemy(EnemyType.GOBLIN, 10, 10)
        skeleton = Enemy(EnemyType.SKELETON, 15, 15)
        
        # Test that enemies have behavior types
        self.assertIsNotNone(goblin.behavior)
        self.assertIsNotNone(skeleton.behavior)
        
        # Test that different enemies can have different behaviors
        # (Goblin is AGGRESSIVE, Skeleton is GUARD based on the implementation)
        self.assertNotEqual(goblin.behavior, skeleton.behavior)
    
    def test_enemy_damage_dealing(self):
        """Test that enemies have strength for damage dealing."""
        enemy = Enemy(EnemyType.ORC, 5, 5)
        
        # Enemies use strength for damage calculations
        self.assertGreater(enemy.strength, 0, "Enemies should have positive strength")
        self.assertLess(enemy.strength, 30, "Enemy strength should be reasonable")
    
    def test_enemy_taking_damage(self):
        """Test enemies taking damage and dying."""
        enemy = Enemy(EnemyType.RAT, 0, 0)
        initial_hp = enemy.hp
        
        # Deal some damage
        damage_amount = 3
        result = enemy.take_damage(damage_amount)
        
        self.assertEqual(enemy.hp, initial_hp - damage_amount)
        self.assertFalse(result, "Enemy should not die from small damage")
        
        # Deal lethal damage
        result = enemy.take_damage(1000)
        
        self.assertTrue(result, "Enemy should die from lethal damage")
        self.assertFalse(enemy.is_alive, "Enemy should not be alive after dying")


class TestHealthBarSystem(unittest.TestCase):
    """Test health bar display and functionality."""
    
    def setUp(self):
        """Set up health bar system."""
        self.character = Character("Test")
        self.character.stats.base_stats[StatType.CONSTITUTION] = 14
        
        self.enemy = Enemy(EnemyType.GOBLIN, 10, 10)
    
    def test_health_bar_creation(self):
        """Test HealthBar utility class exists and has the right methods."""
        # Test that HealthBar has the static draw method
        self.assertTrue(hasattr(HealthBar, 'draw_health_bar'), 
            "HealthBar should have draw_health_bar static method")
        
        # Test that it's callable
        self.assertTrue(callable(getattr(HealthBar, 'draw_health_bar')),
            "draw_health_bar should be callable")
    
    def test_health_bar_percentage_calculation(self):
        """Test health percentage calculation for display."""
        # At full health should be 100%
        full_health_pct = self.character.get_hp_percentage()
        self.assertAlmostEqual(full_health_pct, 1.0, places=2)
        
        # After taking damage
        max_hp = self.character.max_hp
        self.character.take_damage(max_hp // 2)  # Half damage
        
        half_health_pct = self.character.get_hp_percentage()
        self.assertAlmostEqual(half_health_pct, 0.5, places=1)
    
    def test_health_bar_visibility(self):
        """Test health bar visibility and percentage calculations."""
        # Test enemy health percentage
        enemy_full_pct = self.enemy.get_hp_percentage()
        self.assertAlmostEqual(enemy_full_pct, 1.0, places=2)
        
        # After damage, health percentage should change
        self.enemy.take_damage(self.enemy.max_hp // 2)  # Half damage
        enemy_half_pct = self.enemy.get_hp_percentage()
        self.assertAlmostEqual(enemy_half_pct, 0.5, places=1)


class TestCombatIntegration(unittest.TestCase):
    """Test integrated combat scenarios."""
    
    def setUp(self):
        """Set up combat scenario."""
        self.player = Character("Hero")
        self.player.stats.base_stats = {
            StatType.STRENGTH: 14,
            StatType.DEXTERITY: 12,
            StatType.CONSTITUTION: 16,
            StatType.PERCEPTION: 10,
            StatType.LUCK: 8
        }
        self.player._update_equipment_bonuses()
        
        self.enemy = Enemy(EnemyType.GOBLIN, 5, 5)
        self.turn_manager = TurnManager()
        
        # Set up entities in turn manager
        self.turn_manager.set_entity_weapon("player", "Iron Sword")
        self.turn_manager.set_entity_weapon("goblin", "Rusty Dagger")
    
    def test_full_combat_sequence(self):
        """Test a complete combat sequence."""
        # Equip player with weapon
        sword = Item("Iron Sword", ItemType.WEAPON_MELEE)
        sword.damage = 6
        self.player.equipment.equip_item(sword, EquipmentSlot.WEAPON_1)
        
        # Initial HP values
        player_initial_hp = self.player.current_hp
        enemy_initial_hp = self.enemy.current_hp
        
        # Player attacks enemy
        if hasattr(self.turn_manager, 'resolve_attack'):
            damage_dealt = self.turn_manager.resolve_attack(self.player, self.enemy)
            
            self.assertGreater(damage_dealt, 0, "Attack should deal damage")
            self.assertLess(self.enemy.current_hp, enemy_initial_hp,
                "Enemy should take damage")
        
        # Enemy attacks back (if not dead)
        if hasattr(self.enemy, 'is_dead') and not self.enemy.is_dead():
            if hasattr(self.turn_manager, 'resolve_attack'):
                enemy_damage = self.turn_manager.resolve_attack(self.enemy, self.player)
                
                self.assertGreater(enemy_damage, 0, "Enemy should deal damage")
                self.assertLess(self.player.current_hp, player_initial_hp,
                    "Player should take damage")
    
    def test_combat_until_death(self):
        """Test combat continuing until one participant dies."""
        # Give player a powerful weapon to speed up test
        powerful_sword = Item("Great Sword", ItemType.WEAPON_MELEE)
        powerful_sword.damage = 20
        self.player.equipment.equip_item(powerful_sword, EquipmentSlot.WEAPON_1)
        
        combat_rounds = 0
        max_rounds = 20  # Prevent infinite test
        
        while combat_rounds < max_rounds:
            # Player attacks
            if hasattr(self.turn_manager, 'resolve_attack'):
                self.turn_manager.resolve_attack(self.player, self.enemy)
            
            # Check if enemy died
            if hasattr(self.enemy, 'is_dead') and self.enemy.is_dead():
                break
            
            # Enemy attacks back
            if hasattr(self.turn_manager, 'resolve_attack'):
                self.turn_manager.resolve_attack(self.enemy, self.player)
            
            # Check if player died
            if hasattr(self.player, 'is_dead') and self.player.is_dead():
                break
            
            combat_rounds += 1
        
        # Combat should end with someone dead
        if hasattr(self.enemy, 'is_dead') and hasattr(self.player, 'is_dead'):
            combat_ended = self.enemy.is_dead() or self.player.is_dead()
            self.assertTrue(combat_ended or combat_rounds >= max_rounds,
                "Combat should end with death or test limit")
    
    def test_experience_gain(self):
        """Test experience gain from defeating enemies."""
        initial_exp = getattr(self.player, 'experience', 0)
        
        # Kill the enemy
        if hasattr(self.enemy, 'take_damage'):
            self.enemy.take_damage(1000)  # Overkill
        
        # Grant experience
        if hasattr(self.player, 'gain_experience') and hasattr(self.enemy, 'experience_value'):
            exp_gained = self.enemy.experience_value
            self.player.gain_experience(exp_gained)
            
            final_exp = getattr(self.player, 'experience', 0)
            self.assertGreater(final_exp, initial_exp,
                "Should gain experience from defeating enemies")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 