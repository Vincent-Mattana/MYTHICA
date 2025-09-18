#!/usr/bin/env python3
"""
Goblin Bitmap Font System for Treasure Goblin
Creates custom goblin-themed fonts using gob1.webp and gob2.webp images.
"""

import pygame
import os
from typing import Dict, Tuple, Optional

class GoblinFont:
    """Custom bitmap font system using goblin character images."""
    
    def __init__(self):
        self.char_surfaces: Dict[str, pygame.Surface] = {}
        self.char_width = 0
        self.char_height = 0
        self.spacing = 2  # Space between characters
        self.line_height = 0
        self.loaded = False
        
        # Load the goblin character images
        self._load_goblin_chars()
    
    def _load_goblin_chars(self):
        """Load and process goblin character images."""
        try:
            # Load gob1.webp and gob2.webp
            gob1_path = "gob1.webp"
            gob2_path = "gob2.webp"
            
            if not os.path.exists(gob1_path) or not os.path.exists(gob2_path):
                print("Goblin font images not found, falling back to system fonts")
                return
            
            # Load the images
            gob1_image = pygame.image.load(gob1_path).convert_alpha()
            gob2_image = pygame.image.load(gob2_path).convert_alpha()
            
            # Get dimensions (assume both images are same size)
            self.char_width = gob1_image.get_width()
            self.char_height = gob1_image.get_height()
            self.line_height = self.char_height + 4  # Add some line spacing
            
            print(f"Loaded goblin font images: {self.char_width}x{self.char_height}")
            
            # Create character mapping - we'll use these two images to represent different letters
            # Map letters to the appropriate goblin image
            self._create_character_mapping(gob1_image, gob2_image)
            
            self.loaded = True
            print("Goblin font system loaded successfully!")
            
        except Exception as e:
            print(f"Error loading goblin font: {e}")
            self.loaded = False
    
    def _create_character_mapping(self, gob1: pygame.Surface, gob2: pygame.Surface):
        """Create mapping of characters to goblin images with variations."""
        
        # Create tinted versions for variety
        def tint_surface(surface: pygame.Surface, tint: Tuple[int, int, int]) -> pygame.Surface:
            """Tint a surface with a given color."""
            tinted = surface.copy()
            tint_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            tint_overlay.fill((*tint, 180))  # Semi-transparent tint
            try:
                tinted.blit(tint_overlay, (0, 0), special_flags=pygame.BLEND_MULTIPLY)
            except AttributeError:
                # Fallback if BLEND_MULTIPLY not available
                tinted.blit(tint_overlay, (0, 0))
            return tinted
        
        # Create different colored variants
        gob1_bright = tint_surface(gob1, (100, 255, 100))  # Bright green
        gob1_dark = tint_surface(gob1, (50, 150, 50))      # Dark green
        gob2_bright = tint_surface(gob2, (100, 255, 100))  # Bright green
        gob2_dark = tint_surface(gob2, (50, 150, 50))      # Dark green
        
        # Map characters to goblin variants for visual variety
        char_mapping = {
            # Letters (alternating between gob1 and gob2 variants)
            'A': gob1_bright, 'B': gob2_bright, 'C': gob1_dark, 'D': gob2_dark,
            'E': gob1_bright, 'F': gob2_bright, 'G': gob1_dark, 'H': gob2_dark,
            'I': gob1_bright, 'J': gob2_bright, 'K': gob1_dark, 'L': gob2_dark,
            'M': gob1_bright, 'N': gob2_bright, 'O': gob1_dark, 'P': gob2_dark,
            'Q': gob1_bright, 'R': gob2_bright, 'S': gob1_dark, 'T': gob2_dark,
            'U': gob1_bright, 'V': gob2_bright, 'W': gob1_dark, 'X': gob2_dark,
            'Y': gob1_bright, 'Z': gob2_bright,
            
            # Numbers
            '0': gob1_dark, '1': gob2_dark, '2': gob1_bright, '3': gob2_bright,
            '4': gob1_dark, '5': gob2_dark, '6': gob1_bright, '7': gob2_bright,
            '8': gob1_dark, '9': gob2_dark,
            
            # Special characters
            ' ': None,  # Space is handled specially
            ':': gob1_bright, '!': gob2_bright, '?': gob1_dark, '.': gob2_dark,
            ',': gob1_bright, '-': gob2_bright, '+': gob1_dark, '=': gob2_dark,
            '(': gob1_bright, ')': gob2_bright, '[': gob1_dark, ']': gob2_dark,
            '*': gob1_bright, '/': gob2_bright, '\\': gob1_dark, '%': gob2_dark,
        }
        
        self.char_surfaces = char_mapping
    
    def get_text_size(self, text: str) -> Tuple[int, int]:
        """Get the size of text when rendered with this font."""
        if not self.loaded or not text:
            return (0, 0)
        
        lines = text.split('\n')
        max_width = 0
        
        for line in lines:
            line_width = len(line) * (self.char_width + self.spacing)
            if line_width > 0:
                line_width -= self.spacing  # Remove trailing spacing
            max_width = max(max_width, line_width)
        
        height = len(lines) * self.line_height
        return (max_width, height)
    
    def render(self, text: str, color: Tuple[int, int, int] = (100, 255, 100)) -> pygame.Surface:
        """Render text using goblin characters."""
        if not self.loaded or not text:
            # Fallback to pygame font if goblin font failed to load
            fallback_font = pygame.font.SysFont("monospace", 24, bold=True)
            return fallback_font.render(text, True, color)
        
        lines = text.split('\n')
        text_width, text_height = self.get_text_size(text)
        
        if text_width == 0 or text_height == 0:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        
        # Create surface for the text
        text_surface = pygame.Surface((text_width, text_height), pygame.SRCALPHA)
        text_surface.fill((0, 0, 0, 0))  # Transparent background
        
        current_y = 0
        for line in lines:
            current_x = 0
            for char in line.upper():  # Convert to uppercase
                if char == ' ':
                    current_x += self.char_width + self.spacing
                elif char in self.char_surfaces and self.char_surfaces[char] is not None:
                    char_surface = self.char_surfaces[char]
                    text_surface.blit(char_surface, (current_x, current_y))
                    current_x += self.char_width + self.spacing
                else:
                    # Unknown character - draw a small goblin placeholder
                    if 'A' in self.char_surfaces:
                        placeholder = self.char_surfaces['A'].copy()
                        placeholder.set_alpha(128)  # Semi-transparent
                        text_surface.blit(placeholder, (current_x, current_y))
                    current_x += self.char_width + self.spacing
            
            current_y += self.line_height
        
        return text_surface

