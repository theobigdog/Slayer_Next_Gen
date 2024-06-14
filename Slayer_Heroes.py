import Slayer_Accessory as acc
import random
from colorama import Fore, Back, Style, Cursor
import pandas as pd
from ast import literal_eval

"""
Add "Dice" values to appropriate external file
miss - 100 sided, 75 cutoff, above is a miss
crit - 20 sided
lucky - 20
expert - 50
tough - 20
dodge - 15
parry - 20
fear - 20
heal - 100
aoe_heal_roll - 20

"""

items = pd.read_csv('supporting_docs/items.csv')
stats = pd.read_csv('supporting_docs/hero_stats.csv')

def get_starting_inv(hero_class : str, items = items) -> list:
    starting_inv = []
    for row in items.index:
        current_class = literal_eval(items['classes'].iat[row])
        current_source = items['source'].iat[row]
        if hero_class in current_class and current_source == 'starting':
            starting_inv.append(items['item'].iat[row])
    return starting_inv

def value_delta(val : int, adjuster : float, upper_limit : int) -> float:
    adj = 0
    while adj < 1 or adj > upper_limit:
        adj = int(round(val + random.randint(-1,1) * random.random() * adjuster, 0))
    return adj

def value_delta_float(val : int, adjuster : float, upper_limit : float) -> float:
    adj = 0
    while adj < 1 or adj > upper_limit:
        adj = round(val + random.randint(-1,1) * random.random() * adjuster, 1)
    return adj

def get_stats(hero_class : float, stats = stats) -> dict:
    index = stats.index[stats['hero_class'] == hero_class]
    return {
        'crit_chance' : value_delta((stats[stats['hero_class'] == hero_class]['crit_chance'][index]).values[0], 2, 20),
        'crit_mult' : value_delta_float((stats[stats['hero_class'] == hero_class]['crit_mult'][index]).values[0], 0.2, 2.5), # This one needs a float since it is multiplying the crit damage
        'low_miss' : (stats[stats['hero_class'] == hero_class]['low_miss'][index]).values[0],
        'high_miss' : (stats[stats['hero_class'] == hero_class]['high_miss'][index]).values[0],
        'luck' : value_delta((stats[stats['hero_class'] == hero_class]['luck'][index]).values[0], 2, 20),
        'expertise' : value_delta((stats[stats['hero_class'] == hero_class]['expertise'][index]).values[0], 5, 50),
        'toughness' : value_delta((stats[stats['hero_class'] == hero_class]['toughness'][index]).values[0], 2, 20),
        'dodge' : value_delta((stats[stats['hero_class'] == hero_class]['dodge'][index]).values[0], 1.5, 15),
        'parry' : value_delta((stats[stats['hero_class'] == hero_class]['parry'][index]).values[0], 2, 20),
        'fear' : value_delta((stats[stats['hero_class'] == hero_class]['fear'][index]).values[0], 2, 20),
        'heal_chance' : value_delta((stats[stats['hero_class'] == hero_class]['heal_chance'][index]).values[0], 5, 100),
        'aoe_heal_chance' : value_delta((stats[stats['hero_class'] == hero_class]['aoe_heal_chance'][index]).values[0], 2, 20),
        'low_st_health' : (stats[stats['hero_class'] == hero_class]['low_st_health'][index]).values[0],
        'high_st_health' : (stats[stats['hero_class'] == hero_class]['high_st_health'][index]).values[0],
    }

def initialize_char (class_obj):
    class_obj.stats = get_stats(class_obj.hero_class)
    class_obj.starting_inv = get_starting_inv(class_obj.hero_class)
    class_obj.inv = class_obj.starting_inv
    class_obj.starting_health = value_delta(acc.multi_roll(class_obj.stats['low_st_health'], class_obj.stats['high_st_health']), 5, 100)
    class_obj.health = class_obj.starting_health

class Warrior:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Warrior'
        self.attack_style = 'melee'
        self = initialize_char(self)
        return self

class Cleric:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Cleric'
        self.attack_style = 'range'
        self = initialize_char(self)
        return self

print(f'Items df: {items}')
ted = Warrior('Ted')
bill = Warrior('Bill')
sara = Cleric('Sara')
mandy = Cleric('Mandy')
print('gap')
print(ted.stats)
print('another warrior stats')
print(bill.stats)
print('starting stats clerics')
print(sara.stats)
print(mandy.stats)
