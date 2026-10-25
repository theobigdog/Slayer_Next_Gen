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

def show_current_status(party: list, mobs: list, round_num: int):
    wt() 
    print(f'Round:{round_num}\n\n')
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
    hit = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['hit_cutoff'])#heroine_stats['hit'])
    luck = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['luck_cutoff'])
    expertise = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['expertise_cutoff'])
    toughness = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['toughness_cutoff'])
    dodge = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['dodge_cutoff'])
    parry = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['parry_cutoff'])
    fear = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['fear_cutoff'])
    heal = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['heal_cutoff'])
    aoe_heal = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['aoe_heal_cutoff'])
    if crit <= heroine_stats['crit']:
        roll_results['crit_mult'] = heroine_stats['crit_mult'] # crit roll is higher than cutoff, so the crit_mult is returned
    else:
        roll_results['crit_mult'] = 1 # if not a crit, multiplier is 1
    roll_results['hit'] = hit <= heroine_stats['hit']
    roll_results['luck'] = luck <= heroine_stats['luck']
    roll_results['expertise'] = expertise <= heroine_stats['expertise']
    roll_results['toughness'] = toughness <= heroine_stats['toughness']
    roll_results['dodge'] = dodge <= heroine_stats['dodge']
    roll_results['parry'] = parry <= heroine_stats['parry']
    roll_results['fear'] = fear <= heroine_stats['fear']
    roll_results['heal'] = heal <= heroine_stats['heal']
    roll_results['aoe_heal'] = aoe_heal <= heroine_stats['aoe_heal']
    return roll_results

def get_mob_rolls(mob: object) -> dict:
    roll_results = {}
    mob_stats = mob.stats
    enraged = mob.enraged
    mob_dice_cutoffs = acc.get_dice_cutoffs_mobs()
    crit = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['crit_cutoff'])
    hit = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['hit_cutoff'])
    luck = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['luck_cutoff'])
    expertise = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['expertise_cutoff'])
    toughness = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['toughness_cutoff'])
    dodge = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['dodge_cutoff'])
    heal = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['healing_chance_cutoff'])
    scare = acc.multi_roll(mob_dice_cutoffs['low'], mob_dice_cutoffs['scare_cutoff'])
    if enraged:
        if crit <= mob_stats['enraged_crit_chance']:
            roll_results['crit_mult'] = mob_stats['enraged_crit']
        else:
            roll_results['crit_mult'] = 1
        roll_results['hit'] = hit <= mob_stats['enraged_hit']
        roll_results['luck'] = luck <= mob_stats['enraged_luck']
        roll_results['expertise'] = expertise <= mob_stats['enraged_expertise']
        roll_results['toughness'] = toughness <= mob_stats['enraged_toughness']
        roll_results['dodge'] = dodge <= mob_stats['enraged_dodge']
        roll_results['heal'] = heal <= mob_stats['enraged_healing']
        roll_results['scare'] = scare <= mob_stats['enraged_scare']
    else:
        if crit <= mob_stats['crit_chance']:
            roll_results['crit_mult'] = mob_stats['crit']
        else:
            roll_results['crit_mult'] = 1
        roll_results['hit'] = hit <= mob_stats['hit']
        roll_results['luck'] = luck <= mob_stats['luck']
        roll_results['expertise'] = expertise <= mob_stats['expertise']
        roll_results['toughness'] = toughness <= mob_stats['toughness']
        roll_results['dodge'] = dodge <= mob_stats['dodge']
        roll_results['heal'] = heal <= mob_stats['healing']
        roll_results['scare'] = scare <= mob_stats['scare']
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

