import Slayer_Accessory as acc
from Slayer_UI import say, pause, choose, choose_target, show_battle
import random

async def show_current_status(party: list, mobs: list, round_num: int):
    await show_battle(party, mobs, round_num) # the round/enemy/party layout lives in Slayer_UI now

def get_heroine_rolls(heroine: object) -> dict:
    heroine_stats = heroine.stats
    roll_results = {}
    if acc.roll_percent(heroine_stats['crit_chance']):
        roll_results['crit_mult'] = heroine_stats['crit_mult']
    else:
        roll_results['crit_mult'] = 1 # if not a crit, multiplier is 1
    for stat in ['hit', 'luck', 'expertise', 'toughness', 'dodge', 'parry', 'fear']:
        roll_results[stat] = acc.roll_percent(heroine_stats[stat])
    roll_results['heal'] = acc.roll_percent(heroine_stats['heal_chance'])
    roll_results['aoe_heal'] = acc.roll_percent(heroine_stats['aoe_heal_chance'])
    return roll_results

def get_mob_rolls(mob: object) -> dict:
    mob_stats = mob.stats
    prefix = 'enraged_' if mob.enraged else '' # an enraged mob rolls against the enraged_ columns from mobs.csv
    roll_results = {}
    if acc.roll_percent(mob_stats[prefix + 'crit_chance']):
        roll_results['crit_mult'] = mob_stats[prefix + 'crit_mult']
    else:
        roll_results['crit_mult'] = 1
    for stat in ['hit', 'luck', 'expertise', 'toughness', 'dodge']:
        roll_results[stat] = acc.roll_percent(mob_stats[prefix + stat])
    roll_results['heal'] = acc.roll_percent(mob_stats[prefix + 'heal_chance'])
    roll_results['scare'] = acc.roll_percent(mob_stats[prefix + 'scare'])
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

async def check_tough(tough : bool, target : object) -> None:
    if tough and not target.is_mob:
        await say(f"{target.name}, being the tough muthafucka she is, shrugs off half the damage.  Hell yeah!")
    elif tough and target.is_mob:
        await say(f"Damn... {target.name} is one tough piece-of-shit.  They absorbed HALF of the initial damage inflicted!")

def item_label(item_name : str) -> str: # one line of the item menu
    data = acc.get_item(item_name)
    desc = data['item_desc']
    low = data['damage_low']
    high = data['damage_high']
    if data['attack_type'] == 'hail_mary':
        return f'{desc} (hail mary)'
    if low >= 0:
        return f'{desc} ({low} - {high} damage)'
    else:
        return f'{desc} ({-1 * high} - {-1 * low} healing)'

async def get_target_choice(mobs : list, party : list, healing : bool = False) -> object:
    living_party = [x for x in party if not x.is_dead]
    living_mobs = [x for x in mobs if not x.is_dead]
    living_targets = living_party + living_mobs
    if len(living_targets) == 1:
        return living_targets[0]
    if healing:
        prompts = [
            "Pick the number for whoever needs a little TLC.  ",
            "Who gets the healing love this time?  Pick a number.  ",
        ]
        oopses = [
            "\nNo, no, one of THOSE numbers.  Somebody's bleeding over here, hurry up:  "
        ]
    else:
        prompts = [
            "Pick the number for your target.  Make 'em regret it.  ",
        ]
        oopses = [
            "\nWhoa, no, one of THOSE numbers.  Choose the one belonging to whoever you'd like to fuck up:  ",
        ]
    return await choose_target(prompts, living_party, living_mobs, oopses) # lists the targets, keeps asking until the pick is valid

