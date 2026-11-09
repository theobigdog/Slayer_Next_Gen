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

# In the browser (pygbag), files vanish when the page closes, so every save is also kept in the browser's
# localStorage, and copied back into saved_parties when the game starts. (Untested until the first web build.)
BROWSER_SAVE_PREFIX = 'slayer_save:'

def browser_storage():
    """The browser's localStorage when running on the web, else None."""
    if sys.platform != 'emscripten':
        return None
    try:
        import platform
        return platform.window.localStorage
    except Exception as error:
        print('Slayer: no browser storage, saves only last until the page closes:', error)
        return None

def restore_browser_saves():
    storage = browser_storage()
    if storage is None:
        return
    try:
        save_dir.mkdir(exist_ok=True)
        for i in range(int(storage.length)):
            key = str(storage.key(i))
            if key.startswith(BROWSER_SAVE_PREFIX):
                (save_dir / f'{key[len(BROWSER_SAVE_PREFIX):]}.sav').write_text(str(storage.getItem(key)), encoding='ascii')
    except Exception as error:
        print('Slayer: could not read saves from the browser:', error)

restore_browser_saves()

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
    blob = scramble(json.dumps(party_to_data(party)))
    with open(save_dir / f"{name}.sav", 'w', encoding='ascii') as f:
        f.write(blob)
    storage = browser_storage()
    if storage is not None: # on the web: keep it in the browser too, so it survives closing the page
        try:
            storage.setItem(BROWSER_SAVE_PREFIX + name, blob)
        except Exception as error:
            print('Slayer: could not save to the browser:', error)
    await say(f"Your party has been saved as {name}.")
    await say(f"Keep track of this saved name if you want to recover your party: {name}")
    await pause()

def saved_party_names() -> list:
    """Every saved party's name, most recently played first."""
    if not save_dir.exists():
        return []
    saves = sorted(save_dir.glob('*.sav'), key=lambda path: path.stat().st_mtime, reverse=True)
    return [path.stem for path in saves]

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
        "\nWith her last dying breath, {victim} makes one more attempt with her {item}, completely missing {mob}, who begins to chuckle.  \"Guess I'd try the same, but, that was kinda sad....\"\n[narr]Don't let them get away with that.  Come back and take them down next time!![/]",
    ]

# Afflictions: "loot" that isn't a prize. A mob gives it to one random heroine, she's stuck with it for the
# rest of that dungeon run (and can use it as an attack), and it clears up when the next run starts.
# Its bonus column works like a trinket's: the norovirus is dodge-5 (she doesn't want to move much).
AFFLICTIONS = {
    'happys_norovirus_regurgitation': {
        'caught': "{mob} leans in close and coughs right in {who}'s face.  [narr]Aaaand {who} has caught Happy's norovirus.  She's stuck with it for the rest of this run, but hey, now she can puke on people too.[/]",
        'cured': "[narr]Good news: {who}'s norovirus finally cleared up.[/]",
    },
}

# ---------- loot, slots and the stash ---------------------------------------------
# Loot comes from items.csv: a row whose source is a mob's class is in that mob's loot table, and its
# drop_chance (%) is rolled for each one of those mobs that died. Happy hands his over after the tavern.
# Each heroine has three kinds of slots:
#   gear     GEAR_SLOTS (6): weapons, bandages, bombs... everything that isn't one of the two below
#   trinkets her class's trinket_slots (hero_stats.csv, 2-4): attack_type trinket, a bonus while carried
#   potion   POTION_SLOTS (1): a healing item with uses (her own; when it's used up, she's out)
# The Token and afflictions (the norovirus) don't take a slot. Loot is kept across runs and through wipes.
# The stash at Happy's tavern holds the party's spare gear: at the tavern a full slot can send things to the
# stash; in the dungeon there's no stash, so a full slot means dropping something, and dropped is gone for good.
# Starting gear can be stashed or dropped too; it doesn't come back next run unless it was only used up.
GEAR_SLOTS, POTION_SLOTS = 6, 1
MAX_STACK = 2 # a consumable tops up to at most twice its uses
SLOT_NAMES = {'gear': 'bag', 'trinket': 'trinkets', 'potion': 'potion'}

