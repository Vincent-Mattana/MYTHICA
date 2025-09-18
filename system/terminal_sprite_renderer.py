#!/usr/bin/env python3
"""
Terminal Sprite Renderer for Treasure Goblin
Converts pygame sprites to terminal-displayable format using Unicode characters and ANSI colours.
"""

import pygame
from PIL import Image
import numpy as np
from typing import Dict, Tuple, Optional, List
import os
import sys
from pathlib import Path

# Add system path for imports
sys.path.append(str(Path(__file__).parent))
from sprite_system import SpriteSystem, GameSpriteManager


class TerminalSpriteRenderer:
    """Renders pygame sprites as terminal text using Unicode characters and ANSI colours."""
    
    # Unicode block characters for different pixel densities
    BLOCK_CHARS = [
        ' ',      # 0% - empty
        '░',      # 25% - light shade
        '▒',      # 50% - medium shade  
        '▓',      # 75% - dark shade
        '█',      # 100% - full block
    ]
    
    # Half-block characters for better vertical resolution
    HALF_BLOCKS = {
        (0, 0): ' ',   # Both empty
        (0, 1): '▄',   # Top empty, bottom filled
        (1, 0): '▀',   # Top filled, bottom empty  
        (1, 1): '█',   # Both filled
    }
    
    def __init__(self, use_colour: bool = True, use_half_blocks: bool = True):
        """
        Args:
            use_colour: Enable ANSI colour codes
            use_half_blocks: Use half-block characters for better resolution
        """
        self.use_colour = use_colour
        self.use_half_blocks = use_half_blocks
        
        # Check terminal colour support
        if use_colour:
            self.colour_support = self._check_colour_support()
        else:
            self.colour_support = False
    
    def _check_colour_support(self) -> bool:
        """Check if terminal supports colour."""
        # Check common environment variables for colour support
        term = os.environ.get('TERM', '')
        colorterm = os.environ.get('COLORTERM', '')
        
        return (
            'color' in term.lower() or 
            'truecolor' in colorterm.lower() or 
            '256' in term or
            term in ['xterm-256color', 'screen-256color']
        )
    
    def pygame_surface_to_pil(self, surface: pygame.Surface) -> Image.Image:
        """Convert pygame surface to PIL Image."""
        # Convert surface to string format that PIL can read
        size = surface.get_size()
        raw = pygame.image.tostring(surface, 'RGB')
        return Image.frombytes('RGB', size, raw)
    
    def pil_to_terminal(self, image: Image.Image, width: Optional[int] = None, 
                       height: Optional[int] = None) -> str:
        """Convert PIL image to terminal string representation."""
        # Resize if dimensions specified
        if width or height:
            # Calculate aspect ratio
            orig_width, orig_height = image.size
            aspect_ratio = orig_width / orig_height
            
            if width and not height:
                height = int(width / aspect_ratio)
                if self.use_half_blocks:
                    height = height // 2  # Account for half-block vertical compression
            elif height and not width:
                width = int(height * aspect_ratio)
                if self.use_half_blocks:
                    height = height * 2  # Account for half-block expansion
            
            image = image.resize((width, height), Image.Resampling.NEAREST)
        
        if self.use_half_blocks:
            return self._pil_to_half_blocks(image)
        else:
            return self._pil_to_blocks(image)
    
    def _pil_to_blocks(self, image: Image.Image) -> str:
        """Convert PIL image to block characters."""
        # Convert to grayscale for intensity mapping
        gray_image = image.convert('L')
        pixels = np.array(gray_image)
        
        # Convert RGB image to colour codes if colour is enabled
        colour_pixels = None
        if self.colour_support:
            colour_pixels = np.array(image.convert('RGB'))
        
        lines = []
        height, width = pixels.shape
        
        for y in range(height):
            line = ""
            for x in range(width):
                # Map intensity to block character
                intensity = pixels[y, x]
                char_index = min(int(intensity / 255 * (len(self.BLOCK_CHARS) - 1)), 
                               len(self.BLOCK_CHARS) - 1)
                char = self.BLOCK_CHARS[char_index]
                
                # Add colour if supported
                if self.colour_support and colour_pixels is not None and char != ' ':
                    r, g, b = colour_pixels[y, x]
                    char = f"\033[38;2;{r};{g};{b}m{char}\033[0m"
                
                line += char
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _pil_to_half_blocks(self, image: Image.Image) -> str:
        """Convert PIL image to half-block characters for better resolution."""
        # Convert to grayscale
        gray_image = image.convert('L')
        pixels = np.array(gray_image)
        
        # Get colour information if colour is enabled
        colour_pixels = None
        if self.colour_support:
            colour_pixels = np.array(image.convert('RGB'))
        
        lines = []
        height, width = pixels.shape
        
        # Process in pairs of rows (for half-blocks)
        for y in range(0, height, 2):
            line = ""
            for x in range(width):
                # Get top and bottom pixel intensities
                top_intensity = pixels[y, x] if y < height else 0
                bottom_intensity = pixels[y + 1, x] if y + 1 < height else 0
                
                # Threshold for filled/empty (can be adjusted)
                threshold = 128
                top_filled = top_intensity > threshold
                bottom_filled = bottom_intensity > threshold
                
                # Get appropriate half-block character
                char = self.HALF_BLOCKS[(int(top_filled), int(bottom_filled))]
                
                # Add colour if supported and character isn't empty
                if self.colour_support and colour_pixels is not None and char != ' ':
                    # Use the brighter pixel's colour
                    if top_intensity > bottom_intensity:
                        r, g, b = colour_pixels[y, x]
                    else:
                        y_bottom = min(y + 1, height - 1)
                        r, g, b = colour_pixels[y_bottom, x]
                    
                    char = f"\033[38;2;{r};{g};{b}m{char}\033[0m"
                
                line += char
            lines.append(line)
        
        return '\n'.join(lines)
    
    def render_sprite_to_terminal(self, sprite: pygame.Surface, 
                                 width: Optional[int] = None, 
                                 height: Optional[int] = None) -> str:
        """Convert a pygame sprite to terminal representation."""
        # Convert pygame surface to PIL
        pil_image = self.pygame_surface_to_pil(sprite)
        
        # Convert PIL to terminal
        return self.pil_to_terminal(pil_image, width, height)
    
    def print_sprite(self, sprite: pygame.Surface, 
                    width: Optional[int] = None, 
                    height: Optional[int] = None):
        """Print a sprite directly to terminal."""
        terminal_repr = self.render_sprite_to_terminal(sprite, width, height)
        print(terminal_repr)
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')


