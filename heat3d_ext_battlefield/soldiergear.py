"""
The soldiers' weapons and gadgets of Battlefield 6, 4 and 1, for the catalogue (`catalog` verb).

Battlefield 4 and 1: the weapon superbundles (`WeaponsAndAttachments`, Battlefield 4's `XP<n>Weapons`). Every
`SoldierWeaponBlueprint` under `gameplay/weapons/` or `gameplay/gadgets/` is one item; its `SoldierWeaponData`
gives the weapon class (a number) and `DamageGiverName`, the name the game reports kills with. Items under
`gadgets/` are gadgets (launchers, grenades, explosives, tools, drones ...), melee ones weapons of class `melee`.

Battlefield 6: the art of the `weapons`, `vehicles` and `characters` tables, one folder per item:
`common/hardware/weapons/<class>/<name>/` and `common/hardware/gadgets/<class>/<name>/` (the blueprints are in a
type library this reader does not have, so the folder names the item).

Items for AI, the campaign and cosmetics (dog tags, spray cans) are left out.
"""

from __future__ import annotations

import re
from pathlib import Path

#: Battlefield 4 and 1 `WeaponClass` numbers -> class word (the weapon folders say it in Battlefield 1 too).
WEAPON_CLASS = {14: "pistol", 16: "assault-rifle", 17: "shotgun", 18: "smg-pistol", 19: "lmg", 20: "rifle",
                27: "melee", 28: "melee"}
#: Battlefield 1's weapon folders -> class word.
FOLDER_CLASS = {"lmg": "lmg", "semiauto": "rifle", "shotguns": "shotgun", "sidearms": "pistol",
                "singleaction": "rifle", "smg": "smg", "fieldkits": "elite", "vehiclekits": "vehicle-kit",
                "melee": "melee"}
#: Gadget classes by words of the item's path, first match wins.
GADGET_CLASS = (
    ("drone", r"mav|eodbot|eod_bot|suav|ucav|drone|lancet|pigeon|mkv"),
    ("launcher", r"launcher|rpg|smaw|sraw|javelin|fgm|fim92|igla|sa18|stinger|m26|starstreak|nlaw|at4|m136|m320|mgl|xm25|"
                 r"mortar|m224|panzerfaust|mbtlaw|airburst|breachingdart|crossbow|tankgewehr|breechgun|flaregun"),
    ("explosive", r"c4|claymore|mine|slam|dynamite|tripwire|m15|limpet|charge|thermite|explosive"),
    ("support", r"ammo|medic|bandage|syringe|defib|repair|wrench|supply|armou?r|gasmask|shield|ladder|cover|"
                r"revivepen|jammer|nvg|keycard|mp_?aps"),
    ("grenade", r"grenade|m67|v40|rgo|flash|m34|m18|frag|incendiary|smoke|gas|concussion|throwingknife|"
                r"antichars"),
    ("sensor", r"tugs|t-ugs|motionsensor|soflam|beacon|radio|decoy|periscope|laserdesignator|tracerdart|eidos|"
               r"intel|binocular|flare|proximity"),
)
#: Not an item a player carries: AI and campaign copies, placeholders, cosmetics.
SKIP = re.compile(r"(^|[/_])(ai|sp|spec|prologue)([/_]|$)|dummy|handcuff|weaponunarmed|blankweapon|shellcasing|"
                  r"/sp/|dogtags|spraycan|_forgeeditor", re.I)
#: Battlefield 6 weapon folders -> class word.
BF6_WEAPON_CLASS = {"assaultrifle": "assault-rifle", "boltaction": "sniper", "carbine": "carbine", "dmr": "dmr",
                    "melee": "melee", "mg": "lmg", "secondary": "pistol", "shotgun": "shotgun", "smg": "smg"}
