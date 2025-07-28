#!/usr/bin/env python3
"""
Game States for Mythica Dungeon Crawler
Handles different game screens: Menu, Class Selection, Playing, Game Over
"""

import pygame
from enum import Enum
from typing import Dict, Optional, Tuple
from .character_system import Character, StatType, ItemGenerator, ItemType, EquipmentSlot

class GameState(Enum):
    MENU = "menu"
    CLASS_SELECTION = "class_selection"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    PAUSED = "paused"

class CharacterClass(Enum):
    WARRIOR = "Warrior"
    ROGUE = "Rogue"
    MAGE = "Mage"
    RANGER = "Ranger"
    CLERIC = "Cleric"

class CharacterClassData:
    """Defines starting stats and equipment for each character class."""
    
    CLASS_DEFINITIONS = {
        CharacterClass.WARRIOR: {
            'description': 'Strong and tough, excels in combat',
            'stats': {
                StatType.STRENGTH: 15,
                StatType.DEXTERITY: 8,
                StatType.CONSTITUTION: 14,
                StatType.PERCEPTION: 10,
                StatType.LUCK: 8
            },
            'starting_items': [
                (ItemType.WEAPON, 'Iron Sword', {StatType.STRENGTH: 3}),
                (ItemType.ARMOUR, 'Chain Mail', {StatType.CONSTITUTION: 2}),
                (ItemType.HELMET, 'Iron Helm', {StatType.CONSTITUTION: 1})
            ]
        },
        CharacterClass.ROGUE: {
            'description': 'Fast and sneaky, masters of stealth',
            'stats': {
                StatType.STRENGTH: 9,
                StatType.DEXTERITY: 15,
                StatType.CONSTITUTION: 10,
                StatType.PERCEPTION: 13,
                StatType.LUCK: 12
            },
            'starting_items': [
                (ItemType.WEAPON, 'Steel Dagger', {StatType.DEXTERITY: 2, StatType.LUCK: 1}),
                (ItemType.ARMOUR, 'Leather Armour', {StatType.DEXTERITY: 2}),
                (ItemType.RING, 'Lucky Ring', {StatType.LUCK: 2})
            ]
        },
        CharacterClass.MAGE: {
            'description': 'Wise and perceptive, masters of magic',
            'stats': {
                StatType.STRENGTH: 7,
                StatType.DEXTERITY: 11,
                StatType.CONSTITUTION: 9,
                StatType.PERCEPTION: 16,
                StatType.LUCK: 11
            },
            'starting_items': [
                (ItemType.WEAPON, 'Magic Staff', {StatType.PERCEPTION: 3}),
                (ItemType.ARMOUR, 'Mage Robes', {StatType.PERCEPTION: 2}),
                (ItemType.AMULET, 'Wise Pendant', {StatType.PERCEPTION: 1, StatType.LUCK: 1})
            ]
        },
        CharacterClass.RANGER: {
            'description': 'Balanced and perceptive, masters of the wild',
            'stats': {
                StatType.STRENGTH: 11,
                StatType.DEXTERITY: 13,
                StatType.CONSTITUTION: 12,
                StatType.PERCEPTION: 14,
                StatType.LUCK: 10
            },
            'starting_items': [
                (ItemType.WEAPON, 'Hunter\'s Bow', {StatType.DEXTERITY: 2, StatType.PERCEPTION: 1}),
                (ItemType.ARMOUR, 'Leather Armour', {StatType.DEXTERITY: 1}),
                (ItemType.BOOTS, 'Swift Boots', {StatType.DEXTERITY: 2})
            ]
        },
        CharacterClass.CLERIC: {
            'description': 'Hardy and wise, blessed by divine power',
            'stats': {
                StatType.STRENGTH: 10,
                StatType.DEXTERITY: 9,
                StatType.CONSTITUTION: 15,
                StatType.PERCEPTION: 12,
                StatType.LUCK: 14
            },
            'starting_items': [
                (ItemType.WEAPON, 'Holy Mace', {StatType.STRENGTH: 1, StatType.LUCK: 2}),
                (ItemType.ARMOUR, 'Blessed Mail', {StatType.CONSTITUTION: 2}),
                (ItemType.AMULET, 'Divine Symbol', {StatType.LUCK: 2, StatType.CONSTITUTION: 1})
            ]
        }
    }
    
    @staticmethod
    def create_character(character_class: CharacterClass, name: str = "Hero") -> Character:
        """Create a character with class-specific stats and equipment."""
        class_data = CharacterClassData.CLASS_DEFINITIONS[character_class]
        
        # Create character
        character = Character(name)
        
        # Set character class for perk system
        character.set_character_class(character_class)
        
        # Set class-specific base stats
        for stat, value in class_data['stats'].items():
            character.stats.base_stats[stat] = value
        
        # Clear default equipment
        character.equipment = ItemGenerator.generate_starting_equipment()
        for slot in EquipmentSlot:
            character.equipment.unequip_item(slot)
        
        # Add class-specific starting items
        for item_type, item_name, stat_bonuses in class_data['starting_items']:
            item = ItemGenerator.create_item_with_stats(item_name, item_type, stat_bonuses)
            
            # Find appropriate slot for the item
            slot = CharacterClassData._get_slot_for_item(item_type)
            if slot:
                character.equipment.equip_item(item, slot)
        
        # Update equipment bonuses and HP
        character._update_equipment_bonuses()
        
        return character
    
    @staticmethod
    def _get_slot_for_item(item_type: ItemType) -> Optional[EquipmentSlot]:
        """Get the appropriate equipment slot for an item type."""
        slot_mapping = {
            ItemType.HELMET: EquipmentSlot.HEAD,
            ItemType.ARMOUR: EquipmentSlot.TORSO,
            ItemType.BOOTS: EquipmentSlot.LEGS,
            ItemType.WEAPON: EquipmentSlot.WEAPON_1,
            ItemType.RING: EquipmentSlot.RING_1,
            ItemType.AMULET: EquipmentSlot.NECK
        }
        return slot_mapping.get(item_type)

