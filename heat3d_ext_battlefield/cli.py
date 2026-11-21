"""
heat3d-battlefield-maps levels   [--game folder]
heat3d-battlefield-maps level    <level> [-o map.glb] [--detail-budget n] [--textures [px]]
                                 [--ground-texture [m]] [--navmesh] [--skip text ...] ...
heat3d-battlefield-maps layouts  <level|all> [--game folder] [-o folder]
heat3d-battlefield-maps identify <file>

`levels` lists the levels of the installed Battlefield 6 (any Frostbite game
whose `Data` holds a `layout.toc`), or the multiplayer levels of a Battlefield 4
or Battlefield 1 folder given with --game, `level` writes one of them (or `all`)
as a `.glb`, `layouts` writes what each of its game modes is played over
(capture points, objectives, combat areas, spawns) as `<Level>.layouts.json`
beside it (Battlefield 4 and 1),
`identify` says whether a file is a Frostbite table of contents. 3DHeat
GameFiles' `levels`, `level` and `identify` run these.

Exit status: 0 done, 1 failed, 2 nothing to read (no install found, not a
Frostbite file, 3DHeat GameFiles missing); the message says what to do.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__, library

PROG = "heat3d-battlefield-maps"

#: Where the EA app, Origin and the Epic Games launcher install by default.
LAUNCHER_FOLDERS = (
    r"C:\Program Files\EA Games",
    r"C:\Program Files (x86)\Origin Games",
    r"C:\Program Files\Epic Games",
)

NOT_FOUND = (
    "no Frostbite game found in a Steam library or the EA app's, Origin's or Epic's "
    "folder; give --install <the game's folder>"
)


def _identify(path: Path) -> str | None:
    """A Frostbite table of contents, described; None for anything else."""
    from .frostbite import (
        UnsupportedFrostbite,
        parse_toc,
        read_header,
        read_sections,
        superbundles,
    )

    lines = [f"{path.name}  ({path.stat().st_size:,} bytes)"]
    try:
        with path.open("rb") as handle:
            data = handle.read(64)
        info = read_header(data, path.name)
        lines.append(f"  Frostbite table of contents, {info.kind}")
        lines.append(f"    tree begins at {info.payload_offset}")
        whole = path.read_bytes()
        try:
            sections = read_sections(whole, info, path.name)
            lines.append(f"    assets     {sections.asset_count:,}")
        except UnsupportedFrostbite:
            names = superbundles(parse_toc(path)[1])
            lines.append(f"    superbundles {len(names)}")
        return "\n".join(lines)
    except UnsupportedFrostbite:
        return None


def _frostbite_install(given: Path | None) -> Path | None:
    """
    A Frostbite game's folder: the one given, or the first Steam game whose
    `Data` holds a `layout.toc`, else the first such game in the EA app's,
    Origin's or the Epic Games launcher's default folder.
    """
    from heat3d_gamefiles.steam import STEAM_DEFAULTS, steam_libraries

    if given is not None:
        return given
    if os.environ.get(GAME_ENV):
        return Path(os.environ[GAME_ENV])
    roots = [library / "steamapps" / "common" for library in [Path(p) for p in STEAM_DEFAULTS] + steam_libraries()]
    for common in roots + [Path(p) for p in LAUNCHER_FOLDERS]:
        if not common.is_dir():
            continue
        for game in sorted(common.iterdir()):
            if (game / "Data" / "layout.toc").is_file():
                return game
    return None


#: The game's folder, when neither --game nor --install gives it.
GAME_ENV = "HEAT3D_BATTLEFIELD_GAME"


def _legacy(install: Path):
    """A Battlefield 4 or Battlefield 1 install (`legacy`), or None for any other."""
    from .frostbite import UnsupportedFrostbite
    from .legacy import LegacyInstall

    try:
        return LegacyInstall(install)
    except UnsupportedFrostbite:
        return None


def _legacy_levels(game, install: Path) -> int:
    levels = game.multiplayer_levels()
    print(f"{len(levels)} multiplayer levels in {install}")
    for name, tocs in sorted(levels.items()):
        layer = tocs[0].relative_to(install).parts[0]
        print(f"  {name:<30} {layer}")
    return 0


def _legacy_level(game, install: Path, args) -> int:
    import time

    from heat3d_gamefiles import levelshome

    from .frostbite import UnsupportedFrostbite
    from .legacylevel import BUDGET, build_legacy_level, write_legacy_level

    folder = levelshome.game_folder(install)
    if args.level.lower() == "all":
        names = sorted(game.multiplayer_levels())
        if args.order:
            wanted = [line.split()[-1].lower() for line in Path(args.order).read_text().splitlines() if line.strip()]
            names = [n for n in wanted if n in names] + [n for n in names if n not in wanted]
    else:
        names = [args.level]
    failed = 0
    for name in names:
        start = time.time()
        print(f"== {name}", flush=True)
        try:
            model = build_legacy_level(game, name, budget=args.detail_budget or BUDGET)
            if args.out is not None and (len(names) > 1 or args.out.suffix.lower() != ".glb"):
                out = args.out / f"{model.name}.glb"
            elif args.out is not None:
                out = args.out
            else:
                out = levelshome.default(f"{model.name}.glb", folder)
            out.parent.mkdir(parents=True, exist_ok=True)
            write_legacy_level(model, out, folder)
        except (UnsupportedFrostbite, ValueError) as exc:
            print(f"   failed: {exc}", file=sys.stderr, flush=True)
            failed += 1
            continue
        for key, value in model.report.items():
            print(f"   {key}: {value:,}" if isinstance(value, int) else f"   {key}: {value}")
        print(f"-> {out} ({out.stat().st_size / 1e6:,.0f} MB, {time.time() - start:,.0f} s)", flush=True)
    return 1 if failed == len(names) else 0


def _layouts(args) -> int:
    import time

    from heat3d_gamefiles import levelshome

    from .frostbite import UnsupportedFrostbite
    from .legacylayouts import build_layouts, write_layouts

    install = _frostbite_install(args.install)
    if install is None:
        print(NOT_FOUND, file=sys.stderr)
        return 2
    game = _legacy(install)
    if game is None:
        print("layouts reads Battlefield 4 and Battlefield 1 for now; give --game <their folder>", file=sys.stderr)
        return 2
    folder = levelshome.game_folder(install)
    names = sorted(game.multiplayer_levels()) if args.level.lower() == "all" else [args.level]
    failed = 0
    for name in names:
        start = time.time()
        print(f"== {name}", flush=True)
        try:
            doc = build_layouts(game, name, folder, __version__)
        except (UnsupportedFrostbite, ValueError, KeyError, IndexError) as exc:
            print(f"   failed: {exc}", file=sys.stderr, flush=True)
            failed += 1
            continue
        if not doc["layouts"]:
            print("   no game modes found", flush=True)
            continue
        # Named as the level's .glb is, when it is there (`MP_Volga`, not `mp_volga`).
        home = args.out if args.out is not None and args.out.suffix.lower() != ".json" else levelshome.default("x", folder).parent
        glb = next((p for p in home.glob("*.glb") if p.stem.lower() == doc["level"].lower()), None) if home.is_dir() else None
        if glb is not None:
            doc["level"] = glb.stem
        stem = f"{doc['level']}.layouts.json"
        if args.out is not None:
            out = args.out if args.out.suffix.lower() == ".json" and len(names) == 1 else args.out / stem
        else:
            out = levelshome.default(stem, folder)
        write_layouts(doc, out)
        print(f"-> {out} ({len(doc['layouts'])} modes, {time.time() - start:,.1f} s)", flush=True)
    return 1 if names and failed == len(names) else 0


def _levels(args) -> int:
    from .frostbite import UnsupportedFrostbite
    from .frostbitebundle import level_sources

    install = _frostbite_install(args.install)
    if install is None:
        print(NOT_FOUND, file=sys.stderr)
        return 2
    game = _legacy(install)
    if game is not None:
        return _legacy_levels(game, install)
    try:
        tables = level_sources(install)
    except UnsupportedFrostbite as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"{len(tables)} levels in {install}")
    for name, table in sorted(tables.items()):
        extra = f" (+{len(table.supplements)} high-resolution)" if table.supplements else ""
        print(f"  {name:<40} {table.toc.stat().st_size:>12,}  {table.source}{extra}")
    return 0


def _level(args) -> int:
    from heat3d_gamefiles import levelshome

    from .frostbite import UnsupportedFrostbite
    from .frostbitelevel import build_level, write_level

    install = _frostbite_install(args.install)
    if install is None:
        print(NOT_FOUND, file=sys.stderr)
        return 2
    game = _legacy(install)
    if game is not None:
        return _legacy_level(game, install, args)
    out = args.out or levelshome.default(f"{Path(args.level).stem}.glb", levelshome.game_folder(install))
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        model = build_level(
            install,
            args.level,
            budget=args.detail_budget,
            skip=tuple(args.skip or ()),
            textures=args.textures,
            ground_spacing=args.ground_spacing,
            ground_texture=args.ground_texture,
            navmesh=args.navmesh,
            by_mesh=args.by_mesh,
        )
    except UnsupportedFrostbite as exc:
        print(exc, file=sys.stderr)
        return 1

    placed = model.placements
    print(
        f"{placed.copies():,} copies of {len(placed.meshes):,} meshes, from "
        f"{len(placed.partitions)} static model groups"
    )
    for name, copies in sorted(placed.partitions.items(), key=lambda kv: -kv[1]):
        print(f"  {copies:>8,}  {name}")
    if placed.objects:
        print(f"  {placed.objects:>8,}  placed one by one (object and prefab references)")
    if placed.unresolved:
        print(f"{placed.unresolved:,} members name a mesh this level does not carry; left out")
    reasons: dict[str, int] = {}
    for why in model.skipped.values():
        reasons[why] = reasons.get(why, 0) + 1
    for why, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"{count:,} meshes left out: {why}")
    print(
        f"{model.triangles():,} triangles, budget {model.budget:,}; "
        f"{model.coarser:,} meshes drawn at a coarser level to fit"
    )
    if model.dropped:
        print(
            f"{model.dropped:,} copies left out to fit the budget, the smallest first "
            "(--detail-budget raises it)"
        )
    kinds: dict[str, list[int]] = {}
    for part, piece in model.parts.items():
        part = part.replace(" (destructible)", "")
        short = (piece.texture or "").rsplit("/", 1)[-1]
        kind = part[: -len(short) - 1] if piece.texture and part.endswith(" " + short) else part
        entry = kinds.setdefault(kind, [0, 0])
        entry[0] += sum(len(f) for f in piece.faces)
        entry[1] += 1 if piece.texture else 0
    for kind, (triangles, textures) in sorted(kinds.items()):
        print(f"  {triangles:>12,}  {kind}" + (f", {textures:,} texture{'s' if textures > 1 else ''}" if textures else ""))
    if args.textures:
        done, drawn = model.textured
        print(f"{done:,} of {drawn:,} drawn sections carry their colour map; the rest are flat colours")
    print(f"Ground: {model.ground}.")
    if args.navmesh:
        print(f"Navigation mesh: {model.navmesh}.")
    if model.blockout:
        print(f"{model.blockout:,} triangles of placeholder blockout sections left out.")
    if placed.variations:
        print(
            f"{placed.variations:,} grouped copies placed in an object variation; "
            f"{model.varied:,} section copies drawn with their variation's own shader block."
        )
    if model.destructible:
        print(f"{model.destructible:,} triangles of destructible meshes, in parts named '... (destructible)'.")
    if model.sheets:
        print(f"{model.sheets:,} section copies lay their cut-out sheet (lettering, a sign) on by a later texture coordinate set.")
    if model.overlaid:
        print(f"{model.overlaid:,} sections drawn with their object's overlay through its second texture coordinates.")
    try:
        write_level(model, out, clamped=args.clamped_uvs)
    except (UnsupportedFrostbite, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    if model.flattened:
        print(
            f"{model.flattened:,} triangle{'s' if model.flattened > 1 else ''} repeat their texture too "
            "densely to cut and are drawn in its average colour."
        )
    print(f"-> {out} ({out.stat().st_size / 1e6:,.0f} MB)")
    return 0


def _run(verb, args) -> int:
    """A verb, with a missing Oodle library said in one message rather than a traceback."""
    from heat3d_gamefiles.oodle import OodleUnavailable

    try:
        return verb(args)
    except OodleUnavailable as exc:
        print(exc, file=sys.stderr)
        return 2


def _identify_verb(args) -> int:
    if not args.path.exists():
        print(f"no such file: {args.path}", file=sys.stderr)
        return 2
    try:
        found = _identify(args.path)
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 1
    if found is None:
        print("not a Battlefield file", file=sys.stderr)
        return 2
    print(found)
    return 0


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Battlefield 6 levels (Frostbite) from your own install into 3DHeat levels.",
        epilog="It reads the files of your own install; the levels it writes stay on your machine.",
    )
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="verb", required=True)

    p = sub.add_parser("levels", help="list the levels of an installed Frostbite game")
    p.add_argument("--install", "--game", dest="install", type=Path, default=None,
                   help=f"the game's folder (or set {GAME_ENV}); needed for Battlefield 4 and 1")

    p = sub.add_parser(
        "level", help="export a Frostbite level: its terrain backdrop and placed meshes"
    )
    p.add_argument("level", help="the level's name as `levels` lists it, or its .toc; `all` for every multiplayer level of Battlefield 4 or 1")
    p.add_argument(
        "-o", "--out", type=Path, default=None,
        help="the .glb (default: <level>.glb, in $HEAT3D_LEVELS/<game> when that is set)",
    )
    p.add_argument("--install", "--game", dest="install", type=Path, default=None,
                   help=f"the game's folder (or set {GAME_ENV}); needed for Battlefield 4 and 1")
    p.add_argument(
        "--detail-budget",
        type=int,
        default=None,
        help=(
            "a ceiling on triangles; the costliest meshes drop to coarser levels of "
            "detail until it fits (default: every copy at its coarsest, plus a "
            "quarter, at least 1,500,000; the terrain stays at full detail)"
        ),
    )
    p.add_argument(
        "--textures",
        type=int,
        nargs="?",
        const=512,
        default=0,
        metavar="PIXELS",
        help=(
            "write each surface's colour map, no larger than PIXELS a side "
            "(default 512 when given without a size); without it, flat colours"
        ),
    )
    p.add_argument(
        "--ground-texture",
        type=float,
        nargs="?",
        const=0.5,
        default=0.0,
        metavar="METRES",
        help=(
            "bake the terrain decals (roads, aprons, markings) into the ground's "
            "colour, METRES a pixel (default 0.5 when given without a size), in "
            "tiles of at most 4096 pixels"
        ),
    )
    p.add_argument(
        "--navmesh",
        action="store_true",
        help=(
            "add the soldiers' walkable surfaces from the level's navigation mesh "
            "as the part nav:walkable"
        ),
    )
    p.add_argument(
        "--by-mesh",
        action="store_true",
        help=(
            "for finding what a part is: one part per source mesh and material, "
            "named '<part> | <mesh> | <material>' (a much larger file)"
        ),
    )
    p.add_argument(
        "--clamped-uvs",
        action="store_true",
        help=(
            "for a renderer that cannot repeat a texture: cut every textured "
            "triangle into pieces with UVs inside 0..1, and draw the ones that "
            "would need more than 4 pieces in their texture's average colour "
            "(default: UVs as the game has them, with a repeating sampler)"
        ),
    )
    p.add_argument(
        "--ground-spacing",
        type=float,
        default=4.0,
        metavar="METRES",
        help="the terrain heightfield's finest spacing (default 4; 0 leaves it out)",
    )
    p.add_argument(
        "--order",
        type=Path,
        default=None,
        metavar="FILE",
        help="with `all` (Battlefield 4 and 1): a file of level names, one a line, to export first in that order",
    )
    p.add_argument(
        "--skip",
        action="append",
        default=None,
        metavar="TEXT",
        help="leave out static model groups whose partition name contains TEXT (repeatable)",
    )

    p = sub.add_parser(
        "layouts",
        help="write each game mode's capture points, objectives, combat areas and spawns of a level (Battlefield 4 and 1)",
    )
    p.add_argument("level", help="the level's name as `levels` lists it, or `all`")
    p.add_argument(
        "-o", "--out", type=Path, default=None,
        help="a folder (or, for one level, a .json); default: beside the levels, in $HEAT3D_LEVELS/<game> when that is set",
    )
    p.add_argument("--install", "--game", dest="install", type=Path, default=None,
                   help=f"the game's folder (or set {GAME_ENV})")

    for verb, text in (("catalog", "write the vehicles of Battlefield 6, 4 and 1 as a catalogue (<HEAT3D_LEVELS>/<game>/catalog.json)"),
                       ("models", "write the vehicles' models of Battlefield 6, 4 and 1 as a local model pack "
                                  "(<HEAT3D_LEVELS>/model-packs/<game>/)")):
        p = sub.add_parser(verb, help=text)
        p.add_argument("-o", "--out", type=Path, default=None, help="the levels folder to write under (default $HEAT3D_LEVELS)")
        p.add_argument("--install", "--game", dest="install", type=Path, default=None,
                       help=f"the game's folder (default: every Battlefield 6, 4 and 1 installed; or set {GAME_ENV})")
        if verb == "models":
            p.add_argument("--only", nargs="+", help="only the vehicles whose blueprint contains one of these words")
            p.add_argument("--force", action="store_true", help="rewrite vehicles already written")

    p = sub.add_parser("identify", help="say whether a file is a Frostbite table of contents, and what it holds")
    p.add_argument("path", type=Path)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not library.ensure():
        print(library.MISSING, file=sys.stderr)
        return 2
    if args.verb == "identify":
        # A quiet probe: GameFiles asks every installed game tool in turn.
        return _identify_verb(args)
    try:
        from . import update

        update.startup("heat3d_ext_battlefield")
    except Exception:  # an update check never stops an export
        pass
    from .gearcli import catalog, models

    verbs = {"levels": _levels, "level": _level, "layouts": _layouts, "catalog": catalog, "models": models}
    return _run(verbs[args.verb], args)


if __name__ == "__main__":
    sys.exit(main())
