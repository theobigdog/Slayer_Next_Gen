import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import Slayer_Combat
import Slayer_Heroes as heroes
import joblib as jb
import random
from colorama import Fore, Back, Style, Cursor
import time

auto_name_choices = {
    'first' : ["Ath","Jodum","Prinny","Bubba","The Cake","Tedless","Muffy","Bildo","T-Bear","Miss Beans","Billy","Djub-Djub"],
    'middle' : ["the Messy","the Wrong","the Strange","the Savage","the Potent","the Silly-Hearted","the Smelly","the Aromatic","the Unkempt","the Poorly-Dressed","the Cruel","the Really Mean"],
    'last' : ["Wet-Nurse","Sensation","Meal-Worm","Armpit","Butthead","Doofus","Dork","Lamp","Smegma","Jerk","Monkey","Walrus","Doormat"]
}

def get_name() -> str:
    print("Greetings!")
    name = str(input(f'What is your name?  If you have one that is.  {whine()}.  Your name, please:  ')).title()
    unacceptable = True
    while unacceptable:
        if name.upper() in db:
            print('No.')
            time.sleep(2)
            name = str(input(f"Your name!  Your real fucking name!  Jesus Christ!  {whine()}.  "))
        else:
            unacceptable = False
    print()
    print(f"That's gotta be the very lamest name I've heard, and I've been hosting this game for... some time....  You're killing me.")
    return name
        
def print_recommended_classes(num_chars : int):
    print('\nRecommended Party Composition (based on party-size):')
    print()    
    for i in range(num_chars):
        rando = random.randint(1,len(acc.get_hero_classes())-1)
        print(acc.get_hero_classes()[rando])#

def get_default_classes(party_count : int) -> list:
    # 0: Warrior, 1: Shifter, 2: Battle_Mage, 3: Hunter, 4: Wizard, 5: Sapper, 6: Cleric
    if party_count == 1:
        return ['Warrior']
    elif party_count == 2:
        return ['Warrior', 'Cleric']
    elif party_count == 3:
        return ['Warrior', 'Cleric', 'Hunter']
    elif party_count == 4:
        return ['Warrior', 'Cleric', 'Hunter', 'Shifter']
    elif party_count == 5:
        return ['Warrior', 'Cleric', 'Hunter', 'Shifter', 'Cleric']
    elif party_count == 6:
        return ['Warrior', 'Cleric', 'Hunter', 'Shifter', 'Cleric', 'Sapper']
    elif party_count == 7:
        return ['Warrior', 'Cleric', 'Hunter', 'Shifter', 'Cleric', 'Sapper', 'Wizard']
    elif party_count == 8:
        return ['Warrior', 'Cleric', 'Hunter', 'Shifter', 'Cleric', 'Sapper', 'Wizard', 'Battle_Mage']
    else:
        return []

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

db = ["DICK-BUBBLE","DICK BUBBLE","DICK BUBBLES","DICK-BUBBLES","DICK-BBL","DICK BBL", "DICKBBL"]

def print_current_party(party : list):
    for member in party:
        print(f"Hero:  {member.heroine_name}, Class:  {member.hero_class}")

def create_new_party(name: str) -> list:
    new_party = []
    wt()
    acc.print_classes()
    print()
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
        time.sleep(2)
    wt()
    print_recommended_classes(party_count)
    print()
    choose_composition = acc.yes_no(input("Would you like to choose the composition of your party?  "))
    print()
    choose_names = acc.yes_no(input("Would you like to choose the names of your party members?  "))
    if choose_composition:
        print()
        print("Fair enough, but I doubt you'll get the composition right, so suck it.")
        time.sleep(2)
        wt()
        acc.print_classes()
        print()
        for i in range(party_count):
            wt()
            print_current_party(new_party)
            print()
            acc.print_classes()
            print()
            print_recommended_classes(party_count)
            print()
            selection = input("\nWhich Class would you like to add?  ")
            while selection not in acc.get_hero_classes():
                print()
                selection = input("Let's try again.  Of the listed Class options, which would you like to add?  ")
            if choose_names:
                print()
                name_choice = str(input("Ok, let's have a name for her:  "))
                new_party.append(get_hero(selection, name_choice))
            else:
                new_party.append(get_hero(selection, auto_pick_name()))
    else:
        members = get_default_classes(party_count)
        print()
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

def get_party() -> dict:
    name = get_name()
    saved_party = []
    #can_save_party = False
    try:
        saved_party = acc.load_party(name) #jb.load(f"saved_parties/{name}.pkl")
        print(f"Ah yes, here you are: {name}... <snicker-snicker>... God I still think that name is so fucking stupid!  \nOk are you ready to rock and ro......{whine()}\nYou're a dumbass for trying to play again.\nAnd I have schizophrenia.")
        Slayer_Combat.display_party_summary(saved_party['party'])
        next()
        return saved_party
    except(FileNotFoundError):
        name = str(input(f"I don't recognize you.  What was that name again?  "))
        try:
            saved_party = acc.load_party(name) #jb.load(f"saved_parties/{name}.pkl")
            print(f"Oh, that's right, {name}, you were the moron projectile vomiting into that fountain last night.{whine()}  Welcome back.")
            acc.print_player_starting_summary(saved_party.party)
            Slayer_Combat.display_party_summary(saved_party.party)
            next()
            return saved_party
        except(FileNotFoundError):
            print(f"No, I've never seen you.")
            time.sleep(2)
            print(f"Let's just make you a fresh party, mkay?")
            time.sleep(3)
            saved_party = create_new_party(name)
            acc.print_player_starting_summary(saved_party)
            Slayer_Combat.display_party_summary(saved_party)
            next()
            return {
                "name" : name,
                "party" : saved_party,
                "wiped" : False,
                "current_instance" : 0,
            }
            #can_save_party = True
    wt()
    
    '''if can_save_party:
        print()
        save_new_party = acc.yes_no(input('Would you like to save your new party?  '))
        if save_new_party:
            acc.save_party(group)
    
    group = {
        "name" : name,
        "party" : saved_party,
        "wiped" : False,
        "current_instance" : 0,
    }'''
   # return group