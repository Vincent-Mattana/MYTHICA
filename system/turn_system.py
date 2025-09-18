#!/usr/bin/env python3
"""
Turn-Based System for Treasure Goblin
Handles action timing, turn scheduling, and turn-based mechanics.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
import heapq
from .character_system import StatType, ItemType

class ActionType(Enum):
    MOVE = "move"
    ATTACK = "attack"
    RANGED_ATTACK = "ranged_attack"  # For bows, crossbows, etc.
    RELOAD = "reload"
    WAIT = "wait"
    USE_ITEM = "use_item"
    OPEN_DOOR = "open_door"
    PICKUP_ITEM = "pickup_item"

class WeaponType(Enum):
    SWORD = "sword"
    DAGGER = "dagger"
    BOW = "bow"
    CROSSBOW = "crossbow"
    STAFF = "staff"
    MACE = "mace"
    UNARMED = "unarmed"

@dataclass
class Action:
    """Represents an action that can be performed by an entity."""
    action_type: ActionType
    actor_id: str  # ID of the entity performing the action
    time_cost: float  # Time cost in seconds
    target_pos: Optional[Tuple[int, int]] = None
    target_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def __lt__(self, other):
        """For heap ordering - earlier completion times have priority."""
        return self.time_cost < other.time_cost

class TurnScheduler:
    """Manages the scheduling and execution of turn-based actions."""
    
    def __init__(self):
        self.current_time = 0.0
        self.action_queue = []  # Priority queue of (completion_time, action)
        self.entity_last_action = {}  # Track when each entity last acted
        self.entity_busy = set()  # Track entities with pending actions
        self.turn_number = 0
    
    def schedule_action(self, action: Action):
        """Schedule an action to be executed."""
        completion_time = self.current_time + action.time_cost
        heapq.heappush(self.action_queue, (completion_time, action))
        # Mark entity as busy until action completes
        self.entity_busy.add(action.actor_id)
    
    def get_next_action(self) -> Optional[Tuple[float, Action]]:
        """Get the next action to execute, if any."""
        if self.action_queue:
            return heapq.heappop(self.action_queue)
        return None
    
    def advance_time_to_next_action(self):
        """Advance time to the next scheduled action."""
        if self.action_queue:
            next_time = self.action_queue[0][0]
            self.current_time = next_time
            self.turn_number += 1
    
    def can_entity_act(self, entity_id: str) -> bool:
        """Check if an entity can act (their last action has completed)."""
        # If entity is currently busy with an action, they can't act
        if entity_id in self.entity_busy:
            return False
        
        # If entity has never acted, they can act
        if entity_id not in self.entity_last_action:
            return True
        
        # Check if enough time has passed since last action
        last_action_time = self.entity_last_action[entity_id]
        return self.current_time >= last_action_time
    
    def get_entity_ready_time(self, entity_id: str) -> float:
        """Get when an entity will be ready to act again."""
        return self.entity_last_action.get(entity_id, 0.0)
    
    def clear_entity_actions(self, entity_id: str):
        """Remove all pending actions for an entity (e.g., when they die)."""
        self.action_queue = [(time, action) for time, action in self.action_queue 
                           if action.actor_id != entity_id]
        heapq.heapify(self.action_queue)
        self.entity_busy.discard(entity_id)

class ActionCosts:
    """Defines time costs for different actions and weapons."""
    
    # Base action costs (in seconds)
    BASE_COSTS = {
        ActionType.MOVE: 1.0,
        ActionType.WAIT: 1.0,
        ActionType.ATTACK: 1.0,
        ActionType.RANGED_ATTACK: 1.2,  # Ranged attacks take longer
        ActionType.RELOAD: 1.0,
        ActionType.USE_ITEM: 0.5,
        ActionType.OPEN_DOOR: 0.5,
        ActionType.PICKUP_ITEM: 0.5
    }
    
    # Weapon-specific modifiers
    WEAPON_ATTACK_MODIFIERS = {
        WeaponType.SWORD: 1.0,      # 1.0 seconds
        WeaponType.DAGGER: 0.7,     # 0.7 seconds (fast)
        WeaponType.BOW: 0.8,        # 0.8 seconds
        WeaponType.CROSSBOW: 1.2,   # 1.2 seconds (slow but powerful)
        WeaponType.STAFF: 1.1,      # 1.1 seconds
        WeaponType.MACE: 1.3,       # 1.3 seconds (heavy)
        WeaponType.UNARMED: 0.5     # 0.5 seconds (very fast but weak)
    }
    
    # Weapon reload times
    WEAPON_RELOAD_TIMES = {
        WeaponType.SWORD: 0.0,      # No reload
        WeaponType.DAGGER: 0.0,     # No reload
        WeaponType.BOW: 0.5,        # 0.5 seconds to nock arrow
        WeaponType.CROSSBOW: 2.0,   # 2.0 seconds to reload bolt
        WeaponType.STAFF: 0.0,      # No reload
        WeaponType.MACE: 0.0,       # No reload
        WeaponType.UNARMED: 0.0     # No reload
    }
    
    # Movement modifiers based on dexterity
    @staticmethod
    def get_movement_cost(dexterity: int) -> float:
        """Calculate movement cost based on dexterity."""
        base_cost = ActionCosts.BASE_COSTS[ActionType.MOVE]
        # Higher dexterity = faster movement (minimum 0.5 seconds)
        dex_modifier = max(0.5, 1.0 - (dexterity - 10) * 0.02)
        return base_cost * dex_modifier
    
    @staticmethod
    def get_attack_cost(weapon_type: WeaponType, dexterity: int) -> float:
        """Calculate attack cost based on weapon and dexterity."""
        base_cost = ActionCosts.BASE_COSTS[ActionType.ATTACK]
        weapon_modifier = ActionCosts.WEAPON_ATTACK_MODIFIERS.get(weapon_type, 1.0)
        dex_modifier = max(0.7, 1.0 - (dexterity - 10) * 0.01)  # Dex affects attack speed
        return base_cost * weapon_modifier * dex_modifier
    
    @staticmethod
    def get_reload_cost(weapon_type: WeaponType, dexterity: int) -> float:
        """Calculate reload cost based on weapon and dexterity."""
        base_reload = ActionCosts.WEAPON_RELOAD_TIMES.get(weapon_type, 0.0)
        if base_reload == 0.0:
            return 0.0  # No reload needed
        
        dex_modifier = max(0.7, 1.0 - (dexterity - 10) * 0.015)  # Dex affects reload speed
        return base_reload * dex_modifier
    
    @staticmethod
    def get_weapon_type_from_name(weapon_name: str) -> WeaponType:
        """Determine weapon type from weapon name."""
        weapon_name_lower = weapon_name.lower()
        
        if any(word in weapon_name_lower for word in ['sword', 'blade']):
            return WeaponType.SWORD
        elif any(word in weapon_name_lower for word in ['dagger', 'knife']):
            return WeaponType.DAGGER
        elif 'bow' in weapon_name_lower and 'cross' not in weapon_name_lower:
            return WeaponType.BOW
        elif 'crossbow' in weapon_name_lower:
            return WeaponType.CROSSBOW
        elif any(word in weapon_name_lower for word in ['staff', 'wand', 'rod']):
            return WeaponType.STAFF
        elif any(word in weapon_name_lower for word in ['mace', 'hammer', 'club']):
            return WeaponType.MACE
        else:
            return WeaponType.SWORD  # Default fallback

class TurnManager:
    """High-level manager for turn-based gameplay."""
    
    def __init__(self):
        self.scheduler = TurnScheduler()
        self.waiting_for_player = True
        self.player_can_act = True
        
        # Weapon state tracking
        self.weapon_loaded = {}  # entity_id -> bool
        self.weapon_types = {}   # entity_id -> WeaponType
    
    def set_entity_weapon(self, entity_id: str, weapon_name: str):
        """Set the weapon type for an entity."""
        weapon_type = ActionCosts.get_weapon_type_from_name(weapon_name)
        self.weapon_types[entity_id] = weapon_type
        # Most weapons start loaded, crossbows might not
        self.weapon_loaded[entity_id] = weapon_type != WeaponType.CROSSBOW
    
    def get_entity_weapon_type(self, entity_id: str) -> WeaponType:
        """Get the weapon type for an entity."""
        return self.weapon_types.get(entity_id, WeaponType.UNARMED)
    
    def is_weapon_loaded(self, entity_id: str) -> bool:
        """Check if an entity's weapon is loaded."""
        return self.weapon_loaded.get(entity_id, True)
    
    def reload_weapon(self, entity_id: str):
        """Mark an entity's weapon as loaded."""
        self.weapon_loaded[entity_id] = True
    
    def fire_weapon(self, entity_id: str):
        """Mark an entity's weapon as needing reload (for ranged weapons)."""
        weapon_type = self.get_entity_weapon_type(entity_id)
        if weapon_type in [WeaponType.BOW, WeaponType.CROSSBOW]:
            self.weapon_loaded[entity_id] = False
    
    def can_player_act(self) -> bool:
        """Check if the player can take an action."""
        return self.player_can_act and self.scheduler.can_entity_act("player")
    
    def schedule_player_action(self, action_type: ActionType, target_pos: Optional[Tuple[int, int]] = None, 
                             target_id: Optional[str] = None, dexterity: int = 10, **kwargs) -> bool:
        """Schedule a player action and return whether it was successful."""
        if not self.can_player_act():
            return False
        
        # Calculate time cost based on action type
        time_cost = self._calculate_action_cost(action_type, "player", dexterity, **kwargs)
        
        action = Action(
            action_type=action_type,
            actor_id="player",
            time_cost=time_cost,
            target_pos=target_pos,
            target_id=target_id,
            data=kwargs
        )
        
        self.scheduler.schedule_action(action)
        self.player_can_act = False
        self.waiting_for_player = False
        
        return True
    
    def schedule_enemy_action(self, enemy_id: str, action_type: ActionType, 
                            target_pos: Optional[Tuple[int, int]] = None,
                            target_id: Optional[str] = None, dexterity: int = 10, **kwargs):
        """Schedule an enemy action."""
        time_cost = self._calculate_action_cost(action_type, enemy_id, dexterity, **kwargs)
        
        action = Action(
            action_type=action_type,
            actor_id=enemy_id,
            time_cost=time_cost,
            target_pos=target_pos,
            target_id=target_id,
            data=kwargs
        )
        
        self.scheduler.schedule_action(action)
    
    def _calculate_action_cost(self, action_type: ActionType, entity_id: str, dexterity: int, **kwargs) -> float:
        """Calculate the time cost for an action."""
        if action_type == ActionType.MOVE:
            return ActionCosts.get_movement_cost(dexterity)
        elif action_type == ActionType.ATTACK:
            weapon_type = self.get_entity_weapon_type(entity_id)
            return ActionCosts.get_attack_cost(weapon_type, dexterity)
        elif action_type == ActionType.RELOAD:
            weapon_type = self.get_entity_weapon_type(entity_id)
            return ActionCosts.get_reload_cost(weapon_type, dexterity)
        else:
            return ActionCosts.BASE_COSTS.get(action_type, 1.0)
    
    def process_next_action(self) -> Optional[Tuple[float, Action]]:
        """Process the next action in the queue."""
        next_action = self.scheduler.get_next_action()
        if next_action:
            completion_time, action = next_action
            self.scheduler.current_time = completion_time
            
            # Mark when this entity finished their action
            self.scheduler.entity_last_action[action.actor_id] = completion_time
            # Entity is no longer busy
            self.scheduler.entity_busy.discard(action.actor_id)
            
            # Increment turn counter when processing actions
            self.scheduler.turn_number += 1
            
            # If it was a player action, they can act again
            if action.actor_id == "player":
                self.player_can_act = True
                self.waiting_for_player = True
            else:
                # If it was an enemy action, ensure we don't wait for player
                self.waiting_for_player = False
            
            return next_action
        return None
    
    def get_turn_info(self) -> Dict[str, Any]:
        """Get information about the current turn state."""
        return {
            'current_time': self.scheduler.current_time,
            'turn_number': self.scheduler.turn_number,
            'waiting_for_player': self.waiting_for_player,
            'player_can_act': self.can_player_act(),
            'next_action_time': self.scheduler.action_queue[0][0] if self.scheduler.action_queue else None,
            'actions_queued': len(self.scheduler.action_queue)
        }
    
    def get_entity_status(self, entity_id: str) -> Dict[str, Any]:
        """Get status information for a specific entity."""
        weapon_type = self.get_entity_weapon_type(entity_id)
        return {
            'can_act': self.scheduler.can_entity_act(entity_id),
            'ready_time': self.scheduler.get_entity_ready_time(entity_id),
            'weapon_type': weapon_type.value,
            'weapon_loaded': self.is_weapon_loaded(entity_id)
        }
    
    def remove_entity(self, entity_id: str):
        """Remove an entity from the turn system (when they die)."""
        self.scheduler.clear_entity_actions(entity_id)
        if entity_id in self.weapon_loaded:
            del self.weapon_loaded[entity_id]
        if entity_id in self.weapon_types:
            del self.weapon_types[entity_id] 