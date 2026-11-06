from Slayer_UI import say, pause, wait, clear
import Slayer_Accessory as acc
from Slayer_Accessory import whine
import random

LUCKY_GIFT = 5 # the narrator's thank-you for listening: + this much luck for every heroine, first run only

def threatening_item(heroine : object) -> str:
    """Something she can fondle threateningly: a melee weapon if she has one, then any weapon, then whatever she's got."""
    items = [acc.get_item(name) for name in heroine.inv if name != 'token_of_the_wise_witch']
    for kinds in (('melee', 'both'), ('range', 'aoe'), ('heal', 'trinket')):
        found = [item for item in items if item['attack_type'] in kinds]
        if found:
            return random.choice(found)['item_desc']
    return 'fists'

async def intro(party_dict : dict) -> dict:
    await say("[narr]Welcome, welcome.. welcome..... yeah, welcome to Slayer, the GOAT, game of the year.....  Um...[/]")
    await wait(1)
    await say("[narr]Look, I'm just going to be honest with you - I've been doing this for a long fucking time.[/]")
    await say("[narr]I've seen so many parties, like yours, enter this thing and just never come out.[/]")
    await say("[narr]The vast majority, really.[/]")
    await say("[narr]I think...[/]")
    await wait(2)
    await say("[narr]Fuck, now that I think about it, has anyone ever actually walked back out of here?  No?[/]")
    await say("[narr]I just can't take many more observations of failure.  I think it's starting to break me...[/]")
    await pause()
    await say("[narr]Please do better than those who have come before you!  Please?[/]")
    await pause()
    await clear()
    await say(f"[narr]Ok... <ahem>  I hope you're ready for this, {party_dict['name']}.[/]")
    await wait(0.5)
    if party_dict['times_run_dungeon'] == 1:
        await say("[narr]Firstly, as a Thank You for taking the time to enjoy my immense wit and charm...[/]")
        await say("[narr]Fine.  As a token of gratitude for allowing me my little \"stories\", your whole starting party has received a small gift.[/]")
        await say("[narr]If you ask me, I'd say all of you just look.... a little more lucky than you did.[/]")
        for heroine in party_dict['party']: # the gift: a little luck for everyone (never shown as a number)
            heroine.stats['luck'] = min(acc.STAT_CAP, heroine.stats['luck'] + LUCKY_GIFT)
        await say("[narr]Now that my small measure of sappiness is out of my system, let's get to it.[/]")
        await wait(0.5)
    await say("[narr]Well, whether you have played before or not, welcome to Slayer Next Gen.  The LONG-anticipated version of Slayer, the....[/]")
    await say(f"[narr]Wait, Slayer 1 never released?  Then why the fuck is this one called Next Gen?  {whine()}[/]")
    await say("[narr]I guess, suffice it to say that this version is at least a mild upgrade.  Anyone out there sick enough to want to try it, contact My Mom![/]")
    await pause()
    await clear()
    await say("You enter Empathia, a magical world dominated by women.  Wise women.  Honorable women.  Strong women.  Beautiful women.")
    await pause()
    await say("However, festering wounds of ugly chauvinism remain - tucked away in dark pockets of the world.")
    if len(party_dict['party']) == 1:
        await say("You recently squeezed a lead out of someone regarding a newly-discovered dark pocket, deep in the Phallic Mountains - where else?")
    else:
        h1, h2 = random.sample(party_dict['party'], 2) # two different heroines, picked at random
        await say(f"Investigating some of these dark pockets, {h1.name} recently beat the shit out of a rather suspicious character she met down a dark passageway.")
        await say(f"\"Yeah, I remember that!\" squeals {h2.name}.  \"Remember, {h1.name}?  Once you had tightly gripped him by his shriveled cojones, he became the loudest rat I've ever heard!\"")
        await say(f"{h1.name} sneers, \"Right, the fucking 'Phallic Mountains.'  He kept talking about those Dick Hills or whatever.\"")
        await pause()
        await say("[narr]Now where else would it be?[/]")
    await pause()
    await clear()
    await say("[narr]Right.  So the Dick Hills have been calling to you, apparently?  Be honest, have you ever even heard of the \"Phallic Mountains\"?  No?[/]")
    await say("[narr]Exactly, you've never heard of them, you know nothing of the secret tavern in the southwest foothills, shit, if it weren't for me rambling you wouldn't even know about....  Right.[/]")
    await pause()
    await say("[narr]Well, then I guess it's off you go now, to the infamous Devil's Brew Tavern, found in the darkest depths of the Dick Hi...[/]")
    await say("[narr]Wait, what?  You're already here?[/]")
    await say(f"[narr]Jesus Fucking Christ, I'm the fucking Narrator, can someone just keep me up-to-date on this?  You're making me sound like a fucking moron!  {whine()}[/]")
    await say("[narr]I guess I missed out on the part where you were traveling.  It's a shame, I was going to tell you all about the local flora and fauna on the way to the mountains.  All about the histories and cultures of every town we passed.[/]")
    await say("[narr]We were going to do some real girl-scout shit....[/]")
    await wait(1)
    await say("[narr]Welcome to the Devil's Brew![/]")
    await pause()
    return party_dict # party_dict returns unchanged if this isn't the first time they've gone through.  They have to do this their first time, or the opportunity is gone forever for that party

