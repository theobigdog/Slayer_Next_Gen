"""Checks the CSV files in supporting_docs for mistakes, in plain English, before the game trips over them.

Run it from the game folder after editing a CSV:
    python check_data.py

It doesn't change anything. "Row 12" means row 12 in Excel (row 1 is the header).
"""
import ast
import csv
import re
import sys
from pathlib import Path

DOCS = Path(__file__).parent / 'supporting_docs'
ATTACK_TYPES = {'melee', 'range', 'both', 'aoe', 'heal', 'aoe_heal', 'trinket', 'hail_mary'}
MOB_ATTACK_TYPES = {'melee', 'range', 'both', 'aoe'}
MOB_EFFECTS = {'gas', 'junk', 'hiss', 'blink', 'poison'}  # special mob attacks (Slayer_Combat.MOB_EFFECTS)
AI_LEVELS = {'easy', 'medium', 'normal', 'hard'}
problems = []


def problem(file, row, text):
    problems.append(f"{file}, row {row}: {text}")


def read(file):
    path = DOCS / file
    if not path.exists():
        problems.append(f"{file}: the file is missing from supporting_docs.")
        return [], []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        header = reader.fieldnames or []
    for number, row in enumerate(rows, start=2):
        if None in row:
            problem(file, number, "has more cells than the header has columns (an extra comma, or a list without quotes around it?). Fix that first; the rest of this row isn't checked.")
        elif any(value is None for value in row.values()):
            problem(file, number, "has fewer cells than the header has columns. Fix that first; the rest of this row isn't checked.")
    good = [row if None not in row and all(v is not None for v in row.values()) else None for row in rows]
    return header, good


def number(file, row, column, value, kind=int, low=None, high=None, blank_ok=False):
    if value in (None, ''):
        if not blank_ok:
            problem(file, row, f"'{column}' is empty.")
        return None
    try:
        result = kind(value)
    except ValueError:
        problem(file, row, f"'{column}' should be a number, but it says '{value}'.")
        return None
    if (low is not None and result < low) or (high is not None and result > high):
        problem(file, row, f"'{column}' is {value}; it should be between {low} and {high}.")
    return result


def true_false(file, row, column, value):
    if value not in ('TRUE', 'FALSE'):
        problem(file, row, f"'{column}' should be TRUE or FALSE, but it says '{value}'.")


# ---------- hero_stats.csv ----------
hero_header, heroes = read('hero_stats.csv')
classes = [row['hero_class'] for row in heroes if row]
stat_names = [c for c in hero_header if c not in ('hero_class', 'low_st_health', 'high_st_health', 'trinket_slots')]
for i, row in enumerate(heroes, start=2):
    if row is None:
        continue
    for column in hero_header:
        if column == 'hero_class':
            continue
        if column == 'crit_mult':
            number('hero_stats.csv', i, column, row[column], float, 1, 2.5)
        elif column == 'trinket_slots':
            number('hero_stats.csv', i, column, row[column], int, 0, 10)
        elif column in ('low_st_health', 'high_st_health'):
            number('hero_stats.csv', i, column, row[column], int, 1, 500)
        else:
            number('hero_stats.csv', i, column, row[column], int, 0, 100)
    low, high = row.get('low_st_health'), row.get('high_st_health')
    if low and high and low.isdigit() and high.isdigit() and int(low) > int(high):
        problem('hero_stats.csv', i, "low_st_health is bigger than high_st_health.")

# ---------- mobs.csv ----------
_, mobs = read('mobs.csv')
mob_classes = [row['mob_class'] for row in mobs if row]
for i, row in enumerate(mobs, start=2):
    if row is None:
        continue
    for column in ('ai', 'enraged_ai'):
        if row.get(column, '').lower() not in AI_LEVELS:
            problem('mobs.csv', i, f"'{column}' is '{row.get(column)}'; it should be one of {', '.join(sorted(AI_LEVELS))}.")

# ---------- mob_equipment.csv ----------
_, gear = read('mob_equipment.csv')
for i, row in enumerate(gear, start=2):
    if row is None:
        continue
    if row['mob_class'] not in mob_classes:
        problem('mob_equipment.csv', i, f"mob_class '{row['mob_class']}' isn't in mobs.csv.")
    if row['attack_type'] not in MOB_ATTACK_TYPES:
        problem('mob_equipment.csv', i, f"attack_type '{row['attack_type']}' should be one of {', '.join(sorted(MOB_ATTACK_TYPES))}.")
    true_false('mob_equipment.csv', i, 'special', row['special'])
    low = number('mob_equipment.csv', i, 'damage_low', row['damage_low'])
    high = number('mob_equipment.csv', i, 'damage_high', row['damage_high'])
    if low is not None and high is not None and low > high:
        problem('mob_equipment.csv', i, "damage_low is bigger than damage_high.")
    if row.get('effect') and row['effect'] not in MOB_EFFECTS:
        problem('mob_equipment.csv', i, f"effect '{row['effect']}' isn't one the game knows ({', '.join(sorted(MOB_EFFECTS))}), or leave it empty.")
    if 'weight' in row:
        number('mob_equipment.csv', i, 'weight', row['weight'], float, 0, 100, blank_ok=True)

