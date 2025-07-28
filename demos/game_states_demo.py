#!/usr/bin/env python3
"""
Game States Demo for Mythica Dungeon Crawler
Demonstrates the character classes and game state system.
"""

from logic.game_states import CharacterClass, CharacterClassData, GameStateManager
from logic.character_system import StatType
import pygame

def demonstrate_character_classes():
    """Demonstrate all character classes and their differences."""
    print("=== Mythica Character Classes Demo ===\n")
    
    classes_to_test = [
        CharacterClass.WARRIOR,
        CharacterClass.ROGUE, 
        CharacterClass.MAGE,
        CharacterClass.RANGER,
        CharacterClass.CLERIC
    ]
    
    characters = {}
    
    for char_class in classes_to_test:
        character = CharacterClassData.create_character(char_class, f"Test {char_class.value}")
        characters[char_class] = character
        
        print(f"=== {char_class.value.upper()} ===")
        class_data = CharacterClassData.CLASS_DEFINITIONS[char_class]
        print(f"Description: {class_data['description']}")
        print(f"Name: {character.name}")
        print(f"Health: {character.current_hp}/{character.max_hp} HP")
        print(f"Sight Range: {character.get_sight_range()} tiles")
        print(f"Attack Damage: ~{character.get_attack_damage()} (varies)")
        
        print("Stats:")
        for stat_type, (base, bonus, total) in character.stats.get_all_stats().items():
            if bonus > 0:
                print(f"  {stat_type.value}: {base} (+{bonus}) = {total}")
            else:
                print(f"  {stat_type.value}: {base}")
        
        print("Starting Equipment:")
        for slot, item in character.equipment.get_equipment_summary().items():
            if item != "Empty":
                print(f"  {slot}: {item}")
        
        print()
    
    print("=== Class Comparison ===")
    print("Stat comparison across all classes:")
    print(f"{'Class':<10} {'HP':<6} {'STR':<4} {'DEX':<4} {'CON':<4} {'PER':<4} {'LCK':<4} {'Sight':<6} {'Dmg':<4}")
    print("-" * 70)
    
    for char_class, character in characters.items():
        stats = character.stats.get_all_stats()
        hp = f"{character.current_hp}/{character.max_hp}"
        str_val = stats[StatType.STRENGTH][2]  # Total value
        dex_val = stats[StatType.DEXTERITY][2]
        con_val = stats[StatType.CONSTITUTION][2]
        per_val = stats[StatType.PERCEPTION][2]
        lck_val = stats[StatType.LUCK][2]
        sight = character.get_sight_range()
        dmg = character.get_attack_damage()
        
        print(f"{char_class.value:<10} {hp:<6} {str_val:<4} {dex_val:<4} {con_val:<4} {per_val:<4} {lck_val:<4} {sight:<6} ~{dmg:<3}")
    
    print("\n=== Class Strengths ===")
    
    # Find the best class for each stat
    best_hp = max(characters.items(), key=lambda x: x[1].max_hp)
    best_str = max(characters.items(), key=lambda x: x[1].stats.get_total_stat(StatType.STRENGTH))
    best_dex = max(characters.items(), key=lambda x: x[1].stats.get_total_stat(StatType.DEXTERITY))
    best_con = max(characters.items(), key=lambda x: x[1].stats.get_total_stat(StatType.CONSTITUTION))
    best_per = max(characters.items(), key=lambda x: x[1].stats.get_total_stat(StatType.PERCEPTION))
    best_lck = max(characters.items(), key=lambda x: x[1].stats.get_total_stat(StatType.LUCK))
    best_sight = max(characters.items(), key=lambda x: x[1].get_sight_range())
    
    print(f"Highest HP: {best_hp[0].value} ({best_hp[1].max_hp} HP)")
    print(f"Highest Strength: {best_str[0].value} ({best_str[1].stats.get_total_stat(StatType.STRENGTH)})")
    print(f"Highest Dexterity: {best_dex[0].value} ({best_dex[1].stats.get_total_stat(StatType.DEXTERITY)})")
    print(f"Highest Constitution: {best_con[0].value} ({best_con[1].stats.get_total_stat(StatType.CONSTITUTION)})")
    print(f"Highest Perception: {best_per[0].value} ({best_per[1].stats.get_total_stat(StatType.PERCEPTION)})")
    print(f"Highest Luck: {best_lck[0].value} ({best_lck[1].stats.get_total_stat(StatType.LUCK)})")
    print(f"Best Sight Range: {best_sight[0].value} ({best_sight[1].get_sight_range()} tiles)")
    
    print("\n=== Equipment Differences ===")
    
    for char_class, character in characters.items():
        equipped_count = len([item for item in character.equipment.get_equipment_summary().values() if item != "Empty"])
        total_bonuses = character.equipment.get_total_stat_bonuses()
        bonus_sum = sum(total_bonuses.values())
        
        print(f"{char_class.value}: {equipped_count} items equipped, +{bonus_sum} total stat bonuses")
    
    print("\n=== Recommended Playstyles ===")
    
    recommendations = {
        CharacterClass.WARRIOR: "Tank builds, front-line combat, high survivability",
        CharacterClass.ROGUE: "Speed builds, evasion tactics, luck-based strategies", 
        CharacterClass.MAGE: "Exploration builds, maximum sight range, tactical awareness",
        CharacterClass.RANGER: "Balanced builds, adaptable to any situation",
        CharacterClass.CLERIC: "Endurance builds, survive through tough situations"
    }
    
    for char_class, recommendation in recommendations.items():
        print(f"{char_class.value}: {recommendation}")

def demonstrate_game_states():
    """Demonstrate game state management (conceptual - requires pygame display)."""
    print("\n=== Game State System ===")
    print("The game now includes multiple states:")
    print("1. MENU - Main menu with New Game/Quit options")
    print("2. CLASS_SELECTION - Choose your character class")
    print("3. PLAYING - The actual dungeon crawler gameplay")
    print("4. GAME_OVER - Death screen with restart/quit options")
    print("5. PAUSED - Future feature for pausing mid-game")
    
    print("\nNavigation:")
    print("- W/S or Up/Down arrows to navigate menus")
    print("- Enter or Space to select options")
    print("- Escape to go back or quit")
    
    print("\nGame Flow:")
    print("Menu → Class Selection → Playing → Game Over → (restart loop)")
    
    print("\nFeatures:")
    print("✓ Proper game state management")
    print("✓ Character class preview with stats")
    print("✓ In-game death detection")
    print("✓ Restart functionality")
    print("✓ Clean menu interfaces")

if __name__ == "__main__":
    demonstrate_character_classes()
    demonstrate_game_states()
    
    print("\n=== Demo Complete ===")
    print("Character class and game state features:")
    print("✓ 5 distinct character classes with unique stats")
    print("✓ Class-specific starting equipment")
    print("✓ Balanced stat distributions for different playstyles")
    print("✓ Complete game state management system")
    print("✓ Professional menu interfaces")
    print("✓ Game over and restart functionality")
    print("✓ Class selection with detailed previews") 