def slot_kind(item : dict) -> str:
    """'none' (the Token, afflictions), 'trinket', 'potion' or 'gear'."""
    if item['item'] == 'token_of_the_wise_witch' or item['item'] in AFFLICTIONS:
        return 'none'
    if item['attack_type'] == 'trinket':
        return 'trinket'
    if item['attack_type'] in ('heal', 'aoe_heal') and item['uses']:
        return 'potion'
    return 'gear'

def slots(heroine : object, kind : str) -> int:
    if kind == 'trinket':
        return find_row(hero_stats_table, 'hero_class', heroine.hero_class)['trinket_slots']
    return POTION_SLOTS if kind == 'potion' else GEAR_SLOTS

def carried(heroine : object, kind : str) -> list:
    """Her items of one slot kind, counting starting gear that's only gone for this run (a used Big Badda
    Boom comes back next run, so it keeps its slot)."""
    dropped = getattr(heroine, 'dropped', [])
    pending = [item for item in heroine.starting_inv if item not in heroine.inv and item not in dropped]
    return [item for item in heroine.inv + pending if slot_kind(get_item(item)) == kind]

def slot_label(heroine : object, kind : str, item : dict = None) -> str:
    """The right-hand side of her row in the 'Who gets it?' menu. For a potion it says what she's holding (and
    what this one would do to it), so a swap is never a surprise."""
    if kind == 'potion':
        hers = [x for x in carried(heroine, 'potion') if x in heroine.inv]
        if not hers:
            return 'no potion'
        mine = get_item(hers[0])
        left = uses_left(heroine, hers[0])
        if item and item['item'] == hers[0]:
            if stack_full(heroine, item):
                return f"has {left}, full"
            return f"has {left}, stacks to {min(item['uses'] * MAX_STACK, left + item['uses'])}"
        return f"swap out {mine['item_desc']} ({left})"
    return f"{SLOT_NAMES[kind]} {len(carried(heroine, kind))}/{slots(heroine, kind)}"

# How a stat bonus reads to players, without numbers: (going up, going down). A small bonus (1-3) gets
# "a bit", a big one (7+) gets "much". The hint column in items.csv replaces these with Ted's own words.
BONUS_WORDS = {
    'luck': ('luckier', 'unluckier'), 'dodge': ('harder to hit', 'easier to hit'), 'toughness': ('tougher', 'softer'),
    'parry': ('better at blocking', 'worse at blocking'), 'hit': ('better aim', 'shakier aim'),
    'expertise': ('reads enemies better', 'reads enemies worse'), 'crit_chance': ('more crits', 'fewer crits'),
    'crit_mult': ('harder crits', 'softer crits'), 'fear': ('jumpier', 'braver'),
    'heal_chance': ('better at healing', 'worse at healing'), 'aoe_heal_chance': ('better group heals', 'worse group heals'),
}

def bonus_hint(item : dict) -> str:
    """'luck+5 dodge-2' -> 'luckier, a bit easier to hit'. The item's hint column wins if it has one."""
    if item.get('hint'):
        return item['hint']
    words = []
    for stat, sign, amount in parse_bonus(item['bonus']):
        up, down = BONUS_WORDS.get(stat, (f'more {stat}', f'less {stat}'))
        size = 'a bit ' if amount <= 3 else 'much ' if amount >= 7 else ''
        words.append(size + (up if sign == '+' else down))
    return ', '.join(words)

def describe_item(item : dict, left : int = None) -> str:
    """A menu label: 'Bastard Sword (7 - 11 damage)', 'Lucky Rabbit's Foot (trinket: luckier)',
    'Fire Bomb (15 - 25 damage, 2 uses)'. Stat bonuses show as a hint, not numbers (the stats themselves stay
    behind the scenes); dev mode adds the numbers."""
    desc, low, high = item['item_desc'], item['damage_low'], item['damage_high']
    hint = bonus_hint(item)
    if dev_mode() and item['bonus']:
        hint += f" [{', '.join(f'{sign}{amount} {stat}' for stat, sign, amount in parse_bonus(item['bonus']))}]"
    if item['attack_type'] == 'hail_mary':
        return f'{desc} (hail mary)'
    if item['attack_type'] == 'trinket':
        return f"{desc} (trinket{': ' + hint if hint else ''})"
    what = f'{low} - {high} damage' if low >= 0 else f'{-high} - {-low} healing'
    if item['attack_type'] == 'aoe':
        what += ', hits them all'
    elif item['attack_type'] == 'aoe_heal':
        what += ', heals everyone'
    if item['uses']:
        what += f", {item['uses']} uses" if left is None else f", {left} left"
    if hint:
        what += f', {hint}'
    return f'{desc} ({what})'

