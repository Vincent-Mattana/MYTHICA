from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
import json

from .character_system import StatType, Character
from .game_states import CharacterClass


class PerkCategory(Enum):
    """Categories of perks available to characters."""
    COMBAT = "combat"
    SURVIVAL = "survival"
    UTILITY = "utility"
    WARRIOR_SPEC = "warrior_specialization"
    ROGUE_SPEC = "rogue_specialization"
    MAGE_SPEC = "mage_specialization"
    RANGER_SPEC = "ranger_specialization"
    CLERIC_SPEC = "cleric_specialization"


class PerkType(Enum):
    """Types of perk effects."""
    STAT_BONUS = "stat_bonus"
    PERCENTAGE_BONUS = "percentage_bonus"
    SPECIAL_ABILITY = "special_ability"
    PASSIVE_EFFECT = "passive_effect"


@dataclass
class PerkEffect:
    """Defines the effect of a perk."""
    perk_type: PerkType
    target: str  # What the perk affects (stat name, ability name, etc.)
    value: float  # The magnitude of the effect
    description: str  # Human-readable description


@dataclass
class Perk:
    """Defines a perk that can be learned by characters."""
    id: str
    name: str
    description: str
    category: PerkCategory
    prerequisites: List[str]  # List of required perk IDs
    max_rank: int  # Maximum times this perk can be taken
    cost_per_rank: int  # Perk points required per rank
    class_restricted: Optional[CharacterClass]  # None means available to all
    effects: List[PerkEffect]
    
    def can_be_learned(self, character_class: CharacterClass, current_perks: Dict[str, int], available_points: int) -> bool:
        """Check if this perk can be learned by the character."""
        # Check class restriction
        if self.class_restricted and self.class_restricted != character_class:
            return False
            
        # Check if already at max rank
        current_rank = current_perks.get(self.id, 0)
        if current_rank >= self.max_rank:
            return False
            
        # Check perk points
        if available_points < self.cost_per_rank:
            return False
            
        # Check prerequisites
        for prereq_id in self.prerequisites:
            if prereq_id not in current_perks:
                return False
                
        return True


