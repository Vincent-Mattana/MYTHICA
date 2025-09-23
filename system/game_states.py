#!/usr/bin/env python3
"""
Game States for Treasure Goblin
Handles different game screens: Menu, Class Selection, Playing, Game Over
"""

import pygame
from enum import Enum
from typing import Dict, Optional, Tuple, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from main import Game
from .character_system import Character, StatType, ItemGenerator, ItemType, EquipmentSlot, Equipment
from .turn_system import ActionType
from .goblin_font import GoblinFontManager
from .sprite_font import SpriteFont

class GameState(Enum):
    MENU = "menu"
    CLASS_SELECTION = "class_selection"
    NAME_ENTRY = "name_entry"
    PLAYING = "playing"
    TARGETING = "targeting"  # For ranged attacks and abilities
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
                (ItemType.RANGED_WEAPON, 'Hunter\'s Bow', {StatType.DEXTERITY: 2, StatType.PERCEPTION: 1}),
                (ItemType.AMMUNITION, 'Wooden Arrows', {StatType.DEXTERITY: 1}),
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
        
        # Create character without random generation
        character = Character(name, skip_random_generation=True)
        
        # Set character class for perk system
        character.set_character_class(character_class)
        
        # Set class-specific base stats
        for stat, value in class_data['stats'].items():
            character.stats.base_stats[stat] = value
        
        # Create empty equipment
        character.equipment = Equipment()
        
        # Add starting items
        for item_type, name, stat_bonuses in class_data['starting_items']:
            item = ItemGenerator.create_item_with_stats(name, item_type, stat_bonuses)
            if item_type == ItemType.AMMUNITION:
                # Add 20 arrows to start with
                for _ in range(20):
                    character.inventory.add_item(item)
            else:
                # Try to equip the item
                slot = CharacterClassData._get_slot_for_item(item_type)
                if slot:
                    character.equipment.equip_item(item, slot)
                else:
                    # If can't equip, add to inventory
                    character.inventory.add_item(item)
        
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
            ItemType.RANGED_WEAPON: EquipmentSlot.WEAPON_1,
            ItemType.RING: EquipmentSlot.RING_1,
            ItemType.AMULET: EquipmentSlot.NECK
        }
        return slot_mapping.get(item_type)

