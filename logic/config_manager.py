#!/usr/bin/env python3
"""
Configuration Manager for Mythica Dungeon Crawler
Handles reading and parsing configuration files for key bindings and game settings.
"""

import configparser
import pygame
from typing import Dict, List, Set
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # Default configuration
        self.default_config = {
            'Controls': {
                'move_north': 'K_w,K_UP,K_KP8',
                'move_south': 'K_s,K_DOWN,K_KP2',
                'move_west': 'K_a,K_LEFT,K_KP4',
                'move_east': 'K_d,K_RIGHT,K_KP6',
                'move_northwest': 'K_KP7',
                'move_northeast': 'K_KP9',
                'move_southwest': 'K_KP1',
                'move_southeast': 'K_KP3',
                'character_sheet': 'K_c',
                'inventory': 'K_i',
                'wait_turn': 'K_KP5,K_PERIOD,K_SPACE',
                'quit_game': 'K_ESCAPE',
                'auto_explore': 'K_o',
                'go_down_stairs': 'K_RIGHTBRACKET',
                'go_up_stairs': 'K_LEFTBRACKET'
            },
            'Game': {
                'diagonal_movement_enabled': 'true',
                'numpad_movement_enabled': 'true',
                'continuous_movement_delay': '0.15',
                'continuous_hold_delay': '0.3'
            },
            'Display': {
                'show_damage_numbers': 'true',
                'flash_on_damage': 'true'
            }
        }
        
        # Key mappings
        self.key_mappings: Dict[str, Set[int]] = {}
        self.load_config()
        self.parse_key_mappings()
    
    def load_config(self):
        """Load configuration from file, create default if not exists."""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            print(f"Config file {self.config_file} not found, creating default...")
            self.create_default_config()
        
        try:
            self.config.read(self.config_file)
            print(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            print(f"Error reading config file: {e}")
            print("Using default configuration...")
            self.load_default_config()
    
    def create_default_config(self):
        """Create a default configuration file."""
        for section, options in self.default_config.items():
            self.config.add_section(section)
            for option, value in options.items():
                self.config.set(section, option, value)
        
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            print(f"Created default config file: {self.config_file}")
        except Exception as e:
            print(f"Error creating config file: {e}")
    
    def load_default_config(self):
        """Load default configuration into memory."""
        for section, options in self.default_config.items():
            self.config.add_section(section)
            for option, value in options.items():
                self.config.set(section, option, value)
    
    def parse_key_mappings(self):
        """Parse key strings into pygame key constants."""
        self.key_mappings = {}
        
        if not self.config.has_section('Controls'):
            print("No Controls section found in config!")
            return
        
        for action in self.config.options('Controls'):
            key_string = self.config.get('Controls', action)
            keys = self.parse_key_string(key_string)
            self.key_mappings[action] = keys
    
    def parse_key_string(self, key_string: str) -> Set[int]:
        """Parse a comma-separated string of key names into pygame key constants."""
        keys = set()
        
        for key_name in key_string.split(','):
            key_name = key_name.strip()
            
            try:
                # Get pygame key constant
                if hasattr(pygame, key_name):
                    key_value = getattr(pygame, key_name)
                    keys.add(key_value)
                else:
                    print(f"Warning: Unknown key '{key_name}' in config")
            except Exception as e:
                print(f"Error parsing key '{key_name}': {e}")
        
        return keys
    
    def is_key_pressed_for_action(self, action: str, pressed_key: int) -> bool:
        """Check if a pressed key corresponds to an action."""
        if action in self.key_mappings:
            return pressed_key in self.key_mappings[action]
        return False
    
    def is_action_currently_pressed(self, action: str, keys_pressed) -> bool:
        """Check if any key for the given action is currently being held down."""
        if action in self.key_mappings:
            for key_code in self.key_mappings[action]:
                if keys_pressed[key_code]:
                    return True
        return False
    
    def get_movement_direction_for_action(self, action: str) -> tuple:
        """Get movement direction for a specific action."""
        movement_map = {
            'move_north': (0, -1),
            'move_south': (0, 1),
            'move_west': (-1, 0),
            'move_east': (1, 0),
            'move_northwest': (-1, -1),
            'move_northeast': (1, -1),
            'move_southwest': (-1, 1),
            'move_southeast': (1, 1)
        }
        
        direction = movement_map.get(action, (0, 0))
        
        # Check if diagonal movement is enabled for diagonal actions
        if abs(direction[0]) + abs(direction[1]) == 2:  # Diagonal movement
            if self.get_bool_setting('Game', 'diagonal_movement_enabled', True):
                return direction
            else:
                return (0, 0)  # No movement if diagonals disabled
        
        return direction
    
    def get_movement_direction(self, pressed_key: int) -> tuple:
        """Get movement direction for a pressed key."""
        movement_map = {
            'move_north': (0, -1),
            'move_south': (0, 1),
            'move_west': (-1, 0),
            'move_east': (1, 0),
            'move_northwest': (-1, -1),
            'move_northeast': (1, -1),
            'move_southwest': (-1, 1),
            'move_southeast': (1, 1)
        }
        
        for action, direction in movement_map.items():
            if self.is_key_pressed_for_action(action, pressed_key):
                # Check if diagonal movement is enabled
                if abs(direction[0]) + abs(direction[1]) == 2:  # Diagonal movement
                    if self.get_bool_setting('Game', 'diagonal_movement_enabled', True):
                        return direction
                    else:
                        return (0, 0)  # No movement if diagonals disabled
                else:
                    return direction
        
        return (0, 0)  # No movement
    
    def get_bool_setting(self, section: str, option: str, default: bool = False) -> bool:
        """Get a boolean setting from the config."""
        try:
            if self.config.has_option(section, option):
                return self.config.getboolean(section, option)
        except Exception as e:
            print(f"Error reading {section}.{option}: {e}")
        return default
    
    def get_string_setting(self, section: str, option: str, default: str = "") -> str:
        """Get a string setting from the config."""
        try:
            if self.config.has_option(section, option):
                return self.config.get(section, option)
        except Exception as e:
            print(f"Error reading {section}.{option}: {e}")
        return default
    
    def get_float_setting(self, section: str, option: str, default: float = 0.0) -> float:
        """Get a float setting from the config."""
        try:
            if self.config.has_option(section, option):
                return self.config.getfloat(section, option)
        except Exception as e:
            print(f"Error reading {section}.{option}: {e}")
        return default
    
    def get_control_help_text(self) -> List[str]:
        """Get help text showing current key bindings."""
        help_text = []
        help_text.append("=== Current Key Bindings ===")
        
        if not self.config.has_section('Controls'):
            help_text.append("No controls configured!")
            return help_text
        
        # Movement controls
        help_text.append("Movement:")
        movement_actions = [
            ('move_north', 'North'),
            ('move_south', 'South'), 
            ('move_west', 'West'),
            ('move_east', 'East'),
            ('move_northwest', 'Northwest'),
            ('move_northeast', 'Northeast'),
            ('move_southwest', 'Southwest'),
            ('move_southeast', 'Southeast')
        ]
        
        for action, description in movement_actions:
            if action in self.key_mappings:
                keys = []
                for key_code in self.key_mappings[action]:
                    key_name = pygame.key.name(key_code)
                    keys.append(key_name)
                if keys:
                    help_text.append(f"  {description}: {', '.join(keys)}")
        
        # Other controls
        help_text.append("Other:")
        other_actions = [
            ('character_sheet', 'Character Sheet'),
            ('wait_turn', 'Wait/Rest'),
            ('quit_game', 'Quit Game')
        ]
        
        for action, description in other_actions:
            if action in self.key_mappings:
                keys = []
                for key_code in self.key_mappings[action]:
                    key_name = pygame.key.name(key_code)
                    keys.append(key_name)
                if keys:
                    help_text.append(f"  {description}: {', '.join(keys)}")
        
        # Settings
        help_text.append("")
        help_text.append("Settings:")
        diagonal_enabled = self.get_bool_setting('Game', 'diagonal_movement_enabled', True)
        numpad_enabled = self.get_bool_setting('Game', 'numpad_movement_enabled', True)
        help_text.append(f"  Diagonal Movement: {'Enabled' if diagonal_enabled else 'Disabled'}")
        help_text.append(f"  Numpad Movement: {'Enabled' if numpad_enabled else 'Disabled'}")
        
        return help_text
    
    def reload_config(self):
        """Reload configuration from file."""
        print("Reloading configuration...")
        self.load_config()
        self.parse_key_mappings()
        print("Configuration reloaded!")

# Global config instance
config = ConfigManager() 