import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import pandas as pd
import random
from colorama import Fore, Back, Style, Cursor
import time
import Slayer_Combat as combat
from ast import literal_eval

mobs = acc.get_mobs()
mob_equipment = acc.get_mob_equipment()
'''
def get_starting_inv(hero_class : str, items = items) -> list:
    starting_inv = []
    for row in items.index:
        current_class = literal_eval(items['classes'].iat[row])
        current_source = items['source'].iat[row]
        if hero_class in current_class and current_source == 'starting':
            starting_inv.append(items['item'].iat[row])
    return starting_inv

def get_mob_stats(mob_class: str, mobs: pd.DataFrame) -> dict:
    index = mobs.index[mobs['mob_class'] == mob_class]
    return {
        'crit': mobs[mobs['mob_class'] == mob_class]['crit_multiplier'][index],
        'enraged_crit': mobs[mobs['mob_class'] == mob_class]['enraged_crit_multiplier'][index],
        'crit_chance': mobs[mobs['mob_class'] == mob_class]['crit_chance'][index],
        'crit_chance': mobs[mobs['mob_class'] == mob_class]['crit_chance'][index],
    }

def get_mob_inv(mobs: pd.DataFrame, mob_equipment: pd.DataFrame = mob_equipment):
    return {

    }

def initialize_char(class_obj: object, mobs: pd.DataFrame, mob_equipment: pd.DataFrame):
    class_obj.stats = acc.get_mob_stats(class_obj.mob_class, mobs),
    class_obj.inv = acc.get_mob_inv(class_obj.mob_class)
    class_obj.is_dead = False
    class_obj.enraged = False
    
'''    

class Disgruntled_Dwarf:

    def __init__(self, name):
        self.name = name
        self.mob_class = 'Disgruntled Dwarf'
        self = acc.initialize_mob(self, mobs, mob_equipment)
        self.is_boss = True
        self.enraged = False
        
    def toggle_enraged(self):
        print(f"\n\n{self.name} gasps loudly.  \"Now that one fucking hurt!!\"")
        next()
        print(f"\n{self.name} suddenly bulges out in all directions.  He becomes a rippling mass of what looks like pure muscle - the veins in his neck and forearms swell to such a size, they look like they might rupture.\n")
        print(f"\"Oh lassies,\" he growls, \"you really fucked up now!  Now?  NOW I'M ANGRY!!!!\"")
        self.is_dead = False
        self.enraged = True
        self.starting_health = self.stats['enraged_hp']
        self.health = self.stats['enraged_hp']

class Drunk_Dwarf:

    def __init__(self, name):
        self.name = name
        self.mob_class = 'Drunk Dwarf'
        self = acc.initialize_mob(self, mobs, mob_equipment)
        self.is_boss = False