async def get_heal_outcome(heroine : object, item : dict, target : object, party_dict : dict, mobs : list, heroine_rolls : dict, heal_w_crit_mult : float) -> tuple:
    """Every heal, whoever it's aimed at. The amount uses the healer's own class crit
    multiplier (no flat doubling) and never goes past the target's max HP."""
    healing = -int(heal_w_crit_mult) # heal items have negative damage numbers, so flip the sign
    missing_hp = target.starting_health - target.health
    if healing > missing_hp:
        healing = missing_hp

    if target.is_mob:
        # Later: undead go here (the Cleric's heals hurt them; anyone else's heal is a lost turn).
        if target.health == target.starting_health:
            await say(f"That was weird.  {target.name} is your enemy and is at full health anyway, goof.  Oh well, better luck choosing a target next time?")
            await pause()
            return (party_dict, mobs, False)
        target = update_health(target, -healing) # a heal on a mob never fails: picking the target was the mistake
        if heroine.hero_class == 'Cleric': # she's a professional, she should know better
            await say([
                f"{heroine.name} successfully heals {target.name} for {healing} hp.  What in the flying-fuck were you thinking?  Are you trying to give me gas?",
                f"{heroine.name} swells with pride as she successfully heals {target.name} for {healing} hp.  Pride eh?  Well.... Good Job??",
                f"{target.name} grins wickedly at {heroine.name} as their wounds begin to bind.  \"Thank you!\" {target.name} screams in your face, spraying you with spittle.  Did you expect that to go a different way or something?",
                f"{heroine.name} lays her holy hands on {target.name} for {healing} hp.  Somewhere up there, a god just facepalmed so hard it echoed.",
                f"Ah yes, the classic \"heal the guy who's trying to murder us\" strategy.  {heroine.name} patches up {target.name} for {healing} hp.  Bold.  Stupid, but bold.",
            ])
        else:
            await say(f"{heroine.name} takes it upon herself to use her {item['item_desc']} to heal {target.name} for {healing} hp")
            await say("I swear I'm on your side here, but what was she thinking?  I guess she wanted more of a challenge?")
        await pause()
        if hasattr(target, 'healed_by'): # some mobs have something to say about it (Happy does)
            await target.healed_by(heroine)
        return (party_dict, mobs, False) # healing a mob never earns the luck roll

    if not heroine_rolls['heal']:
        await say(f"{heroine.name} tries to heal {'herself' if heroine == target else target.name}, but does a piss-poor job and just ends up wasting her turn.  Doh!")
        await pause()
        return (party_dict, mobs, False)
    if target.health == target.starting_health:
        await say(f"That was weird.  {target.name} is at full health, goof.  Oh well, better luck choosing a target next time?")
        await pause()
        return (party_dict, mobs, heroine_rolls['luck'])
    target = update_health(target, -healing)
    await say(f"{heroine.name} quickly uses {item['item_desc']} to heal {'herself' if heroine == target else target.name} for {healing} hp")
    await say("I'm so proud of you!")
    await pause()
    return (party_dict, mobs, heroine_rolls['luck'])

async def use_hail_mary(heroine : object, item : dict, party_dict : dict, mobs : list) -> tuple:
    """The Token of the Wise Witch, for when things look grim: 30% a fallen heroine comes back
    at half her max HP, 30% the Token takes the heroine using it instead, 40% it fizzles."""
    fallen = [x for x in party_dict['party'] if x.is_dead]
    chosen = None
    if len(fallen) == 1:
        chosen = fallen[0]
    elif fallen:
        chosen = await choose_target(
            f"\nThe Token hums in {heroine.name}'s hand.  Pick the number for the fallen heroine you're gambling on.  ",
            fallen, [], "\nOne of THOSE numbers.  The dead are waiting, and frankly so am I:  ")
    roll = acc.multi_roll(1, 100)
    if roll <= 30:
        if chosen:
            chosen.is_dead = False
            chosen.health = max(1, round(chosen.starting_health * 0.5))
            await say(f"{heroine.name} raises the {item['item_desc']} and mutters something she definitely made up on the spot.  It WORKS.  {chosen.name} gasps back to life with {chosen.health} hp.  Holy shit!")
        else:
            await say(f"The {item['item_desc']} glows a lovely, life-giving green...  and finds nobody dead to bring back.  It sulks.  Wasted turn, but hey, everybody's alive.")
    elif roll <= 60:
        heroine.health = 0
        heroine.is_dead = True
        await say(f"The {item['item_desc']} flares a sickly purple.  Turns out the Wise Witch wanted payment, and {heroine.name} just covered it.  With her life.  Oof.")
    else:
        await say(f"{heroine.name} shakes the {item['item_desc']} like a broken snow globe.  It fizzles.  Pfft.  Nothing happens.")
    await pause()
    return (party_dict, mobs, False)

