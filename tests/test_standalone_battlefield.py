"""The standalone app on synthetic installs: Battlefield 6 and 4 levels as maps, a new level found as new."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from heat3d_ext_battlefield import standalone_spec
from heat3d_ext_battlefield.app import entry, paths
from heat3d_ext_battlefield.standalone_spec import SPEC

from . import frostbite_fixtures as fx


def bf6_level(root: Path, name: str) -> Path:
    path = root / "Data" / "Win32" / "game" / "levels" / name / f"{name}.toc"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(fx.level_table([(b"G" * 16, fx.location(1, 1, 0, 4))], [fx.bundle_blob([(1, 1, 0, 4)])]))
    return path


def bf4_level(root: Path, name: str) -> None:
    folder = root / "Data" / "Win32" / "levels" / "mp" / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.toc").write_bytes(name.encode() * 4)
    (folder / f"{name}.sb").write_bytes(b"")


@pytest.fixture
def steam(tmp_path, monkeypatch):
    """A Steam library holding Battlefield 6 and Battlefield 4 (no Battlefield 1)."""
    lib = tmp_path / "Steam"
    common = lib / "steamapps" / "common"
    bf6 = common / "Battlefield 6"
    (bf6 / "Data").mkdir(parents=True)
    (bf6 / "Data" / "layout.toc").write_bytes(b"")
    bf6_level(bf6, "mp_alpha")
    bf4 = common / "Battlefield 4"
    (bf4 / "Data").mkdir(parents=True)
    (bf4 / "Data" / "layout.toc").write_bytes(b"")
    (bf4 / "Data" / "cas.cat").write_bytes(b"")
    bf4_level(bf4, "mp_bravo")
    bf4_level(bf4, "mp_charlie")
    monkeypatch.setattr(paths, "steam_roots", lambda: [lib])
    monkeypatch.setattr("heat3d_ext_battlefield.cli.LAUNCHER_FOLDERS", ())
    monkeypatch.delenv("HEAT3D_BATTLEFIELD_GAME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "appdata"))
    monkeypatch.setenv("HEAT3D_LEVELS", str(tmp_path / "levels"))
    monkeypatch.setenv("HEAT3D_NO_UPDATE", "1")
    return {"bf6": bf6, "bf4": bf4}


def games(capsys) -> dict:
    assert entry.main(SPEC, ["status", "--json"]) == 0
    return {g["game"]: g for g in json.loads(capsys.readouterr().out)["games"]}


def test_find_and_maps(steam):
    by_key = {g.key: g for g in SPEC.games}
    assert by_key["bf6"].find(None) == steam["bf6"]
    assert by_key["bf4"].find(None) == steam["bf4"]
    assert by_key["bf1"].find(None) is None
    assert by_key["bf4"].find(str(steam["bf6"])) is None  # a folder of the other generation is not taken
    assert [m.id for m in by_key["bf6"].maps(steam["bf6"])] == ["mp_alpha"]
    assert [m.id for m in by_key["bf4"].maps(steam["bf4"])] == ["mp_bravo", "mp_charlie"]


def test_install_that_gains_a_level(steam, tmp_path, monkeypatch, capsys):
    def fake_extract(game, m, out, log):
        out.mkdir(parents=True, exist_ok=True)
        glb = out / f"{m.id.upper()}.glb"  # named as the game names the level
        glb.write_bytes(b"glb")
        return [glb]

    for g in SPEC.games:
        monkeypatch.setattr(g, "extract", fake_extract)
    found = games(capsys)
    assert found["bf6"]["found"] and found["bf4"]["found"] and not found["bf1"]["found"]
    assert found["bf4"]["counts"]["new"] == 2

    assert entry.main(SPEC, ["extract", "--game", "bf4", "--new", "--progress-json"]) == 0
    events = [json.loads(l) for l in capsys.readouterr().out.splitlines() if l.startswith("{")]
    assert events[-1] == {"event": "done", "ok": 2, "failed": 0}
    man = json.loads((tmp_path / "levels" / "battlefield-4" / ".heat3d-extract.json").read_text(encoding="utf-8"))
    assert man["entries"]["mp_bravo"]["outputs"] == ["battlefield-4/MP_BRAVO.glb"]

    # A game update ships a new level: it is new, the extracted ones stay current.
    bf4_level(steam["bf4"], "mp_delta")
    states = {m["id"]: m["state"] for m in games(capsys)["bf4"]["maps"]}
    assert states == {"mp_bravo": "current", "mp_charlie": "current", "mp_delta": "new"}


def test_untracked_level_is_current_when_newer_else_outdated(steam, tmp_path, capsys):
    # A level extracted before the extract record existed: newer than the game files it is current (and said
    # to be untracked), older outdated.
    out = tmp_path / "levels" / "battlefield-4"
    out.mkdir(parents=True)
    glb = out / "MP_Bravo.glb"
    glb.write_bytes(b"old")
    assert [p.name for p in standalone_spec._outputs(out, SPEC.games[1].maps(steam["bf4"])[0])] == ["MP_Bravo.glb"]
    maps = {m["id"]: (m["state"], m.get("untracked")) for m in games(capsys)["bf4"]["maps"]}
    assert maps["mp_bravo"] == ("current", True) and maps["mp_charlie"][0] == "new"
    os.utime(glb, (1, 1))
    states = {m["id"]: m["state"] for m in games(capsys)["bf4"]["maps"]}
    assert states == {"mp_bravo": "outdated", "mp_charlie": "new"}
