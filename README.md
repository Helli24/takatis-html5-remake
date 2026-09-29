# Takatis — HTML5 Remake

A faithful browser remake of the shoot 'em up **"Takatis – A Tribute To Manfred Trenz"**
(Poke53280, version 1.2, January 2002, C++ / DirectX 7 / FMOD), a German freeware homage to
Manfred Trenz's Katakis. The remake runs the original levels, graphics, music and sounds in any
current browser, and its game logic is rebuilt from the original executable, value by value.

<!-- Play online: https://… (add the link once the game is hosted) -->

## Credits

**Takatis – A Tribute To Manfred Trenz** © 2002 Poke53280:

| | |
|---|---|
| Programming | Heiko Kalista (TheWanderer) |
| Graphics, music, level editor | Jörg Matthias Winterstein (Eiswuxe) |
| 3D models | Michael Matzka (Skyrider) |
| Voices | Alexandra Hertstein |
| Intro voice | Heiko Kalista |
| Voice recording | Seb Kugler @ Antiserum Studio |

The complete credits and greetings of the original can be seen in the game (menu → Credits).

The original graphics, levels, 3D models, music and sounds are used with the kind permission of
Jörg Matthias Winterstein. They remain the property of their authors and are not covered by any
licence of this repository.

Music playback uses [libopenmpt](https://lib.openmpt.org/) (BSD licence, see
`lib/LICENSE-libopenmpt.txt`).

## How this remake was made

The remake was created with the help of AI: Claude Code (Anthropic) unpacked the installer,
disassembled `Takatis.exe` and rebuilt the game logic from the machine code step by step —
enemy behaviour, weapons, level end, menus, console and cheats. The boss routine is translated
directly from the machine code into JavaScript. A human steered the project, played and tested it
and reported every difference until it played like the original.

## Playing

Open `game/takatis.html` (after building it, see below) in a browser, click into the page and
play with the keyboard. Saved games, highscores and options are stored in the browser's
`localStorage`.

| Key | Action |
|---|---|
| Arrow keys | fly |
| Space | primary weapon |
| Ctrl | charge the beam |
| Shift | rocket |
| Enter | powerline |
| 1 / 2 / 3, numpad 0 | spread / bounce / laser, next weapon |
| F1 / F2 / Esc | help / volume / quit (as in the original) |
| Tab | console (as in the original, try `help`) |
| P, F4, F9, M, − / + | remake helpers: pause, skip stage, info mode, sound off, music volume |

The game texts are German, as in the original.

## Repository

| Path | Contents |
|---|---|
| `Takatis Setup V1_2.exe` | the original installer (version 1.2), the only input of the build |
| `tools/takatis.py` | toolkit: installer unpacker, image decryption, WAV repair, level parser and writer, PNG renderer |
| `tools/prepare.py` | unpacks the installer into `extracted/` and writes a patched `Takatis_patched.exe` (see below) |
| `tools/xfile.py` | parser for the DirectX `.x` models of the bosses |
| `game/bossvm.py` | translates the boss routine `0x4036d0`–`0x4086e1` of the EXE into JavaScript at build time |
| `game/template.html` | source of the remake (engine, menus, enemies, bosses) |
| `game/build.py` | builds `game/takatis.html` with all data embedded |
| `tests/` | browser tests with Playwright, run with `tests/run.sh` |
| `lib/` | libopenmpt (BSD) for the Impulse Tracker music |

## Building

```bash
pip install pefile capstone
python game/build.py        # writes game/takatis.html (about 14 MB, everything embedded)
```

The first build unpacks the installer into `extracted/`. The result is one self-contained HTML
file that can be opened locally or put on any static web host (e.g. as `index.html`).

## Testing

```bash
tests/run.sh                # needs Node.js and Playwright with Chromium
```

The tests load `game/takatis.html` in Chromium, drive the game with keyboard events and helper
functions of the page (`__tick`, `__dbg`, `__lv`, `__startBoss`) and check that no error occurs:
all 12 stages played by a bot, game mechanics, laser, presses, a boss fight with saving, all
menus with game over and name entry, loading a saved game, console and cheats. Screenshots and
logs go to `tests/out/`.

## Findings: file formats

* **Installer**: NitroSetup 1.4 with its own LZSS variant. Flag byte MSB first, back reference
  16 bit big endian, 12 bit distance, 4 bit length plus 2.