class GameStateManager:
    """Manages game state transitions and UI rendering."""
    
    def __init__(self, screen: pygame.Surface, game=None):
        self.screen = screen
        self.game = game
        self.current_state = GameState.MENU
        self.selected_class = CharacterClass.WARRIOR
        self.menu_selection = 0
        self.class_selection = 0
        self.game_over_selection = 0
        self.name_entry_text = ""
        self.name_entry_cursor_pos = 0
        
        # Use simple default fonts for crisp text rendering
        self.title_font = pygame.font.Font(None, 64)
        self.header_font = pygame.font.Font(None, 42)
        self.text_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        print("Using default pygame fonts for crisp text rendering")
        
        # Clean menu colors with goblin green selection
        self.bg_color = (0, 0, 0)  # Pure black background
        self.text_color = (255, 255, 255)  # Pure white text for maximum legibility
        self.selected_color = (0, 255, 0)  # Goblin green for selected items
        self.accent_color = (255, 255, 255)  # White for all text elements
        self.hover_color = (0, 255, 0)  # Goblin green for hover
        
        # Menu option rectangles for mouse interaction
        self.menu_option_rects = []  # List of (rect, index) tuples for main menu
        self.class_option_rects = []  # List of (rect, index) tuples for class selection
        self.game_over_option_rects = []  # List of (rect, index) tuples for game over screen
        
        # Background image
        self.background_image = None
        self.original_background = None
        self._load_background_image()
        
        # Initialize goblin font system
        self.goblin_font = GoblinFontManager()
        print(f"Goblin font system loaded: {self.goblin_font.is_loaded()}")
    
    def _load_background_image(self):
        """Load the background image for the main menu with proper aspect ratio maintenance."""
        import os
        print("DEBUG: Starting background image loading...")
        try:
            # Try multiple possible paths for the background image
            possible_paths = [
                "Screenshot 2025-09-18 at 19.42.52.png",
                "./Screenshot 2025-09-18 at 19.42.52.png",
                os.path.join(os.getcwd(), "Screenshot 2025-09-18 at 19.42.52.png")
            ]
            
            print(f"DEBUG: Current working directory: {os.getcwd()}")
            
            background_path = None
            for path in possible_paths:
                print(f"DEBUG: Checking path: {path}")
                if os.path.exists(path):
                    background_path = path
                    print(f"DEBUG: Found background image at: {path}")
                    break
                else:
                    print(f"DEBUG: Path not found: {path}")
            
            if not background_path:
                print(f"ERROR: Background image file not found in any of these locations:")
                for path in possible_paths:
                    print(f"  - {path}")
                self.background_image = None
                self.original_background = None
                return
            
            # Load the background image
            raw_image = pygame.image.load(background_path)
            self.original_background = raw_image.convert_alpha()  # Convert for better performance
            self._resize_background()
            
            print(f"Background image loaded successfully: {background_path}")
            print(f"Original image size: {self.original_background.get_size()}")
            
        except pygame.error as e:
            print(f"Could not load background image: {e}")
            self.background_image = None
            self.original_background = None
        except Exception as e:
            print(f"Unexpected error loading background: {e}")
            self.background_image = None
            self.original_background = None
    
    def _resize_background(self):
        """Resize background image to maintain aspect ratio and fill screen with darkened areas."""
        if not self.original_background:
            print("DEBUG: No original background to resize")
            return
            
        screen_width, screen_height = self.screen.get_size()
        img_width, img_height = self.original_background.get_size()
        
        print(f"DEBUG: Resizing background - Screen: {screen_width}x{screen_height}, Image: {img_width}x{img_height}")
        
        # Calculate scale factors to maintain aspect ratio
        scale_x = screen_width / img_width
        scale_y = screen_height / img_height
        
        # Use the larger scale to ensure the image covers the entire screen
        scale = max(scale_x, scale_y)
        
        print(f"DEBUG: Scale factors - X: {scale_x:.2f}, Y: {scale_y:.2f}, Using: {scale:.2f}")
        
        # Calculate new dimensions
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        print(f"DEBUG: New scaled dimensions: {new_width}x{new_height}")
        
        # Scale the image
        try:
            scaled_image = pygame.transform.scale(self.original_background, (new_width, new_height))
            print("DEBUG: Image scaling successful")
        except Exception as e:
            print(f"DEBUG: Error scaling image: {e}")
            return
        
        # Create a darkened version
        darkened_image = scaled_image.copy()
        dark_overlay = pygame.Surface((new_width, new_height), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 120))  # Black overlay with alpha
        try:
            darkened_image.blit(dark_overlay, (0, 0), special_flags=pygame.BLEND_ALPHA)
        except AttributeError:
            # Fallback if BLEND_ALPHA not available
            darkened_image.blit(dark_overlay, (0, 0))
        
        # Create the final background surface
        self.background_image = pygame.Surface((screen_width, screen_height))
        
        # Fill with a dark green/black goblin-themed background for uncovered areas
        self.background_image.fill((10, 20, 10))  # Very dark green
        
        # Calculate position to center the image
        x_offset = (screen_width - new_width) // 2
        y_offset = (screen_height - new_height) // 2
        
        print(f"DEBUG: Centering image at offset: ({x_offset}, {y_offset})")
        
        # Blit the darkened image to the background
        self.background_image.blit(darkened_image, (x_offset, y_offset))
        
        print("DEBUG: Background resize completed successfully")
    
    def handle_resize(self, event):
        """Handle window resize events."""
        if event.type == pygame.VIDEORESIZE:
            # Update screen size
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            # Resize background image
            if self.original_background:
                self._resize_background()
            
            return True
        return False
    
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
            elif self.current_state == GameState.NAME_ENTRY:
                return self._handle_name_entry_input(event.key)
            elif self.current_state == GameState.GAME_OVER:
                return self._handle_game_over_input(event.key)
            elif self.current_state == GameState.TARGETING:
                return self._handle_targeting_input(event.key)
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
        if key in (pygame.K_UP, pygame.K_w, pygame.K_KP8):
            self.menu_selection = max(0, self.menu_selection - 1)
        elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_KP2):
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
        
        if key in (pygame.K_UP, pygame.K_w, pygame.K_KP8):
            self.class_selection = (self.class_selection - 1) % len(classes)
        elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_KP2):
            self.class_selection = (self.class_selection + 1) % len(classes)
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            # Go to name entry screen
            self.current_state = GameState.NAME_ENTRY
            return True, None
        elif key == pygame.K_ESCAPE:
            self.current_state = GameState.MENU
            
        return True, None
    
    def _handle_name_entry_input(self, key) -> Tuple[bool, Optional[Character]]:
        """Handle name entry input."""
        if key == pygame.K_RETURN:
            # Confirm name and create character
            if self.name_entry_text.strip():
                selected_class = list(CharacterClass)[self.class_selection]
                character = CharacterClassData.create_character(selected_class)
                character.name = self.name_entry_text.strip()
                self.current_state = GameState.PLAYING
                return True, character
        elif key == pygame.K_BACKSPACE:
            # Delete character
            if self.name_entry_cursor_pos > 0:
                self.name_entry_text = (self.name_entry_text[:self.name_entry_cursor_pos-1] + 
                                      self.name_entry_text[self.name_entry_cursor_pos:])
                self.name_entry_cursor_pos -= 1
        elif key == pygame.K_ESCAPE:
            # Go back to class selection
            self.current_state = GameState.CLASS_SELECTION
            self.name_entry_text = ""
            self.name_entry_cursor_pos = 0
        elif key == pygame.K_LEFT and self.name_entry_cursor_pos > 0:
            # Move cursor left
            self.name_entry_cursor_pos -= 1
        elif key == pygame.K_RIGHT and self.name_entry_cursor_pos < len(self.name_entry_text):
            # Move cursor right
            self.name_entry_cursor_pos += 1
        elif key == pygame.K_DELETE and self.name_entry_cursor_pos < len(self.name_entry_text):
            # Delete character at cursor
            self.name_entry_text = (self.name_entry_text[:self.name_entry_cursor_pos] + 
                                  self.name_entry_text[self.name_entry_cursor_pos+1:])
        elif key == pygame.K_HOME:
            # Move cursor to beginning
            self.name_entry_cursor_pos = 0
        elif key == pygame.K_END:
            # Move cursor to end
            self.name_entry_cursor_pos = len(self.name_entry_text)
        elif len(self.name_entry_text) < 20:  # Limit name length
            # Add character
            char = None
            if pygame.K_a <= key <= pygame.K_z:
                char = chr(key)
            elif pygame.K_0 <= key <= pygame.K_9:
                char = chr(key)
            elif key == pygame.K_SPACE:
                char = ' '
            elif key == pygame.K_MINUS:
                char = '-'
            elif key == pygame.K_UNDERSCORE:
                char = '_'
            
            if char:
                self.name_entry_text = (self.name_entry_text[:self.name_entry_cursor_pos] + 
                                      char + self.name_entry_text[self.name_entry_cursor_pos:])
                self.name_entry_cursor_pos += 1
        
        return True, None
    
    def _handle_targeting_input(self, key) -> Tuple[bool, Optional[Character]]:
        """Handle input while in targeting mode."""
        if key == pygame.K_ESCAPE:
            self.current_state = GameState.PLAYING
        elif key == pygame.K_RETURN:
            # Fire projectile if target is valid
            game = self._get_game_instance()
            if game and game.targeting_valid:
                # Check if player has a ranged weapon equipped
                weapon = game.player.character.equipment.get_equipped_item(EquipmentSlot.WEAPON_1)
                if weapon and weapon.is_ranged_weapon():
                    # Check if player has ammunition
                    if game.player.character.has_ammunition():
                        # Schedule ranged attack
                        dexterity = game.player.character.stats.get_total_stat(StatType.DEXTERITY)
                        game.turn_manager.schedule_player_action(
                            ActionType.RANGED_ATTACK,
                            target_pos=(game.targeting_x, game.targeting_y),
                            dexterity=dexterity
                        )
                        game.add_to_log("You fire your bow!", (255, 255, 255))
                    else:
                        game.add_to_log("You have no arrows!", (255, 0, 0))
                else:
                    game.add_to_log("You need a bow equipped!", (255, 0, 0))
            self.current_state = GameState.PLAYING
        elif key in (pygame.K_UP, pygame.K_w, pygame.K_KP8):
            # Move cursor up
            game = self._get_game_instance()
            if game:
                game.targeting_y = max(0, game.targeting_y - 1)
                game.update_targeting_validity()
        elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_KP2):
            # Move cursor down
            game = self._get_game_instance()
            if game:
                game.targeting_y = min(game.dungeon.height - 1, game.targeting_y + 1)
                game.update_targeting_validity()
        elif key in (pygame.K_LEFT, pygame.K_a, pygame.K_KP4):
            # Move cursor left
            game = self._get_game_instance()
            if game:
                game.targeting_x = max(0, game.targeting_x - 1)
                game.update_targeting_validity()
        elif key in (pygame.K_RIGHT, pygame.K_d, pygame.K_KP6):
            # Move cursor right
            game = self._get_game_instance()
            if game:
                game.targeting_x = min(game.dungeon.width - 1, game.targeting_x + 1)
                game.update_targeting_validity()
        elif key in (pygame.K_KP7,):  # Northwest
            game = self._get_game_instance()
            if game:
                game.targeting_x = max(0, game.targeting_x - 1)
                game.targeting_y = max(0, game.targeting_y - 1)
                game.update_targeting_validity()
        elif key in (pygame.K_KP9,):  # Northeast
            game = self._get_game_instance()
            if game:
                game.targeting_x = min(game.dungeon.width - 1, game.targeting_x + 1)
                game.targeting_y = max(0, game.targeting_y - 1)
                game.update_targeting_validity()
        elif key in (pygame.K_KP1,):  # Southwest
            game = self._get_game_instance()
            if game:
                game.targeting_x = max(0, game.targeting_x - 1)
                game.targeting_y = min(game.dungeon.height - 1, game.targeting_y + 1)
                game.update_targeting_validity()
        elif key in (pygame.K_KP3,):  # Southeast
            game = self._get_game_instance()
            if game:
                game.targeting_x = min(game.dungeon.width - 1, game.targeting_x + 1)
                game.targeting_y = min(game.dungeon.height - 1, game.targeting_y + 1)
                game.update_targeting_validity()
        
        return True, None
    
    def _get_game_instance(self) -> Optional['Game']:
        """Get the Game instance from the main module."""
        import sys
        main_module = sys.modules.get('__main__')
        if main_module and hasattr(main_module, 'game'):
            return main_module.game
        return None
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
        if key in (pygame.K_UP, pygame.K_w, pygame.K_KP8):
            self.game_over_selection = max(0, self.game_over_selection - 1)
        elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_KP2):
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
        elif self.current_state == GameState.NAME_ENTRY:
            self._render_name_entry()
        elif self.current_state == GameState.GAME_OVER:
            self._render_game_over()
    
    def _render_main_menu(self):
        """Render the main menu with maximum legibility."""
        # Clear previous option rectangles
        self.menu_option_rects = []
        
        # Get current screen dimensions
        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        
        # Draw background image if available, otherwise black background
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill((0, 0, 0))  # Pure black background as fallback
        
        # Helper function for outlined text
        def draw_outlined_text(text, font, color, outline_color, x, y):
            # Draw black outline (8 directions)
            outline_surface = font.render(text, False, outline_color)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        outline_rect = outline_surface.get_rect(center=(x + dx, y + dy))
                        self.screen.blit(outline_surface, outline_rect)
            
            # Draw main text
            text_surface = font.render(text, False, color)
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
            return text_rect
        
        # Title with black outline
        title_text = "TREASURE GOBLIN"
        title_rect = draw_outlined_text(title_text, self.title_font, (255, 255, 255), (0, 0, 0), 
                                       center_x, screen_height // 4)
        
        # Subtitle with black outline
        subtitle_rect = draw_outlined_text("DUNGEON CRAWLER", self.text_font, (255, 255, 255), (0, 0, 0),
                                          center_x, screen_height // 4 + 60)
        
        # Menu options with black outline
        menu_options = ["NEW GAME", "QUIT"]
        start_y = screen_height // 2
        
        for i, option in enumerate(menu_options):
            # Use goblin green for selected option
            text_color = self.selected_color if i == self.menu_selection else self.text_color
            option_rect = draw_outlined_text(option, self.header_font, text_color, (0, 0, 0),
                                           center_x, start_y + i * 60)
            
            # Store clickable area
            padded_rect = option_rect.inflate(40, 20)
            self.menu_option_rects.append((padded_rect, i))
    
    def _render_class_selection(self):
        """Render the class selection screen with clean style."""
        # Clear previous option rectangles
        self.class_option_rects = []
        
        # Get current screen dimensions
        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        
        # Draw background image if available, otherwise black background
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill((0, 0, 0))  # Pure black background as fallback
        
        # Helper function for outlined text (same as main menu)
        def draw_outlined_text(text, font, color, outline_color, x, y):
            # Draw black outline (8 directions)
            outline_surface = font.render(text, False, outline_color)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        outline_rect = outline_surface.get_rect(center=(x + dx, y + dy))
                        self.screen.blit(outline_surface, outline_rect)
            
            # Draw main text
            text_surface = font.render(text, False, color)
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
            return text_rect
        
        # Title - clean outlined text like main menu
        draw_outlined_text("SELECT YOUR CLASS", self.title_font, (255, 255, 255), (0, 0, 0),
                          center_x, screen_height // 6)
        
        # Class options - clean centered list
        classes = list(CharacterClass)
        start_y = screen_height // 3
        
        for i, char_class in enumerate(classes):
            y_pos = start_y + i * 60
            
            # Clean outlined class names - goblin green for selected
            text_color = self.selected_color if i == self.class_selection else self.text_color
            class_rect = draw_outlined_text(char_class.value.upper(), self.header_font, 
                                          text_color, (0, 0, 0), center_x, y_pos)
            
            # Store clickable area
            padded_rect = class_rect.inflate(60, 30)
            self.class_option_rects.append((padded_rect, i))
        
        # Selected class info at bottom - minimal and clean
        selected_class = classes[self.class_selection]
        class_data = CharacterClassData.CLASS_DEFINITIONS[selected_class]
        
        # Simple description
        info_y = screen_height - 120
        desc_text = class_data['description']
        draw_outlined_text(desc_text.upper(), self.text_font, (255, 255, 255), (0, 0, 0),
                          center_x, info_y)
    
    def _render_name_entry(self):
        """Render the name entry screen."""
        # Get current screen dimensions
        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        
        # Draw background image if available, otherwise black background
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill((0, 0, 0))  # Pure black background as fallback
        
        # Helper function for outlined text (same as other menus)
        def draw_outlined_text(text, font, color, outline_color, x, y):
            # Draw black outline (8 directions)
            outline_surface = font.render(text, False, outline_color)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        outline_rect = outline_surface.get_rect(center=(x + dx, y + dy))
                        self.screen.blit(outline_surface, outline_rect)
            
            # Draw main text
            text_surface = font.render(text, False, color)
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
            return text_rect
        
        # Title with clean outlined text
        draw_outlined_text("ENTER YOUR NAME", self.title_font, (255, 255, 255), (0, 0, 0),
                          center_x, screen_height // 4)
        
        # Selected class info with clean outlined text
        classes = list(CharacterClass)
        selected_class = classes[self.class_selection]
        class_text = f"CLASS: {selected_class.value.upper()}"
        draw_outlined_text(class_text, self.header_font, (255, 255, 255), (0, 0, 0),
                          center_x, screen_height // 4 + 60)
        
        # Name input field - positioned relative to screen
        input_y = screen_height // 2 - 25
        input_width = 400
        input_height = 50
        input_x = (screen_width - input_width) // 2
        
        # Input field background - white on black theme
        pygame.draw.rect(self.screen, (0, 0, 0), (input_x, input_y, input_width, input_height))  # Black background
        pygame.draw.rect(self.screen, (255, 255, 255), (input_x, input_y, input_width, input_height), 2)  # White border
        
        # Name text
        display_text = self.name_entry_text
        if not display_text:
            display_text = "Enter your name..."
            text_color = (128, 128, 128)  # Grey placeholder
        else:
            text_color = (255, 255, 255)  # White text
        
        # Render text
        text_surface = self.text_font.render(display_text, True, text_color)
        text_rect = text_surface.get_rect(center=(input_x + input_width // 2, input_y + input_height // 2))
        self.screen.blit(text_surface, text_rect)
        
        # Simple cursor indicator (just show a blinking underscore at the end)
        if display_text and display_text != "Enter your name...":
            import time
            if int(time.time() * 2) % 2:  # Blink every 0.5 seconds
                cursor_x = text_rect.right + 5
                cursor_y = text_rect.centery
                pygame.draw.line(self.screen, (255, 0, 0), (cursor_x, cursor_y - 10), (cursor_x, cursor_y + 10), 2)
        
        # Instructions removed for cleaner interface
    
    def _render_game_over(self):
        """Render the game over screen."""
        # Clear previous option rectangles
        self.game_over_option_rects = []
        
        # Get current screen dimensions
        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        
        # Draw background image if available, otherwise black background
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill((0, 0, 0))  # Pure black background as fallback
        
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Helper function for outlined text (same as other menus)
        def draw_outlined_text(text, font, color, outline_color, x, y):
            # Draw black outline (8 directions)
            outline_surface = font.render(text, False, outline_color)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        outline_rect = outline_surface.get_rect(center=(x + dx, y + dy))
                        self.screen.blit(outline_surface, outline_rect)
            
            # Draw main text
            text_surface = font.render(text, False, color)
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
            return text_rect
        
        # Game Over title with clean outlined text
        draw_outlined_text("GAME OVER", self.title_font, (255, 255, 255), (0, 0, 0),
                          center_x, screen_height // 4)
        
        # Score display with clean outlined text
        if self.game and hasattr(self.game, 'final_score'):
            score_text = f"FINAL SCORE: {self.game.final_score}"
            draw_outlined_text(score_text, self.header_font, (255, 255, 255), (0, 0, 0),
                              center_x, screen_height // 4 + 60)
        
        # High scores with clean outlined text
        if self.game and hasattr(self.game, 'high_scores') and self.game.high_scores:
            draw_outlined_text("HIGH SCORES", self.text_font, (255, 255, 255), (0, 0, 0),
                              center_x, screen_height // 4 + 120)
            
            # Show top 5 high scores
            for i, score_entry in enumerate(self.game.high_scores[:5]):
                y_pos = 280 + i * 25
                name = score_entry.get('name', 'Unknown')
                score_text = f"{i+1}. {name} - {score_entry['score']} - Level {score_entry['level']} - {score_entry['class']}"
                color = (255, 255, 0) if i == 0 else (200, 200, 200)
                score_entry_surface = self.small_font.render(score_text, True, color)
                score_entry_rect = score_entry_surface.get_rect(center=(512, y_pos))
                self.screen.blit(score_entry_surface, score_entry_rect)
        
        # Options
        options = ["RESTART", "QUIT TO MENU"]
        start_y = 450
        
        for i, option in enumerate(options):
            color = self.selected_color if i == self.game_over_selection else self.text_color
            option_surface = self.header_font.render(option, True, color)
            option_rect = option_surface.get_rect(center=(512, start_y + i * 60))
            self.screen.blit(option_surface, option_rect)
            
            # Add padding to the clickable area
            padded_rect = option_rect.inflate(40, 20)
            self.game_over_option_rects.append((padded_rect, i))
        
        # Controls
        controls_surface = self.small_font.render(
            "W/S: NAVIGATE * CLICK OR PRESS ENTER TO SELECT * ESCAPE: QUIT",
            True,
            self.text_color
        )
        controls_rect = controls_surface.get_rect(center=(512, 600))
        self.screen.blit(controls_surface, controls_rect)
    
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