import Slayer_Accessory as acc
import random
from ast import literal_eval

stat_dice_cutoffs = acc.get_dice_cutoffs()

items_df = acc.get_items()
hero_stats_df = acc.get_stats()

def get_starting_inv(hero_class : str, items_df = items_df) -> list:
    starting_inv = []
    for _, item in items_df.iterrows():
        if hero_class in literal_eval(item['classes']) and item['source'] == 'starting':
            starting_inv.append(item['item'])
    return starting_inv
    
def stat_value_delta(val, adjuster, lower_limit : float, upper_limit : float, decimals : int = 0) -> float: #### adjusts stat-cutoffs so there is more variability within each class
    """ val = starting number
    adjuster = desired adj-range delta,
    lower_limit = lower cutoff for adj,
    upper_limit = upper cutoff for adj,
    decimals = number of decimal places in adj if val is a float"""
    adj = lower_limit - 1
    while not (lower_limit <= adj <= upper_limit):
        if isinstance(val, float):
            adj = round(val + random.triangular(-adjuster, adjuster, 0), decimals)
        else:
            adj = int(round(val + random.triangular(-adjuster, adjuster, 0), decimals))
    return adj

def get_stats(hero_class : str, hero_stats_df = hero_stats_df) -> dict:
    row = hero_stats_df[hero_stats_df['hero_class'] == hero_class].iloc[0]
    adj = 5
    low = 1
    high = 100 # every stat is a % chance
    return {
        'crit_chance' : stat_value_delta(row['crit_chance'], adj, low, high, 0),
        'crit_mult' : stat_value_delta(row['crit_mult'], 0.2, low, stat_dice_cutoffs['crit_mult_cutoff'], 2), # This one needs a float since it is multiplying the crit damage
        'hit' : stat_value_delta(row['hit'], adj, low, high, 0),
        'luck' : stat_value_delta(row['luck'], adj, low, high, 0),
        'speed' : row['speed'],
        'expertise' : stat_value_delta(row['expertise'], adj, low, high, 0),
        'toughness' : stat_value_delta(row['toughness'], adj, low, high, 0),
        'dodge' : stat_value_delta(row['dodge'], adj, low, high, 0),
        'parry' : stat_value_delta(row['parry'], adj, low, high, 0),
        'fear' : stat_value_delta(row['fear'], adj, low, high, 0),
        'heal_chance' : stat_value_delta(row['heal_chance'], adj, low, high, 0),
        'aoe_heal_chance' : stat_value_delta(row['aoe_heal_chance'], adj, low, high, 0),
        'low_st_health' : row['low_st_health'],
        'high_st_health' : row['high_st_health'],
    }

def initialize_char (heroine):
    heroine.stats = get_stats(heroine.hero_class)
    heroine.starting_inv = get_starting_inv(heroine.hero_class)
    heroine.inv = heroine.starting_inv.copy()
    heroine.starting_health = stat_value_delta(acc.multi_roll(heroine.stats['low_st_health'], heroine.stats['high_st_health']), 2, 1, 100, 0)
    heroine.health = heroine.starting_health
    heroine.is_dead = False
    heroine.is_mob = False
    return heroine

class Warrior:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Warrior'
        self.attack_style = 'both'
        initialize_char(self)


class Shifter:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Shifter'
        self.attack_style = 'melee'
        initialize_char(self)

        
class Battle_Mage:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Battle_Mage'
        self.attack_style = 'melee'
        initialize_char(self)

        
class Hunter:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Hunter'
        self.attack_style = 'range'
        initialize_char(self)

        
class Witch:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Witch'
        self.attack_style = 'range'
        initialize_char(self)

        
class Sapper:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Sapper'
        self.attack_style = 'melee'
        initialize_char(self)


class Cleric:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Cleric'
        self.attack_style = 'range'
        initialize_char(self)
