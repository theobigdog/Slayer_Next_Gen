"""Party-composition sweep: every lineup of 1-8 heroines (at most 2 of any class) plays the dungeon as it stands:
the Krazy Kobolds, then the wolves with whatever HP and heroines are left (no healing in between, same as the game).
A sensible bot plays (fight_sim's Bot: Cleric heals the hurt / buffs the best fighter, others hit hardest, wolves:
rush the Alpha). Big Badda Boom and the Token aren't used. Not part of the game.
usage: python sweep.py GAME_DIR RUNS OUT.jsonl SIZE[,SIZE..] [lineup;lineup..]"""
import asyncio, json, os, random, re, sys, zlib
from itertools import combinations_with_replacement
from collections import Counter
from multiprocessing import Pool
GAME = sys.argv[1]; sys.path.insert(0, os.path.join(GAME, 'game'))  # GAME: the game's top folder; the code is in its game folder
CLASSES = ['Warrior', 'Shifter', 'Battle_Mage', 'Hunter', 'Witch', 'Sapper', 'Cleric']
REST = os.environ.get('REST', '1') == '1'
BOOM = os.environ.get('BOOM', '')  # '', 'kobolds', 'wolves' or 'any': where the bot may use the Boom
frac = lambda x: x.health / x.starting_health

def setup():
    global ui, acc, fp, combat, gp, Slayer_Kobolds, Slayer_Wolves, bot
    import Slayer_UI as ui, Slayer_Accessory as acc, Slayer_Form_Party as fp, Slayer_Combat as combat, Slayer_Game_Play as gp, Slayer_Kobolds, Slayer_Wolves
    if os.environ.get('WOLF_SCALE'):
        Slayer_Wolves.PARTY_SCALE.update({int(k): tuple(v) for k, v in json.loads(os.environ['WOLF_SCALE']).items()})
    bot = Bot(); ui.use(bot)

class Bot:
    def __init__(self): self.party, self.mobs, self.active, self.last, self.steps = [], [], None, '', 0
    async def say(self, text=''): pass
    async def pause(self): pass
    async def wait(self, s): pass
    async def clear(self): pass
    async def show_party(self, party, active=None): self.party = party
    async def show_battle(self, party, mobs, round_num, active=None): self.party, self.mobs, self.active, self.round = party, mobs, active, round_num
    async def effect(self, *a): pass
    async def yes_no(self, prompt): return False
    async def ask_text(self, prompt): return 'x'
    def numbers(self, label):
        m = re.search(r'\((\d+) - (\d+) (damage|healing)', label)
        return ((int(m.group(1)) + int(m.group(2))) / 2, m.group(3)) if m else (0, None)
    async def choose(self, prompt, labels, oops):
        self.steps += 1
        if self.steps > 6000: raise RuntimeError('stuck')
        me = self.active
        allies = [x for x in self.party if not x.is_dead]
        foes = [x for x in self.mobs if not x.is_dead]
        here = 'wolves' if foes and 'Wolf' in foes[0].mob_class else 'kobolds'
        boom_ok = BOOM in (here, 'any') and not self.boomed and len(foes) >= 3
        ready = [(i, l) for i, l in enumerate(labels) if 'recharging' not in l.lower() and 'Token' not in l and ('Big Badda' not in l or boom_ok)]
        if boom_ok and any('Big Badda' in l for _, l in ready):
            self.boomed = True; self.last = 'Big Badda Boom'
            return next(i for i, l in ready if 'Big Badda' in l)
        heals = [(self.numbers(l)[0], i, l) for i, l in ready if self.numbers(l)[1] == 'healing']
        hits = [(self.numbers(l)[0] * (min(len(foes), 3) if 'hits them all' in l else 1), i, l) for i, l in ready if self.numbers(l)[1] == 'damage']
        pick = None
        if me is not None and me.hero_class == 'Cleric':
            hurt = sorted(allies, key=frac)
            group = [h for h in heals if 'group heal' in h[2]]
            single = [h for h in heals if 'group heal' not in h[2]]
            if group and sum(frac(x) < 0.6 for x in allies) >= 2: pick = max(group)
            elif hurt and frac(hurt[0]) < 0.65 and single: pick = max(single)
            else:
                buff = [(i, l) for i, l in ready if l.startswith('Strength')] or [(i, l) for i, l in ready if l.startswith('Blessing')]
                pick = (0, *buff[0]) if buff and len(allies) > 1 else (max(single) if single else None)
        else:
            potion = [h for h in heals if 'dose' in h[2]]
            if me is not None and frac(me) < 0.3 and potion: pick = max(potion)
            elif hits: pick = max(hits)
            cry = [(i, l) for i, l in ready if l.startswith('Battle Cry')]   # the class abilities with no damage number
            cackle = [(i, l) for i, l in ready if l.startswith('Evil Cackle')]
            if cry and any(x.hero_class == 'Cleric' for x in allies) and random.random() < 0.4: pick = (0, *cry[0])
            elif cackle and len(foes) >= 3 and random.random() < 0.5: pick = (0, *cackle[0])
        if pick is None: pick = (0, *random.choice(ready or list(enumerate(labels))))
        self.last = pick[2]
        return pick[1]
    async def choose_target(self, prompt, party, mobs, oops):
        if party and (self.last.startswith('Strength') or self.last.startswith('Blessing')):
            fighters = [x for x in party if x.hero_class != 'Cleric'] or party
            return max(fighters, key=lambda x: x.starting_health)
        if party and self.numbers(self.last)[1] == 'healing':
            return min(party, key=frac)
        if mobs and getattr(mobs[0], 'mob_class', '') == 'Alpha Wolf': return mobs[0]
        return min(mobs, key=lambda m: m.health)

