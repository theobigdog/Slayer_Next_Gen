import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import pandas as pd
import joblib as jb
import random
from colorama import Fore, Back, Style, Cursor
import time


def clear_screen():
    """Clear the console screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

# ============================================================================
# YOUR EXISTING FUNCTIONS (KEPT!)
# ============================================================================

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

def show_current_status(party: dict, mob: dict):
    wt()
    print('Enemy')
    display_mob_summary(mob)
    print()
    print()
    print('Party')
    display_party_summary(party)

def get_heroine_rolls(heroine, items=None, chosen_weapon=None):
    """
    Generate attack rolls for a heroine and resolve combat checks.
    
    Args:
        heroine: Hero object
        items: Items dataframe (optional)
        chosen_weapon: Specific weapon to use (optional)
        
    Returns:
        dict: Attack roll values and combat resolution
    """
    # Load items if not provided
    if items is None:
        try:
            items = pd.read_csv('supporting_docs/items.csv')
        except FileNotFoundError:
            print(f"{Fore.RED}WARNING: items.csv not found! Using default damage{Style.RESET_ALL}")
            items = pd.DataFrame()
    
    # Get dice cutoffs
    cutoffs = acc.get_dice_cutoffs()
    
    # Find weapon to use
    equipped_weapon = None
    weapon_data = None
    
    if chosen_weapon and chosen_weapon != "Fists":
        # Use the chosen weapon
        if not items.empty:
            item_row = items[items['item'] == chosen_weapon]
            if not item_row.empty:
                equipped_weapon = chosen_weapon
                weapon_data = item_row
    elif not items.empty and hasattr(heroine, 'inv') and heroine.inv:
        # Auto-select first weapon in inventory
        for item_name in heroine.inv:
            item_row = items[items['item'] == item_name]
            if not item_row.empty:
                attack_type = item_row['attack_type'].values[0]
                # Check if it's a weapon type
                if attack_type in ['melee', 'range', 'both', 'special_melee', 'special_range', 'special_both']:
                    equipped_weapon = item_name
                    weapon_data = item_row
                    break
    
    # If no weapon found, use fists (1-4 damage)
    if weapon_data is None:
        low_damage = 1
        high_damage = 4
        weapon_type = 'melee'
    else:
        low_damage = int(weapon_data['damage_range_low'].values[0])
        high_damage = int(weapon_data['damage_range_high'].values[0])
        weapon_type = weapon_data['attack_type'].values[0]
    
    # Roll base damage
    damage = acc.multi_roll(low_damage, high_damage)
    
    # Apply expertise bonus
    damage += heroine.stats['expertise']
    
    # Generate all combat rolls
    crit_roll = random.randint(cutoffs['low'], cutoffs['crit_cutoff'])
    miss_roll = random.randint(heroine.stats['low_miss'], heroine.stats['high_miss'])
    luck_roll = random.randint(cutoffs['low'], heroine.stats['luck'])
    expertise_roll = random.randint(cutoffs['low'], cutoffs['expertise_cutoff'])
    toughness_roll = random.randint(cutoffs['low'], cutoffs['toughness_cutoff'])
    dodge_roll = random.randint(cutoffs['low'], cutoffs['dodge_cutoff'])
    parry_roll = random.randint(cutoffs['low'], cutoffs['parry_cutoff'])
    fear_roll = random.randint(cutoffs['low'], cutoffs['fear_cutoff'])
    heal_roll = random.randint(cutoffs['low'], cutoffs['heal_cutoff'])
    aoe_heal_roll = random.randint(cutoffs['low'], cutoffs['aoe_heal_cutoff'])
    
    # Resolve combat checks
    is_crit = crit_roll >= heroine.stats.get('crit', 18)
    is_miss = miss_roll >= cutoffs['miss_threshold']
    
    # Apply crit multiplier if crit
    if is_crit:
        damage = int(damage * cutoffs['crit_mult_cutoff'])
    
    return {
        'damage': damage,
        'crit_roll': crit_roll,
        'miss_roll': miss_roll,
        'luck_roll': luck_roll,
        'expertise_roll': expertise_roll,
        'toughness_roll': toughness_roll,
        'dodge_roll': dodge_roll,
        'parry_roll': parry_roll,
        'fear_roll': fear_roll,
        'heal_roll': heal_roll,
        'aoe_heal_roll': aoe_heal_roll,
        'crit': is_crit,
        'miss': is_miss,
        'weapon': equipped_weapon if equipped_weapon else "Fists",
        'weapon_type': weapon_type,
    }

def get_mob_rolls(mob: object) -> dict:
    """
    Generate all combat rolls for a mob.
    Returns both numeric roll values AND success/fail booleans.
    
    Args:
        mob: Mob object performing the rolls
        
    Returns:
        dict: All roll results (numeric + boolean)
    """
    roll_results = {}
    mob_stats = mob.stats
    
    # Determine dice range based on mob type
    if mob.mob_type == 'minion':
        low = 1
        high = 10
    elif mob.mob_type == 'boss':
        low = 1
        high = 30
    else:  # regular
        low = 1
        high = 20
    
    # Roll all the dice
    crit_roll = acc.multi_roll(low, high)
    miss_roll = acc.multi_roll(mob_stats['low_miss'], mob_stats['high_miss'])
    luck_roll = acc.multi_roll(low, high)
    expertise_roll = acc.multi_roll(low, high)
    toughness_roll = acc.multi_roll(low, high)
    dodge_roll = acc.multi_roll(low, high)
    parry_roll = acc.multi_roll(low, high)
    fear_roll = acc.multi_roll(low, high)
    base_damage = acc.multi_roll(low, high)
    
    # Add expertise to damage
    damage = base_damage + mob_stats.get('expertise', 0)
    
    # Check for crit
    is_crit = crit_roll > mob_stats['crit']
    
    # Apply crit multiplier if crit
    if is_crit:
        damage = int(damage * mob_stats.get('crit_mult', 1.5))
    
    # Store NUMERIC roll values (for combat comparisons)
    roll_results['crit_roll'] = crit_roll
    roll_results['miss_roll'] = miss_roll
    roll_results['luck_roll'] = luck_roll
    roll_results['expertise_roll'] = expertise_roll
    roll_results['toughness_roll'] = toughness_roll
    roll_results['dodge_roll'] = dodge_roll
    roll_results['parry_roll'] = parry_roll
    roll_results['fear_roll'] = fear_roll
    
    # Store final damage (with expertise and crit already applied)
    roll_results['damage'] = damage
    
    # Store SUCCESS/FAIL booleans (for convenience)
    roll_results['crit'] = is_crit
    roll_results['miss'] = miss_roll < 5  # Mobs have fixed miss threshold
    roll_results['luck'] = luck_roll > mob_stats['luck']
    roll_results['expertise'] = expertise_roll > mob_stats['expertise']
    roll_results['toughness'] = toughness_roll > mob_stats['toughness']
    roll_results['dodge'] = dodge_roll > mob_stats['dodge']
    roll_results['parry'] = parry_roll > mob_stats['parry']
    roll_results['fear'] = fear_roll > mob_stats['fear']
    
    return roll_results

def update_health(initial_health : int, delta : int) -> int:
    return initial_health - delta if initial_health - delta > 0 else 0

# ============================================================================
# NEW UTILITY FUNCTIONS
# ============================================================================

def roll_d20():
    """Standard d20 roll."""
    return random.randint(1, 20)

def roll_d100():
    """Percentage roll."""
    return random.randint(1, 100)

# ============================================================================
# FEAR SYSTEM
# ============================================================================

def check_fear(heroine, mob):
    """
    Check if heroine is frightened by mob.
    
    Args:
        heroine: Heroine object with stats
        mob: Mob object with stats
        
    Returns:
        bool: True if heroine is frightened (loses turn)
    """
    mob_scare_roll = roll_d20() + mob.stats['scare']
    heroine_fear_resist = heroine.stats['fear']
    
    if mob_scare_roll > heroine_fear_resist:
        return True
    return False

def fear_flavor_text(heroine, mob):
    """Generate flavor text for fear effects."""
    fear_messages = [
        f"{heroine.name} freezes, eyes wide with terror.",
        f"{heroine.name}'s hands tremble. She can't move.",
        f"{heroine.name} takes a step back, paralyzed by fear.",
        f"{heroine.name} tries to act, but panic overwhelms her.",
        f"{heroine.name}'s courage fails her. She's rooted to the spot.",
    ]
    return random.choice(fear_messages)

# ============================================================================
# DAMAGE TIER SYSTEM
# ============================================================================

def calculate_damage_tier(damage_dealt, max_possible_damage, is_crit, luck_stat):
    """
    Determine damage tier for flavor text.
    
    Tiers:
    1. Glancing blow (< 25% max damage)
    2. Normal hit (25-50%)
    3. Good hit (50-75%)
    4. Critical hit (75-100% OR crit succeeded)
    5. Devastating crit (crit + high damage + luck check)
    
    Args:
        damage_dealt: Actual damage number
        max_possible_damage: Maximum possible damage from this attack
        is_crit: Whether crit roll succeeded
        luck_stat: Attacker's luck stat
        
    Returns:
        str: Tier name ('glancing', 'normal', 'good', 'critical', 'devastating')
    """
    damage_percent = (damage_dealt / max_possible_damage) * 100 if max_possible_damage > 0 else 0
    
    # Devastating crit: crit + high damage + luck check
    if is_crit and damage_percent >= 75 and roll_d20() <= luck_stat:
        return 'devastating'
    
    # Critical hit: crit roll OR very high damage
    if is_crit or damage_percent >= 75:
        return 'critical'
    
    # Good hit
    if damage_percent >= 50:
        return 'good'
    
    # Normal hit
    if damage_percent >= 25:
        return 'normal'
    
    # Glancing blow
    return 'glancing'

# ============================================================================
# FLAVOR TEXT GENERATORS - HEROINE ATTACKING MOB
# ============================================================================

def get_attack_flavor_heroine_to_mob(heroine, mob, damage, tier, weapon_name):
    """
    Generate sarcastic/humorous flavor text for heroine attacking mob.
    
    Args:
        heroine: Attacking heroine object
        mob: Target mob object
        damage: Damage dealt
        tier: Damage tier ('glancing', 'normal', 'good', 'critical', 'devastating')
        weapon_name: Name of weapon used
        
    Returns:
        str: Flavor text description
    """
    
    if tier == 'glancing':
        messages = [
            f"{heroine.heroine_name} swings {weapon_name} with all the grace of a drunken ox.\nIt barely grazes {mob.name}. How embarrassing. ({damage} damage)",
            f"{heroine.heroine_name} pokes {mob.name} with {weapon_name}.\n{mob.name} looks offended. ({damage} damage)",
            f"{heroine.heroine_name}'s attack glances off {mob.name}'s... is that armor or just dirt?\nEither way, not very effective. ({damage} damage)",
            f"{heroine.heroine_name} tries. She really does.\n{weapon_name} tinks harmlessly off {mob.name}. ({damage} damage)",
        ]
    
    elif tier == 'normal':
        messages = [
            f"{heroine.heroine_name} lands a solid hit with {weapon_name}.\nNothing fancy, but it gets the job done. ({damage} damage)",
            f"{heroine.heroine_name} strikes {mob.name} with {weapon_name}.\n{mob.name} grunts. Progress! ({damage} damage)",
            f"{weapon_name} finds its mark on {mob.name}.\n{heroine.heroine_name} nods, satisfied. ({damage} damage)",
            f"{heroine.heroine_name} swings {weapon_name} competently.\nLook at her, being all professional. ({damage} damage)",
        ]
    
    elif tier == 'good':
        messages = [
            f"{heroine.heroine_name}'s {weapon_name} bites deep into {mob.name}!\nBlood spatters across the dungeon floor. ({damage} damage)",
            f"{heroine.heroine_name} strikes true! {weapon_name} tears through {mob.name}'s defenses.\nThat's going to leave a mark. ({damage} damage)",
            f"{weapon_name} slams into {mob.name} with a satisfying CRUNCH.\n{heroine.heroine_name} grins. \"Felt good.\" ({damage} damage)",
            f"{heroine.heroine_name} puts her weight behind {weapon_name}.\nIt carves a bloody path through {mob.name}. ({damage} damage)",
        ]
    
    elif tier == 'critical':
        messages = [
            f"{heroine.heroine_name}'s {weapon_name} finds a vital spot!\n*CRITICAL HIT!*\n{mob.name}'s arm hangs uselessly, blood pouring from the wound. ({damage} damage)",
            f"{weapon_name} cleaves through {mob.name}'s shoulder with a sickening CRUNCH!\n*CRITICAL HIT!*\nBone splinters. Blood fountains. {mob.name} screams. ({damage} damage)",
            f"{heroine.heroine_name} strikes with deadly precision!\n*CRITICAL HIT!*\n{weapon_name} severs something important. {mob.name}'s leg buckles. ({damage} damage)",
            f"A perfect strike! {heroine.heroine_name}'s {weapon_name} carves a gory path through {mob.name}.\n*CRITICAL HIT!*\nIntestines? Maybe. Hard to tell. ({damage} damage)",
        ]
    
    elif tier == 'devastating':
        messages = [
            f"{heroine.heroine_name} channels every ounce of strength into {weapon_name}!\n*DEVASTATING CRITICAL HIT!*\nThe blade nearly BISECTS {mob.name}! Blood and gore explode everywhere.\n{mob.name} looks down at the ruin of their body in disbelief. ({damage} damage)",
            f"Time seems to slow as {heroine.heroine_name} swings {weapon_name}.\n*DEVASTATING CRITICAL HIT!*\n{mob.name}'s arm separates from their body in a spray of crimson.\nIt lands with a wet THUD several feet away. ({damage} damage)",
            f"{heroine.heroine_name} roars and brings {weapon_name} down like the wrath of an angry god!\n*DEVASTATING CRITICAL HIT!*\n{mob.name}'s skull cracks. Their jaw hangs at an impossible angle.\nThey're still standing. Somehow. ({damage} damage)",
            f"A strike for the history books! {heroine.heroine_name}'s {weapon_name} obliterates {mob.name}!\n*DEVASTATING CRITICAL HIT!*\nRibs shatter. Organs rupture. Blood paints the walls.\n\"Overkill much?\" someone mutters. ({damage} damage)",
        ]
    
    else:
        # Fallback
        messages = [f"{heroine.heroine_name} attacks {mob.name} with {weapon_name}. ({damage} damage)"]
    
    return random.choice(messages)

# ============================================================================
# FLAVOR TEXT GENERATORS - MOB ATTACKING HEROINE
# ============================================================================

def get_attack_flavor_mob_to_heroine(mob, heroine, damage, tier, attack_name="attack"):
    """
    Generate descriptive flavor text for mob attacking heroine.
    
    Args:
        mob: Attacking mob object
        heroine: Target heroine object
        damage: Damage dealt
        tier: Damage tier ('glancing', 'normal', 'good', 'critical', 'devastating')
        attack_name: Name of attack (e.g., "claw", "fireball", "bite")
        
    Returns:
        str: Flavor text description
    """
    
    if tier == 'glancing':
        messages = [
            f"{mob.name}'s {attack_name} barely connects with {heroine.heroine_name}.\nShe sidesteps most of it. Lucky. ({damage} damage)",
            f"{heroine.heroine_name} deflects {mob.name}'s {attack_name} at the last second.\nStill hurts though. ({damage} damage)",
            f"{mob.name} swings wildly. The {attack_name} grazes {heroine.heroine_name}'s armor.\n\"Is that all you've got?\" she taunts. ({damage} damage)",
            f"{heroine.heroine_name} takes a glancing blow from {mob.name}'s {attack_name}.\nHer armor absorbs most of it. ({damage} damage)",
        ]
    
    elif tier == 'normal':
        messages = [
            f"{mob.name}'s {attack_name} strikes {heroine.heroine_name} solidly.\nShe grunts, blood welling from the wound. ({damage} damage)",
            f"{heroine.heroine_name} takes a hit from {mob.name}'s {attack_name}.\nPain flashes across her face. She grits her teeth. ({damage} damage)",
            f"{mob.name} lands a solid blow! The {attack_name} cuts into {heroine.heroine_name}.\n\"Ow,\" she says, unhelpfully. ({damage} damage)",
            f"{heroine.heroine_name} staggers as {mob.name}'s {attack_name} finds its mark.\nBlood trickles down her arm. ({damage} damage)",
        ]
    
    elif tier == 'good':
        messages = [
            f"{mob.name}'s {attack_name} SLAMS into {heroine.heroine_name} with brutal force!\nHer armor dents. Ribs crack. She gasps for air. ({damage} damage)",
            f"{heroine.heroine_name} takes a vicious hit from {mob.name}'s {attack_name}!\nBlood sprays as she's knocked backward, barely keeping her footing. ({damage} damage)",
            f"{mob.name}'s {attack_name} tears through {heroine.heroine_name}'s defenses!\nFlesh rips. Blood flows freely. She cries out in pain. ({damage} damage)",
            f"A devastating blow! {mob.name}'s {attack_name} crushes into {heroine.heroine_name}.\nShe doubles over, coughing blood. ({damage} damage)",
        ]
    
    elif tier == 'critical':
        messages = [
            f"{mob.name}'s {attack_name} finds a gap in {heroine.heroine_name}'s armor!\n*CRITICAL HIT!*\nThe strike pierces deep. Blood pours from the wound. She screams. ({damage} damage)",
            f"{heroine.heroine_name} tries to dodge, but {mob.name} is faster!\n*CRITICAL HIT!*\nThe {attack_name} rakes across her chest, shredding flesh and cloth.\nShe crumples, gasping. ({damage} damage)",
            f"{mob.name} strikes with terrifying precision!\n*CRITICAL HIT!*\nThe {attack_name} shatters {heroine.heroine_name}'s shoulder. Bone cracks audibly.\nHer weapon arm hangs limp. ({damage} damage)",
            f"A perfect strike! {mob.name}'s {attack_name} crushes into {heroine.heroine_name}!\n*CRITICAL HIT!*\nShe's thrown backward, blood streaming from multiple wounds.\n\"That... really hurt...\" she whimpers. ({damage} damage)",
        ]
    
    elif tier == 'devastating':
        messages = [
            f"{mob.name} unleashes a BRUTAL {attack_name}!\n*DEVASTATING CRITICAL HIT!*\n{heroine.heroine_name} is hurled through the air like a ragdoll!\nShe hits the wall with a sickening CRACK. Blood pools beneath her.\nShe's not getting up. ({damage} damage)",
            f"Time slows as {mob.name}'s {attack_name} connects with {heroine.heroine_name}!\n*DEVASTATING CRITICAL HIT!*\nHer armor shatters. Ribs splinter. Blood erupts from her mouth.\nShe collapses in a broken heap. ({damage} damage)",
            f"{mob.name} roars and delivers a killing blow!\n*DEVASTATING CRITICAL HIT!*\nThe {attack_name} nearly cleaves {heroine.heroine_name} in two!\nShe drops like a puppet with cut strings, unconscious before she hits the ground. ({damage} damage)",
            f"A strike of absolute carnage! {mob.name}'s {attack_name} obliterates {heroine.heroine_name}!\n*DEVASTATING CRITICAL HIT!*\nBones shatter. Organs rupture. She doesn't even have time to scream.\nShe's down. ({damage} damage)",
        ]
    
    else:
        # Fallback
        messages = [f"{mob.name} hits {heroine.heroine_name} with {attack_name}. ({damage} damage)"]
    
    return random.choice(messages)

# ============================================================================
# SPECIAL MOB BEHAVIORS
# ============================================================================

def get_silent_mob_action(mob, action_type="attack"):
    """
    Generate flavor text for silent/incomprehensible mobs.
    
    Args:
        mob: The silent mob
        action_type: Type of action ('attack', 'move', 'special')
        
    Returns:
        str: Atmospheric description
    """
    
    if action_type == "attack":
        messages = [
            f"{mob.name} advances silently. No sound. No warning.\nJust violence.",
            f"{mob.name} makes no sound as it strikes.\nThe silence is somehow worse than screaming.",
            f"{mob.name} moves with eerie quiet.\nNo battlecry. No threat. Just death.",
        ]
    elif action_type == "move":
        messages = [
            f"{mob.name} shifts position. Silent. Unreadable.",
            f"{mob.name} moves without sound. Its intentions are a mystery.",
            f"The {mob.name} repositions. No one knows what it's thinking.",
        ]
    else:
        messages = [
            f"{mob.name} does... something. Hard to say what.",
            f"The {mob.name} acts. Your guess is as good as anyone's.",
        ]
    
    return random.choice(messages)

def get_foreign_language_mob_speech(mob, context="attack"):
    """
    Generate incomprehensible foreign language speech from mobs.
    Heroines react based on body language and context.
    
    Args:
        mob: The speaking mob
        context: Situation context ('attack', 'angry', 'wounded', 'victory')
        
    Returns:
        tuple: (mob speech, heroine reaction template)
    """
    
    if context == "attack":
        speeches = [
            "K'THAK SHRII VENNA!",
            "GRAK'TAR MOSH!",
            "ZUL'THAX KREE!",
            "VOSH'NAK TERRA!",
        ]
        reactions = [
            "\"I think it just insulted my mother?\" {heroine} mutters.",
            "{heroine} narrows her eyes. \"That sounded aggressive.\"",
            "\"No idea what that means, but I don't like the tone,\" {heroine} says.",
            "{heroine} shrugs. \"Angry gibberish. Got it.\"",
        ]
    
    elif context == "angry":
        speeches = [
            "SHRAK'TAL VOSS KREEN!",
            "MAL'GORATH THUN!",
            "KRESH'VA DOOM!",
        ]
        reactions = [
            "{heroine} winces. \"Yeah, that one's definitely mad.\"",
            "\"I don't speak whatever that is, but it sounds upset,\" {heroine} observes.",
            "{heroine} takes a defensive stance. \"Angry noises are never good.\"",
        ]
    
    elif context == "wounded":
        speeches = [
            "Greth... nak... vosh...",
            "K'ree... shaal...",
            "Mosh... thara...",
        ]
        reactions = [
            "\"Is it... dying? Or cursing us? Both?\" {heroine} wonders.",
            "{heroine} frowns. \"That sounded pained. Good.\"",
            "\"Keep hitting it. Whatever it's saying, I don't care,\" {heroine} says coldly.",
        ]
    
    elif context == "victory":
        speeches = [
            "KRESH VALLA THOOM!",
            "GRAK'TAR SHEEN!",
            "MAL'GOTH REEN!",
        ]
        reactions = [
            "{heroine} scowls. \"I think it's... celebrating? Rude.\"",
            "\"Did it just laugh at us?\" {heroine} growls.",
            "{heroine} glares. \"Whatever it said, we're making it regret that.\"",
        ]
    
    else:
        speeches = ["Vosh kree tal."]
        reactions = ["{heroine} shrugs. \"No clue.\""]
    
    speech = random.choice(speeches)
    reaction_template = random.choice(reactions)
    
    return speech, reaction_template

# ============================================================================
# INITIATIVE / ROUND ORDER SYSTEM
# ============================================================================

def calculate_initiative(combatants, surprise_factor=0):
    """
    Calculate turn order based on speed + random roll + surprise.
    
    Args:
        combatants: List of all combatants (heroes and mobs)
        surprise_factor: Modifier for surprise (-5 to +5, applied to one side)
        
    Returns:
        list: Sorted list of combatants by initiative (highest first)
    """
    initiative_rolls = []
    
    for combatant in combatants:
        # Base initiative = speed stat + d20 roll
        base_roll = combatant.stats['speed'] + roll_d20()
        
        # Apply surprise factor if applicable
        # (You'll set this per encounter - positive favors heroes, negative favors mobs)
        initiative_score = base_roll + surprise_factor
        
        initiative_rolls.append({
            'combatant': combatant,
            'initiative': initiative_score,
            'name': combatant.name if hasattr(combatant, 'name') else combatant.heroine_name
        })
    
    # Sort by initiative (highest goes first)
    initiative_rolls.sort(key=lambda x: x['initiative'], reverse=True)
    
    return initiative_rolls

def display_initiative_order(initiative_list):
    """
    Display the turn order to player.
    
    Args:
        initiative_list: Sorted initiative list from calculate_initiative()
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}ROUND ORDER:")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    for i, entry in enumerate(initiative_list, 1):
        combatant = entry['combatant']
        initiative = entry['initiative']
        
        # Color code: Green for heroes, Red for mobs
        if hasattr(combatant, 'hero_class'):  # It's a hero
            color = Fore.GREEN
            type_label = f"[{combatant.hero_class}]"
            name = combatant.heroine_name
        else:  # It's a mob
            color = Fore.RED
            type_label = f"[{combatant.mob_class}]"
            name = combatant.name
        
        print(f"{color}{i}. {name} {type_label} - Initiative: {initiative}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

# ============================================================================
# COMBAT STATUS DISPLAY (ENHANCED VERSION)
# ============================================================================

def display_combat_status(heroes, mobs):
    """
    Show current HP and status of all combatants.
    
    Args:
        heroes: List of hero objects
        mobs: List of mob objects
    """
    print(f"\n{Fore.YELLOW}{'='*60}")
    print(f"{Fore.YELLOW}COMBAT STATUS:")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    # Display Heroes
    print(f"{Fore.GREEN}HEROES:{Style.RESET_ALL}")
    for hero in heroes:
        if hero.health > 0:
            hp_percent = (hero.health / hero.starting_health) * 100
            
            # Color code HP bar
            if hp_percent > 60:
                hp_color = Fore.GREEN
            elif hp_percent > 30:
                hp_color = Fore.YELLOW
            else:
                hp_color = Fore.RED
            
            print(f"  {hero.heroine_name} [{hero.hero_class}]: {hp_color}{int(hero.health)}/{hero.starting_health} HP{Style.RESET_ALL}")
        else:
            print(f"  {hero.heroine_name} [{hero.hero_class}]: {Fore.RED}UNCONSCIOUS{Style.RESET_ALL}")
    
    # Display Mobs
    print(f"\n{Fore.RED}ENEMIES:{Style.RESET_ALL}")
    for mob in mobs:
        if mob.health > 0:
            hp_percent = (mob.health / mob.starting_health) * 100
            
            # Color code HP bar
            if hp_percent > 60:
                hp_color = Fore.GREEN
            elif hp_percent > 30:
                hp_color = Fore.YELLOW
            else:
                hp_color = Fore.RED
            
            status = ""
            if hasattr(mob, 'enraged') and mob.enraged:
                status = f" {Fore.MAGENTA}[ENRAGED!]{Style.RESET_ALL}"
            
            print(f"  {mob.name} [{mob.mob_class}]: {hp_color}{int(mob.health)}/{mob.starting_health} HP{Style.RESET_ALL}{status}")
        else:
            print(f"  {mob.name} [{mob.mob_class}]: {Fore.RED}DEFEATED{Style.RESET_ALL}")
    
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")

# ============================================================================
# HAPPY'S RESURRECTION SCENE
# ============================================================================

def happy_resurrection_scene(heroes):
    """
    Happy's emotional breakdown and resurrection of the party.
    Purple haze, lightning, tears, and rewards!
    
    Args:
        heroes: List of all hero objects (all unconscious)
    """
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}SOMETHING UNEXPECTED HAPPENS...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy stands over the fallen heroines, his massive warhammer dripping with blood.")
    print(f"The dungeon is silent except for his heavy breathing.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}He looks down at the bodies. His shoulders slump.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "...not again."{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "I\'m so... so tired of this."{Style.RESET_ALL}')
    print(f"{Fore.CYAN}His voice cracks. The fierce dwarf warrior begins to tremble.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "Every day. EVERY. DAMN. DAY. He makes me do this!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "\'Guard the dungeon, Happy.\' \'Kill the intruders, Happy.\'"')
    print(f'{Fore.YELLOW}Happy: "I didn\'t ask for this! I just wanted to mine some bloody ore!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}A single tear rolls down Happy's blood-splattered cheek.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Then another.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Then he's openly weeping.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy (sobbing): "I\'m sorry! I\'m so, so sorry!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "You seem like nice lasses! You don\'t deserve this!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "None of them do! But what choice do I have?!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy wipes his eyes with a meaty fist and raises his hands.{Style.RESET_ALL}")
    print(f'{Fore.CYAN}He begins chanting in ancient Dwarvish.{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.MAGENTA}A purple haze begins to swirl around each fallen heroine.{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Crackling energy fills the air. Small lightning bolts dance across their bodies.{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}The smell of ozone and magic permeates the dungeon.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.MAGENTA}*CRACK* *FZZZT* *BOOM*{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.GREEN}Wounds close. Bones mend. Color returns to pale faces.{Style.RESET_ALL}")
    print(f"{Fore.GREEN}One by one, the heroines gasp back to life!{Style.RESET_ALL}\n")
    
    # Resurrect all heroes to full HP
    for hero in heroes:
        hero.health = hero.starting_health
        print(f"{Fore.GREEN}{hero.heroine_name} opens her eyes, fully healed!{Style.RESET_ALL}")
    
    input("\nPress Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy (sniffling): "There. Good as new."{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "Now get out of here before HE notices I did that."{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy's demeanor suddenly shifts. The tears stop.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}A genuine smile spreads across his face.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "You know what? You lasses fought well!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "Better than most! Here, take these. You\'ve earned them!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy tosses each heroine a small pouch of coins and some equipment.{Style.RESET_ALL}")
    print(f'{Fore.CYAN}He winks.{Style.RESET_ALL}\n')
    
    print(f'\n{Fore.YELLOW}Happy: "Next time, hit me harder! Maybe you\'ll actually win!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "Now scram! And remember - you didn\'t see me cry!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}RESURRECTION COMPLETE!{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}All heroines restored to full health!{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")

# ============================================================================
# POST-COMBAT REWARDS
# ============================================================================

def apply_stat_increases(heroes):
    """
    Apply random stat increases to heroines after Happy's resurrection.
    Each heroine gets 1-3 random stat improvements, weighted toward their class specialty.
    
    Args:
        heroes: List of hero objects
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}HAPPY'S GIFTS - STAT INCREASES!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    stat_categories = {
        'Warrior': ['toughness', 'parry', 'crit', 'expertise'],
        'Shifter': ['dodge', 'speed', 'crit', 'luck'],
        'Battle_Mage': ['expertise', 'luck', 'crit_mult', 'toughness'],
        'Hunter': ['crit', 'crit_mult', 'dodge', 'speed'],
        'Wizard': ['expertise', 'luck', 'crit_mult', 'toughness'],
        'Sapper': ['expertise', 'crit', 'dodge', 'luck'],
        'Cleric': ['heal', 'aoe_heal', 'toughness', 'fear'],
    }
    
    for hero in heroes:
        num_increases = random.randint(1, 3)
        hero_class = hero.hero_class
        
        print(f"{Fore.GREEN}{hero.heroine_name} receives {num_increases} stat improvement(s):{Style.RESET_ALL}")
        
        # Get weighted stat pool for this class
        preferred_stats = stat_categories.get(hero_class, ['luck', 'toughness', 'dodge', 'fear'])
        
        for i in range(num_increases):
            # 70% chance to improve class specialty, 30% chance any stat
            if random.randint(1, 100) <= 70:
                stat_to_increase = random.choice(preferred_stats)
            else:
                # Any stat
                all_stats = ['crit', 'crit_mult', 'luck', 'expertise', 'toughness', 
                            'dodge', 'parry', 'fear', 'speed']
                stat_to_increase = random.choice(all_stats)
            
            # Determine increase amount based on stat type
            if stat_to_increase == 'crit_mult':
                increase = round(random.uniform(0.05, 0.15), 2)
            elif stat_to_increase in ['heal', 'aoe_heal']:
                increase = random.randint(1, 3)
            else:
                increase = random.randint(1, 2)
            
            # Apply the increase
            old_value = hero.stats[stat_to_increase]
            hero.stats[stat_to_increase] += increase
            new_value = hero.stats[stat_to_increase]
            
            print(f"  • {stat_to_increase}: {old_value} → {Fore.YELLOW}{new_value}{Style.RESET_ALL} (+{increase})")
        
        print()
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    input("Press Enter to continue...")

def apply_loot_rewards(heroes):
    """
    Give gold/items to heroines after Happy's resurrection.
    
    Args:
        heroes: List of hero objects
    """
    print(f"\n{Fore.YELLOW}{'='*60}")
    print(f"{Fore.YELLOW}HAPPY'S GIFTS - LOOT!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")
    
    for hero in heroes:
        gold_reward = random.randint(50, 150)
        hero.gold += gold_reward
        
        print(f"{Fore.GREEN}{hero.heroine_name} receives {Fore.YELLOW}{gold_reward} gold!{Style.RESET_ALL}")
        print(f"  Total gold: {Fore.YELLOW}{hero.gold}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")
    input("Press Enter to continue...")

# ============================================================================
# COMBAT VICTORY/DEFEAT CHECKS
# ============================================================================

def check_party_wipe(heroes):
    """
    Check if all heroines are unconscious.
    
    Args:
        heroes: List of hero objects
        
    Returns:
        bool: True if all heroes are at 0 HP
    """
    return all(hero.health <= 0 for hero in heroes)

def check_mob_defeat(mobs):
    """
    Check if all mobs are defeated.
    
    Args:
        mobs: List of mob objects
        
    Returns:
        bool: True if all mobs are at 0 HP
    """
    return all(mob.health <= 0 for mob in mobs)

def check_happy_enrage(happy_mob):
    """
    Check if Happy should enter enraged state.
    
    Args:
        happy_mob: The Happy mob object
        
    Returns:
        bool: True if Happy should enrage
    """
    if hasattr(happy_mob, 'enraged') and happy_mob.enraged:
        return False  # Already enraged
    
    # Enrage at 50% HP
    hp_percent = (happy_mob.health / happy_mob.starting_health) * 100
    
    if hp_percent <= 50:
        return True
    
    return False

def trigger_happy_enrage(happy_mob):
    """
    Trigger Happy's enrage transformation.
    Updates stats to enraged values.
    
    Args:
        happy_mob: The Happy mob object
    """
    print(f"\n{Fore.RED}{'='*60}")
    print(f"{Fore.RED}{'='*60}")
    print(f"{Fore.RED}SOMETHING TERRIBLE IS HAPPENING...{Style.RESET_ALL}")
    print(f"{Fore.RED}{'='*60}")
    print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy staggers backward, clutching his wounds.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Blood drips from dozens of cuts.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "Ow. OW. That... that actually hurt."{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}His breathing becomes ragged. His eyes begin to glow red.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.RED}Happy: "You know what? I\'m TIRED of holding back!"{Style.RESET_ALL}')
    print(f'{Fore.RED}Happy: "I\'m TIRED of being nice!"{Style.RESET_ALL}')
    print(f'{Fore.RED}Happy: "I\'m TIRED OF THIS JOB!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.RED}Happy throws his head back and ROARS!{Style.RESET_ALL}")
    print(f"{Fore.RED}The entire dungeon shakes!{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.MAGENTA}Dark energy erupts from Happy's body!{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}His muscles bulge. His wounds close. His warhammer crackles with power!{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.RED}Happy (voice distorted): "LET\'S SEE HOW YOU HANDLE THIS!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    # Apply enraged stats
    happy_mob.enraged = True
    happy_mob.starting_health = happy_mob.stats['enraged_hp']
    happy_mob.health = happy_mob.stats['enraged_hp']  # Full heal on enrage
    
    # Update combat stats to enraged versions
    happy_mob.stats['turn'] = happy_mob.stats['enraged_turn']
    happy_mob.stats['crit'] = happy_mob.stats['enraged_crit']
    happy_mob.stats['crit_chance'] = happy_mob.stats['enraged_crit_chance']
    happy_mob.stats['miss'] = happy_mob.stats['enraged_miss']
    happy_mob.stats['luck'] = happy_mob.stats['enraged_luck']
    happy_mob.stats['expertise'] = happy_mob.stats['enraged_expertise']
    happy_mob.stats['toughness'] = happy_mob.stats['enraged_toughness']
    happy_mob.stats['dodge'] = happy_mob.stats['enraged_dodge']
    happy_mob.stats['healing_chance'] = happy_mob.stats['enraged_healing_chance']
    happy_mob.stats['healing'] = happy_mob.stats['enraged_healing']
    happy_mob.stats['scare'] = happy_mob.stats['enraged_scare']
    
    print(f"\n{Fore.RED}{'='*60}")
    print(f"{Fore.RED}HAPPY HAS ENTERED ENRAGED MODE!{Style.RESET_ALL}")
    print(f"{Fore.RED}HP: {happy_mob.health}/{happy_mob.starting_health}{Style.RESET_ALL}")
    print(f"{Fore.RED}All stats dramatically increased!{Style.RESET_ALL}")
    print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")

# ============================================================================
# HEROINE REACTION TO FOREIGN SPEECH (HELPER)
# ============================================================================

def display_foreign_speech_with_reaction(mob, context, random_heroine):
    """
    Display mob's foreign speech and a heroine's confused reaction.
    
    Args:
        mob: The speaking mob
        context: Speech context ('attack', 'angry', 'wounded', 'victory')
        random_heroine: A random heroine from the party to react
    """
    speech, reaction_template = get_foreign_language_mob_speech(mob, context)
    
    print(f"\n{Fore.RED}{mob.name}: \"{speech}\"{Style.RESET_ALL}")
    
    reaction = reaction_template.format(heroine=random_heroine.heroine_name)
    print(f"{Fore.CYAN}{reaction}{Style.RESET_ALL}\n")

# ============================================================================
# DODGE/PARRY FLAVOR TEXT
# ============================================================================

def get_dodge_flavor(heroine, mob):
    """Generate flavor text for successful dodge."""
    messages = [
        f"{heroine.heroine_name} twists aside at the last second! {mob.name}'s attack misses completely.",
        f"{heroine.heroine_name} ducks under {mob.name}'s swing with a grin. \"Too slow!\"",
        f"{mob.name} lunges, but {heroine.heroine_name} sidesteps gracefully. \"Missed me!\"",
        f"{heroine.heroine_name} rolls out of the way. {mob.name}'s attack hits nothing but air.",
    ]
    return random.choice(messages)

def get_parry_flavor(heroine, mob):
    """Generate flavor text for successful parry."""
    messages = [
        f"{heroine.heroine_name} deflects {mob.name}'s attack with her weapon! Sparks fly!",
        f"CLANG! {heroine.heroine_name} parries {mob.name}'s strike perfectly.",
        f"{heroine.heroine_name} blocks {mob.name}'s attack and counters with a shove. \"Not today!\"",
        f"{mob.name}'s weapon bounces off {heroine.heroine_name}'s guard. She smirks.",
    ]
    return random.choice(messages)

def get_miss_flavor(attacker, defender, weapon_type='melee'):
    """
    Get flavor text for a missed attack.
    
    Args:
        attacker: Attacking character
        defender: Defending character
        weapon_type: Type of weapon ('melee', 'range', etc.)
        
    Returns:
        str: Flavor text
    """
    import random
    
    attacker_name = attacker.heroine_name if hasattr(attacker, 'heroine_name') else attacker.name
    defender_name = defender.name if hasattr(defender, 'name') else defender.heroine_name
    
    if 'range' in weapon_type.lower():
        # Ranged miss flavors
        flavors = [
            f"{attacker_name}'s shot misses {defender_name} completely!",
            f"{defender_name} dodges {attacker_name}'s projectile!",
            f"{attacker_name}'s aim is off - the shot goes wide!",
            f"{attacker_name} fires, but {defender_name} sidesteps!",
            f"The projectile whizzes past {defender_name}'s head!",
        ]
    else:
        # Melee miss flavors
        flavors = [
            f"{attacker_name}'s attack misses {defender_name} completely!",
            f"{defender_name} dodges {attacker_name}'s strike!",
            f"{defender_name} parries {attacker_name}'s attack!",
            f"{attacker_name} swings wide, missing {defender_name}!",
            f"{defender_name} sidesteps {attacker_name}'s attack!",
        ]
    
    return random.choice(flavors)

# ============================================================================
# HEALING FLAVOR TEXT
# ============================================================================

def get_healing_flavor(healer, target, amount):
    """
    Generate flavor text for healing actions.
    
    Args:
        healer: The one doing the healing (heroine or mob)
        target: The one being healed
        amount: HP restored
        
    Returns:
        str: Healing flavor text
    """
    if hasattr(healer, 'hero_class'):  # Heroine healing
        messages = [
            f"{healer.heroine_name} channels healing magic into {target.heroine_name}!\nWounds close. Strength returns. (+{amount} HP)",
            f"{healer.heroine_name} mutters a prayer. Golden light surrounds {target.heroine_name}.\nFlesh mends. Pain fades. (+{amount} HP)",
            f"{healer.heroine_name} places her hands on {target.heroine_name}.\nWarm energy flows. Injuries heal. (+{amount} HP)",
        ]
    else:  # Mob healing
        messages = [
            f"{healer.name} growls and regenerates! Wounds seal with sickening speed. (+{amount} HP)",
            f"Dark energy swirls around {healer.name}. Flesh knits back together. (+{amount} HP)",
            f"{healer.name} channels unholy power! Injuries close with a wet, squelching sound. (+{amount} HP)",
        ]
    
    return random.choice(messages)

def get_aoe_healing_flavor(healer, targets, amount):
    """
    Generate flavor text for area-of-effect healing.
    
    Args:
        healer: The heroine doing the healing
        targets: List of heroines being healed
        amount: HP restored to each
        
    Returns:
        str: AOE healing flavor text
    """
    messages = [
        f"{healer.heroine_name} raises her hands and shouts a prayer!\nRadiant light explodes outward, washing over the entire party!\nWounds close. Strength returns to all! (+{amount} HP to all)",
        f"{healer.heroine_name} slams her staff into the ground!\nA wave of golden energy ripples through the party!\nEveryone feels their injuries healing! (+{amount} HP to all)",
        f"{healer.heroine_name} channels divine power!\nA warm glow envelops each heroine!\nPain fades. Hope returns! (+{amount} HP to all)",
    ]
    
    return random.choice(messages)

# ============================================================================
# PLAYER ACTION SYSTEM
# ============================================================================

def display_mob_status_compact(mobs):
    """
    Display compact mob status at top of action menu.
    
    Args:
        mobs: List of all mobs (including defeated)
    """
    print(f"\n{Fore.RED}ENEMIES:{Style.RESET_ALL}")
    
    for mob in mobs:
        if mob.health > 0:
            hp_percent = (mob.health / mob.starting_health) * 100
            
            # Color code HP
            if hp_percent > 66:
                hp_color = Fore.GREEN
            elif hp_percent > 33:
                hp_color = Fore.YELLOW
            else:
                hp_color = Fore.RED
            
            # Status effects
            status = ""
            if hasattr(mob, 'enraged') and mob.enraged:
                status += f" {Fore.MAGENTA}[ENRAGED]{Style.RESET_ALL}"
            if hasattr(mob, 'creature_type') and mob.creature_type == 'undead':
                status += f" {Fore.CYAN}[UNDEAD]{Style.RESET_ALL}"
            if hasattr(mob, 'phase'):
                status += f" {Fore.YELLOW}[PHASE {mob.phase}]{Style.RESET_ALL}"
            
            print(f"  • {mob.name}: {hp_color}{mob.health}/{mob.starting_health} HP{Style.RESET_ALL}{status}")
        else:
            print(f"  • {mob.name}: {Fore.RED}DEFEATED{Style.RESET_ALL}")
    
    print()

def display_action_menu(hero, mobs):
    """
    Display available actions for a hero's turn.
    
    Args:
        hero: The hero taking their turn
        mobs: List of available enemy targets
        
    Returns:
        None (displays menu)
    """
    # Show mob status first
    display_mob_status_compact(mobs)
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{hero.heroine_name.upper()}'S TURN [{hero.hero_class}]")
    print(f"HP: {hero.health}/{hero.starting_health}")
    
    # Show abilities if any
    abilities = hero.get_all_abilities()
    if abilities:
        print(f"Abilities: {', '.join(abilities)}")
    
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Choose Action:{Style.RESET_ALL}")
    
    # Clerics can't attack living!
    if hero.hero_class == 'Cleric':
        print(f"  {Fore.RED}1. Attack - FORBIDDEN! Clerics cannot harm the living!{Style.RESET_ALL}")
    else:
        print(f"  1. Attack (Choose target)")
    
    print(f"  2. Defend (Increase dodge/parry this turn)")
    print(f"  3. Special Ability")
    print(f"  4. Use Item (Not implemented yet)")
    print()

def get_player_action_choice():
    """
    Get player's action choice.
    
    Returns:
        int: Action choice (1-4) or None if invalid
    """
    while True:
        try:
            choice = input(f"{Fore.GREEN}Enter choice (1-4): {Style.RESET_ALL}").strip()
            
            if not choice:
                continue
            
            choice_num = int(choice)
            
            if choice_num < 1 or choice_num > 4:
                print(f"{Fore.RED}Please enter a number between 1 and 4.{Style.RESET_ALL}")
                continue
            
            return choice_num
            
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            continue

def display_weapon_menu(hero):
    """
    Display available weapons for hero to choose from.
    
    Args:
        hero: The hero choosing a weapon
        
    Returns:
        None (displays menu)
    """
    import pandas as pd
    
    # Load items
    try:
        items = pd.read_csv('supporting_docs/items.csv')
    except FileNotFoundError:
        print(f"{Fore.RED}No items.csv found! Using fists.{Style.RESET_ALL}")
        return None
    
    # Find all weapons in inventory
    weapons = []
    
    if hasattr(hero, 'inv') and hero.inv:
        for item_name in hero.inv:
            item_row = items[items['item'] == item_name]
            if not item_row.empty:
                attack_type = item_row['attack_type'].values[0]
                # Check if it's a weapon
                if attack_type in ['melee', 'range', 'both', 'special_melee', 'special_range', 'special_both']:
                    weapons.append({
                        'name': item_name,
                        'type': attack_type,
                        'damage_low': int(item_row['damage_range_low'].values[0]),
                        'damage_high': int(item_row['damage_range_high'].values[0]),
                    })
    
    if not weapons:
        print(f"{Fore.YELLOW}No weapons equipped. Using fists (1-4 damage).{Style.RESET_ALL}\n")
        return None
    
    print(f"\n{Fore.YELLOW}Choose Weapon:{Style.RESET_ALL}")
    
    for i, weapon in enumerate(weapons, 1):
        dmg_range = f"{weapon['damage_low']}-{weapon['damage_high']}"
        weapon_type = weapon['type'].replace('_', ' ').title()
        print(f"  {i}. {weapon['name']} [{weapon_type}] (Damage: {dmg_range})")
    
    print(f"  0. Fists (1-4 damage)")
    print()
    
    return weapons

def get_weapon_choice(hero, weapons):
    """
    Get player's weapon choice.
    
    Args:
        hero: The hero choosing
        weapons: List of available weapons
        
    Returns:
        str: Weapon name, or "Fists" if none chosen
    """
    if not weapons:
        return "Fists"
    
    while True:
        try:
            choice = input(f"{Fore.GREEN}Enter weapon (0-{len(weapons)}): {Style.RESET_ALL}").strip()
            
            if not choice:
                continue
            
            choice_num = int(choice)
            
            if choice_num == 0:
                return "Fists"
            
            if choice_num < 0 or choice_num > len(weapons):
                print(f"{Fore.RED}Please enter a number between 0 and {len(weapons)}.{Style.RESET_ALL}")
                continue
            
            return weapons[choice_num - 1]['name']
            
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            continue

def display_target_menu(mobs):
    """
    Display available enemy targets with color-coded HP.
    
    Args:
        mobs: List of mob objects
        
    Returns:
        None (displays menu)
    """
    print(f"\n{Fore.YELLOW}Choose Target:{Style.RESET_ALL}")
    
    for i, mob in enumerate(mobs, 1):
        hp_percent = (mob.health / mob.starting_health) * 100
        
        # Determine HP color
        if hp_percent > 66:
            hp_color = Style.RESET_ALL  # White (default)
        elif hp_percent > 33:
            hp_color = Fore.YELLOW
        else:
            hp_color = Fore.RED
        
        # Check for enraged status
        status = ""
        if hasattr(mob, 'enraged') and mob.enraged:
            status = f" {Fore.RED}[ENRAGED!]{Style.RESET_ALL}"
        
        print(f"  {i}. {mob.name} [{hp_color}HP: {mob.health}/{mob.starting_health}{Style.RESET_ALL}]{status}")
    
    print()

def get_target_choice(mobs):
    """
    Get player's target choice.
    
    Args:
        mobs: List of available targets
        
    Returns:
        Mob object or None if invalid
    """
    while True:
        try:
            choice = input(f"{Fore.GREEN}Enter target (1-{len(mobs)}): {Style.RESET_ALL}").strip()
            
            if not choice:
                continue
            
            choice_num = int(choice)
            
            if choice_num < 1 or choice_num > len(mobs):
                print(f"{Fore.RED}Please enter a number between 1 and {len(mobs)}.{Style.RESET_ALL}")
                continue
            
            return mobs[choice_num - 1]
            
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            continue

def display_ability_menu(hero):
    """
    Display available special abilities.
    
    Args:
        hero: The hero choosing an ability
        
    Returns:
        None (displays menu)
    """
    abilities = hero.get_all_abilities()
    
    print(f"\n{Fore.YELLOW}Available Abilities:{Style.RESET_ALL}")
    
    for i, ability in enumerate(abilities, 1):
        # Check if on cooldown
        can_use, reason = hero.can_use_ability(ability)
        
        status = ""
        if not can_use:
            status = f" {Fore.RED}[{reason}]{Style.RESET_ALL}"
        
        # Get ability description
        description = get_ability_description(ability)
        
        print(f"  {i}. {ability} - {description}{status}")
    
    print(f"  0. Cancel")
    print()

def get_ability_description(ability_name):
    """
    Get description text for an ability.
    
    Args:
        ability_name: Name of the ability
        
    Returns:
        str: Description text
    """
    descriptions = {
        'Power Strike': '2x damage, -5 accuracy',
        'Heal': 'Restore HP to an ally',
        'AOE Heal': 'Restore HP to entire party',
    }
    
    return descriptions.get(ability_name, 'Unknown ability')

def get_ability_choice(hero):
    """
    Get player's ability choice.
    
    Args:
        hero: The hero choosing an ability
        
    Returns:
        str: Ability name, or None if cancelled
    """
    abilities = hero.get_all_abilities()
    
    while True:
        try:
            choice = input(f"{Fore.GREEN}Enter ability (0-{len(abilities)}): {Style.RESET_ALL}").strip()
            
            if not choice:
                continue
            
            choice_num = int(choice)
            
            if choice_num == 0:
                return None  # Cancelled
            
            if choice_num < 0 or choice_num > len(abilities):
                print(f"{Fore.RED}Please enter a number between 0 and {len(abilities)}.{Style.RESET_ALL}")
                continue
            
            ability = abilities[choice_num - 1]
            
            # Check if can use
            can_use, reason = hero.can_use_ability(ability)
            if not can_use:
                print(f"{Fore.RED}{reason}{Style.RESET_ALL}")
                continue
            
            return ability
            
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            continue

# ============================================================================
# ABILITY EXECUTION FUNCTIONS
# ============================================================================

def execute_ability(hero, ability_name, target, all_heroes, all_mobs):
    """
    Execute a special ability.
    
    Args:
        hero: The hero using the ability
        ability_name: Name of ability to use
        target: Target of ability (can be hero or mob)
        all_heroes: List of all heroes (for AOE heals)
        all_mobs: List of all mobs (for AOE attacks later)
        
    Returns:
        bool: True if ability was executed successfully
    """
    # Route to appropriate ability function
    if ability_name == 'Power Strike':
        return execute_power_strike(hero, target)
    elif ability_name == 'Heal':
        return execute_heal(hero, target)
    elif ability_name == 'AOE Heal':
        return execute_aoe_heal(hero, all_heroes)
    else:
        print(f"{Fore.RED}Unknown ability: {ability_name}{Style.RESET_ALL}")
        return False

def execute_power_strike(hero, target, chosen_weapon=None):
    """
    Execute Power Strike ability.
    2x damage, -10 accuracy penalty (was -5, now harder to hit)
    
    Args:
        hero: Attacking hero
        target: Target mob
        chosen_weapon: Weapon to use (optional)
        
    Returns:
        bool: True if executed
    """
    print(f"\n{Fore.YELLOW}⚔️  {hero.heroine_name} winds up for a POWER STRIKE! ⚔️{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Get hero's attack rolls
    hero_rolls = get_heroine_rolls(hero, chosen_weapon=chosen_weapon)
    
    # Apply -10 accuracy penalty to expertise roll (INCREASED from -5)
    hit_roll = hero_rolls['expertise_roll'] - 10
    
    # Get target's defense rolls
    target_rolls = get_mob_rolls(target)
    
    # Check for automatic miss
    if hero_rolls['miss']:
        miss_flavor = get_miss_flavor(hero, target, hero_rolls.get('weapon_type', 'melee'))
        print(f"{Fore.CYAN}{miss_flavor}{Style.RESET_ALL}")
        time.sleep(0.5)
        return True
    
    # Check if attack hits (must beat both dodge and parry)
    if not check_hit(hit_roll, target_rolls['dodge_roll'], target_rolls['parry_roll']):
        miss_flavor = get_miss_flavor(hero, target, hero_rolls.get('weapon_type', 'melee'))
        print(f"{Fore.CYAN}{miss_flavor}{Style.RESET_ALL}")
        time.sleep(0.5)
        return True
    
    # Damage is already calculated with expertise and crit in get_heroine_rolls
    # Just apply the 2x Power Strike multiplier
    base_damage = hero_rolls['damage']
    damage = int(base_damage * 2)
    
    # Cap damage to remaining HP
    actual_damage = min(damage, target.health)
    
    # Apply damage
    target.health -= damage
    
    # Flavor text
    if hero_rolls['crit']:
        print(f"{Fore.RED}💥 CRITICAL POWER STRIKE! 💥{Style.RESET_ALL}")
    
    hit_flavor = get_hit_flavor(hero, target, actual_damage, hero_rolls['crit'], hero_rolls.get('weapon_type', 'melee'))
    print(f"{Fore.GREEN}{hit_flavor}{Style.RESET_ALL}")
    time.sleep(0.5)
    
    if target.health <= 0:
        print(f"{Fore.YELLOW}☠️  {target.name} has been defeated! ☠️{Style.RESET_ALL}")
        time.sleep(0.5)
        
        # CHECK FOR BOSS RESURRECTION!
        if check_boss_resurrection(target):
            print(f"\n{Fore.RED}⚔️  The battle is NOT over! ⚔️{Style.RESET_ALL}\n")
            time.sleep(1)
    
    return True

def execute_heal(hero, target):
    """
    Execute Heal ability.
    Restores HP to a single target.
    Can accidentally heal living enemies! (But damages undead)
    
    Args:
        hero: Hero casting heal
        target: Target to heal (hero OR mob)
        
    Returns:
        bool: True if executed
    """
    # Check if target is a MOB
    is_mob = hasattr(target, 'mob_class')
    
    if is_mob:
        # Healing a mob!
        if target.creature_type == 'undead':
            # Undead - this will damage them!
            return execute_heal_on_undead(hero, target)
        else:
            # Living mob - ACCIDENTALLY HEAL THEM!
            print(f"\n{Fore.RED}⚠️  OH NO! ⚠️{Style.RESET_ALL}")
            print(f"{Fore.RED}{hero.heroine_name} accidentally heals {target.name}!{Style.RESET_ALL}\n")
            time.sleep(1)
            
            # Get hero's heal roll
            hero_rolls = get_heroine_rolls(hero)
            heal_roll = hero_rolls['heal_roll']
            
            # Add heal stat
            total_heal = heal_roll + hero.stats.get('heal', 0)
            
            # Apply healing to enemy
            old_health = target.health
            target.health = min(target.health + total_heal, target.starting_health)
            actual_heal = target.health - old_health
            
            # Sarcastic flavor text
            oops_messages = [
                f"{Fore.YELLOW}\"Oops.\" {hero.heroine_name} says sheepishly.{Style.RESET_ALL}",
                f"{Fore.YELLOW}\"That... wasn't supposed to happen,\" {hero.heroine_name} mutters.{Style.RESET_ALL}",
                f"{Fore.YELLOW}\"MY BAD!\" {hero.heroine_name} shouts.{Style.RESET_ALL}",
                f"{Fore.YELLOW}The party stares at {hero.heroine_name} in disbelief.{Style.RESET_ALL}",
                f"{Fore.YELLOW}\"Whose side are you ON?!\" someone yells at {hero.heroine_name}.{Style.RESET_ALL}",
            ]
            
            print(f"{Fore.GREEN}{target.name} recovers {actual_heal} HP!{Style.RESET_ALL}")
            print(random.choice(oops_messages))
            print(f"{Fore.CYAN}{target.name} looks confused but grateful.{Style.RESET_ALL}\n")
            time.sleep(2)
            
            return True
    
    # Healing an ally (normal behavior)
    
    # Check if target is at full health
    if target.health >= target.starting_health:
        print(f"\n{Fore.YELLOW}⚠️  {target.heroine_name} is at FULL HEALTH.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Are you SURE you want to waste a turn on this? That's pretty idiotic...{Style.RESET_ALL}\n")
        
        confirm = input(f"{Fore.GREEN}Heal anyway? (y/n): {Style.RESET_ALL}").strip().lower()
        
        if confirm != 'y':
            print(f"{Fore.CYAN}Wise choice. Choosing a different action...{Style.RESET_ALL}")
            time.sleep(1)
            return False  # Return False to let player choose again
        
        # Player confirmed - proceed with pointless heal
        print(f"\n{Fore.RED}What a waste... {hero.heroine_name} stupidly attempts to heal {target.heroine_name},")
        print(f"who is at FULL HEALTH, so, uh yeah, nothing happens. Brilliant.{Style.RESET_ALL}\n")
        time.sleep(2)
        return True
    
    # Get hero's heal roll
    hero_rolls = get_heroine_rolls(hero)
    heal_roll = hero_rolls['heal_roll']
    
    # Add heal stat
    total_heal = heal_roll + hero.stats.get('heal', 0)
    
    if total_heal <= 0:
        print(f"{Fore.RED}{hero.heroine_name} doesn't have healing power!{Style.RESET_ALL}")
        return False
    
    # Apply healing
    old_health = target.health
    target.health = min(target.health + total_heal, target.starting_health)
    actual_heal = target.health - old_health
    
    # Flavor text
    print(f"\n{Fore.CYAN}✨ {hero.heroine_name} channels healing energy into {target.heroine_name}! ✨{Style.RESET_ALL}")
    time.sleep(0.5)
    print(f"{Fore.GREEN}{target.heroine_name} recovers {actual_heal} HP!{Style.RESET_ALL}")
    time.sleep(0.5)
    
    if target.health >= target.starting_health:
        print(f"{Fore.YELLOW}{target.heroine_name} is at full health!{Style.RESET_ALL}")
        time.sleep(0.5)
    
    return True

def execute_heal_on_undead(hero, target):
    """
    Clerics can damage undead by 'healing' them.
    Positive energy burns the unholy!
    
    Args:
        hero: Cleric casting heal
        target: Undead mob
        
    Returns:
        bool: True if executed
    """
    # Get hero's heal roll
    hero_rolls = get_heroine_rolls(hero)
    heal_roll = hero_rolls['heal_roll']
    
    # Add heal stat (this becomes damage to undead)
    total_damage = heal_roll + hero.stats.get('heal', 0)
    
    if total_damage <= 0:
        print(f"{Fore.RED}{hero.heroine_name} doesn't have healing power!{Style.RESET_ALL}")
        return False
    
    # Cap displayed damage to remaining HP (don't show overkill)
    displayed_damage = min(total_damage, max(0, target.health))
    
    # Apply damage to undead
    target.health -= total_damage
    
    # SNARKY FLAVOR TEXT!
    print(f"\n{Fore.YELLOW}✨ {hero.heroine_name} channels HOLY ENERGY at {target.name}! ✨{Style.RESET_ALL}")
    time.sleep(0.5)
    
    snarky_messages = [
        f"{Fore.GREEN}The positive energy BURNS the undead abomination!\n\"How's THAT for bedside manner?\" {hero.heroine_name} quips.",
        f"{Fore.GREEN}Holy light sears {target.name}'s rotting flesh!\n\"I'm helping! Sort of!\" {hero.heroine_name} grins.",
        f"{Fore.GREEN}\"The power of healing compels you to DIE... again!\" {hero.heroine_name} shouts.\n{target.name} looks very confused before bursting into flames.",
        f"{Fore.GREEN}Radiant energy scorches {target.name}! It shrieks in agony!\n\"Oops, did that hurt? My bad!\" {hero.heroine_name} says, not sorry at all.",
        f"{Fore.GREEN}{target.name} writhes as holy energy courses through its undead body!\n\"You're welcome!\" {hero.heroine_name} chirps cheerfully.",
        f"{Fore.GREEN}\"Let me fix that rotting problem for you!\" {hero.heroine_name} says.\nHoly fire engulfs {target.name}. That's one way to fix it.",
        f"{Fore.GREEN}\"This might sting a bit!\" {hero.heroine_name} warns.\n{target.name} explodes in holy flames. \"Okay, more than a bit.\"",
        f"{Fore.GREEN}Positive energy floods {target.name}!\n\"Healing hurts when you're dead!\" {hero.heroine_name} laughs.",
    ]
    
    print(random.choice(snarky_messages))
    print(f"{Fore.RED}{target.name} takes {displayed_damage} holy damage!{Style.RESET_ALL}")
    time.sleep(0.5)
    
    if target.health <= 0:
        death_messages = [
            f"{Fore.YELLOW}☠️  {target.name} crumbles to dust! ☠️{Style.RESET_ALL}",
            f"{Fore.YELLOW}☠️  {target.name} explodes in a shower of bone fragments! ☠️{Style.RESET_ALL}",
            f"{Fore.YELLOW}☠️  {target.name} shrieks and dissolves into nothingness! ☠️{Style.RESET_ALL}",
            f"{Fore.YELLOW}☠️  {target.name} is finally put to rest! ☠️{Style.RESET_ALL}",
            f"{Fore.YELLOW}☠️  {target.name} collapses into a pile of ash! ☠️{Style.RESET_ALL}",
            f"{Fore.YELLOW}☠️  Holy light consumes {target.name} completely! ☠️{Style.RESET_ALL}",
        ]
        print(random.choice(death_messages))
        time.sleep(0.5)

        # Undead don't resurrect again (already dead!)
        # No resurrection check here
    
    return True

def execute_aoe_heal(hero, all_heroes):
    """
    Execute AOE Heal ability.
    Restores HP to entire party.
    
    Args:
        hero: Hero casting AOE heal
        all_heroes: List of all heroes in party
        
    Returns:
        bool: True if executed
    """
    # Get hero's aoe_heal roll
    hero_rolls = get_heroine_rolls(hero)
    heal_roll = hero_rolls['aoe_heal_roll']
    
    # Add aoe_heal stat
    total_heal = heal_roll + hero.stats.get('aoe_heal', 0)
    
    if total_heal <= 0:
        print(f"{Fore.RED}{hero.heroine_name} doesn't have AOE healing power!{Style.RESET_ALL}")
        return False
    
    print(f"\n{Fore.CYAN}✨✨ {hero.heroine_name} releases a wave of healing energy! ✨✨{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Heal all living heroes
    for target in all_heroes:
        if target.health > 0:
            old_health = target.health
            target.health = min(target.health + total_heal, target.starting_health)
            actual_heal = target.health - old_health
            
            if actual_heal > 0:
                print(f"{Fore.GREEN}{target.heroine_name} recovers {actual_heal} HP!{Style.RESET_ALL}")
                time.sleep(0.3)
    
    return True

def execute_defend(hero):
    """
    Execute Defend action.
    Increases dodge and parry for this turn.
    
    Args:
        hero: Hero taking defensive stance
        
    Returns:
        bool: True if executed
    """
    print(f"\n{Fore.CYAN}{hero.heroine_name} takes a defensive stance!{Style.RESET_ALL}")
    
    # Apply temporary defensive bonus
    hero.is_defending = True
    hero.defend_bonus = 5
    
    return True

def clear_defend_status(hero):
    """
    Clear defend status at end of turn.
    
    Args:
        hero: Hero to clear status from
    """
    if hasattr(hero, 'is_defending'):
        hero.is_defending = False
        hero.defend_bonus = 0

# ============================================================================
# COMBAT RESOLUTION FUNCTIONS
# ============================================================================

def check_hit(attacker_expertise_roll, defender_dodge_roll, defender_parry_roll):
    """
    Check if an attack hits the target.
    
    Args:
        attacker_expertise_roll: Attacker's expertise roll value
        defender_dodge_roll: Defender's dodge roll value
        defender_parry_roll: Defender's parry roll value
        
    Returns:
        bool: True if attack hits, False if dodged/parried
    """
    # Attack must beat BOTH dodge AND parry to hit
    if attacker_expertise_roll > defender_dodge_roll and attacker_expertise_roll > defender_parry_roll:
        return True
    else:
        return False

def calculate_damage(attacker_damage_roll, attacker_stats, is_crit, crit_mult):
    """
    Calculate final damage amount.
    
    Args:
        attacker_damage_roll: Attacker's damage roll value
        attacker_stats: Attacker's stat dictionary
        is_crit: Whether this is a critical hit
        crit_mult: Critical hit multiplier
        
    Returns:
        int: Final damage amount
    """
    # Base damage = roll + damage stat
    base_damage = attacker_damage_roll + attacker_stats.get('damage', 0)
    
    # Apply crit multiplier if crit
    if is_crit:
        final_damage = int(base_damage * crit_mult)
    else:
        final_damage = base_damage
    
    # Minimum 1 damage
    return max(1, final_damage)

def get_miss_flavor(attacker, defender):
    """
    Get flavor text for a missed attack.
    
    Args:
        attacker: Attacking character
        defender: Defending character
        
    Returns:
        str: Flavor text
    """
    import random
    
    attacker_name = attacker.heroine_name if hasattr(attacker, 'heroine_name') else attacker.name
    defender_name = defender.name if hasattr(defender, 'name') else defender.heroine_name
    
    flavors = [
        f"{attacker_name}'s attack misses {defender_name} completely!",
        f"{defender_name} dodges {attacker_name}'s strike!",
        f"{defender_name} parries {attacker_name}'s attack!",
        f"{attacker_name} swings wide, missing {defender_name}!",
        f"{defender_name} sidesteps {attacker_name}'s attack!",
    ]
    
    return random.choice(flavors)

def get_hit_flavor(attacker, defender, damage, is_crit, weapon_type='melee'):
    """
    Get flavor text for a successful hit.
    
    Args:
        attacker: Attacking character
        defender: Defending character
        damage: Damage dealt
        is_crit: Whether this was a critical hit
        weapon_type: Type of weapon used
        
    Returns:
        str: Flavor text
    """
    import random
    
    attacker_name = attacker.heroine_name if hasattr(attacker, 'heroine_name') else attacker.name
    defender_name = defender.name if hasattr(defender, 'name') else defender.heroine_name
    
    # Cap displayed damage to remaining HP (don't show overkill)
    displayed_damage = min(damage, max(0, defender.health))
    
    if 'range' in weapon_type.lower():
        # Ranged hit flavors
        if is_crit:
            flavors = [
                f"{attacker_name} lands a CRITICAL SHOT on {defender_name} for {displayed_damage} damage!",
                f"💥 CRITICAL! {attacker_name}'s projectile finds a vital spot on {defender_name} for {displayed_damage} damage!",
                f"{attacker_name}'s shot pierces {defender_name}'s defenses! CRITICAL HIT for {displayed_damage} damage!",
            ]
        else:
            flavors = [
                f"{attacker_name}'s shot hits {defender_name} for {displayed_damage} damage!",
                f"{attacker_name}'s projectile strikes {defender_name}, dealing {displayed_damage} damage!",
                f"{defender_name} takes {displayed_damage} damage from {attacker_name}'s attack!",
            ]
    else:
        # Melee hit flavors
        if is_crit:
            flavors = [
                f"{attacker_name} lands a CRITICAL HIT on {defender_name} for {displayed_damage} damage!",
                f"💥 CRITICAL! {attacker_name} devastates {defender_name} for {displayed_damage} damage!",
                f"{attacker_name} finds a weak spot! CRITICAL HIT for {displayed_damage} damage!",
            ]
        else:
            flavors = [
                f"{attacker_name} hits {defender_name} for {displayed_damage} damage!",
                f"{attacker_name} strikes {defender_name}, dealing {displayed_damage} damage!",
                f"{defender_name} takes {displayed_damage} damage from {attacker_name}!",
            ]
    
    return random.choice(flavors)

def execute_normal_attack(attacker, target, chosen_weapon=None):
    """
    Execute a normal attack.
    
    Args:
        attacker: Attacking character (hero or mob)
        target: Target character (mob or hero)
        chosen_weapon: Weapon to use (for heroes)
        
    Returns:
        bool: True if executed
    """
    # Determine if attacker is hero or mob
    is_hero = hasattr(attacker, 'heroine_name')
    
    # Get attacker's rolls
    if is_hero:
        attacker_rolls = get_heroine_rolls(attacker, chosen_weapon=chosen_weapon)
    else:
        attacker_rolls = get_mob_rolls(attacker)
    
    # Get defender's rolls
    is_defender_hero = hasattr(target, 'heroine_name')
    if is_defender_hero:
        defender_rolls = get_heroine_rolls(target)
    else:
        defender_rolls = get_mob_rolls(target)
    
    # Get weapon type for flavor text
    weapon_type = attacker_rolls.get('weapon_type', 'melee')
    
    # Check for automatic miss
    if attacker_rolls['miss']:
        miss_flavor = get_miss_flavor(attacker, target, weapon_type)
        print(f"{Fore.CYAN}{miss_flavor}{Style.RESET_ALL}")
        time.sleep(0.5)
        return True
    
    # Check if attack hits
    if not check_hit(attacker_rolls['expertise_roll'], defender_rolls['dodge_roll'], defender_rolls['parry_roll']):
        miss_flavor = get_miss_flavor(attacker, target, weapon_type)
        print(f"{Fore.CYAN}{miss_flavor}{Style.RESET_ALL}")
        time.sleep(0.5)
        return True
    
    # Damage is already calculated in get_heroine_rolls/get_mob_rolls
    # It includes base damage + expertise + crit multiplier if applicable
    damage = attacker_rolls['damage']
    
    # Cap damage to remaining HP for display
    actual_damage = min(damage, target.health)
    
    # Apply damage
    target.health -= damage
    
    # Flavor text (use actual_damage for display)
    hit_flavor = get_hit_flavor(attacker, target, actual_damage, attacker_rolls['crit'], weapon_type)
    print(f"{Fore.GREEN}{hit_flavor}{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Check if target defeated
    if target.health <= 0:
        target_name = target.name if hasattr(target, 'name') else target.heroine_name
        print(f"{Fore.YELLOW}☠️  {target_name} has been defeated! ☠️{Style.RESET_ALL}")
        time.sleep(0.5)
        
        # CHECK FOR BOSS RESURRECTION!
        if hasattr(target, 'name'):  # It's a mob
            if check_boss_resurrection(target):
                # Boss resurrected! Combat continues!
                print(f"\n{Fore.RED}⚔️  The battle is NOT over! ⚔️{Style.RESET_ALL}\n")
                time.sleep(1)
    
    return True
    

def check_boss_resurrection(mob):
    """
    Check if a boss should resurrect as undead.
    
    Args:
        mob: The defeated mob
        
    Returns:
        bool: True if boss resurrected
    """
    # Check if mob has resurrection ability
    if not hasattr(mob, 'resurrect_as_undead'):
        return False
    
    # Check if already resurrected
    if hasattr(mob, 'has_resurrected') and mob.has_resurrected:
        return False
    
    # RESURRECTION SCENE!
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{'='*60}")
    print(f"⚠️  WAIT... SOMETHING'S HAPPENING... ⚠️")
    print(f"{'='*60}")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    input("Press ENTER to continue...")
    clear_screen()
    
    print(f"\n{Fore.CYAN}{mob.name}'s body lies motionless on the cold stone floor.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Blood pools beneath the corpse.{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.GREEN}The party begins to relax...{Style.RESET_ALL}\n")
    time.sleep(1)
    
    input("Press ENTER to continue...")
    
    print(f"\n{Fore.YELLOW}But then...{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.RED}The corpse begins to TWITCH.{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.RED}Fingers curl. Limbs spasm.{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.RED}Dark energy swirls around the body like a vortex!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    input("Press ENTER to continue...")
    
    print(f'\n{Fore.MAGENTA}{mob.name}\'s voice echoes from beyond death:{Style.RESET_ALL}')
    print(f'{Fore.MAGENTA}"You fools... did you think DEATH could stop ME?"{Style.RESET_ALL}\n')
    time.sleep(1)
    
    print(f'{Fore.MAGENTA}"I am a MASTER of the dark arts!"{Style.RESET_ALL}\n')
    time.sleep(1)
    
    print(f'{Fore.MAGENTA}"Death is not my enemy... it is my SERVANT!"{Style.RESET_ALL}\n')
    time.sleep(1)
    
    input("Press ENTER to continue...")
    
    print(f"\n{Fore.RED}The body CONVULSES violently!{Style.RESET_ALL}")
    print(f"{Fore.RED}Flesh begins to slough away, revealing bone beneath!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.RED}The corpse RISES, wreathed in necrotic flames!{Style.RESET_ALL}")
    print(f"{Fore.RED}Where a man once stood, now floats a skeletal horror!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.RED}Empty eye sockets glow with unholy green fire!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    input("Press ENTER to continue...")
    
    # Perform resurrection
    mob.resurrect_as_undead()
    
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"💀 {mob.name} HAS RISEN! 💀")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.RED}⚠️  PHASE 2: UNDEAD LICH FORM ⚠️{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}HP: {mob.health}/{mob.starting_health}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Creature Type: {mob.creature_type.upper()}{Style.RESET_ALL}")
    # REMOVED: print(f"{Fore.GREEN}✨ Clerics can now damage this boss with healing spells! ✨{Style.RESET_ALL}")
    print(f"{Fore.RED}⚠️  All stats have been enhanced! ⚠️{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    print(f'{Fore.MAGENTA}{mob.name}: "Now... let us begin AGAIN!"{Style.RESET_ALL}\n')
    
    input("Press ENTER to continue the battle...")
    
    return True

def execute_player_turn(hero, all_heroes, all_mobs):
    """
    Execute a single hero's turn (player-controlled).
    
    Args:
        hero: The hero taking their turn
        all_heroes: List of all heroes in party
        all_mobs: List of all living mobs
        
    Returns:
        bool: True if turn completed successfully
    """
    # Clear defend status from last turn
    clear_defend_status(hero)
    
    # Reduce ability cooldowns
    hero.reduce_cooldowns()
    
    # Display action menu
    display_action_menu(hero, all_mobs)
    
    # Get player's action choice
    action_choice = get_player_action_choice()
    
    # Execute chosen action
    if action_choice == 1:
        # ATTACK
        
        # Check if Cleric trying to attack
        if hero.hero_class == 'Cleric':
            print(f"\n{Fore.RED}❌ {hero.heroine_name} recoils in horror!{Style.RESET_ALL}")
            print(f"{Fore.RED}\"I cannot harm the living! It would corrupt my very soul!\"")
            print(f"She refuses to attack. Choose something else, genius.{Style.RESET_ALL}\n")
            time.sleep(2)
            return execute_player_turn(hero, all_heroes, all_mobs)  # Show menu again
        
        # Choose weapon
        weapons = display_weapon_menu(hero)
        chosen_weapon = get_weapon_choice(hero, weapons)
        
        print(f"\n{Fore.CYAN}{hero.heroine_name} readies {chosen_weapon}!{Style.RESET_ALL}\n")
        time.sleep(0.5)
        
        if len(all_mobs) == 1:
            # Only one target - auto-select
            target = all_mobs[0]
            print(f"{Fore.CYAN}{hero.heroine_name} attacks {target.name}!{Style.RESET_ALL}\n")
        else:
            # Multiple targets - let player choose
            display_target_menu(all_mobs)
            target = get_target_choice(all_mobs)
        
        if target:
            execute_normal_attack(hero, target, chosen_weapon)
            return True
    
    elif action_choice == 2:
        # DEFEND
        execute_defend(hero)
        return True
    
    elif action_choice == 3:
        # SPECIAL ABILITY
        display_ability_menu(hero)
        ability = get_ability_choice(hero)
        
        if ability is None:
            # Player cancelled - show menu again
            return execute_player_turn(hero, all_heroes, all_mobs)
        
        # Determine target based on ability type
        if ability in ['Heal']:
            # Single-target heal - choose ally OR enemy (for "accidents")
            
            print(f"\n{Fore.YELLOW}Choose target:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}ALLIES:{Style.RESET_ALL}")
            for i, ally in enumerate(all_heroes, 1):
                if ally.health > 0:
                    print(f"  {i}. {ally.heroine_name} [HP: {ally.health}/{ally.starting_health}]")
            
            print(f"\n{Fore.RED}ENEMIES (Why would you heal an enemy? Unless...):{Style.RESET_ALL}")
            offset = len(all_heroes)
            for i, mob in enumerate(all_mobs, offset + 1):
                creature_hint = " [UNDEAD]" if mob.creature_type == 'undead' else ""
                print(f"  {i}. {mob.name} [HP: {mob.health}/{mob.starting_health}]{creature_hint}")
            
            while True:
                try:
                    choice = input(f"{Fore.GREEN}Enter target (1-{len(all_heroes) + len(all_mobs)}): {Style.RESET_ALL}").strip()
                    choice_num = int(choice)
                    
                    if 1 <= choice_num <= len(all_heroes):
                        # Healing an ally
                        target = all_heroes[choice_num - 1]
                        result = execute_ability(hero, ability, target, all_heroes, all_mobs)
                        if not result:  # Heal was cancelled (full HP warning)
                            return execute_player_turn(hero, all_heroes, all_mobs)
                        return True
                    elif len(all_heroes) < choice_num <= len(all_heroes) + len(all_mobs):
                        # Healing an enemy (either accident or intentional undead damage)
                        target = all_mobs[choice_num - len(all_heroes) - 1]
                        result = execute_ability(hero, ability, target, all_heroes, all_mobs)
                        if not result:
                            return execute_player_turn(hero, all_heroes, all_mobs)
                        return True
                except (ValueError, IndexError):
                    continue
        
        elif ability in ['AOE Heal']:
            # AOE heal - no target needed
            execute_ability(hero, ability, None, all_heroes, all_mobs)
            return True
        
        elif ability in ['Power Strike']:
            # Attack ability - choose enemy
            if len(all_mobs) == 1:
                # Only one target - auto-select
                target = all_mobs[0]
                print(f"\n{Fore.CYAN}{hero.heroine_name} prepares a Power Strike against {target.name}!{Style.RESET_ALL}\n")
            else:
                # Multiple targets
                display_target_menu(all_mobs)
                target = get_target_choice(all_mobs)
            
            if target:
                execute_ability(hero, ability, target, all_heroes, all_mobs)
                return True
    
    elif action_choice == 4:
        # USE ITEM (not implemented yet)
        print(f"{Fore.RED}Items not implemented yet!{Style.RESET_ALL}")
        time.sleep(1)
        return execute_player_turn(hero, all_heroes, all_mobs)
    
    return False

def execute_mob_turn(mob, all_heroes):
    """
    Execute a single mob's turn (AI-controlled).
    
    Args:
        mob: The mob taking their turn
        all_heroes: List of all living heroes
        
    Returns:
        bool: True if turn completed successfully
    """
    import random
    
    # Filter to living heroes only
    living_heroes = [h for h in all_heroes if h.health > 0]
    
    if not living_heroes:
        return False
    
    # SPECIAL: Necromancer King taunts in Phase 2!
    if hasattr(mob, 'phase') and mob.phase == 2 and random.randint(1, 100) <= 30:
        taunts = [
            f'{Fore.MAGENTA}{mob.name}: "You cannot kill what is already dead!"{Style.RESET_ALL}',
            f'{Fore.MAGENTA}{mob.name}: "Your weapons are USELESS against me now!"{Style.RESET_ALL}',
            f'{Fore.MAGENTA}{mob.name}: "I am ETERNAL! I am UNDYING!"{Style.RESET_ALL}',
            f'{Fore.MAGENTA}{mob.name}: "Death has made me STRONGER!"{Style.RESET_ALL}',
            f'{Fore.MAGENTA}{mob.name}: "Foolish mortals! You only delayed the inevitable!"{Style.RESET_ALL}',
        ]
        print(f"\n{random.choice(taunts)}\n")
        time.sleep(1)
    
    # Simple AI: Attack a random living hero
    target = random.choice(living_heroes)
    
    print(f"\n{Fore.RED}{mob.name}'s turn!{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Execute attack
    execute_normal_attack(mob, target)
    
    return True

# ============================================================================
# MAIN COMBAT LOOP
# ============================================================================

def run_combat(heroes, mobs, location_name="Unknown Location"):
    """
    Main combat loop - handles turn order and victory/defeat conditions.
    
    Args:
        heroes: List of Hero objects
        mobs: List of Mob objects
        location_name: Name of current location (for display)
        
    Returns:
        str: 'victory', 'defeat', or 'fled'
    """
    clear_screen()
    
    print(f"\n{Fore.RED}{'='*60}")
    print(f"⚔️  COMBAT BEGINS at {location_name}! ⚔️")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    time.sleep(1)
    
    # Display initial combatants
    print(f"{Fore.CYAN}YOUR PARTY:{Style.RESET_ALL}")
    for hero in heroes:
        print(f"  {hero.heroine_name} [{hero.hero_class}] - HP: {hero.health}/{hero.starting_health}")
    
    print(f"\n{Fore.RED}ENEMIES:{Style.RESET_ALL}")
    for mob in mobs:
        print(f"  {mob.name} [{mob.mob_type}] - HP: {mob.health}/{mob.starting_health}")
    
    print()
    input(f"\n{Fore.CYAN}Press ENTER to begin combat...{Style.RESET_ALL}")
    
    # Initialize combat tracking
    round_number = 1
    
    # Keep reference to ALL mobs (including defeated) for status display
    all_mobs_including_dead = mobs.copy()
    
    # Main combat loop
    while True:
        clear_screen()
        
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"ROUND {round_number}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        time.sleep(0.5)
        
        # ====================================================================
        # PLAYER PHASE
        # ====================================================================
        
        living_heroes = [h for h in heroes if h.health > 0]
        living_mobs = [m for m in mobs if m.health > 0]
        
        # Check victory condition before player turn
        if not living_mobs:
            return handle_victory(heroes, all_mobs_including_dead)
        
        # Each living hero takes a turn
        for hero in living_heroes:
            # Clear screen for each hero's turn
            clear_screen()
            
            print(f"\n{Fore.YELLOW}{'='*60}")
            print(f"ROUND {round_number}")
            print(f"{'='*60}{Style.RESET_ALL}\n")
            
            # Check if all mobs defeated mid-turn
            living_mobs = [m for m in mobs if m.health > 0]
            if not living_mobs:
                return handle_victory(heroes, all_mobs_including_dead)
            
            # Execute hero's turn
            execute_player_turn(hero, heroes, living_mobs)
            
            # Remove dead mobs from list
            mobs = [m for m in mobs if m.health > 0]
            
            # Pause after each action
            input(f"\n{Fore.CYAN}Press ENTER to continue...{Style.RESET_ALL}")
        
        # ====================================================================
        # ENEMY PHASE
        # ====================================================================
        
        living_mobs = [m for m in mobs if m.health > 0]
        living_heroes = [h for h in heroes if h.health > 0]
        
        # Check victory condition after player phase
        if not living_mobs:
            return handle_victory(heroes, all_mobs_including_dead)
        
        # Check defeat condition before enemy phase
        if not living_heroes:
            return handle_defeat(heroes)
        
        clear_screen()
        
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"ROUND {round_number}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        print(f"\n{Fore.RED}{'='*60}")
        print(f"ENEMY PHASE")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        time.sleep(1)
        
        # Each living mob takes a turn
        for mob in living_mobs:
            # Clear screen for each mob's turn
            clear_screen()
            
            print(f"\n{Fore.YELLOW}{'='*60}")
            print(f"ROUND {round_number}")
            print(f"{'='*60}{Style.RESET_ALL}\n")
            
            # Check if all heroes defeated mid-turn
            living_heroes = [h for h in heroes if h.health > 0]
            if not living_heroes:
                return handle_defeat(heroes)
            
            # Execute mob's turn
            execute_mob_turn(mob, living_heroes)
            
            # Pause after each action
            input(f"\n{Fore.CYAN}Press ENTER to continue...{Style.RESET_ALL}")
        
        # ====================================================================
        # END OF ROUND CLEANUP
        # ====================================================================
        
        # Check defeat condition after enemy phase
        living_heroes = [h for h in heroes if h.health > 0]
        if not living_heroes:
            return handle_defeat(heroes)
        
        # Clear screen and display current status
        clear_screen()
        
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"END OF ROUND {round_number}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Display current status (including defeated mobs/heroes)
        display_combat_status(heroes, all_mobs_including_dead)
        
        # Increment round counter
        round_number += 1
        
        # Pause before next round
        input(f"\n{Fore.CYAN}Press ENTER to continue to next round...{Style.RESET_ALL}")

def display_combat_status(heroes, mobs):
    """
    Display current HP status of all combatants.
    
    Args:
        heroes: List of all heroes
        mobs: List of all mobs (including defeated)
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"CURRENT STATUS")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}YOUR PARTY:{Style.RESET_ALL}")
    for hero in heroes:
        if hero.health > 0:
            hp_percent = (hero.health / hero.starting_health) * 100
            
            if hp_percent > 66:
                color = Fore.GREEN
            elif hp_percent > 33:
                color = Fore.YELLOW
            else:
                color = Fore.RED
            
            print(f"  {color}{hero.heroine_name}: {hero.health}/{hero.starting_health} HP{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}{hero.heroine_name}: DEFEATED{Style.RESET_ALL}")
    
    print(f"\n{Fore.RED}ENEMIES:{Style.RESET_ALL}")
    for mob in mobs:
        if mob.health > 0:
            hp_percent = (mob.health / mob.starting_health) * 100
            
            if hp_percent > 66:
                color = Fore.GREEN
            elif hp_percent > 33:
                color = Fore.YELLOW
            else:
                color = Fore.RED
            
            print(f"  {color}{mob.name}: {mob.health}/{mob.starting_health} HP{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}{mob.name}: DEFEATED{Style.RESET_ALL}")
    
    print()

def handle_victory(heroes, mobs):
    """
    Handle victory condition.
    
    Args:
        heroes: List of heroes
        mobs: List of defeated mobs
        
    Returns:
        str: 'victory'
    """
    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"✨ VICTORY! ✨")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.YELLOW}All enemies have been defeated! Suck it, monsters!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    # Display surviving heroes
    living_heroes = [h for h in heroes if h.health > 0]
    print(f"{Fore.CYAN}Surviving Heroes:{Style.RESET_ALL}")
    for hero in living_heroes:
        print(f"  {hero.heroine_name}: {hero.health}/{hero.starting_health} HP")
    
    # Display fallen heroes
    dead_heroes = [h for h in heroes if h.health <= 0]
    if dead_heroes:
        print(f"\n{Fore.RED}Fallen Heroes:{Style.RESET_ALL}")
        for hero in dead_heroes:
            print(f"  {hero.heroine_name}: DEFEATED")
    
    print()
    time.sleep(2)
    
    # POST-BATTLE HEALING
    post_battle_healing(heroes)
    
    # POST-BATTLE REVIVE (if any Clerics have the ability)
    post_battle_revive_option(heroes)
    
    return 'victory'