#: Display names where the folder's name does not read well.
NAMES = {
    "m136at4": "M136 AT4", "m26mass": "M26 MASS", "m320he": "M320 HE", "m320thermobaric": "M320 Thermobaric",
    "m224mortar": "M224 Mortar", "mbtlaw": "MBT LAW", "panzerfaust3": "Panzerfaust 3", "rpg7": "RPG-7",
    "breachingdart": "Breaching dart", "airburstincendiary": "Airburst (incendiary)", "atmine": "AT mine",
    "m4slam": "M4 SLAM", "ptkm1r": "PTKM-1R", "ceramicarmor": "Ceramic armour", "softarmor": "Soft armour",
    "defibrillator": "Defibrillator", "eodbot": "EOD bot", "gasmask": "Gas mask", "inteldronecontroller": "Intel drone",
    "mobilejammer": "Mobile jammer", "nvg": "Night vision", "revivepen": "Revive pen", "tracerdart": "Tracer dart",
    "uavjammer": "UAV jammer", "vehiclekeycard": "Vehicle keycard", "m18claymore": "M18 Claymore",
    "thermitecharge": "Thermite charge", "supplypouch": "Supply pouch", "antitank": "Anti-tank grenade",
    "c4": "C4", "concussion": "Concussion grenade", "flashbang": "Flashbang", "frag": "Frag grenade",
    "incendiary": "Incendiary grenade", "miniv40": "Mini V40", "proximity": "Proximity sensor",
    "smoke": "Smoke grenade", "supplycrate": "Supply crate", "throwingknife": "Throwing knife",
    "vehiclesupplycrate": "Vehicle supply crate", "deployablecover": "Deployable cover", "eidos": "Eidos",
    "handheldradio": "Radio", "rfradio": "RF radio", "ladder": "Ladder", "laserdesignator": "Laser designator",
    "mpaps": "MP-APS", "repair": "Repair tool", "sniperdecoy": "Sniper decoy", "spawnbeacon": "Spawn beacon",
    "tugs": "T-UGS", "dataextractiontablet": "Data extraction tablet", "lancet": "Lancet drone", "drone": "Drone",
    "dspulse": "DS pulse", "minigun": "Minigun", "railgun": "Railgun", "javelin": "Javelin", "stinger": "Stinger",
    "igla": "Igla", "airburst": "Airburst launcher", "portalgadget": "Portal gadget",
}


