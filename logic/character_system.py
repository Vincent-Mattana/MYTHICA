#!/usr/bin/env python3
"""
Character System for Mythica Dungeon Crawler
Handles character stats, equipment, and related functionality.
"""

from typing import Dict, Optional, Tuple, List
from enum import Enum
import random

class StatType(Enum):
    STRENGTH = "Strength"
    DEXTERITY = "Dexterity"
    CONSTITUTION = "Constitution"
    PERCEPTION = "Perception"
    LUCK = "Luck"

class EquipmentSlot(Enum):
    HEAD = "Head"
    TORSO = "Torso"
    LEGS = "Legs"
    WEAPON_1 = "Weapon Slot 1"
    WEAPON_2 = "Weapon Slot 2"
    RING_1 = "Ring 1"
    RING_2 = "Ring 2"
    NECK = "Neck (Amulet)"

class ItemType(Enum):
    HELMET = "Helmet"
    ARMOUR = "Armour"
    BOOTS = "Boots"
    WEAPON = "Weapon"
    RING = "Ring"
    AMULET = "Amulet"

class Item:
    def __init__(self, name: str, item_type: ItemType, stat_bonuses: Dict[StatType, int] = None):
        self.name = name
        self.item_type = item_type
        self.stat_bonuses = stat_bonuses or {}
        self.description = self._generate_description()
    
    def _generate_description(self) -> str:
        """Generate a description based on stat bonuses."""
        if not self.stat_bonuses:
            return f"A simple {self.item_type.value.lower()}."
        
        bonus_text = []
        for stat, bonus in self.stat_bonuses.items():
            sign = "+" if bonus >= 0 else ""
            bonus_text.append(f"{sign}{bonus} {stat.value}")
        
        return f"A {self.item_type.value.lower()} that grants: {', '.join(bonus_text)}"
    
    def can_equip_to_slot(self, slot: EquipmentSlot) -> bool:
        """Check if this item can be equipped to the given slot."""
        compatibility = {
            ItemType.HELMET: [EquipmentSlot.HEAD],
            ItemType.ARMOUR: [EquipmentSlot.TORSO],
            ItemType.BOOTS: [EquipmentSlot.LEGS],
            ItemType.WEAPON: [EquipmentSlot.WEAPON_1, EquipmentSlot.WEAPON_2],
            ItemType.RING: [EquipmentSlot.RING_1, EquipmentSlot.RING_2],
            ItemType.AMULET: [EquipmentSlot.NECK]
        }
        return slot in compatibility.get(self.item_type, [])

class CharacterStats:
    def __init__(self):
        # Base stats (starting values)
        self.base_stats = {
            StatType.STRENGTH: 10,
            StatType.DEXTERITY: 10,
            StatType.CONSTITUTION: 10,
            StatType.PERCEPTION: 10,
            StatType.LUCK: 10
        }
        
        # Equipment bonuses will be calculated from equipped items
        self.equipment_bonuses = {stat: 0 for stat in StatType}
    
    def get_total_stat(self, stat: StatType) -> int:
        """Get the total value of a stat (base + equipment bonuses)."""
        return self.base_stats[stat] + self.equipment_bonuses[stat]
    
    def get_all_stats(self) -> Dict[StatType, Tuple[int, int, int]]:
        """Get all stats as (base, bonus, total) tuples."""
        stats = {}
        for stat in StatType:
            base = self.base_stats[stat]
            bonus = self.equipment_bonuses[stat]
            total = base + bonus
            stats[stat] = (base, bonus, total)
        return stats
    
    def update_equipment_bonuses(self, equipment_bonuses: Dict[StatType, int]):
        """Update equipment bonuses from equipped items."""
        self.equipment_bonuses = equipment_bonuses.copy()
    
    def increase_base_stat(self, stat: StatType, amount: int = 1):
        """Increase a base stat (for leveling up)."""
        self.base_stats[stat] += amount
    
    def randomize_starting_stats(self, total_points: int = 60):
        """Randomize starting stats with a total point budget."""
        # Reset to minimum values
        for stat in StatType:
            self.base_stats[stat] = 8
        
        # Distribute remaining points randomly
        remaining_points = total_points - (8 * len(StatType))
        
        for _ in range(remaining_points):
            stat = random.choice(list(StatType))
            self.base_stats[stat] += 1