* **Graphics** (`.gfx`, `.stc`, `.tsa`, `.tsb`): 8-bit BMPs whose rows are permuted **and**
  mirrored horizontally. The permutation table is `Level/Levelinfos.tsf`: row k holds a
  permutation of 1..k for images of height k. Transparency is pure green.
* **Sounds** (`.sfx`, `.spc`): RIFF WAV with renamed chunks, `WAVEfmt ` → `LOSTsfx ` and
  `data` → `twew`.
* **Music** (`.trk`): unmodified Impulse Tracker modules.
* **Bosses** (`3D/*.a01` etc.): DirectX `.x` files in text format, skins as unencrypted BMPs.
* **Levels** (`.lvl`):
  ```
  u8   screens           level length in screens of 640 px
  u8   speed             initial scroll speed in px/frame
  u8[13][screens*10+10]  layer A, parallax background, half speed, tileset NN.tsb
  u8[13][screens*20]     layer B, foreground, tileset NN.tsa
  u32  count
  { u32 type; u32 x; i32 y; u32 param; u8 minDifficulty; u8 pad[3]; } objects[count]
  ```
  Tiles are 32×32, a tileset has 10×10 tiles, index 0 is empty.

## Findings: machine code

Addresses refer to `extracted/Takatis.exe`.

* `0x40c760` enemy init: per type energy (`+0x20`), size (`+0x18/+0x1c`), number of frames
  (`+0x3c`), frame delay (`+0x44`), points (`+0x64`).
* `0x4856c0` movement patterns: 64 entries of 320 bytes, each a list of (dx, dy, duration).
  Duration −1/−2 holds, −3 repeats, −4 resets.
* `0x40a260` enemy update: firing behaviour per type. Turrets fire every 90/70/40 frames
  depending on the difficulty in three fixed directions, the spinner only in animation frame 1
  with a chance of 1 in 11.
* `0x40f3d0` shot constructor, `0x41e570` collision and damage. Enemy energy is field `+0x20` in
  a flat array of 124 bytes per entry at `0x4948bc`, the damage is in shot field `+0x5c`.
* Damage: spread 3 with 1/3/5/7 shots per level, laser 5/4/3/3 with two shots, bounce 4 big and
  3 small, powerline 8, rocket 100, beam 10/15/20/25. Enemy shots carry 10 in the damage field,
  but take a flat 1 energy from the player (see below).
* **Frame rate** (`0x418102`): `Flip` with `DDFLIP_WAIT`, then a wait until at least 10 ms have
  passed since the start of the frame (`GetTickCount`, value at `0x485698`). The game therefore
  runs at the display refresh rate, at most about 100 fps. The FAQ recommends 75 Hz, so the
  remake runs at a fixed 75 fps. All frame counts here refer to that.
* **Ship** (`0x41ced0`): 3 px per frame, x 0..591, y 17..398 (screen). Opposite keys cancel the
  movement completely. Tilt counter −10..10, frame 0 neutral, 1/2 sinking, 3/4 rising.
* **Energy** 3. Enemy shot −1, ramming −2, death only below 0, i.e. with the fourth shot hit. No
  invulnerability after a hit or a respawn. Rammed enemies are removed and give single points.
  Walls kill at once, even with the shield. The hit box for enemy shots and items is the full
  49×31 rectangle.
* **Shield** 1000 frames, from 500 on it blinks every 2nd, from 750 on every 4th frame. It
  swallows shots and destroys rammed enemies, only types 26, 27 and 39 still kill.
* **Death** (`0x41c820`, end at `0x41c995`): a counter of 400 runs out, then lives −1, rockets
  −1, powerlines −1, explosions, particles and shots cleared, a fade out with 5 ms per step,
  then the stage intro or game over (`0x4966bc`). Restart at the start of the level or, if
  already passed, at its middle. The scrolling goes on.
* **Start** (`0x420bf4`): spread 1, laser 0, bounce 0, 5 rockets, 3 powerlines. Lives 5/4/3
  depending on the difficulty. Stage cleared: +1 life, no points. Boss: +10000.
* **Weapons**: spread and bounce fire once per key press without cooldown, the laser fires
  continuously every 24/18/12/6 frames. Keys 1 spread, 2 bounce, 3 laser, numpad 0 cycles. The
  beam charges 2 per frame up to 248, the levels are at >40, >110, >180 and =248. Rocket: the
  target is the first matching enemy of the list, steering per axis 6 px or 1 px per frame.
  Powerline: 13 segments over the full height, 15 px per frame, 8 damage in every frame with
  contact. The laser sine curve (`0x40fea0`) is rebuilt exactly in float32.
