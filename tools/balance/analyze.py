import json, sys
from collections import defaultdict
rows = [json.loads(l) for l in open(sys.argv[1])]
short = {'Warrior': 'War', 'Shifter': 'Shf', 'Battle_Mage': 'BM', 'Hunter': 'Hun', 'Witch': 'Wit', 'Sapper': 'Sap', 'Cleric': 'Clr'}
for size in sorted({r['size'] for r in rows}):
    rs = sorted([r for r in rows if r['size'] == size], key=lambda r: -r['clear%'])
    print(f"\n== size {size}: {len(rs)} lineups, median clear {rs[len(rs)//2]['clear%']}%")
    for r in rs[:6] + [None] + rs[-4:]:
        if r is None: print('   ...'); continue
        print(f"  {r['clear%']:5.1f}%  kob {r['kobolds%']:5.1f}  wolves-after {r['wolves_after%']:5.1f}  alive {r['alive_at_end']}  {'/'.join(short[c] for c in r['lineup'])}")
    clerics = defaultdict(list)
    for r in rs: clerics[r['lineup'].count('Cleric')].append(r['clear%'])
    print('  by Clerics:', {k: round(sum(v)/len(v), 1) for k, v in sorted(clerics.items())})
    with_c = defaultdict(list)
    for r in rs:
        for c in short:
            with_c[c].append((c in r['lineup'], r['clear%']))
    print('  avg clear with/without:', {short[c]: (round(sum(x for h, x in v if h)/max(1, sum(h for h, _ in v)), 1), round(sum(x for h, x in v if not h)/max(1, sum(not h for h, _ in v)), 1)) for c, v in with_c.items()})
