"""
Equipment Panel Component
A standalone equipment panel that can be used in various UI contexts.
Integrates with the sprite system for visual rendering.
"""

import pygame
from typing import Dict, Optional, Tuple, Callable
from pathlib import Path
from .character_system import Item, ItemType, EquipmentSlot
from .sprite_font import SpriteFont
from .sprite_system import GameSpriteManager


class EquipmentPanel:
    """
    A visual equipment panel component that can be embedded in other UI elements.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, assets_path: Optional[Path] = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Initialize sprite manager
        self.sprite_manager = GameSpriteManager()
        if assets_path is None:
            assets_path = Path(__file__).parent.parent / "assets"
        self.sprite_manager.load_game_assets(assets_path)
        
        # Equipment slots layout
        self.slot_size = 48
        self.slot_spacing = 60
        self.slots_layout = {
            EquipmentSlot.HEAD: (width // 2 - self.slot_size // 2, 20),
            EquipmentSlot.NECK: (width // 2 - self.slot_size // 2, 20 + self.slot_spacing),
            EquipmentSlot.TORSO: (width // 2 - self.slot_size // 2, 20 + self.slot_spacing * 2),
            EquipmentSlot.LEGS: (width // 2 - self.slot_size // 2, 20 + self.slot_spacing * 3),
            EquipmentSlot.WEAPON_1: (20, 20 + self.slot_spacing * 2),
            EquipmentSlot.WEAPON_2: (width - 20 - self.slot_size, 20 + self.slot_spacing * 2),
            EquipmentSlot.RING_1: (20, 20 + self.slot_spacing * 3),
            EquipmentSlot.RING_2: (width - 20 - self.slot_size, 20 + self.slot_spacing * 3),
        }
        
        # UI state
        self.selected_slot: Optional[EquipmentSlot] = None
        self.hovered_slot: Optional[EquipmentSlot] = None
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
        self.on_slot_click: Optional[Callable[[EquipmentSlot, Optional[Item]], None]] = None
        self.on_slot_hover: Optional[Callable[[EquipmentSlot, Optional[Item]], None]] = None
    
    def set_equipment(self, equipment: Dict[EquipmentSlot, Item]):
        """Set the equipment to display."""
        self.equipment = equipment
    
    def handle_mouse_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle mouse click events.
        
        Args:
            pos: Mouse position (x, y)
            
        Returns:
            Action message or None
        """
        slot = self._get_slot_at_position(pos)
        if slot is not None:
            self.selected_slot = slot
            equipped_item = self.equipment.get(slot)
            
            if self.on_slot_click:
                self.on_slot_click(slot, equipped_item)
            
            if equipped_item:
                return f"Selected {equipped_item.name} in {slot.value}"
            else:
                return f"Selected empty {slot.value} slot"
        
        return None
    
    def handle_mouse_hover(self, pos: Tuple[int, int]):
        """
        Handle mouse hover events.
        
        Args:
            pos: Mouse position (x, y)
        """
        slot = self._get_slot_at_position(pos)
        if slot is not None:
            self.hovered_slot = slot
            equipped_item = self.equipment.get(slot)
            
            if equipped_item:
                self.tooltip_item = equipped_item
                self.tooltip_position = pos
            else:
                self.tooltip_item = None
            
            if self.on_slot_hover:
                self.on_slot_hover(slot, equipped_item)
        else:
            self.hovered_slot = None
            self.tooltip_item = None
    
    def render(self, surface: pygame.Surface):
        """
        Render the equipment panel.
        
        Args:
            surface: Pygame surface to render to
        """
        # Draw panel background
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.BACKGROUND_COLOR, panel_rect)
        pygame.draw.rect(surface, self.BORDER_COLOR, panel_rect, 2)
        
        # Draw title
        title_surface = self.small_font.render_text("EQUIPMENT", self.TEXT_COLOR)
        title_rect = title_surface.get_rect(centerx=self.x + self.width // 2, top=self.y + 5)
        surface.blit(title_surface, title_rect)
        
        # Draw equipment slots
        for slot, position in self.slots_layout.items():
            slot_x = self.x + position[0]
            slot_y = self.y + position[1]
            self._draw_slot(surface, slot, slot_x, slot_y)
        
        # Draw tooltip if hovering over item
        if self.tooltip_item:
            self._render_tooltip(surface, self.tooltip_item, self.tooltip_position)
    
    def _draw_slot(self, surface: pygame.Surface, slot: EquipmentSlot, x: int, y: int):
        """Draw a single equipment slot."""
        slot_rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
        
        # Determine slot state
        is_selected = self.selected_slot == slot
        is_hovered = self.hovered_slot == slot
        has_item = slot in self.equipment
        
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
        
        # Draw equipped item or slot label
        if has_item:
            item = self.equipment[slot]
            self._draw_item(surface, item, x, y)
        else:
            self._draw_slot_label(surface, slot, x, y)
    
    def _draw_item(self, surface: pygame.Surface, item: Item, x: int, y: int):
        """Draw an equipped item."""
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
                item_size = self.slot_size - 8
                scaled_item = pygame.transform.scale(item_sprite, (item_size, item_size))
                item_rect = scaled_item.get_rect(center=(x + self.slot_size // 2, y + self.slot_size // 2))
                surface.blit(scaled_item, item_rect)
        
        # Draw item name below sprite
        item_name = item.name[:6].upper()
        name_surface = self.tiny_font.render_text(item_name, self.TEXT_COLOR)
        name_rect = name_surface.get_rect(center=(x + self.slot_size // 2, y + self.slot_size + 8))
        surface.blit(name_surface, name_rect)
    
    def _draw_slot_label(self, surface: pygame.Surface, slot: EquipmentSlot, x: int, y: int):
        """Draw slot type label for empty slots."""
        slot_abbrev = self._get_slot_abbreviation(slot)
        label_surface = self.tiny_font.render_text(slot_abbrev, (150, 150, 150))
        label_rect = label_surface.get_rect(center=(x + self.slot_size // 2, y + self.slot_size // 2))
        surface.blit(label_surface, label_rect)
    
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
    
    def _get_slot_at_position(self, pos: Tuple[int, int]) -> Optional[EquipmentSlot]:
        """Get equipment slot at mouse position."""
        x, y = pos
        
        # Check if within panel bounds
        if (x < self.x or y < self.y or 
            x > self.x + self.width or y > self.y + self.height):
            return None
        
        # Check each slot
        for slot, position in self.slots_layout.items():
            slot_x = self.x + position[0]
            slot_y = self.y + position[1]
            slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
            
            if slot_rect.collidepoint(pos):
                return slot
        
        return None
    
    def _get_slot_abbreviation(self, slot: EquipmentSlot) -> str:
        """Get abbreviation for equipment slot."""
        abbreviations = {
            EquipmentSlot.HEAD: "HEAD",
            EquipmentSlot.NECK: "NECK", 
            EquipmentSlot.TORSO: "BODY",
            EquipmentSlot.LEGS: "LEGS",
            EquipmentSlot.WEAPON_1: "WEP1",
            EquipmentSlot.WEAPON_2: "WEP2",
            EquipmentSlot.RING_1: "RNG1",
            EquipmentSlot.RING_2: "RNG2"
        }
        return abbreviations.get(slot, "???")
    
    def get_selected_slot(self) -> Optional[EquipmentSlot]:
        """Get the currently selected slot."""
        return self.selected_slot
    
    def clear_selection(self):
        """Clear the current selection."""
        self.selected_slot = None
