import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import Slayer_Heroes as heroes
import pandas as pd
import numpy as np
import joblib as jb
import random
from colorama import Fore, Back, Style, Cursor
import time
import string

auto_name_choices = {
    'first' : ["Ath","Jodum","Prinny","Bubba","The Cake","Tedless","Muffy","Bildo","T-Bear","Miss Beans","Billy","Djub-Djub"],
    'middle' : ["the Messy","the Wrong","the Strange","the Savage","the Potent","the Silly-Hearted","the Smelly","the Aromatic","the Unkempt","the Poorly-Dressed","the Cruel","the Really Mean"],
    'last' : ["Wet-Nurse","Sensation","Meal-Worm","Armpit","Butthead","Doofus","Dork","Lamp","Smegma","Jerk","Monkey","Walrus","Doormat"]
}

dick_bubble = ["DICK-BUBBLE","DICK BUBBLE","DICK BUBBLES","DICK-BUBBLES","DICK-BBL","DICK BBL", "DICKBBL"]

def get_name() -> str:
    print("Greetings!")
    name = str(input(f'What is your name?  If you have one that is.  {whine()}.  Your name, please:  ')).title()
    return name

'''def get_saved_game_obsolete() -> list:  ################### MIght be obsolete
    starting_name = str(input('The name of your saved party, please:  '))
    save_name = starting_name
    if not starting_name.endswith('pkl'):
        save_name = save_name + '.pkl'
    if not starting_name.startswith('saved_parties/'):
        save_name = 'saved_parties/' + save_name
    try:
        saved_party = acc.load_party(save_name)
    except(ValueError, FileNotFoundError):
        saved_party = "invalid"
    return saved_party, starting_name'''

''''
def print_classes():
    print('Class Options:')
    print()
    for hero_class in acc.get_hero_classes():
        print(hero_class)
'''
        
def print_recommended_classes(num_chars : int):
    print('Recommended Party Composition (based on party-size):')
    print()
    '''conversion = {
        "1" : ['Warrior'],
        "2" : ['Warrior', 'Cleric'],
        "3" : ['Warrior', 'Cleric', 'Hunter'],
        "4" : ['Warrior', 'Cleric', 'Hunter', 'Shifter'],
        "5" : 
        "6" : 
        "7" : 
        "8" : ['Warrior', 'Cleric', 'Hunter', 'Shifter', ],
    }'''
    
    for i in range(num_chars): #acc.get_hero_classes():
        rando = random.randint(1,len(acc.get_hero_classes()))
        print(acc.get_hero_classes()[rando])#conversion[str(rando)])
    #print('Cleric (2nd)')

def get_hero(selection : str, name : str):
    if selection == 'Warrior':
        return heroes.Warrior(name)
    elif selection == 'Shifter':
        return heroes.Shifter(name)
    elif selection == 'Battle_Mage':
        return heroes.Battle_Mage(name)
    elif selection == 'Hunter':
        return heroes.Hunter(name)
    elif selection == 'Wizard':
        return heroes.Wizard(name)
    elif selection == 'Sapper':
        return heroes.Sapper(name)
    elif selection == 'Cleric':
        return heroes.Cleric(name)
    else:
        return heroes.Warrior(name)

def auto_pick_name():
    first = auto_name_choices['first'][random.randint(0,len(auto_name_choices['first']) - 1)]
    middle = auto_name_choices['middle'][random.randint(0,len(auto_name_choices['middle']) - 1)]
    last = auto_name_choices['last'][random.randint(0, len(auto_name_choices['last']) - 1)]
    return first + ' ' + middle + ' ' + last

