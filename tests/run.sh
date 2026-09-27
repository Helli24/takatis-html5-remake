#!/bin/sh
# Runs all browser tests against game/takatis.html (build it first with python game/build.py).
# Needs Node.js and Playwright with Chromium. Screenshots go to tests/out/.
# Every test ends with "no errors" when the page threw no error; run.sh reports the ones that did not.
cd "$(dirname "$0")/.."
HTML="$PWD/game/takatis.html"; OUT="$PWD/tests/out"; mkdir -p "$OUT"
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
fail=0
run() { name=$1; shift
  if node "tests/$name.js" "$HTML" "$OUT" "$@" > "$OUT/$name.log" 2>&1 && tail -1 "$OUT/$name.log" | grep -q "^no errors$"
  then echo "ok    $name"; else echo "FAIL  $name (see tests/out/$name.log)"; fail=1; fi; }
run stages                          # all 12 stages played through by a bot
run mechanics                       # movement, energy, weapons, items
run laser                           # laser curve and damage
run press                           # presses cannot be damaged
run bossfight 1 900,1500,2600 1 1200   # boss 1: fight, destruction with F4, save screen, next stage
run shell                           # start sequence, title, all menus, in-game overlays, game over, name entry
run save                            # save after boss 1, load the slot from "new game"
run console                         # console commands and cheats
exit $fail
