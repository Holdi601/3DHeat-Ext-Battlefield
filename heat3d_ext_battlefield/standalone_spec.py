"""
The standalone app's description of this tool (app/spec.py): the Battlefield
6, 4 and 1 installs it reads, the checks before a level can be extracted, and
their levels as maps (new ones after a game update are found by
app/manifest.py). `python -m heat3d_ext_battlefield.standalone_spec` runs the
app from a checkout; the release executables run the same.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from . import __version__
from .app import paths
from .app.spec import Check, GameSpec, MapSource, Spec

#: Game key -> (label, Steam/launcher folder name, generation as the readers tell it).
GAMES = {
    "bf6": ("Battlefield 6", "Battlefield 6", "modern"),
    "bf4": ("Battlefield 4", "Battlefield 4", "bf4"),
    "bf1": ("Battlefield 1", "Battlefield 1", "bf1"),
}


def _generation(folder: Path) -> str | None:
    """`bf4` / `bf1` for an older Frostbite install, `modern` for a newer one, None for neither."""
    from . import library

    try:
        if not (folder / "Data" / "layout.toc").is_file():
            return None
    except OSError:
        return None
    if not library.ensure():
        return None
    from .cli import _legacy

    game = _legacy(folder)
    return game.generation if game is not None else "modern"


def _finder(key: str):
    label, folder_name, generation = GAMES[key]

    def find(given: str | None) -> Path | None:
        from .cli import GAME_ENV, LAUNCHER_FOLDERS

        test = lambda p: _generation(p) == generation  # noqa: E731
        if given:
            return Path(given) if test(Path(given)) else None
        candidates: list[Path | str | None] = [os.environ.get(GAME_ENV)]
        candidates += paths.steam_game_dirs(folder_name)
        candidates += [Path(base) / folder_name for base in LAUNCHER_FOLDERS]
        found = paths.first(candidates, test)
        if found is not None:
            return found
        # A folder named otherwise ("... Premium Edition"): any Battlefield folder of that generation.
        for common in [lib / "steamapps" / "common" for lib in paths.steam_libraries()] + [Path(p) for p in LAUNCHER_FOLDERS]:
            try:
                games = sorted(d for d in common.iterdir() if d.is_dir() and d.name.lower().startswith("battlefield"))
            except OSError:
                continue
            for d in games:
                if test(d):
                    return d
        return None

    return find


#: Levels that are not maps to play on: menus and lobbies.
NOT_A_MAP = re.compile(r"lobby|frontend|mainmenu|(^|_)test(_|$)", re.I)


def _maps_modern(game: Path) -> list[MapSource]:
    from .frostbitebundle import level_sources

    return [MapSource(name, name, [t.toc, *t.supplements], note=t.source)
            for name, t in sorted(level_sources(game).items()) if not NOT_A_MAP.search(name)]


def _maps_legacy(game: Path) -> list[MapSource]:
    from .cli import _legacy

    g = _legacy(game)
    if g is None:
        return []
    return [MapSource(name, name, list(tocs), note=tocs[0].relative_to(game).parts[0])
            for name, tocs in sorted(g.multiplayer_levels().items())]


def _stems(m: MapSource) -> re.Pattern:
    """
    The names a level's outputs may have: its id in any case (`MP_Prison` for `mp_prison`), or, for a
    Battlefield 6 level, its name without `mp_` and with what the export added (`capstone_textured_ground_nav`
    for `mp_capstone`, as `layouts` names them too). A name starting `mp_` is always another level's own.
    """
    short = re.sub(r"^mp_", "", m.id.lower())
    return re.compile(rf"{re.escape(m.id.lower())}|{re.escape(short)}(_[a-z0-9_]+)?")


def _outputs(out: Path, m: MapSource) -> list[Path]:
    """
    What a level has in `out`: its .glb and its layouts (content - catalogue, models - its own files).
    A level counts as extracted by its .glb: layouts alone (written for levels whose .glb was never made)
    are not the level, so such a level is still new.
    """
    if getattr(m, "kind", "map") != "map":
        return [p for p in _content_files(out, m) if p.is_file()]
    if not out.is_dir():
        return []
    rx = _stems(m)
    files = [p for p in out.iterdir() if p.is_file()]
    glbs = sorted(p for p in files if p.suffix.lower() == ".glb" and rx.fullmatch(p.stem.lower())
                  and (p.stem.lower() == m.id.lower() or not p.stem.lower().startswith("mp_")))
    if not glbs:
        return []
    stems = {p.stem.lower() for p in glbs} | {m.id.lower()}
    layouts = sorted(p for p in files if p.name.lower().endswith(".layouts.json")
                     and p.name.lower()[: -len(".layouts.json")] in stems)
    return glbs + layouts


def _extract(game: Path, m: MapSource, out: Path, log) -> list[Path]:
    from . import cli

    had_level = bool(_outputs(out, m))
    modern = _generation(game) == "modern"
    target = out / f"{m.id}.glb" if modern else out
    # Battlefield 6: with its colour maps, the terrain decals baked into the ground, and the walkable surfaces.
    extra = ["--textures", "--ground-texture", "--navmesh"] if modern else []
    code = cli.main(["level", m.id, "--game", str(game), "-o", str(target), *extra])
    if code != 0:
        raise RuntimeError(f"heat3d-battlefield-maps level exited {code}")
    # The game modes' capture points, objectives and spawns; a level without any is not an error. A level
    # extracted for the first time keeps layouts made before (nothing is replaced); extracting it again redoes both.
    have_layouts = out.is_dir() and any(p.name.lower() == f"{m.id.lower()}.layouts.json" for p in out.iterdir())
    if had_level or not have_layouts:
        cli.main(["layouts", m.id, "--game", str(game), "-o", str(out)])
    return _outputs(out, m)


# --------------------------------------------------------------------------- content: catalogue and models


def _source(id_: str, title: str, sources: list[Path], kind: str) -> MapSource:
    """A content entry: the kit's MapSource with `kind` (set by hand on a kit that has no `kind` yet)."""
    try:
        return MapSource(id_, title, sources, kind=kind)  # type: ignore[call-arg]
    except TypeError:
        m = MapSource(id_, title, sources)
        m.kind = kind  # type: ignore[attr-defined]
        return m


