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
| `game/bossvm.py` | übersetzt die Endgegner-Routine `0x4036d0`–`0x4086e1` der EXE beim Bauen in JavaScript |
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
python game/build.py        # erzeugt game/takatis.html (ca. 14 MB, alles eingebettet)
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
* **Tod** (`0x41c820`, Ende bei `0x41c995`): Zähler 400 läuft ab, dann Leben −1, Raketen −1, Powerlines −1,
  Explosionen, Partikel und Schüsse gelöscht, Abblenden mit 5 ms je Stufe, danach Stage-Intro oder Game over
  (`0x4966bc`). Neustart am Levelanfang oder, wenn schon überschritten, bei der Levelhälfte. Das Scrolling läuft
  weiter.
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
  0x19 Klippikloppi, Sprache 4 Intro, 8 Cheat, 9 online, 0xa bounce, 0xb spread, 0xc laser, 0xd homing, 0xe line, 0xf shield,
  0x10 1up, 0x14 bigone.
* **Level-Objekte**: Die y-Koordinate ist eine Bildschirmkoordinate und enthält die 16 px der oberen HUD-Leiste.
  Ein Objekt wird aktiv (`0x40a2ca`), wenn seine x-Position das Fenster 635..640 px vor der Scrollposition
  durchläuft und sein Schwierigkeits-Flag passt, und startet bei x=640. Die Objekte bleiben in der Reihenfolge der
  Leveldatei (das Gegner-Array), die nicht nach x sortiert ist. In dieser Reihenfolge werden sie bewegt, gezeichnet
  und geprüft (z. B. welches Ziel eine Rakete zuletzt markiert, welchen Gegner ein Schuss zuerst trifft).
* **Speed-Trigger** (`0x40b326`): Typ 34..38 setzt die Scrollgeschwindigkeit auf 1..5, und zwar sofort beim Erreichen
  des rechten Randes. Das Levelende ergibt sich allein aus der Scrollposition. Stage 4-1 scrollt ab Position 4270
  mit −2 rückwärts und ab 2970 wieder mit 2 vorwärts (`0x41575f`).
* **Pressen** (Typ 26/27, 64×256, Energie 10000) bewegen sich nur über ihr Bewegungsmuster (19–22).
* **HUD** (`0x41c34c`): Waffenstufen als `ws.gfx`-Blöcke im Abstand von 7 px bei x=122 (Spread), 222 (Bounce),
  322 (Laser); Raketen bei x=422, Powerlines bei x=522.
* **Gegner** (Update `0x40a260`, Init `0x40c760`): Die Init-Werte (Energie, Größe, Animation, Punkte) liest
  `build.py` beim Bauen direkt aus der EXE. Animation mit Frame-Zähler und optionalem Hin-und-zurück (Typen 1, 15,
  25, 28, 29, 30). Abklingzeiten starten beim Erscheinen bei 0. Angriffe hängen teils am Frame-Zähler: Aufzug (25)
  am Ende des Vorwärtslaufs (alle 280 Frames), Bumper (30) bei Bild 1, Minenleger (24) bei Bild 4, Zeitbombe (31)
  einmalig nach 600 Frames. Objekte 3–9 sind Greifer, die ein eigenes Item tragen (+8/+42). Typ 13 ist der Circuit,
  16 der Magnet (Pfad 18, verfolgt das Schiff, haftet daran und bremst es auf 1 px/Frame). Faller (17) fallen nach
  30 Frames Wackeln mit 6 px/Frame. Pfad-Zähler −2 bedeutet Verfolgung mit 2 px/Frame. Gegnerschüsse driften mit
  (Tempo−1) nach links. Jeder Gegner außer 13, 26, 27 zerschellt, wenn sein Rechteck eine Vordergrundkachel überlappt.
* **Kollision** (`0x412f50`): pixelgenau. Zwei Formen berühren sich, wo beide Quellpixel nicht die Farbe
  0x07E0 (Grün, fest bei `0x485644`) haben. So prüft das Original Schiff gegen Wände und Gegner, Schüsse und
  Powerline gegen Wände und Gegner (Raketen nur über das Rechteck). Gegnerschüsse und Items treffen das Schiff
  über das Rechteck 49×31, Gegner zerschellen an Kacheln über ihr Rechteck. Die Form eines Gegners ist das
  Quellrechteck seines letzten Blits an seiner echten x-Position (über den linken Rand hinaus liegt sie also zu
  weit links), oberhalb des Bildschirms bei y=0 mit Rechteck ab −y. Das Remake baut dafür Masken aus Sprites
  und Tilesets.
* **Darstellung**: Das Spiel läuft fest in 640×480 mit 16 Bit (`0x485648`). GDI schneidet die Bitmapfarben beim
  Kopieren auf RGB565 ab, Colour-Key aller Sprites und Kacheln ist die Grün-Maske des Pixelformats (`0x412770`).
  Dadurch sind auch fast reine Grüntöne durchsichtig (4 Pixel in `Lasersmoke`, 14 in `03.tsb`). `build.py`
  rechnet alle Farben entsprechend um. Welche Surfaces einen Key bekommen, steht bei `0x41a789`.
