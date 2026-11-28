"""Weapons and gadgets for the catalogue, and the new-content hooks of the standalone spec (synthetic names only)."""

from __future__ import annotations

from pathlib import Path

from heat3d_ext_battlefield import soldiergear as sg
from heat3d_ext_battlefield import standalone_spec as ss
from heat3d_ext_battlefield.app.spec import MapSource


def test_battlefield6_weapons_and_gadgets_from_their_art_folders():
    names = [
        "common/hardware/weapons/carbine/m4a1/art/ob_wep_m4a1_base_3p_mesh",
        "common/hardware/weapons/carbine/m4a1/art/t_wep_m4a1_cs",
        "common/hardware/weapons/_attachments/suppressor/x/art/mesh",
        "common/hardware/weapons/melee/combatknife/art/mesh",
        "common/hardware/gadgets/launchers/m136at4/art/ob_gad_m136at4_1p_mesh",
        "common/hardware/gadgets/throwables/frag/art/ob_gad_throwable_frag_base_3p_mesh",
        "common/hardware/gadgets/tools/repair/art/mesh",
        "common/hardware/gadgets/misc/dogtags/art/mesh",
        "game/someportal/common/hardware/gadgets/tools/newtool/art/mesh",
    ]
    items = {i["id"]: i for i in sg.bf6_items(names)}
    assert set(items) == {"carbine_m4a1", "melee_combatknife", "launchers_m136at4", "throwables_frag",
                          "tools_repair", "tools_newtool"}
    assert items["carbine_m4a1"] == {"id": "carbine_m4a1", "kind": "weapon", "name": "M4A1", "class": "carbine",
                                     "folder": "common/hardware/weapons/carbine/m4a1"}
    assert (items["launchers_m136at4"]["kind"], items["launchers_m136at4"]["name"]) == ("gadget", "M136 AT4")
    assert items["launchers_m136at4"]["class"] == "launcher"
    assert items["throwables_frag"]["class"] == "grenade"
    assert items["tools_repair"]["class"] == "support"
    assert items["melee_combatknife"]["class"] == "melee"


def test_legacy_blueprints_as_weapons_and_gadgets():
    c4 = sg.legacy_item("Gameplay/Gadgets/C4/C4", 25, "C4")
    assert (c4["id"], c4["kind"], c4["name"], c4["class"]) == ("c4", "gadget", "C4", "explosive")
    ak = sg.legacy_item("Gameplay/Weapons/AK12/AK12", 16, "AK12")
    assert (ak["kind"], ak["class"], ak["weaponClass"]) == ("weapon", "assault-rifle", 16)
    knife = sg.legacy_item("Gameplay/Gadgets/Knife/Knife", 28, "Knife")
    assert (knife["kind"], knife["class"]) == ("weapon", "melee")
    # A kill-feed name another item's (Battlefield 1 reuses them): the blueprint's own name instead.
    mortars = sg.unique_names([sg.legacy_item(f"Gameplay/Gadgets/Support/Mortar/{n}", 31, "Mortar")
                               for n in ("Mortar", "Mortar_HE")])
    assert [m["name"] for m in mortars] == ["Mortar", "Mortar HE"] and mortars[1]["class"] == "launcher"
    bf1 = sg.legacy_item("Gameplay/Weapons/SideArms/Mauser1914/Mauser1914", 18, "Beretta M1915")
    assert bf1["class"] == "pistol" and bf1["name"] != "Beretta M1915"
    assert sg.legacy_item("Gameplay/Gadgets/MGL/MGL_AI", 21, "MGL") is None
    assert sg.legacy_item("Gameplay/Gadgets/SP_Visor/SP_Visor", 29, "SP_Visor") is None
    assert sg.legacy_item("Gameplay/Weapons/BlankWeapon/BlankWeaponBlueprint", 38, "BlankWeapon") is None


def test_battlefield6_outputs_found_under_the_names_they_were_written_with(tmp_path):
    out = tmp_path / "battlefield-6"
    out.mkdir()
    for name in ("capstone_textured_ground_nav.glb", "capstone_textured_ground_nav.layouts.json",
                 "mp_aftermath_portal.layouts.json", "aftermath_textured_ground_nav.glb", "mp_atoll.layouts.json"):
        (out / name).write_bytes(b"x")
    level = lambda i: MapSource(i, i, [])  # noqa: E731
    assert [p.name for p in ss._outputs(out, level("mp_capstone"))] == [
        "capstone_textured_ground_nav.glb", "capstone_textured_ground_nav.layouts.json"]
    assert [p.name for p in ss._outputs(out, level("mp_aftermath"))] == ["aftermath_textured_ground_nav.glb"]
    # Layouts alone are not the level: it was never extracted.
    assert ss._outputs(out, level("mp_atoll")) == []
    assert ss._outputs(out, level("mp_aftermath_portal")) == []
    (out / "mp_atoll.glb").write_bytes(b"x")
    assert [p.name for p in ss._outputs(out, level("mp_atoll"))] == ["mp_atoll.glb", "mp_atoll.layouts.json"]


def test_content_entries_and_their_files(tmp_path):
    out = tmp_path / "levels" / "battlefield-4"
    cat = ss._source("catalog", "Vehicles, weapons and gadgets", [], "catalog")
    models = ss._source("models", "Vehicle models", [], "models")
    assert (cat.kind, models.kind) == ("catalog", "models")
    assert ss._content_files(out, cat) == [out / "catalog.json"]
    assert ss._content_files(out, models) == [tmp_path / "levels" / "model-packs" / "battlefield-4" / "model-pack.json"]
    assert ss._outputs(out, cat) == []
    out.mkdir(parents=True)
    (out / "catalog.json").write_text("{}", encoding="utf-8")
    assert ss._outputs(out, cat) == [out / "catalog.json"]
    for g in ss.SPEC.games:
        assert g.contents is ss._contents and g.catalog_items is ss._catalog_items and g.extract_content


def test_lobbies_are_not_maps():
    assert ss.NOT_A_MAP.search("mp_portal_lobby")
    assert not ss.NOT_A_MAP.search("mp_portal_communitymap_1")
    assert not ss.NOT_A_MAP.search("mp_granite_carrier_portal")


def test_first_extract_keeps_layouts_made_before(tmp_path, monkeypatch):
    calls = []

    def fake_main(argv):
        calls.append(argv[0])
        if argv[0] == "level":
            Path(argv[argv.index("-o") + 1]).write_bytes(b"glb")
        return 0

    monkeypatch.setattr("heat3d_ext_battlefield.cli.main", fake_main)
    monkeypatch.setattr(ss, "_generation", lambda game: "modern")
    out = tmp_path / "battlefield-6"
    out.mkdir()
    (out / "mp_atoll.layouts.json").write_text("{}", encoding="utf-8")
    m = MapSource("mp_atoll", "mp_atoll", [])
    assert [p.name for p in ss._extract(tmp_path, m, out, print)] == ["mp_atoll.glb", "mp_atoll.layouts.json"]
    assert calls == ["level"]
    # Extracted again (a game update): the layouts too.
    ss._extract(tmp_path, m, out, print)
    assert calls == ["level", "level", "layouts"]