def _tables(game: Path, pattern: str) -> list[Path]:
    from .cli import _legacy
    from .soldiergear import bf6_tables, legacy_tables

    g = _legacy(game)
    if g is None:
        return [t for t in bf6_tables(game) if re.search(pattern, t.stem, re.I)]
    return legacy_tables(g, pattern)


def _contents(game: Path) -> list[MapSource]:
    """The catalogue (vehicles, weapons, gadgets) and the vehicles' model pack, by the tables they are read from."""
    out = []
    gear = _tables(game, r"vehicle|weapon|character")
    if gear:
        out.append(_source("catalog", "Vehicles, weapons and gadgets", gear, "catalog"))
    vehicles = _tables(game, r"vehicle")
    if vehicles:
        out.append(_source("models", "Vehicle models", vehicles, "models"))
    return out


def _content_files(out: Path, m: MapSource) -> list[Path]:
    if m.id == "catalog":
        return [out / "catalog.json"]
    if m.id == "models":
        return [out.parent / "model-packs" / out.name / "model-pack.json"]
    return []


def _extract_content(game: Path, m: MapSource, out: Path, log) -> list[Path]:
    """Writes the catalogue or the model pack of this install (`out` is `<levels>/<game>`)."""
    import argparse

    from . import gearcli

    if m.id == "catalog":
        code = gearcli.catalog(argparse.Namespace(install=game, out=out.parent))
        if code != 0:
            raise RuntimeError(f"catalog exited {code}")
        return [p for p in _content_files(out, m) if p.is_file()]
    if m.id == "models":
        failed = gearcli.models(argparse.Namespace(install=game, out=out.parent, only=None, force=False))
        if failed:
            raise RuntimeError(f"models: {failed} vehicles failed")
        pack = out.parent / "model-packs" / out.name
        return sorted(pack.glob("*.glb")) + [p for p in _content_files(out, m) if p.is_file()]
    raise ValueError(f"no content called {m.id!r}")


