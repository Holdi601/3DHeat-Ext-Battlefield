"""The command line: the verbs and options 3DHeat GameFiles passes through, identify, the exit codes."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from heat3d_ext_battlefield import cli, library

from .test_frostbite import _install

ROOT = Path(__file__).resolve().parents[1]


def test_level_takes_every_option_of_the_gamefiles_verb(tmp_path):
    args = cli.parser().parse_args([
        "level", "the test level", "-o", str(tmp_path / "x.glb"), "--install", str(tmp_path),
        "--detail-budget", "3000000", "--textures", "--ground-texture", "--navmesh", "--by-mesh",
        "--clamped-uvs", "--ground-spacing", "8", "--skip", "a", "--skip", "b",
    ])
    assert args.level == "the test level"
    assert args.out == tmp_path / "x.glb" and args.install == tmp_path
    assert args.detail_budget == 3000000
    assert args.textures == 512 and args.ground_texture == 0.5
    assert args.navmesh and args.by_mesh and args.clamped_uvs
    assert args.ground_spacing == 8.0 and args.skip == ["a", "b"]


def test_level_defaults_match_gamefiles():
    args = cli.parser().parse_args(["level", "x"])
    assert args.out is None and args.install is None and args.detail_budget is None
    assert args.textures == 0 and args.ground_texture == 0.0 and args.ground_spacing == 4.0
    assert not (args.navmesh or args.by_mesh or args.clamped_uvs) and args.skip is None


def test_identify_names_a_table_of_contents(tmp_path, capsys):
    root = _install(tmp_path / "game", [{"name": "Win32/the_test_level", "installBundle": "win32/the_test_level"}])
    assert cli.main(["identify", str(root / "Data" / "layout.toc")]) == 0
    assert "Frostbite table of contents" in capsys.readouterr().out


def test_identify_turns_away_another_file_quietly(tmp_path, capsys):
    other = tmp_path / "notes.bin"
    other.write_bytes(b"PK\x03\x04 not a table of contents" * 4)
    assert cli.main(["identify", str(other)]) == 2
    out = capsys.readouterr()
    assert out.out == "" and out.err.strip() == "not a Battlefield file"


def test_identify_a_missing_file(tmp_path, capsys):
    assert cli.main(["identify", str(tmp_path / "gone.toc")]) == 2
    assert "no such file" in capsys.readouterr().err


def test_levels_says_how_to_point_at_the_game(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_frostbite_install", lambda given: given)
    assert cli.main(["levels"]) == 2
    assert "--install" in capsys.readouterr().err


def test_levels_lists_a_made_up_install(tmp_path, capsys):
    root = _install(tmp_path / "game", [])
    assert cli.main(["levels", "--install", str(root)]) == 0
    assert capsys.readouterr().out.strip() == f"0 levels in {root}"


def test_without_gamefiles_it_says_what_to_do(tmp_path):
    # A copy of the package alone, nowhere near GameFiles.
    import shutil

    shutil.copytree(ROOT / "heat3d_ext_battlefield", tmp_path / "pkg" / "heat3d_ext_battlefield",
                    ignore=shutil.ignore_patterns("__pycache__"))
    env = {k: v for k, v in os.environ.items() if k not in ("HEAT3D_GAMEFILES", "PYTHONPATH")}
    r = subprocess.run([sys.executable, "-I", "-c", "import sys; sys.path.insert(0, sys.argv[1]); "
                        "from heat3d_ext_battlefield.cli import main; sys.exit(main(['identify', 'gone.toc']))",
                        str(tmp_path / "pkg")], capture_output=True, text=True, env=env)
    if r.returncode != 2 or library.MISSING not in r.stderr:
        pytest.skip("heat3d_gamefiles is installed in this Python, so it is always found")
    assert r.stderr.strip() == library.MISSING
