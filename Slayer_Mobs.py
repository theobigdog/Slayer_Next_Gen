"""
Generic mob factory for random encounters.
For unique bosses, use dedicated modules (Slayer_Dwarf.py, etc.)
"""

import random
from colorama import Fore, Style

class Mob:
    """Generic mob class for random encounters."""
    
    def __init__(self, mob_species='goblin', mob_type='regular', creature_type='living'):
        """
        Initialize a generic mob.
        
        Args:
            mob_species: Type of creature (goblin, orc, bandit, etc.)
            mob_type: Difficulty tier (minion, regular, elite, boss)
            creature_type: Living status (living, undead, construct, elemental)
        """
        self.mob_species = mob_species
        self.mob_type = mob_type
        self.creature_type = creature_type  # <-- NEW!
        self.name = self._generate_name()
        self.mob_class = mob_species.capitalize()  # <-- ADD THIS for display
        
        # Base stats by type
        self.stats = self._get_base_stats()
        
        # Health
        self.starting_health = self._calculate_health()
        self.health = self.starting_health
        
        # Combat flags
        self.enraged = False
        self.defending = False
        self.defend_bonus = 0
    
    def _generate_name(self):
        """Generate a name for this mob."""
        prefixes = {
            'goblin': ['Sneaky', 'Vicious', 'Mangy', 'Feral', 'Rabid'],
            'orc': ['Brutal', 'Savage', 'Bloodthirsty', 'Fierce', 'Cruel'],
            'bandit': ['Shifty', 'Cunning', 'Ruthless', 'Desperate', 'Greedy'],
            'skeleton': ['Dusty', 'Ancient', 'Rattling', 'Cursed', 'Undead'],
            'zombie': ['Rotting', 'Shambling', 'Putrid', 'Decaying', 'Festering'],  # NEW
            'wraith': ['Spectral', 'Ethereal', 'Ghostly', 'Haunting', 'Vengeful'],  # NEW
            'lich': ['Dark', 'Unholy', 'Cursed', 'Eternal', 'Dread'],  # NEW
            'necromancer': ['Dark', 'Vile', 'Corrupted', 'Malevolent', 'Sinister'],  # NEW!
            'wolf': ['Hungry', 'Feral', 'Pack', 'Wild', 'Howling'],
        }
        
        titles = {
            'minion': ['Grunt', 'Scrapper', 'Peon', 'Weakling', 'Lackey'],
            'regular': ['Warrior', 'Fighter', 'Soldier', 'Raider', 'Marauder'],
            'elite': ['Champion', 'Veteran', 'Berserker', 'Warlord', 'Captain'],
            'boss': ['Chieftain', 'King', 'Lord', 'Overlord', 'Destroyer'],
        }
        
        prefix = random.choice(prefixes.get(self.mob_species, ['Evil']))
        title = random.choice(titles.get(self.mob_type, ['Monster']))
        
        return f"{prefix} {self.mob_species.capitalize()} {title}"
    
    def _get_base_stats(self):
        """Get base stats based on mob type."""
        base_stats = {
            'minion': {
                'damage': 5,
                'expertise': 3,
                'dodge': 2,
                'parry': 2,
                'toughness': 1,
                'crit': 15,
                'crit_mult': 1.5,
                'luck': 2,
                'fear': 1,
                'low_miss': 1,
                'high_miss': 20,
            },
            'regular': {
                'damage': 10,
                'expertise': 8,
                'dodge': 5,
                'parry': 5,
                'toughness': 5,
                'crit': 12,
                'crit_mult': 2.0,
                'luck': 5,
                'fear': 5,
                'low_miss': 1,
                'high_miss': 20,
            },
            'elite': {
                'damage': 15,
                'expertise': 12,
                'dodge': 10,
                'parry': 10,
                'toughness': 10,
                'crit': 10,
                'crit_mult': 2.5,
                'luck': 10,
                'fear': 10,
                'low_miss': 1,
                'high_miss': 20,
            },
            'boss': {
                'damage': 25,
                'expertise': 18,
                'dodge': 15,
                'parry': 15,
                'toughness': 15,
                'crit': 8,
                'crit_mult': 3.0,
                'luck': 15,
                'fear': 20,
                'low_miss': 1,
                'high_miss': 20,
            },
        }
        
        return base_stats.get(self.mob_type, base_stats['regular']).copy()
    
    def _calculate_health(self):
        """Calculate starting health based on mob type."""
        health_values = {
            'minion': 30,
            'regular': 60,
            'elite': 100,
            'boss': 200,
        }
        
        return health_values.get(self.mob_type, 60)


# ============================================================================
# TWO-PHASE RESURRECTION BOSS
# ============================================================================

