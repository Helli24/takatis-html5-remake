# Making of: how Claude rebuilt Takatis from the EXE

This remake was made by **Claude** (Anthropic's AI model, working in Claude Code). A human
started the project, decided what to do next, played every version and reported what felt
different from the original; Claude did the analysis and wrote the code. This report describes
what was actually done — and what was *not* done.

## The starting point

The only input was the original installer, `Takatis Setup V1_2.exe` (freeware, 2002). There was
no source code, no documentation of the file formats and no running copy of the game:

* Claude worked in a Linux container without Windows or any emulator. **The original game was
  never run by Claude**, and no frames or videos of the original were captured or analysed.
* The human could not get the original running properly on Windows 11 either (a DirectDraw flag
  is the likely cause, see the patch at the end).

So everything below comes from reading files and machine code — static analysis only.

## Step 1: unpacking the data

* **Installer**: a NitroSetup 1.4 archive with its own LZSS variant. Claude worked out the flag
  byte order, the back-reference layout (16 bit big endian, 12 bit distance, 4 bit length) and
  wrote an unpacker (`tools/takatis.py`). It yields the 200 original files byte for byte.
* **Graphics** (`.gfx`, `.stc`, `.tsa`, `.tsb`): 8-bit BMPs whose rows are scrambled and mirrored.
  The permutation table turned out to be the innocent-looking `Level/Levelinfos.tsf`.
* **Sounds**: WAV files with renamed chunks (`LOSTsfx `, `twew`). **Music**: plain Impulse
  Tracker modules. **Bosses**: DirectX `.x` models in text form.
* **Levels** (`.lvl`): two tile layers and an object list; the layout was worked out from the
  files themselves, and the code that uses them (object activation, difficulty flags) confirmed
  it later.

## Step 2: reading the machine code

`Takatis.exe` is a 32-bit MSVC build (C++, DirectX 7, FMOD). Claude disassembled it with the
Capstone library into a listing of about 217,000 lines and built a few small helpers for itself:

* an **annotated listing** that resolves imported functions (DirectDraw, DirectSound, FMOD,
  `GetAsyncKeyState`, …), string references and thunks;
* a small **"lifter"** that turns instruction sequences into readable pseudo-code — calls with
  their arguments, conditions and assignments — so a routine can be read like C;
* a growing **table of names** for global variables (`shipX`, `score`, `scroll`, the state
  variable, …) as their meaning became clear.

With these, the game was read routine by routine: the main loop and its twelve program states
(title, menu, options, highscores, credits, the game itself, …), the per-frame routine, the enemy
init and update code, the shot list, collisions, particles, explosions, the level end, saving,
the console with its cheats, and so on. More than 300 distinct addresses of the EXE are
referenced in the code comments and the README, so every rule can be traced back to the place
it came from.

Wherever possible, values are **read from the EXE at build time** instead of being copied by
hand: the enemy table (energy, size, animation, points), the movement patterns, the font widths,
the help pages, the credits text, the stage intro texts and more. `game/build.py` reads them
straight out of the unpacked `Takatis.exe`.

## Step 3: rebuilding it for the browser

The remake is a single HTML file with JavaScript and an embedded copy of the original data.
It follows the original closely:

* the **frame order** of the original main loop (background, parallax layer, presses, foreground
  with the tile collision pass, enemies, boss, ship, explosions, particles, shots, HUD,
  collisions, level end);
* DirectDraw's quirks — for example `BltFast` without a clipper draws nothing at all when a
  sprite does not fit on screen completely, 16-bit colour with the green colour key, and the
  blocking gamma fades;
* **pixel-exact collision** like the original's routine, based on the same colour key;
* the **menus and screens** rebuilt from their state handlers, including oddities such as a menu
  cursor that is shared between screens and an Escape "latch" that skips all later fades.

### The bosses: translated machine code

The six bosses are one large routine of about 4,600 x86 instructions that also drives Direct3D.
Rewriting that by hand would have meant many guesses, so Claude wrote a **translator**
(`game/bossvm.py`): at build time it converts each x86 instruction of the routine into a line of
JavaScript that works on an emulated copy of the EXE's data sections. The boss logic in the
remake is therefore the original machine code, just executed differently. Its Direct3D 7 calls
are replaced by WebGL code that reproduces what DX7's fixed-function pipeline did (per-vertex
lighting with one directional light, the materials from the model files, wrapped textures,
16-bit output, D3D's pixel centres).

## Step 4: checking the result

Since the original could not be run, checking happened in two ways:

* **Automated tests** (`tests/`): headless Chromium loads the game and a bot plays all 12 stages,
  fights a boss, walks through every menu, saves and loads a game and types console cheats; the
  tests fail on any error. Claude also looked at screenshots of the remake to check screens and
  effects.
* **A human playing it.** Every report ("the presses flash when hit", "I can switch to a weapon I
  don't have", "an enemy spawns right in front of me after dying", "this claw dropped two
  powerlines") was traced back to the machine code. Some were bugs in the remake and got fixed;
  others turned out to be exactly how the original behaves (the powerline claw really does drop
  a second powerline).

The project took two rounds. An earlier attempt with an earlier Claude model produced a playable
game, but many values were estimated and the bosses did not work. The second round, with a newer
Claude model, went through the EXE systematically and replaced the estimates with the original
logic, then audited the main loop state by state.

## Honest limits

* **Readability.** The remake's source (`game/template.html`, about 110 KB) is dense, and its
  structure mirrors the original's machine code rather than a clean modern design. It is
  commented with the EXE addresses it comes from, which helps to trace things, but it is not the
  code a human would have written. The translated boss routine is not meant to be read by humans
  at all. Working on it further is realistic mainly with an AI assistant — that dependency is
  real.
* **Performance.** The game runs at a fixed 75 fps and is light for today's browsers, including
  the emulated boss routine, but nothing was optimised beyond that.
* **Deliberate differences**: fixed 75 fps instead of the monitor's refresh rate, no joystick yet,
  "Quit Game" returns to the start screen, a browser font in the console, a few small details
  listed in the README, and some helpers the original does not have (pause, skip stage, volume
  keys).
* **Unverified details.** Things that can only be judged by eye or ear next to the original —
  e.g. the exact balance of sound effects against the music — were taken from the formulas in
  the code but never compared with the running original.

## The patch for Windows 11

The original requests `DDSCAPS_VIDEOMEMORY` for four DirectDraw surfaces, which makes creating
the scroll surface fail on Windows 11. `tools/prepare.py` writes a patched copy of the EXE with
that flag cleared. Claude could not try it on Windows itself.