async def get_heroine_turn_outcome(heroine : object, item : dict,  target : object, party_dict : dict,  mobs : list, heroine_rolls : dict, mob_rolls : dict) -> tuple:
    base_damage = acc.multi_roll(item['damage_low'], item['damage_high'])
    attack_type = item['attack_type']
    crit_mult = heroine_rolls['crit_mult']
    is_crit = crit_mult > 1 # will be used for auto commenting later
    damage_w_crit_mult = base_damage * crit_mult
    if attack_type == 'heal': # every heal, on a heroine or a mob, has its own function
        return await get_heal_outcome(heroine, item, target, party_dict, mobs, heroine_rolls, damage_w_crit_mult)
    if target.is_mob:  # an attack on a mob
        tough = mob_rolls['toughness']
        if tough:
            damage = damage_w_crit_mult / 2
        else:
            damage = damage_w_crit_mult
        damage = int(damage)
        if target.health <= damage:
            damage = target.health
        if mob_rolls['scare'] and heroine_rolls['fear']:
            await say(f"As {heroine.name} approaches {target.name}, she uncontrollably recoils at the very sight of them.  Honestly?  Fair.  That's a lost turn, though.")
            await pause()
            return (party_dict, mobs, False)
        if not heroine_rolls['hit']:
            await say(f"Wow, that was a big ol' whiff, now wasn't it, {heroine.name}.")
            await pause()
            return (party_dict, mobs, False)
        if mob_rolls['dodge'] and not heroine_rolls['expertise']:
            await say(f"{target.name} slips out of the way like a greased weasel.  {heroine.name}'s attack finds only air.")
            await pause()
            return (party_dict, mobs, False)
        target = update_health(target, damage)
        if mob_rolls['dodge']: # it dodged, but her expertise beat it
            await say(f"Despite their best effort to evade the attack, {heroine.name} successfully contacts {target.name} for {damage} hp.")
        else:
            await say(f"{heroine.name} slams {target.name} with her {item['item_desc']} for {damage} hp.")
        if target.mob_class == 'Disgruntled Dwarf' and target.enraged and target.is_dead:
            party_dict = acc.wipe_party(party_dict)
            return (party_dict, mobs, False)
        if target.mob_class == 'Disgruntled Dwarf' and target.health < 0.5 * target.starting_health and not target.enraged:
            await target.enrage()
            await pause()
            return (party_dict, mobs, False)
        if target.is_dead:
            await say(f"{target.name} has been slain!!  Take THAT motherfucker!!")
            await pause()
            return (party_dict, mobs, heroine_rolls['luck'])
        await check_tough(tough, target)
        await pause()
        return (party_dict, mobs, heroine_rolls['luck'])
    else: # can't happen today (only heals can target the party), but never a silent turn
        await say(f"{heroine.name} waves her {item['item_desc']} at {target.name}.  Nothing happens.  Weird flex.")
        await pause()
        return (party_dict, mobs, False)

async def player_turn(heroine : object, party_dict : dict, mobs : list) -> tuple:
    if heroine.is_dead:
        return (party_dict, mobs, False)
    inv = heroine.inv
    inv_len = len(inv)
    if inv_len < 1:
        await say(f"{heroine.name} has no inventory, so I guess she's skipping this turn...")
        await pause()
        return (party_dict, mobs, False)
    await say(f"\n{heroine.name}'s turn:")
    item_labels = [item_label(item) for item in inv]
    if inv_len > 1:
        item_choice = await choose( # lists the items, keeps asking until the pick is valid
            "Pick the number for whatever item you feel like using.  Choose wisely.  Or don't, chaos is fun too...  ",
            item_labels,
            f"\nNo, numb-nuts... sorry, I mean {party_dict['name']}, please choose one of the numbers!\n",
        )
    else:
        await say(f'1:  {item_labels[0]}')
        await say(f"Looks like {heroine.name} has but one item remaining, so I'm just going to assume it's the one you want and select it for you, mkay?")
        await pause()
        item_choice = 0

    item = acc.get_item(inv[item_choice])
    item_attack_type = item['attack_type']
    is_heal = item_attack_type == 'heal'

    if item_attack_type == 'aoe':
        pass # stub for aoe attacks/heals, from mobs and heroines, to be added still
    if item_attack_type == 'hail_mary':
        return await use_hail_mary(heroine, item, party_dict, mobs)

    if is_heal:
        target = await get_target_choice(mobs, party_dict['party'], True) # anyone can heal anyone, a mob too if they insist
    else:
        target = await get_target_choice(mobs, [])

    heroine_rolls = get_heroine_rolls(heroine)
    if target.is_mob:
        mob_rolls = get_mob_rolls(target)
        return await get_heroine_turn_outcome(heroine, item, target, party_dict, mobs, heroine_rolls, mob_rolls)
    else:
        return await get_heroine_turn_outcome(heroine, item, target, party_dict, mobs, heroine_rolls, {})