class PerkSystem:
    """Manages character perks and specialization trees."""
    
    def __init__(self):
        self.perks = self._initialize_perks()
    
    def _initialize_perks(self) -> Dict[str, Perk]:
        """Initialize all available perks."""
        perks = {}
        
        # === UNIVERSAL COMBAT PERKS ===
        perks["power_attack"] = Perk(
            id="power_attack",
            name="Power Attack",
            description="Increases base attack damage by 2 per rank",
            category=PerkCategory.COMBAT,
            prerequisites=[],
            max_rank=3,
            cost_per_rank=1,
            class_restricted=None,
            effects=[PerkEffect(PerkType.STAT_BONUS, "damage", 2.0, "+2 base damage")]
        )
        
        perks["combat_reflexes"] = Perk(
            id="combat_reflexes",
            name="Combat Reflexes",
            description="Reduces action time by 5% per rank",
            category=PerkCategory.COMBAT,
            prerequisites=[],
            max_rank=3,
            cost_per_rank=1,
            class_restricted=None,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "action_speed", 0.05, "-5% action time")]
        )
        
        perks["critical_strike"] = Perk(
            id="critical_strike",
            name="Critical Strike",
            description="5% chance per rank to deal double damage",
            category=PerkCategory.COMBAT,
            prerequisites=["power_attack"],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=None,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "critical_chance", 0.05, "+5% critical hit chance")]
        )
        
        # === UNIVERSAL SURVIVAL PERKS ===
        perks["toughness"] = Perk(
            id="toughness",
            name="Toughness",
            description="Increases maximum health by 5 per rank",
            category=PerkCategory.SURVIVAL,
            prerequisites=[],
            max_rank=5,
            cost_per_rank=1,
            class_restricted=None,
            effects=[PerkEffect(PerkType.STAT_BONUS, "max_hp", 5.0, "+5 maximum health")]
        )
        
        perks["regeneration"] = Perk(
            id="regeneration",
            name="Regeneration",
            description="Slowly regenerate health over time",
            category=PerkCategory.SURVIVAL,
            prerequisites=["toughness"],
            max_rank=3,
            cost_per_rank=2,
            class_restricted=None,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "health_regen", 1.0, "Regenerate 1 HP per 10 turns")]
        )
        
        perks["damage_resistance"] = Perk(
            id="damage_resistance",
            name="Damage Resistance",
            description="Reduces incoming damage by 1 per rank",
            category=PerkCategory.SURVIVAL,
            prerequisites=["toughness"],
            max_rank=3,
            cost_per_rank=2,
            class_restricted=None,
            effects=[PerkEffect(PerkType.STAT_BONUS, "damage_reduction", 1.0, "-1 incoming damage")]
        )
        
        # === UNIVERSAL UTILITY PERKS ===
        perks["keen_senses"] = Perk(
            id="keen_senses",
            name="Keen Senses",
            description="Increases sight range by 1 per rank",
            category=PerkCategory.UTILITY,
            prerequisites=[],
            max_rank=3,
            cost_per_rank=1,
            class_restricted=None,
            effects=[PerkEffect(PerkType.STAT_BONUS, "sight_range", 1.0, "+1 sight range")]
        )
        
        perks["fast_learner"] = Perk(
            id="fast_learner",
            name="Fast Learner",
            description="Gain 10% more experience per rank",
            category=PerkCategory.UTILITY,
            prerequisites=[],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=None,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "experience_gain", 0.10, "+10% experience gain")]
        )
        
        # === WARRIOR SPECIALIZATION ===
        perks["weapon_mastery"] = Perk(
            id="weapon_mastery",
            name="Weapon Mastery",
            description="Increases weapon damage by 25% per rank",
            category=PerkCategory.WARRIOR_SPEC,
            prerequisites=[],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.WARRIOR,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "weapon_damage", 0.25, "+25% weapon damage")]
        )
        
        perks["berserker_rage"] = Perk(
            id="berserker_rage",
            name="Berserker Rage",
            description="Attack speed increases as health decreases",
            category=PerkCategory.WARRIOR_SPEC,
            prerequisites=["weapon_mastery"],
            max_rank=1,
            cost_per_rank=3,
            class_restricted=CharacterClass.WARRIOR,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "berserker_rage", 1.0, "Attack speed +50% when below 25% HP")]
        )
        
        perks["armor_expertise"] = Perk(
            id="armor_expertise",
            name="Armour Expertise",
            description="Reduces equipment weight penalties and increases armour effectiveness",
            category=PerkCategory.WARRIOR_SPEC,
            prerequisites=["weapon_mastery"],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.WARRIOR,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "armor_bonus", 0.5, "+50% armour stat bonuses")]
        )
        
        # === ROGUE SPECIALIZATION ===
        perks["stealth"] = Perk(
            id="stealth",
            name="Stealth",
            description="Enemies are less likely to detect you",
            category=PerkCategory.ROGUE_SPEC,
            prerequisites=[],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.ROGUE,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "stealth_chance", 0.3, "+30% stealth effectiveness")]
        )
        
        perks["backstab"] = Perk(
            id="backstab",
            name="Backstab",
            description="Attacks from behind deal extra damage",
            category=PerkCategory.ROGUE_SPEC,
            prerequisites=["stealth"],
            max_rank=2,
            cost_per_rank=3,
            class_restricted=CharacterClass.ROGUE,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "backstab_damage", 1.0, "+100% damage from behind")]
        )
        
        perks["lucky_strike"] = Perk(
            id="lucky_strike",
            name="Lucky Strike",
            description="Luck influences critical hit chance and damage",
            category=PerkCategory.ROGUE_SPEC,
            prerequisites=[],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.ROGUE,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "luck_crit", 1.0, "Luck stat affects critical chance")]
        )
        
        # === MAGE SPECIALIZATION ===
        perks["arcane_knowledge"] = Perk(
            id="arcane_knowledge",
            name="Arcane Knowledge",
            description="Increases perception-based sight range bonus",
            category=PerkCategory.MAGE_SPEC,
            prerequisites=[],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.MAGE,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "perception_sight", 0.5, "+50% perception sight bonus")]
        )
        
        perks["mana_shield"] = Perk(
            id="mana_shield",
            name="Mana Shield",
            description="Reduces damage based on Perception stat",
            category=PerkCategory.MAGE_SPEC,
            prerequisites=["arcane_knowledge"],
            max_rank=1,
            cost_per_rank=3,
            class_restricted=CharacterClass.MAGE,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "mana_shield", 1.0, "Reduce damage by Perception/4")]
        )
        
        perks["spell_power"] = Perk(
            id="spell_power",
            name="Spell Power",
            description="Staff weapons gain bonus damage from Perception",
            category=PerkCategory.MAGE_SPEC,
            prerequisites=["arcane_knowledge"],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.MAGE,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "spell_damage", 1.0, "Staff damage +Perception/2")]
        )
        
        # === RANGER SPECIALIZATION ===
        perks["nature_lore"] = Perk(
            id="nature_lore",
            name="Nature Lore",
            description="Enhanced perception in natural environments",
            category=PerkCategory.RANGER_SPEC,
            prerequisites=[],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.RANGER,
            effects=[PerkEffect(PerkType.STAT_BONUS, "dungeon_sight", 2.0, "+2 sight range in dungeons")]
        )
        
        perks["precise_shot"] = Perk(
            id="precise_shot",
            name="Precise Shot",
            description="Bow weapons have increased accuracy and damage",
            category=PerkCategory.RANGER_SPEC,
            prerequisites=["nature_lore"],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.RANGER,
            effects=[PerkEffect(PerkType.PERCENTAGE_BONUS, "bow_damage", 0.4, "+40% bow weapon damage")]
        )
        
        perks["tracking"] = Perk(
            id="tracking",
            name="Tracking",
            description="Can sense nearby enemies even when not visible",
            category=PerkCategory.RANGER_SPEC,
            prerequisites=["nature_lore"],
            max_rank=1,
            cost_per_rank=3,
            class_restricted=CharacterClass.RANGER,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "enemy_sense", 3.0, "Sense enemies within 3 tiles")]
        )
        
        # === CLERIC SPECIALIZATION ===
        perks["divine_favour"] = Perk(
            id="divine_favour",
            name="Divine Favour",
            description="Luck affects all beneficial random events",
            category=PerkCategory.CLERIC_SPEC,
            prerequisites=[],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.CLERIC,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "divine_luck", 1.0, "Luck affects all positive outcomes")]
        )
        
        perks["blessed_recovery"] = Perk(
            id="blessed_recovery",
            name="Blessed Recovery",
            description="Constitution provides enhanced healing effects",
            category=PerkCategory.CLERIC_SPEC,
            prerequisites=["divine_favour"],
            max_rank=2,
            cost_per_rank=2,
            class_restricted=CharacterClass.CLERIC,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "blessed_heal", 1.0, "Constitution boosts regeneration")]
        )
        
        perks["holy_strength"] = Perk(
            id="holy_strength",
            name="Holy Strength",
            description="Mace weapons gain damage from both Strength and Luck",
            category=PerkCategory.CLERIC_SPEC,
            prerequisites=["divine_favour"],
            max_rank=1,
            cost_per_rank=3,
            class_restricted=CharacterClass.CLERIC,
            effects=[PerkEffect(PerkType.SPECIAL_ABILITY, "holy_damage", 1.0, "Mace damage +Luck/3")]
        )
        
        return perks
    
    def get_available_perks(self, character_class: CharacterClass, current_perks: Dict[str, int], available_points: int) -> List[Perk]:
        """Get all perks that can currently be learned."""
        available = []
        for perk in self.perks.values():
            if perk.can_be_learned(character_class, current_perks, available_points):
                available.append(perk)
        return available
    
    def get_perks_by_category(self, category: PerkCategory) -> List[Perk]:
        """Get all perks in a specific category."""
        return [perk for perk in self.perks.values() if perk.category == category]
    
    def get_perk(self, perk_id: str) -> Optional[Perk]:
        """Get a specific perk by ID."""
        return self.perks.get(perk_id)
    
    def calculate_experience_required(self, level: int) -> int:
        """Calculate experience required to reach a given level."""
        if level <= 1:
            return 0
        # Experience formula: 100 for level 2, then scales up
        if level == 2:
            return 100
        # After level 2: 100 * (level-1)^1.5 (rounded)
        return int(100 * ((level-1) ** 1.5))
    
    def get_experience_to_next_level(self, current_level: int, current_exp: int) -> int:
        """Get experience needed for next level."""
        next_level_exp = self.calculate_experience_required(current_level + 1)
        return max(0, next_level_exp - current_exp)
    
    def check_level_up(self, character: Character) -> bool:
        """Check if character should level up and apply if so."""
        next_level_exp = self.calculate_experience_required(character.level + 1)
        if character.experience >= next_level_exp:
            character.level += 1
            # Grant 2 perk points per level (stored as new attribute)
            if not hasattr(character, 'perk_points'):
                character.perk_points = 0
            character.perk_points += 2
            
            # Update max HP for new level
            old_max = character.max_hp
            character.max_hp = character._calculate_max_hp()
            # Grant full heal on level up
            character.current_hp = character.max_hp
            
            return True
        return False


