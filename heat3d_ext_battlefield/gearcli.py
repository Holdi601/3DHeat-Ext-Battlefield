"""
The `catalog` and `models` verbs: the vehicles of Battlefield 4 and 1 (`legacygear`) and of Battlefield 6
(`frostbitegear`) as a catalogue and a local model pack, for every such game installed (or the one given).
The catalogue lists the soldiers' weapons and gadgets too (`soldiergear`).

    catalog  -> <HEAT3D_LEVELS>/<game>/catalog.json
    models   -> <HEAT3D_LEVELS>/model-packs/<game>/<vehicle>.glb + model-pack.json

The files are made from the user's own install and stay on this machine.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from . import __version__

SOURCE = "heat3d-battlefield-maps"


def installs(given: Path | None) -> list[Path]:
    """Every Battlefield 4, 1 or 6 install found (Steam libraries, the EA app's, Origin's and Epic's folders), or the one given."""
    from heat3d_gamefiles.steam import STEAM_DEFAULTS, steam_libraries

    from .cli import GAME_ENV, LAUNCHER_FOLDERS, _legacy

    if given is not None:
        return [given]
    if os.environ.get(GAME_ENV):
        return [Path(os.environ[GAME_ENV])]
    roots = [lib / "steamapps" / "common" for lib in [Path(p) for p in STEAM_DEFAULTS] + steam_libraries()]
    found, seen = [], set()
    for common in roots + [Path(p) for p in LAUNCHER_FOLDERS]:
        if not common.is_dir():
            continue
        for game in sorted(common.iterdir()):
            key = str(game).lower()
            if key in seen or not (game / "Data" / "layout.toc").is_file():
                continue
            seen.add(key)
            from .frostbitegear import bf6_vehicles_table

            if _legacy(game) is not None or bf6_vehicles_table(game) is not None:
                found.append(game)
    return found


def _levels_root(out: Path | None) -> Path | None:
    if out is not None:
        return out
    lv = os.environ.get("HEAT3D_LEVELS")
    return Path(lv) if lv else None


def _game_build(install: Path) -> str:
    for name in ("version.json", "Data/layout.toc"):
        p = install / name
        if p.is_file():
            st = p.stat()
            return f"{time.strftime('%Y-%m-%d', time.gmtime(st.st_mtime))}-{st.st_size}"
    return "unknown"


def _open(install: Path):
    from heat3d_gamefiles import levelshome

    from .cli import _legacy
    from .legacygear import Vehicles

    game = _legacy(install)
    if game is None:
        return None, None, levelshome.game_folder(install)
    return game, Vehicles(game), levelshome.game_folder(install)


def _bf6(install: Path):
    """(catalogue of the vehicles table, {vehicle id: base mesh}) of a Battlefield 6 install."""
    from .frostbitebundle import LevelCatalogue
    from .frostbitegear import bf6_vehicles_table, vehicles

    cat = LevelCatalogue(bf6_vehicles_table(install))
    return cat, vehicles(cat)


def catalog(args) -> int:
    from .legacygear import describe
    from .modelpack import write_catalog

    games = installs(args.install)
    if not games:
        print("no Battlefield 6, 4 or 1 install found; give --game <its folder>", file=sys.stderr)
        return 2
    root = _levels_root(args.out)
    if root is None:
        print("no output folder: pass --out or set HEAT3D_LEVELS", file=sys.stderr)
        return 2
    for install in games:
        _game, vs, folder = _open(install)
        items = []
        if vs is None:
            from .frostbitegear import describe as describe6

            _cat, found = _bf6(install)
            items = [describe6(vid, mesh) for vid, mesh in found.items()]
        pack_index = root / "model-packs" / folder / "model-pack.json"
        have = {}
        if pack_index.is_file():
            import json

            have = json.loads(pack_index.read_text(encoding="utf-8")).get("units", {})
        for bp in vs.blueprints() if vs is not None else []:
            d = describe(vs, bp)
            if d["id"] in have:
                d["model"] = f"model-packs/{folder}/{have[d['id']]['file']}"
            items.append(d)
        vehicles = len(items)
        # The soldiers' weapons and gadgets beside the vehicles.
        from . import soldiergear

        gear = soldiergear.legacy_gear(_game) if _game is not None else soldiergear.bf6_gear(install)
        items += gear
        weapons = sum(1 for i in gear if i["kind"] == "weapon")
        out = root / folder / "catalog.json"
        write_catalog(out, folder, _game_build(install), f"{SOURCE} {__version__}", items)
        print(f"{folder}: {vehicles} vehicles, {weapons} weapons, {len(gear) - weapons} gadgets -> {out}")
    return 0


def models(args) -> int:
    from .legacygear import build_vehicle, describe, fingerprint
    from .modelpack import Pack

    games = installs(args.install)
    if not games:
        print("no Battlefield 6, 4 or 1 install found; give --game <its folder>", file=sys.stderr)
        return 2
    root = _levels_root(args.out)
    if root is None:
        print("no output folder: pass --out or set HEAT3D_LEVELS", file=sys.stderr)
        return 2
    failed_all = 0
    for install in games:
        t0 = time.time()
        _game, vs, folder = _open(install)
        if vs is None:
            failed_all += _models6(install, folder, root, args)
            continue
        pack = Pack(root / "model-packs" / folder, folder, _game_build(install), f"{SOURCE} {__version__}")
        done = same = failed = 0
        bps = vs.blueprints()
        print(f"{folder}: {len(bps)} vehicles", flush=True)
        for bp in bps:
            d = describe(vs, bp)
            if args.only and not any(o.lower() in bp.lower() for o in args.only):
                continue
            fp = fingerprint(vs, bp)
            if not args.force and pack.fresh(d["id"], fp):
                same += 1
                continue
            try:
                dm: list = []
                parts, pivots, notes = build_vehicle(vs, bp, d["domain"], dm)
                e = pack.add(d["id"], parts, d["domain"], d["class"], key=d["key"], pivots=pivots, dm=dm, fingerprint=fp,
                             extra={"name": d["name"], "nation": d["nation"], "blueprint": bp, "notes": notes[:4]})
                done += 1
                print(f"  {d['id']}: {e['parts']} {e['tris']} tris, {e['dm']} hit regions, "
                      f"{e['length']} x {e['width']} x {e['height']} m", flush=True)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"  {d['id']}: FAILED {exc}", flush=True)
        pack.save()
        failed_all += failed
        print(f"{folder}: {done} written, {same} unchanged, {failed} failed; {pack.bytes / 1e6:.1f} MB; "
              f"{time.time() - t0:.0f} s -> {pack.index_path}")
    return 0


