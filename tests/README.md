# Mythica Test Suite

Comprehensive test suite for the Mythica dungeon crawler game, designed to detect regressions and ensure all game features work correctly.

## Test Organization

The test suite is organized into four main categories:

### Character System Tests (`test_character_system.py`)
- Character stats and stat calculations
- Equipment system and stat bonuses  
- Character classes and their starting configurations
- Item generation and equipment mechanics
- HP calculations based on Constitution

### Turn System Tests (`test_turn_system.py`)
- Action timing and scheduling
- Weapon-specific timing (attack and reload speeds)
- Turn order management
- Dexterity effects on action speed
- Combat timing mechanics

### Combat & Damage Tests (`test_combat_damage.py`)
- Damage calculation mechanics
- Health point systems
- Combat resolution
- Enemy AI and behavior
- Health bar functionality
- Death and defeat mechanics

### Dungeon Generation Tests (`test_dungeon_generation.py`)
- Dungeon generation algorithms
- Line of sight calculations
- Collision detection
- Room and corridor generation
- Minimap functionality
- Fog of war mechanics

## Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Specific Test Suite
```bash
python tests/run_all_tests.py --suite "Character System"
python tests/run_all_tests.py --suite "Turn System"
python tests/run_all_tests.py --suite "Combat & Damage"
python tests/run_all_tests.py --suite "Dungeon Generation"
```

### Run Regression Tests Only
```bash
python tests/run_all_tests.py --regression
```

### Run Individual Test Files
```bash
python -m unittest tests.test_character_system
python -m unittest tests.test_turn_system
python -m unittest tests.test_combat_damage
python -m unittest tests.test_dungeon_generation
```

### Run Specific Test Classes
```bash
python -m unittest tests.test_character_system.TestCharacterStats
python -m unittest tests.test_turn_system.TestActionCosts
```

## Test Features

### Comprehensive Coverage
- **Turn Timing**: Tests weapon attack speeds, reload times, and Dexterity effects
- **Combat Mechanics**: Tests damage calculation, health systems, and combat resolution
- **Character System**: Tests stats, equipment, character classes, and HP calculations
- **Dungeon Systems**: Tests generation, line of sight, movement, and minimap

### Regression Detection
- Validates critical game mechanics haven't broken
- Tests edge cases and boundary conditions
- Verifies stat calculations and formulas
- Ensures weapon timing remains consistent

### Detailed Reporting
- Shows pass/fail status for each test category
- Provides timing information for performance monitoring
- Identifies specific failing tests with error details
- Gives feature coverage analysis

## Expected Test Results

When all systems are working correctly, you should see:
- ✓ Character Stats & Equipment
- ✓ Character Classes
- ✓ Turn Timing & Actions  
- ✓ Weapon Timing
- ✓ Damage Calculation
- ✓ Health System
- ✓ Enemy AI
- ✓ Dungeon Generation
- ✓ Line of Sight

## Adding New Tests

When adding new game features, create corresponding tests:

1. Add test methods to existing test classes if they fit the category
2. Create new test classes for entirely new systems
3. Update `run_all_tests.py` to include new test classes
4. Ensure tests cover both normal operation and edge cases

## Test Design Principles

- **Isolated**: Each test is independent and doesn't rely on others
- **Deterministic**: Tests produce consistent results
- **Fast**: Tests run quickly to encourage frequent execution
- **Comprehensive**: Tests cover normal cases, edge cases, and error conditions
- **Readable**: Test names clearly describe what they're testing

## Dependencies

Tests use Python's built-in `unittest` framework and require the game's logic modules to be importable from the `logic/` directory. 