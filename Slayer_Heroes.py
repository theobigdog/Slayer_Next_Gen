import Slayer_Accessory as acc
import random
from colorama import Fore, Back, Style, Cursor
import pandas as pd
from ast import literal_eval

items = pd.read_csv('supporting_docs/items.csv')

def get_starting_inv(hero_class, items = items):
    starting_inv = {}
    for row in items.index:
        current_class = literal_eval(items['classes'].iat[row])
        current_source = items['source'].iat[row]
        if hero_class in current_class and current_source == 'starting':
            starting_inv[items['item'].iat[row]] = items['item_desc'].iat[row]
    return starting_inv

class Warrior:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Warrior'
        self.attack_style = 'melee'
        self.starting_health = acc.multi_roll(40,65)
        self.health = self.starting_health
        self.starting_inv = get_starting_inv(self.hero_class)

class Cleric:

    def __init__ (self, name : str):
        self.name = name
        self.hero_class = 'Cleric'
        self.attack_style = 'range'
        self.starting_health = acc.multi_roll(15,25)
        self.health = self.starting_health
        self.starting_inv = get_starting_inv(self.hero_class)

print(f'Items df: {items}')
ted = Warrior('Ted')
sara = Cleric('Sara')
#test = items['classes'][0]
print('Ted' + str(ted.starting_inv))
print('Sara' + str(sara.starting_inv))
#print(test)
#for item in items['classes']:
#    print(literal_eval(item))

#for item in items['classes']:
 #   if 'Warrior' in literal_eval(item):
 #       print('yes')
 #   else:
 #       print('nope')
#print('gap')
#print([literal_eval(item) for item in items['classes'] if char_class.hero_class in item])
#print([item for item in items['classes'] if char_class in item])
#test = [literal_eval(item) for item in items['classes'] if char_class.hero_class in item]
#print(test[0])
#starting = items[items['source'] == 'starting']
#for row in items.index:
 #   test.append(items.iloc[row]['damage_range_high'])
#print(starting)
#print(char_class)

#for thing in items['classes']:
#    print(literal_eval(thing)[-1])
'''
for row in items.index:
    current_class = literal_eval(items['classes'].iat[row])
    current_source = items['source'].iat[row]
    if ted.hero_class in current_class and current_source == 'starting':
        ted.starting_inv[items['item'].iat[row]] = items['item_desc'].iat[row]
print('Ted  ' + str([value for value in ted.starting_inv.values()]))

for row in items.index:
    current_class = literal_eval(items['classes'].iloc[row])
    current_source = items['source'].iat[row]
    if sara.hero_class in current_class and current_source == 'starting':
        sara.starting_inv[items['item'].iloc[row]] = items['item_desc'].iloc[row]
print('Sara  ' + str([value for value in sara.starting_inv.values()]))
'''