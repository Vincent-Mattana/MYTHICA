#!/usr/bin/env python3
"""
Comprehensive tests for the turn timing system including:
- Action timing and scheduling
- Weapon-specific timing (attack and reload speeds)
- Turn order management
- Dexterity effects on action speed
- Combat timing mechanics
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.turn_system import (
    TurnManager, ActionType, ActionCosts, WeaponType, Action, TurnScheduler
)
from logic.character_system import Character, StatType, ItemType, Item


class TestActionCosts(unittest.TestCase):
    """Test action cost calculations and weapon timing."""
    
    def setUp(self):
        """Set up action costs calculator."""
        self.action_costs = ActionCosts()
    
    def test_base_action_costs(self):
        """Test base action costs without modifiers."""
        # Test basic movement cost with average dexterity (10)
        move_cost = ActionCosts.get_movement_cost(dexterity=10)
        self.assertEqual(move_cost, 1.0, "Base movement should cost 1.0 seconds")
        
        # Test base action costs from the BASE_COSTS dict
        wait_cost = ActionCosts.BASE_COSTS[ActionType.WAIT]
        self.assertEqual(wait_cost, 1.0, "Wait action should cost 1.0 seconds")
    
    def test_weapon_attack_speeds(self):
        """Test different weapon attack speeds."""
        # Test various weapon types with average dexterity (10)
        weapon_timings = [
            (WeaponType.SWORD, 1.0),
            (WeaponType.DAGGER, 0.7),
            (WeaponType.BOW, 0.8),
            (WeaponType.CROSSBOW, 1.2),
            (WeaponType.STAFF, 1.1)
        ]
        
        for weapon_type, expected_time in weapon_timings:
            attack_cost = ActionCosts.get_attack_cost(weapon_type, dexterity=10)
            self.assertAlmostEqual(attack_cost, expected_time, places=1,
                msg=f"{weapon_type} should have attack time {expected_time}")
    
    def test_weapon_reload_speeds(self):
        """Test weapon reload timing."""
        # Test reload times with average dexterity (10)
        reload_timings = [
            (WeaponType.BOW, 0.5),
            (WeaponType.CROSSBOW, 2.0),
            (WeaponType.SWORD, 0.0),  # Melee weapons don't reload
            (WeaponType.DAGGER, 0.0)
        ]
        
        for weapon_type, expected_reload in reload_timings:
            reload_cost = ActionCosts.get_reload_cost(weapon_type, dexterity=10)
            self.assertAlmostEqual(reload_cost, expected_reload, places=1,
                msg=f"{weapon_type} should have reload time {expected_reload}")
    
    def test_dexterity_effects_on_speed(self):
        """Test that higher Dexterity reduces action times."""
        # Test movement speed with different Dexterity values
        low_dex_cost = ActionCosts.get_movement_cost(dexterity=8)
        high_dex_cost = ActionCosts.get_movement_cost(dexterity=18)
        
        self.assertGreater(low_dex_cost, high_dex_cost,
            "Higher Dexterity should reduce movement time")
        
        # Test attack speed with different Dexterity values
        low_dex_attack = ActionCosts.get_attack_cost(WeaponType.SWORD, dexterity=8)
        high_dex_attack = ActionCosts.get_attack_cost(WeaponType.SWORD, dexterity=18)
        
        self.assertGreater(low_dex_attack, high_dex_attack,
            "Higher Dexterity should reduce attack time")
    
    def test_dexterity_modifier_calculation(self):
        """Test Dexterity modifier effects on timing."""
        # Test that different dexterity values produce different costs
        base_dex = 10
        high_dex = 16
        low_dex = 6
        
        # Get movement costs for different dexterity values
        base_cost = ActionCosts.get_movement_cost(base_dex)
        high_dex_cost = ActionCosts.get_movement_cost(high_dex)
        low_dex_cost = ActionCosts.get_movement_cost(low_dex)
        
        # High dex should be faster (lower cost), low dex should be slower (higher cost)
        self.assertLess(high_dex_cost, base_cost, "High dexterity should reduce action time")
        self.assertGreater(low_dex_cost, base_cost, "Low dexterity should increase action time")


class TestTurnScheduler(unittest.TestCase):
    """Test turn scheduling and action queuing."""
    
    def setUp(self):
        """Set up turn scheduler."""
        self.scheduler = TurnScheduler()
        self.character1 = Character("Fighter")
        self.character2 = Character("Rogue")
    
    def test_schedule_action(self):
        """Test scheduling actions in the queue."""
        # Create an action
        action = Action(ActionType.MOVE, "player", 2.0)
        
        # Schedule the action
        self.scheduler.schedule_action(action)
        
        # Verify action is in the queue
        self.assertGreater(len(self.scheduler.action_queue), 0, "Action should be queued")
        
        # Advance time to when action completes
        self.scheduler.advance_time_to_next_action()
        
        # Should be able to get the action
        next_action = self.scheduler.get_next_action()
        self.assertIsNotNone(next_action)
    
    def test_action_order_by_time(self):
        """Test that actions are processed in chronological order."""
        # Schedule actions with different completion times
        action1 = Action(ActionType.MOVE, "player1", 1.0)
        action2 = Action(ActionType.ATTACK, "player2", 0.5)
        action3 = Action(ActionType.WAIT, "player1", 1.5)
        
        self.scheduler.schedule_action(action1)
        self.scheduler.schedule_action(action2)
        self.scheduler.schedule_action(action3)
        
        # Get actions in order they would complete
        completed_actions = []
        while self.scheduler.action_queue:
            next_action = self.scheduler.get_next_action()
            if next_action:
                completed_actions.append(next_action[1])  # Get the Action object
        
        # Actions should be processed in order: action2 (0.5s), action1 (1.0s), action3 (1.5s)
        self.assertEqual(len(completed_actions), 3)
        self.assertEqual(completed_actions[0].action_type, ActionType.ATTACK)
        self.assertEqual(completed_actions[1].action_type, ActionType.MOVE)
        self.assertEqual(completed_actions[2].action_type, ActionType.WAIT)
    
    def test_simultaneous_actions(self):
        """Test handling of actions that complete at the same time."""
        # Schedule two actions to complete at the same time
        action1 = Action(ActionType.MOVE, "player1", 1.0)
        action2 = Action(ActionType.MOVE, "player2", 1.0)
        
        self.scheduler.schedule_action(action1)
        self.scheduler.schedule_action(action2)
        
        # Both actions should be in the queue
        self.assertEqual(len(self.scheduler.action_queue), 2)
        
        # Should be able to get both actions
        action_a = self.scheduler.get_next_action()
        action_b = self.scheduler.get_next_action()
        
        self.assertIsNotNone(action_a)
        self.assertIsNotNone(action_b)
    
    def test_time_advancement(self):
        """Test time advancement and action timing."""
        initial_time = self.scheduler.current_time
        
        # Schedule action for 3 seconds in the future
        action = Action(ActionType.WAIT, "player", 3.0)
        self.scheduler.schedule_action(action)
        
        # Check that action is scheduled for the future
        self.assertEqual(len(self.scheduler.action_queue), 1)
        completion_time, scheduled_action = self.scheduler.action_queue[0]
        expected_completion = initial_time + 3.0
        self.assertEqual(completion_time, expected_completion)
        
        # Advance time to next action
        self.scheduler.advance_time_to_next_action()
        self.assertEqual(self.scheduler.current_time, expected_completion)


class TestTurnManager(unittest.TestCase):
    """Test high-level turn management and game flow."""
    
    def setUp(self):
        """Set up turn manager with test entity IDs."""
        self.turn_manager = TurnManager()
        
        # Set up entity weapon types (since TurnManager tracks weapons by entity ID)
        self.turn_manager.set_entity_weapon("fast_character", "Dagger")
        self.turn_manager.set_entity_weapon("slow_character", "Crossbow")
    
    def test_character_action_submission(self):
        """Test submitting actions for entities."""
        # Submit a player action (the TurnManager has specific player action method)
        success = self.turn_manager.schedule_player_action(ActionType.MOVE, dexterity=14)
        
        self.assertTrue(success, "Should be able to submit valid player action")
        
        # Player should not be able to act again immediately
        self.assertFalse(self.turn_manager.can_player_act(), "Player should be busy after action")
    
    def test_weapon_specific_actions(self):
        """Test weapon-specific action timing."""
        # Test different weapon attack costs
        dagger_cost = self.turn_manager._calculate_action_cost(ActionType.ATTACK, "fast_character", 14)
        crossbow_cost = self.turn_manager._calculate_action_cost(ActionType.ATTACK, "slow_character", 10)
        
        # Dagger should be faster than crossbow
        self.assertLess(dagger_cost, crossbow_cost,
                       "Dagger attack should be faster than crossbow attack")
    
    def test_reload_mechanics(self):
        """Test weapon reload timing and mechanics."""
        # Test reload cost calculation
        reload_cost = self.turn_manager._calculate_action_cost(ActionType.RELOAD, "slow_character", 10)
        
        # Crossbow reload should take significant time
        self.assertGreater(reload_cost, 1.0, "Crossbow reload should take significant time")
        
        # Test weapon loaded status
        self.turn_manager.fire_weapon("slow_character")  # Fire crossbow
        self.assertFalse(self.turn_manager.is_weapon_loaded("slow_character"), 
                        "Crossbow should be unloaded after firing")
        
        self.turn_manager.reload_weapon("slow_character")  # Reload
        self.assertTrue(self.turn_manager.is_weapon_loaded("slow_character"),
                      "Crossbow should be loaded after reloading")
    
    def test_action_queue_processing(self):
        """Test processing of queued actions."""
        # Schedule actions using the turn manager
        self.turn_manager.schedule_player_action(ActionType.MOVE, dexterity=14)
        self.turn_manager.schedule_enemy_action("enemy1", ActionType.MOVE, dexterity=10)
        
        # Verify actions are queued in the scheduler
        queue_size = len(self.turn_manager.scheduler.action_queue)
        self.assertEqual(queue_size, 2, "Both actions should be queued")
        
        # Process next action
        next_action = self.turn_manager.process_next_action()
        self.assertIsNotNone(next_action, "Should be able to process queued action")
    
    def test_turn_order_with_different_speeds(self):
        """Test that dexterity affects action speeds."""
        # Test that higher dexterity results in faster actions
        fast_move_cost = self.turn_manager._calculate_action_cost(ActionType.MOVE, "fast_character", 18)
        slow_move_cost = self.turn_manager._calculate_action_cost(ActionType.MOVE, "slow_character", 8)
        
        # Higher dexterity should result in faster (lower cost) actions
        self.assertLess(fast_move_cost, slow_move_cost,
            "Higher dexterity should result in faster movement")


class TestCombatTiming(unittest.TestCase):
    """Test combat-specific timing mechanics."""
    
    def setUp(self):
        """Set up combat scenario."""
        self.turn_manager = TurnManager()
        
        # Set up weapons for combat timing tests
        self.turn_manager.set_entity_weapon("attacker", "Iron Sword")
        self.turn_manager.set_entity_weapon("defender", "Hunter's Bow")
    
    def test_attack_action_timing(self):
        """Test attack action timing and resolution."""
        # Test attack cost calculation for sword
        attack_cost = self.turn_manager._calculate_action_cost(ActionType.ATTACK, "attacker", 12)
        
        # Attack should take reasonable time (approximately 1 second for sword)
        self.assertGreater(attack_cost, 0.5, "Attack should take at least 0.5 seconds")
        self.assertLess(attack_cost, 2.0, "Attack should take less than 2 seconds")
    
    def test_multi_action_combat_sequence(self):
        """Test a sequence of combat action cost calculations."""
        # Set up weapons for entities
        self.turn_manager.set_entity_weapon("attacker", "Iron Sword")
        self.turn_manager.set_entity_weapon("defender", "Hunter's Bow")
        
        # Test different action costs for different weapons and actions
        sword_attack = self.turn_manager._calculate_action_cost(ActionType.ATTACK, "attacker", 12)
        bow_attack = self.turn_manager._calculate_action_cost(ActionType.ATTACK, "defender", 12)
        bow_reload = self.turn_manager._calculate_action_cost(ActionType.RELOAD, "defender", 12)
        
        # Verify all actions have reasonable timing
        action_costs = [sword_attack, bow_attack, bow_reload]
        
        for cost in action_costs:
            self.assertGreater(cost, 0.1, "All actions should take some time")
            self.assertLess(cost, 5.0, "No action should take excessively long")
        
        # Bow reload should take longer than bow attack
        self.assertGreater(bow_reload, bow_attack, "Bow reload should take longer than bow attack")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 