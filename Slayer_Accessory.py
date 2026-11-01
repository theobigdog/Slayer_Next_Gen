import random
import csv
import json
import sys
from pathlib import Path
import Slayer_UI as ui


whines = ["Jesus Christ, this dungeon's plumbing is a nightmare. Sorry, I'm good, I'm good", "Would you stop that sh-- oh, sorry, I was yelling at the banshee in the walls", "I haven't had a day off since the Third Age, but sure, let's go", "I'm running on four hours of sleep and pure spite, but for YOU? Anything", "Why do I do this to myself?  I told mother I would never.... Umm Hi!", "Sometimes, I just care too fucking much about this, that's my problem.  What?  Oh!"]

game_dir = Path(__file__).parent # the folder these .py files live in, so the game finds its files no matter where it's launched from
docs_dir = game_dir / 'supporting_docs'
save_dir = game_dir / 'saved_parties'

def read_table(file_name : str) -> list:
    """Read one CSV from supporting_docs into a list of rows, one dict per row, keyed by the
    column names. Each column is converted as a whole, the way pandas did it: all whole
    numbers -> int, any decimals -> float, all TRUE/FALSE -> True/False, anything else stays
    text. A blank cell becomes None."""
    with open(docs_dir / file_name, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    columns = rows[0].keys() if rows else []
    for column in columns:
        filled = [row[column] for row in rows if row[column] != '']
        if filled and all(value in ('TRUE', 'FALSE') for value in filled):
            convert = lambda value: value == 'TRUE'
        elif filled and all(_is_number(value, int) for value in filled):
            convert = int
        elif filled and all(_is_number(value, float) for value in filled):
            convert = float
        else:
            convert = str
        for row in rows:
            row[column] = None if row[column] == '' else convert(row[column])
    return rows

def _is_number(value : str, kind) -> bool:
    try:
        kind(value)
        return True
    except ValueError:
        return False

def find_row(table : list, column : str, value) -> dict:
    """The first row whose column holds value (a copy, so changing it can't change the table)."""
    return dict(next(row for row in table if row[column] == value))

items_table = read_table('items.csv')
hero_stats_table = read_table('hero_stats.csv')
mobs_table = read_table('mobs.csv')
mob_equipment_table = read_table('mob_equipment.csv')

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

def party_to_data(party_dict : dict) -> dict:
    """The party as plain data (text, numbers, lists, dicts) that JSON can store.
    Each heroine keeps every attribute she has, so anything added to the heroine
    classes later (stat increases, loot) gets saved automatically."""
    data = dict(party_dict)
    data['party'] = [dict(vars(heroine)) for heroine in party_dict['party']]
    return data

def party_from_data(data : dict) -> dict:
    """The reverse of party_to_data: rebuild each heroine as her own class, attributes and all."""
    import Slayer_Heroes # imported here, because Slayer_Heroes imports this file
    party_dict = dict(data)
    party_dict['party'] = []
    for saved in data['party']:
        hero_class = getattr(Slayer_Heroes, saved['hero_class'])
        heroine = hero_class.__new__(hero_class) # an empty heroine: no new stats rolled
        vars(heroine).update(saved)
        party_dict['party'].append(heroine)
    return party_dict

async def save_party(party : dict):
    name = party['name'].title()
    save_dir.mkdir(exist_ok=True) # create the folder if it's missing
    with open(save_dir / f"{name}.json", 'w', encoding='utf-8') as f:
        json.dump(party_to_data(party), f, indent=2)
    await ui.say(f"Your party has been saved as {name}.")
    await ui.say(f"Keep track of this saved name if you want to recover your party: {name}")
    await ui.pause()

def load_party(name : str) -> dict:
    with open(save_dir / f'{name.title()}.json', encoding='utf-8') as f: # a missing save raises FileNotFoundError, which get_party relies on
        return party_from_data(json.load(f))

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

def get_items() -> list:
    return items_table

def get_item(item_name : str) -> dict:
    return find_row(items_table, 'item', item_name)

def get_stats() -> list:
    return hero_stats_table

def get_mobs() -> list:
    return mobs_table

def get_mob_equipment() -> list:
    return mob_equipment_table

def get_mob_stats(mob_class: str, mobs_table: list) -> dict:
    return find_row(mobs_table, 'mob_class', mob_class) # every column of mobs.csv, keyed by its column name (the enraged_ versions included)

def get_mob_inv(mob_class: str) -> list:
    return [row['item'] for row in mob_equipment_table if row['mob_class'] == mob_class]

def initialize_mob(mob: object, mobs_table: list):
    row = find_row(mobs_table, 'mob_class', mob.mob_class)
    mob.attack_style = row['attack_style']
    mob.stats = get_mob_stats(mob.mob_class, mobs_table)
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

