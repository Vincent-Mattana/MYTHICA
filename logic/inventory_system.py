"""
Inventory System for Mythica
Manages character inventory, interactive character screen, and item management.
"""

import pygame
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
from .character_system import Item, EquipmentSlot, ItemType
from . import sprite_manager, SpriteType
from .sprite_font import SpriteFont


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
        Add an item to the inventory.
        
        Args:
            item: Item to add
            
        Returns:
            True if item was added, False if inventory is full
        """
        if len(self.items) >= self.max_items:
            return False
        
        self.items.append(item)
        return True
    
    def remove_item(self, item: Item) -> bool:
        """
        Remove an item from the inventory.
        
        Args:
            item: Item to remove
            
        Returns:
            True if item was removed, False if not found
        """
        if item in self.items:
            self.items.remove(item)
            return True
        return False
    
    def remove_item_at_index(self, index: int) -> Optional[Item]:
        """
        Remove an item at a specific index.
        
        Args:
            index: Index of item to remove
            
        Returns:
            Removed item or None if index invalid
        """
        if 0 <= index < len(self.items):
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
    """
    
    def __init__(self, screen_width: int = 800, screen_height: int = 600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # UI Layout constants
        self.PANEL_WIDTH = 900  # Even wider panel
        self.PANEL_HEIGHT = 700  # Even taller panel
        self.PANEL_X = (screen_width - self.PANEL_WIDTH) // 2
        self.PANEL_Y = (screen_height - self.PANEL_HEIGHT) // 2
        
        # Equipment slots layout (visual positions)
        # Completely reorganized equipment slots
        slot_base_x = 80  # Left margin for equipment section
        self.equipment_slots_layout = {
            # Center column
            EquipmentSlot.HEAD: (slot_base_x + 80, 180),     # Head at top
            EquipmentSlot.NECK: (slot_base_x + 80, 260),     # Neck below head
            EquipmentSlot.TORSO: (slot_base_x + 80, 340),    # Torso in middle
            EquipmentSlot.LEGS: (slot_base_x + 80, 420),     # Legs at bottom
            # Left column
            EquipmentSlot.WEAPON_1: (slot_base_x, 340),      # Left weapon
            EquipmentSlot.RING_1: (slot_base_x, 420),        # Left ring
            # Right column
            EquipmentSlot.WEAPON_2: (slot_base_x + 160, 340), # Right weapon
            EquipmentSlot.RING_2: (slot_base_x + 160, 420),   # Right ring
        }
        
        # Inventory grid layout
        self.INVENTORY_START_X = 450  # Much more space between equipment and inventory
        self.INVENTORY_START_Y = 180  # Start lower to align with equipment
        self.SLOT_SIZE = 50  # Slightly larger slots
        self.SLOT_SPACING = 70  # Much more space between slots
        self.INVENTORY_COLS = 6
        self.INVENTORY_ROWS = 7  # Reduced rows to prevent overflow
        
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
        
        # Draw main panel
        panel_surface = pygame.Surface((self.PANEL_WIDTH, self.PANEL_HEIGHT))
        panel_surface.fill(self.PANEL_COLOR)
        pygame.draw.rect(panel_surface, self.BORDER_COLOR, 
                        (0, 0, self.PANEL_WIDTH, self.PANEL_HEIGHT), 2)
        
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
        # Equipment section header with line
        pygame.draw.line(surface, self.BORDER_COLOR, 
                        (50, 170), (350, 170), 1)
        title_surface = self.header_font.render_text("EQUIPMENT", self.TEXT_COLOR)
        title_rect = title_surface.get_rect(centerx=200, top=180)
        surface.blit(title_surface, title_rect)
        
        for slot, position in self.equipment_slots_layout.items():
            x, y = position
            
            # Get equipment slot sprite
            slot_sprite = sprite_manager.load_oryx_sprite("inventory_slot", SpriteType.UI)
            if slot_sprite:
                # Scale slot sprite to match slot size
                scaled_slot = pygame.transform.scale(slot_sprite, (self.SLOT_SIZE, self.SLOT_SIZE))
                
                # Tint slot if selected
                if self.selected_equipment_slot == slot:
                    tinted_slot = scaled_slot.copy()
                    tint_overlay = pygame.Surface(scaled_slot.get_size(), pygame.SRCALPHA)
                    tint_overlay.fill((100, 255, 100, 100))  # Green tint
                    tinted_slot.blit(tint_overlay, (0, 0))
                    surface.blit(tinted_slot, (x, y))
                else:
                    surface.blit(scaled_slot, (x, y))
            
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
                    item_sprite = sprite_manager.load_oryx_sprite(sprite_name, SpriteType.ITEMS)
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
        # Inventory section header with line
        pygame.draw.line(surface, self.BORDER_COLOR, 
                        (self.INVENTORY_START_X - 20, 170),
                        (self.PANEL_WIDTH - 50, 170), 1)
        
        # Inventory title and capacity on same line
        title_surface = self.header_font.render_text("INVENTORY", self.TEXT_COLOR)
        capacity_surface = self.text_font.render_text(f"{inventory.get_item_count()}/{inventory.max_items} ITEMS", self.TEXT_COLOR)
        
        # Center the combined text
        total_width = title_surface.get_width() + 20 + capacity_surface.get_width()
        center_x = self.INVENTORY_START_X + ((self.PANEL_WIDTH - self.INVENTORY_START_X) // 2)
        start_x = center_x - (total_width // 2)
        
        surface.blit(title_surface, (start_x, 180))
        surface.blit(capacity_surface, (start_x + title_surface.get_width() + 20, 182))
        
        # Draw inventory slots
        for row in range(self.INVENTORY_ROWS):
            for col in range(self.INVENTORY_COLS):
                index = row * self.INVENTORY_COLS + col
                x = self.INVENTORY_START_X + col * self.SLOT_SPACING
                y = self.INVENTORY_START_Y + row * self.SLOT_SPACING
                
                # Get inventory slot sprite
                slot_sprite = sprite_manager.load_oryx_sprite("inventory_slot", SpriteType.UI)
                if slot_sprite:
                    # Scale slot sprite to match slot size
                    scaled_slot = pygame.transform.scale(slot_sprite, (self.SLOT_SIZE, self.SLOT_SIZE))
                    
                    # Tint slot if selected
                    if self.selected_item_index == index:
                        tinted_slot = scaled_slot.copy()
                        tint_overlay = pygame.Surface(scaled_slot.get_size(), pygame.SRCALPHA)
                        tint_overlay.fill((255, 255, 0, 100))  # Yellow tint
                        tinted_slot.blit(tint_overlay, (0, 0))
                        surface.blit(tinted_slot, (x, y))
                    else:
                        surface.blit(scaled_slot, (x, y))
                
                # Draw item if present
                if index < len(inventory.items):
                    item = inventory.items[index]
                    # Get item sprite based on type
                    item_sprite_map = {
                        ItemType.WEAPON: "sword",
                        ItemType.ARMOUR: "armor_light",
                        ItemType.HELMET: "helmet",
                        ItemType.BOOTS: "boots",
                        ItemType.RING: "ring",
                        ItemType.AMULET: "amulet"
                    }
                    sprite_name = item_sprite_map.get(item.item_type)
                    if sprite_name:
                        item_sprite = sprite_manager.load_oryx_sprite(sprite_name, SpriteType.ITEMS)
                        if item_sprite:
                            # Scale and center item sprite in slot
                            scaled_item = pygame.transform.scale(item_sprite, (self.SLOT_SIZE - 8, self.SLOT_SIZE - 8))
                            item_rect = scaled_item.get_rect(center=(x + self.SLOT_SIZE // 2, y + self.SLOT_SIZE // 2))
                            surface.blit(scaled_item, item_rect)
                    
                    # Draw item name below sprite
                    item_surface = self.small_font.render_text(item.name[:6].upper(), self.TEXT_COLOR)
                    text_rect = item_surface.get_rect(center=(x + self.SLOT_SIZE // 2, y + self.SLOT_SIZE + 5))
                    surface.blit(item_surface, text_rect)
    
    def _render_instructions(self, surface: pygame.Surface):
        """Render control instructions."""
        instructions = [
            "Left Click: Select/Equip item",
            "Right Click: Unequip item", 
            "Hover: View item details",
            "ESC/I: Close inventory"
        ]
        
        # Draw a separator line
        pygame.draw.line(surface, self.BORDER_COLOR, 
                        (50, self.PANEL_HEIGHT - 120),
                        (self.PANEL_WIDTH - 50, self.PANEL_HEIGHT - 120), 1)
        
        # Center instructions at bottom with more space
        y_start = self.PANEL_HEIGHT - 90
        for i, instruction in enumerate(instructions):
            text_surface = self.text_font.render_text(instruction.upper(), (200, 200, 200))
            text_rect = text_surface.get_rect(centerx=self.PANEL_WIDTH // 2, top=y_start + i * 30)
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
        
        # Draw tooltip background
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height))
        tooltip_surface.fill((30, 30, 30))
        pygame.draw.rect(tooltip_surface, self.BORDER_COLOR, 
                        (0, 0, tooltip_width, tooltip_height), 1)
        
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