def parse_bonus(bonus) -> list:
    """'luck+5 dodge-2' -> [('luck', '+', 5), ('dodge', '-', 2)]"""
    return [(stat, sign, int(amount)) for stat, sign, amount in re.findall(r'(\w+)([+-])(\d+)', bonus or '')]

def stat_bonus(heroine : object, stat : str) -> int:
    """What her items add to (or take off) one stat right now: trinkets, and afflictions like the norovirus."""
    total = 0
    for item_name in heroine.inv:
        for name, sign, amount in parse_bonus(get_item(item_name)['bonus']):
            if name == stat:
                total += amount if sign == '+' else -amount
    return total

def uses_left(heroine : object, item_name : str):
    return getattr(heroine, 'uses', {}).get(item_name)

def add_item(heroine : object, item : dict, uses : int = None) -> str:
    """Put an item in her slots (room already checked). uses: what's left on one coming out of the stash.
    Returns the narration line."""
    heroine.uses = getattr(heroine, 'uses', {})
    uses = item['uses'] if uses is None else uses
    if item['uses'] and item['item'] in heroine.inv:
        before = heroine.uses.get(item['item'], 0)
        heroine.uses[item['item']] = min(item['uses'] * MAX_STACK, before + uses)
        return f"[narr]{heroine.name} stacks it with the {item['item_desc']} she already had: {before} uses, now {heroine.uses[item['item']]}.[/]"
    heroine.inv.append(item['item'])
    if item['uses']:
        heroine.uses[item['item']] = uses
    if item['item'] in getattr(heroine, 'dropped', []):
        heroine.dropped.remove(item['item']) # her own starting gear, back from the stash
    return f"[narr]{heroine.name} takes {item['item_desc']}.[/]"

def remove_item(heroine : object, item_name : str):
    """Out of her slots (dropped, or off to the stash). Starting gear stays gone next run."""
    if item_name in heroine.inv:
        heroine.inv.remove(item_name)
    if item_name in heroine.starting_inv:
        heroine.dropped = getattr(heroine, 'dropped', []) + [item_name]
    return getattr(heroine, 'uses', {}).pop(item_name, None)

def drop_item(heroine : object, item_name : str):
    remove_item(heroine, item_name)

STASH_SIZES = {1: 10, 2: 18, 3: 24, 4: 28, 5: 34, 6: 38, 7: 44, 8: 50} # Ted's table: stash capacity by party size

def stash_capacity(party_dict : dict) -> int:
    return STASH_SIZES.get(len(party_dict['party']), max(STASH_SIZES.values()))

def capacity_facts(party_dict : dict) -> dict:
    """The carrying limits, read live from the real rules, for Happy's speech in Slayer_Narration.happy_loot (Ted,
    Nov 8: 'there should be some kind of link to the proper value, so Happy is always accurate'). Trinket room
    depends on class, so 'trinkets' names only the classes in this party: 'Warriors can carry 2, Clerics 3'."""
    by_class = {}
    for heroine in party_dict['party']:
        by_class.setdefault(heroine.hero_class, slots(heroine, 'trinket'))
    plural = lambda cls: class_label(cls) + ('es' if cls.endswith(('ch', 'sh', 's')) else 's')
    and_list = lambda words: words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' and ' + words[-1]
    groups = {} # classes with the same room go together: 'Clerics, Hunters and Shifters 3'
    for cls, n in by_class.items():
        groups.setdefault(n, []).append(plural(cls))
    if len(party_dict['party']) == 1:
        trinkets = f"you can carry {next(iter(by_class.values()))}"
    else:
        parts = [f"{and_list(sorted(names))} {'can carry ' if spot == 0 else ''}{n}" for spot, (n, names) in enumerate(sorted(groups.items()))]
        trinkets = parts[0] if len(parts) == 1 else ', '.join(parts[:-1]) + ', and ' + parts[-1]
    return {'gear': GEAR_SLOTS, 'potions': POTION_SLOTS, 'stack': {2: 'twice', 3: 'three times'}.get(MAX_STACK, f'{MAX_STACK} times'),
            'trinkets': trinkets, 'stash': stash_capacity(party_dict)}

