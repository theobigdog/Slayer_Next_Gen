import random
import re
import csv
import json
import zlib
import base64
import hmac
import sys
from pathlib import Path
from Slayer_UI import say, wait, pause, ask_text


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
stat_growth_table = read_table('stat_growth.csv')

def dev_mode() -> bool:
    return True

def get_hero_classes():
    return ['Warrior', 'Shifter', 'Battle_Mage', 'Hunter', 'Witch', 'Sapper', 'Cleric']

def class_label(hero_class : str) -> str:
    return hero_class.replace('_', ' ') # 'Battle_Mage' is the code's name for her; players see 'Battle Mage'

async def end(full = False):
    await say()
    await say("The End.")
    if full:
        pass # TO Do - full ending
    await say()
    await say()
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
    await say('Class Options:')
    await say()
    for hero_class in get_hero_classes():
        await say(class_label(hero_class))

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

# Saves are scrambled so players can't just open one and read or edit their stats.
# Not real security (anyone with this code can unscramble a save), but it stops casual
# peeking, and the seal below catches edits. Changing save_key makes every old save unreadable.
save_key = b"Happy's toe taps: left, left, right, stomp, wiggle"

class TamperedSave(FileNotFoundError):
    """A save that's been edited or is broken. It counts as 'no save found' (get_party
    already handles that), and can be caught on its own later for a 'nice try' line."""

def scramble(text : str) -> str:
    packed = zlib.compress(text.encode('utf-8'))
    mixed = bytes(byte ^ save_key[i % len(save_key)] for i, byte in enumerate(packed))
    seal = hmac.new(save_key, packed, 'sha256').hexdigest()[:16] # changes if a single byte of the save changes
    return seal + base64.b64encode(mixed).decode('ascii')

def unscramble(blob : str) -> str:
    try:
        seal, mixed = blob[:16], base64.b64decode(blob[16:])
        packed = bytes(byte ^ save_key[i % len(save_key)] for i, byte in enumerate(mixed))
        if not hmac.compare_digest(seal, hmac.new(save_key, packed, 'sha256').hexdigest()[:16]):
            raise TamperedSave('save was edited')
        return zlib.decompress(packed).decode('utf-8')
    except TamperedSave:
        raise
    except Exception as error: # bad base64, bad zlib data, wrong key...
        raise TamperedSave(f'save is unreadable: {error}')

async def save_party(party : dict):
    name = party['name'].title()
    save_dir.mkdir(exist_ok=True) # create the folder if it's missing
    with open(save_dir / f"{name}.sav", 'w', encoding='ascii') as f:
        f.write(scramble(json.dumps(party_to_data(party))))
    await say(f"Your party has been saved as {name}.")
    await say(f"Keep track of this saved name if you want to recover your party: {name}")
    await pause()

def load_party(name : str) -> dict:
    with open(save_dir / f'{name.title()}.sav', encoding='ascii') as f: # a missing save raises FileNotFoundError, which get_party relies on
        return party_from_data(json.loads(unscramble(f.read())))

def whine() -> str:
    return "..." + random.choice(whines)

async def print_player_starting_summary(party : list):
    for dudette in party:
        await say(f"{dudette.name}:  {class_label(dudette.hero_class)}")
        await say('Inventory:  ')
        for inv_item in dudette.inv:
            await say(get_item(inv_item)['item_desc'])
        await say(f"Starting Health: {int(round(dudette.starting_health, 0))}")
        await say()
    await pause()

async def check_bad_name(name : str) -> str:
    name = name.strip()
    while name.upper() in db or name == '':
        await say('[narr]No.[/]')
        await wait(2)
        if name.upper() in db:
            name = (await ask_text(f'[narr]No, Bubba!  {whine()}.  Try again![/]  ')).title().strip()
        else:
            name = (await ask_text(f"[narr]Your NAME, buddy!  The thing your mom yells across the yard!  {whine()}.[/]  ")).title().strip()
    return name

