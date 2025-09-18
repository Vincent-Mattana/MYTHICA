"""
Sprite Font System for Mythica
Handles rendering text using sprite-based fonts.
"""

import pygame
from typing import Dict, Tuple, Optional
from pathlib import Path

class SpriteFont:
    """
    A class to handle sprite-based font rendering.
    Uses the Classic Roguelike tileset for character sprites.
    """
    
    def __init__(self, scale: float = 1.0, assets_path: Optional[Path] = None):
        """
        Initialize the sprite font.
        
        Args:
            scale: Scale factor for the font sprites (default 1.0)
            assets_path: Path to assets directory (defaults to project assets)
        """
        self.scale = scale
        self.char_cache: Dict[str, pygame.Surface] = {}
        self.char_spacing = 4  # Pixels between characters
        self.line_spacing = 8  # Pixels between lines
        
        # Set assets path
        if assets_path is None:
            self.assets_path = Path(__file__).parent.parent / "assets"
        else:
            self.assets_path = assets_path
        
        # Load each character sprite individually
        self.char_sprites = {}
        self.char_width = 24  # Width of each character in pixels
        self.char_height = 24  # Height of each character in pixels
        self._load_character_sprites()
        
        # Initialize character mappings
        self._init_char_mappings()
    
    def _load_character_sprites(self):
        """Load individual character sprites from the Classic Roguelike sliced sprites."""
        # Skip sliced sprite loading - use fallback font directly
        self._create_fallback_font()
        return
    
    def _create_fallback_font(self):
        """Create a simple fallback font using pygame's default font."""
        try:
            # Try to use a system font
            fallback_font = pygame.font.Font(None, self.char_height)
        except:
            # If that fails, use the default font
            fallback_font = pygame.font.Font(pygame.font.get_default_font(), self.char_height)
        
        # Create sprites for all characters using the fallback font
        all_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()+-=.,:;\'<>?/\\|_ '
        
        for char in all_chars:
            try:
                # Render the character
                char_surface = fallback_font.render(char, True, (255, 255, 255))
                
                # Scale to match our character size
                scaled_char = pygame.transform.scale(char_surface, (self.char_width, self.char_height))
                self.char_sprites[char.upper()] = scaled_char
            except:
                # If rendering fails, create a blank sprite
                blank = pygame.Surface((self.char_width, self.char_height), pygame.SRCALPHA)
                self.char_sprites[char.upper()] = blank
        
        # Created fallback font silently
    
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
