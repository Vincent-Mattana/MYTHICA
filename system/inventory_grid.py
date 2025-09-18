"""
Inventory Grid Component
A standalone inventory grid that can be used in various UI contexts.
Integrates with the sprite system for visual rendering.
"""

import pygame
from typing import List, Optional, Tuple, Callable
from pathlib import Path
from .character_system import Item, ItemType
from .sprite_font import SpriteFont
from .sprite_system import GameSpriteManager


class InventoryGrid:
    """
    A visual inventory grid component that can be embedded in other UI elements.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 cols: int = 6, rows: int = 6, assets_path: Optional[Path] = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.cols = cols
        self.rows = rows
        
        # Calculate slot dimensions
        self.slot_width = width // cols
        self.slot_height = height // rows
        
        # Initialize sprite manager
        self.sprite_manager = GameSpriteManager()
        if assets_path is None:
            assets_path = Path(__file__).parent.parent / "assets"
        self.sprite_manager.load_game_assets(assets_path)
        
        # UI state
        self.selected_slot: Optional[int] = None
        self.hovered_slot: Optional[int] = None
        self.tooltip_item: Optional[Item] = None
        self.tooltip_position: Tuple[int, int] = (0, 0)
        
        # Colors
        self.BACKGROUND_COLOR = (40, 40, 50)
        self.SLOT_COLOR = (80, 80, 90)
        self.SELECTED_COLOR = (255, 255, 100)
        self.HOVER_COLOR = (100, 255, 100)
        self.BORDER_COLOR = (200, 200, 200)
        self.TEXT_COLOR = (255, 255, 255)
        
        # Fonts
        self.small_font = SpriteFont(scale=0.5)
        self.tiny_font = SpriteFont(scale=0.4)
        
        # Callbacks
        self.on_item_click: Optional[Callable[[Item, int], None]] = None
        self.on_slot_hover: Optional[Callable[[Item, int], None]] = None
    
    def set_inventory(self, items: List[Item]):
        """Set the inventory items to display."""
        self.items = items
    
    def handle_mouse_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle mouse click events.
        
        Args:
            pos: Mouse position (x, y)
            
        Returns:
            Action message or None
        """
        slot_index = self._get_slot_at_position(pos)
        if slot_index is not None:
            if slot_index < len(self.items):
                item = self.items[slot_index]
                self.selected_slot = slot_index
                
                if self.on_item_click:
                    self.on_item_click(item, slot_index)
                
                return f"Selected {item.name}"
            else:
                self.selected_slot = None
                return "Empty slot"
        
        return None
    
    def handle_mouse_hover(self, pos: Tuple[int, int]):
        """
        Handle mouse hover events.
        
        Args:
            pos: Mouse position (x, y)
        """
        slot_index = self._get_slot_at_position(pos)
        if slot_index is not None:
            self.hovered_slot = slot_index
            if slot_index < len(self.items):
                self.tooltip_item = self.items[slot_index]
                self.tooltip_position = pos
                
                if self.on_slot_hover:
                    self.on_slot_hover(self.items[slot_index], slot_index)
            else:
                self.tooltip_item = None
        else:
            self.hovered_slot = None
            self.tooltip_item = None
    
    def render(self, surface: pygame.Surface):
        """
        Render the inventory grid.
        
        Args:
            surface: Pygame surface to render to
        """
        # Draw grid background
        grid_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.BACKGROUND_COLOR, grid_rect)
        pygame.draw.rect(surface, self.BORDER_COLOR, grid_rect, 2)
        
        # Draw slots
        for row in range(self.rows):
            for col in range(self.cols):
                slot_index = row * self.cols + col
                slot_x = self.x + col * self.slot_width
                slot_y = self.y + row * self.slot_height
                
                self._draw_slot(surface, slot_x, slot_y, slot_index)
        
        # Draw tooltip if hovering over item
        if self.tooltip_item:
            self._render_tooltip(surface, self.tooltip_item, self.tooltip_position)
    
    def _draw_slot(self, surface: pygame.Surface, x: int, y: int, slot_index: int):
        """Draw a single inventory slot."""
        slot_rect = pygame.Rect(x, y, self.slot_width, self.slot_height)
        
        # Determine slot state
        is_selected = self.selected_slot == slot_index
        is_hovered = self.hovered_slot == slot_index
        has_item = slot_index < len(self.items)
        
        # Draw slot background
        if is_selected:
            pygame.draw.rect(surface, self.SELECTED_COLOR, slot_rect)
        elif is_hovered:
            pygame.draw.rect(surface, self.HOVER_COLOR, slot_rect)
        else:
            pygame.draw.rect(surface, self.SLOT_COLOR, slot_rect)
        
        # Draw slot border
        border_color = self.SELECTED_COLOR if is_selected else self.BORDER_COLOR
        pygame.draw.rect(surface, border_color, slot_rect, 2)
        
        # Draw item if present
        if has_item:
            item = self.items[slot_index]
            self._draw_item(surface, item, x, y, slot_index)
    
    def _draw_item(self, surface: pygame.Surface, item: Item, x: int, y: int, slot_index: int):
        """Draw an item in a slot."""
        if item is None:
            return
            
        # Get item sprite
        item_sprite_map = {
            ItemType.WEAPON: "sword",
            ItemType.RANGED_WEAPON: "bow",
            ItemType.AMMUNITION: "arrow",
            ItemType.POTION: "classic_roguelike_134",
            ItemType.ARMOUR: "armor_light",
            ItemType.HELMET: "helmet",
            ItemType.BOOTS: "boots",
            ItemType.RING: "ring",
            ItemType.AMULET: "amulet"
        }
        
        sprite_name = item_sprite_map.get(item.item_type)
        if sprite_name:
            item_sprite = self.sprite_manager.sprite_system.get_sprite(sprite_name)
            if item_sprite:
                # Scale and center item sprite
                item_size = min(self.slot_width - 8, self.slot_height - 8)
                scaled_item = pygame.transform.scale(item_sprite, (item_size, item_size))
                item_rect = scaled_item.get_rect(center=(x + self.slot_width // 2, y + self.slot_height // 2))
                surface.blit(scaled_item, item_rect)
        
        # Draw item name
        item_name = item.name[:6].upper()
        name_surface = self.tiny_font.render_text(item_name, self.TEXT_COLOR)
        name_rect = name_surface.get_rect(center=(x + self.slot_width // 2, y + self.slot_height - 8))
        surface.blit(name_surface, name_rect)
        
        # Draw stack count for stackable items
        if item.item_type.is_stackable() and item.stack_size > 1:
            count_surface = self.tiny_font.render_text(str(item.stack_size), self.TEXT_COLOR)
            count_rect = count_surface.get_rect(bottomright=(x + self.slot_width - 2, y + self.slot_height - 2))
            
            # Draw black outline for better visibility
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                outline_rect = count_rect.copy()
                outline_rect.x += dx
                outline_rect.y += dy
                outline_surface = self.tiny_font.render_text(str(item.stack_size), (0, 0, 0))
                surface.blit(outline_surface, outline_rect)
            
            surface.blit(count_surface, count_rect)
    
    def _render_tooltip(self, surface: pygame.Surface, item: Item, position: Tuple[int, int]):
        """Render item tooltip."""
        lines = [
            item.name,
            f"Type: {item.item_type.value}",
            "",
            item.description
        ]
        
        # Add stat bonuses
        if item.stat_bonuses:
            lines.append("")
            lines.append("Bonuses:")
            for stat, bonus in item.stat_bonuses.items():
                sign = "+" if bonus >= 0 else ""
                lines.append(f"  {sign}{bonus} {stat.value}")
        
        # Convert lines to uppercase for sprite font
        lines = [line.upper() for line in lines]
        
        # Render each line to calculate dimensions
        rendered_lines = []
        max_width = 0
        total_height = 0
        line_spacing = 16
        
        for line in lines:
            if line.strip():
                text_surface = self.tiny_font.render_text(line, self.TEXT_COLOR)
                rendered_lines.append(text_surface)
                max_width = max(max_width, text_surface.get_width())
                total_height += line_spacing
            else:
                rendered_lines.append(None)
                total_height += line_spacing // 2
        
        # Calculate tooltip dimensions
        tooltip_width = max_width + 16
        tooltip_height = total_height + 16
        
        # Position tooltip
        tooltip_x = min(position[0] + 10, surface.get_width() - tooltip_width)
        tooltip_y = min(position[1] - tooltip_height - 10, surface.get_height() - tooltip_height)
        
        # Create tooltip surface
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        
        # Draw tooltip background
        pygame.draw.rect(tooltip_surface, (0, 0, 0, 200), tooltip_surface.get_rect())
        pygame.draw.rect(tooltip_surface, self.BORDER_COLOR, tooltip_surface.get_rect(), 2)
        
        # Draw tooltip text
        y_offset = 8
        for rendered_line in rendered_lines:
            if rendered_line:
                tooltip_surface.blit(rendered_line, (8, y_offset))
                y_offset += line_spacing
            else:
                y_offset += line_spacing // 2
        
        surface.blit(tooltip_surface, (tooltip_x, tooltip_y))
    
    def _get_slot_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """Get slot index at mouse position."""
        x, y = pos
        
        # Check if within grid bounds
        if (x < self.x or y < self.y or 
            x > self.x + self.width or y > self.y + self.height):
            return None
        
        # Calculate slot coordinates
        col = (x - self.x) // self.slot_width
        row = (y - self.y) // self.slot_height
        
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return row * self.cols + col
        
        return None
    
    def get_selected_item(self) -> Optional[Item]:
        """Get the currently selected item."""
        if self.selected_slot is not None and self.selected_slot < len(self.items):
            return self.items[self.selected_slot]
        return None
    
    def clear_selection(self):
        """Clear the current selection."""
        self.selected_slot = None
