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

Tips:
- PNG with a transparent background.
- Draw it big; the game scales it down to fit its slot and keeps the shape (it never stretches).
  Heroines fit in a 104 x 104 box, the dwarves in 120 x 150, Happy in 200 x 240, enraged Happy in 250 x 300.
- Sprites stand on the bottom edge of their slot, so leave the feet at the bottom of the image.
- Pixel art: draw it small (say 48 x 48) and tell Claude, so it gets scaled up with sharp pixels instead of smoothed.
- Dead combatants are drawn darkened automatically; no separate art needed.

## Fonts (`assets/fonts/`)

DejaVu Sans and DejaVu Sans Mono, placeholders until a real font is picked. Their license
(free to use and share, with the license file kept alongside) is `LICENSE-DejaVu.txt`.
The window version ships its own fonts because a browser has none of your system fonts.