def stash_has_room(party_dict : dict) -> bool:
    return len(party_dict.setdefault('stash', [])) < stash_capacity(party_dict)

def stash_label(party_dict : dict) -> str:
    return f"{len(party_dict.setdefault('stash', []))}/{stash_capacity(party_dict)}"

def stash_item(party_dict : dict, heroine : object, item_name : str):
    uses = remove_item(heroine, item_name)
    party_dict.setdefault('stash', []).append({'item': item_name, 'uses': uses})

def stash_new(party_dict : dict, item : dict):
    party_dict.setdefault('stash', []).append({'item': item['item'], 'uses': item['uses']})

def use_up(heroine : object, item_name : str):
    """She just used a consumable: one less use, and it's gone at zero."""
    left = uses_left(heroine, item_name)
    if left is None:
        return
    heroine.uses[item_name] = left - 1
    if left - 1 <= 0:
        heroine.inv.remove(item_name)
        del heroine.uses[item_name]

def can_use(heroine : object, item : dict) -> bool:
    from ast import literal_eval
    return heroine.hero_class in literal_eval(item['classes'])

def stack_full(heroine : object, item : dict) -> bool:
    """She already carries this consumable at its stacking limit (MAX_STACK times its uses)."""
    return bool(item['uses']) and item['item'] in heroine.inv and (uses_left(heroine, item['item']) or 0) >= item['uses'] * MAX_STACK

def has_room(heroine : object, item : dict) -> bool:
    kind = slot_kind(item)
    if item['uses'] and item['item'] in heroine.inv:
        return not stack_full(heroine, item) # tops up what she has
    return kind == 'none' or len(carried(heroine, kind)) < slots(heroine, kind)

async def make_room(heroine : object, item : dict, party_dict : dict, at_tavern : bool, new_can_stash : bool = True):
    """Her slot for this item is full: swap something out. At the tavern her old one goes to the stash (if it
    has room); otherwise it's dropped for good. Returns 'done', 'stashed' (the new item went to the stash
    instead) or 'back' (pick someone else)."""
    from Slayer_UI import choose
    kind = slot_kind(item)
    hers = [x for x in heroine.inv if slot_kind(get_item(x)) == kind]
    to_stash = at_tavern and stash_has_room(party_dict)
    verb = 'Stash' if to_stash else 'Drop'
    labels = ([f"{verb} her {describe_item(get_item(x), uses_left(heroine, x))}, take {item['item_desc']}" for x in hers] if kind == 'potion'
              else [f"{verb}: {describe_item(get_item(x), uses_left(heroine, x))}" for x in hers])
    extra = [f"Put {item['item_desc']} in the stash instead"] if to_stash and new_can_stash else []
    full = '' if to_stash or not at_tavern else f"  (The stash is full too: {stash_label(party_dict)}.)"
    prompt = (f"{heroine.name}'s {SLOT_NAMES[kind]} is full.  Swap something out for {item['item_desc']}?{full}  " if kind != 'potion'
              else f"{heroine.name} can only carry one potion, and she already has {get_item(hers[0])['item_desc']} ({uses_left(heroine, hers[0])} left).  {'Stash' if to_stash else 'Toss'} it for {item['item_desc']}?{full}  ")
    out = await choose(prompt, labels + extra + ['Never mind, pick someone else'], "One of THOSE numbers, please:  ")
    if out < len(hers):
        old = get_item(hers[out])
        if to_stash:
            stash_item(party_dict, heroine, hers[out])
            await say(f"[narr]Into the stash: {old['item_desc']}.[/]")
        else:
            drop_item(heroine, hers[out])
            await say(f"[narr]{heroine.name} tosses her {old['item_desc']}.  Gone for good.[/]")
        return 'done'
    if extra and out == len(hers):
        return 'stashed'
    return 'back'