class NecromancerKing(Mob):
    """
    A powerful necromancer boss with TWO PHASES:
    
    PHASE 1 (Living): Normal boss fight - powerful caster
    PHASE 2 (Undead Lich): Rises after "death" - faster, hits harder, WEAK TO HEALING
    
    This boss will "die" once, then resurrect as an undead lich!
    """
    
    def __init__(self, name="Necromancer King Valdris"):
        # Initialize as LIVING boss first
        super().__init__(
            mob_species='necromancer',
            mob_type='boss',
            creature_type='living'  # Starts as living
        )
        
        # Override the generated name
        self.name = name
        self.mob_class = "Necromancer King"
        
        # PHASE 1 STATS (Living Necromancer) - BUFFED!
        self.stats = {
            'damage': 45,           # Was 30, now 45
            'expertise': 25,        # Was 20, now 25
            'dodge': 20,            # Was 16, now 20
            'parry': 18,            # Was 14, now 18
            'toughness': 18,        # Was 14, now 18
            'crit': 6,              # Was 8, now 6 (easier to crit)
            'crit_mult': 3.0,       # Was 2.5, now 3.0
            'luck': 20,             # Was 16, now 20
            'fear': 22,             # Was 18, now 22
            'scare': 20,            # Was 16, now 20
            'speed': 18,            # Was 14, now 18
            'low_miss': 1,
            'high_miss': 20,
        }
        
        # PHASE 1 HEALTH - BUFFED!
        self.starting_health = 250  # Was 150, now 250
        self.health = 250
        
        # Track resurrection status
        self.phase = 1
        self.has_resurrected = False
        
        # PHASE 2 STATS (Undead Lich form) - BUFFED!
        self.undead_stats = {
            'damage': 60,           # Was 40, now 60
            'expertise': 30,        # Was 24, now 30
            'dodge': 25,            # Was 20, now 25
            'parry': 15,            # Was 12, now 15
            'toughness': 8,         # Was 10, now 8 (MORE vulnerable to healing!)
            'crit': 4,              # Was 6, now 4 (crits even more!)
            'crit_mult': 3.5,       # Was 3.0, now 3.5
            'luck': 25,             # Was 20, now 25
            'fear': 30,             # Was 25, now 30 (TERRIFYING!)
            'scare': 28,            # Was 22, now 28
            'speed': 22,            # Was 18, now 22
            'low_miss': 1,
            'high_miss': 20,
        }
        
        # PHASE 2 HEALTH - BUFFED!
        self.undead_health = 200  # Was 120, now 200
    
    def resurrect_as_undead(self):
        """
        Transform into undead lich form (Phase 2).
        Called when health reaches 0 for the first time.
        
        Returns:
            bool: True if resurrection succeeded
        """
        if self.has_resurrected:
            return False  # Can only resurrect once!
        
        # TRANSFORMATION!
        self.phase = 2
        self.has_resurrected = True
        self.creature_type = 'undead'  # NOW WEAK TO HEALING!
        
        # Update appearance - EXTRACT BASE NAME FIRST
        # Remove any existing titles like "the Deathless"
        base_name = self.name.split(' the ')[0] if ' the ' in self.name else self.name
        self.name = f"{base_name} the Undying"
        self.mob_class = "Undead Lich"
        
        # Swap to undead stats
        self.stats = self.undead_stats.copy()
        
        # Restore health (undead form)
        self.starting_health = self.undead_health
        self.health = self.undead_health
        
        return True

# ============================================================================
# MOB FACTORY FUNCTIONS
# ============================================================================

def create_random_encounter(difficulty='easy'):
    """
    Create a random mob encounter.
    
    Args:
        difficulty: 'easy', 'medium', 'hard', 'deadly', 'undead_easy', 'undead_medium', 'undead_hard'
        
    Returns:
        list: List of Mob objects
    """
    encounters = {
        'easy': [
            [Mob('goblin', 'minion'), Mob('goblin', 'minion')],
            [Mob('wolf', 'minion'), Mob('wolf', 'minion'), Mob('wolf', 'minion')],
            [Mob('bandit', 'minion')],
        ],
        'medium': [
            [Mob('orc', 'regular'), Mob('goblin', 'minion')],
            [Mob('bandit', 'regular'), Mob('bandit', 'minion'), Mob('bandit', 'minion')],
            [Mob('skeleton', 'regular', 'undead'), Mob('skeleton', 'regular', 'undead')],
        ],
        'hard': [
            [Mob('orc', 'elite'), Mob('orc', 'regular')],
            [Mob('bandit', 'elite'), Mob('bandit', 'regular'), Mob('bandit', 'regular')],
            [Mob('wolf', 'elite'), Mob('wolf', 'regular'), Mob('wolf', 'minion')],
        ],
        'deadly': [
            [Mob('orc', 'boss'), Mob('orc', 'elite'), Mob('orc', 'regular')],
            [Mob('bandit', 'boss'), Mob('bandit', 'elite'), Mob('bandit', 'elite')],
        ],
        # NEW UNDEAD ENCOUNTERS
        'undead_easy': [
            [Mob('skeleton', 'minion', 'undead'), Mob('skeleton', 'minion', 'undead')],
            [Mob('zombie', 'minion', 'undead'), Mob('zombie', 'minion', 'undead')],
        ],
        'undead_medium': [
            [Mob('skeleton', 'regular', 'undead'), Mob('zombie', 'regular', 'undead')],
            [Mob('wraith', 'regular', 'undead'), Mob('skeleton', 'minion', 'undead')],
        ],
        'undead_hard': [
            [Mob('wraith', 'elite', 'undead'), Mob('skeleton', 'regular', 'undead'), Mob('zombie', 'regular', 'undead')],
            [Mob('lich', 'elite', 'undead'), Mob('skeleton', 'regular', 'undead')],
        ],
        'undead_boss': [
            [Mob('lich', 'boss', 'undead')],
        ],
    }
    
    return random.choice(encounters.get(difficulty, encounters['medium']))

def create_specific_encounter(mob_list):
    """
    Create a specific encounter from a list of (species, type) tuples.
    
    Args:
        mob_list: List of (species, type) tuples
        Example: [('goblin', 'minion'), ('orc', 'regular')]
        
    Returns:
        list: List of Mob objects
    """
    return [Mob(species, mob_type) for species, mob_type in mob_list]