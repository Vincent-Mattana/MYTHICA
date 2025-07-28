# Mythica - Grid-Based Dungeon Crawler

A procedurally generated dungeon exploration game with minimap functionality, built with Python and pygame.

## Features

- **Grid-based movement**: Classic dungeon crawler movement system with 8-directional support
- **Turn-based combat**: Tactical action system where each action takes time
- **Weapon timing**: Different weapons have unique attack speeds and reload times
- **Configurable controls**: Rebindable keys via .ini file with numpad support
- **Character classes**: Choose from 5 distinct classes (Warrior, Rogue, Mage, Ranger, Cleric)
- **Level-up system**: Automatic leveling with experience thresholds and perk points
- **Comprehensive perk trees**: 25+ perks across universal and class-specific specializations
- **Character specialization**: Deep character customization through perk choices
- **Multi-level dungeons**: Descend through increasingly challenging dungeon levels
- **Progressive difficulty**: Enemies become stronger and more dangerous on deeper levels
- **Staircase exploration**: Find and use staircases to progress to new dungeon levels
- **Streamlined game over**: Death is logged in sidebar without interrupting gameplay
- **Procedural generation**: Each game creates a unique dungeon layout
- **Line of sight system**: Vision blocked by walls for tactical exploration
- **Combat system**: Fight various enemies with stat-based damage calculations
- **Health system**: HP bars for player and enemies with Constitution-based health and regeneration
- **Always-visible enemy HP**: Red health bars with high contrast for easy reading
- **Enemy AI**: Different behavior patterns adapted for turn-based play
- **Character stats system**: Five core stats affecting action speeds and capabilities
- **Equipment system**: Eight equipment slots with stat-boosting items
- **Character sheet**: Press 'C' to view detailed character information including perks
- **Game log system**: Recent Events sidebar with color-coded combat and exploration messages
- **Clean sidebar UI**: Streamlined interface showing only essential information
- **Minimap**: Track your exploration progress and navigate the dungeon
- **Room and corridor system**: Interconnected rooms with corridor pathways
- **Real-time exploration**: Areas are revealed as you explore them
- **Fog of war**: Previously explored areas remain visible but dimmed
- **Auto-explore mode**: Press 'O' to automatically explore unexplored areas
- **Smart pathfinding**: Auto-explore uses A* pathfinding to efficiently navigate to unexplored regions
- **Enemy detection**: Auto-explore automatically stops when enemies are detected within line of sight
- **HP regeneration system**: Constitution-based health regeneration enhanced by perks
- **Turn-based regeneration**: Health regenerates during combat, movement, and rest actions
- **Treasure system**: Randomly placed chests containing equipment and HP pickups for healing
- **Interactive exploration**: Automatically collect treasures and pickups by walking over them
- **Comprehensive test suite**: 100% test coverage for perk system ensuring code quality

## Installation

1. Ensure you have Python 3.7+ installed
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## File Structure
Mythica/
├── logic/                    # Core game logic (NEW)
│   ├── character_system.py   # Character stats, equipment, classes
│   ├── enemy_system.py       # Enemy AI, health bars, spawning  
│   ├── turn_system.py        # Action timing, weapon speeds
│   ├── game_states.py        # Game state management, menus
│   ├── config_manager.py     # Configuration handling
│   └── __init__.py          # Package exports
├── tests/                    # Comprehensive test suite (NEW)
│   ├── test_character_system.py   # Character & equipment tests
│   ├── test_turn_system.py        # Turn timing & action tests
│   ├── test_combat_damage.py      # Combat & damage tests  
│   ├── test_dungeon_generation.py # Dungeon & spatial tests
│   ├── run_all_tests.py           # Test runner with reporting
│   ├── README.md                  # Test documentation
│   └── test_game.py               # Original tests (kept)
├── demos/                    # Demo scripts (MOVED)
│   ├── character_demo.py     # Character system demo
│   ├── enemy_demo.py         # Enemy system demo
│   ├── turn_system_demo.py   # Turn timing demo
│   └── ... (all demo files)
├── main.py                   # Main game loop (updated imports)
└── ... (config files remain in root)

## Usage

Run the game:
```bash
python main.py
```

## Controls

### Default Controls
- **WASD** or **Arrow Keys**: 4-directional movement
- **Numpad 1-9**: 8-directional movement (diagonal support)
  ```
  7 8 9    ← Northwest, North, Northeast
  4   6    ← West,      Wait,  East  
  1 2 3    ← Southwest, South, Southeast
  ```
