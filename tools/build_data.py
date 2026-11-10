"""Build the app's runtime artifacts from the local-only Shining Soul II extract.

Reads  ../_ss2_extract/data/{characters,skills,items,combat,world}/*.json   (tools/dec_*.py in the extract)
       ../_ss2_extract/assets/icons_bankNNN.png   (16x16 icon sheets, 16 per row; tools/dec_assets.py --png)
Writes data.js (window.SS2_DATA), assets/icons/bankNNN.png, precache-list.json; then stamps the cache-bust
tokens (../tools/app/stamp_cache.py, rule A-cache-bust).
The extract itself is never copied here (G-extract-not-in-app). Guardrails: every reference (set member, spell,
enchantment kind, icon sheet) must resolve or the build fails and data.js is left as it was.

  python tools/build_data.py [--strict]
"""
import hashlib, json, os, shutil, sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X = os.path.join(os.path.dirname(APP), "_ss2_extract")
D = os.path.join(X, "data")
STRICT = "--strict" in sys.argv
errors, warnings = [], []

# icon field hi byte -> icon sheet (sprite bank); dec_assets.py ICON_OBJ_BANK (FUN_0805F54C)
ICON_OBJ_BANK = [159, 157, 160, 158, 215, 216, 218, 217, 185, 171, 237]
ELEMENTS = ["", "Fire", "Ice", "Thunder", "Light", "Darkness", "Poison", "Strong Poison"]
CLASS_NAMES = ["Warrior", "Sorceress", "Archer", "Dragonute", "Priestess", "Brawler", "Dark Wizard", "Ninja"]


def load(rel):
    with open(os.path.join(D, rel), encoding="utf-8") as f:
        return json.load(f)


def clean(name):
    """Item names carry inline glyph codes ({ICON123}, {SOUL}, {CARD}); keep the readable part."""
    import re
    s = re.sub(r"\{ICON123\}", "Lv", name or "")
    s = re.sub(r"\{[^}]*\}", "", s)
    return s.strip()


used_banks = set()


def icon(v):
    if v is None:
        return None
    obj, fr = v >> 8, v & 0xFF
    if obj >= len(ICON_OBJ_BANK):
        warnings.append("icon field 0x%x has no sheet" % v)
        return None
    b = ICON_OBJ_BANK[obj]
    used_banks.add(b)
    return [b, fr]


def bonuses(lst):
    return [[b["kind"], b["value"]] for b in (lst or [])]


def class_ids(names):
    return [CLASS_NAMES.index(n) for n in names if n in CLASS_NAMES]


# ---------- classes ----------
cls_src = load("characters/classes.json")["classes"]
sk_src = load("skills/skills.json")
classes = []
for c in cls_src:
    group = 6 if c["id"] == 8 else c["id"]
    sk = next(s for s in sk_src["classes"] if s["classId"] == group)
    slots = []
    for s in sk["slots"]:
        slots.append({k: s.get(k) for k in ("slot", "name", "description", "kind", "weapon", "spellId", "effect",
                                            "formula", "perLevel", "conf") if s.get(k) is not None})
        slots[-1]["description"] = clean(slots[-1].get("description", ""))
    classes.append({
        "id": c["id"], "name": c["name"] if c["id"] != 8 else "Dark Wizard (hidden)", "defaultName": c["defaultName"],
        "blurb": c.get("blurb", ""), "skillGroup": group,
        "base": {"STR": c["STR"], "DEX": c["DEX"], "INT": c["INT"], "VIT": c["VIT"]}, "walk": c["walkingSpeed"],
        "skills": slots,
    })

# ---------- spells, souls ----------
spells = []
for s in load("skills/spells.json")["spells"]:
    if not s.get("name"):
        continue
    beh = s.get("behaviour") or {}
    spells.append({"id": s["id"], "name": s["name"], "power": s["power"], "element": s["element"],
                   "sp": s["mpCost"], "effect": beh.get("effect", ""), "perLevel": beh.get("perLevel")})
spell_ids = {s["id"] for s in spells}
souls_src = load("skills/souls.json")
souls = [{"id": s["soulId"], "name": s["name"], "element": s.get("attackElement") or 0,
          "ailment": s.get("statusLevel"), "plain": s.get("plain", "")} for s in souls_src["souls"]]
soul_power = souls_src["meta"]["soulTable"]["powerByLevel"]

# ---------- items ----------
items = []


def add(cat, rec, **kw):
    it = {"cat": cat, "id": rec["id"], "name": clean(rec.get("displayName") or rec["name"]), "price": rec.get("price", 0),
          "icon": icon(rec.get("icon")), "bonuses": bonuses(rec.get("bonuses")), "set": rec.get("setId") or 0,
          "unique": bool(rec.get("unique"))}
    if "classes" in rec:
        it["classes"] = class_ids(rec["classes"])
    it.update({k: v for k, v in kw.items() if v is not None})
    items.append(it)


for r in load("items/weapons.json")["records"]:
    if not r["name"] or r.get("typeName") is None:
        continue
    add("weapon", r, type=r["typeName"], atk=r["attack"], delay=r["attackDelay"], kb=r["knockback"],
        charge=r["chargeRate"], element=r.get("element") or 0, req=r.get("reqWeaponSkill"),
        spell=r.get("spellId"), spellMax=r.get("spellMaxLevel"))
for cat, fn in (("body", "items/body_armour.json"), ("helmet", "items/helmets.json"), ("offhand", "items/offhand.json")):
    for r in load(fn)["records"]:
        if not r["name"]:
            continue
        add(cat, r, defense=r["defense"], reqSTR=r.get("requiredSTR") or 0,
            shield=bool(r.get("isShield")) if cat == "offhand" else None)
