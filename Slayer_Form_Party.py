import Slayer_Accessory as acc
from Slayer_Accessory import cls, pause, whine
import Slayer_Combat as combat
import Slayer_Heroes as heroes
import random
import time
from colorama import Fore, Style

auto_name_choices = {
    'first' : ["Ath","Jodum","Prinny","Bubba","The Cake","Tedless","Muffy","Bildo","T-Bear","Miss Beans","Billy","Djub-Djub"],
    'middle' : ["the Messy","the Wrong","the Strange","the Savage","the Potent","the Silly-Hearted","the Smelly","the Aromatic","the Unkempt","the Poorly-Dressed","the Cruel","the Really Mean"],
    'last' : ["Wet-Nurse","Sensation","Meal-Worm","Armpit","Butthead","Doofus","Dork","Lamp","Smegma","Jerk","Monkey","Walrus","Doormat"]
}

def get_name() -> str:
    print("Greetings!")
    name = input(f'What\'s your name, hero?  Assuming they gave you one.  {whine()}.  Your name, please:  ').title()
    name = acc.check_bad_name(name)
    print()
    print("Ooh, solid name.  I've been hosting this game for... some time... and that one's going in my top ten.  Maybe top twelve.")
    return name
        
def print_recommended_classes(num_chars : int):
    print('\nRecommended Party Composition (based on party-size):')
    print()    
    for _ in range(num_chars):
        print(random.choice(acc.get_hero_classes()))

def get_default_classes(party_count : int) -> list:
    default_order =  ['Warrior', 'Cleric', 'Hunter', 'Shifter', 'Cleric', 'Sapper', 'Witch', 'Battle_Mage']
    return default_order[:party_count]


def get_hero(selection : str, name : str) -> object:
    hero_classes = {
        'Warrior' : heroes.Warrior,
        'Shifter' : heroes.Shifter,
        'Battle_Mage' : heroes.Battle_Mage,
        'Hunter' : heroes.Hunter,
        'Witch' : heroes.Witch,
        'Sapper' : heroes.Sapper,
        'Cleric' : heroes.Cleric,
    }
    hero_class = hero_classes.get(selection, heroes.Warrior) # if the selection is unrecognized, Warrior by default    
    return hero_class(name)

def auto_pick_name() -> str:
    first = random.choice(auto_name_choices['first'])
    middle = random.choice(auto_name_choices['middle'])
    last = random.choice(auto_name_choices['last'])
    return first + ' ' + middle + ' ' + last

def print_current_party(party : list):
    for member in party:
        print(f"Hero:  {member.name}, Class:  {member.hero_class}")

def name_heroine(prompt : str, choose_names : bool) -> str:
    if choose_names:
        return acc.check_bad_heroine_name(input(prompt))
    return auto_pick_name()

def create_new_party(name: str) -> list:
    new_party = []
    cls()
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
        except ValueError:
            party_count = input("I don't think that's a proper integer.  Try again (1 - 8):  ")
    if party_count == 1:
        print("One?  One.  You chose One.  One....  Ok, One it is....")
        time.sleep(2)
    elif party_count <= 3:
        print(f'{party_count}?!  Ballsy, I like it!')
        time.sleep(2)
    cls()
    print_recommended_classes(party_count)
    print()
    choose_composition = acc.yes_no("Would you like to choose the composition of your party?  ")
    if choose_composition:
        print("My recommendations are garbage, so take them with a grain of salt....")
        pause()
    else:
        print("Wait... You want ME to choose for you?  Why, I'm so fucking excited, I think I need new underwear!")
        pause()
    print()
    choose_names = acc.yes_no("Would you like to choose the names of your party members?  ")
    if choose_names:
        print("Probably a wise choice.  I'm shit at naming.")
        pause()
    else:
        print("Oh hell yes, I LOVE naming people.  Prepare to be emotionally attached, and perhaps disgusted a little bit too.")
        pause()
    if choose_composition:
        for _ in range(party_count):
            cls()
            print_current_party(new_party)
            print()
            acc.print_classes()
            print()
            print_recommended_classes(party_count)
            print()
            selection = input("\nWhich Class would you like to add?  ").strip().title().replace(' ', '_')
            while selection not in acc.get_hero_classes():
                selection = input("\nLet's try that again.  Of the listed Class options, which would you like to add?  ").strip().title().replace(' ', '_')
            heroine_name = name_heroine('\nOk, let\'s have a name for her:  ', choose_names)
            new_party.append(get_hero(selection, heroine_name))
    else:
        print()
        print("Fair enough.  Leave it to fate.  Fate's a drunk, but she's got good instincts.  Sometimes.")
        time.sleep(2)
        members = get_default_classes(party_count)
        print()
        time.sleep(2)
        cls()
        for selection in members:
            heroine_name = name_heroine(f"Ok, let's have a name for your {selection}:  ", choose_names)
            new_party.append(get_hero(selection, heroine_name))
    return new_party

def welcome_back(saved_party : dict) -> dict:
    pause()
    cls()
    saved_party = acc.refresh_party(saved_party, True)
    acc.print_player_starting_summary(saved_party['party'])
    cls()
    combat.display_party_summary(saved_party['party'])
    pause()
    return saved_party

def get_party() -> dict:
    name = get_name()
    try:
        saved_party = acc.load_party(name)
        print(f"Ah yes, here you are: {name}!  The legend returns!  \nOk, are you ready to rock and ro......{whine()}\nSorry.  I'm thrilled.  Genuinely.  This is my thrilled face.")
        return welcome_back(saved_party)
    except FileNotFoundError:
        print('Hmmmm.....')
        time.sleep(1)
        name = input(f"I don't recognize you, and I don't think you're on {Fore.RED + Style.BRIGHT}The List{Style.RESET_ALL}.\nWhat was that name again?  ").title()
        name = acc.check_bad_name(name)
        try:
            saved_party = acc.load_party(name)
            print(f"Oh, that's right, {name}!  You're the one who projectile-vomited into the fountain last night.  Legendary distance, by the way.{whine()}  Welcome back.")
            return welcome_back(saved_party)
        except FileNotFoundError:
            print(f"No, I've never seen you.")
            time.sleep(2)
            print(f"Let's just make you a fresh party, mkay, {name}?")
            time.sleep(3)
            new_party = create_new_party(name)
            cls()
            acc.print_player_starting_summary(new_party)
            cls()
            combat.display_party_summary(new_party)
            pause()
            return {
                "name" : name,
                "party" : new_party,
                "wiped" : False,
                "times_run_dungeon" : 1,
                "narration" : True,
            }