* **Points**: a kill by weapon counts the enemy's points five times (the addition sits in the
  explosion loop `0x41f250`), ramming once. Items: weapon +1000, rocket +100, powerline +200,
  shield +500, 1UP +2500. Random drops with `rand()%3500`: ≤20 shield, ≤100 rocket,
  ≤140 powerline. Claws always drop the item they carry; the rocket claw adds 3 rockets, the
  powerline claw 1 powerline (`0x41f542`).
* **Sound IDs** (loader at `0x414a00`): 0 explosion, 1 spread, 2 beam, 3 hit, 5 rocket, 6 laser,
  7 bounce, 0x11 shield, 0x12 big explosion, 0x13 powerline, 0x15 morph, 0x16 laser2, 0x17
  bigshot, 0x18 trigger, 0x19 klippikloppi; speech 4 intro, 8 cheat, 9 online, 0xa bounce,
  0xb spread, 0xc laser, 0xd homing, 0xe line, 0xf shield, 0x10 1up, 0x14 bigone.
* **Level objects**: the y coordinate is a screen coordinate and includes the 16 px of the top
  HUD bar. An object becomes active (`0x40a2ca`) when its x position passes the window 635..640 px
  ahead of the scroll position and its difficulty flag matches, and starts at x=640. The objects
  keep the order of the level file (the enemy array), which is not sorted by x. They are moved,
  drawn and checked in that order (e.g. which target a rocket marks last, which enemy a shot
  hits first).
* **Speed triggers** (`0x40b326`): types 34..38 set the scroll speed to 1..5, right when they
  reach the right edge. The end of the level follows from the scroll position alone. Stage 4-1
  scrolls backwards with −2 from position 4270 and forwards again with 2 from 2970
  (`0x41575f`).
* **Presses** (types 26/27, 64×256, energy 10000) move only by their movement pattern (19–22).
* **HUD** (`0x41c34c`): weapon levels as `ws.gfx` blocks 7 px apart at x=122 (spread), 222
  (bounce), 322 (laser); rockets at x=422, powerlines at x=522.
* **Enemies** (update `0x40a260`, init `0x40c760`): `build.py` reads the init values (energy,
  size, animation, points) straight from the EXE. Animation with a frame counter and an optional
  back and forth (types 1, 15, 25, 28, 29, 30). Cooldowns start at 0 when an enemy appears.
  Some attacks depend on the frame counter: elevator (25) at the end of its forward run (every
  280 frames), bumper (30) at frame 1, mine layer (24) at frame 4, time bomb (31) once after
  600 frames. Objects 3–9 are claws that carry an item of their own (+8/+42). Type 13 is the
  circuit, 16 the magnet (path 18, follows the ship, sticks to it and slows it to 1 px/frame).
  Fallers (17) drop at 6 px/frame after 30 frames of shaking. Path counter −2 means chasing at
  2 px/frame. Enemy shots drift left with (speed−1). Every enemy except 13, 26, 27 is destroyed
  when its rectangle overlaps a foreground tile.
* **Collision** (`0x412f50`): pixel exact. Two shapes touch where neither source pixel has the
  colour 0x07E0 (green, fixed at `0x485644`). That is how the original tests the ship against
  walls and enemies, and shots and the powerline against walls and enemies (rockets only by
  their rectangle). Enemy shots and items hit the ship by the 49×31 rectangle, enemies crash
  into tiles by their rectangle. An enemy's shape is the source rectangle of its last blit at
  its real x position (beyond the left edge it therefore lies too far left), above the screen at
  y=0 with the rectangle starting at −y. The remake builds masks from sprites and tilesets for
  this.
* **Display**: the game runs at a fixed 640×480 in 16 bit (`0x485648`). GDI truncates the bitmap
  colours to RGB565 when copying, the colour key of all sprites and tiles is the green mask of
  the pixel format (`0x412770`). Nearly pure greens are therefore transparent too (4 pixels in
  `Lasersmoke`, 14 in `03.tsb`). `build.py` converts all colours accordingly. Which surfaces get
  a key is at `0x41a789`.
