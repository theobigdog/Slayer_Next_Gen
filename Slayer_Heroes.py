import Slayer_Accessory as acc
import random
from colorama import Fore, Back, Style, Cursor
import pandas as pd
from ast import literal_eval

items = pd.read_csv('supporting_docs/items.csv')
stats = pd.read_csv('supporting_docs/hero_stats.csv')

def get_starting_inv(hero_class : str, items = items) -> list:
    #starting_inv = {}
    starting_inv = []
    for row in items.index:
        current_class = literal_eval(items['classes'].iat[row])
        current_source = items['source'].iat[row]
        if hero_class in current_class and current_source == 'starting':
            #starting_inv[items['item'].iat[row]] = items['item_desc'].iat[row]
            starting_inv.append(items['item'].iat[row])
    return starting_inv

def value_delta(val : int, adjuster : float) -> float:
    return val + random.randint(-1,1) * adjuster

def get_stats(hero_class : float, stats = stats) -> dict:
    index = stats.index[stats['hero_class'] == hero_class]
    return {
        'crit_chance' : value_delta((stats[stats['hero_class'] == hero_class]['crit_chance'][index]).values[0], 1),
        'crit_mult' : value_delta((stats[stats['hero_class'] == hero_class]['crit_mult'][index]).values[0], 0.1),
        'low_miss' : (stats[stats['hero_class'] == hero_class]['low_miss'][index]).values[0],
        'high_miss' : (stats[stats['hero_class'] == hero_class]['high_miss'][index]).values[0],
        'luck' : value_delta((stats[stats['hero_class'] == hero_class]['luck'][index]).values[0], 1),
        'expertise' : value_delta((stats[stats['hero_class'] == hero_class]['expertise'][index]).values[0], 1),
        'toughness' : value_delta((stats[stats['hero_class'] == hero_class]['toughness'][index]).values[0], 1),
        'dodge' : value_delta((stats[stats['hero_class'] == hero_class]['dodge'][index]).values[0], 1),
        'parry' : value_delta((stats[stats['hero_class'] == hero_class]['parry'][index]).values[0], 1),
        'fear' : value_delta((stats[stats['hero_class'] == hero_class]['fear'][index]).values[0], 1),
        'heal_chance' : value_delta((stats[stats['hero_class'] == hero_class]['heal_chance'][index]).values[0], 1),
        'aoe_heal_chance' : value_delta((stats[stats['hero_class'] == hero_class]['aoe_heal_chance'][index]).values[0], 1),
        'low_st_health' : (stats[stats['hero_class'] == hero_class]['low_st_health'][index]).values[0],
        'high_st_health' : (stats[stats['hero_class'] == hero_class]['high_st_health'][index]).values[0],
    }

def initialize_char (class_obj):
    class_obj.stats = get_stats(class_obj.hero_class)
    class_obj.starting_inv = get_starting_inv(class_obj.hero_class)
    class_obj.inv = class_obj.starting_inv
    class_obj.starting_health = acc.multi_roll(class_obj.stats['low_st_health'], class_obj.stats['high_st_health'])
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
#test = items['classes'][0]
print('gap')
print(ted.stats)
print('another warrior stats')
print(bill.stats)
print('starting inv cleric, warrior')
print(sara.starting_inv)
print(ted.starting_inv)

