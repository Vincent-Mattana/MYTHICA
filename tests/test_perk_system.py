"""
Test suite for the perk system and character leveling mechanics.

Tests cover:
- Experience gain and automatic leveling
- Perk learning and restrictions
- Perk effects on combat and stats
- Class-specific perk trees
- Level-up mechanics and perk points
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.character_system import Character, StatType
from logic.perk_system import PerkSystem, CharacterPerks, PerkCategory, PerkType
from logic.game_states import CharacterClassData, CharacterClass


class TestPerkSystem(unittest.TestCase):
    """Test the core perk system functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.perk_system = PerkSystem()
        self.character = Character("Test Hero")
        self.character.set_character_class(CharacterClass.WARRIOR)
        self.character_perks = CharacterPerks(self.character)
    
    def test_perk_system_initialization(self):
        """Test that perk system initializes correctly."""
        self.assertIsInstance(self.perk_system.perks, dict)
        self.assertGreater(len(self.perk_system.perks), 0)
        
        # Check for universal perks
        self.assertIn("power_attack", self.perk_system.perks)
        self.assertIn("toughness", self.perk_system.perks)
        self.assertIn("keen_senses", self.perk_system.perks)
    
    def test_experience_requirements(self):
        """Test experience requirements for leveling."""
        # Level 1 should require 0 experience
        self.assertEqual(self.perk_system.calculate_experience_required(1), 0)
        
        # Level 2 should require some experience
        level_2_exp = self.perk_system.calculate_experience_required(2)
        self.assertGreater(level_2_exp, 0)
        
        # Higher levels should require more experience
        level_3_exp = self.perk_system.calculate_experience_required(3)
        self.assertGreater(level_3_exp, level_2_exp)
    
    def test_level_up_mechanics(self):
        """Test automatic level-up functionality."""
        # Character starts at level 1
        self.assertEqual(self.character.level, 1)
        self.assertEqual(self.character.perk_points, 0)
        
        # Give enough experience to level up
        required_exp = self.perk_system.calculate_experience_required(2)
        self.character.experience = required_exp
        
        # Check level up
        level_up_occurred = self.perk_system.check_level_up(self.character)
        self.assertTrue(level_up_occurred)
        self.assertEqual(self.character.level, 2)
        self.assertEqual(self.character.perk_points, 2)
    
    def test_multiple_level_ups(self):
        """Test multiple level-ups from large experience gains."""
        # Give enough experience for multiple levels
        level_5_exp = self.perk_system.calculate_experience_required(5)
        messages = self.character.gain_experience(level_5_exp)
        
        # Should have leveled up multiple times
        self.assertGreater(self.character.level, 1)
        self.assertGreater(self.character.perk_points, 0)
        self.assertGreater(len(messages), 0)