* **Frame order** (`0x41575a`/`0x41c820`): the background picture (`NN.stc`) from offset
  `0x49406c`, which moves 1 px per frame from scroll speed 3 on (not in 1-2); scroll position +
  speed, then the level routine `0x42bdb0`: parallax layer (tsb, half speed), enemy routine pass
  1 (presses only), boss of stage 2-2, foreground (tsa) with the tile pass (ship, shots and
  enemies against every tile), ship speed back to 3, enemy routine pass 0 (all other enemies),
  boss of the other stages. Then the ship or the death sequence, explosions, particles, shot
  list, HUD, collisions (`0x41e570`), level end. Presses therefore come out from behind the
  foreground, all other enemies lie in front of it. The tile pass sees the enemies at their
  position of the previous frame.
* **Enemy blit** (`0x40a61a`, `0x40b5ed`–`0x40b784`): source rectangle of the current animation
  frame before the movement, the right edge is clipped with the old x position (incoming enemies
  lack their step width there). After the movement clipping on the left, at the top and at the
  bottom (limit y=433) without regard to the animation row, only the asteroid works with rows of
  54 px. BltFast has no clipper: a rectangle that does not fit completely draws nothing. Only
  then does the animation advance. A faller shakes via the global `0x49647c`, which every other
  blit clears again. The docked magnet shows frame 6.
* **Bosses** (`0x4036d0`–`0x4086e1`): the whole routine is translated from machine code to
  JavaScript and runs on emulated memory (`.rdata`/`.data` from the EXE). The image is rendered
  into a 320×270 surface with a z-buffer: projection 45°, aspect 1.333, near 10, far 2000, one
  directional light (1,−1,1), no ambient light, per-vertex lighting with normalised normals,
  material from the file (diffuse = ambient = faceColor, so 0.584 for boss 3), textures with
  WRAP and linear filtering, result in RGB565. The DX7 loader only takes `MeshNormals` when
  there are as many as vertices, otherwise it computes them itself (`0x42e5d1`). Below 600
  energy (not on easy) boss 5 runs the enemy routine a second time for its tail segments.
* **Effects**: particles (`0x491c20`, types 0–9 with Debris1–5, Smoke, Lasersmoke, Shieldflare,
  Drive) and explosions (`0x494078`, Explosion/Explosion2, BeamExplode, Small_Explosion, with a
  delay) as in the original.
* **Shot list** (`0x492540`): one shared list for player and enemy shots and items; a shot is
  drawn before it moves.
* **Sound** (`0x414d00`): one buffer per sound, playing it again restarts it, all at the same
  volume. Only the shield hum loops.
* **Level end**: phases at `0x49645c` (1 end reached, 2 transition, 3 boss destroyed). The ship
  flies out at 4 px/frame, then `morph`, after 50 frames music and the wave transition (row 430
  of `title.gfx`), after 430 frames a 2 s fade out, +1 life, next stage. Boss stages: "Big one"
  640 px before the end, the scrolling stops, the ship glides to (0,184), the music fades out
  over 100 frames.
* **Stage intro** (`0x416301`): "Get ready" at (160,180) and three lines from the EXE, fade in
  100×6 ms, then a 2 s wait. The intro of 4-1, 5-1 and 6-1 turns a negative scroll speed back
  to 1 (`0x416715`). **Saving** after bosses 1–5 (state 7, `0x423400`), **end sequence** after
  boss 6 (state 10, `0x42a250`, the same level routine with `ot.lvl` and `bigfont.gfx` as tiles).
* **Font**: proportional, width table at `0x484820`, advance width+1, space 10 (+1).
* **Program states** (`0x4936b0`, jump table `0x41815e`): 0 menu `0x420900`, 1 game, 2 start
  sequence `0x429340`, 3 title `0x4203a0`, 4 options `0x420ef0`, 5 help `0x421cc0`, 6 new game
  `0x422520`, 7 save `0x423400`, 8 highscores `0x4243f0`, 9 credits `0x424fd0`, 10 end sequence
  `0x42a250`, 11 joystick `0x42ab60`. The menus poll the keys with `GetAsyncKeyState`, with a
  latch until release (`0x4966ab`) and a shared cursor (`0x4966c0`). It is not reset
  everywhere: after saving in slot 2 and quitting the game, the menu cursor stands on
  "Options".
* **Fades** (`0x4124f0` in, `0x412620` out): 100 gamma steps of n ms, blocking. Escape during a
  fade sets `0x496460`, which is never cleared. Once the start sequence is past step 3
  (`0x494898`), every later fade ends at once. Waits (`0x425bd0`) cannot be skipped. Escape in
  the intro therefore leads straight to the menu, because the title sees the key still held.