async def one_run(classes):
    party = [fp.get_hero(c, f'{c[:4]}{i}') for i, c in enumerate(classes)]
    pd = {'name': 'Sim', 'party': party, 'stash': [], 'times_run_dungeon': 1, 'wiped': False}
    bot.steps = 0; bot.boomed = False
    pd = await gp.battle(pd, Slayer_Kobolds.make_pack(len(party)), Slayer_Kobolds.round_end, Slayer_Kobolds.after_turn)
    if pd['wiped']:
        return (False, False, 0)
    if REST: acc.rest_party(pd)
    else:
        for h in party: h.status = {}
    bot.steps = 0
    pd = await gp.battle(pd, Slayer_Wolves.make_pack(len(party)), Slayer_Wolves.round_end)
    return (True, not pd['wiped'], sum(not h.is_dead for h in party) if not pd['wiped'] else 0)

def play(job):
    classes, runs, seed = job
    random.seed(seed)
    out = [asyncio.run(one_run(classes)) for _ in range(runs)]
    k = sum(o[0] for o in out); w = sum(o[1] for o in out)
    return {'size': len(classes), 'lineup': classes, 'runs': runs, 'kobolds%': round(100 * k / runs, 1),
            'wolves_after%': round(100 * w / max(1, k), 1), 'clear%': round(100 * w / runs, 1),
            'alive_at_end': round(sum(o[2] for o in out) / max(1, w), 2)}

def lineups(size):
    return [list(c) for c in combinations_with_replacement(CLASSES, size) if max(Counter(c).values()) <= 2]

if __name__ == '__main__':
    runs, out = int(sys.argv[2]), sys.argv[3]
    sizes = [int(x) for x in sys.argv[4].split(',')]
    jobs = [l.split(',') for l in sys.argv[5].split(';')] if len(sys.argv) > 5 else [l for s in sizes for l in lineups(s)]
    cores = max(1, (os.cpu_count() or 2) - 1) # all but one core
    with Pool(cores, initializer=setup) as pool, open(out, 'a') as f:
        for n, r in enumerate(pool.imap_unordered(play, [(l, runs, zlib.crc32(','.join(l).encode()) % 100000) for l in jobs])):
            f.write(json.dumps(r) + '\n'); f.flush()
