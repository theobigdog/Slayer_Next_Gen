# Slayer art and fonts

## Sprites (`assets/sprites/`)

Drop a PNG here with the right name and the window version uses it instead of the
placeholder box. No code changes needed. Missing files just stay as boxes.

Name: `<class>_<pose>.png`, all lowercase, spaces become underscores.

| File | Shown for |
|---|---|
| `warrior_idle.png`, `shifter_idle.png`, `battle_mage_idle.png`, `hunter_idle.png`, `witch_idle.png`, `sapper_idle.png`, `cleric_idle.png` | the heroines |
| `disgruntled_dwarf_idle.png` | Happy |
| `disgruntled_dwarf_enraged.png` | Happy after he enrages (falls back to the idle one if it's missing) |
| `drunk_dwarf_idle.png` | the drunk dwarves |
| `krazy_kobolds_idle.png`, `krazy_kobolds_enraged.png` | the Krazy Kobolds (the enraged one is optional) |
| `pack_wolf_idle.png` | the wolves |
| `alpha_wolf_idle.png` | the Alpha, the pack's leader |

Sizes (DRAFT, Nov 19). The game window is 1280 x 720. What matters most is the *shape* of the canvas: the game
shrinks each sprite to fit its box and never stretches it, so a canvas with the box's shape fills the box. Draw at
about 4x the on-screen size so it stays crisp:

| Sprite | Box on screen | Suggested canvas |
|---|---|---|
| each heroine | 104 x 104 | 512 x 512 |
| a Krazy Kobold | 104 x 112 (up to 8, in two rows) | 480 x 520 |
| the wolves and the Alpha | 104 x 112 in a big pack, 120 x 150 in a small one | 480 x 560 |
| the drunk dwarves | 120 x 150 | 480 x 600 |
| Happy | 200 x 240, enraged 250 x 300 | 500 x 600 |

The Kobold Shaman and the Alpha get a slightly bigger box with a gold edge. The Shaman uses the regular Kobold art.

Tips:
- PNG with a transparent background.
- Sprites stand on the bottom edge of their slot, so put the feet on the bottom of the image.
- Heroines stand on the left and face right; the monsters stand on the right and face left.
- The name and class are written over the bottom of the sprite (with a soft shadow), so keep the
  important bits (faces!) out of the bottom third or so.
- Dead combatants are drawn darkened automatically; no separate art needed.
- Pixel art: draw it small (say 48 x 48 for a heroine) and tell Claude, so it gets scaled up with sharp pixels
  instead of smoothed.
- The web version has to stay small, so very big files may get smaller copies made for the game (the originals
  are kept).

## Fonts (`assets/fonts/`)

- **New Rocker** (`NewRocker-Regular.ttf`, picked by Ted on Nov 1): names, headings, menus, box labels,
  HP numbers and floating numbers. License: SIL Open Font License, `LICENSE-NewRocker-OFL.txt`.
- **Fondamento** (`Fondamento-Regular.ttf`): the narration, readable but still stylized. License: SIL Open
  Font License, `LICENSE-Fondamento-OFL.txt`. To try another, change `NARRATION_FONT` near the top of
  `game/Slayer_Window.py`.
- **DejaVu Sans / Sans Mono**: the click hints and the ASCII title art. License: `LICENSE-DejaVu.txt`.

All three come from Google Fonts / the DejaVu project. Both licenses allow shipping the fonts with the game, as long as the license files stay alongside.
The window version ships its own fonts because a browser has none of your system fonts.