async def check_bad_heroine_name(name : str) -> str:
    name = name.strip()
    while name.upper() in db or name == '':
        await say('[narr]Nope.[/]')
        await wait(2)
        if name.upper() in db:
            name = (await ask_text(f"[narr]Stopit!!  Take this more seriously.  What name do you want to give her, Bubba?  {whine()}.[/]  ")).strip()
        else:
            name = (await ask_text(f"[narr]Stopit!!  Take this more seriously.  What name do you want to give her?  {whine()}.[/]  ")).strip()
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
        "\n{mob} walks over to pick up {victim}'s {item}, immediately hurling it into {victim2}'s remains.  \"Take That!!\", they scream!!\n[narr]Jesus Christ, what a CUNT!![/]",
        "\n{mob} immediately starts cackling, eyeing {victim}'s {item}.  \"What a pathetic little garbage weapon that was!  No wonder they wiped!!\"\n[narr]I hope you come back and teach these bitches a lesson!![/]",
        "\n{mob} sneers at {victim}'s dead body.  \"{item}?  Really?  You thought you could take ME down with your {item}??!!!\"\n[narr]Now was that really necessary.  Don't take their shit!![/]",
        "\nWith her last dying breath, {victim} makes one more attempt with the {item}, completely missing {mob}, who begins to chuckle.  \"Guess I'd try the same, but, that was kinda sad....\"\n[narr]Don't let them get away with that.  Come back and take them down next time!![/]",
    ]

# Afflictions: "loot" that isn't a prize. A mob gives it to one random heroine, she's stuck with it for the
# rest of that dungeon run (and can use it as an attack), and it clears up when the next run starts.
AFFLICTIONS = {
    'happys_norovirus_regurgitation': {
        'caught': "{mob} leans in close and coughs right in {who}'s face.  [narr]Aaaand {who} has caught Happy's norovirus.  She's stuck with it for the rest of this run, but hey, now she can puke on people too.[/]",
        'cured': "[narr]Good news: {who}'s norovirus finally cleared up.[/]",
    },
}

# ---------- loot and the bag ---------------------------------------------------
# Loot comes from items.csv: a row whose source is a mob's class is in that mob's loot table, and its
# drop_chance (%) is rolled for each one of those mobs that died. Happy hands his over after the tavern.
# Each heroine's bag holds BAG_SIZE items. The Token and afflictions don't count. Loot is kept across runs
# and through wipes. A full bag means dropping something (starting gear too), and dropped is gone for good.
# Consumables (a uses number) get used up; finding another tops up the uses. Trinkets (attack_type trinket)
# can't be used in a fight: they give their bonus (e.g. luck+5) while she carries them.
BAG_SIZE = 6
MAX_STACK = 2 # a consumable tops up to at most twice its uses

def not_in_bag(item_name : str) -> bool:
    return item_name == 'token_of_the_wise_witch' or item_name in AFFLICTIONS

def bag(heroine : object) -> list:
    """What counts against her 6: what she's carrying, plus starting gear that's only gone for this run
    (a used Big Badda Boom) and comes back next run."""
    dropped = getattr(heroine, 'dropped', [])
    pending = [item for item in heroine.starting_inv if item not in heroine.inv and item not in dropped]
    return [item for item in heroine.inv + pending if not not_in_bag(item)]

def describe_item(item : dict, left : int = None) -> str:
    """A menu label: 'Bastard Sword (7 - 11 damage)', 'Lucky Rabbit's Foot (+5 luck)', 'Fire Bomb (15 - 25 damage, 2 left)'."""
    desc, low, high = item['item_desc'], item['damage_low'], item['damage_high']
    if item['attack_type'] == 'hail_mary':
        return f'{desc} (hail mary)'
    if item['attack_type'] == 'trinket':
        return f"{desc} ({', '.join(f'{sign}{amount} {stat}' for stat, sign, amount in parse_bonus(item['bonus']))})"
    what = f'{low} - {high} damage' if low >= 0 else f'{-high} - {-low} healing'
    if item['uses']:
        what += f", {item['uses']} uses" if left is None else f", {left} left"
    return f'{desc} ({what})'

def parse_bonus(bonus) -> list:
    """'luck+5 dodge+2' -> [('luck', '+', 5), ('dodge', '+', 2)]"""
    return [(stat, sign, int(amount)) for stat, sign, amount in re.findall(r'(\w+)([+-])(\d+)', bonus or '')]

