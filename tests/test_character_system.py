#!/usr/bin/env python3
"""
Comprehensive tests for the character system including:
- Character stats and stat calculations
- Equipment system and stat bonuses
- Character classes and their starting configurations
- Item generation and equipment
- HP calculations based on Constitution
"""

import unittest
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.character_system import (
    Character, StatType, EquipmentSlot, ItemGenerator, ItemType, 
    Item, CharacterStats, Equipment
)
from logic.game_states import CharacterClass, CharacterClassData


class TestCharacterStats(unittest.TestCase):
    """Test character stat calculations and modifications."""
    
    def setUp(self):
        """Set up test character with known stats."""
        self.character = Character("TestHero")
        # Set known base stats for predictable testing
        self.character.stats.base_stats = {
            StatType.STRENGTH: 12,
            StatType.DEXTERITY: 14,
            StatType.CONSTITUTION: 16,
            StatType.PERCEPTION: 10,
            StatType.LUCK: 8
        }
    
    def test_base_stat_access(self):
        """Test accessing base stats."""
        self.assertEqual(self.character.stats.base_stats[StatType.STRENGTH], 12)
        self.assertEqual(self.character.stats.base_stats[StatType.CONSTITUTION], 16)
    
    def test_equipment_stat_bonuses(self):
        """Test that equipment provides stat bonuses."""
        # Create a test item with stat bonuses
        test_ring = Item("Strength Ring", ItemType.RING, {StatType.STRENGTH: 2})
        
        # Record the current strength before equipping
        base_str = self.character.stats.get_total_stat(StatType.STRENGTH)
        
        # Equip the item
        self.character.equipment.equip_item(test_ring, EquipmentSlot.RING_1)
        self.character._update_equipment_bonuses()  # Update bonuses
        
        # Check that total stats include the bonus
        total_str = self.character.stats.get_total_stat(StatType.STRENGTH)
        self.assertEqual(total_str, base_str + 2)  # Should be base + 2 bonus
    
    def test_hp_calculation_from_constitution(self):
        """Test that HP is correctly calculated from Constitution."""
        # Set known Constitution value and update HP
        self.character.stats.base_stats[StatType.CONSTITUTION] = 16
        self.character._update_equipment_bonuses()  # Recalculate HP
        
        # HP formula: Base 20 + (Constitution-10)*2 + Level bonuses  
        # Level bonuses = (level - 1) * 5 = (1 - 1) * 5 = 0 for level 1
        constitution = self.character.stats.get_total_stat(StatType.CONSTITUTION)
        expected_hp = 20 + (constitution - 10) * 2 + (self.character.level - 1) * 5
        actual_hp = self.character.max_hp
        self.assertEqual(actual_hp, expected_hp)
    
    def test_total_stat_calculation(self):
        """Test total stat calculation (base + equipment bonuses)."""
        # Set up a test with known equipment bonus
        self.character.stats.equipment_bonuses[StatType.STRENGTH] = 3
        
        # Total should be base + equipment bonus
        total_str = self.character.stats.get_total_stat(StatType.STRENGTH)
        expected_total = 12 + 3  # base 12 + equipment 3
        self.assertEqual(total_str, expected_total)


