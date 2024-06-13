import Slayer_Accessory as acc
import random
from colorama import Fore, Back, Style, Cursor
import pandas as pd
from ast import literal_eval

items = pd.read_csv('supporting_docs/items.csv')

class Warrior:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Warrior'
        self.attack_style = 'melee'
        self.starting_health = acc.multi_roll(40,65)
        self.health = self.starting_health
        self.starting_inv = {
            "Token of the Wise Wizard"
        }

print(f'Items df: {items}')
char_class = 'Cleric'
#test = items['classes'][0]
print()
print()
#print(test)
#for item in items['classes']:
#    print(literal_eval(item))

#for item in items['classes']:
 #   if 'Warrior' in literal_eval(item):
 #       print('yes')
 #   else:
 #       print('nope')
#print('gap')
print([literal_eval(item) for item in items['classes'] if char_class in item])
print([item for item in items['classes'] if char_class in item])