def party_wiped_taunt(mob : object, party : list) -> str:
    # first make sure at least one heroine exists (may need to adjust to starting count of party, per encounter?) and still has a melee item, if we want to include item-specific taunts
    if len(party) > 1 :
        melee_names = {item['item'] for item in acc.get_items() if item['attack_type'] == 'melee' and not item['special']} # regular melee weapons only, specials left out (same as before the special column)
        have_items = [(heroine, item_name) for heroine in party for item_name in heroine.inv if item_name in melee_names]
        # if anyone has a melee weapon, which may need to be refined by hero_class or something to avoid things like Sappers' "Deep Scratch", there is a 50:50 chance of doing item-specific or non-item-specific taunts so that both lists are actually used haha
        if len(have_items) > 0:
            do_item_taunt = random.choice([True, False])
            if do_item_taunt:
                victim, item_name = random.choice(have_items)
                victim2 = random.choice([x for x in party if x != victim])
                item_desc = acc.get_item(item_name)['item_desc']
                template = random.choice(acc.item_specific_wipe_taunts())
                return template.format(mob=mob.name, victim=victim.name, item=item_desc, victim2=victim2.name)
        # emergency backup if noone has an item - can't really see this happening but hey, it's here
        victim = random.choice(party)
        victim2 = random.choice([x for x in party if x != victim])
        template = random.choice(acc.generic_wipe_taunts())
        return template.format(mob=mob.name, victim=victim.name, victim2=victim2.name)
    elif len(party) == 1:
        return f"\n{mob.name} walks over to {party[0].name}'s mangled corpse and spits on it.  \"What kind of FUCKING idiot attempts a dungeon encounter solo?!\""
    else:
        return "No party members.  Right...."

def choose_mob_item(inv : list, ai : str, party_dict : dict) -> dict:
    mob_inv = [dict(item) for item in acc.get_mob_equipment() if item['item'] in inv and item['attack_type'] == 'melee'] ###### since we haven't worked on aoe or ranged attacks logic, just doing melee for now, this will need to be fixed, especially for when higher ai is factored in
    if ai == 'easy':
        return random.choice(mob_inv)
    return random.choice(mob_inv) # for now it just always returns this, but this will update with other ai mode updates

def choose_mob_target(targets : list, ai : str) -> object:
    if ai == 'easy':
        return random.choice(targets)
    return random.choice(targets) # for now it just always returns this, but this will update with other ai mode updates

