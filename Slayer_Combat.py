import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import joblib as jb
import random
from colorama import Fore, Back, Style, Cursor
import time

def display_mob_summary(mob: dict):
    print()
    print(f"Name: {mob.name}")
    print(f"Class: {mob.mob_class}")
    low_health = mob.health <= (mob.starting_health * 0.1)
    half_health = mob.health <= (mob.starting_health * 0.5)
    if low_health:
        print(f"Current Health: {Fore.RED}{int(round(mob.health, 0))}{Style.RESET_ALL}/{mob.starting_health}")
    elif half_health:
        print(f"Current Health: {Fore.MAGENTA}{int(round(mob.health, 0))}{Style.RESET_ALL}/{mob.starting_health}")
    else:
        print(f"Current Health: {mob.health}/{mob.starting_health}")

def display_party_summary(party : list):
    print()
    for heroine in party:
        low_health = heroine.health <= (heroine.starting_health * 0.1)
        half_health = heroine.health <= (heroine.starting_health * 0.5)
        if low_health:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {Fore.RED}{int(round(heroine.health, 0))}{Style.RESET_ALL}/{heroine.starting_health}")
        elif half_health:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {Fore.MAGENTA}{int(round(heroine.health, 0))}{Style.RESET_ALL}/{heroine.starting_health}")
        else:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {int(round(heroine.health, 0))}/{heroine.starting_health}")

def show_current_status(party: dict, mobs: list):
    wt()
    print('Enemy')
    for i in range(len(mobs)):
        display_mob_summary(mobs[i])
        print()
    print()
    print('Party')
    display_party_summary(party)

def get_heroine_rolls(heroine: object) -> dict:  ### In this function, "cutoffs" indicate max value for dice roll, ""
    roll_results = {}
    heroine_stats = heroine.stats
    heroine_dice_cutoffs = acc.get_dice_cutoffs()
    crit = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['crit_cutoff'])
    miss = acc.multi_roll(heroine_stats['low_miss'], heroine_stats['high_miss'])
    luck = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['luck_cutoff'])
    expertise = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['expertise_cutoff'])
    toughness = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['toughness_cutoff'])
    dodge = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['dodge_cutoff'])
    parry = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['parry_cutoff'])
    fear = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['fear_cutoff'])
    heal = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['heal_cutoff'])
    aoe_heal = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['aoe_heal_cutoff'])
    if crit > heroine_stats['crit']:
        roll_results['crit_mult'] = heroine_stats['crit_mult'] # crit roll is higher than cutoff, so the crit_mult is returned
    else:
        roll_results['crit_mult'] = 1 # if not a crit, multiplier is 1
    roll_results['miss'] = miss < heroine_dice_cutoffs['miss_threshold']
    roll_results['luck'] = luck > heroine_stats['luck']
    roll_results['expertise'] = expertise > heroine_stats['expertise']
    roll_results['toughness'] = toughness > heroine_stats['toughness']
    roll_results['dodge'] = dodge > heroine_stats['dodge']
    roll_results['parry'] = parry > heroine_stats['parry']
    roll_results['fear'] = fear > heroine_stats['fear']
    roll_results['heal'] = heal > heroine_stats['heal']
    roll_results['aoe_heal'] = aoe_heal > heroine_stats['aoe_heal']
    return roll_results

def get_mob_rolls(mob: object) -> dict:
    roll_results = {}
    mob_stats = mob.stats
    enraged = mob.enraged
    mob_dice_cutoffs = acc.get_dice_cutoffs_mobs()
    crit = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['crit_cutoff'])
    miss = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['miss_cutoff'])
    luck = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['luck_cutoff'])
    expertise = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['expertise_cutoff'])
    toughness = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['toughness_cutoff'])
    dodge = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['dodge_cutoff'])
    heal = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['healing_chance_cutoff'])
    scare = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['scare_cutoff'])
    if enraged:
        if crit > mob_stats['enraged_crit_chance']:
            roll_results['crit_mult'] = mob_stats['enraged_crit']
        else:
            roll_results['crit_mult'] = 1
        roll_results['miss'] = miss < mob_stats['enraged_miss']
        roll_results['luck'] = luck > mob_stats['enraged_luck']
        roll_results['expertise'] = expertise > mob_stats['enraged_expertise']
        roll_results['toughness'] = toughness > mob_stats['enraged_toughness']
        roll_results['dodge'] = dodge > mob_stats['enraged_dodge']
        roll_results['heal'] = heal > mob_stats['enraged_healing_chance']
        roll_results['scare'] = scare > mob_stats['enraged_scare']
    else:
        if crit > mob_stats['crit_chance']:
            roll_results['crit_mult'] = mob_stats['crit']
        else:
            roll_results['crit_mult'] = 1
        roll_results['miss'] = miss < mob_stats['miss']
        roll_results['luck'] = luck > mob_stats['luck']
        roll_results['expertise'] = expertise > mob_stats['expertise']
        roll_results['toughness'] = toughness > mob_stats['toughness']
        roll_results['dodge'] = dodge > mob_stats['dodge']
        roll_results['heal'] = heal > mob_stats['healing_chance']
        roll_results['scare'] = scare > mob_stats['scare']
    return roll_results

def update_health(initial_health : int, max_health : int, delta : int) -> int:
    new_health = initial_health - delta
    if new_health > max_health:
        return max_health
    elif new_health > 0:
        return new_health
    else:
        return 0

def display_inventory(inv):
    items = acc.get_items()
    inv_item_ct = len(inv)
    for i in range(inv_item_ct):
        item = inv[i]
        data = items[items['item'] == item].iloc[0]
        desc = data['item_desc']
        low = data['damage_range_low']
        high = data['damage_range_high']
        if low >= 0:
            print(f'{i + 1}:  {desc} ({low} - {high} damage)')
        else:
            print(f'{i + 1}:  {desc} ({-1 * high} - {-1 * low} healing)')


def take_turn(heroine : object, party : list, mobs : list) -> set:
    print(f'{heroine.heroine_name}\n')
    inv = heroine.inv
    inv_len = len(inv)
    choices = [str(x) for x in list(range(1,inv_len + 1))]
    choice = None
    ok = False
    print(choices)
    while not ok:
        display_inventory(inv)
        choice = input("Pick the number for whatever item you feel like using. Not that it's going to matter...  ")
        if choice in choices:
            ok = True
        else:
            print(f'\nNo, numb-nuts, choose one of the numbers!\n')
    choice = int(choice)
    print(inv[choice-1])
    return (party, mobs)

def mob_turn():
    None

"""
    'crit_cutoff' : 20,
        'crit_mult_cutoff' : 100,
        'miss_cutoff' : 30,
        'luck_cutoff' : 20,
        'expertise_cutoff' : 20,
        'toughness_cutoff' : 20,
        'dodge_cutoff' : 15,
        'healing_chance_cutoff' : 20,
    'scare' : 20
    """