- **C**: Toggle character sheet display
- **O**: Toggle auto-explore mode (automatically explore unexplored areas)
- **]**: Go down stairs (when standing on a staircase)
- **[**: Go up stairs (when standing on a staircase)
- **Space/Period/Numpad 5**: Wait/rest turn
- **ESC**: Exit the game
- **F5**: Reload configuration file

### Customizable Controls
Controls can be customized by editing `config.ini`:
- Multiple keys can be assigned to the same action
- Diagonal movement can be enabled/disabled
- Uses pygame key names (e.g., K_w, K_KP8, K_SPACE)

## Auto-Explore Feature

### How Auto-Explore Works
- **Activation**: Press 'O' to toggle auto-explore mode on/off
- **Intelligent Pathfinding**: Uses A* algorithm to find the shortest path to nearest unexplored areas
- **Enemy Detection**: Automatically stops when any enemy comes into line of sight
- **Manual Override**: Any manual movement input cancels auto-explore mode
- **Completion Notification**: Alerts when all accessible areas have been explored

### Auto-Explore Behavior
- **Safety First**: Cannot activate auto-explore when enemies are visible
- **Turn-Based**: Follows the same turn-based movement system as manual play
- **Pathfinding**: Avoids enemies and impassable terrain when planning routes
- **Efficient Exploration**: Always moves towards the closest unexplored area
- **Real-Time Feedback**: Status updates appear in the game log with color coding

### Auto-Explore Messages
- 🔵 **Blue**: "Auto-explore enabled" - Mode successfully activated
- ⚪ **White**: "Auto-explore disabled/cancelled" - Mode deactivated
- 🔴 **Red**: "Cannot auto-explore: enemies nearby!" - Activation blocked by visible enemies
- 🔴 **Red**: "Auto-explore stopped: enemy detected!" - Mode stopped due to enemy detection
- 🟢 **Green**: "Auto-explore complete: all areas explored!" - All accessible areas discovered
- 🟡 **Yellow**: "Auto-explore stopped: cannot reach target" - Pathfinding failed

## Stair Navigation System

### How Stair Navigation Works
- **Find Staircases**: Locate bright yellow staircase tiles throughout dungeon levels
- **Stand on Stairs**: Move your character onto a staircase tile
- **Navigate Levels**: Use '>' to descend to deeper levels or '<' to ascend to previous levels
- **Level Persistence**: All previously visited levels are saved with their current state

### Stair Navigation Controls
- **Descent ('>')**: Creates a new deeper dungeon level with increased difficulty
- **Ascent ('<')**: Returns to a previously visited level, restoring its exact state
- **Safety Checks**: Commands only work when standing directly on a staircase
- **Auto-Explore Integration**: Stair navigation automatically cancels active auto-explore

### Level State Management
- **Preserved Exploration**: Your exploration progress is maintained when returning to levels
- **Enemy States**: Enemies remain in their last known positions and health states
- **Dynamic Difficulty**: Each new level down increases enemy count and statistics
- **No Level Limit**: Continue descending as deep as you dare

### Stair Navigation Messages
- 🟡 **Yellow**: "Descending to dungeon level X..." - Successfully going down stairs
- 🟡 **Yellow**: "Ascending to dungeon level X..." - Successfully going up stairs
- 🔴 **Red**: "No staircase here to go down/up" - Attempted stair navigation without being on stairs
- 🟡 **Yellow**: "You are already on the top level" - Attempted to go up from level 1

## Health and Regeneration System

### Constitution-Based Health
- **Maximum HP**: Base 20 + (Constitution-10)*2 + level bonuses
- **High Constitution Benefits**: Characters with 12+ Constitution gain slow natural regeneration
- **Scaling Health**: Each level grants +5 maximum HP and fully restores health

### HP Regeneration Mechanics
- **Base Regeneration**: High Constitution (15+) provides 1 HP every 20 turns
- **Perk Enhancement**: Regeneration perk provides 1-3 HP every 8-10 turns based on rank
- **Blessed Recovery**: Cleric perk makes Constitution significantly boost regeneration
- **Turn-Based Timing**: Regeneration processes after movement, combat, and wait actions

### Regeneration Formula
- **Without Perks**: Constitution 15+ = 1 HP per 20-30 turns
- **With Regeneration Perk**: 1 HP per 10 turns per rank (faster with higher ranks)
- **With Blessed Recovery**: +Constitution bonus healing and faster regeneration rate
- **Combined Effect**: High-Constitution Clerics can regenerate 3-5+ HP every 5-8 turns

### Regeneration Messages
- 🟢 **Green**: "Regenerated X HP" - Successful health regeneration during play

## Treasure and Loot System

### Treasure Chests
- **Room Placement**: Each room has a 70% chance of containing 1-2 treasure chests
- **Strategic Positioning**: Chests are placed away from room centers and entrances for exploration rewards
- **Quality Scaling**: Chest contents improve with deeper dungeon levels (quality 1-5)
- **Auto-Equip**: Found items are automatically equipped if suitable and if slots are available

### Health Pickups
- **Random Distribution**: Health potions scattered throughout dungeon floors (roughly 1 per 50 floor tiles)
- **Instant Healing**: Restore 5-15 HP immediately when collected
- **Strategic Value**: Provide crucial healing between combat encounters

### Treasure Interaction
- **Automatic Collection**: Simply walk over chests and pickups to interact with them
- **One-Time Use**: Opened chests become empty floor tiles
- **Level Persistence**: Treasure states are saved when moving between dungeon levels

### Loot Quality by Depth
- **Level 1-2**: Basic equipment with 1-2 stat bonuses
- **Level 3-4**: Improved gear with 2-3 stat bonuses  
- **Level 5+**: Exceptional equipment with 3+ stat bonuses and higher values

### Treasure Messages
- 🟢 **Green**: "Found and equipped: [Item]" - Automatic equipment upgrade
- 🟡 **Yellow**: "Found: [Item] (inventory full)" - Item found but couldn't be equipped
- 🟢 **Green**: "Picked up health potion! Healed X HP" - Successful healing
- 🟡 **Yellow**: "Picked up health potion, but you're already at full health" - Potion collected at full HP
- ⚪ **Grey**: "This chest is already empty" - Attempting to open an already opened chest

## Level-Up and Perk System

### Experience and Leveling
- **Experience Gain**: Defeat enemies to gain experience points (varies by enemy type)
- **Automatic Leveling**: Characters automatically level up when reaching experience thresholds
- **Experience Formula**: Level requirements follow `100 * level^1.5` (rounded)
- **Perk Points**: Gain 2 perk points per level to spend on character advancement
- **Level Benefits**: Each level increases maximum HP by 5 and fully restores health

### Perk Categories

#### **Universal Perks** (Available to All Classes)

**Combat Perks:**
- **Power Attack** (3 ranks): +2 base damage per rank
- **Combat Reflexes** (3 ranks): -5% action time per rank
- **Critical Strike** (2 ranks): +5% critical hit chance per rank (requires Power Attack)

**Survival Perks:**
- **Toughness** (5 ranks): +5 maximum health per rank
- **Regeneration** (3 ranks): Regenerate 1-3 HP every 8-10 turns (requires Toughness)
- **Damage Resistance** (3 ranks): -1 incoming damage per rank (requires Toughness)

**Utility Perks:**
- **Keen Senses** (3 ranks): +1 sight range per rank
- **Fast Learner** (2 ranks): +10% experience gain per rank

#### **Class-Specific Specializations**

### **Warrior Specialization**
*Focus: Melee combat mastery and heavy armour*

- **Weapon Mastery** (2 ranks): +25% weapon damage per rank
- **Berserker Rage**: +50% attack speed when below 25% health (requires Weapon Mastery)
- **Armour Expertise** (2 ranks): +50% armour stat bonuses per rank (requires Weapon Mastery)

### **Rogue Specialization**
*Focus: Stealth, luck, and precision strikes*

- **Stealth** (2 ranks): +30% stealth effectiveness per rank
- **Backstab** (2 ranks): +100% damage from behind per rank (requires Stealth)
- **Lucky Strike** (2 ranks): Luck stat affects critical hit chance

### **Mage Specialization**  
*Focus: Perception enhancement and magical abilities*

- **Arcane Knowledge** (2 ranks): +50% perception sight bonus per rank
- **Mana Shield**: Reduce damage by Perception/4 (requires Arcane Knowledge)
- **Spell Power** (2 ranks): Staff damage +Perception/2 (requires Arcane Knowledge)

### **Ranger Specialization**
*Focus: Ranged combat and environmental awareness*

- **Nature Lore** (2 ranks): +2 sight range in dungeons per rank
- **Precise Shot** (2 ranks): +40% bow weapon damage per rank (requires Nature Lore)
- **Tracking**: Sense enemies within 3 tiles (requires Nature Lore)

### **Cleric Specialization**
*Focus: Divine favour and constitution-based abilities*

- **Divine Favour** (2 ranks): Luck affects all beneficial random events
- **Blessed Recovery** (2 ranks): Constitution significantly enhances regeneration rate and amount (requires Divine Favour)
- **Holy Strength**: Mace damage +Luck/3 (requires Divine Favour)

### Perk Strategy Tips

**Early Game Priorities:**
- **Toughness**: Immediate survivability boost
- **Power Attack**: Reliable damage increase
- **Keen Senses**: Better exploration and combat awareness

**Mid Game Specialization:**
- Focus on your class-specific tree for maximum effectiveness
- **Fast Learner**: Accelerates progression if taken early
- **Critical Strike**: High-impact combat enhancement

**Late Game Mastery:**
- Complete your chosen specialization branch
- **Regeneration**: Long-term sustainability
- Advanced class abilities for unique tactical options

**Class-Specific Builds:**

*Warrior Tank*: Toughness → Damage Resistance → Armour Expertise → Berserker Rage

*Rogue Assassin*: Lucky Strike → Stealth → Backstab → Critical Strike

*Mage Scholar*: Keen Senses → Arcane Knowledge → Spell Power → Mana Shield

*Ranger Marksman*: Nature Lore → Precise Shot → Fast Learner → Tracking

*Cleric Support*: Divine Favour → Blessed Recovery → Toughness → Regeneration

## Dungeon Exploration and Progression

### Multi-Level Dungeon System
- **Staircase Discovery**: Find bright yellow staircases throughout each dungeon level
- **Level Navigation**: Stand on staircases and use '>' to go down or '<' to go up between levels
- **Level Memory**: Previously visited levels are preserved, allowing you to return with the same layout and exploration progress
- **Automatic Generation**: Each new level features a newly generated layout with unique room configurations
- **Progressive Challenge**: Deeper levels contain more enemies with enhanced statistics

### Difficulty Scaling by Level

**Level 1** (Starting Level):
- Enemies: Mostly Giant Rats, Goblins, some Spiders and Skeletons
- Enemy Count: 15 enemies
- Stats: Base enemy statistics

**Level 2-3** (Early Depths):
- Enemies: Fewer rats, more Goblins and Spiders, increased Skeletons
- Enemy Count: 17-19 enemies  
- Stats: +15-30% increase to all enemy statistics

**Level 4-5** (Mid Depths):
- Enemies: Introduction of Orcs, occasional Trolls, balanced mix
- Enemy Count: 21-23 enemies
- Stats: +45-60% increase to all enemy statistics

**Level 5+** (Deep Levels):
- Enemies: Dominant Orcs and Trolls, fewer weak creatures
- Enemy Count: Up to 25 enemies
- Stats: +75%+ increase to all enemy statistics

### Strategic Considerations
- **Risk vs Reward**: Deeper levels provide more experience but exponentially increased danger
- **Character Progression**: Use perk points to prepare for deeper challenges
- **Level Planning**: Find staircases but choose carefully when to descend
- **Retreat Strategy**: You can always return to previous levels if current level becomes too dangerous
- **Resource Management**: Consider your health and supplies before committing to deeper exploration
- **Treasure Hunting**: Thoroughly explore rooms to find valuable chests and health pickups
- **Equipment Progression**: Better loot on deeper levels rewards brave exploration
- **Enemy Variety**: Different enemy types require adapted strategies at each level

## Game Elements

- **Yellow Circle**: Your character (flashes red when damaged)
- **Bright Yellow Squares**: Staircases leading to the next dungeon level
- **Brown Squares**: Treasure chests containing random equipment (max 2 per room)
- **Light Red Squares**: Health potions that restore 5-15 HP when collected
- **Coloured Circles with Letters**: Enemies (R=Rat, G=Goblin, S=Skeleton/Spider, O=Orc, T=Troll)
- **Player Health Bar**: Green/yellow/red bar in sidebar showing current HP
- **Dungeon Level**: Current depth shown in sidebar (Level: X)
- **Level & Experience**: Shows current level and experience progress in character sheet
- **Perk Points**: Available points for character advancement (shown in character sheet)
- **Enemy Health Bars**: Always-visible red bars with black background and white outline above all enemies
- **Recent Events Log**: Color-coded messages in sidebar showing combat, exploration, and game events
- **Turn Status**: Shows "Your Turn", "Processing...", or "DEAD" in sidebar
- **Bright White Areas**: Currently visible floor tiles (walkable)
- **Dimmed White Areas**: Previously explored floor tiles (walkable)
- **Bright Grey Areas**: Currently visible wall tiles (impassable)
- **Dimmed Grey Areas**: Previously explored wall tiles (impassable)
- **Brown Areas**: Door tiles (walkable)
- **Red Dot on Minimap**: Your current position
- **Yellow Areas on Minimap**: Discovered staircases
- **Black Areas**: Unexplored regions

## User Interface & Experience

### Sidebar Information
- **Player Info**: Name, level, and HP with visual health bar
- **Turn Info**: Current turn number, game time, and action status
- **Recent Events**: Scrolling log of the last 8 game events with color coding:
  - 🟡 **Yellow**: Game start, experience gained, important events
  - 🔴 **Red**: Taking damage, enemy attacks, death notifications
  - 🟢 **Green**: Victories, defeating enemies, positive events
  - ⚪ **White**: Your attacks and standard actions
  - 🔵 **Blue**: Exploration progress and area discovery
  - ⚪ **Grey**: Neutral actions (waiting, resting)

### Enhanced Visual Design
- **High-contrast enemy health bars**: Red bars with black background and white outline for maximum visibility
- **Always-visible enemy HP**: No need to damage enemies first - see their health immediately
- **Clean, minimal interface**: Removed clutter to focus on essential game information
- **Streamlined death experience**: No full-screen interruptions - death becomes part of your story
- **Perk progression feedback**: Clear indicators of character advancement and available upgrades

### Character Progression
- **Level-up notifications**: Automatic alerts when gaining levels and perk points
- **Experience tracking**: Character sheet shows experience progress and points to next level
- **Perk effects display**: Active perk bonuses shown in character sheet
- **Specialization feedback**: Clear indication of chosen character build path

### Death & Game Over
- **In-game death logging**: Death is recorded in the Recent Events log
- **View-only mode**: After death, you can still observe the game world but cannot take actions
- **Immediate feedback**: Clear "DEAD" status and "Press ESC to exit" instruction
- **No action interruptions**: Game continues smoothly with death as a narrative event

## Technical Details

- Built with pygame for cross-platform compatibility
- Procedural generation using room placement and corridor connection algorithms
- Grid-based coordinate system for precise movement
- Advanced line of sight system using raycasting algorithm
- Fog of war with separate tracking of explored vs visible areas
- Efficient rendering with viewport culling
- Minimap scaling for large dungeon navigation with visibility states
- **Comprehensive perk system**: 25+ perks with prerequisite trees and class restrictions
- **Automatic level progression**: Experience-based advancement with configurable thresholds
- **Modular architecture**: Clean separation between game logic, UI, systems, and character progression
- **Real-time event logging**: Color-coded game events with automatic message management
- **100% test coverage**: Comprehensive testing for perk system and character advancement

## Game Architecture

The game follows a modular design with separate classes for:
- `Game`: Main game loop and coordination
- `Player`: Character state and movement
- `Character`: RPG stats, equipment management, and perk integration
- `PerkSystem`: Character advancement and specialization trees
- `CharacterPerks`: Individual character perk management
- `Dungeon`: Procedural generation and collision detection
- `Camera`: Viewport management
- `Minimap`: Navigation aid rendering
- `Room`: Dungeon room generation
- `LineOfSight`: Vision calculation system
- `Equipment`: Item and gear management
- `ItemGenerator`: Procedural item creation
- `EnemyManager`: Enemy spawning and AI coordination
- `Enemy`: Individual enemy behavior and stats
- `HealthBar`: HP visualization system
- `ConfigManager`: Configuration file handling and key mapping
- `GameStateManager`: Menu, class selection, and game over screens
- `CharacterClassData`: Character class definitions and creation
- `TurnManager`: Turn-based action scheduling and timing
- `ActionCosts`: Weapon timing and action cost calculations

Enjoy exploring the depths of Mythica and developing your unique character build! 