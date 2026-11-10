# Shining Soul II Build Calculator

Plan a Shining Soul II (GBA, 2003) character: class, level, stat and skill points, six equipment slots with
+N / enchantment / element, set bonuses, the full stat sheet, and damage against any monster (weapon hits,
charge attacks, spells, soul attacks, and the monster's hits on you).

Every number comes from a datamine of the game's own code (local-only workspace `../_ss2_extract`, never
shipped here). Rebuild the data: `python tools/build_data.py` (writes `data.js`, `assets/icons/`,
`precache-list.json` and stamps the cache-bust tokens). Preview: `node tools/serve.mjs`, stop it when done.
One-time per clone: `git config core.hooksPath .githooks`.

Fan-made, not affiliated with Atlus or Sega.