async def get_mob_turn_outcome(mob : object, target : object, item : dict, party_dict : dict, mobs : list, mob_rolls : dict, target_rolls : dict) -> tuple:
    base_delta = acc.multi_roll(item['damage_low'], item['damage_high'])
    attack_type = item['attack_type'] # for future use to determine aoe outcomes
    crit_mult = mob_rolls['crit_mult']
    is_crit = crit_mult > 1 # intended to be used for autocommenting, for future work
    delta_w_crit = base_delta * crit_mult
    if item['damage_high'] < 0:
        healing = -int(delta_w_crit)
        if target.health + healing > target.starting_health:
            healing = target.starting_health - target.health
        if target.is_mob:
            if not mob_rolls['heal']:
                await say(f"{mob.name} attempts to heal {target.name if target != mob else 'themself'} with {item['item_desc']}, but fucks up and nothing happens.  Idiot!")
                await pause()
                return (party_dict, mobs, False)
            if mob == target:
                mob = update_health(mob, -healing)
                await say(f"Using their {item['item_desc']}, {mob.name} heals for {healing} hp.  Oh dear.")
                await pause()
                return (party_dict, mobs, mob_rolls['luck'])
            else:
                target = update_health(target, -healing)
                await say(f"Using their {item['item_desc']}, {mob.name} heals {target.name} for {healing} hp.  Ugh, teamwork.  Gross.")
                await pause()
                return (party_dict, mobs, mob_rolls['luck'])
        else:
            await say('Need logic for mobs healing party members, in case we decide to do this.  I say no luck roll for it, though.')
            await pause()
            return (party_dict, mobs, False) # add logic for mob healing party members
    else:
        if not target.is_mob:
            tough = target_rolls['toughness']
            parry = target_rolls['parry'] and attack_type == 'melee'
            damage = int(delta_w_crit)
            if tough:
                damage = int(damage / 2)
            if parry:
                damage = int(damage / 2)
            if target.health <= damage:
                damage = target.health
            if not mob_rolls['hit']:
                await say(f"{mob.name} attempts to attack {target.name} with their {item['item_desc']}, but misses widely.")
                await pause()
                return (party_dict, mobs, False)
            if target_rolls['dodge'] and not mob_rolls['expertise']:
                await say(f"HELL YES!  {target.name} dodges {mob.name}'s attack like a goddamn ninja!")
                await pause()
                return (party_dict, mobs, False)
            target = update_health(target, damage)
            if target_rolls['dodge']: # she tried to dodge, but its expertise beat her
                await say(f"Despite her best effort to dodge the attack, {mob.name} strikes {target.name} with their {item['item_desc']} for {damage} hp.")
            else:
                await say(f"{mob.name} bashes {target.name} with their {item['item_desc']} for {damage} hp.")
            if target.is_dead:
                await say([
                    f"NOOO!  {target.name} has been slain!  We'll remember you, bud.",
                    f"Oh shit.  {target.name} has been slain.  She'll be back next run, but damn, that one hurt.",
                ])
                await pause()
                return (party_dict, mobs, mob_rolls['luck'])
            if parry:
                await say([
                    f"But {target.name} manages to deflect half of the damage!  Way to go!",
                    f"But {target.name} manages to parry half of the damage!  Incredible!",
                ])
            await check_tough(tough, target)
            await pause()
            return (party_dict, mobs, mob_rolls['luck'])
        else:
            await say('Filler for mobs attacking each other, if I decide to have a berserker spell or perhaps a witch can cast confusion or something that makes mobs attack each other, or just randomly in general (party or other mobs can be attacked?).  Might be fun.')
            await pause()
            return (party_dict, mobs, mob_rolls['luck'])

async def mob_turn(mob : object, party_dict : dict, mobs : list) -> tuple:
    if mob.is_dead:
        return (party_dict, mobs, False)
    if party_dict['wiped']:
        await say(party_wiped_taunt(mob, party_dict['party']))
        await pause()
        return (party_dict, mobs, False)

    await say(f"\n\n{mob.name}'s turn:\n")
    inv = mob.inv

    ai = mob.starting_ai
    if mob.enraged:
        ai = mob.enraged_ai

    item = choose_mob_item(inv, ai, party_dict)
    if item['damage_high'] < 0:
        living_mobs = [x for x in mobs if not x.is_dead]
        if len(living_mobs) > 0:
            target = choose_mob_target(living_mobs, ai)
            mob_rolls = get_mob_rolls(mob)
            return await get_mob_turn_outcome(mob, target, item, party_dict, mobs, mob_rolls, {})
    else:
        living_heroines = [x for x in party_dict['party'] if not x.is_dead]
        if len(living_heroines) > 0:
            target = choose_mob_target(living_heroines, ai)
            mob_rolls = get_mob_rolls(mob)
            target_rolls = get_heroine_rolls(target)
            return await get_mob_turn_outcome(mob, target, item, party_dict, mobs, mob_rolls, target_rolls)
    return (party_dict, mobs, False)