def stat_bonus(heroine : object, stat : str) -> int:
    """What her trinkets add to one stat right now."""
    total = 0
    for item_name in heroine.inv:
        item = get_item(item_name)
        if item['attack_type'] == 'trinket':
            total += sum(amount if sign == '+' else -amount for name, sign, amount in parse_bonus(item['bonus']) if name == stat)
    return total

def uses_left(heroine : object, item_name : str):
    return getattr(heroine, 'uses', {}).get(item_name)

def add_item(heroine : object, item : dict) -> str:
    """Put a found item in her bag (room already checked). Returns what happened, for the narration."""
    heroine.uses = getattr(heroine, 'uses', {})
    if item['uses'] and item['item'] in heroine.inv:
        heroine.uses[item['item']] = min(item['uses'] * MAX_STACK, heroine.uses.get(item['item'], 0) + item['uses'])
        return f"[narr]Topped up: {heroine.name} now has {heroine.uses[item['item']]} uses of {item['item_desc']}.[/]"
    heroine.inv.append(item['item'])
    if item['uses']:
        heroine.uses[item['item']] = item['uses']
    return f"[narr]{heroine.name} takes {item['item_desc']}.[/]"

def drop_item(heroine : object, item_name : str):
    """Gone for good, starting gear included (it won't come back next run)."""
    if item_name in heroine.inv:
        heroine.inv.remove(item_name)
    if item_name in heroine.starting_inv:
        heroine.dropped = getattr(heroine, 'dropped', []) + [item_name]
    getattr(heroine, 'uses', {}).pop(item_name, None)

def use_up(heroine : object, item_name : str):
    """She just used a consumable: one less use, and it's gone at zero."""
    left = uses_left(heroine, item_name)
    if left is None:
        return
    heroine.uses[item_name] = left - 1
    if left - 1 <= 0:
        heroine.inv.remove(item_name)
        del heroine.uses[item_name]

async def give_loot(item : dict, source : str, party : list):
    """One piece of loot: the player picks who gets it (or leaves it), and makes room if her bag is full."""
    from ast import literal_eval
    from Slayer_UI import choose
    able = [heroine for heroine in party if heroine.hero_class in literal_eval(item['classes'])]
    label = describe_item(item)
    if not able:
        await say(f"From {source}: {label}.  [narr]Nobody here can use it, so it stays on the floor.[/]")
        return
    await say(f"From {source}: {label}.")
    while True:
        names = [f"{x.name}  ({class_label(x.hero_class)}, bag {len(bag(x))}/{BAG_SIZE})" for x in able]
        pick = await choose(f"Who gets {item['item_desc']}?  ", names + ['Leave it behind'], "One of THOSE numbers, please:  ")
        if pick == len(able):
            await say(f"[narr]Fine.  {item['item_desc']} stays on the floor.  Somebody's gonna trip on that.[/]")
            return
        who = able[pick]
        if (item['uses'] and item['item'] in who.inv) or len(bag(who)) < BAG_SIZE:
            await say(add_item(who, item))
            return
        droppable = [x for x in who.inv if not not_in_bag(x)]
        labels = [describe_item(get_item(x), uses_left(who, x)) for x in droppable]
        out = await choose(f"{who.name}'s bag is full.  Drop something to make room for {item['item_desc']}?  ",
                           labels + ['Never mind, pick someone else'], "One of THOSE numbers, please:  ")
        if out == len(droppable):
            continue
        drop_item(who, droppable[out])
        await say(f"[narr]{who.name} tosses her {get_item(droppable[out])['item_desc']}.[/]")
        await say(add_item(who, item))
        return

