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

Tips:
- PNG with a transparent background.
- Draw it big; the game scales it down to fit its slot and keeps the shape (it never stretches).
  Heroines fit in a 104 x 104 box, the dwarves in 120 x 150, Happy in 200 x 240, enraged Happy in 250 x 300,
  and each Krazy Kobold in 104 x 112 (up to 8 of them, in two rows).
- Sprites stand on the bottom edge of their slot, so leave the feet at the bottom of the image.
- Pixel art: draw it small (say 48 x 48) and tell Claude, so it gets scaled up with sharp pixels instead of smoothed.
- Dead combatants are drawn darkened automatically; no separate art needed.
- The name and class are written over the bottom of the sprite (with a soft shadow), so keep the
  important bits (faces!) out of the bottom third or so.

## Fonts (`assets/fonts/`)

- **New Rocker** (`NewRocker-Regular.ttf`, picked by Ted on Nov 1): names, headings, menus, box labels,
  HP numbers and floating numbers. License: SIL Open Font License, `LICENSE-NewRocker-OFL.txt`.
- **Fondamento** (`Fondamento-Regular.ttf`): the narration, readable but still stylized. License: SIL Open
  Font License, `LICENSE-Fondamento-OFL.txt`. To try another, change `NARRATION_FONT` near the top of
  `Slayer_Window.py`.
- **DejaVu Sans / Sans Mono**: the click hints and the ASCII title art. License: `LICENSE-DejaVu.txt`.

All three come from Google Fonts / the DejaVu project. Both licenses allow shipping the fonts with the game, as long as the license files stay alongside.
The window version ships its own fonts because a browser has none of your system fonts.
