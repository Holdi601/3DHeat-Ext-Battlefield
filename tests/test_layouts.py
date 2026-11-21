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