# ---------- items.csv ----------
_, items = read('items.csv')
seen = {}
for i, row in enumerate(items, start=2):
    if row is None:
        continue
    key = row['item']
    if not re.fullmatch(r'[a-z0-9_]+', key or ''):
        problem('items.csv', i, f"the item key '{key}' should be lowercase letters, numbers and underscores only (like fire_bomb).")
    if key in seen:
        problem('items.csv', i, f"the item key '{key}' is already used on row {seen[key]}.")
    seen[key] = i
    try:
        who = ast.literal_eval(row['classes'])
        if not isinstance(who, list):
            raise ValueError
        for name in who:
            if name not in classes and name not in mob_classes:
                problem('items.csv', i, f"the class '{name}' isn't a heroine class ({', '.join(classes)}).")
    except (ValueError, SyntaxError):
        problem('items.csv', i, f"'classes' should look like ['Warrior', 'Hunter'], but it says {row['classes']}.")
    kind = row['attack_type']
    if kind not in ATTACK_TYPES:
        problem('items.csv', i, f"attack_type '{kind}' should be one of {', '.join(sorted(ATTACK_TYPES))}.")
    true_false('items.csv', i, 'special', row['special'])
    low = number('items.csv', i, 'damage_low', row['damage_low'])
    high = number('items.csv', i, 'damage_high', row['damage_high'])
    if low is not None and high is not None:
        if low > high:
            problem('items.csv', i, "damage_low is bigger than damage_high (for heals, both are negative: -8 then -3).")
        if kind == 'heal' and high > 0:
            problem('items.csv', i, "a heal needs negative numbers (heals 3 to 8 is written -8, -3).")
        if kind in ('melee', 'range', 'both', 'aoe') and low < 0:
            problem('items.csv', i, "an attack has a negative damage number (only heals are negative).")
    source = row['source']
    if source not in ('starting', 'mob') and source not in mob_classes:
        problem('items.csv', i, f"source '{source}' should be starting, or a mob class from mobs.csv ({', '.join(mob_classes)}).")
    if 'drop_chance' in row:
        number('items.csv', i, 'drop_chance', row['drop_chance'], int, 0, 100, blank_ok=True)
        if source in mob_classes and not row['drop_chance']:
            problem('items.csv', i, "is loot (its source is a mob) but has no drop_chance, so it always drops. Fine if that's on purpose.")
    if 'uses' in row:
        number('items.csv', i, 'uses', row['uses'], int, 1, 99, blank_ok=True)
    if 'bonus' in row and row['bonus']:
        parts = row['bonus'].split()
        for part in parts:
            match = re.fullmatch(r'(\w+)([+-])(\d+)', part)
            if not match:
                problem('items.csv', i, f"bonus '{part}' should look like luck+5 or dodge-2 (no spaces inside).")
            elif match.group(1) not in stat_names:
                problem('items.csv', i, f"bonus stat '{match.group(1)}' isn't a stat ({', '.join(stat_names)}).")
    if kind == 'trinket' and not row.get('bonus'):
        problem('items.csv', i, "is a trinket with no bonus, so it does nothing.")

# ---------- stat_growth.csv ----------
growth_header, growth = read('stat_growth.csv')
for i, row in enumerate(growth, start=2):
    if row is None:
        continue
    if row['hero_class'] not in classes:
        problem('stat_growth.csv', i, f"'{row['hero_class']}' isn't a heroine class in hero_stats.csv.")
    for column in growth_header[1:]:
        number('stat_growth.csv', i, column, row[column], float, 0, 10)
missing = [c for c in classes if c not in [row['hero_class'] for row in growth if row]]
if missing:
    problems.append(f"stat_growth.csv: no row for {', '.join(missing)}.")

if problems:
    print(f"Found {len(problems)} thing{'s' if len(problems) != 1 else ''} to fix:\n")
    for line in problems:
        print('  - ' + line)
    sys.exit(1)
print("All good!  The CSVs look fine.")