class TerminalGameRenderer:
    """High-level terminal renderer for game scenes."""
    
    def __init__(self, sprite_manager: GameSpriteManager, 
                 terminal_renderer: TerminalSpriteRenderer):
        self.sprite_manager = sprite_manager
        self.terminal_renderer = terminal_renderer
    
    def render_scene_to_terminal(self, scene_data: List[List[str]], 
                               tile_width: int = 2, tile_height: int = 1) -> str:
        """Render a game scene to terminal."""
        if not scene_data or not scene_data[0]:
            return ""
        
        scene_height = len(scene_data)
        scene_width = len(scene_data[0])
        
        # Create a combined image for the entire scene
        sprite_size = self.sprite_manager.sprite_system.tile_size
        full_width = scene_width * sprite_size[0]
        full_height = scene_height * sprite_size[1]
        
        # Create a surface to render the scene
        scene_surface = pygame.Surface((full_width, full_height), pygame.SRCALPHA)
        scene_surface.fill((0, 0, 0, 0))  # Transparent background
        
        # Render each sprite to the scene surface
        for y, row in enumerate(scene_data):
            for x, sprite_name in enumerate(row):
                if sprite_name and sprite_name != '':
                    sprite = self.sprite_manager.sprite_system.get_sprite(sprite_name)
                    if sprite:
                        pos_x = x * sprite_size[0]
                        pos_y = y * sprite_size[1]
                        scene_surface.blit(sprite, (pos_x, pos_y))
        
        # Convert to terminal
        terminal_width = scene_width * tile_width
        terminal_height = scene_height * tile_height
        
        return self.terminal_renderer.render_sprite_to_terminal(
            scene_surface, terminal_width, terminal_height
        )
    
    def print_scene(self, scene_data: List[List[str]], 
                   tile_width: int = 2, tile_height: int = 1):
        """Print a game scene to terminal."""
        terminal_repr = self.render_scene_to_terminal(scene_data, tile_width, tile_height)
        print(terminal_repr)


def demo_terminal_sprites():
    """Demonstration of terminal sprite rendering."""
    print("🎮 Treasure Goblin Terminal Sprite Demo 🎮\n")
    
    # Initialize sprite system
    assets_path = Path(__file__).parent.parent / "assets"
    sprite_manager = GameSpriteManager()
    
    print("Loading sprites...")
    if not sprite_manager.load_game_assets(assets_path):
        print("❌ Failed to load some assets, but continuing with demo...")
    
    # Initialize terminal renderer
    terminal_renderer = TerminalSpriteRenderer(use_colour=True, use_half_blocks=True)
    game_renderer = TerminalGameRenderer(sprite_manager, terminal_renderer)
    
    print(f"✅ Loaded {len(sprite_manager.sprite_system.list_sprites())} sprites")
    print(f"🎨 Colour support: {'Yes' if terminal_renderer.colour_support else 'No'}")
    print(f"📦 Half-blocks: {'Yes' if terminal_renderer.use_half_blocks else 'No'}\n")
    
    # Get available sprites
    available_sprites = sprite_manager.sprite_system.list_sprites()
    
    if not available_sprites:
        print("❌ No sprites loaded. Check your assets directory.")
        return
    
    # Demo individual sprites
    print("🔍 Demo: Individual Sprites")
    print("-" * 40)
    
    # Show first few sprites
    for i, sprite_name in enumerate(available_sprites[:5]):
        sprite = sprite_manager.sprite_system.get_sprite(sprite_name)
        if sprite:
            print(f"\n📝 Sprite: {sprite_name}")
            terminal_renderer.print_sprite(sprite, width=8)
    
    # Demo scene rendering
    print("\n\n🗺️  Demo: Scene Rendering")
    print("-" * 40)
    
    # Create a small demo scene
    demo_scene = []
    if len(available_sprites) >= 4:
        demo_scene = [
            [available_sprites[0], available_sprites[1], available_sprites[0]],
            [available_sprites[2], available_sprites[3], available_sprites[2]],
            [available_sprites[0], available_sprites[1], available_sprites[0]]
        ]
    else:
        # Fallback with repeated sprites
        sprite = available_sprites[0] if available_sprites else ''
        demo_scene = [
            [sprite, sprite, sprite],
            [sprite, sprite, sprite],
            [sprite, sprite, sprite]
        ]
    
    print("\n📝 Demo Scene:")
    game_renderer.print_scene(demo_scene, tile_width=4, tile_height=2)
    
    print("\n✨ Demo complete!")


if __name__ == "__main__":
    demo_terminal_sprites()
