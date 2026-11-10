# SS2 Build Calculator — Progress

Cross-session log. Data source: `../_ss2_extract` (EXTRACT_PLAN.md § Start here; player summaries CHARACTERS.md,
SKILLS.md, DAMAGE.md, EQUIPMENT.md). Build: `python tools/build_data.py` (guardrails: set members, spells, bonus
kinds and icon sheets must resolve or data.js is not written).

## Current state (2026-11-10, first build)
- Build view: class (9, incl. the hidden one), level 1-200, secret name, stat points (4/level, caps 500/500/500/333),
  skill points (1/level, n -> n+1 costs n+1), 6 gear slots with +0..+20, enchantment (allowed per slot), element
  (weapons without one), one active set bonus, requirement warnings.
- Stat table Base | Gear | Skill | Total: STR DEX INT VIT, HP, SP, Attack, Defense, Critical, Block, Walking speed,
  6 resistances; attack delay and crit chance line.
- Damage vs a chosen monster: hit range, crit, hit chance, hits to kill, charge levels with SP, spell levels with
  SP (spell books), soul attack, the monster's damage and hit chance on you.
- Browse: spells, souls, sets, enchantments, bonus kinds, monsters, rules.

## Backlog
- P1: party buffs (Protect, Resist, Bless, Battle Cry aura, Magic Shield, Speed) as toggles; Armor Break /
  Intimidate on the target; Counter Strike / Backstab / Anti-Air toggles; Blast + Summon DEF route; multiplayer
  soul bonus; hard-mode monster table; SP recovery and HP regen rates; starting gear on class pick.
- P1: item detail pages (where it drops, shop, smith recipe); build share link.
- P2: class portraits (portrait banks 115-120, 198-200, 287: mapping open); skill-screen art for skill names.
- Open game questions (in-game checks) live in the extract: EXTRACT_PLAN.md § Open.