* **Ablauf eines Frames** (`0x41575a`/`0x41c820`): Scrollposition + Tempo, dann die Level-Routine `0x42bdb0`:
  Parallax-Ebene (tsb, halbe Geschwindigkeit), Gegner-Routine Durchgang 1 (nur Pressen), Boss von Stage 2-2,
  Vordergrund (tsa) mit dem Kachel-Durchgang (Schiff, Schüsse und Gegner gegen jede Kachel), Schiffstempo
  zurück auf 3, Gegner-Routine Durchgang 0 (alle anderen Gegner), Boss der übrigen Stages. Danach Schiff bzw.
  Todessequenz, Explosionen, Partikel, Schussliste, HUD, Kollisionen (`0x41e570`), Levelende. Pressen kommen
  also hinter dem Vordergrund hervor, alle anderen Gegner liegen davor. Der Kachel-Durchgang sieht die Gegner
  noch an ihrer Position aus dem letzten Frame.
* **Gegner-Blit** (`0x40a61a`, `0x40b5ed`–`0x40b784`): Quellrechteck des aktuellen Animationsbilds vor der
  Bewegung, der rechte Rand wird mit der alten x-Position abgeschnitten (einlaufende Gegner fehlen dort um ihre
  Schrittweite). Nach der Bewegung links abschneiden, oben und unten (Grenze y=433) ohne Rücksicht auf die
  Animationszeile, nur der Asteroid rechnet mit Zeilen zu 54 px. BltFast hat keinen Clipper: ein Rechteck, das
  nicht ganz passt, zeichnet nichts. Erst danach geht die Animation weiter. Ein Faller wackelt über die globale
  Variable `0x49647c`, die jeder andere Blit wieder löscht. Der angedockte Magnet zeigt Bild 6.
* **Endgegner** (`0x4036d0`–`0x4086e1`): Die ganze Routine wird aus dem Maschinencode nach JavaScript übersetzt
  und läuft auf emuliertem Speicher (`.rdata`/`.data` aus der EXE). Das Bild entsteht in einer 320×270-Surface mit
  Z-Buffer: Projektion 45°, Seitenverhältnis 1,333, near 10, far 2000, ein Richtungslicht (1,−1,1), kein
  Umgebungslicht, Licht pro Vertex mit normalisierten Normalen, Material der Datei (Diffuse = Ambient =
  faceColor, Boss 3 also 0,584), Texturen mit WRAP und linearem Filter, Ergebnis in RGB565. Der DX7-Loader nimmt
  `MeshNormals` nur bei gleicher Anzahl wie Vertices, sonst rechnet er sie selbst (`0x42e5d1`). Unter 600 Energie
  (nicht auf leicht) lässt Boss 5 die Gegner-Routine für seine Schwanzsegmente ein zweites Mal laufen.
* **Effekte**: Partikel (`0x491c20`, Typen 0–9 mit Debris1–5, Smoke, Lasersmoke, Shieldflare, Drive) und
  Explosionen (`0x494078`, Explosion/Explosion2, BeamExplode, Small_Explosion, mit Verzögerung) wie im Original.
* **Schussliste** (`0x492540`): eine gemeinsame Liste für Spieler- und Gegnerschüsse sowie Items; ein Schuss wird
  gezeichnet, bevor er sich bewegt.
* **Sound** (`0x414d00`): ein Puffer je Sound, erneutes Abspielen startet ihn neu, alle mit derselben Lautstärke.
  Nur das Schild-Summen läuft in Schleife.
* **Levelende**: Phasen bei `0x49645c` (1 Ende erreicht, 2 Übergang, 3 Boss zerstört). Das Schiff fliegt mit
  4 px/Frame hinaus, dann `morph`, nach 50 Frames Musik und die Wellen-Überblendung (Zeile 430 aus `title.gfx`),
  nach 430 Frames Abblenden in 2 s, +1 Leben, nächste Stage. Boss-Stages: „Big one“ 640 px vor dem Ende,
  Scrolling stoppt, Schiff gleitet nach (0,184), Musik blendet über 100 Frames aus.
* **Stage-Intro** (`0x416301`): „Get ready“ bei (160,180) und drei Zeilen aus der EXE, Einblenden 100×6 ms,
  dann 2 s warten. **Speichern** nach den Bossen 1–5 (Zustand 7, `0x423400`), **Abspann** nach Boss 6
  (Zustand 10, `0x42a250`, dieselbe Level-Routine mit `ot.lvl` und `bigfont.gfx` als Kacheln).
