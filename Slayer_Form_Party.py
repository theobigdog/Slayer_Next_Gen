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
    name = str(input(f'What\'s your name, hero?  Assuming they gave you one.  {whine()}.  Your name, please:  ')).title()
    name = acc.check_bad_name(name)
    print()
    print(f"Ooh, solid name.  I've been hosting this game for... some time... and that one's going in my top ten.  Maybe top twelve.")
    return name
        
def print_recommended_classes(num_chars : int):
    print('\nRecommended Party Composition (based on party-size):')
    print()    
    for _ in range(num_chars):
        print(random.choice(acc.get_hero_classes()))

def get_default_classes(party_count : int) -> list:
    # 0: Warrior, 1: Shifter, 2: Battle_Mage, 3: Hunter, 4: Witch, 5: Sapper, 6: Cleric
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
        return ['Warrior', 'Cleric', 'Hunter', 'Shifter', 'Cleric', 'Sapper', 'Witch']
    elif party_count == 8:
        return ['Warrior', 'Cleric', 'Hunter', 'Shifter', 'Cleric', 'Sapper', 'Witch', 'Battle_Mage']
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
    elif selection == 'Witch':
        return heroes.Witch(name)
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
    if party_count == 1:
        print("One?  One.  You chose One.  One....  Ok, One it is....")
        time.sleep(2)
    elif party_count <= 3:
        print(f'{party_count}?!  Ballsy, I like it!')
        time.sleep(2)
    wt()
    print_recommended_classes(party_count)
    print()
    choose_composition = acc.yes_no(input("Would you like to choose the composition of your party?  "))
    if choose_composition:
        print("My recommendations are garbage, so take them with a grain of salt....")
        next()
    else:
        print("Wait... You want ME to choose for you?  Why, I'm so fucking excited, I think I need new underwear!")
        next()
    print()
    choose_names = acc.yes_no(input("Would you like to choose the names of your party members?  "))
    if choose_names:
        print("Probably a wise choice.  I'm shit at naming.")
        next()
    else:
        print("Oh hell yes, I LOVE naming people.  Prepare to be emotionally attached, and perhaps disgusted a little bit too.")
        next()
    if choose_composition:
        #print()
        #print("Fair enough.  Leave it to fate.  Fate's a drunk, but she's got good instincts.  Sometimes.")
        #time.sleep(2)
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
                selection = input("Let's try that again.  Of the listed Class options, which would you like to add?  ")
            if choose_names:
                print()
                name_choice = str(input("Ok, let's have a name for her:  "))
                name_choice = acc.check_bad_heroine_name(name_choice)
                new_party.append(get_hero(selection, name_choice))
            else:
                new_party.append(get_hero(selection, auto_pick_name()))
    else:
        print()
        print("Fair enough.  Leave it to fate.  Fate's a drunk, but she's got good instincts.  Sometimes.")
        time.sleep(2)
        members = get_default_classes(party_count)
        print()
        time.sleep(2)
        wt()
        for i in range(party_count):
            selection = members[i]
            if choose_names:
                name_choice = str(input("Ok, let's have a name for your " + selection + ":  "))
                name_choice = acc.check_bad_heroine_name(name_choice)
                new_party.append(get_hero(selection, name_choice))
            else: 
                new_party.append(get_hero(selection, auto_pick_name()))
    return new_party

def get_party() -> dict:
    name = get_name()
    saved_party = []
    try:
        saved_party = acc.load_party(name)
        print(f"Ah yes, here you are: {name}!  The legend returns!  \nOk, are you ready to rock and ro......{whine()}\nSorry.  I'm thrilled.  Genuinely.  This is my thrilled face.")
        next()
        wt()
        saved_party = acc.refresh_party(saved_party, True)
        acc.print_player_starting_summary(saved_party['party'])
        wt()
        Slayer_Combat.display_party_summary(saved_party['party'])
        next()
        return saved_party
    except(FileNotFoundError):
        print('Hmmmm.....')
        time.sleep(1)
        name = str(input(f"I don't recognize you, and I don't think you're on The List.\nWhat was that name again?  ")).title()
        name = acc.check_bad_name(name)
        try:
            saved_party = acc.load_party(name)
            print(f"Oh, that's right, {name}!  You're the one who projectile-vomited into the fountain last night.  Legendary distance, by the way.{whine()}  Welcome back.")
            next()
            wt()
            saved_party = acc.refresh_party(saved_party, True)
            acc.print_player_starting_summary(saved_party['party'])
            wt()
            Slayer_Combat.display_party_summary(saved_party['party'])
            next()
            return saved_party
        except(FileNotFoundError):
            print(f"No, I've never seen you.")
            time.sleep(2)
            print(f"Let's just make you a fresh party, mkay, {name}?")
            time.sleep(3)
            saved_party = create_new_party(name)
            wt()
            acc.print_player_starting_summary(saved_party)
            wt()
            Slayer_Combat.display_party_summary(saved_party)
            next()
            return {
                "name" : name,
                "party" : saved_party,
                "wiped" : False,
                "times_run_dungeon" : 1,
                "narration" : True,
            }