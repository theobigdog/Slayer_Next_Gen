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
        print(f"Current Health: {int(round(mob.health, 0))}/{mob.starting_health}")

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

def show_current_status(party: list, mobs: list):
    wt()
    print('Enemy')
    for i in range(len(mobs)):
        display_mob_summary(mobs[i])
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

def update_health(to_update : object, delta : int) -> object:
    new_health = to_update.health - delta
    if new_health > to_update.starting_health:
        to_update.health = to_update.starting_health
    elif new_health > 0:
        to_update.health = new_health
    else:
        to_update.health = 0
        to_update.is_dead = True
    return to_update

def check_tough(tough : bool, name : str) -> None:
    if tough:
        print(f"{name}, being the tough muthafucka they are, was able to absorb half of the damage.  Wow, getting exciting now....   I'm so bored....")

def display_inventory(inv : list) -> None:
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

def get_target_choice(mobs : list, party : list) -> object:
    counter = 1
    mobs_len = len(mobs)
    targets = {}
    if mobs_len > 0:
        print()
        print('Mobs:')
        for i in range(mobs_len):
            if not mobs[i].is_dead:
                print(f'{counter}: {mobs[i].name}')
                targets[counter] = mobs[i]
                counter += 1
    party_len = len(party)
    if party_len > 0:
        print()
        print('Party Members:')
        for i in range(party_len):
            if not party[i].is_dead:
                print(f'{counter}: {party[i].heroine_name}')
                targets[counter] = party[i]
                counter += 1
    
    target_choices = [str(x) for x in list(range(1,counter))]
    target_choice = None
    ok = False
    while not ok:
        target_choice = input("Pick the number for your target.  And, uh, good luck?  ")
        if target_choice in target_choices:
            ok = True
        else:
            print(f'\nJesus Christ, no, pick one of those numbers.  The one corresponding to who you want to fuck up, or whatever:  ')
    target = targets[int(target_choice)]
    return target

def get_heroine_turn_outcome(heroine, item,  mob_choice, party, mobs, heroine_rolls, mob_rolls) -> tuple:
    base_damage = acc.multi_roll(item['damage_range_low'], item['damage_range_high'])
    attack_type = item['attack_type']
    crit_mult = heroine_rolls['crit_mult']
    is_crit = crit_mult > 1
    damage_w_crit_mult = base_damage * crit_mult
    damage = None
    if len(mob_rolls.keys()) > 0:  # check to see if it is an attack or not
        tough = mob_rolls['toughness']
        if tough:
            damage = damage_w_crit_mult / 2
        else:
            damage = damage_w_crit_mult
        damage = int(damage)
        if mob_choice.health <= damage:
            damage = mob_choice.health
        if mob_rolls['scare'] and heroine_rolls['fear']:
            print(f"As {heroine.heroine_name} approaches {mob_choice.name}, she uncontrollably recoils at the very sight of them.  Way to go dipshit, you just lost that turn.")
            next()
            return (party, mobs, False)
        if heroine_rolls['miss']:
            print(f"Wow, that was a big ol' whiff now wasn't it, {heroine.heroine_name}.")
            next()
            return (party, mobs, False)
        if mob_rolls['dodge']:
            if heroine_rolls['expertise']:
                mob_choice = update_health(mob_choice, damage)
                print(f"Despite their best effort to evade the attack, {heroine.heroine_name} successfully contacts {mob_choice.name} for {damage} hp.")
                if mob_choice.is_dead:
                    return (party, mobs, heroine_rolls['luck'])
                check_tough(tough, mob_choice.name)
                next()
                return (party, mobs, heroine_rolls['luck'])
            else:
                print(f"You are probably not worthy of facing this foe.  {mob_choice.name} easily evades {heroine.heroine_name}'s attack.")
                next()
                return (party, mobs, heroine_rolls['luck'])
        mob_choice = update_health(mob_choice, damage)
        print(f"{heroine.heroine_name} slams {mob_choice.name} with her {item['item_desc']} for {damage} hp.")
        if mob_choice.is_dead:
            print(f"{mob_choice.name} has been slain!!")
            next()
            return (party, mobs, heroine_rolls['luck'])
        check_tough(tough, mob_choice.name)
        next()
        return (party, mobs, heroine_rolls['luck'])
    #delete this eventually - just need the function to return something, no matter what
    return (party, mobs, heroine_rolls['luck'])