* **Schrift**: proportional, Breitentabelle bei `0x484820`, Vorschub Breite+1, Leerzeichen 10 (+1).
* **Programmzustände** (`0x4936b0`, Sprungtabelle `0x41815e`): 0 Menü `0x420900`, 1 Spiel, 2 Startsequenz
  `0x429340`, 3 Titel `0x4203a0`, 4 Optionen `0x420ef0`, 5 Hilfe `0x421cc0`, 6 Neues Spiel `0x422520`,
  7 Speichern `0x423400`, 8 Highscores `0x4243f0`, 9 Credits `0x424fd0`, 10 Abspann `0x42a250`, 11 Joystick
  `0x42ab60`. Die Menüs fragen die Tasten mit `GetAsyncKeyState` ab, mit einer Sperre bis zum Loslassen
  (`0x4966ab`) und einem gemeinsamen Cursor (`0x4966c0`). Der wird nicht überall zurückgesetzt: Nach dem Speichern
  in Slot 2 steht er nach „Spiel beenden“ im Menü auf „Options“.
* **Blenden** (`0x4124f0` ein, `0x412620` aus): 100 Gamma-Stufen zu n ms, blockierend. Escape während einer Blende
  setzt `0x496460`, das nie zurückgesetzt wird. Ist die Startsequenz über Schritt 3 hinaus (`0x494898`), endet
  danach jede Blende sofort. Wartezeiten (`0x425bd0`) lassen sich nicht überspringen. Escape im Intro führt daher
  direkt ins Menü, weil der Titel die noch gedrückte Taste sieht.
* **Startsequenz** (Zustand 2): Poke53280, Loading, zwei Intro-Bilder mit Sprachsample, dann der Titel mit
  wehendem Logo (140 Zeilen, Sinus) und Sternenfeld. Die Credits (Zustand 9) laufen über Kacheln, Schienen und
  Türme; ihr Text steht als 351 Zeilen im Code bei `0x426bb8`, die Hilfe als 5 Seiten bei `0x480e0c`.
* **Im Spiel** (`0x4176dd`): F1 Hilfe, F2 Lautstärke, Escape die Abfrage „Spiel beenden ?“ (nicht bei Game over
  und nicht im Stage-Übergang `0x4966dc`), Tab die Konsole. Eine Pause-Taste gibt es nicht.
* **Optionen** ohne `Options.ini` (`0x419161`): Effekt an, Joystick-Knöpfe 0..7, Rauch aus, Lautstärken 100/100.
  Die mitgelieferte `Options.ini` besteht aus 13 Nullbytes, das Remake nimmt deshalb die Werte ohne Datei.
* **Spielstände** `Takatis.SG1`..`SG6`, 48 Byte, jeder Wert +0x1966: Stage, Schwierigkeit, Waffe, Spread, Laser,
  Bounce, Raketen, Powerlines, Leben, Schildzeit, Punkte, Cheater. Nach Boss n wird die folgende Stage gespeichert.
* **Highscores** `Highscores.hsl`: 10 Einträge zu 88 Byte mit Prüfsumme, Standardliste von Poke53280 (100000) bis
  ZFX-Forum (10000). Bei Game over steigt „Game Over“ von y=441 mit 3 px pro Frame auf, dann folgt die
  Namenseingabe oder eine Bemerkung (zu wenig Punkte, Cheater).

## Stand des Remakes

Alle 12 Stages mit Original-Karten, -Bewegungsmustern, -Schadenswerten und -Gegnerverhalten,
die sechs Endgegner als übersetzte Originalroutine mit 3D-Darstellung über WebGL, Effekte,
Levelende, Intro, Speicherbildschirm und Abspann wie im Original, Musik über libopenmpt,
Original-Sounds und -Sprachsamples.

Startsequenz, Titel, Menü, Neues Spiel, Optionen, Hilfe, Highscores, Credits, die Abfrage beim
Beenden und Game over mit Namenseingabe sind aus den Zustands-Handlern nachgebaut, samt Blenden
und Escape-Sperre. Spielstände, Highscores und Optionen liegen im `localStorage` des Browsers.
Die Option `0x4966b4` (Rauch hinter Debris1) ist anfangs aus und lässt sich in den Optionen
einschalten.

Angenähert: Joystick (nur „Kein Joystick angeschlossen !“), „Quit Game“ blendet ab und kehrt zum
Startbild des Remakes zurück, der Flaggeneffekt der Highscores vergleicht in Zeile 0 mit 0 statt mit
Speicherresten, die Prüfsummen der Dateien entfallen. Noch offen: die Konsole (Tab) mit
ihren Befehlen.

Hilfen des Remakes, die es im Original nicht gibt: Escape überspringt das Intro schon ab dem
Poke53280-Logo (im Original erst ab dem ersten Intro-Bild), P Pause, F4 Stage überspringen bzw.
Boss zerstören, F9 Infomodus, M Ton aus, −/+ Musiklautstärke.

## Der Patch für das Original

`extracted/Takatis_patched.exe` ist die Original-EXE mit entfernter Anforderung
`DDSCAPS_VIDEOMEMORY` an vier Stellen. Ohne diesen Patch scheitert das Spiel auf
Windows 11 beim Anlegen der Scroll-Surface.
