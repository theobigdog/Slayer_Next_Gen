"""
Generic mob factory for random encounters.
For unique bosses, use dedicated modules (Slayer_Dwarf.py, etc.)
"""

import random
from colorama import Fore, Style

class Mob:
    """Generic mob class for random encounters."""
    
    def __init__(self, mob_species='goblin', mob_type='regular'):
        """
        Initialize a generic mob.
        
        Args:
            mob_species: Type of creature (goblin, orc, bandit, etc.)
            mob_type: Difficulty tier (minion, regular, elite, boss)
        """
        self.mob_species = mob_species
        self.mob_type = mob_type
        self.name = self._generate_name()
        
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
# MOB FACTORY FUNCTIONS
# ============================================================================

def create_random_encounter(difficulty='easy'):
    """
    Create a random mob encounter.
    
    Args:
        difficulty: 'easy', 'medium', 'hard', 'deadly'
        
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
            [Mob('skeleton', 'regular'), Mob('skeleton', 'regular')],
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