import Slayer_Accessory as acc
from Slayer_UI import say, pause, clear
import Slayer_Narration as nar


mobs_table = acc.get_mobs()

class Disgruntled_Dwarf:

    def __init__(self, name : str):
        self.name = name
        self.mob_class = 'Disgruntled Dwarf'
        acc.initialize_mob(self, mobs_table)
        self.is_boss = True

    async def enrage(self):
        await pause()  # let the hit that did it sink in...
        await clear()  # ...then the enrage gets the narration box all to itself
        await say(f"{self.name} gasps loudly.  \"Now that one fucking hurt!!\"")
        await pause()
        await say(f"\n{self.name} suddenly bulges out in all directions.  He becomes a rippling mass of what looks like pure muscle - the veins in his neck and forearms swell to such a size, they look like they might rupture.\n")
        await say("\"Oh lassies,\" he growls, \"you really fucked up now!  Now?  NOW I'M ANGRY!!!!\"")
        self.is_dead = False # setting to True is necessary just in case the blow that caused Happy to enrage also "killed" him
        self.enraged = True
        self.starting_health = self.stats['enraged_hp']
        self.health = self.stats['enraged_hp']

    async def healed_by(self, heroine : object):
        """Happy has opinions about being healed by the people trying to kill him."""
        await say(f"{self.name} holds up his hand a moment to quiet the group.  Oddly, it works.")
        await say(f"\"Dear lass,\" he hoarsely whispers and smirks at {heroine.name}, \"Whose side are you on anyway?\"")
        await say("[narr]I wonder the same thing!![/]")
        await pause()

    async def trigger_happy_wipe(self, party_dict : dict, happy_killed : bool, mobs : list = ()) -> dict:
        """After the tavern fight: the wipe, the resurrection, Happy's loot, the first stat raises and the back
        room. The story lines are Ted's, in Slayer_Narration.py."""
        await nar.happy_wipe(party_dict, happy_killed)
        await nar.happy_resurrection(party_dict)
        await nar.happy_loot(party_dict)
        party_dict = await acc.get_loot(self, party_dict, mobs, at_tavern=True) # Happy's loot, plus whatever his dead buddies dropped
        await nar.happy_stats(party_dict)
        party_dict = await acc.get_stat_increases(party_dict)
        await nar.happy_back_room(party_dict)
        party_dict = await acc.visit_stash(party_dict) # swap gear in Happy's back room before the dungeon
        return party_dict


class Drunk_Dwarf:

    def __init__(self, name : str):
        self.name = name
        self.mob_class = 'Drunk Dwarf'
        acc.initialize_mob(self, mobs_table)
        self.is_boss = False