async def give_loot(item : dict, source : str, party_dict : dict, at_tavern : bool = False):
    """One piece of loot: the player picks who gets it (or stashes it at the tavern, or leaves it)."""
    from Slayer_UI import choose
    party = party_dict['party']
    able = [heroine for heroine in party if can_use(heroine, item)]
    kind = slot_kind(item)
    label = describe_item(item)
    if not able:
        if at_tavern and stash_has_room(party_dict):
            stash_new(party_dict, item)
            await say(f"From {source}: {label}.  [narr]Nobody here can use it, so it goes in the stash for later.[/]")
        else:
            await say(f"From {source}: {label}.  [narr]Nobody here can use it, so it stays on the floor.[/]")
        return
    await say(f"From {source}: {label}.")
    while True:
        names = [f"{x.name}  ({class_label(x.hero_class)})\t{slot_label(x, kind, item)}" for x in able]
        extra = [f"Put it in the stash\tstash {stash_label(party_dict)}"] if at_tavern and stash_has_room(party_dict) else []
        pick = await choose(f"Who gets {item['item_desc']}?  ", names + extra + ['Leave it behind'], "One of THOSE numbers, please:  ")
        if pick >= len(able):
            if extra and pick == len(able):
                stash_new(party_dict, item)
                await say(f"[narr]{item['item_desc']} goes in the stash.[/]")
            else:
                await say(f"[narr]Fine.  {item['item_desc']} stays on the floor.  Somebody's gonna trip on that.[/]")
            return
        who = able[pick]
        if stack_full(who, item):
            await say(f"[narr]{who.name} can't carry any more {item['item_desc']} than she's got.  Pick someone else.[/]")
            continue
        if not has_room(who, item):
            result = await make_room(who, item, party_dict, at_tavern)
            if result == 'back':
                continue
            if result == 'stashed':
                stash_new(party_dict, item)
                await say(f"[narr]{item['item_desc']} goes in the stash.[/]")
                return
        await say(add_item(who, item))
        return

async def get_loot(mob : object, party_dict : dict, others : list = (), at_tavern : bool = False) -> dict:
    """After a fight: mob (here, Happy) hands over his loot, and every one of the others that died drops
    theirs, each piece rolled against its drop_chance. An affliction (the norovirus) goes to one random
    heroine for the rest of the run instead. at_tavern: the stash is right there."""
    party = party_dict['party']
    found = []
    for source in [mob] + [m for m in others if m is not mob and m.is_dead]:
        for item in [row for row in items_table if row['source'] == source.mob_class]:
            if item['item'] in AFFLICTIONS:
                able = [heroine for heroine in party if can_use(heroine, item)]
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
        import Slayer_Narration as nar # imported here, because Slayer_Narration imports this file
        await nar.loot_found(party_dict)
    for item, source in found:
        await give_loot(item, source, party_dict, at_tavern)
    await pause()
    return party_dict

def who_can_use(item : dict) -> str:
    from ast import literal_eval
    classes = literal_eval(item['classes'])
    return 'anyone' if all(c in classes for c in get_hero_classes()) else ', '.join(class_label(c) for c in classes)