class CharacterPerks:
    """Manages perks for a specific character."""
    
    def __init__(self, character: Character):
        self.character = character
        self.learned_perks: Dict[str, int] = {}  # perk_id -> rank
        self.perk_system = PerkSystem()
        
        # Initialize perk points if not present
        if not hasattr(character, 'perk_points'):
            character.perk_points = 0
    
    def learn_perk(self, perk_id: str) -> bool:
        """Learn a perk if possible."""
        perk = self.perk_system.get_perk(perk_id)
        if not perk:
            return False
        
        # Get character class
        character_class = getattr(self.character, 'character_class', CharacterClass.WARRIOR)
            
        if not perk.can_be_learned(character_class, self.learned_perks, self.character.perk_points):
            return False
            
        # Deduct perk points
        self.character.perk_points -= perk.cost_per_rank
        
        # Add perk rank
        self.learned_perks[perk_id] = self.learned_perks.get(perk_id, 0) + 1
        
        # Apply perk effects
        self._apply_perk_effects(perk)
        
        return True
    
    def _apply_perk_effects(self, perk: Perk):
        """Apply the effects of a learned perk."""
        current_rank = self.learned_perks.get(perk.id, 1)
        
        for effect in perk.effects:
            if effect.perk_type in [PerkType.STAT_BONUS, PerkType.PERCENTAGE_BONUS, PerkType.SPECIAL_ABILITY]:
                # Apply all bonus types through the perk bonus system
                if not hasattr(self.character, 'perk_bonuses'):
                    self.character.perk_bonuses = {}
                
                if effect.target not in self.character.perk_bonuses:
                    self.character.perk_bonuses[effect.target] = 0.0
                    
                self.character.perk_bonuses[effect.target] += effect.value
    
    def get_perk_bonus(self, bonus_type: str) -> float:
        """Get total perk bonus for a specific type."""
        if not hasattr(self.character, 'perk_bonuses'):
            return 0.0
        return self.character.perk_bonuses.get(bonus_type, 0.0)
    
    def has_perk(self, perk_id: str) -> bool:
        """Check if character has learned a specific perk."""
        return perk_id in self.learned_perks
    
    def get_perk_rank(self, perk_id: str) -> int:
        """Get the rank of a learned perk."""
        return self.learned_perks.get(perk_id, 0)
    
    def get_available_perks(self) -> List[Perk]:
        """Get perks available to learn."""
        # Determine character class from the character instance
        character_class = getattr(self.character, 'character_class', None)
        if not character_class:
            # Try to infer from stats - this is a fallback
            character_class = CharacterClass.WARRIOR  # Default assumption
            
        return self.perk_system.get_available_perks(
            character_class, 
            self.learned_perks, 
            self.character.perk_points
        )
    
    def get_character_summary(self) -> Dict:
        """Get character summary including perk information."""
        base_summary = self.character.get_character_summary()
        base_summary.update({
            'perk_points': getattr(self.character, 'perk_points', 0),
            'learned_perks': self.learned_perks.copy(),
            'available_perks': len(self.get_available_perks())
        })
        return base_summary 