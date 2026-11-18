# SLAYER

*A profane parody dungeon crawler, written in Python.*

<!-- DRAFT by Claude for Ted to review: rewrite anything, especially the voice. -->

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
- **Bosses with tricks:** Krazy Kobolds who share their wounds through their purple-eyed boss, and a wolf
  pack that hunts as one and guards its Alpha.
- **Loot, a stash and a forge:** gear, potions and trinkets drop after fights. Keep the overflow in The Stash
  and bring upgrade kits to the forge out back of the Devil's Brew.
- **Heroines who grow:** every won fight makes them a little better, and saved parties keep it across runs.
- **Its own soundtrack** (in the game window): a rowdy fiddle-and-bagpipe jig to start, a seedy, lurching waltz
  once the tavern door creaks shut behind you, a galloping battle march for Happy (faster and angrier once he's
  enraged), something tender and magical while he brings you back, a jolly oom-pah for the loot, scratching and
  giggling in the dark as the Kobolds close in, then their own goofy, spooky fight music, a creeping dungeon, and a
  grim, driving one for the wolves. The title buzzes and crackles like a fluorescent tube that won't come on. In a
  fight, weapons make a sound as you pick them (steel, a bow drawn, a spell gathering...), misses go SHWOOP, fire
  roars (Fire Rain is a whole firestorm), lightning cracks and thunders, a Shifter's specials roar and snarl,
  vomit gets a gag, dwarves grunt (Kobolds squeak, wolves yelp) and heroines cry out when hit, a killing blow gets
  a death cry, a scared heroine screams, a heal makes her squeal, and a group heal plays a harp and a choir. A volume
  slider in the top-right corner sets how loud it all is (and remembers it), and clicking the ♪ turns it off and on.
- **Play it your way:** a game window (Windows, Mac or Linux), the original command-prompt version, or in a
  web browser, tablets included.

Still early: the dungeon currently ends after the wolves. *To be continued!*

## Playing it

### The easy way (Windows)

Download `Slayer.zip` from the [Releases page](https://github.com/theobigdog/slayer_next_gen/releases), unzip it
anywhere, open the `Slayer` folder and double-click `Slayer.exe`. Nothing to install. Your saved parties are kept in
that folder, so keep it together.

Windows may warn about an unrecognized app the first time, since the game isn't signed: click **More info**, then
**Run anyway**.

When a new version comes out, download the new zip and unzip it into a fresh folder. To keep your parties, copy the
`saved_parties` folder over from the old one.

### From the source

You'll need Python (it's made with 3.12.3) and two packages:

```
pip install -r requirements.txt
```

Then, in the game's top folder:

| Command | What it starts |
|---|---|
| `python main.py` | the game window |
| `python game\Slayer_Main.py` | the command-prompt version (Windows only) |

To build your own `Slayer.exe`, double-click `build\build_exe.bat`; the result lands in `dist\Slayer.zip`.

To play in a browser or on a tablet, see [build/WEB_BUILD.md](build/WEB_BUILD.md).

Making a release (developers): publish a GitHub release tagged like `v0.1`. A few minutes later
[the release build](.github/workflows/release-build.yml) attaches `Slayer.zip` to it. The same build can be run by
hand from the Actions tab to try it out without releasing anything.

## What's where

| Folder | What's in it |
|---|---|
| `game/` | the game's code: every `Slayer_*.py` |
| `supporting_docs/` | the CSVs with the game's numbers (below) |
| `assets/` | art, fonts, music and the icon |
| `build/` | how the `.exe` and the browser version get built |
| `tools/` | `check_data.py`, the balance simulations, and `make_music.py` (the soundtrack) |
| `saved_parties/` | your saves, when you run it from the source |

`main.py` stays in the top folder because the browser build looks for it there.

## Making changes

Most of the game's numbers live in plain CSV files in `supporting_docs/`, so you can change a lot without
touching code:

| File | What's in it |
|---|---|
| `hero_stats.csv`, `stat_growth.csv` | each class's starting stats and how they grow |
| `items.csv` | every weapon, spell, potion and trinket: damage, who can use it, where it drops |
| `mobs.csv`, `mob_equipment.csv` | the enemies and their attacks |
| `upgrades.csv` | the upgrade kits for the forge |

After editing them, `python tools\check_data.py` checks for typos and anything that doesn't add up.

The narrator's lines are in `game/Slayer_Narration.py`. Art and fonts go in `assets/`, and `assets/README.md` explains
how to drop in your own sprites. The music is written as notes in `tools/make_music.py`, which renders it into
`assets/music/*.ogg` (and the sound effects into `assets/sounds/`) (it needs `pip install numpy soundfile`, for whoever changes the music; players don't).
`tools/balance/` has the simulations used to balance the classes and fights.

## Credits

- Made by **theobigdog**, in collaboration with Claude (Anthropic).
- Fonts: New Rocker and Fondamento (SIL Open Font License) and DejaVu. Their licenses are in `assets/fonts/`.
- Music and sound effects: original, composed and synthesized in `tools/make_music.py` (no samples), under the same
  licence as the art.

## License

Free forever, never for profit. Code: PolyForm Noncommercial 1.0.0. Art and writing: CC BY-NC-SA 4.0. The fonts
keep their own licenses. See [LICENSE.md](LICENSE.md).