async def get_loot(mob : object, party_dict : dict, others : list = ()) -> dict:
    """After a fight: mob (here, Happy) hands over his loot, and every one of the others that died drops
    theirs, each piece rolled against its drop_chance. An affliction (the norovirus) goes to one random
    heroine for the rest of the run instead."""
    from ast import literal_eval
    party = party_dict['party']
    found = []
    for source in [mob] + [m for m in others if m is not mob and m.is_dead]:
        for item in [row for row in items_table if row['source'] == source.mob_class]:
            if item['item'] in AFFLICTIONS:
                able = [heroine for heroine in party if heroine.hero_class in literal_eval(item['classes'])]
                for heroine in party: # only ever one of them has it
                    if item['item'] in heroine.inv:
                        heroine.inv.remove(item['item'])
                if able:
                    who = random.choice(able)
                    who.inv.append(item['item'])
                    await say(AFFLICTIONS[item['item']]['caught'].format(mob=source.name, who=who.name))
            elif roll_percent(item['drop_chance'] if item['drop_chance'] is not None else 100):
                found.append((item, source.name))
    if found:
        await say(f"\n[narr]Loot!  Let's see what's on the floor.[/]")
    for item, source in found:
        await give_loot(item, source, party)
    await pause()
    return party_dict

# ---------- stat bonuses after a fight ------------------------------------------
# Every heroine (dead, alive or blown to bits) improves 1-4 stats by 1-3 points each, plus 1-3 max HP.
# Which stats: every stat has a base chance, times her class leaning (stat_growth.csv: 1 = normal,
# 2-3 = leans that way, 0.5 = rarely), times a bonus for what she did this fight (her tally).
# Gains shrink as a stat gets high, and nothing goes past 95% (fear goes DOWN, to no lower than 5).
# Players never see the numbers, just the odd hint; dev mode prints them all.
GROWTH_STATS = ['hit', 'crit_chance', 'crit_mult', 'luck', 'expertise', 'toughness', 'dodge', 'parry', 'fear', 'heal_chance', 'aoe_heal_chance']
DOING = { # what she did -> the stats it helps
    'attacks': ['hit', 'expertise'], 'crits': ['crit_chance', 'crit_mult'], 'heals': ['heal_chance', 'aoe_heal_chance'],
    'hits_taken': ['toughness', 'dodge'], 'dodges': ['dodge'], 'parries': ['parry'], 'toughs': ['toughness'],
    'scared': ['fear'], 'lucky': ['luck'],
}
STAT_CAP, FEAR_FLOOR, CRIT_MULT_CAP = 95, 5, get_dice_cutoffs()['crit_mult_cutoff']
STAT_HINTS = { # one of these now and then, for the stat she improved most (drafts: Ted, rewrite away)
    'hit': "{name}'s aim looks a little steadier.",
    'crit_chance': "{name} has a nasty new glint in her eye.",
    'crit_mult': "{name} seems to hit a little harder when it counts.",
    'luck': "{name} found a penny on the floor.  Heads up, even.",
    'expertise': "{name} is reading her enemies a little better.",
    'toughness': "{name} looks a bit sturdier.  Scarier, too.",
    'dodge': "{name} seems quicker on her feet.",
    'parry': "{name}'s blocking looks a little crisper.",
    'fear': "{name} doesn't flinch quite so much anymore.",
    'heal_chance': "{name}'s bandaging is getting less embarrassing.",
    'aoe_heal_chance': "{name}'s prayers seem to carry a little farther.",
    'max_hp': "{name} looks a little beefier.",
}
HINT_CHANCE = 0.5 # how often a heroine gets a hint after a fight

def growth_weights(heroine : object) -> dict:
    leaning = find_row(stat_growth_table, 'hero_class', heroine.hero_class)
    done = getattr(heroine, 'fight_tally', {})
    weights = {}
    for stat in GROWTH_STATS:
        value = heroine.stats[stat]
        capped = value <= FEAR_FLOOR if stat == 'fear' else value >= (CRIT_MULT_CAP if stat == 'crit_mult' else STAT_CAP)
        if capped:
            continue
        bonus = min(2.0, 0.4 * sum(count for what, count in done.items() if stat in DOING.get(what, [])))
        weights[stat] = leaning[stat] * (1 + bonus)
    return weights

def grow_stat(heroine : object, stat : str) -> float:
    """Raise one stat (lower, for fear) and return the change."""
    value = heroine.stats[stat]
    if stat == 'crit_mult':
        new = min(CRIT_MULT_CAP, round(value + random.uniform(0.02, 0.06), 2))
    elif stat == 'fear':
        gain = 1 if value <= 15 else random.randint(1, 3)
        new = max(FEAR_FLOOR, value - gain)
    else:
        gain = random.randint(1, 3)
        if value >= 85:
            gain = 1
        elif value >= 70:
            gain = max(1, gain - 1)
        new = min(STAT_CAP, value + gain)
    heroine.stats[stat] = new
    return round(new - value, 2)

