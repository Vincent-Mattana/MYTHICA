#!/usr/bin/env python3
"""
Character System Demo for Mythica Dungeon Crawler
Demonstrates the character stats and equipment functionality.
"""

from logic.character_system import Character, ItemGenerator, ItemType, StatType, EquipmentSlot

def demonstrate_character_system():
    """Demonstrate the character system features."""
    print("=== Mythica Character System Demo ===\n")
    
    # Create a new character
    hero = Character("Brave Adventurer")
    
    print(f"Character: {hero.name}")
    print(f"Level: {hero.level}")
    print(f"Starting sight range: {hero.get_sight_range()} tiles\n")
    
    # Show starting stats
    print("=== Starting Stats ===")
    for stat_type, (base, bonus, total) in hero.stats.get_all_stats().items():
        bonus_text = f" (+{bonus})" if bonus > 0 else f" ({bonus})" if bonus < 0 else ""
        print(f"{stat_type.value}: {base}{bonus_text} = {total}")
    
    print("\n=== Starting Equipment ===")
    for slot_name, item_name in hero.equipment.get_equipment_summary().items():
        print(f"{slot_name}: {item_name}")
    
    # Generate some new equipment
    print("\n=== Finding New Equipment ===")
    
    # Generate a high-quality helmet
    helmet = ItemGenerator.generate_random_item(ItemType.HELMET, quality=2)
    print(f"\nFound: {helmet.name}")
    print(f"Description: {helmet.description}")
    
    # Equip the helmet
    if hero.equip_item(helmet, EquipmentSlot.HEAD):
        print(f"✓ Equipped {helmet.name} to head slot")
    else:
        print("✗ Failed to equip helmet")
    
    # Generate a magic ring
    magic_ring = ItemGenerator.generate_random_item(ItemType.RING, quality=3)
    print(f"\nFound: {magic_ring.name}")
    print(f"Description: {magic_ring.description}")
    
    # Equip the ring
    if hero.equip_item(magic_ring, EquipmentSlot.RING_1):
        print(f"✓ Equipped {magic_ring.name} to ring slot 1")
    else:
        print("✗ Failed to equip ring")
    
    # Show updated stats
    print("\n=== Updated Stats (with equipment bonuses) ===")
    for stat_type, (base, bonus, total) in hero.stats.get_all_stats().items():
        if bonus > 0:
            print(f"{stat_type.value}: {base} (+{bonus}) = {total}")
        elif bonus < 0:
            print(f"{stat_type.value}: {base} ({bonus}) = {total}")
        else:
            print(f"{stat_type.value}: {base}")
    
    print(f"\nUpdated sight range: {hero.get_sight_range()} tiles")
    
    print("\n=== Final Equipment ===")
    for slot_name, item_name in hero.equipment.get_equipment_summary().items():
        print(f"{slot_name}: {item_name}")
    
    # Demonstrate stat effects
    perception = hero.stats.get_total_stat(StatType.PERCEPTION)
    sight_bonus = max(0, (perception - 10) // 2)
    print(f"\nPerception Impact:")
    print(f"- Perception stat: {perception}")
    print(f"- Base sight range: 6 tiles")
    print(f"- Perception bonus: +{sight_bonus} tiles")
    print(f"- Total sight range: {hero.get_sight_range()} tiles")

if __name__ == "__main__":
    demonstrate_character_system() 