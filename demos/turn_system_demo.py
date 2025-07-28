#!/usr/bin/env python3
"""
Turn System Demo for Mythica Dungeon Crawler
Demonstrates the turn-based action system with weapon timing.
"""

from logic.turn_system import TurnManager, ActionType, ActionCosts, WeaponType
from logic.character_system import StatType

def demonstrate_action_timing():
    """Demonstrate action timing and costs."""
    print("=== Mythica Turn-Based System Demo ===\n")
    
    print("=== Action Base Costs ===")
    for action_type in ActionType:
        cost = ActionCosts.BASE_COSTS.get(action_type, 1.0)
        print(f"{action_type.value.title()}: {cost}s")
    
    print("\n=== Weapon Attack Speeds ===")
    dexterity = 10  # Average dexterity
    
    for weapon_type in WeaponType:
        attack_cost = ActionCosts.get_attack_cost(weapon_type, dexterity)
        reload_cost = ActionCosts.get_reload_cost(weapon_type, dexterity)
        
        if reload_cost > 0:
            print(f"{weapon_type.value.title()}: {attack_cost}s attack, {reload_cost}s reload")
        else:
            print(f"{weapon_type.value.title()}: {attack_cost}s attack (no reload)")
    
    print("\n=== Dexterity Impact ===")
    dexterity_values = [8, 10, 12, 15, 18]
    
    print("Movement speed by Dexterity:")
    for dex in dexterity_values:
        move_cost = ActionCosts.get_movement_cost(dex)
        print(f"  Dex {dex}: {move_cost:.2f}s per move")
    
    print("\nSword attack speed by Dexterity:")
    for dex in dexterity_values:
        attack_cost = ActionCosts.get_attack_cost(WeaponType.SWORD, dex)
        print(f"  Dex {dex}: {attack_cost:.2f}s per attack")
    
    print("\nCrossbow reload speed by Dexterity:")
    for dex in dexterity_values:
        reload_cost = ActionCosts.get_reload_cost(WeaponType.CROSSBOW, dex)
        print(f"  Dex {dex}: {reload_cost:.2f}s to reload")

def demonstrate_combat_scenario():
    """Demonstrate a combat scenario with timing."""
    print("\n=== Combat Timing Scenario ===")
    
    # Simulate a warrior vs archer scenario
    print("Scenario: Warrior (sword) vs Archer (bow)")
    print("Both start 3 tiles apart, warrior wants to close distance")
    print()
    
    warrior_dex = 12
    archer_dex = 15
    
    # Calculate action costs
    warrior_move = ActionCosts.get_movement_cost(warrior_dex)
    warrior_attack = ActionCosts.get_attack_cost(WeaponType.SWORD, warrior_dex)
    
    archer_move = ActionCosts.get_movement_cost(archer_dex)
    archer_attack = ActionCosts.get_attack_cost(WeaponType.BOW, archer_dex)
    archer_reload = ActionCosts.get_reload_cost(WeaponType.BOW, archer_dex)
    
    print(f"Warrior (Dex {warrior_dex}):")
    print(f"  Move: {warrior_move:.2f}s")
    print(f"  Sword attack: {warrior_attack:.2f}s")
    
    print(f"\nArcher (Dex {archer_dex}):")
    print(f"  Move: {archer_move:.2f}s")
    print(f"  Bow attack: {archer_attack:.2f}s")
    print(f"  Bow reload: {archer_reload:.2f}s")
    
    print(f"\nAnalysis:")
    print(f"- Archer shoots and reloads in {archer_attack + archer_reload:.2f}s total")
    print(f"- Warrior moves 3 times to close distance: {warrior_move * 3:.2f}s")
    print(f"- Archer can shoot {(warrior_move * 3) / (archer_attack + archer_reload):.1f} times before warrior reaches melee range")