class Equipment:
    def __init__(self):
        self.equipped_items: Dict[EquipmentSlot, Optional[Item]] = {
            slot: None for slot in EquipmentSlot
        }
    
    def equip_item(self, item: Item, slot: EquipmentSlot) -> bool:
        """Equip an item to a specific slot. Returns True if successful."""
        if not item.can_equip_to_slot(slot):
            return False
        
        self.equipped_items[slot] = item
        return True
    
    def unequip_item(self, slot: EquipmentSlot) -> Optional[Item]:
        """Unequip an item from a slot and return it."""
        item = self.equipped_items[slot]
        self.equipped_items[slot] = None
        return item
    
    def get_equipped_item(self, slot: EquipmentSlot) -> Optional[Item]:
        """Get the item equipped in a specific slot."""
        return self.equipped_items[slot]
    
    def get_total_stat_bonuses(self) -> Dict[StatType, int]:
        """Calculate total stat bonuses from all equipped items."""
        total_bonuses = {stat: 0 for stat in StatType}
        
        for item in self.equipped_items.values():
            if item:
                for stat, bonus in item.stat_bonuses.items():
                    total_bonuses[stat] += bonus
        
        return total_bonuses
    
    def get_equipment_summary(self) -> Dict[str, str]:
        """Get a summary of equipped items for display."""
        summary = {}
        for slot, item in self.equipped_items.items():
            if item:
                summary[slot.value] = item.name
            else:
                summary[slot.value] = "Empty"
        return summary

class ItemGenerator:
    """Generates random items for the game."""
    
    ITEM_NAMES = {
        ItemType.HELMET: ["Iron Helm", "Leather Cap", "Steel Helmet", "Mage Hood", "Warrior's Crown"],
        ItemType.ARMOUR: ["Leather Armour", "Chain Mail", "Plate Armour", "Robes", "Scale Mail"],
        ItemType.BOOTS: ["Leather Boots", "Iron Boots", "Swift Boots", "Heavy Boots", "Mage Slippers"],
        ItemType.WEAPON: ["Iron Sword", "Steel Blade", "Magic Staff", "War Hammer", "Dagger"],
        ItemType.RING: ["Ring of Power", "Lucky Ring", "Swift Ring", "Strong Ring", "Wise Ring"],
        ItemType.AMULET: ["Amulet of Strength", "Pendant of Luck", "Charm of Dexterity", "Wise Pendant"]
    }
    
    @staticmethod
    def create_item_with_stats(name: str, item_type: ItemType, stat_bonuses: Dict[StatType, int]) -> Item:
        """Create an item with specific name and stat bonuses."""
        return Item(name, item_type, stat_bonuses)
    
    @staticmethod
    def generate_random_item(item_type: ItemType, quality: int = 1) -> Item:
        """Generate a random item of the specified type and quality."""
        name = random.choice(ItemGenerator.ITEM_NAMES[item_type])
        
        # Generate random stat bonuses based on quality
        num_bonuses = min(quality, 3)  # Max 3 different stat bonuses
        stats_to_bonus = random.sample(list(StatType), num_bonuses)
        
        stat_bonuses = {}
        for stat in stats_to_bonus:
            bonus = random.randint(1, quality + 1)
            stat_bonuses[stat] = bonus
        
        return Item(name, item_type, stat_bonuses)
    
    @staticmethod
    def generate_starting_equipment() -> Equipment:
        """Generate basic starting equipment for a new character."""
        equipment = Equipment()
        
        # Give some basic starting gear
        starting_items = [
            (ItemGenerator.generate_random_item(ItemType.WEAPON, 1), EquipmentSlot.WEAPON_1),
            (ItemGenerator.generate_random_item(ItemType.ARMOUR, 1), EquipmentSlot.TORSO)
        ]
        
        for item, slot in starting_items:
            equipment.equip_item(item, slot)
        
        return equipment