for r in load("items/accessories.json")["records"]:
    if r["name"]:
        add("accessory", r)
soul_by_item = {i["index"]: i for i in souls_src["items"]}
for r in load("items/soul_items.json")["records"]:
    si = soul_by_item.get(r["id"], {})
    add("soul", r, soul=si.get("soulId"), level=si.get("level"), gauge=r.get("gaugeNeeded"))

ench = [{"id": e["id"], "name": e["displayName"], "mult": e["priceMultTenths"], "bonuses": bonuses(e["bonuses"]),
         "on": e["allowedOn"]} for e in load("items/enchantments.json")["records"]]
kinds_src = load("items/affix_kinds.json")["kinds"]
kinds = {k: {"plus": v.get("labelPlus") or "", "minus": v.get("labelMinus") or "", "effect": v.get("effect", ""),
             "conf": v.get("conf", "")} for k, v in kinds_src.items()}

SLOT_OF = {"weapon": "weapon", "body armour": "body", "helmet": "helmet", "off-hand": "offhand",
           "accessory": "accessory", "soul": "soul"}
sets = []
for s in load("items/sets.json")["records"]:
    members = {SLOT_OF[k]: v["id"] for k, v in (s.get("members") or {}).items()}
    sets.append({"id": s["setId"], "name": s["name"], "members": members, "bonuses": bonuses(s["bonuses"])})

# ---------- monsters (normal table, named; hard-mode copies are the same records + 197) ----------
monsters = []
for m in load("world/monsters.json")["monsters"]:
    if m["table"] != "normal" or not m["nameEn"]:
        continue
    r = m["resist"]
    monsters.append({"i": m["index"], "name": clean(m["nameEn"]), "lv": m["level"], "atk": m["atk"], "def": m["def"],
                     "hit": m["hit"], "hp": m["hpSolo"], "cat": m["category"], "boss": m["isBoss"],
                     "res": [r["el%d" % k] for k in range(1, 7)]})

exp = load("characters/exp_curve.json")
exp_list = [l["totalExpForNext"] for l in exp.get("levels", [])]
secret = load("characters/secret_names.json")

# ---------- guardrails ----------
by_key = {(i["cat"], i["id"]) for i in items}
seen = set()
for i in items:
    k = (i["cat"], i["id"])
    if k in seen:
        errors.append("duplicate item %s" % (k,))
    seen.add(k)
    for kd, _ in i["bonuses"]:
        if str(kd) not in kinds:
            errors.append("%s %s: unknown bonus kind %s" % (i["cat"], i["name"], kd))
    if i.get("spell") is not None and i["spell"] not in spell_ids:
        errors.append("weapon %s: spell %s not in spell list" % (i["name"], i["spell"]))
for s in sets:
    for slot, mid in s["members"].items():
        if (slot, mid) not in by_key:
            errors.append("set %s: %s id %s does not resolve" % (s["name"], slot, mid))
for e in ench:
    for kd, _ in e["bonuses"]:
        if str(kd) not in kinds:
            errors.append("enchantment %s: unknown bonus kind %s" % (e["name"], kd))
for c in classes:
    for s in c["skills"]:
        if s.get("spellId") is not None and s["spellId"] not in spell_ids:
            errors.append("class %s skill %s: spell %s missing" % (c["name"], s["name"], s["spellId"]))
if not exp_list:
    errors.append("exp curve: no list found in exp_curve.json (keys %s)" % list(exp))
src_icons = {}
for b in sorted(used_banks):
    p = os.path.join(X, "assets", "icons_bank%03d.png" % b)
    if not os.path.exists(p):
        errors.append("icon sheet %s missing (run _ss2_extract/tools/dec_assets.py --png)" % p)
    src_icons[b] = p

print("-- Data hygiene report --")
print("  %d classes, %d items, %d sets, %d enchantments, %d spells, %d souls, %d monsters, %d icon sheets"
      % (len(classes), len(items), len(sets), len(ench), len(spells), len(souls), len(monsters), len(used_banks)))
for e in errors:
    print("  ERROR", e)
for w in warnings:
    print("  warn ", w)
if errors or (STRICT and warnings):
    print("BUILD FAILED: data.js left untouched")
    sys.exit(1)

# ---------- write ----------
os.makedirs(os.path.join(APP, "assets", "icons"), exist_ok=True)
for b, p in src_icons.items():
    shutil.copyfile(p, os.path.join(APP, "assets", "icons", "bank%03d.png" % b))
data = {"classes": classes, "spells": spells, "souls": souls, "soulPower": soul_power, "items": items,
        "enchantments": ench, "kinds": kinds, "sets": sets, "monsters": monsters, "exp": exp_list,
        "secretNames": secret.get("names") or secret.get("records") or secret, "elements": ELEMENTS}
with open(os.path.join(APP, "data.js"), "w", encoding="utf-8", newline="\n") as f:
    f.write("window.SS2_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
print("wrote data.js (%d KB)" % (os.path.getsize(os.path.join(APP, "data.js")) // 1024))

urls = sorted("assets/icons/" + n for n in os.listdir(os.path.join(APP, "assets", "icons")))
v = hashlib.md5("\n".join(urls).encode()).hexdigest()[:8]
with open(os.path.join(APP, "precache-list.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"v": v, "urls": urls}, f)

sys.path.insert(0, os.path.join(os.path.dirname(APP), "tools", "app"))
from stamp_cache import stamp  # noqa: E402
print("cache-bust:", stamp(APP) or "unchanged")
