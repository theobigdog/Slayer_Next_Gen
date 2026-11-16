"""Marginal value of each class: for a few base parties, add each class in turn and see the clear rate.
usage: python marginal.py GAME_DIR RUNS OUT.jsonl   (ADD=Warrior,Cleric to try only some classes)"""
import subprocess, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))  # tools/balance
CLASSES = os.environ.get('ADD', 'Warrior,Shifter,Battle_Mage,Hunter,Witch,Sapper,Cleric').split(',')
BASES = [['Warrior', 'Hunter', 'Cleric'], ['Shifter', 'Witch', 'Cleric'],
         ['Warrior', 'Shifter', 'Hunter', 'Cleric'], ['Hunter', 'Witch', 'Sapper', 'Cleric'],
         ['Warrior', 'Shifter', 'Hunter', 'Witch', 'Cleric'], ['Shifter', 'Hunter', 'Witch', 'Sapper', 'Cleric']]
jobs = [b + [c] for b in BASES for c in CLASSES]
out = sys.argv[3]
if os.path.exists(out): os.remove(out)
subprocess.run([sys.executable, os.path.join(HERE, 'sweep.py'), sys.argv[1], sys.argv[2], out, '0', ';'.join(','.join(j) for j in jobs)], check=True, env=dict(os.environ, BOOM='wolves'))
rows = {tuple(json.loads(l)['lineup']): json.loads(l) for l in open(out)}
short = {'Warrior': 'War', 'Shifter': 'Shf', 'Battle_Mage': 'BM', 'Hunter': 'Hun', 'Witch': 'Wit', 'Sapper': 'Sap', 'Cleric': 'Clr'}
print('base'.ljust(26) + ''.join(short[c].rjust(13) for c in CLASSES))
for b in BASES:
    cells = []
    for c in CLASSES:
        r = rows[tuple(b + [c])]
        cells.append(f"{r['clear%']:5.1f}({r['kobolds%']:3.0f}/{r['wolves_after%']:3.0f})".rjust(13))
    print('/'.join(short[x] for x in b).ljust(26) + ''.join(cells))

best = []
for b in BASES:
    others = max(rows[tuple(b + [c])]['clear%'] for c in CLASSES if c != 'Cleric')
    best.append((len(b) + 1, round(rows[tuple(b + ['Cleric'])]['clear%'] - others, 1)))
print('2nd-Cleric edge over the best other pick, by party size:', best)
