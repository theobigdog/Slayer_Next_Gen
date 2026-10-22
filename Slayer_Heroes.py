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
        'crit' : stat_value_delta((stats[stats['hero_class'] == hero_class]['crit_chance'][index]).values[0], 2, 1, stat_dice_cutoffs['crit_cutoff'], 0), #stat_value_delta((stats[stats['hero_class'] == hero_class]['crit_chance'][index]).values[0], 2, 20),
        'crit_mult' : stat_value_delta((stats[stats['hero_class'] == hero_class]['crit_mult'][index]).values[0], 0.2, 1, stat_dice_cutoffs['crit_mult_cutoff'], 2), # This one needs a float since it is multiplying the crit damage
        'low_miss' : (stats[stats['hero_class'] == hero_class]['low_miss'][index]).values[0],
        'high_miss' : (stats[stats['hero_class'] == hero_class]['high_miss'][index]).values[0],
        'luck' : stat_value_delta((stats[stats['hero_class'] == hero_class]['luck'][index]).values[0], 2, 1, stat_dice_cutoffs['luck_cutoff'], 0),
        'speed' : (stats[stats['hero_class'] == hero_class]['speed'][index]).values[0],
        'expertise' : stat_value_delta((stats[stats['hero_class'] == hero_class]['expertise'][index]).values[0], 5, 1, stat_dice_cutoffs['expertise_cutoff'], 0),
        'toughness' : stat_value_delta((stats[stats['hero_class'] == hero_class]['toughness'][index]).values[0], 2, 1, stat_dice_cutoffs['toughness_cutoff'], 0),
        'dodge' : stat_value_delta((stats[stats['hero_class'] == hero_class]['dodge'][index]).values[0], 1.5, 1, stat_dice_cutoffs['dodge_cutoff'], 0),
        'parry' : stat_value_delta((stats[stats['hero_class'] == hero_class]['parry'][index]).values[0], 2, 1, stat_dice_cutoffs['parry_cutoff'], 0),
        'fear' : stat_value_delta((stats[stats['hero_class'] == hero_class]['fear'][index]).values[0], 2, 1, stat_dice_cutoffs['fear_cutoff'], 0),
        'heal' : stat_value_delta((stats[stats['hero_class'] == hero_class]['heal_chance'][index]).values[0], 5, 1, stat_dice_cutoffs['heal_cutoff'], 0),# if hero_class == 'Cleric' else 100,
        'aoe_heal' : stat_value_delta((stats[stats['hero_class'] == hero_class]['aoe_heal_chance'][index]).values[0], 2, 1, stat_dice_cutoffs['aoe_heal_cutoff'], 0),# if hero_class == 'Cleric' else 20,
        'low_st_health' : (stats[stats['hero_class'] == hero_class]['low_st_health'][index]).values[0],
        'high_st_health' : (stats[stats['hero_class'] == hero_class]['high_st_health'][index]).values[0],
    }

def initialize_char (class_obj):
    class_obj.stats = get_stats(class_obj.hero_class)
    class_obj.starting_inv = get_starting_inv(class_obj.hero_class)
    class_obj.inv = class_obj.starting_inv.copy()
    class_obj.starting_health = stat_value_delta(acc.multi_roll(class_obj.stats['low_st_health'], class_obj.stats['high_st_health']), 2, 1, 100, 0)
    class_obj.health = class_obj.starting_health
    class_obj.is_dead = False

class Warrior:

    def __init__ (self, name : str):
        self.heroine_name = name
        self.hero_class = 'Warrior'
        self.attack_style = 'both'
        self = initialize_char(self)


class Shifter:

    def __init__ (self, name : str):
        self.heroine_name = name
        self.hero_class = 'Shifter'
        self.attack_style = 'melee'
        self = initialize_char(self)

        
class Battle_Mage:

    def __init__ (self, name : str):
        self.heroine_name = name
        self.hero_class = 'Battle_Mage'
        self.attack_style = 'melee'
        self = initialize_char(self)

        
class Hunter:

    def __init__ (self, name : str):
        self.heroine_name = name
        self.hero_class = 'Hunter'
        self.attack_style = 'range'
        self = initialize_char(self)

        
class Witch:

    def __init__ (self, name : str):
        self.heroine_name = name
        self.hero_class = 'Witch'
        self.attack_style = 'range'
        self = initialize_char(self)

        
class Sapper:

    def __init__ (self, name : str):
        self.heroine_name = name
        self.hero_class = 'Sapper'
        self.attack_style = 'melee'
        self = initialize_char(self)


class Cleric:

    def __init__ (self, name : str):
        self.heroine_name = name
        self.hero_class = 'Cleric'
        self.attack_style = 'range'
        self = initialize_char(self)