def _catalog_items(game: Path) -> dict[str, list[str]]:
    """The item ids the install holds by kind (vehicle, weapon, gadget), as the catalogue names them."""
    from . import soldiergear as sg
    from .cli import _legacy

    g = _legacy(game)
    if g is None:
        from .frostbitebundle import LevelCatalogue
        from .frostbitegear import bf6_vehicles_table, vehicles

        table = bf6_vehicles_table(game)
        vids = sorted(vehicles(LevelCatalogue(table))) if table is not None else []
        gear = sg.bf6_gear(game)
    else:
        vids = sg.legacy_vehicle_ids(g)
        gear = sg.legacy_gear(g)
    found: dict[str, list[str]] = {"vehicle": vids}
    for item in gear:
        found.setdefault(item["kind"], []).append(item["id"])
    return {k: sorted(v) for k, v in found.items()}


def _build(game: Path) -> str | None:
    from .gearcli import _game_build

    b = _game_build(game)
    return None if b == "unknown" else b


def _checks(found: dict, levels: Path) -> list[Check]:
    from . import library

    checks = [Check(
        "gamefiles", "3DHeat GameFiles (the library the readers build on)", library.ensure(),
        "found" if library.ensure() else library.MISSING,
    )]
    bf6 = found.get("bf6")
    if bf6 is not None and checks[0].ok:
        from heat3d_gamefiles.oodle import find_oodle

        own = next((p for p in sorted(bf6.glob("oo2core_*_win64.dll"))), None)
        lib = own or find_oodle(bf6)
        checks.append(Check(
            "oodle", "Oodle library (from your own Battlefield 6 install)", lib is not None,
            str(lib) if lib else "not found; Battlefield 6 levels need it (4 and 1 do not). "
                                 "Set HEAT3D_OODLE to the oo2core_*_win64.dll in the game's folder.",
        ))
    return checks


def _game(key: str, maps, output_version: str) -> GameSpec:
    label, folder_name, _ = GAMES[key]
    g = GameSpec(
        key=key, label=label, find=_finder(key), subdir=folder_name.lower().replace(" ", "-"), build=_build,
        maps=maps, extract=_extract, existing_outputs=_outputs, output_version=output_version,
        platforms=("windows-x64",),
    )
    # The new-content hooks, set as attributes so a kit without them still runs.
    g.contents = _contents  # type: ignore[attr-defined]
    g.extract_content = _extract_content  # type: ignore[attr-defined]
    g.catalog_items = _catalog_items  # type: ignore[attr-defined]
    return g


SPEC = Spec(
    id="heat3d-battlefield",
    name="3DHeat Battlefield",
    repo="Holdi601/3DHeat-Ext-Battlefield",
    version=__version__,
    tools={"heat3d-battlefield-maps": "heat3d_ext_battlefield.cli:main"},
    default_tool="heat3d-battlefield-maps",
    description="Battlefield 6, 4 and 1 levels as 3D levels for the 3DHeat viewer",
    module="heat3d_ext_battlefield.standalone_spec",
    games=[_game("bf6", _maps_modern, "0.3.0"), _game("bf4", _maps_legacy, "0.3.0"), _game("bf1", _maps_legacy, "0.3.0")],
    checks=_checks,
    min_free_gb=5.0,
    notice="Not affiliated with or endorsed by Electronic Arts or DICE.",
)

if __name__ == "__main__":
    from . import update
    from .app.entry import main

    raise SystemExit(main(SPEC, apply_source=update.apply))
