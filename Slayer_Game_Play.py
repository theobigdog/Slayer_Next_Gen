import Slayer_Accessory as acc
from Slayer_UI import pause, say, wait, yes_no
import Slayer_Combat as combat
import Slayer_Dwarf
import Slayer_Narration as nar
import random

happy_buddy_names = ['Burpy', 'Gassy', 'Smelly', 'Grumpy', 'Hairy', 'Slappy', 'Fuck-Head', 'Bloaty']

def get_turn_order(party: list, mobs: list) -> list:
    heroine_dice_cutoff = acc.get_dice_cutoffs()['speed_cutoff']
    mob_dice_cutoff = acc.get_dice_cutoffs_mobs()['speed_cutoff']
    entity_dict = {}
    for heroine in party:
        if not heroine.is_dead:
            speed = heroine.stats['speed']
            speed_roll = acc.multi_roll(1,heroine_dice_cutoff)
            entity_dict[heroine] = speed + speed_roll
    for mob in mobs:
        if not mob.is_dead:
            if mob.enraged:
                speed = mob.stats['enraged_speed']
            else:
                speed = mob.stats['speed']
            speed_roll = acc.multi_roll(1,mob_dice_cutoff)
            entity_dict[mob] = speed + speed_roll
    return sorted(entity_dict, key=entity_dict.get, reverse=True)
    
def alive_mobs(mobs: list) -> bool:
    return any(not mob.is_dead for mob in mobs)

def check_wiped(party: list) -> bool:
    return all(heroine.is_dead for heroine in party)


async def play_game(party_dict: dict) -> dict:
    dev_mode = acc.dev_mode()
    if not dev_mode:
        if party_dict['times_run_dungeon'] == 1:
            party_dict['narration'] = await yes_no('[narr]Would you like narrative?[/]  ')
            if party_dict['narration']:
                await say("[narr]Really?  Oh hell yes, I've been practicing my voices.[/]")
            else:
                await say("[narr]Fair.  I'll be over here.  Quietly.  Silently judging the mobs, not you.[/]")
            await pause()
            if party_dict['narration']:
                await nar.intro()
                await nar.happy_intro()
        else:
            first = await yes_no("[narr]I'm assuming you don't want to hear me blabber the-fuck on about details again, do you?[/]  ")
            if first:
                _ = await yes_no("[narr]Uh, yes you DO want me to provide narrative, or not?[/]  ")
            else:
                _ = await yes_no("[narr]Oh, so no I assumed wrong you do need narrative again, or did you mean you didn't want repeated narrative?[/]  ")
            await wait(0.3)
            await say("[narr]But wait, bone-head, you're still not clearly answering my question.....[/]")
            await wait(0.75)
            await say("[narr]I could go on like this all day....[/]")
            await wait(0.3)
            await say('[narr]Oh, right.  Sorry.[/]')
            await wait(0.2)

            party_dict['narration'] = await yes_no("[narr]Ok, for realsies, would you like narration?[/]  ")
            if party_dict['narration']:
                await say("[narr]Shirley you can't be serious....[/]")
                await wait(0.3)
                await say(f"[narr]Sorry, I'll stop calling you \"Shirley\", {party_dict['name']}...[/]")
                await wait(0.7)
                await say('[narr]You beautiful masochist.[/]')
                await wait(1)
            else:
                await say('[narr]Understood.  Grabbing a roll of duct tape for my own mouth.[/]')
                await wait(0.5)
                await say('[narr]Umm....  May I at least have a small breathing hole?  I have a deviated septum and I\'m a mouth-breather....[/]')
                await pause()

    happy = Slayer_Dwarf.Disgruntled_Dwarf('Happy')
    buddy1, buddy2 = random.sample(happy_buddy_names, 2)
    mobs = [happy, Slayer_Dwarf.Drunk_Dwarf(buddy1), Slayer_Dwarf.Drunk_Dwarf(buddy2)]
    combat.start_battle(party_dict['party']) # special weapons are ready again

    round_num = 0
    while not party_dict['wiped'] and alive_mobs(mobs):
        round_num += 1
        turn_order = get_turn_order(party_dict['party'], mobs)
        for attacker in turn_order:
            if not attacker.is_dead and alive_mobs(mobs):
                await combat.show_current_status(party_dict['party'], mobs, round_num)
                await wait(0.5)
                if not attacker.is_mob: # player's turn with the given heroine
                    party_dict, mobs, luck_roll = await combat.player_turn(attacker, party_dict, mobs)
                    if luck_roll and not attacker.is_dead and alive_mobs(mobs): #  Intentionally, this does not loop, only one lucky attack per round ;)
                        await say(f"[narr]{attacker.name}'s lucky fuckin' day![/]  She gets an extra turn.  [narr]Make it count![/]")
                        await pause()
                        await combat.show_current_status(party_dict['party'], mobs, round_num)
                        party_dict, mobs, _ = await combat.player_turn(attacker, party_dict, mobs)
                    for mob in mobs:
                        if not mob.is_dead:
                            turn_stat = 'enraged_turn_chance' if mob.enraged else 'turn_chance'
                            if acc.multi_roll(1,100) <= mob.stats[turn_stat]:
                                party_dict['wiped'] = check_wiped(party_dict['party'])
                                await combat.show_current_status(party_dict['party'], mobs, round_num)
                                await say(f"{mob.name}, that insane bastard, moves like a horny jack-rabbit on a date and gets an extra attack.  [narr]Boo.[/]")
                                party_dict, mobs, _ = await combat.mob_turn(mob, party_dict, mobs, extra=True)
                                
                else: # mob-group's turn with the given mob(attacker)
                    party_dict, mobs, luck_roll = await combat.mob_turn(attacker, party_dict, mobs)
                    party_dict['wiped'] = check_wiped(party_dict['party'])
                    if luck_roll and not attacker.is_dead and alive_mobs(mobs) and not party_dict['wiped']:#  Intentionally, this does not loop, only one lucky attack per round ;) - though it's possible I might want to be able to toggle this for mobs so that multiple luck rolls are possible.  Maybe a separate luck function for certain mob class_types
                        await say(f"[narr]Oh, shit.[/]  {attacker.name} gets an extra attack!  [narr]Brace yourselves![/]")
                        await combat.show_current_status(party_dict['party'], mobs, round_num)
                        party_dict, mobs, _ = await combat.mob_turn(attacker, party_dict , mobs, extra=True) # straight to the results
                party_dict['wiped'] = check_wiped(party_dict['party'])
        if party_dict['wiped'] or not alive_mobs(mobs):
            await combat.show_current_status(party_dict['party'], mobs, round_num)
            await pause()
    if party_dict['wiped']:
        party_dict = await happy.trigger_happy_wipe(party_dict, happy.is_dead)
        party_dict = acc.refresh_party(party_dict, False)

    return party_dict