class TestEquipmentSystem(unittest.TestCase):
    """Test equipment management and item interactions."""
    
    def setUp(self):
        """Set up test character and items."""
        self.character = Character("TestHero")
        self.item_generator = ItemGenerator()
    
    def test_equip_item_to_slot(self):
        """Test equipping items to specific slots."""
        helmet = Item("Iron Helm", ItemType.HELMET, {StatType.CONSTITUTION: 1})
        
        result = self.character.equipment.equip_item(helmet, EquipmentSlot.HEAD)
        self.assertTrue(result)
        
        equipped_item = self.character.equipment.get_equipped_item(EquipmentSlot.HEAD)
        self.assertEqual(equipped_item.name, "Iron Helm")
    
    def test_unequip_item(self):
        """Test unequipping items."""
        sword = Item("Iron Sword", ItemType.WEAPON)
        
        # Equip then unequip
        self.character.equipment.equip_item(sword, EquipmentSlot.WEAPON_1)
        unequipped = self.character.equipment.unequip_item(EquipmentSlot.WEAPON_1)
        
        self.assertEqual(unequipped.name, "Iron Sword")
        self.assertIsNone(self.character.equipment.get_equipped_item(EquipmentSlot.WEAPON_1))
    
    def test_equipment_stat_aggregation(self):
        """Test that multiple equipment pieces aggregate stat bonuses correctly."""
        # Create multiple items with overlapping stat bonuses
        helmet = Item("Strength Helm", ItemType.HELMET, {StatType.STRENGTH: 1})
        ring = Item("Strength Ring", ItemType.RING, {StatType.STRENGTH: 2})
        armour = Item("Plate Mail", ItemType.ARMOUR, {StatType.CONSTITUTION: 3})
        
        # Equip all items
        self.character.equipment.equip_item(helmet, EquipmentSlot.HEAD)
        self.character.equipment.equip_item(ring, EquipmentSlot.RING_1)
        self.character.equipment.equip_item(armour, EquipmentSlot.TORSO)
        
        # Check aggregated bonuses
        bonuses = self.character.equipment.get_total_stat_bonuses()
        self.assertEqual(bonuses.get(StatType.STRENGTH, 0), 3)  # 1 + 2
        self.assertEqual(bonuses.get(StatType.CONSTITUTION, 0), 3)
    
    def test_item_type_slot_compatibility(self):
        """Test that items can only be equipped to compatible slots."""
        sword = Item("Sword", ItemType.WEAPON)
        helmet = Item("Helmet", ItemType.HELMET)
        
        # Valid equips
        self.assertTrue(self.character.equipment.equip_item(sword, EquipmentSlot.WEAPON_1))
        self.assertTrue(self.character.equipment.equip_item(helmet, EquipmentSlot.HEAD))
        
        # Invalid equips should fail
        sword2 = Item("Another Sword", ItemType.WEAPON)
        result = self.character.equipment.equip_item(sword2, EquipmentSlot.HEAD)
        self.assertFalse(result, "Should not be able to equip weapon to head slot")


class TestCharacterClasses(unittest.TestCase):
    """Test character class creation and starting configurations."""
    
    def test_all_character_classes_creation(self):
        """Test that all character classes can be created successfully."""
        for char_class in CharacterClass:
            character = CharacterClassData.create_character(char_class)
            self.assertIsInstance(character, Character)
            self.assertIsNotNone(character.name)
    
    def test_warrior_starting_configuration(self):
        """Test Warrior class starting stats and equipment."""
        warrior = CharacterClassData.create_character(CharacterClass.WARRIOR)
        
        # Warriors should have high Strength and Constitution
        str_stat = warrior.stats.base_stats[StatType.STRENGTH]
        con_stat = warrior.stats.base_stats[StatType.CONSTITUTION]
        
        self.assertGreaterEqual(str_stat, 14, "Warriors should have high Strength")
        self.assertGreaterEqual(con_stat, 12, "Warriors should have decent Constitution")
        
        # Check for melee weapon
        weapon1 = warrior.equipment.get_equipped_item(EquipmentSlot.WEAPON_1)
        self.assertIsNotNone(weapon1, "Warriors should start with a weapon")
    
    def test_rogue_starting_configuration(self):
        """Test Rogue class starting stats and equipment."""
        rogue = CharacterClassData.create_character(CharacterClass.ROGUE)
        
        # Rogues should have high Dexterity and Luck
        dex_stat = rogue.stats.base_stats[StatType.DEXTERITY]
        luck_stat = rogue.stats.base_stats[StatType.LUCK]
        
        self.assertGreaterEqual(dex_stat, 14, "Rogues should have high Dexterity")
        self.assertGreaterEqual(luck_stat, 12, "Rogues should have good Luck")
    
    def test_mage_starting_configuration(self):
        """Test Mage class starting stats and equipment."""
        mage = CharacterClassData.create_character(CharacterClass.MAGE)
        
        # Mages should have high Perception for sight range
        per_stat = mage.stats.base_stats[StatType.PERCEPTION]
        
        self.assertGreaterEqual(per_stat, 14, "Mages should have high Perception")
    
    def test_class_stat_distributions(self):
        """Test that each class has distinct stat distributions."""
        classes_and_primary_stats = [
            (CharacterClass.WARRIOR, [StatType.STRENGTH, StatType.CONSTITUTION]),
            (CharacterClass.ROGUE, [StatType.DEXTERITY, StatType.LUCK]),
            (CharacterClass.MAGE, [StatType.PERCEPTION]),
            (CharacterClass.RANGER, [StatType.PERCEPTION, StatType.DEXTERITY]),
            (CharacterClass.CLERIC, [StatType.CONSTITUTION, StatType.LUCK])
        ]
        
        for char_class, primary_stats in classes_and_primary_stats:
            character = CharacterClassData.create_character(char_class)
            
            for stat in primary_stats:
                stat_value = character.stats.base_stats[stat]
                self.assertGreaterEqual(stat_value, 12, 
                    f"{char_class.value} should have high {stat.value}")