class Character:
    def __init__(self, name: str = "Hero"):
        self.name = name
        self.level = 1
        self.experience = 0
        self.stats = CharacterStats()
        self.equipment = Equipment()
        
        # Perk system integration
        self.perk_points = 0
        self.perk_bonuses = {}  # Store perk-based bonuses
        self.character_class = None  # Will be set when class is selected
        
        # Generate starting character
        self.stats.randomize_starting_stats()
        self.equipment = ItemGenerator.generate_starting_equipment()
        self._update_equipment_bonuses()
        
        # Health system
        self.max_hp = self._calculate_max_hp()
        self.current_hp = self.max_hp
        self.last_damage_time = 0
        
        # Regeneration system
        self.regen_timer = 0  # Tracks turns for regeneration timing
    
    def set_character_class(self, character_class):
        """Set the character's class (for perk system)."""
        self.character_class = character_class
    
    def gain_experience(self, amount: int) -> List[str]:
        """Gain experience and check for level ups. Returns list of level up messages."""
        from .perk_system import PerkSystem
        
        # Apply experience gain bonuses from perks
        exp_bonus = self.get_perk_bonus("experience_gain")
        if exp_bonus > 0:
            amount = int(amount * (1.0 + exp_bonus))
        
        self.experience += amount
        
        # Check for level ups
        level_up_messages = []
        perk_system = PerkSystem()
        
        while perk_system.check_level_up(self):
            level_up_messages.append(f"Level up! You are now level {self.level}")
            level_up_messages.append(f"Gained 2 perk points! Total: {self.perk_points}")
            
        return level_up_messages
    
    def get_perk_bonus(self, bonus_type: str) -> float:
        """Get total perk bonus for a specific type."""
        return self.perk_bonuses.get(bonus_type, 0.0)
    
    def apply_perk_bonus(self, bonus_type: str, value: float):
        """Apply a perk bonus."""
        if bonus_type not in self.perk_bonuses:
            self.perk_bonuses[bonus_type] = 0.0
        self.perk_bonuses[bonus_type] += value
    
    def _update_equipment_bonuses(self):
        """Update character stats based on equipped items."""
        bonuses = self.equipment.get_total_stat_bonuses()
        self.stats.update_equipment_bonuses(bonuses)
        
        # Update max HP when stats change
        old_max = self.max_hp if hasattr(self, 'max_hp') else 0
        new_max = self._calculate_max_hp()
        
        if hasattr(self, 'current_hp') and old_max > 0:
            # Maintain HP percentage when max changes
            hp_percentage = self.current_hp / old_max
            self.current_hp = int(new_max * hp_percentage)
        else:
            self.current_hp = new_max
        
        self.max_hp = new_max
    
    def equip_item(self, item: Item, slot: EquipmentSlot) -> bool:
        """Equip an item and update stats."""
        success = self.equipment.equip_item(item, slot)
        if success:
            self._update_equipment_bonuses()
        return success
    
    def unequip_item(self, slot: EquipmentSlot) -> Optional[Item]:
        """Unequip an item and update stats."""
        item = self.equipment.unequip_item(slot)
        if item:
            self._update_equipment_bonuses()
        return item
    
    def get_sight_range(self) -> int:
        """Calculate sight range based on Perception stat and perks."""
        perception = self.stats.get_total_stat(StatType.PERCEPTION)
        base_range = 6
        perception_bonus = max(0, (perception - 10) // 2)  # +1 range per 2 perception above 10
        
        # Apply perk bonuses
        perk_sight_bonus = self.get_perk_bonus("sight_range")
        dungeon_sight_bonus = self.get_perk_bonus("dungeon_sight")
        perception_sight_bonus = self.get_perk_bonus("perception_sight")
        
        # Enhanced perception bonus from mage perk
        if perception_sight_bonus > 0:
            perception_bonus = int(perception_bonus * (1.0 + perception_sight_bonus))
        
        total_range = base_range + perception_bonus + int(perk_sight_bonus) + int(dungeon_sight_bonus)
        return max(1, total_range)
    
    def _calculate_max_hp(self) -> int:
        """Calculate maximum HP based on Constitution, level, and perks."""
        constitution = self.stats.get_total_stat(StatType.CONSTITUTION)
        base_hp = 20  # Base HP at level 1
        con_bonus = max(0, (constitution - 10) * 2)  # +2 HP per point above 10
        level_bonus = (self.level - 1) * 5  # +5 HP per level
        
        # Apply perk bonuses
        perk_hp_bonus = self.get_perk_bonus("max_hp")
        
        total_hp = base_hp + con_bonus + level_bonus + int(perk_hp_bonus)
        return max(1, total_hp)
    
    def take_damage(self, damage: int) -> bool:
        """Apply damage to character. Returns True if character dies."""
        # Apply damage reduction from perks
        damage_reduction = self.get_perk_bonus("damage_reduction")
        
        # Apply mana shield (mage perk)
        if self.get_perk_bonus("mana_shield") > 0:
            perception = self.stats.get_total_stat(StatType.PERCEPTION)
            damage_reduction += perception // 4
        
        # Ensure minimum 1 damage
        final_damage = max(1, damage - int(damage_reduction))
        
        self.current_hp = max(0, self.current_hp - final_damage)
        self.last_damage_time = 0
        return self.current_hp <= 0
    
    def heal(self, amount: int):
        """Heal the character."""
        self.current_hp = min(self.max_hp, self.current_hp + amount)
    
    def process_regeneration(self):
        """Process HP regeneration based on constitution and perks."""
        # Only regenerate if not at full health
        if self.current_hp >= self.max_hp:
            return 0
        
        self.regen_timer += 1
        
        # Calculate regeneration rate and amount
        regen_rate, regen_amount = self._calculate_regeneration()
        
        # Check if it's time to regenerate
        if regen_rate > 0 and self.regen_timer >= regen_rate:
            self.heal(regen_amount)
            self.regen_timer = 0  # Reset timer
            return regen_amount
        
        return 0
    
    def _calculate_regeneration(self) -> Tuple[int, int]:
        """Calculate regeneration rate (turns between heals) and amount per heal.
        Returns (rate_in_turns, heal_amount)"""
        
        # Base regeneration from constitution (very slow)
        constitution = self.stats.get_total_stat(StatType.CONSTITUTION)
        base_rate = 0  # No base regeneration without perks
        base_amount = 0
        
        # Constitution provides slight regeneration bonus (slow natural healing)
        if constitution >= 15:
            base_rate = 20  # Every 20 turns
            base_amount = 1
        elif constitution >= 12:
            base_rate = 30  # Every 30 turns  
            base_amount = 1
        
        # Check for Regeneration perk
        regen_perk_bonus = self.get_perk_bonus("health_regen")
        perk_rate = 0
        perk_amount = 0
        
        if regen_perk_bonus > 0:
            # Regeneration perk: 1 HP per 10 turns per rank
            perk_rate = max(1, 10 // int(regen_perk_bonus))  # Faster with higher ranks
            perk_amount = int(regen_perk_bonus)
        
        # Check for Blessed Recovery perk (constitution enhancement)
        blessed_recovery_bonus = self.get_perk_bonus("blessed_heal")
        if blessed_recovery_bonus > 0 and regen_perk_bonus > 0:
            # Blessed Recovery makes constitution boost regeneration
            con_bonus = max(0, (constitution - 10) // 3)  # Extra heal every 3 constitution above 10
            perk_amount += int(blessed_recovery_bonus * con_bonus)
            
            # Also slightly increases rate
            rate_improvement = int(blessed_recovery_bonus * 2)
            if perk_rate > 0:
                perk_rate = max(3, perk_rate - rate_improvement)
        
        # Use the best available regeneration source
        if perk_rate > 0:
            return (perk_rate, perk_amount)
        elif base_rate > 0:
            return (base_rate, base_amount)
        else:
            return (0, 0)  # No regeneration
    
    def get_hp_percentage(self) -> float:
        """Get HP as percentage (0.0 to 1.0)."""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0
    
    def get_attack_damage(self) -> int:
        """Calculate attack damage based on Strength, equipped weapons, and perks."""
        base_damage = max(1, self.stats.get_total_stat(StatType.STRENGTH) // 2)
        
        # Add weapon damage bonuses
        weapon_bonus = 0
        weapon1 = self.equipment.get_equipped_item(EquipmentSlot.WEAPON_1)
        weapon2 = self.equipment.get_equipped_item(EquipmentSlot.WEAPON_2)
        
        if weapon1:
            weapon_damage = sum(weapon1.stat_bonuses.values())
            
            # Apply weapon-specific perk bonuses
            weapon_name = weapon1.name.lower()
            if "bow" in weapon_name and self.get_perk_bonus("bow_damage") > 0:
                weapon_damage = int(weapon_damage * (1.0 + self.get_perk_bonus("bow_damage")))
            elif "staff" in weapon_name and self.get_perk_bonus("spell_damage") > 0:
                perception = self.stats.get_total_stat(StatType.PERCEPTION)
                weapon_damage += perception // 2
            elif "mace" in weapon_name and self.get_perk_bonus("holy_damage") > 0:
                luck = self.stats.get_total_stat(StatType.LUCK)
                weapon_damage += luck // 3
            
            # Apply general weapon mastery
            if self.get_perk_bonus("weapon_damage") > 0:
                weapon_damage = int(weapon_damage * (1.0 + self.get_perk_bonus("weapon_damage")))
            
            weapon_bonus += weapon_damage
            
        if weapon2:
            weapon_bonus += sum(weapon2.stat_bonuses.values()) // 2  # Secondary weapon half bonus
        
        # Apply perk damage bonuses
        perk_damage_bonus = self.get_perk_bonus("damage")
        
        total_damage = base_damage + weapon_bonus + int(perk_damage_bonus)
        
        # Apply critical hit chance
        critical_chance = self.get_perk_bonus("critical_chance")
        if self.get_perk_bonus("luck_crit") > 0:
            luck = self.stats.get_total_stat(StatType.LUCK)
            critical_chance += (luck - 10) * 0.01  # +1% crit per luck above 10
        
        if critical_chance > 0 and random.random() < critical_chance:
            total_damage *= 2  # Critical hit doubles damage
        
        variance = max(1, total_damage // 3)
        return random.randint(total_damage - variance, total_damage + variance)
    
    def is_alive(self) -> bool:
        """Check if character is alive."""
        return self.current_hp > 0
    
    def get_character_summary(self) -> Dict:
        """Get a complete summary of the character for display."""
        from .perk_system import PerkSystem
        
        perk_system = PerkSystem()
        experience_to_next = perk_system.get_experience_to_next_level(self.level, self.experience)
        
        return {
            'name': self.name,
            'level': self.level,
            'experience': self.experience,
            'experience_to_next': experience_to_next,
            'perk_points': self.perk_points,
            'hp': (self.current_hp, self.max_hp),
            'stats': self.stats.get_all_stats(),
            'equipment': self.equipment.get_equipment_summary(),
            'sight_range': self.get_sight_range(),
            'perk_bonuses': self.perk_bonuses.copy()
        } 