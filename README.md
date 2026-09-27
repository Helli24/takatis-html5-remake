# Takatis — Reverse Engineering und Browser-Remake

Analyse des Shoot-'em-ups **"Takatis – A Tribute To Manfred Trenz"** (Poke53280, Version 1.2,
Januar 2002, C++ / DirectX 7 / FMOD) und ein spielbares Remake im Browser, das die
Originaldaten verwendet.

> **Privates Repo.** Das Spiel ist Freeware, aber `extracted/Copyright.txt` verbietet
> ausdrücklich das Verändern des Programms und die anderweitige Verwendung von Dateien,
> Grafiken und Sounds ohne schriftliche Genehmigung von Poke53280. Die Entwickler sind
> weiterhin aktiv (winterworks GmbH) und planen laut ihrer Webseite ein Steam-Re-Release.
> Dieses Repo darf deshalb **nicht öffentlich** werden. Für eine Veröffentlichung käme nur
> der Code ohne Spieldaten in Frage, und selbst dann besser erst nach Rückfrage bei den
> Autoren.

## Aufbau

| Ordner | Inhalt |
|---|---|
| `Takatis Setup V1_2.exe` | Originalinstaller, Quelle von allem |
| `extracted/` | die 203 Dateien aus dem Installer, statisch entpackt |
| `tools/takatis.py` | Toolkit: Installer-Entpacker, Bild-Entschlüsselung, WAV-Reparatur, Level-Parser und -Writer, PNG-Renderer |
| `tools/xfile.py` | Parser für die DirectX-`.x`-Modelle der Endgegner |
| `game/template.html` | Quelltext des Remakes (Engine, Menüs, Gegner, Bosse) |
| `game/build.py` | baut daraus `game/takatis.html` mit allen eingebetteten Daten |
| `game/patch_*.py` | dokumentierte Einzelschritte der Entwicklung |
| `viewer/takatis-analyse.html` | Bericht zur Analyse |
| `viewer/template.html` | Quelltext des Level-Atlas |
| `libopenmpt.js`, `libopenmpt.wasm` | Fremdbibliothek (BSD) zum Abspielen der Impulse-Tracker-Musik |

Nicht eingecheckt, weil erzeugbar: `assets/`, `assets_png/`, `render/`,
`game/takatis.html`, `viewer/takatis-level-atlas.html`, `viewer/data.json`.

## Bauen

```bash
python game/build.py        # erzeugt game/takatis.html (ca. 11 MB, alles eingebettet)
```

Voraussetzung sind `extracted/` sowie `assets/` (Sounds und Musik in Standardformaten).
`assets/` wird aus `extracted/` erzeugt, siehe `tools/takatis.py`.

## Erkenntnisse zu den Dateiformaten

* **Installer**: NitroSetup 1.4 mit eigener LZSS-Variante. Flag-Byte MSB zuerst,
  Rückverweis 16 Bit Big-Endian, 12 Bit Distanz, 4 Bit Länge plus 2.
* **Grafiken** (`.gfx`, `.stc`, `.tsa`, `.tsb`): 8-Bit-BMPs, deren Bildzeilen permutiert
  **und** horizontal gespiegelt sind. Die Permutationstabelle ist `Level/Levelinfos.tsf`:
  Zeile k enthält eine Permutation von 1..k für Bilder der Höhe k. Transparenz ist reines Grün.
* **Sounds** (`.sfx`, `.spc`): RIFF-WAV mit umbenannten Chunks, `WAVEfmt ` → `LOSTsfx `
  und `data` → `twew`.
* **Musik** (`.trk`): unveränderte Impulse-Tracker-Module.
* **Endgegner** (`3D/*.a01` usw.): DirectX-`.x`-Dateien im Textformat, Skins als BMP ohne
  Verschlüsselung.
* **Level** (`.lvl`):
  ```
  u8   screens           Levellänge in Bildschirmen zu 640 px
  u8   speed             Start-Scrollgeschwindigkeit in px/Frame
  u8[13][screens*10+10]  Layer A, Parallax-Hintergrund, halbe Geschwindigkeit, Tileset NN.tsb
  u8[13][screens*20]     Layer B, Vordergrund, Tileset NN.tsa
  u32  count
  { u32 type; u32 x; i32 y; u32 param; u8 minDifficulty; u8 pad[3]; } objects[count]
  ```
  Kacheln sind 32×32, ein Tileset hat 10×10 Kacheln, Index 0 ist leer.

## Erkenntnisse aus dem Maschinencode

Adressen beziehen sich auf `extracted/Takatis.exe`.

* `0x40c760` Gegner-Init: pro Typ Energie (`+0x20`), Größe (`+0x18/+0x1c`),
  Bilderzahl (`+0x3c`), Bildverzögerung (`+0x44`), Punkte (`+0x64`).
* `0x4856c0` Bewegungsmuster: 64 Einträge zu 320 Byte, je eine Liste aus
  (dx, dy, Dauer). Dauer −1/−2 hält, −3 wiederholt, −4 setzt zurück.
* `0x40a260` Gegner-Update: Schussverhalten pro Typ. Türme feuern alle 90/70/40 Bilder
  je nach Schwierigkeit in drei festen Richtungen, der Spinner nur im Animationsbild 1
  mit einer Chance von 1 zu 11.