def check_tough(tough : bool, target : object) -> None:
    if tough and hasattr(target, 'hero_class'):
        print(f"{target.heroine_name}, being the tough muthafucka she is, shrugs off half the damage.  Hell yeah!")
    elif tough and hasattr(target, 'mob_class'):
        print(f"Damn... {target.name} is one tough piece-of-shit.  They absorbed HALF of the initial damage inflicted!")

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
    living_mobs = [x for x in mobs if not x.is_dead]
    mobs_len = len(living_mobs)
    if mobs_len == 1:
        return living_mobs[0]
    targets = {}
    party_len = len(party)
    if party_len > 0:
        print()
        print('Party Members:')
        for i in range(party_len):
            if not party[i].is_dead:
                print(f'{counter}: {party[i].heroine_name}')
                targets[counter] = party[i]
                counter += 1
    if mobs_len > 0:
        print()
        print('Mobs:')
        for i in range(mobs_len):
            if not mobs[i].is_dead:
                print(f'{counter}: {mobs[i].name}')
                targets[counter] = mobs[i]
                counter += 1
    
    target_choices = [str(x) for x in list(range(1,counter))]
    target_choice = None
    ok = False
    while not ok:
        target_choice = input("Pick the number for your target.  Make 'em regret it.  ")
        if target_choice in target_choices:
            ok = True
        else:
            print(f'\nWhoa, no, one of THOSE numbers.  The one belonging to whoever you\'d like to fuck up:  ')
    target = targets[int(target_choice)]
    return target

def get_heroine_turn_outcome(heroine : object, item : dict,  mob_choice : object, party_dict : dict,  mobs : list, heroine_rolls : dict, mob_rolls : dict) -> tuple:
    base_damage = acc.multi_roll(item['damage_range_low'], item['damage_range_high'])
    attack_type = item['attack_type'] # to be used for future work
    crit_mult = heroine_rolls['crit_mult']
    is_crit = crit_mult > 1 # will be used for auto commenting later
    damage_w_crit_mult = base_damage * crit_mult
    damage = None
    if len(mob_rolls.keys()) > 0:  # check to see if it is an attack or not
        if attack_type == 'heal' and heroine.hero_class != 'Cleric':
            healing = -int(damage_w_crit_mult)
            missing_hp = mob_choice.starting_health - mob_choice.health
            if healing > missing_hp:
                healing = missing_hp
            if mob_choice.health == mob_choice.starting_health:
                print(f"That was weird.  {mob_choice.name} is your enemy and is at full health anyway, goof.  Oh well, better luck choosing a target next time?")
                next()
                return (party_dict, mobs, False)
            mob_choice = update_health(mob_choice, -healing)
            print(f"{heroine.heroine_name} takes it upon herself to use her {item['item_desc']} to heal {mob_choice.name} for {healing} hp")
            print(f"I swear I'm on your side here, but what was she thinking?  I guess she wanted more of a challenge?")
            next()
            return (party_dict, mobs, False)
        tough = mob_rolls['toughness']
        if tough:
            damage = damage_w_crit_mult / 2
        else:
            damage = damage_w_crit_mult
        damage = int(damage)
        #if mob_choice.mob_class == 'Disgruntled Dwarf' and (mob_choice.health < 0.5 * mob_choice.starting_health or mob_choice.health <= damage):
         #   mob_choice.toggle_enraged()
          #  next()
           # return (party_dict, mobs, False)
        if mob_choice.health <= damage:
            damage = mob_choice.health
        if mob_rolls['scare'] and heroine_rolls['fear']:
            print(f"As {heroine.heroine_name} approaches {mob_choice.name}, she uncontrollably recoils at the very sight of them.  Honestly?  Fair.  That's a lost turn, though.")
            next()
            return (party_dict, mobs, False)
        if not heroine_rolls['hit']:
            print(f"Wow, that was a big ol' whiff, now wasn't it, {heroine.heroine_name}.")
            next()
            return (party_dict, mobs, False)
        if mob_rolls['dodge']:
            if heroine_rolls['expertise']:
                mob_choice = update_health(mob_choice, damage)
                print(f"Despite their best effort to evade the attack, {heroine.heroine_name} successfully contacts {mob_choice.name} for {damage} hp.")
                if mob_choice.mob_class == 'Disgruntled Dwarf' and mob_choice.health < 0.5 * mob_choice.starting_health  and not mob_choice.enraged:
                    mob_choice.toggle_enraged()
                    next()
                    return (party_dict, mobs, False)
                if mob_choice.is_dead:
                    print(f"{mob_choice.name} has been slain!!")
                    next()
                    return (party_dict, mobs, heroine_rolls['luck'])
                check_tough(tough, mob_choice)
                next()
                return (party_dict, mobs, heroine_rolls['luck'])
            else:
                print(f"{mob_choice.name} slips out of the way like a greased weasel.  {heroine.heroine_name}'s attack finds only air.")
                next()
                return (party_dict, mobs, False)
        mob_choice = update_health(mob_choice, damage)
        print(f"{heroine.heroine_name} slams {mob_choice.name} with her {item['item_desc']} for {damage} hp.")
        if mob_choice.mob_class == 'Disgruntled Dwarf' and mob_choice.health < 0.5 * mob_choice.starting_health and not mob_choice.enraged:
            mob_choice.toggle_enraged()
            next()
            return (party_dict, mobs, False)
        if mob_choice.is_dead:
            print(f"{mob_choice.name} has been slain!!")
            next()
            return (party_dict, mobs, heroine_rolls['luck'])
        check_tough(tough, mob_choice)
        next()
        return (party_dict, mobs, heroine_rolls['luck'])
    else:
        if attack_type == 'heal':
            if not heroine_rolls['heal']:
                print(f"{heroine.heroine_name} tries to heal {'herself' if heroine == mob_choice else mob_choice.heroine_name}, but does a piss-poor job and just ends up wasting her turn.  Doh!")
                next()
                return (party_dict, mobs, False)
            healing = -int(damage_w_crit_mult)
            missing_hp = mob_choice.starting_health - mob_choice.health
            if healing > missing_hp:
                healing = missing_hp
            if mob_choice.health == mob_choice.starting_health:
                print(f"That was weird.  {mob_choice.heroine_name} is at full health, goof.  Oh well, better luck choosing a target next time?")
                next()
                return (party_dict, mobs, heroine_rolls['luck'])
            mob_choice = update_health(mob_choice, -healing)
            print(f"{heroine.heroine_name} quickly uses {item['item_desc']} to heal {'herself' if heroine == mob_choice else mob_choice.heroine_name} for {healing} hp")
            print(f"I'm so proud of you!")
            next()
            return (party_dict, mobs, heroine_rolls['luck'])
        next()
        return (party_dict, mobs, heroine_rolls['luck'])