def player_turn(heroine : object, party : list, mobs : list) -> tuple:
    if heroine.is_dead:
        return (party, mobs, False)
    inv = heroine.inv
    inv_len = len(inv)
    if inv_len < 1:
        print(f"{heroine.heroine_name} has no inventory, so I guess she's skipping this turn...")
        next()
        return (party, mobs, False)
    item_choices = [str(x) for x in list(range(1,inv_len + 1))]
    item_choice = None
    ok = False
    while not ok:
        print(f"\n{heroine.heroine_name}'s turn:")
        display_inventory(inv)
        item_choice = input("Pick the number for whatever item you feel like using. Not that it's going to matter...  ")
        if item_choice in item_choices:
            ok = True
        else:
            print(f'\nNo, numb-nuts, choose one of the numbers!\n')

    items = acc.get_items()
    item = items[items['item'] == heroine.inv[int(item_choice) - 1]].iloc[0]
    item_attack_type = item['attack_type']

    if item_attack_type == 'aoe':
        None

    mobs_len = len(mobs)

    mob_choice = None
    if heroine.hero_class == 'Cleric':
        mob_choice = get_target_choice(mobs, party)
    elif item['damage_range_high'] < 0:
        mob_choice = heroine
    else:
        if mobs_len > 1:
            mob_choice = get_target_choice(mobs, [])
        else:
            mob_choice = mobs[0]
    
    heroine_rolls = get_heroine_rolls(heroine)
    if mob_choice in mobs:
        mob_rolls = get_mob_rolls(mob_choice)
        return get_heroine_turn_outcome(heroine, item, mob_choice, party, mobs, heroine_rolls, mob_rolls)
    else:
        return get_heroine_turn_outcome(heroine, item, mob_choice, party, mobs, heroine_rolls, {})

def party_wiped_taunt(mob : object, party : list) -> str:
    items = acc.get_items()
    melee_items = items[items['attacke_type'] == 'melee']
    melee_names = set(melee_items['item'])

    have_items = [(heroine, item_name) for heroine in party for item_name in heroine.inv if item_name in melee_names]
    if len(have_items) > 0:
        victim, item_name = random.choice(have_items)
        item_desc = melee_items[melee_items['item'] == item_name].iloc[0]['item_desc']
        victim2 = random.choice(party)
        template = random.choice(acc.item_specific_wipe_taunts())
        return template.format(mob=mob.name, victim=victim.heroine_name, item=item_desc, victim2=victim2.heroine_name)
    victim = random.choice(party)
    template = random.choice(acc.generic_wipe_taunts())
    return template.format(mob=mob.name, victim=victim.heroine_name)

def mob_turn(mob : object, party : list, mobs : list) -> tuple:
    print('Mob Turn')
    next()
    if mob.is_dead:
        return (party, mobs, False)
    if party['wiped']:
        print(party_wiped_taunt(mob, party))
        next()
        return (party, mobs, False)
    inv = mob.inv

    ai = mob.starting_ai
    if mob.enraged:
        ai = mob.enraged_ai

        '''
        easy: 1) random target, 2) "random" attack tendency towards weaker weapons

        medium: 1) random target, 3

        hard: 1) targets healers, 2) checks party general health, chooses aoe attack if this is the case 3) checks heroine low in health and try to take them out 4) tendency towards stronger weapons
        '''
    
    return (party, mobs, False)# "False" is a placeholder for the "luck" roll of the mob, to return whether they will have a second turn or not
