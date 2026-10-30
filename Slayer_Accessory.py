import random
from msvcrt import kbhit, getch
import time
from colorama import init
from colorama.winterm import WinTerm
import pandas as pd
import joblib as jb
import sys

init()



yes = ['YES','Y']
no = ['NO','N']

whines = ["Jesus Christ, this dungeon's plumbing is a nightmare. Sorry, I'm good, I'm good", "Would you stop that sh-- oh, sorry, I was yelling at the banshee in the walls", "I haven't had a day off since the Third Age, but sure, let's go", "I'm running on four hours of sleep and pure spite, but for YOU? Anything", "Why do I do this to myself?  I told mother I would never.... Umm Hi!", "Sometimes, I just care too fucking much about this, that's my problem.  What?  Oh!"]

items_df = pd.read_csv('supporting_docs/items.csv')
hero_stats_df = pd.read_csv('supporting_docs/hero_stats.csv')
mobs_df = pd.read_csv('supporting_docs/mobs.csv')
mob_equipment_df = pd.read_csv('supporting_docs/mob_equipment.csv')

def dev_mode() -> bool:
    return True

def get_hero_classes():
    return ['Warrior', 'Shifter', 'Battle_Mage', 'Hunter', 'Witch', 'Sapper', 'Cleric']

def yes_no(prompt : str) -> bool:
    response = input(prompt).strip().upper()
    while (response not in yes) and (response not in no):
        response = input("Let's pretend you didn't type that and try again.  Yes or No?:  ").strip().upper()
    return response in yes

def pause():
    done = False
    while not done:
        if kbhit():
            key = ord(getch())
            if key == 13:
                print()
                done = True
        time.sleep(0.02) # a very brief sleep keeps the CPU core from running at 100%, waiting for a response here

def cls():
    winterm = WinTerm()
    winterm.erase_screen(mode=2)
    print()
    print()

def end(full = False):
    print()
    print("The End.")
    if full:
        pass # TO Do - full ending
    print()
    print()
    sys.exit()

def multi_roll(low_range : int, high_range : int) -> int:
    return random.randint(low_range, high_range)

def roll_percent(chance) -> bool:
    return multi_roll(1, 100) <= chance # every stat is a % chance: roll 1-100, succeed at or under the stat

def get_dice_cutoffs() -> dict: ### These are only for heroine, not mobs.  Every other stat is a % chance (see roll_percent)
    return {
        'crit_mult_cutoff' : 2.5,
        'speed_cutoff' : 40,
    }

db = ["DICK BUBBLE","DICK-BUBBLE","DICKBUBBLE","DICK BUBBLES", "DICKBUBBLES","DICK-BUBBLES","DICK-BBL","DICKBBL", "DICK-BBLS", "DICKBBLS", "DICK BBL", "DICK BBLS"]

def get_dice_cutoffs_mobs() -> dict:  ### These are only for mobs, not heroine.  Every other stat is a % chance (see roll_percent)
    return {
        'crit_mult_cutoff' : 5,
        'speed_cutoff' : 40,
    }

def print_classes():
    print('Class Options:')
    print()
    for hero_class in get_hero_classes():
        print(hero_class)

def save_party(party : dict):
    name = party['name'].title()
    jb.dump(party, f"saved_parties/{name}.pkl")
    print(f"Your party has been saved as {name}.")
    print(f"Keep track of this saved name if you want to recover your party: {name}")
    pause()

def load_party(name : str) -> dict:
    return jb.load(f'saved_parties/{name.title()}.pkl')

def whine() -> str:
    return "..." + random.choice(whines)

def print_player_starting_summary(party : list):
    for dudette in party:
        print(f"{dudette.name}:  {dudette.hero_class}")
        print('Inventory:  ')
        for inv_item in dudette.inv:
            print(get_item(inv_item)['item_desc'])
        print(f"Starting Health: {int(round(dudette.starting_health, 0))}")
        print()
    pause()

def check_bad_name(name : str) -> str:
    name = name.strip()
    while name.upper() in db or name == '':
        print('No.')
        time.sleep(2)
        if name.upper() in db:
            name = input(f'No, Bubba!  {whine()}.  Try again!  ').title().strip()
        else:
            name = input(f"Your NAME, buddy!  The thing your mom yells across the yard!  {whine()}.  ").title().strip()
    return name

