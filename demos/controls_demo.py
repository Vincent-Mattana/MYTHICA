#!/usr/bin/env python3
"""
Controls Demo for Mythica Dungeon Crawler
Demonstrates the configurable control system and diagonal movement.
"""

import pygame
from logic.config_manager import ConfigManager

def demonstrate_controls():
    """Demonstrate the control system features."""
    print("=== Mythica Controls System Demo ===\n")
    
    # Initialize pygame to get key constants
    pygame.init()
    
    # Create config manager
    config = ConfigManager()
    
    # Show current configuration
    help_text = config.get_control_help_text()
    for line in help_text:
        print(line)
    
    print("\n=== Testing Key Mappings ===")
    
    # Test movement key detection
    test_keys = [
        (pygame.K_w, "W key"),
        (pygame.K_KP8, "Numpad 8"),
        (pygame.K_KP7, "Numpad 7 (Northwest)"),
        (pygame.K_KP9, "Numpad 9 (Northeast)"),
        (pygame.K_c, "C key"),
        (pygame.K_ESCAPE, "Escape key"),
        (pygame.K_KP5, "Numpad 5 (Wait)"),
    ]
    
    for key_code, key_description in test_keys:
        print(f"\nTesting {key_description}:")
        
        # Check movement direction
        direction = config.get_movement_direction(key_code)
        if direction != (0, 0):
            dx, dy = direction
            direction_name = get_direction_name(dx, dy)
            print(f"  Movement: {direction_name} ({dx}, {dy})")
        
        # Check other actions
        if config.is_key_pressed_for_action('character_sheet', key_code):
            print(f"  Action: Open Character Sheet")
        
        if config.is_key_pressed_for_action('wait_turn', key_code):
            print(f"  Action: Wait/Rest Turn")
        
        if config.is_key_pressed_for_action('quit_game', key_code):
            print(f"  Action: Quit Game")
        
        if direction == (0, 0) and not any(config.is_key_pressed_for_action(action, key_code) 
                                         for action in ['character_sheet', 'wait_turn', 'quit_game']):
            print(f"  No action mapped")
    
    print("\n=== Diagonal Movement Test ===")
    
    # Test all 8 directions
    directions_to_test = [
        (0, -1, "North"),
        (1, -1, "Northeast"), 
        (1, 0, "East"),
        (1, 1, "Southeast"),
        (0, 1, "South"),
        (-1, 1, "Southwest"),
        (-1, 0, "West"),
        (-1, -1, "Northwest")
    ]
    
    print("8-directional movement support:")
    for dx, dy, name in directions_to_test:
        # Find a key that produces this direction
        found_key = None
        for action, keys in config.key_mappings.items():
            if action.startswith('move_'):
                test_direction = config.get_movement_direction(list(keys)[0] if keys else 0)
                if test_direction == (dx, dy):
                    key_names = [pygame.key.name(k) for k in keys]
                    found_key = ', '.join(key_names)
                    break
        
        if found_key:
            print(f"  {name:10} ({dx:2}, {dy:2}): {found_key}")
        else:
            print(f"  {name:10} ({dx:2}, {dy:2}): No key mapped")
    
    print("\n=== Configuration Settings ===")
    
    # Show current settings
    diagonal_enabled = config.get_bool_setting('Game', 'diagonal_movement_enabled', True)
    numpad_enabled = config.get_bool_setting('Game', 'numpad_movement_enabled', True)
    show_damage = config.get_bool_setting('Display', 'show_damage_numbers', True)
    flash_damage = config.get_bool_setting('Display', 'flash_on_damage', True)
    
    print(f"Diagonal Movement: {'Enabled' if diagonal_enabled else 'Disabled'}")
    print(f"Numpad Movement: {'Enabled' if numpad_enabled else 'Disabled'}")
    print(f"Show Damage Numbers: {'Enabled' if show_damage else 'Disabled'}")
    print(f"Flash on Damage: {'Enabled' if flash_damage else 'Disabled'}")
    
    print("\n=== Numpad Layout ===")
    print("Standard roguelike numpad movement:")
    print("┌───┬───┬───┐")
    print("│ 7 │ 8 │ 9 │  ← Northwest, North, Northeast")
    print("├───┼───┼───┤")
    print("│ 4 │ 5 │ 6 │  ← West, Wait, East")
    print("├───┼───┼───┤")
    print("│ 1 │ 2 │ 3 │  ← Southwest, South, Southeast")
    print("└───┴───┴───┘")
    
    print("\n=== Configuration File ===")
    print(f"Configuration loaded from: {config.config_file}")
    print("You can edit this file to customize controls!")
    print("Key names use pygame constants (e.g., K_w, K_KP8, K_SPACE)")
    print("Multiple keys can be assigned to the same action using commas")
    print("Press F5 in-game to reload configuration")
    
    print("\n=== Demo Complete ===")
    print("Control system features:")
    print("✓ Configurable key bindings via .ini file")
    print("✓ 8-directional movement with diagonals")
    print("✓ Full numpad support for movement")
    print("✓ Multiple keys per action")
    print("✓ Runtime configuration reloading (F5)")
    print("✓ Boolean settings for enabling/disabling features")

def get_direction_name(dx: int, dy: int) -> str:
    """Get the name of a movement direction."""
    direction_names = {
        (0, -1): "North",
        (0, 1): "South",
        (-1, 0): "West",
        (1, 0): "East",
        (-1, -1): "Northwest",
        (1, -1): "Northeast",
        (-1, 1): "Southwest",
        (1, 1): "Southeast",
        (0, 0): "No Movement"
    }
    return direction_names.get((dx, dy), f"Unknown ({dx}, {dy})")

if __name__ == "__main__":
    demonstrate_controls() 