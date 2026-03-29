import Slayer_Accessory as acc
import random
from colorama import Fore, Back, Style, Cursor, win32, init
import pandas as pd
import numpy as np
from ast import literal_eval

stat_dice_cutoffs = acc.get_dice_cutoffs()

items = acc.get_items()
stats = acc.get_stats()

def get_starting_inv(hero_class : str, items = items) -> list:
    starting_inv = []
    for row in items.index:
        current_class = literal_eval(items['classes'].iat[row])
        current_source = items['source'].iat[row]
        if hero_class in current_class and current_source == 'starting':
            starting_inv.append(items['item'].iat[row])
    return starting_inv

    # val = starting number
    # adjuster = desired adj-range delta,
    # lower_limit = lower cutoff for adj,
    # upper_limit = upper cutoff for adj,
    # decimals = number of decimal places in adj if val is a float
def stat_value_delta(val, adjuster, lower_limit : float, upper_limit : float, decimals : int = 0) -> float: #### adjusts stat-cutoffs so there is more variability within each class
    adj = lower_limit - 1
    while not(lower_limit <= adj and adj <= upper_limit):
        if type(val) == np.float64:
            adj = round(val + random.randint(-1,1) * random.random() * adjuster, decimals)
        else:
            adj = int(round(val + random.randint(-1,1) * random.random() * adjuster, decimals))
    return adj

def get_stats(hero_class : str, stats = stats) -> dict:
    index = stats.index[stats['hero_class'] == hero_class]
    return {
        'crit' : stat_value_delta((stats[stats['hero_class'] == hero_class]['crit_chance'][index]).values[0], 2, 1, stat_dice_cutoffs['crit_cutoff'], 0),
        'crit_mult' : stat_value_delta((stats[stats['hero_class'] == hero_class]['crit_mult'][index]).values[0], 0.2, 1, stat_dice_cutoffs['crit_mult_cutoff'], 2),
        'low_miss' : (stats[stats['hero_class'] == hero_class]['low_miss'][index]).values[0],
        'high_miss' : (stats[stats['hero_class'] == hero_class]['high_miss'][index]).values[0],
        'luck' : stat_value_delta((stats[stats['hero_class'] == hero_class]['luck'][index]).values[0], 2, 1, stat_dice_cutoffs['luck_cutoff'], 0),
        'expertise' : stat_value_delta((stats[stats['hero_class'] == hero_class]['expertise'][index]).values[0], 5, 1, stat_dice_cutoffs['expertise_cutoff'], 0),
        'toughness' : stat_value_delta((stats[stats['hero_class'] == hero_class]['toughness'][index]).values[0], 2, 1, stat_dice_cutoffs['toughness_cutoff'], 0),
        'dodge' : stat_value_delta((stats[stats['hero_class'] == hero_class]['dodge'][index]).values[0], 1.5, 1, stat_dice_cutoffs['dodge_cutoff'], 0),
        'parry' : stat_value_delta((stats[stats['hero_class'] == hero_class]['parry'][index]).values[0], 2, 1, stat_dice_cutoffs['parry_cutoff'], 0),
        'fear' : stat_value_delta((stats[stats['hero_class'] == hero_class]['fear'][index]).values[0], 2, 1, stat_dice_cutoffs['fear_cutoff'], 0),
        'heal' : stat_value_delta((stats[stats['hero_class'] == hero_class]['heal_chance'][index]).values[0], 5, 1, stat_dice_cutoffs['heal_cutoff'], 0) if hero_class == 'Cleric' else 100,
        'aoe_heal' : stat_value_delta((stats[stats['hero_class'] == hero_class]['aoe_heal_chance'][index]).values[0], 2, 1, stat_dice_cutoffs['aoe_heal_cutoff'], 0) if hero_class == 'Cleric' else 20,
        'low_st_health' : (stats[stats['hero_class'] == hero_class]['low_st_health'][index]).values[0],
        'high_st_health' : (stats[stats['hero_class'] == hero_class]['high_st_health'][index]).values[0],
        'speed' : stat_value_delta((stats[stats['hero_class'] == hero_class]['speed'][index]).values[0], 2, 1, 20, 0),
    }

def _get_base_ability(class_obj):
    """
    Get the base ability for this hero's class.
    
    Args:
        class_obj: The hero object
        
    Returns:
        str: Ability name
    """
    base_abilities = {
        'Warrior': 'Power Strike',
        'Shifter': 'Power Strike',
        'Battle_Mage': 'Power Strike',
        'Hunter': 'Power Strike',
        'Wizard': 'Power Strike',
        'Sapper': 'Power Strike',
        'Cleric': 'Heal',
    }
    
    return base_abilities.get(class_obj.hero_class, 'Power Strike')

