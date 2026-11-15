"""Write docs/cli-reference.md from the code itself, so the reference cannot drift.

The options come from the program's own `--help` for every verb; the level's
parts from the part names the code gives them.

    python tools/gen_docs_reference.py          # rewrite the page
    python tools/gen_docs_reference.py --check  # exit 1 when the page is stale
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "cli-reference.md"
COMMAND = "heat3d-battlefield-maps"
PACKAGE = "heat3d_ext_battlefield"
VERBS = ["levels", "level", "identify"]


def run(args):
    env = dict(os.environ, HEAT3D_NO_UPDATE="1", COLUMNS="88", PYTHONIOENCODING="utf-8",
               PYTHONPATH=str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    r = subprocess.run([sys.executable, "-m", PACKAGE] + args, capture_output=True, text=True,
                       env=env, encoding="utf-8", cwd=ROOT)
    return (r.stdout or r.stderr).rstrip()


def outputs():
    sys.path.insert(0, str(ROOT))
    from heat3d_ext_battlefield import frostbitelevel as fl

    kinds = ", ".join(f"`{name}`" for name, _ in fl.CATEGORIES)
    return ["### `.glb` parts", "",
            f"`{fl.TERRAIN_PART}` (the heightfield; `{fl.TERRAIN_PART} x<x> z<z>` per tile with `--ground-texture`), "
            f"`{fl.BACKDROP_PART}`, `{fl.BLEND_PART}`; per kind of mesh {kinds}, else `structure:props` "
            f"(with `--textures`, one part per colour map: `<kind> <texture>`); `<part>{fl.DESTRUCTIBLE}` for what a "
            f"match can destroy; `{fl.NAV_PART}` with `--navmesh`; `<part> (average colour)` with `--clamped-uvs`; "
            "`<part> | <mesh> | <material>` with `--by-mesh`.", "",
            "`asset.generator`: `heat3d_gamefiles` (the glTF writer of 3DHeat GameFiles).", ""]


def build():
    out = ["---", "title: Command reference", "nav_order: 90", "---", "", "# Command reference", "",
           "Generated from the code by `tools/gen_docs_reference.py`: do not edit by hand.",
           "The other pages explain each command step by step.", "",
           f"## `{COMMAND}`", "", "```text", run(["--help"]), "```", ""]
    for v in VERBS:
        out += [f"## `{v}`", "", "```text", run([v, "--help"]), "```", ""]
    out += ["## Output", ""]
    return "\n".join(out + outputs())


if __name__ == "__main__":
    text = build()
    if "--check" in sys.argv:
        sys.exit(0 if OUT.exists() and OUT.read_text(encoding="utf-8") == text else 1)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("wrote", OUT.relative_to(ROOT))