async def visit_stash(party_dict : dict) -> dict:
    """Happy's back room, before the dungeon: gear up a heroine from the stash (only what she can use is
    shown), put things in, or look through the whole thing."""
    from Slayer_UI import choose
    party = party_dict['party']
    party_dict.setdefault('stash', [])
    while True:
        stash = party_dict['stash']
        what = await choose(f"The stash: {stash_label(party_dict)}.  What'll it be?  ",
                            ['Gear up a heroine', 'Put something in the stash', 'Look through the whole stash', "Done, let's go"],
                            "One of THOSE numbers, please:  ")
        if what == 3:
            return party_dict
        if what == 2:
            if not stash:
                await say("[narr]It's empty.  Just dust and a sad sock.[/]")
            for entry in stash:
                item = get_item(entry['item'])
                await say(f"  {describe_item(item, entry['uses'])}:  {who_can_use(item)}")
            continue
        names = [f"{x.name}  ({class_label(x.hero_class)})" for x in party]
        who_pick = await choose("Gear up who?  " if what == 0 else "Whose gear goes in?  ", names + ['Never mind'], "One of THOSE numbers, please:  ")
        if who_pick == len(party):
            continue
        who = party[who_pick]
        if what == 0:
            hers = [entry for entry in stash if can_use(who, get_item(entry['item']))]
            if not hers:
                await say(f"[narr]Nothing in there {who.name} can use.[/]")
                continue
            labels = [f"{describe_item(get_item(e['item']), e['uses'])}\t{slot_label(who, slot_kind(get_item(e['item'])))}" for e in hers]
            pick = await choose(f"What does {who.name} take?  ", labels + ['Never mind'], "One of THOSE numbers, please:  ")
            if pick == len(hers):
                continue
            entry = hers[pick]
            item = get_item(entry['item'])
            stash.remove(entry) # out of the stash first, so a swap can put her old one in its place
            if not has_room(who, item):
                result = await make_room(who, item, party_dict, True, new_can_stash=False)
                if result != 'done':
                    stash.append(entry) # changed her mind: it goes back
                    continue
            await say(add_item(who, item, entry['uses']))
        else:
            if not stash_has_room(party_dict):
                await say(f"[narr]The stash is stuffed ({stash_label(party_dict)}).  Take something out first.[/]")
                continue
            hers = [x for x in who.inv if slot_kind(get_item(x)) != 'none']
            if not hers:
                await say(f"[narr]{who.name} has nothing to put in.[/]")
                continue
            labels = [describe_item(get_item(x), uses_left(who, x)) for x in hers]
            pick = await choose(f"Which of {who.name}'s things?  ", labels + ['Never mind'], "One of THOSE numbers, please:  ")
            if pick == len(hers):
                continue
            stash_item(party_dict, who, hers[pick])
            await say(f"[narr]Into the stash: {get_item(hers[pick])['item_desc']}.[/]")

# ---------- stat bonuses after a fight ------------------------------------------
# Every heroine (dead, alive or blown to bits) improves 1-4 stats by 1-3 points each, plus some max HP
# (hp_low to hp_high in stat_growth.csv: Warrior 2-4 ... Witch and Sapper 1-2).
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
# The hint lines themselves (STAT_HINTS) are Ted's, in Slayer_Narration.py.
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
    growth = find_row(stat_growth_table, 'hero_class', heroine.hero_class)
    hp = random.randint(int(growth['hp_low']), int(growth['hp_high'])) # by class: Warriors beef up faster than Witches
    heroine.starting_health += hp
    heroine.health = min(heroine.starting_health, heroine.health + hp)
    changes['max_hp'] = hp
    heroine.fight_tally = {}
    return changes

async def get_stat_increases(party_dict : dict) -> dict:
    import Slayer_Narration as nar # imported here, because Slayer_Narration imports this file
    lines = []
    for heroine in party_dict['party']:
        changes = improve_heroine(heroine)
        if dev_mode():
            shown = ', '.join(f"{stat} {'-' if stat == 'fear' else '+'}{abs(change)} ({heroine.stats[stat] if stat != 'max_hp' else heroine.starting_health})"
                              for stat, change in changes.items())
            lines.append(f"[dev] {heroine.name}: {shown}")
        if random.random() < HINT_CHANCE:
            biggest = max(changes, key=lambda stat: abs(changes[stat]) * (30 if stat == 'crit_mult' else 1))
            lines.append(f"[narr]{nar.STAT_HINTS[biggest].format(name=heroine.name)}[/]")
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
    cured = False
    for heroine in party_dict['party']:
        for item_name, lines in AFFLICTIONS.items():
            if item_name in heroine.inv:
                heroine.inv.remove(item_name)
                await say(lines['cured'].format(who=heroine.name))
                cured = True
    if cured:
        await pause() # read it before the party screen replaces it (Ted, Nov 8: it flashed past)
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
    """Everyone dies at once (killing enraged Happy). Who was still standing, and with how much HP, is kept in
    standing_at_wipe (spot in the party, HP) so Ted's happy_wipe scene can have them watch him get back up."""
    party_dict['wiped'] = True
    party_dict['standing_at_wipe'] = [[spot, heroine.health] for spot, heroine in enumerate(party_dict['party']) if not heroine.is_dead]
    for heroine in party_dict['party']:
        heroine.is_dead = True
        heroine.health = 0
    return party_dict