def player_turn(heroine : object, party_dict : dict, mobs : list) -> tuple:
    if heroine.is_dead:
        return (party_dict, mobs, False)
    inv = heroine.inv
    inv_len = len(inv)
    if inv_len < 1:
        print(f"{heroine.heroine_name} has no inventory, so I guess she's skipping this turn...")
        next()
        return (party_dict, mobs, False)
    item_choices = [str(x) for x in list(range(1,inv_len + 1))]
    item_choice = None
    ok = False
    if len(item_choices) > 1:
        while not ok:
            print(f"\n{heroine.heroine_name}'s turn:")
            display_inventory(inv)
            item_choice = input("Pick the number for whatever item you feel like using.  Choose wisely.  Or don't, chaos is fun too...  ")
            if item_choice in item_choices:
                ok = True
            else:
                print(f'\nNo, numb-nuts.... sorry, I meant {party_dict['name']}, choose one of the numbers!\n')
    else:
        print(f"\n{heroine.heroine_name}'s turn:")
        display_inventory(inv)
        print(f"Looks like {heroine.heroine_name} has but one item remaining, so I'm just going to assume it's the one you want and select it for you, mkay?")
        next()
        item_choice = 1

    items = acc.get_items()
    item = items[items['item'] == heroine.inv[int(item_choice) - 1]].iloc[0]
    item_attack_type = item['attack_type']

    if item_attack_type == 'aoe':
        None

    mobs_len = len([x for x in mobs if not x.is_dead])

    mob_choice = None
    if heroine.hero_class == 'Cleric':
        mob_choice = get_target_choice(mobs, party_dict['party'])
    elif item_attack_type == "heal":
        mob_choice = get_target_choice([], party_dict['party'])
    else:
        if mobs_len > 1:
            mob_choice = get_target_choice(mobs, [])
        else:
            mob_choice = mobs[0]
    
    heroine_rolls = get_heroine_rolls(heroine)
    if mob_choice in mobs:
        mob_rolls = get_mob_rolls(mob_choice)
        return get_heroine_turn_outcome(heroine, item, mob_choice, party_dict, mobs, heroine_rolls, mob_rolls)
    else:
        return get_heroine_turn_outcome(heroine, item, mob_choice, party_dict, mobs, heroine_rolls, {})