async def happy_intro(party_dict : dict) -> None:
    party = party_dict['party']
    armed = [x for x in party if any(acc.get_item(i)['attack_type'] in ('melee', 'both') for i in x.inv)]
    h1 = random.choice(armed or party) # the one who gets in the barkeep's face, with a melee weapon if anyone has one
    others = [x for x in party if x is not h1]
    h2 = random.choice(others) if others else h1 # a solo heroine does all the talking
    await clear()
    await say("As your ragtag party enters the tavern, weary from days of traveling, and ready to kick back with a fresh cold mug, they catch sight of the general clientele.")
    await say(f"Coming from back home, a tavern filled with men, seedy, dark, vicious men, is not something {h1.name} is used to.")
    await say(f"\"What the hell are they looking at?\" murmurs {h2.name}.  \"I'm getting the feeling that I'm not wanted here.\"")
    await pause()
    await say(f"Catching the eye of the proprietor, a somewhat-aged, dwarven tavern-keep, {h1.name} maneuvers past two semi-comatose dwarves, incoherently mumbling to each other, more in gurgles and pops than in any identifiable language.")
    await say(f"\"Tavern Keeper!\" yells {h1.name}, in a voice far too loud for such close quarters.  \"A word, please.\"")
    await say("\"It is my understanding that this building is a front for the center of the Nocturnal Order of Males Against Authoritative Matriarchy (NO MAAM) movement.  You ARE familiar with this movement, no?\"")
    await say("The tavern keeper, carefully cleaning mugs, clearly stifling a sigh, begins, \"Look here, lass, I don't know where you think you are, but you're not in Vulvamora anymore, and you might want to show a little more respect.\"")
    await pause()
    item = threatening_item(h1) # a melee weapon if she has one (a Cleric makes do with her Healing Wand)
    await say(f"{h1.name} smirks.  \"Oh, you want a little more respect, do you?\" she says as she, seemingly idly, yet threateningly, fondles her {item}.  \"Perhaps we try this again.\"")
    await say("\"Barkeep, either help us with the cause, or get out of the way.  But we will not tolerate any further foolishness from you.\"")
    await pause()
    await say("\"Oh lassie.... Now take it easy or you might make me angry.\"")
    await say(f"{h2.name} belts out with laughter, \"Really, you think I'm scared of some old, washed-up dwarf?  I eat pieces of shit like you for breakfast!\"")
    await pause()
    await say("His brows furrow briefly, and there is the briefest hint of almost purple-fire, reflecting across his eyes.  \"Why did you have to go and say something like that?  We dwarves, say what you will about us, but, shit?  For breakfast?  I don't think so!!\" he growls and nimbly leaps over the bar in front of the party.")
    await say("The two drunk dwarves suddenly stop their incoherent babbling, and seem to be taking notice of the situation.")
    await say(f"\"Now hold on, buddy,\" starts {h1.name}, but she is immediately interrupted.")
    await pause()
    await say("\"No!  No, you hold on, BUDDY!  This is my home.  This is my business, and you are no longer welcome.  Please Leave!\" he growls.")
    await say("The words are punctuated by both drunk dwarves hopping off their seats and taking up a fighting stance next to the tavern keeper.")
    await say(f"\"Are you fucking kidding me right now?\" starts {h2.name}.  \"We will mop the floor with you, old dwarf!\"")
    await say("\"ENOUGH!\" he booms.  \"I think it's about time you lassies learn a little respect....\"")
    await say(f"{h1.name} stares the tavern keeper in the eyes, hissing, \"Bring it!!\"")
    await pause()