def post_battle_healing(heroes):
    """
    Fully heal all living heroes after battle.
    
    Args:
        heroes: List of all heroes
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"POST-BATTLE RECOVERY")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}The party takes a moment to catch their breath and tend to their wounds...{Style.RESET_ALL}\n")
    time.sleep(1)
    
    for hero in heroes:
        if hero.health > 0:
            if hero.health < hero.starting_health:
                healed_amount = hero.starting_health - hero.health
                hero.health = hero.starting_health
                print(f"{Fore.GREEN}{hero.heroine_name} recovers {healed_amount} HP! (Now at {hero.health}/{hero.starting_health}){Style.RESET_ALL}")
            else:
                print(f"{Fore.CYAN}{hero.heroine_name} is already at full health. Show-off.{Style.RESET_ALL}")
    
    print()
    time.sleep(1)

def post_battle_revive_option(heroes):
    """
    Allow Clerics to revive ONE dead party member (if they have the spell).
    This is a framework for future implementation.
    
    Args:
        heroes: List of all heroes
        
    Returns:
        bool: True if any revives were performed
    """
    # Check for dead heroes
    dead_heroes = [h for h in heroes if h.health <= 0]
    
    if not dead_heroes:
        return False  # No one to revive
    
    # Check for living Clerics with revive ability
    living_clerics = [h for h in heroes if h.health > 0 and h.hero_class == 'Cleric']
    
    if not living_clerics:
        return False  # No Clerics to perform revival
    
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"REVIVAL OPPORTUNITY")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    revive_performed = False
    
    for cleric in living_clerics:
        # Check if Cleric has revive ability (for future implementation)
        if not hasattr(cleric, 'has_revive') or not cleric.has_revive:
            continue
        
        # Check if Cleric has already used their one revive for this dungeon
        if hasattr(cleric, 'revive_used') and cleric.revive_used:
            print(f"{Fore.YELLOW}{cleric.heroine_name} has already used their revive for this dungeon.{Style.RESET_ALL}")
            continue
        
        print(f"{Fore.CYAN}{cleric.heroine_name} can revive ONE fallen ally!{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Fallen heroes:{Style.RESET_ALL}")
        
        for i, dead_hero in enumerate(dead_heroes, 1):
            print(f"  {i}. {dead_hero.heroine_name} [{dead_hero.hero_class}]")
        
        print(f"  0. Don't revive anyone")
        
        while True:
            try:
                choice = input(f"\n{Fore.GREEN}Choose hero to revive (0-{len(dead_heroes)}): {Style.RESET_ALL}").strip()
                choice_num = int(choice)
                
                if choice_num == 0:
                    print(f"{Fore.CYAN}{cleric.heroine_name} decides not to revive anyone. Cold.{Style.RESET_ALL}")
                    break
                
                if 1 <= choice_num <= len(dead_heroes):
                    revived_hero = dead_heroes[choice_num - 1]
                    
                    # Perform revival!
                    print(f"\n{Fore.MAGENTA}{cleric.heroine_name} channels divine energy!{Style.RESET_ALL}")
                    time.sleep(1)
                    print(f"{Fore.MAGENTA}Golden light surrounds {revived_hero.heroine_name}...{Style.RESET_ALL}")
                    time.sleep(1)
                    print(f"{Fore.GREEN}✨ {revived_hero.heroine_name} gasps back to life! ✨{Style.RESET_ALL}\n")
                    
                    # Restore to 50% HP
                    revived_hero.health = revived_hero.starting_health // 2
                    
                    print(f"{Fore.GREEN}{revived_hero.heroine_name} is revived with {revived_hero.health} HP!{Style.RESET_ALL}")
                    
                    # Mark revive as used
                    cleric.revive_used = True
                    revive_performed = True
                    
                    # Remove from dead list
                    dead_heroes.remove(revived_hero)
                    
                    break
                    
            except ValueError:
                continue
    
    return revive_performed

def handle_defeat(heroes):
    """
    Handle defeat condition.
    
    Args:
        heroes: List of defeated heroes
        
    Returns:
        str: 'defeat'
    """
    print(f"\n{Fore.RED}{'='*60}")
    print(f"☠️  DEFEAT! ☠️")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.YELLOW}Your entire party has been defeated...{Style.RESET_ALL}\n")
    time.sleep(2)
    
    return 'defeat'

# ============================================================================
# TEST COMBAT FUNCTION
# ============================================================================

def test_combat():
    """
    Quick test function to run a sample combat.
    Run this to test the combat system!
    """
    import Slayer_Heroes as sh
    import Slayer_Mobs as sm
    
    print(f"{Fore.CYAN}Creating test party...{Style.RESET_ALL}")
    
    # Create test heroes with names
    warrior = sh.Warrior("Aria the Brave")
    cleric = sh.Cleric("Lyra the Healer")
    wizard = sh.Wizard("Zara the Wise")
    
    heroes = [warrior, cleric, wizard]
    
    print(f"{Fore.CYAN}Creating test enemies...{Style.RESET_ALL}")
    
    # Create test mobs using the factory
    mobs = sm.create_random_encounter('medium')
    
    print(f"{Fore.GREEN}Starting combat!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    # Run combat
    result = run_combat(heroes, mobs, "Test Arena")
    
    print(f"\n{Fore.YELLOW}Combat Result: {result.upper()}{Style.RESET_ALL}")
    
    return result
# ============================================================================
# RUN TEST WHEN EXECUTED DIRECTLY
# ============================================================================

def test_undead_combat():
    """
    Test combat with undead mobs to see Cleric healing damage them!
    """
    import Slayer_Heroes as sh
    import Slayer_Mobs as sm
    
    print(f"{Fore.CYAN}Creating test party with a Cleric...{Style.RESET_ALL}")
    
    # Create test heroes
    warrior = sh.Warrior("Aria the Brave")
    cleric = sh.Cleric("Lyra the Healer")
    
    heroes = [warrior, cleric]
    
    print(f"{Fore.CYAN}Creating UNDEAD enemies...{Style.RESET_ALL}")
    
    # Create undead mobs manually
    from Slayer_Mobs import Mob
    
    skeleton1 = Mob(mob_species='skeleton', mob_type='regular', creature_type='undead')
    skeleton2 = Mob(mob_species='skeleton', mob_type='minion', creature_type='undead')
    zombie = Mob(mob_species='zombie', mob_type='regular', creature_type='undead')
    
    mobs = [skeleton1, skeleton2, zombie]
    
    print(f"{Fore.GREEN}Starting UNDEAD combat!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}The Cleric can now damage undead with healing spells!{Style.RESET_ALL}\n")
    time.sleep(2)
    
    # Run combat
    result = run_combat(heroes, mobs, "Cursed Crypt")
    
    print(f"\n{Fore.YELLOW}Combat Result: {result.upper()}{Style.RESET_ALL}")
    
    return result

def test_necromancer_king_boss():
    """
    Epic two-phase boss fight against the Necromancer King!
    Phase 1: Living necromancer
    Phase 2: Rises as undead lich (weak to healing!)
    """
    import Slayer_Heroes as sh
    from Slayer_Mobs import NecromancerKing
    
    print(f"{Fore.CYAN}Creating a balanced party for the boss fight...{Style.RESET_ALL}")
    
    # Create a strong party
    warrior = sh.Warrior("Aria the Brave")
    cleric = sh.Cleric("Lyra the Healer")
    wizard = sh.Wizard("Zara the Wise")
    hunter = sh.Hunter("Kira the Swift")
    
    heroes = [warrior, cleric, wizard, hunter]
    
    # Buff them a bit for the boss fight
    for hero in heroes:
        hero.health = hero.starting_health + 20
        hero.starting_health = hero.health
    
    print(f"{Fore.CYAN}Summoning the NECROMANCER KING...{Style.RESET_ALL}")
    time.sleep(1)
    
    # Create the boss
    boss = NecromancerKing("Valdris the Deathless")
    
    mobs = [boss]
    
    print(f"\n{Fore.RED}{'='*60}")
    print(f"{Fore.RED}⚠️  BOSS BATTLE: NECROMANCER KING ⚠️{Style.RESET_ALL}")
    print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}You enter a massive throne room...{Style.RESET_ALL}")
    time.sleep(1)
    print(f"{Fore.YELLOW}A robed figure sits upon a throne of bones.{Style.RESET_ALL}")
    time.sleep(1)
    print(f'{Fore.RED}Valdris: "Welcome, mortals. You have come to die."{Style.RESET_ALL}')
    time.sleep(1)
    print(f'{Fore.RED}Valdris: "But know this... death is merely the BEGINNING!"{Style.RESET_ALL}\n')
    time.sleep(2)
    
    input("Press ENTER to begin the boss fight...")
    
    # Run combat
    result = run_combat(heroes, mobs, "The Necromancer's Throne Room")
    
    print(f"\n{Fore.YELLOW}Combat Result: {result.upper()}{Style.RESET_ALL}")
    
    if result == 'victory':
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"The Necromancer King has been vanquished!")
        print(f"Both his living AND undead forms have been destroyed!")
        print(f"The curse upon the land begins to lift...")
        print(f"{'='*60}{Style.RESET_ALL}\n")
    
    return result

if __name__ == "__main__":
    # Uncomment whichever test you want to run:
    
    # test_combat()  # Normal combat
    # test_undead_combat()  # Undead combat (Clerics can damage them!)
    test_necromancer_king_boss()  # EPIC TWO-PHASE BOSS FIGHT!
# ============================================================================
# END OF SLAYER_COMBAT.PY
# ============================================================================