def create_new_party(name: str) -> list:
    new_party = []
    wt()
    acc.print_classes()
    print()
   # print_recommended_classes()
    #print()

    party_count = input("How many party members would you like to include (1 minimum, 8 maximum)?  ")
    value_ok = False
    while not value_ok:
        try:
            party_count = int(party_count)
            if party_count >= 1 and party_count <= 8:
                value_ok = True
            else:
                party_count = input("I don't think that's a proper integer.  Try again (1 - 8):  ")
        except(ValueError):
            party_count = input("I don't think that's a proper integer.  Try again (1 - 8):  ")
    if party_count <= 3:
        print(f'{party_count}?!  Ballsy, I like it!')
    print_recommended_classes(party_count)
    choose_composition = acc.yes_no(input("Would you like to choose the composition of your party?"))
    choose_names = acc.yes_no(input("Would you like to choose the names of your party members?"))
    if choose_composition:
        print("Fair enough, but I doubt you'll get the composition right, so suck it.")
        time.sleep(2)
        wt()
        acc.print_classes()
        print()
        for i in range(party_count):
            selection = input("Which Class would you like to add?  ")
            while selection not in acc.get_hero_classes():
                selection = input("Let's try again.  Of the listed Class options, which would you like to add?  ")
            if choose_names:
                name_choice = str(input("Ok, let's have a name for her:  "))
                new_party.append(get_hero(selection, name_choice))
            else:
                new_party.append(get_hero(selection, auto_pick_name()))
    else:
        members = acc.get_hero_classes()
        members.append('Cleric')
        print("I figured as much.  Where is your sense of originality?")
        time.sleep(2)
        wt()
        for i in range(party_count):
            selection = members[i]
            if choose_names:
                name_choice = str(input("Ok, let's have a name for your " + selection + ":  "))
                new_party.append(get_hero(selection, name_choice))
            else:
                new_party.append(get_hero(selection, auto_pick_name()))
    return new_party
'''
def form_party_obsolete(name : str) -> list:
    repeat_customer = acc.yes_no(input(f"Have we seen you here before, uh, what was it again?  Oh, right, {name}.\nThat's a weird freakin' name, but whatever.\nOk, {name}, do you have an old party to further abuse? I mean, load?\n(If you don't actually have a save or you forgot the name just enter 'No'):  "))
    saved_party = None
    if repeat_customer:
        acceptable = False
        saved_party, saved_name = get_saved_game()
        while (not acceptable) and (repeat_customer):
            if type(saved_party) != list and repeat_customer == True: #pd.DataFrame and repeat_customer == True:
                repeat_customer = acc.yes_no(input('Are you having trouble understanding?  Yes, or No, do you have a valid saved party?:  '))
                if repeat_customer:
                    saved_party, saved_name = get_saved_game()
                else:
                    repeat_customer = False
                    saved_party = create_new_party(saved_name)
                    acc.save_party(saved_party, saved_name)
            else:
                acceptable = True
                print('Your party was imported successfully.')
                next()
    else:
        saved_party = create_new_party(name)
        acc.save_party(saved_party, name)
'''
#def get_saved_party(name):
 #   try:
  #      return 


def form_party() -> list:
    name = get_name()
    saved_party = []#saved_party
    try:
        saved_party = jb.load(f"saved_parties/{name}.pkl")
        print(f"Ah yes, {name}... <snicker snicker>... God I still think that name is so fucking stupid!  \nOk are you ready to rock and ro......{whine()}\nYou're a dumbass for trying to play again.")
        next()
    except(FileNotFoundError):
        name = str(input(f"I don't recognize you.  What was that name again?  "))
        try:
            saved_party = jb.load(f"saved_parties/{name}.pkl")
            print(f"Oh, that's right, you were the dude projectile vomiting into that fountain last night.{whine()}  Welcome back.")
            next()
        except(FileNotFoundError):
            print(f"No, I've never seen you.")
            time.sleep(2)
            print(f"Let's just make you a fresh party, mkay?")
            time.sleep(2)
            saved_party = create_new_party(name)


            '''
    repeat_customer = acc.yes_no(input(f"Have we seen you here before, uh, what was it again?  Oh, right, {name}.\nThat's a weird freakin' name, but whatever.\nOk, {name}, do you have an old party to further abuse? I mean, load?\n(If you don't actually have a save or you forgot the name just enter 'No'):  "))
    saved_party = None
    if repeat_customer:
        acceptable = False
        saved_party, saved_name = get_saved_game()
        while (not acceptable) and (repeat_customer):
            if type(saved_party) != list and repeat_customer == True: #pd.DataFrame and repeat_customer == True:
                repeat_customer = acc.yes_no(input('Are you having trouble understanding?  Yes, or No, do you have a valid saved party?:  '))
                if repeat_customer:
                    saved_party, saved_name = get_saved_game()
                else:
                    repeat_customer = False
                    saved_party = create_new_party(saved_name)
                    acc.save_party(saved_party, saved_name)
            else:
                acceptable = True
                print('Your party was imported successfully.')
                next()
    else:
        saved_party = create_new_party(name)
        acc.save_party(saved_party, name)
    '''
    print()
    for dudette in saved_party:
        print(dudette.name)
        print(dudette.hero_class)
        print(dudette.stats)
        #print(dudette.starting_inv)
        print(dudette.inv)
        #print(dudette.starting_health)
        print(dudette.health)
        next()
    return saved_party