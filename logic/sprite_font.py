"""
Sprite Font System for Mythica
Handles rendering text using sprite-based fonts.
"""

import pygame
from typing import Dict, Tuple, Optional
from .sprite_manager import sprite_manager, SpriteType

class SpriteFont:
    """
    A class to handle sprite-based font rendering.
    Uses the Classic Roguelike tileset for character sprites.
    """
    
    def __init__(self, scale: float = 1.0):
        """
        Initialize the sprite font.
        
        Args:
            scale: Scale factor for the font sprites (default 1.0)
        """
        self.scale = scale
        self.char_cache: Dict[str, pygame.Surface] = {}
        self.char_spacing = 4  # Pixels between characters
        self.line_spacing = 8  # Pixels between lines
        
        # Load each character sprite individually
        self.char_sprites = {}
        self.char_width = 24  # Width of each character in pixels
        self.char_height = 24  # Height of each character in pixels
        self._load_character_sprites()
        
        # Initialize character mappings
        self._init_char_mappings()
    
    def _load_character_sprites(self):
        """Load individual character sprites from the Classic Roguelike sliced sprites."""
        base_path = sprite_manager.assets_path / "Classic Roguelike" / "classic_roguelike_sliced"
        
        # Load letters A-Z (140-165)
        for i, char in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            sprite_num = 140 + i
            sprite_path = base_path / f"classic_roguelike_{sprite_num}.png"
            try:
                sprite = pygame.image.load(str(sprite_path)).convert_alpha()
                self.char_sprites[char] = sprite
            except pygame.error:
                print(f"Failed to load sprite for character {char}")
        
        # Load numbers 0-9 (168-177)
        number_sprites = {
            '1': 168, '2': 169, '3': 170, '4': 171, '5': 172,
            '6': 173, '7': 174, '8': 175, '9': 176, '0': 177
        }
        for num, sprite_num in number_sprites.items():
            sprite_path = base_path / f"classic_roguelike_{sprite_num}.png"
            try:
                sprite = pygame.image.load(str(sprite_path)).convert_alpha()
                self.char_sprites[num] = sprite
            except pygame.error:
                print(f"Failed to load sprite for number {num}")
        
        # Load special characters
        special_chars = {
            '!': 112,  # Exclamation
            '@': 113,  # At symbol
            '#': 114,  # Hash
            '$': 115,  # Dollar
            '%': 116,  # Percentage
            '^': 117,  # Caret
            '&': 118,  # Ampersand
            '*': 119,  # Asterisk
            '(': 120,  # Open bracket
            ')': 121,  # Close bracket
            '-': 122,  # Minus/dash
            '=': 123,  # Equals
            '+': 124,  # Plus
            '.': 125,  # Full stop/period
            ',': 126,  # Comma
            ':': 127,  # Colon
            ';': 128,  # Semi-colon
            "'": 129,  # Quote
            '<': 130,  # Open sharp bracket
            '>': 131,  # Close sharp bracket
            '?': 132,  # Question mark
            '\\': 133, # Backslash
            '/': 134,  # Forward slash
            '|': 135,  # Pipe
            '_': 193,  # Underscore
        }
        for char, sprite_num in special_chars.items():
            sprite_path = base_path / f"classic_roguelike_{sprite_num}.png"
            try:
                sprite = pygame.image.load(str(sprite_path)).convert_alpha()
                self.char_sprites[char] = sprite
            except pygame.error:
                print(f"Failed to load sprite for character {char}")
        
        # Create a blank sprite for space
        space = pygame.Surface((self.char_width, self.char_height), pygame.SRCALPHA)
        self.char_sprites[' '] = space
    
    def _init_char_mappings(self):
        """Initialize the mapping of available characters."""
        # We don't need position mappings anymore since we load sprites directly
        self.char_positions = {char: None for char in self.char_sprites.keys()}
    
    def _get_char_sprite(self, char: str) -> Optional[pygame.Surface]:
        """
        Get the sprite for a single character.
        
        Args:
            char: The character to get the sprite for
            
        Returns:
            pygame.Surface or None if character not found
        """
        # Return cached sprite if available
        if char in self.char_cache:
            return self.char_cache[char]
        
        # Get the base sprite
        sprite = self.char_sprites.get(char.upper())
        if sprite is None:
            return None
        
        # Scale if needed
        if self.scale != 1.0:
            sprite = pygame.transform.scale(
                sprite,
                (int(self.char_width * self.scale), int(self.char_height * self.scale))
            )
        
        # Cache and return
        self.char_cache[char] = sprite
        return sprite
    
    def render_text(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> pygame.Surface:
        """
        Render text using sprite font.
        
        Args:
            text: The text to render
            color: RGB color tuple for tinting the sprites
            
        Returns:
            pygame.Surface containing the rendered text
        """
        if not text:
            return pygame.Surface((0, 0), pygame.SRCALPHA)
        
        # Calculate dimensions
        char_width = int(self.char_width * self.scale)
        char_height = int(self.char_height * self.scale)
        spacing = int(self.char_spacing * self.scale)
        
        # Create surface for the text
        width = (char_width + spacing) * len(text) - spacing
        surface = pygame.Surface((width, char_height), pygame.SRCALPHA)
        
        # Render each character
        x = 0
        for char in text:
            sprite = self._get_char_sprite(char)
            if sprite:
                # Apply color tint
                if color != (255, 255, 255):
                    tinted = sprite.copy()
                    tinted.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
                    surface.blit(tinted, (x, 0))
                else:
                    surface.blit(sprite, (x, 0))
                x += char_width + spacing
            elif char == ' ':
                x += char_width + spacing
        
        return surface
    
    def render_text_centered(self, text: str, center_pos: Tuple[int, int], 
                           color: Tuple[int, int, int] = (255, 255, 255)) -> pygame.Rect:
        """
        Render text centered at the specified position.
        
        Args:
            text: The text to render
            center_pos: (x, y) position to center the text at
            color: RGB color tuple for tinting the sprites
            
        Returns:
            pygame.Rect of the rendered text area
        """
        text_surface = self.render_text(text, color)
        text_rect = text_surface.get_rect(center=center_pos)
        pygame.display.get_surface().blit(text_surface, text_rect)
        return text_rect
    
    def clear_cache(self):
        """Clear the character sprite cache."""
        self.char_cache.clear()
