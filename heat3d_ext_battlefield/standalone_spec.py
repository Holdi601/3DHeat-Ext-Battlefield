"""
The standalone app's description of this tool (app/spec.py): the Battlefield
6, 4 and 1 installs it reads, the checks before a level can be extracted, and
their levels as maps (new ones after a game update are found by
app/manifest.py). `python -m heat3d_ext_battlefield.standalone_spec` runs the
app from a checkout; the release executables run the same.
"""

from __future__ import annotations

import os
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


def _maps_modern(game: Path) -> list[MapSource]:
    from .frostbitebundle import level_sources

    return [MapSource(name, name, [t.toc, *t.supplements], note=t.source)
            for name, t in sorted(level_sources(game).items())]


def _maps_legacy(game: Path) -> list[MapSource]:
    from .cli import _legacy

    g = _legacy(game)
    if g is None:
        return []
    return [MapSource(name, name, list(tocs), note=tocs[0].relative_to(game).parts[0])
            for name, tocs in sorted(g.multiplayer_levels().items())]


def _outputs(out: Path, m: MapSource) -> list[Path]:
    """The level's .glb (named as the game names it, `MP_Prison` for `mp_prison`) and its layouts."""
    if not out.is_dir():
        return []
    return sorted(p for p in out.iterdir() if p.is_file() and p.name.lower() in (f"{m.id}.glb", f"{m.id}.layouts.json"))


def _extract(game: Path, m: MapSource, out: Path, log) -> list[Path]:
    from . import cli

    target = out / f"{m.id}.glb" if _generation(game) == "modern" else out
    code = cli.main(["level", m.id, "--game", str(game), "-o", str(target)])
    if code != 0:
        raise RuntimeError(f"heat3d-battlefield-maps level exited {code}")
    # The game modes' capture points, objectives and spawns; a level without any is not an error.
    cli.main(["layouts", m.id, "--game", str(game), "-o", str(out)])
    return _outputs(out, m)


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
    return GameSpec(
        key=key, label=label, find=_finder(key), subdir=folder_name.lower().replace(" ", "-"), build=_build,
        maps=maps, extract=_extract, existing_outputs=_outputs, output_version=output_version,
        platforms=("windows-x64",),
    )


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
