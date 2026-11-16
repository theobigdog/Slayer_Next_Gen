# Balance tools

Simulations for tuning the game's numbers. Not part of the game; nothing here is imported by it. A simple bot
plays the real fights (the real code and CSVs): the Cleric heals whoever's hurt (or buffs the best fighter), everyone
else uses her hardest hit, potions under 30% HP, and in the wolf fight they rush the Alpha. It never uses Hide or the
Token, and with `BOOM=wolves` the Sapper saves her Big Badda Boom for the wolves. Every party starts fresh (no stat
raises, no loot), then plays the Kobolds, the full heal, and the wolves, just like a run.

Run these from a command prompt in the game folder. They use every CPU core but one, and write results as
`.jsonl` files (one line per lineup) next to the scripts; those and `variants/` are ignored by git.

| Script | What it answers | Example |
|---|---|---|
| `sweep.py` | How do these lineups do? (or every lineup of a size, at most 2 of a class) | `python tools\balance\sweep.py . 200 out.jsonl 4` |
| `analyze.py` | Best/worst lineups per size, and how much each class helps | `python tools\balance\analyze.py tools\balance\out.jsonl` |
| `marginal.py` | What does each class add to a few base parties? (and the 2nd Cleric's edge) | `python tools\balance\marginal.py . 300 m.jsonl` |
| `variant.py` | Same as marginal, on a copy of the game with some CSV numbers changed | see below |
| `tune_wolves.py` | Wolf damage per party size so a decent one-Cleric party wins about N% | `python tools\balance\tune_wolves.py . 600 85` |

`sweep.py` arguments: game folder, runs per lineup, output file, party sizes (`4` or `2,3,4`), and optionally
your own lineups instead, separated by `;`: `... out.jsonl 0 "Warrior,Hunter,Cleric;Witch,Sapper,Cleric"`.

Each line of output: `kobolds%` (won the Kobolds), `wolves_after%` (won the wolves, of the parties that got there),
`clear%` (won both), `alive_at_end` (heroines standing after a clear). With 500 runs, treat differences under about
4 points as a tie.

Trying out numbers without touching the real CSVs (here: a Healing Wand nerf and a sturdier Battle Mage):

    python tools\balance\variant.py wandtest 300 "{\"items.csv\": {\"healing_wand\": {\"damage_low\": -10, \"damage_high\": -4}}, \"hero_stats.csv\": {\"Battle_Mage\": {\"toughness\": 30}}}"

Environment switches: `BOOM=wolves` (or `kobolds`, `any`; off by default in sweep.py, on in the others),
`REST=0` (no full heal between fights), `WOLF_SCALE={"4": [1.0, 1.0, 0.42]}` (override the wolves' PARTY_SCALE),
`ADD=Warrior,Cleric` (marginal/variant: only try adding these classes).

## What the Nov 15, 2026 tuning found

- No Cleric is close to hopeless (best lineups cleared 16-26%); the narrator now double-checks a party without one.
- Changed: Healing Wand 4-10 (was 6-14), Cleric heal chance 85 (was 92), Battle Mage 45-60 HP and 30 toughness
  (was 35-50 and 20), wolf damage cut about a third (PARTY_SCALE in Slayer_Wolves.py). A 2nd Cleric now only edges
  out other picks at 5-6 heroines, and the Battle Mage is mid-pack.
- After that, a decent one-Cleric party wins the wolves ~85% at every size 2-8; the Kobolds are 54% (2 heroines),
  ~75% (3), 76-85% (4), 90% (5), 74-79% (6-8). Still to tune.
- Putting Strength on a recharge didn't change the 2nd Cleric's value; a stronger, rechargeable Deep Meditation
  made the 2nd Cleric too good again.