def get_all_abilities(class_obj):
    """
    Get list of all available abilities for this hero.
    
    Args:
        class_obj: The hero object
        
    Returns:
        list: All ability names (base + learned + equipment)
    """
    all_abilities = []
    
    if class_obj.abilities['base']:
        all_abilities.append(class_obj.abilities['base'])
    
    all_abilities.extend(class_obj.abilities['learned'])
    all_abilities.extend(class_obj.abilities['equipment'])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_abilities = []
    for ability in all_abilities:
        if ability not in seen:
            seen.add(ability)
            unique_abilities.append(ability)
    
    return unique_abilities

def can_use_ability(class_obj, ability_name):
    """
    Check if hero can currently use this ability.
    
    Args:
        class_obj: The hero object
        ability_name: Name of ability to check
        
    Returns:
        tuple: (bool can_use, str reason)
    """
    # Check if hero has this ability
    all_abilities = get_all_abilities(class_obj)
    if ability_name not in all_abilities:
        return (False, "You don't have that ability!")
    
    # Check if on cooldown
    if ability_name in class_obj.ability_cooldowns:
        if class_obj.ability_cooldowns[ability_name] > 0:
            return (False, f"On cooldown for {class_obj.ability_cooldowns[ability_name]} more turns!")
    
    # Check resource cost (for future mana/stamina system)
    # For now, all abilities are free
    
    return (True, "")

def reduce_cooldowns(class_obj):
    """Reduce all ability cooldowns by 1 turn."""
    for ability in list(class_obj.ability_cooldowns.keys()):
        class_obj.ability_cooldowns[ability] -= 1
        if class_obj.ability_cooldowns[ability] <= 0:
            del class_obj.ability_cooldowns[ability]

def initialize_char(class_obj):
    """Initialize a hero character with stats and abilities."""
    class_obj.stats = get_stats(class_obj.hero_class)
    class_obj.starting_inv = get_starting_inv(class_obj.hero_class)
    class_obj.inv = class_obj.starting_inv.copy()
    class_obj.starting_health = stat_value_delta(
        acc.multi_roll(class_obj.stats['low_st_health'], class_obj.stats['high_st_health']), 
        2, 1, 100, 0
    )
    class_obj.health = class_obj.starting_health
    class_obj.abilities = {
        'base': _get_base_ability(class_obj),  # Class default ability
        'learned': [],  # From ability scrolls (loot)
        'equipment': []  # From equipped items
    }
    class_obj.ability_cooldowns = {}  # turn tracking
    class_obj.resource = 100  # if mana/stamina added later
    class_obj.max_resource = 100
    class_obj.is_dead = False
    class_obj.is_defending = False  # For defend action
    class_obj.defend_bonus = 0  # Bonus to dodge/parry when defending
    
    # Add methods to the object
    class_obj.get_all_abilities = lambda: get_all_abilities(class_obj)
    class_obj.can_use_ability = lambda ability_name: can_use_ability(class_obj, ability_name)
    class_obj.reduce_cooldowns = lambda: reduce_cooldowns(class_obj)
    class_obj._get_base_ability = lambda: _get_base_ability(class_obj)

class Warrior:
    def __init__(self, name: str):
        self.heroine_name = name
        self.hero_class = 'Warrior'
        self.attack_style = 'both'
        initialize_char(self)  # Remove the "self =" part!


class Shifter:
    def __init__(self, name: str):
        self.heroine_name = name
        self.hero_class = 'Shifter'
        self.attack_style = 'both'
        initialize_char(self)


class Battle_Mage:
    def __init__(self, name: str):
        self.heroine_name = name
        self.hero_class = 'Battle_Mage'
        self.attack_style = 'melee'
        initialize_char(self)


class Hunter:
    def __init__(self, name: str):
        self.heroine_name = name
        self.hero_class = 'Hunter'
        self.attack_style = 'range'
        initialize_char(self)


class Wizard:
    def __init__(self, name: str):
        self.heroine_name = name
        self.hero_class = 'Wizard'
        self.attack_style = 'range'
        initialize_char(self)


class Sapper:
    def __init__(self, name: str):
        self.heroine_name = name
        self.hero_class = 'Sapper'
        self.attack_style = 'melee'
        initialize_char(self)


class Cleric:
    def __init__(self, name: str):
        self.heroine_name = name
        self.hero_class = 'Cleric'
        self.attack_style = 'range'
        initialize_char(self)