class GoblinFontManager:
    """Manager for different sizes of goblin fonts."""
    
    def __init__(self):
        self.fonts: Dict[str, GoblinFont] = {}
        self.scale_factors = {
            'title': 3.0,
            'header': 2.0,
            'text': 1.5,
            'small': 1.0
        }
        
        # Create base font
        self.base_font = GoblinFont()
        
        # Pre-create scaled versions if base font loaded successfully
        if self.base_font.loaded:
            for size_name in self.scale_factors:
                self.fonts[size_name] = self.base_font
    
    def render(self, text: str, size: str = 'text', color: Tuple[int, int, int] = (100, 255, 100)) -> pygame.Surface:
        """Render text with specified size."""
        if size not in self.fonts or not self.base_font.loaded:
            # Fallback to pygame fonts
            size_map = {'title': 72, 'header': 48, 'text': 36, 'small': 24}
            font_size = size_map.get(size, 36)
            fallback_font = pygame.font.SysFont("monospace", font_size, bold=True)
            return fallback_font.render(text, True, color)
        
        # Render with goblin font
        base_surface = self.base_font.render(text, color)
        
        # Scale the surface
        scale = self.scale_factors[size]
        if scale != 1.0:
            new_width = int(base_surface.get_width() * scale)
            new_height = int(base_surface.get_height() * scale)
            if new_width > 0 and new_height > 0:
                return pygame.transform.scale(base_surface, (new_width, new_height))
        
        return base_surface
    
    def is_loaded(self) -> bool:
        """Check if goblin font system is loaded."""
        return self.base_font.loaded
