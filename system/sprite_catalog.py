import pygame
import json
from pathlib import Path
import csv
import warnings
import os

# Suppress libpng warnings about sRGB profiles
warnings.filterwarnings("ignore", ".*iCCP.*")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

class SpriteCatalog:
    def __init__(self, assets_folder=None, screen_size=(1024, 768)):
        # Suppress pygame welcome message
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
        pygame.init()
        pygame.scrap.init()
        self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
        pygame.display.set_caption("Sprite Catalog")
        
        # Colors - define these first since they're used in create_pencil_icon
        self.BACKGROUND = (30, 30, 40)
        self.BORDER = (100, 100, 120)
        self.TEXT = (200, 200, 220)
        self.HIGHLIGHT = (120, 120, 160)
        self.INPUT_BG = (50, 50, 60)
        self.BUTTON_HOVER = (140, 140, 180)
        self.BUTTON_NORMAL = (80, 80, 100)
        
        # Initialize fonts
        self.font = pygame.font.SysFont('Arial', 16)
        self.large_font = pygame.font.SysFont('Arial', 20)
        
        # Create pencil icon (for future use if needed)
        self.pencil_icon = self.create_pencil_icon()
        
        # Sprite and layout settings
        self.SPRITE_SIZE = (16, 24)
        self.CELL_PADDING = 15
        self.MIN_CELL_WIDTH = 200
        self.MIN_CELL_HEIGHT = self.SPRITE_SIZE[1] + 40
        self.CELL_WIDTH = self.MIN_CELL_WIDTH
        self.CELL_HEIGHT = self.MIN_CELL_HEIGHT
        self.COLUMNS = screen_size[0] // self.CELL_WIDTH
        
        # Tab settings
        self.TAB_HEIGHT = 40
        self.current_tab = 0
        
        # Set up assets folder and tabs
        self.assets_folder = assets_folder or self.get_default_assets_folder()
        self.tabs = self.discover_tabs()
        self.update_window_title()
        
        # Enlarged sprite settings
        self.ENLARGED_SCALE = 4
        self.enlarged_sprite = None
        self.enlarged_rect = None
        
        # Input handling
        self.selected_sprite = None
        self.input_active = False
        self.input_text = ""
        self.text_selected = False
        self.custom_names = {}
        self.hovered_sprite = None
        
        # Folder selection
        self.folder_input_active = False
        self.folder_input_text = str(self.assets_folder)
        
        self.clock = pygame.time.Clock()
        self.scroll_y = 0
        self.scroll_speed = 20
        
        # Load sprites and mappings
        self.load_custom_names()  # Load names first
        self.load_resources()
    
    def get_default_assets_folder(self):
        """Get the default assets folder path"""
        return Path(__file__).parent.parent / "assets" / "oryx_roguelike"
    
    def discover_tabs(self):
        """Discover available sprite files in the assets folder and create tabs"""
        tabs = []
        
        if not self.assets_folder.exists():
            print(f"Assets folder not found: {self.assets_folder}")
            return tabs
        
        # Priority order for important sprite files
        priority_files = [
            "Terrain.png",
            "Terrain_Objects.png", 
            "Monsters.png",
            "Items.png",
            "Interface.png"
        ]
        
        # First add priority files if they exist
        for filename in priority_files:
            png_file = self.assets_folder / filename
            if png_file.exists():
                name = filename.replace("_", " ").replace(".png", "").title()
                tabs.append({
                    "name": name,
                    "file": filename,
                    "path": png_file
                })
        
        # Then add any other PNG files not already included
        for png_file in self.assets_folder.glob("*.png"):
            if png_file.name not in priority_files:
                name = png_file.stem.replace("_", " ").title()
                tabs.append({
                    "name": name,
                    "file": png_file.name,
                    "path": png_file
                })
        
        return tabs
    
    def update_window_title(self):
        """Update the window title to show current file name"""
        if self.tabs and 0 <= self.current_tab < len(self.tabs):
            current_file = self.tabs[self.current_tab]['file']
            pygame.display.set_caption(f"Sprite Catalog - {current_file}")
        else:
            pygame.display.set_caption("Sprite Catalog")
    
    def load_folder(self, folder_path):
        """Load a new assets folder and refresh the catalog"""
        try:
            new_folder = Path(folder_path)
            if not new_folder.exists():
                print(f"Folder does not exist: {new_folder}")
                return False
            
            if not new_folder.is_dir():
                print(f"Path is not a directory: {new_folder}")
                return False
            
            # Update assets folder
            self.assets_folder = new_folder
            
            # Discover new tabs
            self.tabs = self.discover_tabs()
            
            if not self.tabs:
                print(f"No PNG files found in {new_folder}")
                return False
            
            # Reset to first tab
            self.current_tab = 0
            self.scroll_y = 0
            
            # Reload resources
            self.load_custom_names()
            self.load_resources()
            self.redraw_catalog()
            self.update_window_title()
            
            print(f"Successfully loaded folder: {new_folder}")
            print(f"Found {len(self.tabs)} tabs")
            return True
            
        except Exception as e:
            print(f"Error loading folder: {e}")
            return False
        
    def load_resources(self):
        """Load sprite sheet and mapping data"""
        if not self.tabs:
            print("No tabs available")
            return
            
        # Load sprite mappings if available
        try:
            project_root = Path(__file__).parent.parent
            mappings_file = project_root / "assets" / "sprite_mappings.json"
            if mappings_file.exists():
                with open(mappings_file) as f:
                    self.mappings = json.load(f)
            else:
                self.mappings = {}
        except Exception:
            self.mappings = {}
            
        # Load current tab's spritesheet
        current_tab = self.tabs[self.current_tab]
        if "path" in current_tab:
            spritesheet_path = current_tab["path"]
        else:
            spritesheet_path = self.assets_folder / current_tab["file"]
            
        try:
            self.spritesheet = pygame.image.load(str(spritesheet_path)).convert_alpha()
        except pygame.error as e:
            print(f"Error loading spritesheet {spritesheet_path}: {e}")
            return
        
        # Extract individual sprites in the correct order (left to right, top to bottom)
        self.sprites = []
        sheet_width = self.spritesheet.get_width()
        sheet_height = self.spritesheet.get_height()
        
        # Calculate how many sprites fit in each row and column
        sprites_per_row = sheet_width // self.SPRITE_SIZE[0]
        sprites_per_col = sheet_height // self.SPRITE_SIZE[1]
        
        # Extract sprites in the correct order
        for y in range(0, sheet_height, self.SPRITE_SIZE[1]):
            for x in range(0, sheet_width, self.SPRITE_SIZE[0]):
                sprite_surface = pygame.Surface(self.SPRITE_SIZE, pygame.SRCALPHA)
                sprite_surface.blit(self.spritesheet, (0, 0), (x, y, self.SPRITE_SIZE[0], self.SPRITE_SIZE[1]))
                
                # Calculate the index based on position in the spritesheet
                row = y // self.SPRITE_SIZE[1]
                col = x // self.SPRITE_SIZE[0]
                index = row * sprites_per_row + col
                
                self.sprites.append({
                    'surface': sprite_surface,
                    'coords': (x, y),
                    'index': index
                })
        
        # Create sprite catalog with descriptions
        self.catalog = []
        
        # For now, just show all sprites from the current sheet
        # In the future, we could add specific mappings for each tab
        current_file = self.tabs[self.current_tab]['file']
        for sprite in self.sprites:
            # Use the spritesheet index for consistent ordering
            sprite_index = sprite['index']
            # Check if we have a custom name for this sprite (including file info)
            sprite_key = (current_file, sprite['coords'][0], sprite['coords'][1], sprite_index)
            custom_name = self.custom_names.get(sprite_key, f"{self.tabs[self.current_tab]['name']}.sprite_{sprite_index}")
            
            # Skip empty sprites
            if custom_name == "[EMPTY]":
                continue
            
            self.catalog.append({
                'sprite': sprite['surface'],
                'coords': sprite['coords'],
                'name': custom_name,
                'index': sprite_index,
                'file': current_file,
                'original_name': f"{self.tabs[self.current_tab]['name']}.sprite_{sprite_index}"
            })
        
        # Sort catalog by spritesheet index to ensure correct order
        self.catalog.sort(key=lambda x: x['index'])

    def load_custom_names(self):
        """Load custom sprite names from CSV"""
        # Try to find CSV file in multiple locations
        csv_locations = [
            self.assets_folder / "sprite_names.csv",
            self.assets_folder.parent / "sprite_names.csv",
            Path("sprite_names.csv"),  # Current directory
            Path(__file__).parent / "sprite_names.csv"  # World directory
        ]
        
        for csv_path in csv_locations:
            try:
                with open(csv_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    
                    # Skip header row if it exists
                    start_index = 1 if rows and rows[0] == ['file', 'x', 'y', 'index', 'name'] else 0
                    
                    for row in rows[start_index:]:
                        if len(row) >= 5:  # file, x, y, index, name
                            file_name = row[0]
                            key = (file_name, int(row[1]), int(row[2]), int(row[3]))
                            self.custom_names[key] = row[4]
                break  # Successfully loaded, exit the loop
            except FileNotFoundError:
                continue  # Try next location

    def save_custom_names(self):
        """Save custom sprite names to CSV"""
        # Save to the first available location (prefer assets folder)
        csv_locations = [
            self.assets_folder / "sprite_names.csv",
            self.assets_folder.parent / "sprite_names.csv",
            Path("sprite_names.csv"),  # Current directory
            Path(__file__).parent / "sprite_names.csv"  # World directory
        ]
        
        # Try to save to the first writable location
        for csv_path in csv_locations:
            try:
                # Ensure parent directory exists
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write header row
                    writer.writerow(['file', 'x', 'y', 'index', 'name'])
                    for (file_name, x, y, index), name in self.custom_names.items():
                        writer.writerow([file_name, x, y, index, name])
                break  # Successfully saved, exit the loop
            except Exception as e:
                print(f"Could not save to {csv_path}: {e}")
                continue  # Try next location
    
    def create_pencil_icon(self, size=(20, 20)):
        """Create a simple pencil icon"""
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        # Draw pencil body
        points = [
            (size[0] * 0.2, size[1] * 0.8),  # Bottom left
            (size[0] * 0.8, size[1] * 0.2),  # Top right
            (size[0] * 0.7, size[1] * 0.1),  # Top
            (size[0] * 0.1, size[1] * 0.7),  # Left
        ]
        pygame.draw.polygon(surface, self.TEXT, points)
        
        # Draw pencil tip
        tip_points = [
            (size[0] * 0.85, size[1] * 0.15),  # Top
            (size[0] * 0.9, size[1] * 0.2),    # Right
            (size[0] * 0.8, size[1] * 0.25),   # Bottom
        ]
        pygame.draw.polygon(surface, (200, 180, 160), tip_points)
        
        return surface

    def draw_sprite_cell(self, surface, sprite_info, x, y):
        """Draw a single sprite cell with border and description"""
        # Draw cell background and border
        cell_rect = pygame.Rect(x, y, self.CELL_WIDTH, self.CELL_HEIGHT)
        pygame.draw.rect(surface, self.BACKGROUND, cell_rect)
        
        # Selection highlight is now drawn on screen, not here
        
        pygame.draw.rect(surface, self.BORDER, cell_rect, 1)
        
        # Draw sprite centered horizontally
        sprite_x = x + (self.CELL_WIDTH - self.SPRITE_SIZE[0]) // 2
        sprite_y = y + self.CELL_PADDING
        surface.blit(sprite_info['sprite'], (sprite_x, sprite_y))
        
        # Draw only the name in grid view
        name_text = self.font.render(sprite_info['name'], True, self.TEXT)
        
        # Center the text below the sprite
        text_y = y + self.SPRITE_SIZE[1] + self.CELL_PADDING
        text_x = x + (self.CELL_WIDTH - name_text.get_width()) // 2
        
        surface.blit(name_text, (text_x, text_y))

    def draw_enlarged_sprite(self):
        """Draw the enlarged sprite overlay with details"""
        if self.enlarged_sprite and self.enlarged_rect and self.selected_sprite:
            # Draw semi-transparent background
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            # Draw enlarged sprite
            self.screen.blit(self.enlarged_sprite, self.enlarged_rect)
            
            # Draw details below the sprite
            details_y = self.enlarged_rect.bottom + 20
            details_x = self.enlarged_rect.centerx
            
            # Sprite name
            name_text = self.large_font.render(f"Name: {self.selected_sprite['name']}", True, self.TEXT)
            name_rect = name_text.get_rect(centerx=details_x, y=details_y)
            self.screen.blit(name_text, name_rect)
            
            # File information
            file_text = self.font.render(f"File: {self.selected_sprite['file']}", True, self.TEXT)
            file_rect = file_text.get_rect(centerx=details_x, y=details_y + 30)
            self.screen.blit(file_text, file_rect)
            
            # Coordinates
            coords_text = self.font.render(f"Coords: ({self.selected_sprite['coords'][0]}, {self.selected_sprite['coords'][1]})", True, self.TEXT)
            coords_rect = coords_text.get_rect(centerx=details_x, y=details_y + 50)
            self.screen.blit(coords_text, coords_rect)
            
            # Index
            index_text = self.font.render(f"Index: {self.selected_sprite['index']}", True, self.TEXT)
            index_rect = index_text.get_rect(centerx=details_x, y=details_y + 70)
            self.screen.blit(index_text, index_rect)
            
            # Instructions
            instructions_text = self.font.render("F2: rename | DEL: mark empty | F5: refresh | F12: load folder | 1-9: switch tabs | ESC: close", True, (150, 150, 150))
            instructions_rect = instructions_text.get_rect(centerx=details_x, y=details_y + 100)
            self.screen.blit(instructions_text, instructions_rect)

    def draw_tabs(self):
        """Draw the tab bar with numbered tabs"""
        if not self.tabs:
            return
            
        tab_width = self.screen.get_width() // len(self.tabs)
        
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(i * tab_width, 0, tab_width, self.TAB_HEIGHT)
            
            # Highlight current tab
            if i == self.current_tab:
                pygame.draw.rect(self.screen, self.HIGHLIGHT, tab_rect)
            else:
                pygame.draw.rect(self.screen, self.BUTTON_NORMAL, tab_rect)
            
            # Draw tab border
            pygame.draw.rect(self.screen, self.BORDER, tab_rect, 1)
            
            # Draw tab number instead of name
            tab_number = str(i + 1)  # 1-based numbering
            text = self.font.render(tab_number, True, self.TEXT)
            text_rect = text.get_rect(center=tab_rect.center)
            self.screen.blit(text, text_rect)

    def draw_input_box(self):
        """Draw the input box for renaming sprites"""
        if self.input_active and self.selected_sprite:
            input_rect = pygame.Rect(
                self.screen.get_width() // 4,
                self.screen.get_height() // 2 - 50,
                self.screen.get_width() // 2,
                100
            )
            
            # Draw semi-transparent background
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            # Draw input box
            pygame.draw.rect(self.screen, self.INPUT_BG, input_rect)
            pygame.draw.rect(self.screen, self.BORDER, input_rect, 2)
            
            # Draw prompt
            prompt = self.font.render("Enter new name:", True, self.TEXT)
            self.screen.blit(prompt, (input_rect.x + 10, input_rect.y + 10))
            
            # Draw input text
            text_surface = self.font.render(self.input_text, True, self.TEXT)
            text_rect = text_surface.get_rect()
            text_rect.topleft = (input_rect.x + 10, input_rect.y + 40)
            
            # Draw selection background if text is selected
            if self.text_selected and self.input_text:
                selection_rect = pygame.Rect(text_rect.x, text_rect.y, text_rect.width, text_rect.height)
                pygame.draw.rect(self.screen, self.HIGHLIGHT, selection_rect)
            
            self.screen.blit(text_surface, text_rect)
    
    def draw_folder_input_box(self):
        """Draw the input box for folder selection"""
        if self.folder_input_active:
            input_rect = pygame.Rect(
                self.screen.get_width() // 4,
                self.screen.get_height() // 2 - 50,
                self.screen.get_width() // 2,
                100
            )
            
            # Draw semi-transparent background
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            # Draw input box
            pygame.draw.rect(self.screen, self.INPUT_BG, input_rect)
            pygame.draw.rect(self.screen, self.BORDER, input_rect, 2)
            
            # Draw prompt
            prompt = self.font.render("Enter folder path:", True, self.TEXT)
            self.screen.blit(prompt, (input_rect.x + 10, input_rect.y + 10))
            
            # Draw input text
            text_surface = self.font.render(self.folder_input_text, True, self.TEXT)
            text_rect = text_surface.get_rect()
            text_rect.topleft = (input_rect.x + 10, input_rect.y + 40)
            
            # Draw selection background if text is selected
            if self.text_selected and self.folder_input_text:
                selection_rect = pygame.Rect(text_rect.x, text_rect.y, text_rect.width, text_rect.height)
                pygame.draw.rect(self.screen, self.HIGHLIGHT, selection_rect)
            
            self.screen.blit(text_surface, text_rect)
            
            # Draw instructions
            instructions = self.font.render("Enter: load folder | ESC: cancel", True, (150, 150, 150))
            self.screen.blit(instructions, (input_rect.x + 10, input_rect.y + 70))

    def handle_click(self, pos):
        """Handle mouse click events"""
        # Check for tab clicks first
        if pos[1] < self.TAB_HEIGHT:
            tab_width = self.screen.get_width() // len(self.tabs)
            clicked_tab = pos[0] // tab_width
            if 0 <= clicked_tab < len(self.tabs) and clicked_tab != self.current_tab:
                self.current_tab = clicked_tab
                self.scroll_y = 0  # Reset scroll when switching tabs
                self.load_custom_names()  # Reload names for new tab
                self.load_resources()  # Reload sprites for new tab
                self.redraw_catalog()  # Redraw the catalog surface
                self.update_window_title()  # Update window title with new file name
                return
            
        if self.enlarged_sprite:
            # Check if clicking outside the enlarged sprite or on close button
            if not self.enlarged_rect.collidepoint(pos):
                self.enlarged_sprite = None
                self.enlarged_rect = None
            return
            
        if self.folder_input_active:
            # Close folder input box if clicking outside
            input_rect = pygame.Rect(
                self.screen.get_width() // 4,
                self.screen.get_height() // 2 - 50,
                self.screen.get_width() // 2,
                100
            )
            if not input_rect.collidepoint(pos):
                self.folder_input_active = False
                self.text_selected = False
            return
            
        if self.input_active:
            # Close input box if clicking outside
            input_rect = pygame.Rect(
                self.screen.get_width() // 4,
                self.screen.get_height() // 2 - 50,
                self.screen.get_width() // 2,
                100
            )
            if not input_rect.collidepoint(pos):
                self.input_active = False
                self.text_selected = False
                self.save_custom_names()
            return
            
        # Check for sprite cell clicks
        sprite_info = self.get_sprite_at_position(pos)
        if sprite_info:
            self.selected_sprite = sprite_info
            
            # Create enlarged sprite
            enlarged_size = (self.SPRITE_SIZE[0] * self.ENLARGED_SCALE,
                           self.SPRITE_SIZE[1] * self.ENLARGED_SCALE)
            self.enlarged_sprite = pygame.transform.scale(sprite_info['sprite'], enlarged_size)
            
            # Center the enlarged sprite
            self.enlarged_rect = self.enlarged_sprite.get_rect()
            self.enlarged_rect.center = self.screen.get_rect().center
    
    def get_sprite_at_position(self, pos):
        """Get the sprite at the given screen position, accounting for scrolling"""
        # Ensure we have valid cell dimensions
        if self.CELL_WIDTH <= 0 or self.CELL_HEIGHT <= 0:
            return None
            
        # Adjust for tab height and scroll offset
        adjusted_y = pos[1] - self.TAB_HEIGHT + self.scroll_y
        
        # Calculate which cell this position corresponds to using current cell dimensions
        row = adjusted_y // self.CELL_HEIGHT
        col = pos[0] // self.CELL_WIDTH
        index = row * self.COLUMNS + col
        
        if 0 <= index < len(self.catalog):
            sprite_info = self.catalog[index]
            
            # Calculate the actual cell position (same as drawing)
            cell_x = col * self.CELL_WIDTH
            cell_y = row * self.CELL_HEIGHT
            
            # Create rectangle for collision detection using current dimensions
            # Adjust for tab height in the collision detection
            cell_rect = pygame.Rect(cell_x, cell_y - self.scroll_y + self.TAB_HEIGHT, self.CELL_WIDTH, self.CELL_HEIGHT)
            
            # Debug: print cell info (remove this in production)
            # print(f"Pos: {pos}, Adjusted Y: {adjusted_y}, Row: {row}, Col: {col}, Index: {index}")
            # print(f"Cell rect: {cell_rect}, Cell size: {self.CELL_WIDTH}x{self.CELL_HEIGHT}")
            
            # Check if position is within the cell bounds
            if cell_rect.collidepoint(pos):
                return sprite_info
        
        return None
    
    def handle_mouse_motion(self, pos):
        """Handle mouse motion for hover effects"""
        if self.enlarged_sprite or self.input_active or self.folder_input_active:
            self.hovered_sprite = None
            return
            
        # Use the same helper method for consistency
        self.hovered_sprite = self.get_sprite_at_position(pos)
    
    def draw_hover_effect(self):
        """Draw hover effect on top of the screen"""
        if not self.hovered_sprite:
            return
            
        # Find the hovered sprite in the catalog
        for i, sprite_info in enumerate(self.catalog):
            if (sprite_info['coords'] == self.hovered_sprite['coords'] and
                sprite_info['file'] == self.hovered_sprite['file']):
                
                # Calculate cell position
                row = i // self.COLUMNS
                col = i % self.COLUMNS
                cell_x = col * self.CELL_WIDTH
                cell_y = row * self.CELL_HEIGHT
                
                # Adjust for scroll and tab height
                hover_rect = pygame.Rect(
                    cell_x, 
                    cell_y - self.scroll_y + self.TAB_HEIGHT, 
                    self.CELL_WIDTH, 
                    self.CELL_HEIGHT
                )
                
                # Draw green hover effect
                pygame.draw.rect(self.screen, (0, 255, 0), hover_rect, 3)
                break
    
    def mark_sprite_as_empty(self):
        """Mark the selected sprite as empty and exclude it from the catalog"""
        if not self.selected_sprite:
            return
            
        # Update the custom names dictionary with file info
        sprite_key = (self.selected_sprite['file'],
                    self.selected_sprite['coords'][0],
                    self.selected_sprite['coords'][1],
                    self.selected_sprite['index'])
        self.custom_names[sprite_key] = "[EMPTY]"
        
        # Update the catalog entry directly
        for catalog_entry in self.catalog:
            if (catalog_entry['coords'] == self.selected_sprite['coords'] and 
                catalog_entry['index'] == self.selected_sprite['index'] and
                catalog_entry['file'] == self.selected_sprite['file']):
                catalog_entry['name'] = "[EMPTY]"
                break
        
        # Save and reload names
        self.save_custom_names()
        self.load_custom_names()
        self.redraw_catalog()
        
        # Clear selection
        self.selected_sprite = None
        self.enlarged_sprite = None
        self.enlarged_rect = None
    
    def calculate_optimal_cell_size(self):
        """Calculate optimal cell size based on content"""
        if not self.catalog:
            return
        
        # Find the longest name to determine minimum width
        max_name_width = 0
        for sprite_info in self.catalog:
            name_text = self.font.render(sprite_info['name'], True, self.TEXT)
            max_name_width = max(max_name_width, name_text.get_width())
        
        # Calculate optimal cell width (sprite width + padding + text width + some margin)
        optimal_width = max(
            self.MIN_CELL_WIDTH,
            self.SPRITE_SIZE[0] + self.CELL_PADDING * 2 + max_name_width + 20
        )
        
        # Calculate optimal cell height (sprite height + padding + text height + some margin)
        text_height = self.font.get_height()
        optimal_height = max(
            self.MIN_CELL_HEIGHT,
            self.SPRITE_SIZE[1] + self.CELL_PADDING * 2 + text_height + 10
        )
        
        # Update cell dimensions
        self.CELL_WIDTH = optimal_width
        self.CELL_HEIGHT = optimal_height
        
        # Recalculate columns based on new width
        self.COLUMNS = max(1, self.screen.get_width() // self.CELL_WIDTH)

    def refresh_catalog(self):
        """Refresh the entire catalog by reloading names and redrawing"""
        self.load_custom_names()  # Reload names from file
        self.load_resources()     # Reload sprites with updated names
        self.hovered_sprite = None  # Clear hover state
        self.redraw_catalog()     # Redraw the display

    def redraw_catalog(self):
        """Redraw the catalog surface with current sprites"""
        # Calculate optimal cell size first
        self.calculate_optimal_cell_size()
        
        # Calculate total height needed
        rows = (len(self.catalog) + self.COLUMNS - 1) // self.COLUMNS
        total_height = rows * self.CELL_HEIGHT
        
        # Create a surface for all sprites (accounting for tab height)
        self.catalog_surface = pygame.Surface((self.screen.get_width(), total_height), pygame.SRCALPHA)
        
        # No rename buttons to clear
        
        # Draw all sprites to the catalog surface
        for i, sprite_info in enumerate(self.catalog):
            row = i // self.COLUMNS
            col = i % self.COLUMNS
            x = col * self.CELL_WIDTH
            y = row * self.CELL_HEIGHT
            self.draw_sprite_cell(self.catalog_surface, sprite_info, x, y)

    def run(self):
        """Main display loop"""
        running = True
        
        # Initial catalog setup
        self.redraw_catalog()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEWHEEL:
                    if not self.enlarged_sprite and not self.input_active:
                        max_scroll = self.catalog_surface.get_height() - (self.screen.get_height() - self.TAB_HEIGHT)
                        self.scroll_y = max(min(self.scroll_y - event.y * self.scroll_speed, max_scroll), 0)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_click(event.pos)
                
                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resize
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.refresh_catalog()  # Refresh entire catalog
                
                elif event.type == pygame.MOUSEMOTION:
                    # Handle mouse hover
                    self.handle_mouse_motion(event.pos)
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Cancel folder input first (highest priority)
                        if self.folder_input_active:
                            self.folder_input_active = False
                            self.text_selected = False
                        # Cancel rename process second
                        elif self.input_active:
                            self.input_active = False
                            self.input_text = ""
                            self.text_selected = False
                        # Cancel enlarged sprite view
                        elif self.enlarged_sprite:
                            self.enlarged_sprite = None
                            self.enlarged_rect = None
                    
                    elif event.key == pygame.K_F5:
                        # Refresh catalog from file
                        self.refresh_catalog()
                    
                    elif event.key == pygame.K_F12:
                        # Open folder input
                        self.folder_input_active = True
                        self.folder_input_text = str(self.assets_folder)
                        self.text_selected = True
                    
                    # Number keys for tab switching
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        tab_index = event.key - pygame.K_1  # Convert to 0-based index
                        if tab_index < len(self.tabs):
                            self.current_tab = tab_index
                            self.scroll_y = 0
                            self.load_custom_names()
                            self.load_resources()
                            self.redraw_catalog()
                            self.update_window_title()
                    
                    elif event.key == pygame.K_DELETE and self.selected_sprite:
                        # Mark sprite as empty
                        self.mark_sprite_as_empty()
                    
                    elif event.key == pygame.K_F2 and self.selected_sprite:
                        self.input_active = True
                        sprite_key = (self.selected_sprite['file'],
                                    self.selected_sprite['coords'][0],
                                    self.selected_sprite['coords'][1],
                                    self.selected_sprite['index'])
                        self.input_text = self.custom_names.get(sprite_key, self.selected_sprite['name'])
                        self.text_selected = True  # Text will be selected when input starts
                    
                    elif self.folder_input_active:
                        if event.key == pygame.K_RETURN:
                            if self.folder_input_text:
                                # Try to load the new folder
                                if self.load_folder(self.folder_input_text):
                                    print(f"Successfully loaded folder: {self.folder_input_text}")
                                else:
                                    print(f"Failed to load folder: {self.folder_input_text}")
                            self.folder_input_active = False
                            self.text_selected = False
                        
                        elif event.key == pygame.K_BACKSPACE:
                            if self.text_selected:
                                self.folder_input_text = ""
                                self.text_selected = False
                            else:
                                self.folder_input_text = self.folder_input_text[:-1]
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_UP:
                            # Move cursor to end of line
                            self.text_selected = False
                        elif event.key == pygame.K_LEFT or event.key == pygame.K_DOWN:
                            # Move cursor to beginning of line
                            self.text_selected = False
                        elif event.key == pygame.K_c and pygame.key.get_pressed()[pygame.K_LCTRL]:
                            # Copy selected text to clipboard
                            if self.text_selected:
                                pygame.scrap.put(pygame.SCRAP_TEXT, self.folder_input_text.encode('utf-8'))
                        elif event.key == pygame.K_v and pygame.key.get_pressed()[pygame.K_LCTRL]:
                            # Paste from clipboard
                            try:
                                clipboard_text = pygame.scrap.get(pygame.SCRAP_TEXT).decode('utf-8')
                                if self.text_selected:
                                    self.folder_input_text = clipboard_text
                                    self.text_selected = False
                                else:
                                    self.folder_input_text += clipboard_text
                            except:
                                pass  # Ignore clipboard errors
                        else:
                            if self.text_selected:
                                self.folder_input_text = event.unicode
                                self.text_selected = False
                            else:
                                self.folder_input_text += event.unicode
                    
                    elif self.input_active:
                        if event.key == pygame.K_RETURN:
                            if self.input_text:
                                # Update the custom names dictionary with file info
                                sprite_key = (self.selected_sprite['file'],
                                            self.selected_sprite['coords'][0],
                                            self.selected_sprite['coords'][1],
                                            self.selected_sprite['index'])
                                self.custom_names[sprite_key] = self.input_text
                                
                                # Update the catalog entry directly
                                for catalog_entry in self.catalog:
                                    if (catalog_entry['coords'] == self.selected_sprite['coords'] and 
                                        catalog_entry['index'] == self.selected_sprite['index'] and
                                        catalog_entry['file'] == self.selected_sprite['file']):
                                        catalog_entry['name'] = self.input_text
                                        break
                                
                                # Save and reload names
                                self.save_custom_names()
                                self.load_custom_names()  # Reload names from file
                                self.redraw_catalog()
                            self.input_active = False
                            self.text_selected = False
                        
                        elif event.key == pygame.K_BACKSPACE:
                            if self.text_selected:
                                self.input_text = ""
                                self.text_selected = False
                            else:
                                self.input_text = self.input_text[:-1]
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_UP:
                            # Move cursor to end of line
                            self.text_selected = False
                        elif event.key == pygame.K_LEFT or event.key == pygame.K_DOWN:
                            # Move cursor to beginning of line
                            self.text_selected = False
                        elif event.key == pygame.K_c and pygame.key.get_pressed()[pygame.K_LCTRL]:
                            # Copy selected text to clipboard
                            if self.text_selected:
                                pygame.scrap.put(pygame.SCRAP_TEXT, self.input_text.encode('utf-8'))
                        elif event.key == pygame.K_v and pygame.key.get_pressed()[pygame.K_LCTRL]:
                            # Paste from clipboard
                            try:
                                clipboard_text = pygame.scrap.get(pygame.SCRAP_TEXT).decode('utf-8')
                                if self.text_selected:
                                    self.input_text = clipboard_text
                                    self.text_selected = False
                                else:
                                    self.input_text += clipboard_text
                            except:
                                pass  # Ignore clipboard errors
                        else:
                            if self.text_selected:
                                self.input_text = event.unicode
                                self.text_selected = False
                            else:
                                self.input_text += event.unicode
            
            # Draw everything
            self.screen.fill(self.BACKGROUND)
            
            # Draw tabs
            self.draw_tabs()
            
            # Draw sprites (offset by tab height)
            self.screen.blit(self.catalog_surface, (0, self.TAB_HEIGHT - self.scroll_y))
            
            # Draw hover effect on top of sprites
            if not self.enlarged_sprite and not self.input_active and not self.folder_input_active and self.hovered_sprite:
                self.draw_hover_effect()
            
            if self.enlarged_sprite:
                self.draw_enlarged_sprite()
            
            if self.folder_input_active:
                self.draw_folder_input_box()
            
            if self.input_active:
                self.draw_input_box()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # Save custom names before quitting
        self.save_custom_names()
        pygame.quit()

if __name__ == "__main__":
    import sys
    
    # Allow specifying a folder as a command line argument
    assets_folder = None
    if len(sys.argv) > 1:
        assets_folder = Path(sys.argv[1])
        if not assets_folder.exists():
            print(f"Error: Folder '{assets_folder}' does not exist")
            sys.exit(1)
    
    catalog = SpriteCatalog(assets_folder)
    catalog.run()