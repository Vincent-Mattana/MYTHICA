#!/usr/bin/env python3
"""
Game States for Mythica Dungeon Crawler
Handles different game screens: Menu, Class Selection, Playing, Game Over
"""

import pygame
from enum import Enum
from typing import Dict, Optional, Tuple
from .character_system import Character, StatType, ItemGenerator, ItemType, EquipmentSlot
from .sprite_font import SpriteFont
from .sprite_manager import sprite_manager

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
        
        # Sprite Fonts
        self.title_font = SpriteFont(scale=2.0)  # Larger scale for title
        self.header_font = SpriteFont(scale=1.0)  # Medium scale for headers
        self.text_font = SpriteFont(scale=0.75)  # Normal scale for text
        self.small_font = SpriteFont(scale=0.5)  # Smaller scale for details
        
        # Colors
        self.bg_color = (20, 20, 30)
        self.text_color = (255, 255, 255)
        self.selected_color = (255, 255, 100)
        self.accent_color = (100, 150, 255)
        self.hover_color = (200, 200, 100)
        
        # Menu option rectangles for mouse interaction
        self.menu_option_rects = []  # List of (rect, index) tuples for main menu
        self.class_option_rects = []  # List of (rect, index) tuples for class selection
        self.game_over_option_rects = []  # List of (rect, index) tuples for game over screen
    
    def handle_input(self, event) -> Tuple[bool, Optional[Character]]:
        """
        Handle input for current state.
        Returns (continue_game, character) where continue_game indicates if we should keep running.
        """
        if event.type == pygame.KEYDOWN:
            if self.current_state == GameState.MENU:
                return self._handle_menu_input(event.key)
            elif self.current_state == GameState.CLASS_SELECTION:
                return self._handle_class_selection_input(event.key)
            elif self.current_state == GameState.GAME_OVER:
                return self._handle_game_over_input(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            if self.current_state == GameState.MENU:
                return self._handle_menu_mouse_click(event.pos)
            elif self.current_state == GameState.CLASS_SELECTION:
                return self._handle_class_selection_mouse_click(event.pos)
            elif self.current_state == GameState.GAME_OVER:
                return self._handle_game_over_mouse_click(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_hover(event.pos)
        
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
        # Clear previous option rectangles
        self.menu_option_rects = []
        
        # Title
        title_rect = self.title_font.render_text_centered("MYTHICA", (512, 150), self.accent_color)
        subtitle_rect = self.text_font.render_text_centered("DUNGEON CRAWLER", (512, 200), self.text_color)
        
        # Menu options
        menu_options = ["NEW GAME", "QUIT"]
        start_y = 300
        
        for i, option in enumerate(menu_options):
            color = self.selected_color if i == self.menu_selection else self.text_color
            text_rect = self.header_font.render_text_centered(option, (512, start_y + i * 60), color)
            # Add padding to the clickable area
            padded_rect = text_rect.inflate(40, 20)
            self.menu_option_rects.append((padded_rect, i))
        
        # Controls
        controls = [
            "USE W/S OR UP/DOWN TO NAVIGATE",
            "CLICK OR PRESS ENTER/SPACE TO SELECT",
            "PRESS ESCAPE TO QUIT"
        ]
        
        for i, control in enumerate(controls):
            self.small_font.render_text_centered(control, (512, 500 + i * 25), self.text_color)
    
    def _render_class_selection(self):
        """Render the class selection screen."""
        # Clear previous option rectangles
        self.class_option_rects = []
        
        # Draw dividing line
        pygame.draw.line(self.screen, self.accent_color, (256, 0), (256, 768), 2)
        
        # Load portraits if not already loaded
        if not hasattr(self, 'class_portraits'):
            self.class_portraits = {}
            portrait_sheet = pygame.image.load(str(sprite_manager.assets_path / "oryx_roguelike_2.0" / "oryx_roguelike_2.0" / "Interface_Portraits.png")).convert_alpha()
            # Portrait positions in the sheet (x, y)
            portrait_positions = {
                CharacterClass.WARRIOR: (0, 0),    # First portrait - warrior
                CharacterClass.ROGUE: (48, 0),     # Second portrait - rogue/thief
                CharacterClass.MAGE: (96, 0),      # Third portrait - mage/wizard
                CharacterClass.RANGER: (144, 0),   # Fourth portrait - ranger/archer
                CharacterClass.CLERIC: (192, 0)    # Fifth portrait - cleric/priest
            }
            for char_class, pos in portrait_positions.items():
                portrait = pygame.Surface((48, 48), pygame.SRCALPHA)
                portrait.blit(portrait_sheet, (0, 0), (pos[0], pos[1], 48, 48))
                self.class_portraits[char_class] = portrait

        # Class list (left side)
        classes = list(CharacterClass)
        start_y = 100
        spacing = 80  # Increased spacing to accommodate portraits
        
        for i, char_class in enumerate(classes):
            y_pos = start_y + i * spacing
            color = self.selected_color if i == self.class_selection else self.text_color
            
            # Draw portrait
            portrait = self.class_portraits[char_class]
            portrait_rect = portrait.get_rect(midleft=(32, y_pos))
            self.screen.blit(portrait, portrait_rect)
            
            # Draw class name
            text_rect = self.text_font.render_text_centered(char_class.value.upper(), (160, y_pos), color)
            # Add padding to the clickable area (include portrait area)
            padded_rect = pygame.Rect(16, y_pos - 30, 224, 60)
            self.class_option_rects.append((padded_rect, i))
        
        # Class details (right side)
        selected_class = classes[self.class_selection]
        class_data = CharacterClassData.CLASS_DEFINITIONS[selected_class]
        right_x = 640  # Center point for right side
        
        # Draw large portrait for selected class
        portrait = self.class_portraits[selected_class]
        large_portrait = pygame.transform.scale(portrait, (96, 96))
        portrait_rect = large_portrait.get_rect(midtop=(right_x, 40))
        self.screen.blit(large_portrait, portrait_rect)

        # Class name and description
        self.title_font.render_text_centered(selected_class.value.upper(), (right_x, 160), self.accent_color)
        
        # Description - split into two lines
        desc_y = 220
        desc = class_data['description'].upper()
        words = desc.split()
        mid = len(words) // 2
        line1 = ' '.join(words[:mid])
        line2 = ' '.join(words[mid:])
        self.text_font.render_text_centered(line1, (right_x, desc_y), self.text_color)
        self.text_font.render_text_centered(line2, (right_x, desc_y + 30), self.text_color)
        
        # Stats
        stats_y = 320
        self.header_font.render_text_centered("STARTING STATS", (right_x, stats_y), self.accent_color)
        stats_y += 50
        
        # Stats in a clean layout
        for stat, value in class_data['stats'].items():
            stat_text = f"{stat.value} {value}"
            self.text_font.render_text_centered(stat_text.upper(), (right_x, stats_y), self.text_color)
            stats_y += 30
        
        # Equipment
        equip_y = stats_y + 40
        self.header_font.render_text_centered("STARTING EQUIPMENT", (right_x, equip_y), self.accent_color)
        equip_y += 50
        
        # Equipment items in a clean layout
        for item_type, item_name, bonuses in class_data['starting_items']:
            self.text_font.render_text_centered(item_name.upper(), (right_x, equip_y), self.text_color)
            equip_y += 30
    
    def _render_game_over(self):
        """Render the game over screen."""
        # Clear previous option rectangles
        self.game_over_option_rects = []
        
        # Semi-transparent overlay
        overlay = pygame.Surface((1024, 768))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Game Over title
        self.title_font.render_text_centered("GAME OVER", (512, 250), (255, 100, 100))
        
        # Options
        options = ["RESTART", "QUIT TO MENU"]
        start_y = 350
        
        for i, option in enumerate(options):
            color = self.selected_color if i == self.game_over_selection else self.text_color
            text_rect = self.header_font.render_text_centered(option, (512, start_y + i * 60), color)
            # Add padding to the clickable area
            padded_rect = text_rect.inflate(40, 20)
            self.game_over_option_rects.append((padded_rect, i))
        
        # Controls
        self.small_font.render_text_centered(
            "W/S: NAVIGATE * CLICK OR PRESS ENTER TO SELECT * ESCAPE: QUIT",
            (512, 500),
            self.text_color
        )
    
    def _handle_menu_mouse_click(self, pos: Tuple[int, int]) -> Tuple[bool, Optional[Character]]:
        """Handle mouse clicks in the main menu."""
        for rect, index in self.menu_option_rects:
            if rect.collidepoint(pos):
                self.menu_selection = index
                if index == 0:  # New Game
                    self.current_state = GameState.CLASS_SELECTION
                    return True, None
                elif index == 1:  # Quit
                    return False, None
        return True, None

    def _handle_class_selection_mouse_click(self, pos: Tuple[int, int]) -> Tuple[bool, Optional[Character]]:
        """Handle mouse clicks in the class selection screen."""
        for rect, index in self.class_option_rects:
            if rect.collidepoint(pos):
                self.class_selection = index
                classes = list(CharacterClass)
                selected_class = classes[self.class_selection]
                character = CharacterClassData.create_character(selected_class, "Adventurer")
                self.current_state = GameState.PLAYING
                return True, character
        return True, None

    def _handle_game_over_mouse_click(self, pos: Tuple[int, int]) -> Tuple[bool, Optional[Character]]:
        """Handle mouse clicks in the game over screen."""
        for rect, index in self.game_over_option_rects:
            if rect.collidepoint(pos):
                self.game_over_selection = index
                if index == 0:  # Restart
                    self.current_state = GameState.CLASS_SELECTION
                    self.class_selection = 0
                    return True, None
                elif index == 1:  # Quit
                    return False, None
        return True, None

    def _handle_mouse_hover(self, pos: Tuple[int, int]):
        """Handle mouse hover effects for menu options."""
        if self.current_state == GameState.MENU:
            for rect, index in self.menu_option_rects:
                if rect.collidepoint(pos):
                    self.menu_selection = index
                    break
        elif self.current_state == GameState.CLASS_SELECTION:
            for rect, index in self.class_option_rects:
                if rect.collidepoint(pos):
                    self.class_selection = index
                    break
        elif self.current_state == GameState.GAME_OVER:
            for rect, index in self.game_over_option_rects:
                if rect.collidepoint(pos):
                    self.game_over_selection = index
                    break

    def show_game_over(self):
        """Transition to game over state."""
        self.current_state = GameState.GAME_OVER
        self.game_over_selection = 0 