def _models6(install: Path, folder: str, root: Path, args) -> int:
    from .frostbitegear import build, describe, fingerprint
    from .modelpack import Pack

    t0 = time.time()
    cat, found = _bf6(install)
    pack = Pack(root / "model-packs" / folder, folder, _game_build(install), f"{SOURCE} {__version__}")
    done = same = failed = 0
    print(f"{folder}: {len(found)} vehicles", flush=True)
    for vid, mesh in found.items():
        if args.only and not any(o.lower() in vid.lower() for o in args.only):
            continue
        d = describe(vid, mesh)
        fp = fingerprint(cat, mesh)
        if not args.force and pack.fresh(vid, fp):
            same += 1
            continue
        try:
            parts, pivots, notes = build(cat, mesh, d["domain"], d["class"])
            e = pack.add(vid, parts, d["domain"], d["class"], key=d["key"], pivots=pivots, fingerprint=fp,
                         extra={"name": d["name"], "nation": d["nation"], "mesh": mesh, "notes": notes})
            done += 1
            print(f"  {vid}: {e['parts']} {e['tris']} tris, {e['length']} x {e['width']} x {e['height']} m", flush=True)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {vid}: FAILED {exc}", flush=True)
    pack.save()
    print(f"{folder}: {done} written, {same} unchanged, {failed} failed; {pack.bytes / 1e6:.1f} MB; "
          f"{time.time() - t0:.0f} s -> {pack.index_path}")
    return failed
