"""
Inventory System for Mythica
Manages character inventory, interactive character screen, and item management.
Integrates with the sprite system for visual rendering.
"""

import pygame
import random
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
from pathlib import Path
from .character_system import Item, EquipmentSlot, ItemType
from .sprite_font import SpriteFont
from .sprite_system import GameSpriteManager


class InventoryAction(Enum):
    """Actions that can be performed in the inventory screen."""
    EQUIP = "equip"
    UNEQUIP = "unequip"
    DROP = "drop"
    EXAMINE = "examine"


class Inventory:
    """
    Character inventory for storing unequipped items.
    """
    
    def __init__(self, max_items: int = 30):
        self.items: List[Item] = []
        self.max_items = max_items
    
    def add_item(self, item: Item) -> bool:
        """
        Add an item to the inventory. Attempts to stack with existing items if possible.
        
        Args:
            item: Item to add
            
        Returns:
            True if item was added (or stacked), False if inventory is full
        """
        # Try to stack with existing items first
        if item.item_type.is_stackable():
            for existing_item in self.items:
                if existing_item.can_stack_with(item):
                    remaining = existing_item.add_to_stack(item.stack_size)
                    if remaining == 0:
                        return True
                    item.stack_size = remaining  # Update remaining count
        
        # If we couldn't stack completely, need a new slot
        if len(self.items) >= self.max_items:
            return False
        
        self.items.append(item)
        return True
    
    def remove_item(self, item: Item, count: int = 1) -> bool:
        """
        Remove an item from the inventory.
        
        Args:
            item: Item to remove
            count: Number of items to remove from stack (default 1)
            
        Returns:
            True if item was removed, False if not found
        """
        if item in self.items:
            if item.item_type.is_stackable():
                removed = item.remove_from_stack(count)
                if removed > 0:
                    if item.stack_size == 0:
                        self.items.remove(item)
                    return True
                return False
            else:
                self.items.remove(item)
                return True
        return False
    
    def remove_item_at_index(self, index: int, count: int = 1) -> Optional[Item]:
        """
        Remove an item at a specific index.
        
        Args:
            index: Index of item to remove
            count: Number of items to remove from stack (default 1)
            
        Returns:
            Removed item or None if index invalid
        """
        if 0 <= index < len(self.items):
            item = self.items[index]
            if item.item_type.is_stackable():
                # Create a new item with the removed stack
                removed = item.remove_from_stack(count)
                if removed > 0:
                    if item.stack_size == 0:
                        self.items.pop(index)
                    new_item = Item(item.name, item.item_type, item.stat_bonuses.copy(), removed)
                    return new_item
                return None
            else:
                return self.items.pop(index)
        return None
    
    def get_item_count(self) -> int:
        """Get the number of items in inventory."""
        return len(self.items)
    
    def is_full(self) -> bool:
        """Check if inventory is full."""
        return len(self.items) >= self.max_items
    
    def get_items_by_type(self, item_type: ItemType) -> List[Item]:
        """Get all items of a specific type."""
        return [item for item in self.items if item.item_type == item_type]
    
    def clear(self):
        """Remove all items from inventory."""
        self.items.clear()