def demonstrate_weapon_comparison():
    """Compare different weapon types in combat scenarios."""
    print("\n=== Weapon Comparison ===")
    
    dexterity = 12
    weapons = [
        WeaponType.DAGGER,
        WeaponType.SWORD, 
        WeaponType.BOW,
        WeaponType.CROSSBOW,
        WeaponType.MACE
    ]
    
    print(f"Combat efficiency comparison (Dex {dexterity}):")
    print(f"{'Weapon':<12} {'Attack':<8} {'Reload':<8} {'Total':<8} {'DPS*':<8}")
    print("-" * 50)
    
    for weapon in weapons:
        attack_cost = ActionCosts.get_attack_cost(weapon, dexterity)
        reload_cost = ActionCosts.get_reload_cost(weapon, dexterity)
        total_time = attack_cost + reload_cost
        dps_factor = 1.0 / total_time  # Attacks per second (assuming equal damage)
        
        print(f"{weapon.value.title():<12} {attack_cost:.2f}s{'':<3} {reload_cost:.2f}s{'':<3} {total_time:.2f}s{'':<3} {dps_factor:.2f}")
    
    print("\n*DPS factor assumes equal base damage - actual damage varies by weapon type")

def demonstrate_turn_manager():
    """Demonstrate the turn manager functionality."""
    print("\n=== Turn Manager Demo ===")
    
    turn_manager = TurnManager()
    
    # Set up entities
    turn_manager.set_entity_weapon("player", "Iron Sword")
    turn_manager.set_entity_weapon("goblin1", "Rusty Dagger")
    turn_manager.set_entity_weapon("archer1", "Hunter's Bow")
    
    print("Initial setup:")
    print(f"  Player weapon: {turn_manager.get_entity_weapon_type('player').value}")
    print(f"  Goblin weapon: {turn_manager.get_entity_weapon_type('goblin1').value}")
    print(f"  Archer weapon: {turn_manager.get_entity_weapon_type('archer1').value}")
    
    # Schedule some actions
    print(f"\nScheduling actions at time {turn_manager.scheduler.current_time:.1f}:")
    
    # Player moves
    turn_manager.schedule_player_action(ActionType.MOVE, target_pos=(5, 5), dexterity=12)
    print("  Player moves")
    
    # Goblin attacks
    turn_manager.schedule_enemy_action("goblin1", ActionType.ATTACK, target_id="player", dexterity=14)
    print("  Goblin attacks")
    
    # Archer shoots and reloads
    turn_manager.schedule_enemy_action("archer1", ActionType.ATTACK, target_id="player", dexterity=15)
    print("  Archer shoots")
    
    print(f"\nAction queue ({len(turn_manager.scheduler.action_queue)} actions):")
    
    # Process actions
    action_count = 0
    while action_count < 5:  # Limit to prevent infinite loop
        next_action = turn_manager.process_next_action()
        if not next_action:
            break
            
        completion_time, action = next_action
        action_count += 1
        
        print(f"  Time {completion_time:.2f}s: {action.actor_id} performs {action.action_type.value}")
        
        # Schedule archer reload after shooting
        if action.actor_id == "archer1" and action.action_type == ActionType.ATTACK:
            turn_manager.schedule_enemy_action("archer1", ActionType.RELOAD, dexterity=15)
            print(f"    Archer schedules reload")
    
    turn_info = turn_manager.get_turn_info()
    print(f"\nFinal state:")
    print(f"  Current time: {turn_info['current_time']:.2f}s")
    print(f"  Turn number: {turn_info['turn_number']}")
    print(f"  Waiting for player: {turn_info['waiting_for_player']}")

if __name__ == "__main__":
    demonstrate_action_timing()
    demonstrate_combat_scenario()
    demonstrate_weapon_comparison()
    demonstrate_turn_manager()
    
    print("\n=== Demo Complete ===")
    print("Turn-based system features:")
    print("✓ Action timing with time costs")
    print("✓ Weapon-specific attack and reload speeds")
    print("✓ Dexterity affects action speed")
    print("✓ Turn scheduling and queue management")
    print("✓ Strategic timing considerations")
    print("✓ Proper turn-based enemy AI")
    print("✓ Tactical weapon choice implications") 