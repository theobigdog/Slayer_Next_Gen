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

    def __init__(self, name : str):
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

    def trigger_happy_wipe(self, party_dict : dict, happy_killed : bool) -> dict:
        if happy_killed:
            print('Add Immortal Happy -> wipes the party anyway narration')
            party_dict = acc.wipe_party(party_dict)
        else:
            print('Add wipe narration here')
        #party_dict = acc.wipe_party(party_dict)  Only actually necessary if Happy is killed i think
        print('Add specific Happy narration here for getting the loot, maybe explaining whats up, though this part may not be necessary to explain')
        party_dict = acc.get_loot(self, party_dict)
        print('Add specific Happy narration here for gett stat increases, to explain how it works even, maybe?  Actual stats will never be shown, just set and updated in the background, so nothing should actually print from this function when finished.')
        print(f'1 idea:  "Now listen close, young lassies, I don\'t know exactly how this could be, but this last battle seems to have increased certain skills, for each of you, at a rate I didn\'t think was possible for folks to improve, but you appear to be no average adventurers!')
        print(f'Don\'t ask me who improved in what, or by how much.')
        print(F'Also, I would expect this to occur again after each successful encounter you wee lassies may face.')
        next()
        party_dict = acc.get_stat_increases(party_dict)
        return party_dict


class Drunk_Dwarf:

    def __init__(self, name : str):
        self.name = name
        self.mob_class = 'Drunk Dwarf'
        self = acc.initialize_mob(self, mobs, mob_equipment)
        self.is_boss = False