def party_wiped_taunt(mob : object, party : list) -> str:
    # first make sure at least one heroine exists (may need to adjust to starting count of party, per encounter?) and still has a melee item, if we want to include item-specific taunts
    if len(party) > 1 :
        items = acc.get_items()
        melee_items = items[items['attack_type'] == 'melee']
        melee_names = set(melee_items['item'])
        have_items = [(heroine, item_name) for heroine in party for item_name in heroine.inv if item_name in melee_names]
        # if anyone has a melee weapon, which may need to be refined by hero_class or something to avoid things like Sappers' "Deep Scratch", there is a 50:50 chance of doing item-specific or non-item-specific taunts so that both lists are actually used haha
        if len(have_items) > 0:
            do_item_taunt = random.choice([True, False])
            if do_item_taunt:
                victim, item_name = random.choice(have_items)
                victim2 = random.choice([x for x in party if x != victim])
                item_desc = melee_items[melee_items['item'] == item_name].iloc[0]['item_desc']
                template = random.choice([random.choice(acc.item_specific_wipe_taunts())])
                return template.format(mob=mob.name, victim=victim.heroine_name, item=item_desc, victim2=victim2.heroine_name)
        # emergency backup if noone has an item - can't really see this happening but hey, it's here
        victim = random.choice(party)
        victim2 = random.choice([x for x in party if x != victim])
        template = random.choice(acc.generic_wipe_taunts())
        return template.format(mob=mob.name, victim=victim.heroine_name, victim2=victim2.heroine_name)
    elif len(party) == 1:
        return f"{mob.name} walks over to {party[0].heroine_name}'s mangled corpse and spits on it.  \"What kind of FUCKING idiot attempts a dungeon encounter solo?!\""
    #  Because I'm sure Claude will ding me if I don't include the "possibility" below!!  So how closely do you read my code, Claude?  LOL!!
    else:
        return "No party members.  Right...."
    
def choose_mob_item(inv : list, ai : str, party_dict : dict) -> dict:
    mob_items = acc.get_mob_equipment()
    mob_inv = mob_items[(mob_items['item'].isin(inv)) & (mob_items['attack_style'] == 'melee')].to_dict('records') ###### since we haven't worked on aoe or ranged attacks logic, just doing melee for now, this will need to be fixed, especially for when higher ai is factored in
    if ai == 'easy':
        return random.choice(mob_inv)
    return random.choice(mob_inv) # for now it just always returns this, but this will update with other ai mode updates

def get_target_mob(mobs : list, ai : str) -> object:
    if ai == 'easy':
        return random.choice(mobs)
    return random.choice(mobs) # for now it just always returns this, but this will update with other ai mode updates

