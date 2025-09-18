#!/usr/bin/env python3
"""
Town Editor for Treasure Goblin
A visual tool for creating and editing town layouts
"""

import pygame
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum

# Import game systems
from system import GameSpriteManager

# Import CellType from main
try:
    from main import CellType
except ImportError:
    # Define CellType locally if main module not available
    from enum import Enum
    class CellType(Enum):
        WALL = 0
        FLOOR = 1
        DOOR = 2
        STAIRCASE = 3
        CHEST = 4
        HP_PICKUP = 5
        TOWN_FLOOR = 6
        TOWN_WALL = 7
        TOWN_DOOR = 8
        TOWN_BUILDING = 9
        DUNGEON_ENTRANCE = 10

class EditorMode(Enum):
    TILE_PLACE = "tile_place"
    SPRITE_PAINT = "sprite_paint"
    NPC_PLACE = "npc_place"
    PLAY = "play"

class TownEditor:
    def __init__(self):
        pygame.init()
        
        # Screen setup
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Treasure Goblin Town Editor")
        
        # Game systems
        self.sprite_manager = GameSpriteManager()
        assets_path = Path("assets")
        self.sprite_manager.load_game_assets(assets_path)
        
        # Editor state
        self.tile_size = 24
        self.grid_width = 40
        self.grid_height = 30
        self.camera_x = 0
        self.camera_y = 0
        
        # Town data
        self.town_data = {
            "width": self.grid_width,
            "height": self.grid_height,
            "tiles": {},
            "npcs": [],
            "painted_sprites": {}
        }
        
        # Editor state
        self.current_mode = EditorMode.SPRITE_PAINT
        self.selected_tile = CellType.TOWN_FLOOR
        self.selected_sprite = "small grass"  # Default sprite
        self.selected_npc_type = "shopkeeper"
        self.is_dragging = False
        self.drag_start = None
        
        # Sprite picker
        self.sprite_picker_open = False
        self.sprite_picker_scroll = 0
        self.available_sprites = list(self.sprite_manager.sprite_system.list_sprites())
        self.sprites_per_row = 8
        self.sprite_picker_rect = pygame.Rect(50, 50, 600, 400)
        
        # UI
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Available tiles for editing
        self.available_tiles = [
            CellType.TOWN_FLOOR,
            CellType.TOWN_WALL,
            CellType.TOWN_DOOR,
            CellType.TOWN_BUILDING,
            CellType.DUNGEON_ENTRANCE,
            CellType.CHEST,
            CellType.HP_PICKUP
        ]
        
        # Sprite painting data
        self.painted_sprites = {}  # (x, y) -> sprite_name
        
        # Available NPCs
        self.available_npcs = [
            "shopkeeper",
            "innkeeper", 
            "blacksmith",
            "priest"
        ]
        
        # Initialize empty town
        self._initialize_empty_town()
        
    def _initialize_empty_town(self):
        """Initialize an empty town grid"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                self.town_data["tiles"][f"{x},{y}"] = CellType.TOWN_FLOOR.value
        
    def run(self):
        """Main editor loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            dt = clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_down(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self._handle_mouse_up(event)
                elif event.type == pygame.MOUSEMOTION:
                    self._handle_mouse_motion(event)
            
            self._update(dt)
            self._render()
            pygame.display.flip()
        
        pygame.quit()
    
    def _handle_keydown(self, event):
        """Handle keyboard input"""
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
        elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
            self._save_town()
        elif event.key == pygame.K_o and pygame.key.get_pressed()[pygame.K_LCTRL]:
            self._load_town()
        elif event.key == pygame.K_n and pygame.key.get_pressed()[pygame.K_LCTRL]:
            self._new_town()
        elif event.key == pygame.K_TAB:
            self._cycle_mode()
        elif event.key == pygame.K_1:
            self.current_mode = EditorMode.TILE_PLACE
        elif event.key == pygame.K_2:
            self.current_mode = EditorMode.SPRITE_PAINT
        elif event.key == pygame.K_3:
            self.current_mode = EditorMode.NPC_PLACE
        elif event.key == pygame.K_4:
            self.current_mode = EditorMode.PLAY
        elif event.key == pygame.K_p:
            self.sprite_picker_open = not self.sprite_picker_open
        elif event.key == pygame.K_r:
            self._rotate_selection()
        elif event.key == pygame.K_DELETE:
            self._delete_selected()
    
    def _handle_mouse_down(self, event):
        """Handle mouse button press"""
        if event.button == 1:  # Left click
            self.is_dragging = True
            self.drag_start = event.pos
            self._handle_click(event.pos)
        elif event.button == 3:  # Right click
            self._handle_right_click(event.pos)
    
    def _handle_mouse_up(self, event):
        """Handle mouse button release"""
        if event.button == 1:  # Left click
            self.is_dragging = False
            self.drag_start = None
    
    def _handle_mouse_motion(self, event):
        """Handle mouse movement"""
        if self.is_dragging and self.drag_start:
            self._handle_click(event.pos)
    
    def _handle_click(self, pos):
        """Handle click at position"""
        # Check if clicking in sprite picker
        if self.sprite_picker_open and self.sprite_picker_rect.collidepoint(pos):
            self._handle_sprite_picker_click(pos)
            return
            
        grid_x, grid_y = self._screen_to_grid(pos)
        if self._is_valid_position(grid_x, grid_y):
            if self.current_mode == EditorMode.TILE_PLACE:
                self._place_tile(grid_x, grid_y)
            elif self.current_mode == EditorMode.SPRITE_PAINT:
                self._paint_sprite(grid_x, grid_y)
            elif self.current_mode == EditorMode.NPC_PLACE:
                self._place_npc(grid_x, grid_y)
    
    def _handle_right_click(self, pos):
        """Handle right click"""
        grid_x, grid_y = self._screen_to_grid(pos)
        if self._is_valid_position(grid_x, grid_y):
            if self.current_mode == EditorMode.TILE_PLACE:
                self._remove_tile(grid_x, grid_y)
            elif self.current_mode == EditorMode.SPRITE_PAINT:
                self._remove_sprite(grid_x, grid_y)
            elif self.current_mode == EditorMode.NPC_PLACE:
                self._remove_npc(grid_x, grid_y)
    
    def _screen_to_grid(self, pos):
        """Convert screen coordinates to grid coordinates"""
        screen_x, screen_y = pos
        grid_x = (screen_x + self.camera_x) // self.tile_size
        grid_y = (screen_y + self.camera_y) // self.tile_size
        return grid_x, grid_y
    
    def _is_valid_position(self, x, y):
        """Check if position is within grid bounds"""
        return 0 <= x < self.grid_width and 0 <= y < self.grid_height
    
    def _place_tile(self, x, y):
        """Place a tile at the given position"""
        key = f"{x},{y}"
        self.town_data["tiles"][key] = self.selected_tile.value
    
    def _remove_tile(self, x, y):
        """Remove tile at position (set to floor)"""
        key = f"{x},{y}"
        self.town_data["tiles"][key] = CellType.TOWN_FLOOR.value
    
    def _paint_sprite(self, x, y):
        """Paint a sprite at the given position"""
        self.painted_sprites[(x, y)] = self.selected_sprite
    
    def _remove_sprite(self, x, y):
        """Remove sprite at position"""
        if (x, y) in self.painted_sprites:
            del self.painted_sprites[(x, y)]
    
    def _handle_sprite_picker_click(self, pos):
        """Handle click in sprite picker"""
        # Calculate which sprite was clicked
        relative_x = pos[0] - self.sprite_picker_rect.x
        relative_y = pos[1] - self.sprite_picker_rect.y
        
        # Account for scroll
        relative_y += self.sprite_picker_scroll
        
        sprite_size = 32
        col = relative_x // sprite_size
        row = relative_y // sprite_size
        
        sprite_index = row * self.sprites_per_row + col
        
        if 0 <= sprite_index < len(self.available_sprites):
            self.selected_sprite = self.available_sprites[sprite_index]
            self.sprite_picker_open = False
    
    def _place_npc(self, x, y):
        """Place an NPC at the given position"""
        # Remove any existing NPC at this position
        self._remove_npc(x, y)
        
        # Add new NPC
        npc = {
            "x": x,
            "y": y,
            "type": self.selected_npc_type
        }
        self.town_data["npcs"].append(npc)
    
    def _remove_npc(self, x, y):
        """Remove NPC at position"""
        self.town_data["npcs"] = [npc for npc in self.town_data["npcs"] 
                                 if not (npc["x"] == x and npc["y"] == y)]
    
    def _cycle_mode(self):
        """Cycle through editor modes"""
        modes = list(EditorMode)
        current_index = modes.index(self.current_mode)
        next_index = (current_index + 1) % len(modes)
        self.current_mode = modes[next_index]
    
    def _rotate_selection(self):
        """Rotate through available tiles/NPCs"""
        if self.current_mode == EditorMode.TILE_PLACE:
            current_index = self.available_tiles.index(self.selected_tile)
            next_index = (current_index + 1) % len(self.available_tiles)
            self.selected_tile = self.available_tiles[next_index]
        elif self.current_mode == EditorMode.NPC_PLACE:
            current_index = self.available_npcs.index(self.selected_npc_type)
            next_index = (current_index + 1) % len(self.available_npcs)
            self.selected_npc_type = self.available_npcs[next_index]
    
    def _delete_selected(self):
        """Delete selected tiles/NPCs"""
        # This could be expanded to support multi-select
        pass
    
    def _save_town(self):
        """Save town to file"""
        # Update town data with current painted sprites
        self.town_data["painted_sprites"] = {f"{x},{y}": sprite for (x, y), sprite in self.painted_sprites.items()}
        
        filename = "saved_town.json"
        with open(filename, 'w') as f:
            json.dump(self.town_data, f, indent=2)
        print(f"Town saved to {filename}")
    
    def _load_town(self):
        """Load town from file"""
        filename = "saved_town.json"
        if Path(filename).exists():
            with open(filename, 'r') as f:
                self.town_data = json.load(f)
            
            # Load painted sprites
            self.painted_sprites = {}
            for key, sprite in self.town_data.get("painted_sprites", {}).items():
                x, y = map(int, key.split(','))
                self.painted_sprites[(x, y)] = sprite
            
            print(f"Town loaded from {filename}")
        else:
            print(f"File {filename} not found")
    
    def _new_town(self):
        """Create a new empty town"""
        self.town_data = {
            "width": self.grid_width,
            "height": self.grid_height,
            "tiles": {},
            "npcs": []
        }
        self._initialize_empty_town()
        print("New town created")
    
    def _update(self, dt):
        """Update editor state"""
        keys = pygame.key.get_pressed()
        
        # Camera movement
        move_speed = 200 * dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.camera_x -= move_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.camera_x += move_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.camera_y -= move_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.camera_y += move_speed
    
    def _render(self):
        """Render the editor"""
        self.screen.fill((50, 50, 50))
        
        # Render grid
        self._render_grid()
        
        # Render tiles
        self._render_tiles()
        
        # Render painted sprites
        self._render_painted_sprites()
        
        # Render NPCs
        self._render_npcs()
        
        # Render sprite picker
        if self.sprite_picker_open:
            self._render_sprite_picker()
        
        # Render UI
        self._render_ui()
    
    def _render_grid(self):
        """Render the grid lines"""
        # Vertical lines
        for x in range(0, self.screen_width + self.tile_size, self.tile_size):
            screen_x = x - (self.camera_x % self.tile_size)
            if 0 <= screen_x <= self.screen_width:
                pygame.draw.line(self.screen, (100, 100, 100), 
                               (screen_x, 0), (screen_x, self.screen_height))
        
        # Horizontal lines
        for y in range(0, self.screen_height + self.tile_size, self.tile_size):
            screen_y = y - (self.camera_y % self.tile_size)
            if 0 <= screen_y <= self.screen_height:
                pygame.draw.line(self.screen, (100, 100, 100), 
                               (0, screen_y), (self.screen_width, screen_y))
    
    def _render_tiles(self):
        """Render all tiles"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                key = f"{x},{y}"
                if key in self.town_data["tiles"]:
                    cell_type = CellType(self.town_data["tiles"][key])
                    self._render_tile(cell_type, x, y)
    
    def _render_tile(self, cell_type, grid_x, grid_y):
        """Render a single tile"""
        screen_x = grid_x * self.tile_size - self.camera_x
        screen_y = grid_y * self.tile_size - self.camera_y
        
        # Only render if visible
        if (screen_x >= -self.tile_size and screen_x < self.screen_width + self.tile_size and
            screen_y >= -self.tile_size and screen_y < self.screen_height + self.tile_size):
            
            # Try to use sprite
            sprite_name = self._get_cell_sprite(cell_type)
            if sprite_name and self.sprite_manager.sprite_system.get_sprite(sprite_name):
                # Center the 16x24 sprite in the 24x24 tile
                offset_x = (self.tile_size - 16) // 2
                offset_y = (self.tile_size - 24) // 2
                self.sprite_manager.sprite_system.draw_sprite(
                    self.screen, sprite_name, screen_x + offset_x, screen_y + offset_y, 
                    scale=1, prevent_overlap=False
                )
            else:
                # Fallback to color
                color = self._get_cell_color(cell_type)
                pygame.draw.rect(self.screen, color, 
                               (screen_x, screen_y, self.tile_size, self.tile_size))
    
    def _render_npcs(self):
        """Render all NPCs"""
        for npc in self.town_data["npcs"]:
            self._render_npc(npc["x"], npc["y"], npc["type"])
    
    def _render_npc(self, grid_x, grid_y, npc_type):
        """Render a single NPC"""
        screen_x = grid_x * self.tile_size - self.camera_x
        screen_y = grid_y * self.tile_size - self.camera_y
        
        # Only render if visible
        if (screen_x >= -self.tile_size and screen_x < self.screen_width + self.tile_size and
            screen_y >= -self.tile_size and screen_y < self.screen_height + self.tile_size):
            
            # Try to use sprite
            sprite_name = self._get_npc_sprite(npc_type)
            if sprite_name and self.sprite_manager.sprite_system.get_sprite(sprite_name):
                # Center the 16x24 sprite in the 24x24 tile
                offset_x = (self.tile_size - 16) // 2
                offset_y = (self.tile_size - 24) // 2
                self.sprite_manager.sprite_system.draw_sprite(
                    self.screen, sprite_name, screen_x + offset_x, screen_y + offset_y, 
                    scale=1, prevent_overlap=False
                )
            else:
                # Fallback to colored circle
                center_x = screen_x + self.tile_size // 2
                center_y = screen_y + self.tile_size // 2
                pygame.draw.circle(self.screen, (255, 255, 100), (center_x, center_y), self.tile_size // 4)
    
    def _render_ui(self):
        """Render the user interface"""
        # Mode indicator
        mode_text = f"Mode: {self.current_mode.value}"
        mode_surface = self.font.render(mode_text, True, (255, 255, 255))
        self.screen.blit(mode_surface, (10, 10))
        
        # Selection indicator
        if self.current_mode == EditorMode.TILE_PLACE:
            selection_text = f"Selected: {self.selected_tile.name}"
        elif self.current_mode == EditorMode.SPRITE_PAINT:
            selection_text = f"Selected Sprite: {self.selected_sprite}"
        elif self.current_mode == EditorMode.NPC_PLACE:
            selection_text = f"Selected: {self.selected_npc_type}"
        else:
            selection_text = "Play Mode"
        
        selection_surface = self.font.render(selection_text, True, (255, 255, 255))
        self.screen.blit(selection_surface, (10, 40))
        
        # Instructions
        instructions = [
            "Controls:",
            "1: Tile Mode | 2: Sprite Paint | 3: NPC Mode | 4: Play",
            "P: Open/Close Sprite Picker",
            "R: Rotate selection",
            "Tab: Cycle modes",
            "Ctrl+S: Save | Ctrl+O: Load | Ctrl+N: New",
            "Left Click: Place | Right Click: Remove",
            "WASD/Arrows: Move camera"
        ]
        
        y_offset = 80
        for instruction in instructions:
            text_surface = self.small_font.render(instruction, True, (200, 200, 200))
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 20
    
    def _get_cell_sprite(self, cell_type):
        """Get sprite name for a cell type"""
        sprite_mapping = {
            CellType.TOWN_FLOOR: "small grass",
            CellType.TOWN_WALL: "Wall",
            CellType.TOWN_DOOR: "window",
            CellType.TOWN_BUILDING: "Wall",
            CellType.DUNGEON_ENTRANCE: "stairs down",
            CellType.CHEST: "prison gate",
            CellType.HP_PICKUP: "bubbles 1",
        }
        return sprite_mapping.get(cell_type)
    
    def _get_cell_color(self, cell_type):
        """Get color for a cell type (fallback)"""
        colors = {
            CellType.TOWN_FLOOR: (100, 150, 100),
            CellType.TOWN_WALL: (150, 100, 100),
            CellType.TOWN_DOOR: (200, 150, 100),
            CellType.TOWN_BUILDING: (120, 80, 80),
            CellType.DUNGEON_ENTRANCE: (100, 100, 200),
            CellType.CHEST: (150, 100, 50),
            CellType.HP_PICKUP: (200, 50, 50),
        }
        return colors.get(cell_type, (100, 100, 100))
    
    def _get_npc_sprite(self, npc_type):
        """Get NPC sprite based on type"""
        npc_sprites = {
            "shopkeeper": "big grass",
            "innkeeper": "grass flowers", 
            "blacksmith": "shrub",
            "priest": "lily pad 2"
        }
        return npc_sprites.get(npc_type, "big grass")
    
    def _render_painted_sprites(self):
        """Render all painted sprites"""
        for (grid_x, grid_y), sprite_name in self.painted_sprites.items():
            self._render_painted_sprite(grid_x, grid_y, sprite_name)
    
    def _render_painted_sprite(self, grid_x, grid_y, sprite_name):
        """Render a single painted sprite"""
        screen_x = grid_x * self.tile_size - self.camera_x
        screen_y = grid_y * self.tile_size - self.camera_y
        
        # Only render if visible
        if (screen_x >= -self.tile_size and screen_x < self.screen_width + self.tile_size and
            screen_y >= -self.tile_size and screen_y < self.screen_height + self.tile_size):
            
            if self.sprite_manager.sprite_system.get_sprite(sprite_name):
                # Center the 16x24 sprite in the 24x24 tile
                offset_x = (self.tile_size - 16) // 2
                offset_y = (self.tile_size - 24) // 2
                self.sprite_manager.sprite_system.draw_sprite(
                    self.screen, sprite_name, screen_x + offset_x, screen_y + offset_y, 
                    scale=1, prevent_overlap=False
                )
    
    def _render_sprite_picker(self):
        """Render the sprite picker UI"""
        # Draw background
        pygame.draw.rect(self.screen, (30, 30, 30), self.sprite_picker_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), self.sprite_picker_rect, 2)
        
        # Draw sprites
        sprite_size = 32
        start_y = self.sprite_picker_rect.y - self.sprite_picker_scroll
        
        for i, sprite_name in enumerate(self.available_sprites):
            row = i // self.sprites_per_row
            col = i % self.sprites_per_row
            
            x = self.sprite_picker_rect.x + col * sprite_size
            y = start_y + row * sprite_size
            
            # Only draw if visible
            if (y >= self.sprite_picker_rect.y - sprite_size and 
                y <= self.sprite_picker_rect.bottom):
                
                # Draw sprite
                if self.sprite_manager.sprite_system.get_sprite(sprite_name):
                    sprite_rect = pygame.Rect(x + 8, y + 4, 16, 24)
                    self.sprite_manager.sprite_system.draw_sprite(
                        self.screen, sprite_name, x + 8, y + 4, 
                        scale=1, prevent_overlap=False
                    )
                
                # Draw border
                pygame.draw.rect(self.screen, (150, 150, 150), 
                               (x, y, sprite_size, sprite_size), 1)
                
                # Highlight selected sprite
                if sprite_name == self.selected_sprite:
                    pygame.draw.rect(self.screen, (255, 255, 0), 
                                   (x, y, sprite_size, sprite_size), 3)
        
        # Draw scrollbar
        total_height = ((len(self.available_sprites) - 1) // self.sprites_per_row + 1) * sprite_size
        if total_height > self.sprite_picker_rect.height:
            scrollbar_height = int(self.sprite_picker_rect.height * self.sprite_picker_rect.height / total_height)
            scrollbar_y = self.sprite_picker_rect.y + int(self.sprite_picker_scroll * self.sprite_picker_rect.height / total_height)
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (self.sprite_picker_rect.right - 10, scrollbar_y, 8, scrollbar_height))

def main():
    """Main function"""
    editor = TownEditor()
    editor.run()

if __name__ == "__main__":
    main()
