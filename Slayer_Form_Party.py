import Slayer_Accessory as acc
from Slayer_Accessory import whine
import Slayer_Heroes as heroes
import Slayer_UI as ui
import random

auto_name_choices = {
    'first' : ["Ath","Jodum","Prinny","Bubba","The Cake","Tedless","Muffy","Bildo","T-Bear","Miss Beans","Billy","Djub-Djub"],
    'middle' : ["the Messy","the Wrong","the Strange","the Savage","the Potent","the Silly-Hearted","the Smelly","the Aromatic","the Unkempt","the Poorly-Dressed","the Cruel","the Really Mean"],
    'last' : ["Wet-Nurse","Sensation","Meal-Worm","Armpit","Butthead","Doofus","Dork","Lamp","Smegma","Jerk","Monkey","Walrus","Doormat"]
}

async def get_name() -> str:
    await ui.say("Greetings!")
    name = (await ui.ask_text(f'What\'s your name, hero?  Assuming they gave you one.  {whine()}.  Your name, please:  ')).title()
    name = await acc.check_bad_name(name)
    await ui.say()
    await ui.say("Ooh, solid name.  I've been hosting this game for... some time... and that one's going in my top ten.  Maybe top twelve.")
    return name

async def print_recommended_classes(num_chars : int):
    await ui.say('\nRecommended Party Composition (based on party-size):')
    await ui.say()
    for _ in range(num_chars):
        await ui.say(random.choice(acc.get_hero_classes()))

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

async def print_current_party(party : list):
    for member in party:
        await ui.say(f"Hero:  {member.name}, Class:  {member.hero_class}")

async def name_heroine(prompt : str, choose_names : bool) -> str:
    if choose_names:
        return await acc.check_bad_heroine_name(await ui.ask_text(prompt))
    return auto_pick_name()

async def create_new_party(name: str) -> list:
    new_party = []
    await ui.clear()
    await acc.print_classes()
    await ui.say()
    party_count = await ui.ask_text("How many party members would you like to include (1 minimum, 8 maximum)?  ")
    value_ok = False
    while not value_ok:
        try:
            party_count = int(party_count)
            if party_count >= 1 and party_count <= 8:
                value_ok = True
            else:
                party_count = await ui.ask_text("I don't think that's a proper integer.  Try again (1 - 8):  ")
        except ValueError:
            party_count = await ui.ask_text("I don't think that's a proper integer.  Try again (1 - 8):  ")
    if party_count == 1:
        await ui.say("One?  One.  You chose One.  One....  Ok, One it is....")
        await ui.wait(2)
    elif party_count <= 3:
        await ui.say(f'{party_count}?!  Ballsy, I like it!')
        await ui.wait(2)
    await ui.clear()
    await print_recommended_classes(party_count)
    await ui.say()
    choose_composition = await ui.yes_no("Would you like to choose the composition of your party?  ")
    if choose_composition:
        await ui.say("My recommendations are garbage, so take them with a grain of salt....")
        await ui.pause()
    else:
        await ui.say("Wait... You want ME to choose for you?  Why, I'm so fucking excited, I think I need new underwear!")
        await ui.pause()
    await ui.say()
    choose_names = await ui.yes_no("Would you like to choose the names of your party members?  ")
    if choose_names:
        await ui.say("Probably a wise choice.  I'm shit at naming.")
        await ui.pause()
    else:
        await ui.say("Oh hell yes, I LOVE naming people.  Prepare to be emotionally attached, and perhaps disgusted a little bit too.")
        await ui.pause()
    if choose_composition:
        for _ in range(party_count):
            await ui.clear()
            await print_current_party(new_party)
            await ui.say()
            await acc.print_classes()
            await ui.say()
            await print_recommended_classes(party_count)
            await ui.say()
            selection = (await ui.ask_text("\nWhich Class would you like to add?  ")).strip().title().replace(' ', '_')
            while selection not in acc.get_hero_classes():
                selection = (await ui.ask_text("\nLet's try that again.  Of the listed Class options, which would you like to add?  ")).strip().title().replace(' ', '_')
            heroine_name = await name_heroine('\nOk, let\'s have a name for her:  ', choose_names)
            new_party.append(get_hero(selection, heroine_name))
    else:
        await ui.say()
        await ui.say("Fair enough.  Leave it to fate.  Fate's a drunk, but she's got good instincts.  Sometimes.")
        await ui.wait(2)
        members = get_default_classes(party_count)
        await ui.say()
        await ui.wait(2)
        await ui.clear()
        for selection in members:
            heroine_name = await name_heroine(f"Ok, let's have a name for your {selection}:  ", choose_names)
            new_party.append(get_hero(selection, heroine_name))
    return new_party

async def welcome_back(saved_party : dict) -> dict:
    await ui.pause()
    await ui.clear()
    saved_party = acc.refresh_party(saved_party, True)
    await acc.print_player_starting_summary(saved_party['party'])
    await ui.clear()
    await ui.show_party(saved_party['party'])
    await ui.pause()
    return saved_party

async def get_party() -> dict:
    name = await get_name()
    try:
        saved_party = acc.load_party(name)
        await ui.say(f"Ah yes, here you are: {name}!  The legend returns!  \nOk, are you ready to rock and ro......{whine()}\nSorry.  I'm thrilled.  Genuinely.  This is my thrilled face.")
        return await welcome_back(saved_party)
    except FileNotFoundError:
        await ui.say('Hmmmm.....')
        await ui.wait(1)
        name = (await ui.ask_text("I don't recognize you, and I don't think you're on [red]The List[/].\nWhat was that name again?  ")).title()
        name = await acc.check_bad_name(name)
        try:
            saved_party = acc.load_party(name)
            await ui.say(f"Oh, that's right, {name}!  You're the one who projectile-vomited into the fountain last night.  Legendary distance, by the way.{whine()}  Welcome back.")
            return await welcome_back(saved_party)
        except FileNotFoundError:
            await ui.say("No, I've never seen you.")
            await ui.wait(2)
            await ui.say(f"Let's just make you a fresh party, mkay, {name}?")
            await ui.wait(3)
            new_party = await create_new_party(name)
            await ui.clear()
            await acc.print_player_starting_summary(new_party)
            await ui.clear()
            await ui.show_party(new_party)
            await ui.pause()
            return {
                "name" : name,
                "party" : new_party,
                "wiped" : False,
                "times_run_dungeon" : 1,
                "narration" : True,
            }