class TestPerkLearning(unittest.TestCase):
    """Test perk learning and restrictions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.character = Character("Test Hero")
        self.character.set_character_class(CharacterClass.WARRIOR)
        self.character.perk_points = 10  # Give some points to spend
        self.character_perks = CharacterPerks(self.character)
    
    def test_basic_perk_learning(self):
        """Test learning basic perks."""
        # Should be able to learn power attack
        success = self.character_perks.learn_perk("power_attack")
        self.assertTrue(success)
        
        # Check perk was learned
        self.assertTrue(self.character_perks.has_perk("power_attack"))
        self.assertEqual(self.character_perks.get_perk_rank("power_attack"), 1)
        
        # Perk points should be reduced
        self.assertEqual(self.character.perk_points, 9)
    
    def test_perk_prerequisites(self):
        """Test perk prerequisite system."""
        # Should not be able to learn critical strike without power attack
        success = self.character_perks.learn_perk("critical_strike")
        self.assertFalse(success)
        
        # Learn prerequisite first
        self.character_perks.learn_perk("power_attack")
        
        # Now should be able to learn critical strike
        success = self.character_perks.learn_perk("critical_strike")
        self.assertTrue(success)
    
    def test_class_restricted_perks(self):
        """Test class-specific perk restrictions."""
        # Warrior should be able to learn weapon mastery
        success = self.character_perks.learn_perk("weapon_mastery")
        self.assertTrue(success)
        
        # Create a mage character
        mage = Character("Test Mage")
        mage.set_character_class(CharacterClass.MAGE)
        mage.perk_points = 10
        mage_perks = CharacterPerks(mage)
        
        # Mage should not be able to learn warrior-specific perks
        success = mage_perks.learn_perk("weapon_mastery")
        self.assertFalse(success)
        
        # But should be able to learn mage-specific perks
        success = mage_perks.learn_perk("arcane_knowledge")
        self.assertTrue(success)
    
    def test_max_rank_limits(self):
        """Test maximum rank limits for perks."""
        perk = self.character_perks.perk_system.get_perk("power_attack")
        max_rank = perk.max_rank
        
        # Learn perk to max rank
        for _ in range(max_rank):
            success = self.character_perks.learn_perk("power_attack")
            self.assertTrue(success)
        
        # Should not be able to learn beyond max rank
        success = self.character_perks.learn_perk("power_attack")
        self.assertFalse(success)
        
        self.assertEqual(self.character_perks.get_perk_rank("power_attack"), max_rank)
    
    def test_insufficient_perk_points(self):
        """Test learning with insufficient perk points."""
        self.character.perk_points = 0
        
        success = self.character_perks.learn_perk("power_attack")
        self.assertFalse(success)


class TestPerkEffects(unittest.TestCase):
    """Test perk effects on character stats and abilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.character = Character("Test Hero")
        self.character.set_character_class(CharacterClass.WARRIOR)
        self.character.perk_points = 20
        self.character_perks = CharacterPerks(self.character)
    
    def test_stat_bonus_perks(self):
        """Test perks that provide stat bonuses."""
        # Get initial max HP
        initial_hp = self.character.max_hp
        
        # Learn toughness perk
        self.character_perks.learn_perk("toughness")
        
        # Max HP should increase
        new_hp = self.character._calculate_max_hp()
        self.assertGreater(new_hp, initial_hp)
    
    def test_sight_range_perks(self):
        """Test perks that affect sight range."""
        initial_sight = self.character.get_sight_range()
        
        # Learn keen senses perk
        self.character_perks.learn_perk("keen_senses")
        
        new_sight = self.character.get_sight_range()
        self.assertGreater(new_sight, initial_sight)
    
    def test_damage_perks(self):
        """Test perks that affect damage output."""
        initial_damage = self.character.get_attack_damage()
        
        # Learn power attack perk
        self.character_perks.learn_perk("power_attack")
        
        # Damage should increase (test multiple times due to randomness)
        damage_increased = False
        for _ in range(10):
            new_damage = self.character.get_attack_damage()
            if new_damage > initial_damage:
                damage_increased = True
                break
        
        self.assertTrue(damage_increased, "Power attack perk should increase damage")
    
    def test_damage_reduction_perks(self):
        """Test perks that reduce incoming damage."""
        # Learn damage resistance perk
        self.character_perks.learn_perk("toughness")  # Prerequisite
        self.character_perks.learn_perk("damage_resistance")
        
        # Test damage reduction
        initial_hp = self.character.current_hp
        damage_amount = 10
        
        self.character.take_damage(damage_amount)
        actual_damage = initial_hp - self.character.current_hp
        
        # Should take less damage due to resistance
        self.assertLess(actual_damage, damage_amount)


