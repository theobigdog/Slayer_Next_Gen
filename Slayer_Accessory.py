import random
import pandas as pd
import joblib as jb
import sys
from pathlib import Path
import Slayer_UI as ui


whines = ["Jesus Christ, this dungeon's plumbing is a nightmare. Sorry, I'm good, I'm good", "Would you stop that sh-- oh, sorry, I was yelling at the banshee in the walls", "I haven't had a day off since the Third Age, but sure, let's go", "I'm running on four hours of sleep and pure spite, but for YOU? Anything", "Why do I do this to myself?  I told mother I would never.... Umm Hi!", "Sometimes, I just care too fucking much about this, that's my problem.  What?  Oh!"]

game_dir = Path(__file__).parent # the folder these .py files live in, so the game finds its files no matter where it's launched from
docs_dir = game_dir / 'supporting_docs'
save_dir = game_dir / 'saved_parties'

items_df = pd.read_csv(docs_dir / 'items.csv')
hero_stats_df = pd.read_csv(docs_dir / 'hero_stats.csv')
mobs_df = pd.read_csv(docs_dir / 'mobs.csv')
mob_equipment_df = pd.read_csv(docs_dir / 'mob_equipment.csv')

def dev_mode() -> bool:
    return True

def get_hero_classes():
    return ['Warrior', 'Shifter', 'Battle_Mage', 'Hunter', 'Witch', 'Sapper', 'Cleric']

async def end(full = False):
    await ui.say()
    await ui.say("The End.")
    if full:
        pass # TO Do - full ending
    await ui.say()
    await ui.say()
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

async def print_classes():
    await ui.say('Class Options:')
    await ui.say()
    for hero_class in get_hero_classes():
        await ui.say(hero_class)

async def save_party(party : dict):
    name = party['name'].title()
    save_dir.mkdir(exist_ok=True) # create the folder if it's missing
    jb.dump(party, save_dir / f"{name}.pkl")
    await ui.say(f"Your party has been saved as {name}.")
    await ui.say(f"Keep track of this saved name if you want to recover your party: {name}")
    await ui.pause()

def load_party(name : str) -> dict:
    return jb.load(save_dir / f'{name.title()}.pkl')

def whine() -> str:
    return "..." + random.choice(whines)

async def print_player_starting_summary(party : list):
    for dudette in party:
        await ui.say(f"{dudette.name}:  {dudette.hero_class}")
        await ui.say('Inventory:  ')
        for inv_item in dudette.inv:
            await ui.say(get_item(inv_item)['item_desc'])
        await ui.say(f"Starting Health: {int(round(dudette.starting_health, 0))}")
        await ui.say()
    await ui.pause()

async def check_bad_name(name : str) -> str:
    name = name.strip()
    while name.upper() in db or name == '':
        await ui.say('No.')
        await ui.wait(2)
        if name.upper() in db:
            name = (await ui.ask_text(f'No, Bubba!  {whine()}.  Try again!  ')).title().strip()
        else:
            name = (await ui.ask_text(f"Your NAME, buddy!  The thing your mom yells across the yard!  {whine()}.  ")).title().strip()
    return name

async def check_bad_heroine_name(name : str) -> str:
    name = name.strip()
    while name.upper() in db or name == '':
        await ui.say('Nope.')
        await ui.wait(2)
        if name.upper() in db:
            name = (await ui.ask_text(f"Stopit!!  Take this more seriously.  What name do you want to give her, Bubba?  {whine()}.  ")).strip()
        else:
            name = (await ui.ask_text(f"Stopit!!  Take this more seriously.  What name do you want to give her?  {whine()}.  ")).strip()
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

async def get_loot(mob : object, party_dict : dict) -> dict:
    await ui.say('Add looting process here, per party member, from specific mob loot-tables in the items.csv')
    await ui.pause()
    return party_dict

async def get_stat_increases(party_dict : dict) -> dict:
    await ui.say('Add stat increase process here, per party member.  Right now, NOT specified by mob, or difficulty thereof, but this should probably be implemented.')
    await ui.pause()
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