class InteractiveCharacterScreen:
    """
    Interactive character screen with full inventory management.
    Handles mouse/keyboard input for equipping/unequipping items.
    Integrates with the sprite system for visual rendering.
    """
    
    def __init__(self, screen_width: int = 800, screen_height: int = 600, assets_path: Optional[Path] = None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Initialize sprite manager
        self.sprite_manager = GameSpriteManager()
        if assets_path is None:
            assets_path = Path(__file__).parent.parent / "assets"
        self.sprite_manager.load_game_assets(assets_path)
        
        # UI Layout constants
        self.PANEL_WIDTH = 1000  # Wider panel for better spacing
        self.PANEL_HEIGHT = 800  # Taller panel for better spacing
        self.PANEL_X = (screen_width - self.PANEL_WIDTH) // 2
        self.PANEL_Y = (screen_height - self.PANEL_HEIGHT) // 2
        
        # Equipment slots layout (visual positions)
        # Reorganized equipment slots with more spacing
        slot_base_x = 100  # Increased left margin for equipment section
        slot_spacing_y = 90  # Increased vertical spacing between slots
        base_y = 220  # Increased top margin
        
        self.equipment_slots_layout = {
            # Center column
            EquipmentSlot.HEAD: (slot_base_x + 90, base_y),                    # Head at top
            EquipmentSlot.NECK: (slot_base_x + 90, base_y + slot_spacing_y),   # Neck below head
            EquipmentSlot.TORSO: (slot_base_x + 90, base_y + slot_spacing_y * 2), # Torso in middle
            EquipmentSlot.LEGS: (slot_base_x + 90, base_y + slot_spacing_y * 3),  # Legs at bottom
            # Left column
            EquipmentSlot.WEAPON_1: (slot_base_x, base_y + slot_spacing_y * 2),      # Left weapon
            EquipmentSlot.RING_1: (slot_base_x, base_y + slot_spacing_y * 3),        # Left ring
            # Right column
            EquipmentSlot.WEAPON_2: (slot_base_x + 180, base_y + slot_spacing_y * 2), # Right weapon
            EquipmentSlot.RING_2: (slot_base_x + 180, base_y + slot_spacing_y * 3),   # Right ring
        }
        
        # Inventory grid layout
        self.INVENTORY_START_X = 500  # More space between equipment and inventory
        self.INVENTORY_START_Y = 220  # Align with equipment section
        self.SLOT_SIZE = 48  # Adjusted to match Interface sprites
        self.SLOT_SPACING = 80  # More space between slots
        self.INVENTORY_COLS = 6
        self.INVENTORY_ROWS = 6  # Reduced rows to prevent overflow
        
        # UI state
        self.selected_item_index: Optional[int] = None
        self.selected_equipment_slot: Optional[EquipmentSlot] = None
        self.tooltip_item: Optional[Item] = None
        self.tooltip_position: Tuple[int, int] = (0, 0)
        
        # Colors
        self.BACKGROUND_COLOR = (40, 40, 50)
        self.PANEL_COLOR = (60, 60, 70)
        self.BORDER_COLOR = (200, 200, 200)
        self.SLOT_COLOR = (80, 80, 90)
        self.SELECTED_COLOR = (255, 255, 100)
        self.EQUIPPED_COLOR = (100, 255, 100)
        self.TEXT_COLOR = (255, 255, 255)
        self.TOOLTIP_COLOR = (255, 255, 220)
        
        # Sprite Fonts with adjusted scales
        self.title_font = SpriteFont(scale=1.5)  # Larger for main title
        self.header_font = SpriteFont(scale=1.0)  # For section headers
        self.text_font = SpriteFont(scale=0.75)  # For regular text
        self.small_font = SpriteFont(scale=0.5)  # For tooltips and item names
    
    def handle_mouse_click(self, pos: Tuple[int, int], character, inventory: Inventory) -> Optional[str]:
        """
        Handle mouse click events in the character screen.
        
        Args:
            pos: Mouse position (x, y)
            character: Character object
            inventory: Inventory object
            
        Returns:
            Action message or None
        """
        adjusted_pos = (pos[0] - self.PANEL_X, pos[1] - self.PANEL_Y)
        
        # Check equipment slot clicks
        equipment_slot = self._get_equipment_slot_at_position(adjusted_pos)
        if equipment_slot:
            return self._handle_equipment_slot_click(equipment_slot, character, inventory)
        
        # Check inventory slot clicks
        inventory_index = self._get_inventory_slot_at_position(adjusted_pos)
        if inventory_index is not None and inventory_index < len(inventory.items):
            return self._handle_inventory_slot_click(inventory_index, character, inventory)
        
        # Clear selection if clicking empty area
        self.selected_item_index = None
        self.selected_equipment_slot = None
        return None
    
    def handle_mouse_hover(self, pos: Tuple[int, int], character, inventory: Inventory):
        """
        Handle mouse hover for tooltips.
        
        Args:
            pos: Mouse position (x, y)
            character: Character object
            inventory: Inventory object
        """
        adjusted_pos = (pos[0] - self.PANEL_X, pos[1] - self.PANEL_Y)
        
        # Check if hovering over equipment slot
        equipment_slot = self._get_equipment_slot_at_position(adjusted_pos)
        if equipment_slot:
            equipped_item = character.equipment.get_equipped_item(equipment_slot)
            if equipped_item:
                self.tooltip_item = equipped_item
                self.tooltip_position = pos
                return
        
        # Check if hovering over inventory item
        inventory_index = self._get_inventory_slot_at_position(adjusted_pos)
        if inventory_index is not None and inventory_index < len(inventory.items):
            self.tooltip_item = inventory.items[inventory_index]
            self.tooltip_position = pos
            return
        
        # Clear tooltip
        self.tooltip_item = None
    
    def render(self, screen: pygame.Surface, character, inventory: Inventory):
        """
        Render the interactive character screen.
        
        Args:
            screen: Pygame surface to render to
            character: Character object
            inventory: Inventory object
        """
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Create main panel surface
        panel_surface = pygame.Surface((self.PANEL_WIDTH, self.PANEL_HEIGHT), pygame.SRCALPHA)
        
        # Draw panel background
        background = self.sprite_manager.sprite_system.get_sprite("interface_background")
        if background:
            # Scale background to 32x32 tiles
            scaled_background = pygame.transform.scale(background, (32, 32))
            for y in range(0, self.PANEL_HEIGHT, 32):
                for x in range(0, self.PANEL_WIDTH, 32):
                    panel_surface.blit(scaled_background, (x, y))
        
        # Draw panel frame (ornate style)
        frame_top = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_top")
        frame_bottom = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_bottom")
        frame_left = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_left")
        frame_right = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_right")
        frame_corner_tl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tl")
        frame_corner_tr = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tr")
        frame_corner_bl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_bl")
        frame_corner_br = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_br")
        
        if all([frame_top, frame_bottom, frame_left, frame_right,
               frame_corner_tl, frame_corner_tr, frame_corner_bl, frame_corner_br]):
            # Scale frame elements to appropriate sizes
            corner_size = 16
            frame_top_scaled = pygame.transform.scale(frame_top, (32, 16))
            frame_bottom_scaled = pygame.transform.scale(frame_bottom, (32, 16))
            frame_left_scaled = pygame.transform.scale(frame_left, (16, 32))
            frame_right_scaled = pygame.transform.scale(frame_right, (16, 32))
            corner_tl_scaled = pygame.transform.scale(frame_corner_tl, (corner_size, corner_size))
            corner_tr_scaled = pygame.transform.scale(frame_corner_tr, (corner_size, corner_size))
            corner_bl_scaled = pygame.transform.scale(frame_corner_bl, (corner_size, corner_size))
            corner_br_scaled = pygame.transform.scale(frame_corner_br, (corner_size, corner_size))
            
            # Draw corners
            panel_surface.blit(corner_tl_scaled, (0, 0))
            panel_surface.blit(corner_tr_scaled, (self.PANEL_WIDTH - corner_size, 0))
            panel_surface.blit(corner_bl_scaled, (0, self.PANEL_HEIGHT - corner_size))
            panel_surface.blit(corner_br_scaled, (self.PANEL_WIDTH - corner_size, self.PANEL_HEIGHT - corner_size))
            
            # Draw top and bottom edges
            for x in range(corner_size, self.PANEL_WIDTH - corner_size, 32):
                panel_surface.blit(frame_top_scaled, (x, 0))
                panel_surface.blit(frame_bottom_scaled, (x, self.PANEL_HEIGHT - 16))
            
            # Draw left and right edges
            for y in range(corner_size, self.PANEL_HEIGHT - corner_size, 32):
                panel_surface.blit(frame_left_scaled, (0, y))
                panel_surface.blit(frame_right_scaled, (self.PANEL_WIDTH - 16, y))
        
        # Render character info
        self._render_character_info(panel_surface, character)
        
        # Render equipment slots
        self._render_equipment_slots(panel_surface, character)
        
        # Render inventory grid
        self._render_inventory_grid(panel_surface, inventory)
        
        # Render instructions
        self._render_instructions(panel_surface)
        
        # Blit panel to screen
        screen.blit(panel_surface, (self.PANEL_X, self.PANEL_Y))
        
        # Render tooltip if hovering over item
        if self.tooltip_item:
            self._render_tooltip(screen, self.tooltip_item, self.tooltip_position)
    
    def _render_character_info(self, surface: pygame.Surface, character):
        """Render character stats and basic info."""
        summary = character.get_character_summary()
        
        # Title - centered at top with more space
        title_surface = self.title_font.render_text(f"ADVENTURER - LEVEL {summary['level']}", self.TEXT_COLOR)
        title_rect = title_surface.get_rect(centerx=self.PANEL_WIDTH // 2, top=40)
        surface.blit(title_surface, title_rect)
        
        # Character stats in a clean layout
        stats_x = 80  # Align with equipment section
        stats_y = 120
        line_height = 35  # More space between lines
        
        # Health with colored slash
        hp_current, hp_max = summary['hp']
        hp_label = self.text_font.render_text("HP", self.TEXT_COLOR)
        surface.blit(hp_label, (stats_x, stats_y))
        
        hp_value = self.text_font.render_text(f"{hp_current}/{hp_max}", self.TEXT_COLOR)
        surface.blit(hp_value, (stats_x + 100, stats_y))
        
        # Experience points
        xp_label = self.text_font.render_text("XP", self.TEXT_COLOR)
        surface.blit(xp_label, (stats_x + 250, stats_y))
        
        xp_value = self.text_font.render_text(str(summary['experience']), self.TEXT_COLOR)
        surface.blit(xp_value, (stats_x + 350, stats_y))
        
        # Perk points on new line
        perk_label = self.text_font.render_text("PERK POINTS", self.SELECTED_COLOR)
        surface.blit(perk_label, (stats_x, stats_y + line_height))
        
        perk_value = self.text_font.render_text(str(summary['perk_points']), self.SELECTED_COLOR)
        surface.blit(perk_value, (stats_x + 200, stats_y + line_height))
    
    def _render_equipment_slots(self, surface: pygame.Surface, character):
        """Render equipment slots with equipped items."""
        # Draw equipment frame
        frame_x = 50
        frame_y = 160
        frame_width = 300
        frame_height = 400
        
        # Draw frame background
        background = self.sprite_manager.sprite_system.get_sprite("interface_background")
        if background:
            scaled_background = pygame.transform.scale(background, (32, 32))
            for y in range(frame_y + 16, frame_y + frame_height - 16, 32):
                for x in range(frame_x + 16, frame_x + frame_width - 16, 32):
                    surface.blit(scaled_background, (x, y))
        
        # Draw frame borders (ornate style)
        frame_top = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_top")
        frame_bottom = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_bottom")
        frame_left = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_left")
        frame_right = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_right")
        frame_corner_tl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tl")
        frame_corner_tr = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tr")
        frame_corner_bl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_bl")
        frame_corner_br = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_br")
        
        if all([frame_top, frame_bottom, frame_left, frame_right,
               frame_corner_tl, frame_corner_tr, frame_corner_bl, frame_corner_br]):
            # Scale frame elements to appropriate sizes
            corner_size = 16
            frame_top_scaled = pygame.transform.scale(frame_top, (32, 16))
            frame_bottom_scaled = pygame.transform.scale(frame_bottom, (32, 16))
            frame_left_scaled = pygame.transform.scale(frame_left, (16, 32))
            frame_right_scaled = pygame.transform.scale(frame_right, (16, 32))
            corner_tl_scaled = pygame.transform.scale(frame_corner_tl, (corner_size, corner_size))
            corner_tr_scaled = pygame.transform.scale(frame_corner_tr, (corner_size, corner_size))
            corner_bl_scaled = pygame.transform.scale(frame_corner_bl, (corner_size, corner_size))
            corner_br_scaled = pygame.transform.scale(frame_corner_br, (corner_size, corner_size))
            
            # Draw corners
            surface.blit(corner_tl_scaled, (frame_x, frame_y))
            surface.blit(corner_tr_scaled, (frame_x + frame_width - corner_size, frame_y))
            surface.blit(corner_bl_scaled, (frame_x, frame_y + frame_height - corner_size))
            surface.blit(corner_br_scaled, (frame_x + frame_width - corner_size, frame_y + frame_height - corner_size))
            
            # Draw top and bottom edges
            for x in range(frame_x + corner_size, frame_x + frame_width - corner_size, 32):
                surface.blit(frame_top_scaled, (x, frame_y))
                surface.blit(frame_bottom_scaled, (x, frame_y + frame_height - 16))
            
            # Draw left and right edges
            for y in range(frame_y + corner_size, frame_y + frame_height - corner_size, 32):
                surface.blit(frame_left_scaled, (frame_x, y))
                surface.blit(frame_right_scaled, (frame_x + frame_width - 16, y))
        
        # Equipment title
        title_surface = self.header_font.render_text("EQUIPMENT", self.TEXT_COLOR)
        title_rect = title_surface.get_rect(centerx=frame_x + frame_width // 2, top=frame_y + 20)
        surface.blit(title_surface, title_rect)
        
        # Draw equipment slots
        for slot, position in self.equipment_slots_layout.items():
            x, y = position
            
            # Get appropriate slot sprite based on slot type
            slot_type_map = {
                EquipmentSlot.HEAD: "interface_slot_armor",
                EquipmentSlot.NECK: "interface_slot_amulet",
                EquipmentSlot.TORSO: "interface_slot_armor",
                EquipmentSlot.LEGS: "interface_slot_armor",
                EquipmentSlot.WEAPON_1: "interface_slot_weapon",
                EquipmentSlot.WEAPON_2: "interface_slot_weapon",
                EquipmentSlot.RING_1: "interface_slot_ring",
                EquipmentSlot.RING_2: "interface_slot_ring"
            }
            
            # Load slot background at original size
            slot_sprite = self.sprite_manager.sprite_system.get_sprite(
                slot_type_map.get(slot, "interface_slot_empty")
            )
            
            # Scale to match our slot size
            if slot_sprite:
                slot_sprite = pygame.transform.scale(slot_sprite, (self.SLOT_SIZE, self.SLOT_SIZE))
                
            if slot_sprite:
                # Tint slot if selected
                if self.selected_equipment_slot == slot:
                    tinted_slot = slot_sprite.copy()
                    tint_overlay = pygame.Surface(slot_sprite.get_size(), pygame.SRCALPHA)
                    tint_overlay.fill((100, 255, 100, 100))  # Green tint
                    tinted_slot.blit(tint_overlay, (0, 0))
                    surface.blit(tinted_slot, (x, y))
                else:
                    surface.blit(slot_sprite, (x, y))
                    
                # Draw borders
                border_color = (100, 255, 100) if self.selected_equipment_slot == slot else (200, 200, 200)
                border_alpha = 255 if self.selected_equipment_slot == slot else 128
                
                # Draw border lines
                pygame.draw.line(surface, border_color, (x, y), (x + self.SLOT_SIZE, y), 2)  # Top
                pygame.draw.line(surface, border_color, (x, y + self.SLOT_SIZE), (x + self.SLOT_SIZE, y + self.SLOT_SIZE), 2)  # Bottom
                pygame.draw.line(surface, border_color, (x, y), (x, y + self.SLOT_SIZE), 2)  # Left
                pygame.draw.line(surface, border_color, (x + self.SLOT_SIZE, y), (x + self.SLOT_SIZE, y + self.SLOT_SIZE), 2)  # Right
            
            # Draw equipped item or slot label
            equipped_item = character.equipment.get_equipped_item(slot)
            if equipped_item:
                # Get item sprite based on type
                item_sprite_map = {
                    ItemType.WEAPON: "sword",
                    ItemType.ARMOUR: "armor_light",
                    ItemType.HELMET: "helmet",
                    ItemType.BOOTS: "boots",
                    ItemType.RING: "ring",
                    ItemType.AMULET: "amulet"
                }
                sprite_name = item_sprite_map.get(equipped_item.item_type)
                if sprite_name:
                    item_sprite = self.sprite_manager.sprite_system.get_sprite(sprite_name)
                    if item_sprite:
                        # Scale and center item sprite in slot
                        scaled_item = pygame.transform.scale(item_sprite, (self.SLOT_SIZE - 8, self.SLOT_SIZE - 8))
                        item_rect = scaled_item.get_rect(center=(x + self.SLOT_SIZE // 2, y + self.SLOT_SIZE // 2))
                        surface.blit(scaled_item, item_rect)
                
                # Draw item name below sprite
                item_surface = self.small_font.render_text(equipped_item.name[:8].upper(), self.TEXT_COLOR)
                text_rect = item_surface.get_rect(center=(x + self.SLOT_SIZE // 2, y + self.SLOT_SIZE + 5))
                surface.blit(item_surface, text_rect)
            else:
                # Draw slot type abbreviation
                slot_abbrev = self._get_slot_abbreviation(slot)
                slot_surface = self.small_font.render_text(slot_abbrev, (150, 150, 150))
                text_rect = slot_surface.get_rect(center=(x + self.SLOT_SIZE // 2, y + self.SLOT_SIZE // 2))
                surface.blit(slot_surface, text_rect)
    
    def _render_inventory_grid(self, surface: pygame.Surface, inventory: Inventory):
        """Render inventory grid with items."""
        # Draw inventory frame (ornate style)
        frame_top = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_top")
        frame_bottom = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_bottom")
        frame_left = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_left")
        frame_right = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_right")
        frame_corner_tl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tl")
        frame_corner_tr = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tr")
        frame_corner_bl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_bl")
        frame_corner_br = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_br")
        
        # Calculate frame dimensions
        frame_x = self.INVENTORY_START_X - 20
        frame_y = 160
        frame_width = (self.PANEL_WIDTH - 50) - frame_x
        frame_height = (self.INVENTORY_START_Y + self.INVENTORY_ROWS * self.SLOT_SPACING + 40) - frame_y
        
        # Draw frame background
        background = self.sprite_manager.sprite_system.get_sprite("interface_background")
        if background:
            scaled_background = pygame.transform.scale(background, (32, 32))
            for y in range(frame_y + 16, frame_y + frame_height - 16, 32):
                for x in range(frame_x + 16, frame_x + frame_width - 16, 32):
                    surface.blit(scaled_background, (x, y))
        
        # Draw frame borders (ornate style)
        if all([frame_top, frame_bottom, frame_left, frame_right,
               frame_corner_tl, frame_corner_tr, frame_corner_bl, frame_corner_br]):
            # Scale frame elements to appropriate sizes
            corner_size = 16
            frame_top_scaled = pygame.transform.scale(frame_top, (32, 16))
            frame_bottom_scaled = pygame.transform.scale(frame_bottom, (32, 16))
            frame_left_scaled = pygame.transform.scale(frame_left, (16, 32))
            frame_right_scaled = pygame.transform.scale(frame_right, (16, 32))
            corner_tl_scaled = pygame.transform.scale(frame_corner_tl, (corner_size, corner_size))
            corner_tr_scaled = pygame.transform.scale(frame_corner_tr, (corner_size, corner_size))
            corner_bl_scaled = pygame.transform.scale(frame_corner_bl, (corner_size, corner_size))
            corner_br_scaled = pygame.transform.scale(frame_corner_br, (corner_size, corner_size))
            
            # Draw corners
            surface.blit(corner_tl_scaled, (frame_x, frame_y))
            surface.blit(corner_tr_scaled, (frame_x + frame_width - corner_size, frame_y))
            surface.blit(corner_bl_scaled, (frame_x, frame_y + frame_height - corner_size))
            surface.blit(corner_br_scaled, (frame_x + frame_width - corner_size, frame_y + frame_height - corner_size))
            
            # Draw top and bottom edges
            for x in range(frame_x + corner_size, frame_x + frame_width - corner_size, 32):
                surface.blit(frame_top_scaled, (x, frame_y))
                surface.blit(frame_bottom_scaled, (x, frame_y + frame_height - 16))
            
            # Draw left and right edges
            for y in range(frame_y + corner_size, frame_y + frame_height - corner_size, 32):
                surface.blit(frame_left_scaled, (frame_x, y))
                surface.blit(frame_right_scaled, (frame_x + frame_width - 16, y))
        
        # Inventory title and capacity
        title_surface = self.header_font.render_text("INVENTORY", self.TEXT_COLOR)
        capacity_surface = self.text_font.render_text(f"{inventory.get_item_count()}/{inventory.max_items} ITEMS", self.TEXT_COLOR)
        
        # Center the combined text
        total_width = title_surface.get_width() + 20 + capacity_surface.get_width()
        center_x = frame_x + (frame_width // 2)
        start_x = center_x - (total_width // 2)
        
        surface.blit(title_surface, (start_x, frame_y + 20))
        surface.blit(capacity_surface, (start_x + title_surface.get_width() + 20, frame_y + 22))
        
        # Draw inventory slots
        for row in range(self.INVENTORY_ROWS):
            for col in range(self.INVENTORY_COLS):
                index = row * self.INVENTORY_COLS + col
                x = self.INVENTORY_START_X + col * self.SLOT_SPACING
                y = self.INVENTORY_START_Y + row * self.SLOT_SPACING
                
                                # Draw slot background and border
                def draw_slot_border(x: int, y: int, index: int, selected: bool = False):
                    # Draw background
                    slot_sprite = None
                    if index < len(inventory.items):
                        item = inventory.items[index]
                        slot_type_map = {
                            ItemType.WEAPON: "interface_slot_weapon",
                            ItemType.RANGED_WEAPON: "interface_slot_weapon",
                            ItemType.ARMOUR: "interface_slot_armor",
                            ItemType.HELMET: "interface_slot_armor",
                            ItemType.BOOTS: "interface_slot_armor",
                            ItemType.RING: "interface_slot_ring",
                            ItemType.AMULET: "interface_slot_amulet",
                            ItemType.POTION: "interface_slot_potion"
                        }
                        slot_sprite = self.sprite_manager.sprite_system.get_sprite(
                            slot_type_map.get(item.item_type, "interface_slot_empty")
                        )
                    
                    if not slot_sprite:
                        slot_sprite = self.sprite_manager.sprite_system.get_sprite(
                            "interface_slot_empty"
                        )
                    
                    if slot_sprite:
                        if selected:
                            # Create tinted copy for selected slot
                            tinted_slot = slot_sprite.copy()
                            tint_overlay = pygame.Surface(slot_sprite.get_size(), pygame.SRCALPHA)
                            tint_overlay.fill((255, 255, 0, 100))  # Yellow tint
                            tinted_slot.blit(tint_overlay, (0, 0))
                            surface.blit(tinted_slot, (x, y))
                        else:
                            # Make empty slots slightly transparent
                            if index >= len(inventory.items):
                                slot_sprite.set_alpha(128)
                            surface.blit(slot_sprite, (x, y))
                    
                    # Draw borders
                    border_color = (255, 255, 100) if selected else (200, 200, 200)
                    border_alpha = 255 if selected else 128
                    
                    # Draw border lines
                    pygame.draw.line(surface, border_color, (x, y), (x + self.SLOT_SIZE, y), 2)  # Top
                    pygame.draw.line(surface, border_color, (x, y + self.SLOT_SIZE), (x + self.SLOT_SIZE, y + self.SLOT_SIZE), 2)  # Bottom
                    pygame.draw.line(surface, border_color, (x, y), (x, y + self.SLOT_SIZE), 2)  # Left
                    pygame.draw.line(surface, border_color, (x + self.SLOT_SIZE, y), (x + self.SLOT_SIZE, y + self.SLOT_SIZE), 2)  # Right
                
                # Draw the slot with border
                draw_slot_border(x, y, index, self.selected_item_index == index)
                
                # Draw item if present
                if index < len(inventory.items):
                    item = inventory.items[index]
                    # Get sprite name based on type
                    item_sprite_map = {
                        ItemType.WEAPON: "sword",
                        ItemType.RANGED_WEAPON: "bow",
                        ItemType.AMMUNITION: "arrow",
                        ItemType.POTION: "classic_roguelike_134",  # Base potion sprite
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
                            # Scale and center item sprite in slot
                            scaled_item = pygame.transform.scale(item_sprite, (self.SLOT_SIZE - 8, self.SLOT_SIZE - 8))
                            item_rect = scaled_item.get_rect(center=(x + self.SLOT_SIZE // 2, y + self.SLOT_SIZE // 2))
                            surface.blit(scaled_item, item_rect)
                    
                    # Draw item name below sprite
                    item_surface = self.small_font.render_text(item.name[:6].upper(), self.TEXT_COLOR)
                    text_rect = item_surface.get_rect(center=(x + self.SLOT_SIZE // 2, y + self.SLOT_SIZE + 5))
                    surface.blit(item_surface, text_rect)
                    
                    # Draw stack count for stackable items
                    if item.item_type.is_stackable():
                        count_surface = self.small_font.render_text(str(item.stack_size), self.TEXT_COLOR)
                        count_rect = count_surface.get_rect(bottomright=(x + self.SLOT_SIZE - 2, y + self.SLOT_SIZE - 2))
                        # Draw black outline for better visibility
                        for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                            outline_rect = count_rect.copy()
                            outline_rect.x += dx
                            outline_rect.y += dy
                            outline_surface = self.small_font.render_text(str(item.stack_size), (0, 0, 0))
                            surface.blit(outline_surface, outline_rect)
                        surface.blit(count_surface, count_rect)
    
    def _render_instructions(self, surface: pygame.Surface):
        """Render control instructions."""
        instructions = [
            "Left Click: Select/Equip item",
            "Right Click: Unequip item", 
            "Hover: View item details",
            "ESC/I: Close inventory"
        ]
        
        # Calculate frame dimensions
        frame_x = 50
        frame_y = self.PANEL_HEIGHT - 120
        frame_width = self.PANEL_WIDTH - 100
        frame_height = 110
        
        # Draw frame background
        background = self.sprite_manager.sprite_system.get_sprite("interface_background")
        if background:
            scaled_background = pygame.transform.scale(background, (32, 32))
            for y in range(frame_y + 16, frame_y + frame_height - 16, 32):
                for x in range(frame_x + 16, frame_x + frame_width - 16, 32):
                    surface.blit(scaled_background, (x, y))
        
        # Draw frame borders (ornate style)
        frame_top = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_top")
        frame_bottom = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_bottom")
        frame_left = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_left")
        frame_right = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_right")
        frame_corner_tl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tl")
        frame_corner_tr = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tr")
        frame_corner_bl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_bl")
        frame_corner_br = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_br")
        
        if all([frame_top, frame_bottom, frame_left, frame_right,
               frame_corner_tl, frame_corner_tr, frame_corner_bl, frame_corner_br]):
            # Scale frame elements to appropriate sizes
            corner_size = 16
            frame_top_scaled = pygame.transform.scale(frame_top, (32, 16))
            frame_bottom_scaled = pygame.transform.scale(frame_bottom, (32, 16))
            frame_left_scaled = pygame.transform.scale(frame_left, (16, 32))
            frame_right_scaled = pygame.transform.scale(frame_right, (16, 32))
            corner_tl_scaled = pygame.transform.scale(frame_corner_tl, (corner_size, corner_size))
            corner_tr_scaled = pygame.transform.scale(frame_corner_tr, (corner_size, corner_size))
            corner_bl_scaled = pygame.transform.scale(frame_corner_bl, (corner_size, corner_size))
            corner_br_scaled = pygame.transform.scale(frame_corner_br, (corner_size, corner_size))
            
            # Draw corners
            surface.blit(corner_tl_scaled, (frame_x, frame_y))
            surface.blit(corner_tr_scaled, (frame_x + frame_width - corner_size, frame_y))
            surface.blit(corner_bl_scaled, (frame_x, frame_y + frame_height - corner_size))
            surface.blit(corner_br_scaled, (frame_x + frame_width - corner_size, frame_y + frame_height - corner_size))
            
            # Draw top and bottom edges
            for x in range(frame_x + corner_size, frame_x + frame_width - corner_size, 32):
                surface.blit(frame_top_scaled, (x, frame_y))
                surface.blit(frame_bottom_scaled, (x, frame_y + frame_height - 16))
            
            # Draw left and right edges
            for y in range(frame_y + corner_size, frame_y + frame_height - corner_size, 32):
                surface.blit(frame_left_scaled, (frame_x, y))
                surface.blit(frame_right_scaled, (frame_x + frame_width - 16, y))
        
        # Center instructions at bottom with more space
        y_start = frame_y + 20
        for i, instruction in enumerate(instructions):
            text_surface = self.text_font.render_text(instruction.upper(), (200, 200, 200))
            text_rect = text_surface.get_rect(centerx=frame_x + frame_width // 2, top=y_start + i * 20)
            surface.blit(text_surface, text_rect)
    
    def _render_tooltip(self, screen: pygame.Surface, item: Item, position: Tuple[int, int]):
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
        
        # Render each line to calculate max width
        rendered_lines = []
        max_width = 0
        total_height = 0
        line_spacing = 20  # Increased spacing for sprite font
        
        for line in lines:
            if line.strip():  # Skip empty lines
                text_surface = self.small_font.render_text(line, self.TOOLTIP_COLOR)
                rendered_lines.append(text_surface)
                max_width = max(max_width, text_surface.get_width())
                total_height += line_spacing
            else:
                rendered_lines.append(None)
                total_height += line_spacing // 2  # Half spacing for empty lines
        
        # Calculate tooltip dimensions
        tooltip_width = max_width + 20
        tooltip_height = total_height + 20
        
        # Position tooltip
        tooltip_x = min(position[0] + 10, self.screen_width - tooltip_width)
        tooltip_y = min(position[1] - tooltip_height - 10, self.screen_height - tooltip_height)
        
        # Create tooltip surface
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        
        # Draw tooltip background
        background = self.sprite_manager.sprite_system.get_sprite("interface_background")
        if background:
            scaled_background = pygame.transform.scale(background, (32, 32))
            for y in range(0, tooltip_height, 32):
                for x in range(0, tooltip_width, 32):
                    tooltip_surface.blit(scaled_background, (x, y))
        
        # Draw tooltip frame (ornate style)
        frame_top = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_top")
        frame_bottom = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_bottom")
        frame_left = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_left")
        frame_right = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_right")
        frame_corner_tl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tl")
        frame_corner_tr = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_tr")
        frame_corner_bl = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_bl")
        frame_corner_br = self.sprite_manager.sprite_system.get_sprite("interface_ornate_frame_corner_br")
        
        if all([frame_top, frame_bottom, frame_left, frame_right,
               frame_corner_tl, frame_corner_tr, frame_corner_bl, frame_corner_br]):
            # Scale frame elements to appropriate sizes
            corner_size = 16
            frame_top_scaled = pygame.transform.scale(frame_top, (32, 16))
            frame_bottom_scaled = pygame.transform.scale(frame_bottom, (32, 16))
            frame_left_scaled = pygame.transform.scale(frame_left, (16, 32))
            frame_right_scaled = pygame.transform.scale(frame_right, (16, 32))
            corner_tl_scaled = pygame.transform.scale(frame_corner_tl, (corner_size, corner_size))
            corner_tr_scaled = pygame.transform.scale(frame_corner_tr, (corner_size, corner_size))
            corner_bl_scaled = pygame.transform.scale(frame_corner_bl, (corner_size, corner_size))
            corner_br_scaled = pygame.transform.scale(frame_corner_br, (corner_size, corner_size))
            
            # Draw corners
            tooltip_surface.blit(corner_tl_scaled, (0, 0))
            tooltip_surface.blit(corner_tr_scaled, (tooltip_width - corner_size, 0))
            tooltip_surface.blit(corner_bl_scaled, (0, tooltip_height - corner_size))
            tooltip_surface.blit(corner_br_scaled, (tooltip_width - corner_size, tooltip_height - corner_size))
            
            # Draw top and bottom edges
            for x in range(corner_size, tooltip_width - corner_size, 32):
                tooltip_surface.blit(frame_top_scaled, (x, 0))
                tooltip_surface.blit(frame_bottom_scaled, (x, tooltip_height - 16))
            
            # Draw left and right edges
            for y in range(corner_size, tooltip_height - corner_size, 32):
                tooltip_surface.blit(frame_left_scaled, (0, y))
                tooltip_surface.blit(frame_right_scaled, (tooltip_width - 16, y))
        
        # Draw tooltip text
        y_offset = 10
        for surface in rendered_lines:
            if surface:  # Skip None (empty lines)
                tooltip_surface.blit(surface, (10, y_offset))
                y_offset += line_spacing
            else:
                y_offset += line_spacing // 2
        
        screen.blit(tooltip_surface, (tooltip_x, tooltip_y))
    
    def _get_equipment_slot_at_position(self, pos: Tuple[int, int]) -> Optional[EquipmentSlot]:
        """Get equipment slot at mouse position."""
        x, y = pos
        for slot, (slot_x, slot_y) in self.equipment_slots_layout.items():
            if (slot_x <= x <= slot_x + self.SLOT_SIZE and 
                slot_y <= y <= slot_y + self.SLOT_SIZE):
                return slot
        return None
    
    def _get_inventory_slot_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """Get inventory slot index at mouse position."""
        x, y = pos
        
        # Check if within inventory area
        if (x < self.INVENTORY_START_X or 
            y < self.INVENTORY_START_Y or 
            x > self.INVENTORY_START_X + self.INVENTORY_COLS * self.SLOT_SPACING or
            y > self.INVENTORY_START_Y + self.INVENTORY_ROWS * self.SLOT_SPACING):
            return None
        
        col = (x - self.INVENTORY_START_X) // self.SLOT_SPACING
        row = (y - self.INVENTORY_START_Y) // self.SLOT_SPACING
        
        if 0 <= col < self.INVENTORY_COLS and 0 <= row < self.INVENTORY_ROWS:
            return row * self.INVENTORY_COLS + col
        
        return None
    
    def _handle_equipment_slot_click(self, slot: EquipmentSlot, character, inventory: Inventory) -> str:
        """Handle clicking on an equipment slot."""
        equipped_item = character.equipment.get_equipped_item(slot)
        
        if equipped_item:
            # Unequip item to inventory
            if inventory.is_full():
                return "Inventory is full! Cannot unequip item."
            
            unequipped_item = character.unequip_item(slot)
            if unequipped_item:
                inventory.add_item(unequipped_item)
                return f"Unequipped {unequipped_item.name}"
        
        # If we have a selected inventory item, try to equip it
        if self.selected_item_index is not None and self.selected_item_index < len(inventory.items):
            item = inventory.items[self.selected_item_index]
            if item.can_equip_to_slot(slot):
                # Remove from inventory and equip
                inventory.remove_item_at_index(self.selected_item_index)
                character.equip_item(item, slot)
                self.selected_item_index = None
                return f"Equipped {item.name}"
            else:
                return f"Cannot equip {item.name} to {slot.value}"
        
        return "No item selected or slot empty"
    
    def _handle_inventory_slot_click(self, index: int, character, inventory: Inventory) -> str:
        """Handle clicking on an inventory slot."""
        if index >= len(inventory.items):
            return "Empty slot"
        
        item = inventory.items[index]
        
        # If it's a potion, use it
        if item.item_type == ItemType.POTION:
            # Remove one potion from stack
            inventory.remove_item(item, 1)
            # Heal the player
            old_hp = character.current_hp
            heal_amount = random.randint(5, 15)  # Random healing amount
            character.heal(heal_amount)
            actual_heal = character.current_hp - old_hp
            return f"Used Health Potion - Healed {actual_heal} HP"
            
        # If item already selected, try to auto-equip
        if self.selected_item_index == index:
            # Find appropriate slot for item
            suitable_slots = [slot for slot in EquipmentSlot if item.can_equip_to_slot(slot)]
            
            for slot in suitable_slots:
                if character.equipment.get_equipped_item(slot) is None:
                    # Empty slot found, equip item
                    inventory.remove_item_at_index(index)
                    character.equip_item(item, slot)
                    self.selected_item_index = None
                    return f"Equipped {item.name}"
            
            # No empty slots, ask to replace
            if suitable_slots:
                return f"All suitable slots occupied. Click {suitable_slots[0].value} slot to replace."
        
        # Select this item
        self.selected_item_index = index
        return f"Selected {item.name}"
    
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
    
    def _get_item_type_color(self, item_type: ItemType) -> Tuple[int, int, int]:
        """Get color indicator for item type."""
        colors = {
            ItemType.WEAPON: (255, 100, 100),    # Red
            ItemType.ARMOUR: (100, 100, 255),    # Blue
            ItemType.HELMET: (100, 255, 100),    # Green
            ItemType.BOOTS: (255, 255, 100),     # Yellow
            ItemType.RING: (255, 100, 255),      # Magenta
            ItemType.AMULET: (100, 255, 255)     # Cyan
        }
        return colors.get(item_type, (200, 200, 200)) 