* `0x40f3d0` Schuss-Konstruktor, `0x41e570` Kollision und Schaden.
  Gegner-Energie ist Feld `+0x20` in einem flachen Array zu 124 Byte je Eintrag bei
  `0x4948bc`, der Schaden steht im Schuss-Feld `+0x5c`.
* Schadenswerte: Spread 3 bei 1/3/5/7 Schüssen je Stufe, Laser 5/4/3/3 bei zwei Schüssen,
  Bounce 4 groß und 3 klein, Powerline 8, Rakete 100, Beam 10/15/20/25.
  Gegnerschüsse tragen den Wert 10 im Schadensfeld, beim Spieler ziehen sie aber pauschal 1 Energie ab (siehe unten).
* **Bildrate** (`0x418102`): `Flip` mit `DDFLIP_WAIT`, danach Warten bis mindestens 10 ms seit Framebeginn
  (`GetTickCount`, Wert bei `0x485698`). Das Spiel läuft also mit der Bildwiederholrate, höchstens etwa 100 fps.
  Die FAQ empfiehlt 75 Hz, das Remake läuft deshalb fest mit 75 fps. Alle Frame-Angaben hier beziehen sich darauf.
* **Schiff** (`0x41ced0`): 3 px pro Frame, x 0..591, y 17..398 (Bildschirm). Gegensätzliche Tasten heben die
  Bewegung ganz auf. Neigungszähler −10..10, Frame 0 neutral, 1/2 sinken, 3/4 steigen.
* **Energie** 3. Gegnerschuss −1, Rammen −2, Tod erst unter 0, also beim vierten Schusstreffer. Keine
  Unverwundbarkeit nach Treffer oder Respawn. Gerammte Gegner werden entfernt und geben einfache Punkte.
  Wände töten sofort, auch mit Schild. Trefferbox für Gegnerschüsse und Items ist das volle Rechteck 49×31.
* **Schild** 1000 Frames, ab 500 blinkt er jedes 2., ab 750 jedes 4. Frame. Er schluckt Schüsse und zerstört
  gerammte Gegner, nur die Typen 26, 27 und 39 töten trotzdem.
* **Tod** (`0x41c820`): 400 Frames Explosionssequenz, dann Leben −1, Raketen −1, Powerlines −1. Game over bei 0
  Leben. Neustart am Levelanfang oder, wenn schon überschritten, bei der Levelhälfte. Das Scrolling läuft weiter.
* **Start** (`0x420bf4`): Spread 1, Laser 0, Bounce 0, 5 Raketen, 3 Powerlines. Leben 5/4/3 je nach
  Schwierigkeit. Stage geschafft: +1 Leben, keine Punkte. Endgegner: +10000.
* **Waffen**: Spread und Bounce feuern einmal pro Tastendruck ohne Abklingzeit, der Laser feuert Dauerfeuer alle
  24/18/12/6 Frames. Tasten 1 Spread, 2 Bounce, 3 Laser, Num 0 schaltet weiter. Der Beam lädt 2 pro Frame bis 248,
  die Stufen liegen bei >40, >110, >180 und =248. Rakete: Ziel ist der erste passende Gegner der Liste, Lenkung
  pro Achse 6 px oder 1 px pro Frame. Powerline: 13 Segmente über die ganze Höhe, 15 px pro Frame, 8 Schaden in
  jedem Frame mit Kontakt. Die Laser-Sinuskurve (`0x40fea0`) ist exakt in float32 nachgebaut.
* **Punkte**: Abschuss per Waffe zählt die Punkte des Gegners fünfmal (die Addition steht in der
  Explosionsschleife `0x41f250`), Rammen einmal. Items: Waffe +1000, Rakete +100, Powerline +200, Schild +500,
  1UP +2500. Zufallsdrops bei `rand()%3500`: ≤20 Schild, ≤100 Rakete, ≤140 Powerline.
* **Sound-IDs** (Ladefunktion bei `0x414a00`): 0 Explosion, 1 Spread, 2 Beam, 3 Hit, 5 Rocket, 6 Laser, 7 Bounce,
  0x11 Shield, 0x12 BigExplosion, 0x13 Powerline, 0x15 Morph, 0x16 Laser2, 0x17 Bigshot, 0x18 Trigger,
  0x19 Klippikloppi, Sprache 9 online, 0xa bounce, 0xb spread, 0xc laser, 0xd homing, 0xe line, 0xf shield,
  0x10 1up, 0x14 bigone.
* Es gibt **keine** kachelbasierte Kollision. Die Level-Arrays werden nur von der
  Zeichenfunktion `0x42bdb0` gelesen, das Original prüft Pixel auf der DirectDraw-Surface.

## Stand des Remakes

Alle 12 Stages mit Original-Karten, -Bewegungsmustern, -Schadenswerten und -Gegnerverhalten,
sechs 3D-Endgegner über WebGL, komplettes Menüsystem mit sechs Speicherplätzen, Musik über
libopenmpt, Original-Sounds und -Sprachsamples.

Nicht aus dem Original rekonstruiert, sondern selbst entworfen: das Verhalten der Endgegner
sowie einige Detailregeln bei Magnet und Faller.

## Der Patch für das Original

`extracted/Takatis_patched.exe` ist die Original-EXE mit entfernter Anforderung
`DDSCAPS_VIDEOMEMORY` an vier Stellen. Ohne diesen Patch scheitert das Spiel auf
Windows 11 beim Anlegen der Scroll-Surface.
