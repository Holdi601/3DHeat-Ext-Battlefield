import numpy as np

from heat3d_ext_battlefield.frostbitegear import describe, to_frame
from heat3d_ext_battlefield.legacygear import _mat
from heat3d_ext_battlefield.modelpack import norm_key


def test_battlefield6_vehicle_names_and_classes():
    d = describe("tank_abrams", "common/hardware/vehicles/tank/abrams/art/ob_veh_tank_abrams_base_mesh")
    assert (d["key"], d["class"], d["domain"]) == ("M1A2 SEPv3", "mbt", "ground")
    assert describe("helicopter_uh60", "x")["domain"] == "air"
    assert describe("tank_unknownthing", "x")["class"] == "mbt"


def test_frostbite_frame_and_transforms():
    # x left, y up, z forward -> x forward, y up, z right: a rotation
    assert to_frame(np.array([[1.0, 2.0, 3.0]])).tolist() == [[3.0, 2.0, -1.0]]
    m = _mat([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 4, 5, 6, 0])
    p = np.array([1.0, 1.0, 1.0]) @ m[:3, :3] + m[3, :3]
    assert p.tolist() == [5.0, 6.0, 7.0]
    assert norm_key("M1A2 SEP") == "m1a2sep"
