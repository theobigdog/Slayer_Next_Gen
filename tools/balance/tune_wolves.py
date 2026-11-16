"""Bisect the wolves' damage multiplier per party size so a decent one-Cleric party wins the wolves (after the
Kobolds and the full heal) about TARGET% of the time. usage: python tune_wolves.py GAME_DIR RUNS TARGET"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))  # tools/balance
sys.path.insert(0, sys.argv[1]); import Slayer_Wolves
GAME, RUNS, TARGET = sys.argv[1], sys.argv[2], float(sys.argv[3])
PARTIES = {2: 'Warrior,Cleric', 3: 'Warrior,Hunter,Cleric', 4: 'Warrior,Shifter,Hunter,Cleric', 5: 'Warrior,Shifter,Hunter,Witch,Cleric',
           6: 'Warrior,Shifter,Hunter,Witch,Sapper,Cleric', 7: 'Warrior,Shifter,Battle_Mage,Hunter,Witch,Sapper,Cleric',
           8: 'Warrior,Warrior,Shifter,Battle_Mage,Hunter,Witch,Sapper,Cleric'}
def wolves_win(size, dmg):
    a, w, _ = Slayer_Wolves.PARTY_SCALE[size]
    out = os.path.join(HERE, f'tw_{size}.jsonl')
    if os.path.exists(out): os.remove(out)
    subprocess.run([sys.executable, os.path.join(HERE, 'sweep.py'), GAME, RUNS, out, '0', PARTIES[size]], check=True,
                   env=dict(os.environ, BOOM='wolves', WOLF_SCALE=json.dumps({size: [a, w, dmg]})))
    r = json.loads(open(out).readline()); return r['wolves_after%'], r['kobolds%']
result = {}
for size in PARTIES:
    lo, hi = 0.2, 1.0
    for _ in range(5):
        mid = round((lo + hi) / 2, 3)
        win, kob = wolves_win(size, mid)
        if win > TARGET: lo = mid
        else: hi = mid
    final = round((lo + hi) / 2, 2)
    win, kob = wolves_win(size, final)
    result[size] = final
    print(size, 'old dmg', Slayer_Wolves.PARTY_SCALE[size][2], '-> new', final, ' wolves win', win, ' kobolds', kob, flush=True)
print(json.dumps(result))
