"""The layouts reader's pieces that need no game files."""

import numpy as np

from heat3d_ext_battlefield.legacylayouts import (
    _inside,
    _letter,
    _nice_name,
    field_id,
    interface_value,
    mode_name,
    objective_kind,
)


def test_interface_values():
    m = interface_value("LinearTransform ((1,0,0),(0,1,0),(0,0,1),(-784.5897,992.0308,-378.7326))")
    assert np.allclose(m[3, :3], (-784.5897, 992.0308, -378.7326))
    assert interface_value('CString "ID_CAP_STORAGE"') == "ID_CAP_STORAGE"
    assert interface_value("Float32 15") == 15.0
    assert interface_value("TeamId Team2") == 2
    assert interface_value("Boolean True") is True


def test_field_ids_are_the_name_hash():
    # As the game's connections name them.
    assert field_id("BlueprintTransform") == -409930682
    assert field_id("CaptureRadius") == 1043301209


def test_names():
    assert _nice_name("ID_CAP_MACHINE_ROOM") == "Machine Room"
    assert _letter("cq_capturepointprefab_bf4_b_short", []) == "B"
    assert _letter("generic", ["x", "C"]) == "C"
    assert mode_name("ConquestLarge0") == "Conquest Large"
    assert mode_name("SomethingNew0") == "Something New"
    assert objective_kind("rush_base_objective") == ("mcom", "M-COM")
    assert objective_kind("bombdropoff_team1")[0] == "bomb_target"


def test_inside():
    square = [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]]
    assert _inside([5, 0, 5], square)
    assert not _inside([15, 0, 5], square)
    assert _inside([15, 0, 5], square, 6.0)


def test_vehicle_kinds():
    from heat3d_ext_battlefield.legacylayouts import SPAWNER, vehicle_class_of

    assert SPAWNER.search("spawnerprefab_tank_mbt").group(1) == "tank_mbt"
    assert SPAWNER.search("spawnerprefab_static_aa_nongroupable_autogen_win32").group(1) == "static_aa"
    assert SPAWNER.search("spawnerprefab_static_mg_neutral").group(1) == "static_mg"
    assert vehicle_class_of("tank_mbt") == "tank"
    assert vehicle_class_of("car_heavy") == "car"
    assert vehicle_class_of("boat_attack") == "boat"
    assert vehicle_class_of("heli_scout") == "helicopter"
    assert vehicle_class_of("static_aa") == "stationary"
    assert vehicle_class_of("gameplay/vehicles/pwc_jetski/pwc_jetski") == "boat"


def test_spawn_owners_rules_and_drops():
    from heat3d_ext_battlefield.legacylayouts import Layout, _finish_spawns, _own

    lay = Layout("ConquestLarge0")
    a = {"id": "", "type": "capture_zone", "team": None, "letter": "A", "name": "A", "position": [0, 0, 0], "radius": 10}
    hq = {"id": "", "type": "base", "team": 1, "letter": "", "name": "HQ", "position": [500, 0, 0]}
    lay.objectives = [a, hq]
    linked = {"type": "spawn", "team": 1, "position": [5, 0, 5], "heading": 0}
    at_hq = {"type": "vehicle_spawn", "team": None, "position": [505, 0, 0], "heading": 0, "vehicleKind": "tank"}
    near = {"type": "spawn", "team": 2, "position": [40, 0, 0], "heading": 0}
    far = {"type": "spawn", "team": 2, "position": [2000, 0, 0], "heading": 0}
    spare = {"type": "spawn", "team": None, "position": [0, 0, 0], "heading": 0}
    gun = {"type": "vehicle_spawn", "team": None, "position": [30, 0, 0], "heading": 0, "vehicleKind": "stationary"}
    lay.spawns = [linked, at_hq, near, far, spare, gun]
    _own(linked, a, "prefab")
    _own(linked, a, "link")
    _own(linked, hq, "nearest")
    _own(at_hq, hq, "link")
    # Fewer than half linked: nothing is given its nearest flag.
    _finish_spawns(lay)
    assert a["id"] == "A" and hq["id"] == "HQ1"
    assert linked["baseId"] == "A" and linked["baseSource"] == "link" and linked["rule"] == "flag"
    assert at_hq["baseId"] == "HQ1" and at_hq["rule"] == "hq" and at_hq["team"] == 1
    assert "baseId" not in near and near["rule"] == "team"
    assert gun["rule"] == "free"
    assert spare not in lay.spawns and lay.dropped == {"at the origin (a prefab's spare)": 1}

    lay = Layout("ConquestLarge0")
    a = dict(a, id="")
    lay.objectives = [a]
    one = {"type": "spawn", "team": 1, "position": [5, 0, 5], "heading": 0}
    two = {"type": "spawn", "team": 1, "position": [6, 0, 5], "heading": 0}
    near = {"type": "spawn", "team": 2, "position": [40, 0, 0], "heading": 0}
    far = {"type": "spawn", "team": 2, "position": [2000, 0, 0], "heading": 0}
    lay.spawns = [one, two, near, far]
    _own(one, a, "link")
    _own(two, a, "link")
    _finish_spawns(lay)
    # Half linked: the rest within reach of a flag get the nearest, marked so.
    assert near["baseId"] == "A" and near["baseSource"] == "nearest"
    assert "baseId" not in far