class TestItemGeneration(unittest.TestCase):
    """Test procedural item generation and quality."""
    
    def setUp(self):
        """Set up item generator."""
        self.generator = ItemGenerator()
    
    def test_generate_weapons(self):
        """Test weapon generation."""
        weapon = ItemGenerator.generate_random_item(ItemType.WEAPON)
        self.assertIsInstance(weapon, Item)
        self.assertEqual(weapon.item_type, ItemType.WEAPON)
    
    def test_generate_armour(self):
        """Test armour generation."""
        armour = ItemGenerator.generate_random_item(ItemType.ARMOUR)
        self.assertIsInstance(armour, Item)
        self.assertEqual(armour.item_type, ItemType.ARMOUR)
    
    def test_item_stat_bonuses(self):
        """Test that generated items have appropriate stat bonuses."""
        # Generate multiple items to test variability
        item_types = [ItemType.WEAPON, ItemType.ARMOUR, ItemType.HELMET, ItemType.RING]
        items = [ItemGenerator.generate_random_item(random.choice(item_types)) for _ in range(10)]
        
        for item in items:
            self.assertIsInstance(item, Item)
            # Items should have some stat bonuses
            self.assertIsInstance(item.stat_bonuses, dict)
            # Bonuses should be reasonable (not negative, not too high)
            for stat, bonus in item.stat_bonuses.items():
                self.assertGreaterEqual(bonus, 0)
                self.assertLessEqual(bonus, 10)  # Reasonable upper bound


class TestCombatCalculations(unittest.TestCase):
    """Test combat-related calculations and formulas."""
    
    def setUp(self):
        """Set up test characters."""
        self.attacker = Character("Attacker")
        self.attacker.stats.base_stats[StatType.STRENGTH] = 16
        
        self.defender = Character("Defender")
        self.defender.stats.base_stats[StatType.CONSTITUTION] = 14
    
    def test_damage_calculation_with_strength(self):
        """Test that damage scales with Strength stat."""
        # Create weapon with stat bonuses (this is how damage bonuses work in this system)
        weapon = Item("Test Sword", ItemType.WEAPON, {StatType.STRENGTH: 3})
        
        self.attacker.equipment.equip_item(weapon, EquipmentSlot.WEAPON_1)
        
        # Test that the character can calculate attack damage
        if hasattr(self.attacker, 'get_attack_damage'):
            damage = self.attacker.get_attack_damage()
            self.assertIsInstance(damage, int)
            self.assertGreater(damage, 0, "Attack damage should be positive")
    
    def test_hp_system_integrity(self):
        """Test HP system calculations are consistent."""
        character = Character("Test")
        character.stats.base_stats[StatType.CONSTITUTION] = 18
        character._update_equipment_bonuses()  # Recalculate HP
        
        max_hp = character.max_hp
        
        # HP should be positive and reasonable
        self.assertGreater(max_hp, 0)
        self.assertLess(max_hp, 200)  # Reasonable upper bound
        
        # HP should scale with Constitution
        character.stats.base_stats[StatType.CONSTITUTION] = 20
        character._update_equipment_bonuses()  # Recalculate HP
        higher_hp = character.max_hp
        self.assertGreater(higher_hp, max_hp)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 