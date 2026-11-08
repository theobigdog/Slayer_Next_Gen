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
        standing = party_dict.pop('standing_at_wipe', []) # who was still up when the killing blow landed (wipe_party)
        if not happy_killed:
            standing = []
        for spot, health in standing: # they killed him: whoever was still up is alive for the scene, until he gets back up
            party_dict['party'][spot].is_dead, party_dict['party'][spot].health = False, health
        await nar.happy_wipe(party_dict, happy_killed)
        for spot, _ in standing:
            party_dict['party'][spot].is_dead, party_dict['party'][spot].health = True, 0
        self.is_dead, self.enraged = False, False # he always gets back up, and the rage is spent: calm Happy does the resurrecting
        self.starting_health = self.health = self.stats['starting_hp']
        await nar.happy_resurrection(party_dict)
        party_dict = acc.refresh_party(party_dict, False) # everyone's back on her feet (and on screen) once Happy's done
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