def improve_heroine(heroine : object) -> dict:
    """One heroine's bonuses for one fight: {stat: change}, max_hp included."""
    changes = {}
    weights = growth_weights(heroine)
    for _ in range(random.randint(1, 4)):
        if not weights:
            break
        stat = random.choices(list(weights), list(weights.values()))[0]
        del weights[stat] # four different stats at most
        changes[stat] = grow_stat(heroine, stat)
    hp = random.randint(1, 3)
    heroine.starting_health += hp
    heroine.health = min(heroine.starting_health, heroine.health + hp)
    changes['max_hp'] = hp
    heroine.fight_tally = {}
    return changes

async def get_stat_increases(party_dict : dict) -> dict:
    lines = []
    for heroine in party_dict['party']:
        changes = improve_heroine(heroine)
        if dev_mode():
            shown = ', '.join(f"{stat} {'-' if stat == 'fear' else '+'}{abs(change)} ({heroine.stats[stat] if stat != 'max_hp' else heroine.starting_health})"
                              for stat, change in changes.items())
            lines.append(f"[dev] {heroine.name}: {shown}")
        if random.random() < HINT_CHANCE:
            biggest = max(changes, key=lambda stat: abs(changes[stat]) * (30 if stat == 'crit_mult' else 1))
            lines.append(f"[narr]{STAT_HINTS[biggest].format(name=heroine.name)}[/]")
    for line in lines:
        await say(line)
    if lines:
        await pause()
    return party_dict

def refresh_party(party_dict : dict, increment : bool) -> dict:
    """A fresh start: everyone alive at full health with her full starting kit (the Token and Big Badda Boom
    included), and a blown-up Sapper back in one piece. A wipe is a full dungeon restart, so it gets this too.
    increment=True also counts a new dungeon run (loading a saved party). The tavern wipe doesn't bump the
    counter, since the dungeon proper hasn't started yet."""
    if increment:
        party_dict['times_run_dungeon'] += 1
    party_dict['token_used'] = False
    party_dict['wiped'] = False
    for heroine in party_dict['party']:
        restore_starting_items(heroine)
        heroine.is_dead = False
        heroine.blown_up = False
        heroine.health = heroine.starting_health
    return party_dict

async def start_new_run(party_dict : dict) -> dict:
    """The start of a new dungeon run: refresh_party, and any affliction from last run (the norovirus)
    clears up. Happy hands out a fresh one after the tavern fight."""
    party_dict = refresh_party(party_dict, True)
    for heroine in party_dict['party']:
        for item_name, lines in AFFLICTIONS.items():
            if item_name in heroine.inv:
                heroine.inv.remove(item_name)
                await say(lines['cured'].format(who=heroine.name))
    return party_dict

def restore_starting_items(heroine : object):
    """Every dungeon run gives back the starting gear that was only used up (the Token, Big Badda Boom),
    not anything she dropped. Everything else she's carrying stays. Safety net: if she's left with nothing
    to fight with but the Token and a bandage, her first starting weapon comes back."""
    dropped = getattr(heroine, 'dropped', [])
    for position, item in enumerate(heroine.starting_inv):
        if item not in heroine.inv and item not in dropped:
            heroine.inv.insert(min(position, len(heroine.inv)), item)
    fighting = [x for x in heroine.inv if get_item(x)['attack_type'] not in ('hail_mary', 'trinket') and x != 'plain_bandage']
    if not fighting:
        backup = next((x for x in heroine.starting_inv if get_item(x)['attack_type'] not in ('hail_mary', 'trinket') and x != 'plain_bandage'), None)
        if backup:
            heroine.inv.append(backup)
            heroine.dropped = [x for x in dropped if x != backup]

def wipe_party(party_dict : dict) -> dict:
    party_dict['wiped'] = True
    for heroine in party_dict['party']:
        heroine.is_dead = True
        heroine.health = 0
    return party_dict