* **Start sequence** (state 2): Poke53280, loading, two intro pictures with a speech sample,
  then the title with a waving logo (140 rows, sine) and a starfield. The credits (state 9) run
  over tiles, rails and turrets; their text is stored as 351 lines in the code at `0x426bb8`,
  the help as 5 pages at `0x480e0c`.
* **In the game** (`0x4176dd`): F1 help, F2 volume, Escape the question "Spiel beenden ?" (not
  at game over and not during the stage transition `0x4966dc`), Tab the console. There is no
  pause key.
* **Console** (Tab, `0x401500`–`0x4029af`, input `0x425c50`): only in the game, and it stops the
  game. Nine lines of history and the input "> …" in white system font over `Console.gfx` on the
  frozen screen. Letters and space at most every 150 ms, Return every 500 ms. Commands: `help`,
  `quit`, `infomode on/off`, `bullettime mode on/off` (at least 70 ms per frame instead of 10,
  `0x485698`), `katakis`/`wanderwuxe` (`player2.gfx` or the normal ship), `the nexus`,
  `dosenhalter` (opens the CD drive in the original). Cheats with a speech sample and the cheater
  flag: `the barrens` shield, `silkworm` +5 rockets, `rick dangerous` +5 powerlines,
  `master of puppets` 99 lives, `ping pong`/`we will rock you`/`feuerwuxe` bounce/laser/spread to
  4, `crazy volcanos` harmless volcano balls (the volcanos fire every 15 instead of 50 frames),
  `merry xmas` every kill drops a shield, rocket or powerline, `zerbiebomb` a shot with 11000
  damage out of every enemy, `scott me up beamy` jumps to the end of the level. `pfundi`
  destroys the ship and sets the lives to 1. The title resets volcanos, extras and bullettime.
* **Common end of every frame** (`0x417bb6`, in all states): boss energy bar (only in the game,
  with lives left and no game over), console, info mode (scroll position and speed, count and
  memory of shots, debris, explosions and active enemies, digits from `font2.gfx`),
  "Version 1.2" at the top left of title and menu, then `Flip` and the wait up to 10 ms.
* **Options** without `Options.ini` (`0x419161`): effect on, joystick buttons 0..7, smoke off,
  volumes 100/100. The installer ships no `Options.ini`, so the remake starts with these values.
* **Saved games** `Takatis.SG1`..`SG6`, 48 bytes, every value +0x1966: stage, difficulty,
  weapon, spread, laser, bounce, rockets, powerlines, lives, shield time, score, cheater. After
  boss n the following stage is saved.
* **Highscores** `Highscores.hsl`: 10 entries of 88 bytes with a checksum, default list from
  Poke53280 (100000) to ZFX-Forum (10000). At game over "Game Over" rises from y=441 at 3 px per
  frame, then the name entry follows, or a remark (not enough points, cheater).

## State of the remake

All 12 stages with the original maps, movement patterns, damage values and enemy behaviour,
the six bosses as the translated original routine with 3D rendering via WebGL, effects, level
end, intro, save screen and end sequence as in the original, music via libopenmpt, original
sounds and speech samples.

Start sequence, title, menu, new game, options, help, highscores, credits, the quit question,
game over with name entry and the console are rebuilt from the state handlers, including the
fades and the Escape latch. Saved games, highscores and options live in the browser's
`localStorage`, separately for every browser. The option `0x4966b4` (smoke behind Debris1) is
off at first and can be switched on in the options.

Approximated: joystick (only "Kein Joystick angeschlossen !"), "Quit Game" fades out and
returns to the remake's start screen, the highscore flag effect compares row 0 with 0 instead
of leftover memory, the file checksums are left out, the console uses a browser font instead of
the Windows system font, the frame rate is a fixed 75 fps.

Remake helpers that the original does not have: volumes start at 20 instead of 100, Escape
skips the intro from the Poke53280 logo on (in the original only from the first intro
picture), P pause, F4 skip the stage or destroy the boss, F9 info mode, M sound off, −/+ music
volume.

## The patch for the original

`tools/prepare.py` also writes `extracted/Takatis_patched.exe`: the original EXE with the
`DDSCAPS_VIDEOMEMORY` request removed in four places. Without it the original fails on
Windows 11 when it creates the scroll surface.