class GameStateManager:
    """Manages game state transitions and UI rendering."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.current_state = GameState.MENU
        self.selected_class = CharacterClass.WARRIOR
        self.menu_selection = 0
        self.class_selection = 0
        self.game_over_selection = 0
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.header_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Colors
        self.bg_color = (20, 20, 30)
        self.text_color = (255, 255, 255)
        self.selected_color = (255, 255, 100)
        self.accent_color = (100, 150, 255)
    
    def handle_input(self, event) -> Tuple[bool, Optional[Character]]:
        """
        Handle input for current state.
        Returns (continue_game, character) where continue_game indicates if we should keep running.
        """
        if event.type != pygame.KEYDOWN:
            return True, None
        
        if self.current_state == GameState.MENU:
            return self._handle_menu_input(event.key)
        elif self.current_state == GameState.CLASS_SELECTION:
            return self._handle_class_selection_input(event.key)
        elif self.current_state == GameState.GAME_OVER:
            return self._handle_game_over_input(event.key)
        
        return True, None
    
    def _handle_menu_input(self, key) -> Tuple[bool, Optional[Character]]:
        """Handle main menu input."""
        if key == pygame.K_UP or key == pygame.K_w:
            self.menu_selection = max(0, self.menu_selection - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.menu_selection = min(1, self.menu_selection + 1)
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            if self.menu_selection == 0:  # New Game
                self.current_state = GameState.CLASS_SELECTION
            elif self.menu_selection == 1:  # Quit
                return False, None
        elif key == pygame.K_ESCAPE:
            return False, None
        
        return True, None
    
    def _handle_class_selection_input(self, key) -> Tuple[bool, Optional[Character]]:
        """Handle class selection input."""
        classes = list(CharacterClass)
        
        if key == pygame.K_UP or key == pygame.K_w:
            self.class_selection = (self.class_selection - 1) % len(classes)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.class_selection = (self.class_selection + 1) % len(classes)
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            # Create character and start game
            selected_class = classes[self.class_selection]
            character = CharacterClassData.create_character(selected_class, "Adventurer")
            self.current_state = GameState.PLAYING
            return True, character
        elif key == pygame.K_ESCAPE:
            self.current_state = GameState.MENU
        
        return True, None
    
    def _handle_game_over_input(self, key) -> Tuple[bool, Optional[Character]]:
        """Handle game over screen input."""
        if key == pygame.K_UP or key == pygame.K_w:
            self.game_over_selection = max(0, self.game_over_selection - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.game_over_selection = min(1, self.game_over_selection + 1)
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            if self.game_over_selection == 0:  # Restart
                self.current_state = GameState.CLASS_SELECTION
                self.class_selection = 0
            elif self.game_over_selection == 1:  # Quit
                return False, None
        elif key == pygame.K_ESCAPE:
            return False, None
        
        return True, None
    
    def render(self):
        """Render the current state."""
        self.screen.fill(self.bg_color)
        
        if self.current_state == GameState.MENU:
            self._render_main_menu()
        elif self.current_state == GameState.CLASS_SELECTION:
            self._render_class_selection()
        elif self.current_state == GameState.GAME_OVER:
            self._render_game_over()
    
    def _render_main_menu(self):
        """Render the main menu."""
        # Title
        title = self.title_font.render("MYTHICA", True, self.accent_color)
        title_rect = title.get_rect(center=(512, 150))
        self.screen.blit(title, title_rect)
        
        subtitle = self.text_font.render("Dungeon Crawler", True, self.text_color)
        subtitle_rect = subtitle.get_rect(center=(512, 200))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Menu options
        menu_options = ["New Game", "Quit"]
        start_y = 300
        
        for i, option in enumerate(menu_options):
            color = self.selected_color if i == self.menu_selection else self.text_color
            text = self.header_font.render(option, True, color)
            text_rect = text.get_rect(center=(512, start_y + i * 60))
            self.screen.blit(text, text_rect)
        
        # Controls
        controls = [
            "Use W/S or Up/Down to navigate",
            "Press Enter or Space to select",
            "Press Escape to quit"
        ]
        
        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, self.text_color)
            text_rect = text.get_rect(center=(512, 500 + i * 25))
            self.screen.blit(text, text_rect)
    
    def _render_class_selection(self):
        """Render the class selection screen."""
        # Title
        title = self.header_font.render("Choose Your Class", True, self.accent_color)
        title_rect = title.get_rect(center=(512, 50))
        self.screen.blit(title, title_rect)
        
        # Class list
        classes = list(CharacterClass)
        start_y = 120
        
        for i, char_class in enumerate(classes):
            color = self.selected_color if i == self.class_selection else self.text_color
            text = self.text_font.render(char_class.value, True, color)
            self.screen.blit(text, (50, start_y + i * 40))
        
        # Selected class details
        selected_class = classes[self.class_selection]
        class_data = CharacterClassData.CLASS_DEFINITIONS[selected_class]
        
        # Class description
        desc_y = 150
        desc_text = self.text_font.render(class_data['description'], True, self.text_color)
        self.screen.blit(desc_text, (400, desc_y))
        
        # Stats
        stats_y = 200
        stats_title = self.text_font.render("Starting Stats:", True, self.accent_color)
        self.screen.blit(stats_title, (400, stats_y))
        
        for i, (stat, value) in enumerate(class_data['stats'].items()):
            stat_text = f"{stat.value}: {value}"
            text = self.small_font.render(stat_text, True, self.text_color)
            self.screen.blit(text, (400, stats_y + 30 + i * 25))
        
        # Starting equipment
        equip_y = 350
        equip_title = self.text_font.render("Starting Equipment:", True, self.accent_color)
        self.screen.blit(equip_title, (400, equip_y))
        
        for i, (item_type, item_name, bonuses) in enumerate(class_data['starting_items']):
            text = self.small_font.render(f"• {item_name}", True, self.text_color)
            self.screen.blit(text, (400, equip_y + 30 + i * 25))
        
        # Controls
        controls = [
            "W/S: Navigate classes",
            "Enter: Select class",
            "Escape: Back to menu"
        ]
        
        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, self.text_color)
            self.screen.blit(text, (50, 600 + i * 25))
    
    def _render_game_over(self):
        """Render the game over screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((1024, 768))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Game Over title
        title = self.title_font.render("GAME OVER", True, (255, 100, 100))
        title_rect = title.get_rect(center=(512, 250))
        self.screen.blit(title, title_rect)
        
        # Options
        options = ["Restart", "Quit to Menu"]
        start_y = 350
        
        for i, option in enumerate(options):
            color = self.selected_color if i == self.game_over_selection else self.text_color
            text = self.header_font.render(option, True, color)
            text_rect = text.get_rect(center=(512, start_y + i * 60))
            self.screen.blit(text, text_rect)
        
        # Controls
        controls_text = self.small_font.render("W/S: Navigate, Enter: Select, Escape: Quit", 
                                             True, self.text_color)
        controls_rect = controls_text.get_rect(center=(512, 500))
        self.screen.blit(controls_text, controls_rect)
    
    def show_game_over(self):
        """Transition to game over state."""
        self.current_state = GameState.GAME_OVER
        self.game_over_selection = 0 