# SLAYER

*A profane parody dungeon crawler, written in Python.*

<!-- DRAFT by Claude for Ted to review: rewrite anything, especially the voice. Lines marked TODO need your answer. -->

Pick a party of heroines, walk into the Devil's Brew, and pick a fight with Happy, the tavern's very disgruntled
dwarf. Lose. Get dragged into his secret dungeon anyway. Then fight your way down, one bad decision at a time,
while a narrator who's only *pretending* to be an asshole heckles every move you make.

> **Heads-up:** it swears. A lot. Like, a lot a lot. If that's not your thing, this isn't your game.

## What's in it

- **Seven classes:** Warrior, Shifter, Battle Mage, Hunter, Witch, Sapper and Cleric. Each has her own starting
  kit, specials and quirks. (The Cleric can't touch a weapon. It burns.)
- **Parties of 1 to 8.** Choose every class and name yourself, or let the narrator do it. He has opinions.
- **Turn-based fights** with speed, luck, crits, dodges, buffs and debuffs: poison, bleeding, drunkenness,
  confusion, Blessings, Strength, and a Big Badda Boom that ends badly for everyone, the Sapper most of all.
- **Bosses with tricks:** Krazy Kobolds who share their wounds through a purple-eyed Grand Poobah, and a wolf
  pack that hunts as one and guards its Alpha.
- **Loot, a stash and a forge:** gear, potions and trinkets drop after fights. Keep the overflow in The Stash
  and bring upgrade kits to the forge out back of the Devil's Brew.
- **Heroines who grow:** every won fight makes them a little better, and saved parties keep it across runs.
- **Play it your way:** a game window (Windows, Mac or Linux), the original command-prompt version, or in a
  web browser, tablets included.

Still early: the dungeon currently ends after the wolves. *To be continued!*

## Playing it

### The easy way (Windows)

<!-- TODO: where should people get Slayer.zip? A GitHub Release, itch.io, a link you send them? -->
Download `Slayer.zip`, unzip it anywhere, and double-click `Slayer.exe`. No Python needed. Your saved parties are
kept in the same folder.

### From the source

You'll need Python 3 <!-- TODO: which version do you use? (`python --version`) --> and two packages:

```
pip install pygame-ce colorama
```

Then, in the game folder:

| Command | What it starts |
|---|---|
| `python main.py` | the game window |
| `python Slayer_Main.py` | the command-prompt version (Windows only) |

To build your own `Slayer.exe`, double-click `build_exe.bat`; the result lands in `dist\Slayer.zip`.
To play in a browser or on a tablet, see [WEB_BUILD.md](WEB_BUILD.md).

## Making changes

Most of the game's numbers live in plain CSV files in `supporting_docs/`, so you can change a lot without
touching code:

| File | What's in it |
|---|---|
| `hero_stats.csv`, `stat_growth.csv` | each class's starting stats and how they grow |
| `items.csv` | every weapon, spell, potion and trinket: damage, who can use it, where it drops |
| `mobs.csv`, `mob_equipment.csv` | the enemies and their attacks |
| `upgrades.csv` | the upgrade kits for the forge |

After editing them, `python check_data.py` checks for typos and anything that doesn't add up.

The narrator's lines are in `Slayer_Narration.py`. Art and fonts go in `assets/`, and `assets/README.md` explains
how to drop in your own sprites. `tools/balance/` has the simulations used to balance the classes and fights.

## Credits

<!-- TODO: how do you want to be credited? Name, handle, a line about the project? -->
- Made by **theobigdog**, with a lot of coding help from Claude (Anthropic).
- Fonts: New Rocker and Fondamento (SIL Open Font License) and DejaVu. Their licenses are in `assets/fonts/`.

## License

<!-- TODO: pick one. If you want it to stay free and never be sold, ask Claude about the options. -->
Not decided yet.