class TestCharacterClasses(unittest.TestCase):
    """Test perk interactions with different character classes."""
    
    def test_warrior_specialization(self):
        """Test warrior-specific perks."""
        warrior = CharacterClassData.create_character(CharacterClass.WARRIOR, "Test Warrior")
        warrior.perk_points = 10
        warrior_perks = CharacterPerks(warrior)
        
        # Should be able to learn warrior perks
        self.assertTrue(warrior_perks.learn_perk("weapon_mastery"))
        self.assertTrue(warrior_perks.learn_perk("armor_expertise"))
        
        # Check perk effects are applied
        self.assertGreater(warrior_perks.get_perk_bonus("weapon_damage"), 0)
    
    def test_mage_specialization(self):
        """Test mage-specific perks."""
        mage = CharacterClassData.create_character(CharacterClass.MAGE, "Test Mage")
        mage.perk_points = 10
        mage_perks = CharacterPerks(mage)
        
        # Should be able to learn mage perks
        self.assertTrue(mage_perks.learn_perk("arcane_knowledge"))
        self.assertTrue(mage_perks.learn_perk("spell_power"))
        
        # Check enhanced sight range from arcane knowledge
        initial_sight = mage.get_sight_range()
        self.assertGreater(initial_sight, 6)  # Should be enhanced due to high perception + perk
    
    def test_rogue_specialization(self):
        """Test rogue-specific perks."""
        rogue = CharacterClassData.create_character(CharacterClass.ROGUE, "Test Rogue")
        rogue.perk_points = 10
        rogue_perks = CharacterPerks(rogue)
        
        # Should be able to learn rogue perks
        self.assertTrue(rogue_perks.learn_perk("stealth"))
        self.assertTrue(rogue_perks.learn_perk("lucky_strike"))
        
        # Check perk effects
        self.assertGreater(rogue_perks.get_perk_bonus("stealth_chance"), 0)
    
    def test_ranger_specialization(self):
        """Test ranger-specific perks."""
        ranger = CharacterClassData.create_character(CharacterClass.RANGER, "Test Ranger")
        ranger.perk_points = 10
        ranger_perks = CharacterPerks(ranger)
        
        # Should be able to learn ranger perks
        self.assertTrue(ranger_perks.learn_perk("nature_lore"))
        self.assertTrue(ranger_perks.learn_perk("precise_shot"))
        
        # Check enhanced sight in dungeons
        self.assertGreater(ranger_perks.get_perk_bonus("dungeon_sight"), 0)
    
    def test_cleric_specialization(self):
        """Test cleric-specific perks."""
        cleric = CharacterClassData.create_character(CharacterClass.CLERIC, "Test Cleric")
        cleric.perk_points = 10
        cleric_perks = CharacterPerks(cleric)
        
        # Should be able to learn cleric perks
        self.assertTrue(cleric_perks.learn_perk("divine_favour"))
        self.assertTrue(cleric_perks.learn_perk("blessed_recovery"))


class TestExperienceSystem(unittest.TestCase):
    """Test the enhanced experience and leveling system."""
    
    def test_experience_gain_with_bonuses(self):
        """Test experience gain with perk bonuses."""
        character = Character("Test Hero")
        character.set_character_class(CharacterClass.WARRIOR)
        character.perk_points = 10
        character_perks = CharacterPerks(character)
        
        # Learn fast learner perk
        character_perks.learn_perk("fast_learner")
        
        # Gain experience
        base_exp = 100
        messages = character.gain_experience(base_exp)
        
        # Should gain more than base experience due to perk
        expected_exp = int(base_exp * 1.1)  # 10% bonus
        self.assertEqual(character.experience, expected_exp)
    
    def test_level_up_health_restoration(self):
        """Test that leveling up fully restores health."""
        character = Character("Test Hero")
        character.set_character_class(CharacterClass.WARRIOR)
        
        # Damage the character
        character.take_damage(10)
        damaged_hp = character.current_hp
        self.assertLess(damaged_hp, character.max_hp)
        
        # Level up
        level_2_exp = PerkSystem().calculate_experience_required(2)
        character.gain_experience(level_2_exp)
        
        # Should be fully healed
        self.assertEqual(character.current_hp, character.max_hp)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPerkSystem,
        TestPerkLearning,
        TestPerkEffects,
        TestCharacterClasses,
        TestExperienceSystem
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"PERK SYSTEM TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split(chr(10))[-2]}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[-2]}") 