def get_mob_turn_outcome(mob : object, target : object, item : dict, party_dict : dict, mobs : list, mob_rolls : dict, target_rolls : dict) -> tuple:
    base_delta = acc.multi_roll(item['damage_low'], item['damage_high'])
    attack_style = item['attack_style'] # for future use
    crit_mult = mob_rolls['crit_mult']
    is_crit = crit_mult > 1 # intended to be used for autocommenting, for future work
    delta_w_crit = base_delta * crit_mult
    if item['damage_high'] < 0:
        healing = int(delta_w_crit)
        if target.health - healing > target.starting_health:
            healing = target.starting_health - target.health
        if hasattr(target, 'mob_class'):
            if not mob_rolls['heal']:
                print(f"{mob.name} attempts to heal {target.name if target.name != mob.name else 'themself'} with {item['item_desc']}, but fucks up and nothing happens.  Idiot!")
                next()
                return (party_dict, mobs, False)
            if mob == target:
                mob = update_health(mob, healing)
                print(f"Using their {item['item_desc']}, {mob.name} heals for {healing} hp.  Oh dear.")
                next()
                return (party_dict, mobs, mob_rolls['luck'])
            else:
                target = update_health(target, healing)
                print(f"Using their {item['item_desc']}, {mob.name} heals {target.name} for {healing} hp.  Ugh, teamwork.  Gross.")
                next()
                return (party_dict, mobs, mob_rolls['luck'])
        else:
            return (party_dict, mobs, mob_rolls['luck']) # add logic for mob healing party members              
    else:
        if hasattr(target, 'hero_class'):
            tough = target_rolls['toughness']
            parry = target_rolls['parry'] and item['attack_style'] == 'melee'
            damage = int(delta_w_crit)
            if tough:
                damage = int(damage / 2)
            if parry:
                damage = int(damage / 2)
            if target.health <= damage:
                damage = target.health
            if not mob_rolls['hit']:
                print(f"{mob.name} attempts to attack {target.heroine_name} with their {item['item_desc']}, but misses widely.")
                next()
                return (party_dict, mobs, False)
            if target_rolls['dodge']:
                if mob_rolls['expertise']:
                    target = update_health(target, damage)
                    print(f"Despite her best effort to dodge the attack, {mob.name} strikes {target.heroine_name} with their {item['item_desc']} for {damage} hp.")
                    if parry and not target.is_dead:
                        print(f"But {target.heroine_name} manages to deflect half of the damage!  Way to go!")
                        #next()
                        #return (party_dict, mobs, mob_rolls['luck'])
                    if target.is_dead:
                        print(f"NOOO!  {target.heroine_name} has been slain!  We'll remember you, bud.")
                        next()
                        return (party_dict, mobs, mob_rolls['luck'])
                    #if parry:
                       # print(f"But {target.heroine_name} manages to deflect half of the damage!  Way to go!")
                    check_tough(tough, target)
                    next()
                    return (party_dict, mobs, mob_rolls['luck'])
                else:
                    print(f"HELL YES!  {target.heroine_name} dodges {mob.name}'s attack like a goddamn ninja!")
                    next()
                    return(party_dict, mobs, False)
            target = update_health(target, damage)
            print(f"{mob.name} bashes {target.heroine_name} with their {item['item_desc']} for {damage} hp.")
            if target.is_dead:
                print(f"Oh shit.  {target.heroine_name} has been slain.  She'll be back next run, but damn, that one hurt.")
                next()
                return (party_dict, mobs, mob_rolls['luck'])
            if parry:
                print(f"But {target.heroine_name} manages to parry half of the damage!  Incredible!")
            check_tough(tough, target)
            next()
            return (party_dict, mobs, mob_rolls['luck'])

def mob_turn(mob : object, party_dict : dict, mobs : list) -> tuple:
    if mob.is_dead:
        return (party_dict, mobs, False)
    if party_dict['wiped']:
        print(party_wiped_taunt(mob, party_dict['party']))
        next()
        return (party_dict, mobs, False)

    print(f"\n\n{mob.name}'s turn:\n")
    inv = mob.inv

    ai = mob.starting_ai
    if mob.enraged:
        ai = mob.enraged_ai

        '''
        easy: 1) random target, 2) "random" attack tendency towards weaker weapons

        medium: 1) random target, 2) add more criteria later, 3)starts healing themself or mob-party-members

        hard: 1) targets healers, 2) checks party general health, chooses aoe attack if this is the case 3) checks heroine low in health and try to take them out 4) tendency towards stronger weapons, 5) can heal self and/or mob-party, strongly, with aoe and single-target options

        '''
    item = choose_mob_item(inv, ai, party_dict)
    if item['damage_high'] < 0:
        living_mobs = [x for x in mobs if not x.is_dead]
        if len(living_mobs) > 0:
            mob_choice = get_target_mob(living_mobs, ai)
            mob_rolls = get_mob_rolls(mob)
            return get_mob_turn_outcome(mob, mob_choice, item, party_dict, mobs, mob_rolls, {})
        else:
            return (party_dict, mobs, False)
    else:
        living_heroines = [x for x in party_dict['party'] if not x.is_dead]
        if len(living_heroines) > 0:
            target = get_target_mob(living_heroines, ai)
            mob_rolls = get_mob_rolls(mob)
            target_rolls = get_heroine_rolls(target)
            return get_mob_turn_outcome(mob, target, item, party_dict, mobs, mob_rolls, target_rolls)
        else:
            return (party_dict, mobs, False)