def check_bad_heroine_name(name : str) -> str:
    name = name.strip()
    while name.upper() in db or name == '':
        print('Nope.')
        time.sleep(2)
        if name.upper() in db:
            name = input(f"Stopit!!  Take this more seriously.  What name do you want to give her, Bubba?  {whine()}.  ").strip()
        else:
            name = input(f"Stopit!!  Take this more seriously.  What name do you want to give her?  {whine()}.  ").strip()
    return name

def get_items() -> pd.DataFrame:
    return items_df

def get_item(item_name : str) -> pd.Series:
    return items_df[items_df['item'] == item_name].iloc[0]

def get_stats() -> pd.DataFrame:
    return hero_stats_df

def get_mobs() -> pd.DataFrame:
    return mobs_df

def get_mob_equipment() -> pd.DataFrame:
    return mob_equipment_df

def get_mob_stats(mob_class: str, mobs_df: pd.DataFrame) -> dict:
    row = mobs_df[mobs_df['mob_class'] == mob_class].iloc[0]
    return row.to_dict() # every column of mobs.csv, keyed by its column name (the enraged_ versions included)

def get_mob_inv(mob_class: str) -> list:
    return list(mob_equipment_df.loc[mob_equipment_df['mob_class'] == mob_class, 'item'])

def initialize_mob(mob: object, mobs_df: pd.DataFrame):
    row = mobs_df[mobs_df['mob_class'] == mob.mob_class].iloc[0]
    mob.attack_style = row['attack_style']
    mob.stats = get_mob_stats(mob.mob_class, mobs_df)
    mob.inv = get_mob_inv(mob.mob_class)
    mob.starting_health = mob.stats['starting_hp']
    mob.health = mob.stats['starting_hp']
    mob.is_dead = False
    mob.enraged = False
    mob.is_mob = True
    mob.starting_ai = row['ai']
    mob.enraged_ai = row['enraged_ai']
    return mob

def generic_wipe_taunts() -> list:
    return [
        "\n{mob} casually stands over {victim}'s corpse, mumbling, \"Not today....\"",
        "\n{mob} shouts in triumph!",
        "\n{mob} starts to shake, then suddenly begins to bellow with terrible, evil laughter.  \"Puny weaklings!\"",
        "\n{mob} sits atop {victim}'s head, grinding in, real deep.",
        "\n{mob} begins to pick at what remains of {victim}.  \"Well that was easy!\"",
    ]

def item_specific_wipe_taunts() -> list:
    return [
        "\n{mob} walks over to pick up {victim}'s {item}, immediately hurling it into {victim2}'s remains.  \"Take That!!\", they scream!!\nJesus Christ, what a CUNT!!",
        "\n{mob} immediately starts cackling, eyeing {victim}'s {item}.  \"What a pathetic little garbage weapon that was!  No wonder they wiped!!\"\nI hope you come back and teach these bitches a lesson!!",
        "\n{mob} sneers at {victim}'s dead body.  \"{item}?  Really?  You thought you could take ME down with your {item}??!!!\"\nNow was that really necessary.  Don't take their shit!!",
        "\nWith her last dying breath, {victim} makes one more attempt with the {item}, completely missing {mob}, who begins to chuckle.  \"Guess I'd try the same, but, that was kinda sad....\"\nDon't let them get away with that.  Come back and take them down next time!!",
    ]

def get_loot(mob : object, party_dict : dict) -> dict:
    print('Add looting process here, per party member, from specific mob loot-tables in the items.csv')
    pause()
    return party_dict

def get_stat_increases(party_dict : dict) -> dict:
    print('Add stat increase process here, per party member.  Right now, NOT specified by mob, or difficulty thereof, but this should probably be implemented.')
    pause()
    return party_dict

def refresh_party(party_dict : dict, increment : bool) -> dict:
    if increment:
        party_dict['times_run_dungeon'] += 1
    party_dict['wiped'] = False
    for heroine in party_dict['party']:
        heroine.is_dead = False
        heroine.health = heroine.starting_health
    return party_dict

def wipe_party(party_dict : dict) -> dict:
    party_dict['wiped'] = True
    for heroine in party_dict['party']:
        heroine.is_dead = True
        heroine.health = 0
    return party_dict