def _flat(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def pretty(word: str) -> str:
    """A folder or blueprint name as a display name: `m4a1` -> `M4A1`, `knife_trench` -> `Knife Trench`."""
    if word.lower() in NAMES:
        return NAMES[word.lower()]
    parts = [p for p in re.split(r"[_\-\s]+", word) if p]
    return " ".join(p.upper() if any(c.isdigit() for c in p) or len(p) <= 3 else p.capitalize() for p in parts)


def gadget_class(path: str) -> str:
    low = path.lower()
    for cls, rx in GADGET_CLASS:
        if re.search(rx, low):
            return cls
    return "gadget"


def legacy_item(blueprint: str, weapon_class: int | None, damage_giver: str | None) -> dict | None:
    """The catalogue entry of a Battlefield 4 or 1 `SoldierWeaponBlueprint` (its ebx name), or None to leave it out."""
    name = blueprint.lower()
    if SKIP.search(name) or not re.search(r"gameplay/(weapons|gadgets)/", name):
        return None
    stem = name.rsplit("/", 1)[-1]
    tail = name.split("gameplay/", 1)[1]
    melee = weapon_class in (27, 28) or "/melee/" in "/" + tail
    if melee:
        kind, cls = "weapon", "melee"
    elif "gadgets/" in tail:
        kind, cls = "gadget", gadget_class(tail)
    else:
        kind = "weapon"
        folder = tail.split("/")[1] if tail.count("/") >= 3 else ""
        cls = FOLDER_CLASS.get(folder) or WEAPON_CLASS.get(weapon_class or -1, "weapon")
    label = pretty(stem)
    dg = (damage_giver or "").strip()
    # The kill feed's name, where it is this item's own (Battlefield 1 reuses names across items).
    if dg and "/" not in dg and len(_flat(dg)) >= 2 and (_flat(dg) in _flat(stem) or _flat(stem) in _flat(dg)):
        label = re.sub(r"_PDA$|_Portable$", "", dg, flags=re.I).replace("_", " ")
    item = {"id": stem, "kind": kind, "name": label, "class": cls, "blueprint": blueprint}
    if dg:
        item["damageGiver"] = dg
    if weapon_class is not None:
        item["weaponClass"] = int(weapon_class)
    return item


def unique_names(items: list[dict]) -> list[dict]:
    """Items sharing a name (a mortar and its HE variant, both `Mortar` in the kill feed) take their blueprint's."""
    seen: dict[str, int] = {}
    for i in items:
        seen[i["name"].lower()] = seen.get(i["name"].lower(), 0) + 1
    for i in items:
        if seen[i["name"].lower()] > 1 and i.get("blueprint"):
            i["name"] = pretty(i["blueprint"].rsplit("/", 1)[-1])
    return items


def bf6_items(names) -> list[dict]:
    """The weapons and gadgets a Battlefield 6 install's art names (ebx or res names of its tables)."""
    found: dict[str, dict] = {}
    weapon = re.compile(r"(?:^|/)common/hardware/weapons/([a-z0-9]+)/([^/_][^/]*)/")
    gadget = re.compile(r"(?:^|/)common/hardware/gadgets/([a-z0-9]+)/([^/]+)/")
    for n in names:
        low = n.lower()
        m = weapon.search(low)
        if m and m.group(1) in BF6_WEAPON_CLASS:
            cat, name = m.groups()
            vid = f"{cat}_{name}"
            found.setdefault(vid, {"id": vid, "kind": "weapon", "name": pretty(name), "class": BF6_WEAPON_CLASS[cat],
                                   "folder": f"common/hardware/weapons/{cat}/{name}"})
            continue
        m = gadget.search(low)
        if m:
            cat, name = m.groups()
            if SKIP.search(name):
                continue
            vid = f"{cat}_{name}"
            cls = "pickup" if cat == "battlepickups" else gadget_class(f"{cat}/{name}")
            found.setdefault(vid, {"id": vid, "kind": "gadget", "name": pretty(name), "class": cls,
                                   "folder": low[: m.end() - 1]})
    return [found[k] for k in sorted(found)]


# --------------------------------------------------------------------------- installs


BF6_TABLES = ("weapons", "vehicles", "characters")


def bf6_tables(install: Path) -> list[Path]:
    return [p for p in (Path(install) / "Data" / "Win32" / f"{t}.toc" for t in BF6_TABLES) if p.is_file()]


def bf6_gear(install: Path) -> list[dict]:
    from .frostbitebundle import LevelCatalogue

    names: list[str] = []
    for toc in bf6_tables(install):
        cat = LevelCatalogue(toc)
        names += list(cat.ebx) + list(cat.res)
    return bf6_items(names)


def legacy_tables(game, pattern: str) -> list[Path]:
    """The superbundle tables of a Battlefield 4 or 1 install whose name matches `pattern` (every layer)."""
    out = []
    for layer in game.layers:
        for toc in sorted(layer.glob("Win32/*.toc")):
            if re.search(pattern, toc.stem, re.I) and toc.with_suffix(".sb").is_file():
                out.append(toc)
    return out


def open_superbundles(game, pattern: str):
    """The superbundles matching `pattern`, opened together for their ebx (no chunk tables: names and blueprints only)."""
    from .legacy import LegacyLevel
    from .legacygear import Vehicles

    vs = object.__new__(Vehicles)
    vs.install = game
    vs.sb = LegacyLevel(pattern, Path("."))
    vs._parts, vs._names = {}, None
    by_name: dict[str, list[Path]] = {}
    for toc in legacy_tables(game, pattern):
        by_name.setdefault(toc.stem.lower(), []).append(toc)
    for tocs in by_name.values():
        vs._open(tocs)
    return vs


def legacy_gear(game) -> list[dict]:
    """The weapons and gadgets of a Battlefield 4 or 1 install (a `LegacyInstall`)."""
    sbs = open_superbundles(game, r"weapon")
    items: dict[str, dict] = {}
    for name in sorted(sbs.sb.ebx):
        if not re.search(r"gameplay/(weapons|gadgets)/", name) or re.search(
                r"_mesh|_3p|projectile|/fx/|sound|_1p|unlock|/ai/", name):
            continue
        p = sbs.partition(name)
        if p is None or p.primary is None or p.primary.type != "SoldierWeaponBlueprint":
            sbs._parts.pop(name, None)
            continue
        data = p.of_type("SoldierWeaponData")
        sw = data[0] if data else None
        item = legacy_item(name, sw.get("WeaponClass") if sw else None, sw.get("DamageGiverName") if sw else None)
        sbs._parts.pop(name, None)
        if item is None:
            continue
        if item["id"] in items:
            # Two blueprints of one name (an expansion's copy): the second keeps its folder.
            item["id"] = "_".join(name.lower().split("/")[-3:])
            if item["id"] in items:
                continue
        items[item["id"]] = item
    return unique_names([items[k] for k in sorted(items)])


def legacy_vehicle_ids(game) -> list[str]:
    """The vehicle ids (blueprint stems) of a Battlefield 4 or 1 install, without its chunk tables."""
    from .legacygear import Vehicles

    vs = open_superbundles(game, r"vehicles")
    return sorted({b.rsplit("/", 1)[-1] for b in Vehicles.blueprints(vs)})
