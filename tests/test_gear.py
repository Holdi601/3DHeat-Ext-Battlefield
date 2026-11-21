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


def test_hit_regions_split_by_direction_zone_and_piece():
    from heat3d_ext_battlefield.legacygear import hit_regions, zone_of_normals

    n = np.array([[1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0.2]], float)
    assert zone_of_normals(n, {"front", "top"}).tolist() == ["front", "rear", "right", "left", "top", "right"]
    # Flat faces without a top zone go with the side they lie on.
    at = np.array([[3, 0, 0], [-3, 0, 0], [0, 0, 1], [0, 0, -1], [0.1, 1, 0.5], [0, -1, -0.9]], float)
    assert zone_of_normals(n, set(), at).tolist() == ["front", "rear", "right", "left", "right", "left"]
    # A box in the game's frame (x left, y up, z forward): part index 3 is a destructible piece.
    v = np.array([[x, y, z] for x in (-1, 1) for y in (0, 1) for z in (-2, 2)], float)
    quads = [[i for i in range(8) if (v[i, ax] > v[:, ax].mean()) == hi] for ax in range(3) for hi in (False, True)]
    f = np.array([t for q in quads for t in ([q[0], q[1], q[3]], [q[0], q[3], q[2]])])
    # Wound outwards, as the game's meshes are.
    c = v[f].mean(1)
    nrm = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    f = np.where(((nrm * c).sum(1) < 0)[:, None], f[:, [0, 2, 1]], f)
    tri_part = np.array(["hull"] * 12, object)
    pidx = np.array([0] * 10 + [3, 3])
    zones = {z: {"hp": 1000.0, "shield": 0.0, "minAngle": 0.0, "angleMultiplier": 1.0, "angleDamage": False}
             for z in ("front", "rear", "left", "right", "top")}
    out = hit_regions([(v, f, tri_part, pidx, "m_side")], {3: (100.0, False), 0: (100000.0, True)}, zones)
    names = {name: ex for name, _v, _f, ex in out}
    assert {"hull_front", "hull_rear", "hull_left", "hull_right", "hull_top", "piece3"} <= set(names)
    assert names["piece3"] == {"part": "hull", "group": "piece", "hp": 100.0, "material": "m_side"}
    assert names["hull_front"]["zone"] == "front" and names["hull_front"]["hp"] == 1000.0
    # The front zone is the faces at the front (game z = +2 -> figure x = +2).
    fv = next(v2 for name, v2, _f, _e in out if name == "hull_front")
    assert np.allclose(fv[:, 0], 2.0)
