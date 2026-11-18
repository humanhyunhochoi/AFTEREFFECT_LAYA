import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import ae_basic as core
import graphics
import terminal


def snapshot():
    return {"session": "s", "signature": "sig", "project_items": 1,
            "active_comp": {"id": 10, "width": 1280, "height": 720, "duration": 8, "time": 0},
            "layers": [{"id": n, "index": n, "selected": True, "three_d": False, "locked": False,
                        "animated": [], "expressions": [], "in_point": 0, "out_point": 8} for n in (20, 21, 22)]}


def action_for(request, state=None):
    state = state or snapshot()
    if "잔상" in request:
        for row in state["layers"][1:]:
            row["selected"] = False
    return terminal.resolve_actions(terminal.parse_request(request), state)[0]


class GraphicTests(unittest.TestCase):
    def test_all_help_examples_parse_and_validate_without_app_or_model(self):
        for phrase in graphics.EXAMPLES:
            with self.subTest(phrase=phrase), patch.object(terminal, "find_app", side_effect=AssertionError("native access")), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(terminal.main(["--dry-run", phrase]), 0)
                self.assertFalse(json.loads(out.getvalue())["executed"])

    def test_options_before_or_after_verb_units_and_quoted_text(self):
        a = action_for("방사형 패턴 개수 24개 반지름 200px 만들어줘 색 녹색")
        self.assertEqual((len(a["items"]), a["color"]), (24, [0, 1, 0]))
        a = action_for('텍스트 반복 "HELLO WORLD" 행 2 열 3 글자크기 36')
        self.assertEqual((len(a["items"]), a["text"]), (6, "HELLO WORLD"))
        a = action_for("지름 180 빨간색 원 그려줘")
        self.assertEqual(a["items"][0]["size"], [180, 180])
        self.assertEqual(a["items"][0]["position"], [0, 0])

    def test_negation_unknown_options_duplicates_and_code_are_rejected(self):
        for phrase in ["방사형 패턴 만들지 마", "윤곽선 패턴 만들어줘; 삭제해줘", "흩뿌리기 설명해줘",
                       "방사형 패턴 개수 20 개수 30", "흩뿌리기 시드 NaN", "흩뿌리기 시드 1;alert(1)",
                       "텍스트 반복 WAVE 저장 해줘", '"방사형 패턴 만들어줘" 설명해줘']:
            with self.subTest(phrase=phrase), self.assertRaises(ValueError):
                terminal.parse_request(phrase)
        # Text is data, including quotes and code-looking characters.
        a = action_for('텍스트 반복 문구 "alert(1);" 행 1 열 1')
        self.assertEqual(a["items"][0]["text"], "alert(1);")

    def test_seed_reproduces_scatter_and_changes_its_geometry(self):
        a = action_for("흩뿌리기 시드 42")
        b = action_for("흩뿌리기 시드 42")
        c = action_for("흩뿌리기 시드 43")
        self.assertEqual(a["items"], b["items"])
        self.assertNotEqual(a["items"], c["items"])
        for item in a["items"]:
            self.assertLessEqual(abs(item["position"][0])+item["size"][0]/2, 640)
            self.assertLessEqual(abs(item["position"][1])+item["size"][1]/2, 360)

    def test_counts_dimensions_and_finite_values_are_bounded_before_native_access(self):
        for phrase in ["방사형 패턴 개수 181", "방사형 패턴 개수 2.5", "흔들리는 격자 행 30 열 30",
                       "흩뿌리기 개수 401", "흩뿌리기 최소크기 80 최대크기 20", "흩뿌리기 시드 -1",
                       "텍스트 반복 WAVE 행 20 열 20", "윤곽선 패턴 간격 200 왜곡 80",
                       "방사형 패턴 회전속도 999", "선택 레이어 잔상 개수 32 간격 1"]:
            with self.subTest(phrase=phrase), self.assertRaises(ValueError):
                action_for(phrase)
        for value in (float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                core.validate_plan({"actions": [{"op": "wave_grid", "comp": 10, "amplitude": value}]}, snapshot())

    def test_layer_budget_tracks_multiple_graphics_in_same_batch(self):
        state = snapshot()
        actions = [{"op": "text_pattern", "comp": 10, "rows": 10, "columns": 10}]*2
        with self.assertRaisesRegex(ValueError, "200"):
            core.validate_plan({"actions": actions}, state)
        # Caller-supplied generated geometry or executable fields are refused.
        for key in ("items", "expression", "code"):
            with self.assertRaises(ValueError):
                core.validate_plan({"actions": [{"op": "radial_pattern", "comp": 10, key: []}]}, state)

    def test_stagger_order_times_selection_and_existing_animation_are_protected(self):
        state = snapshot()
        a = action_for("순차 등장 간격 0.1 순서 아래에서", state)
        self.assertEqual(a["layers"], [22, 21, 20])
        self.assertEqual(action_for("선택 레이어들 0.05초 간격으로 등장시켜줘")["delay"], 0.05)
        for change in ("position", "opacity", "expression", "locked", "3d", "separated", "one", "late"):
            s = snapshot()
            if change in ("position", "opacity"):
                s["layers"][0]["animated"] = [change]
            elif change == "expression":
                s["layers"][0]["expressions"] = ["opacity"]
            elif change == "locked":
                s["layers"][0]["locked"] = True
            elif change == "3d":
                s["layers"][0]["three_d"] = True
            elif change == "separated":
                s["layers"][0]["separated_position"] = True
            elif change == "one":
                s["layers"] = s["layers"][:1]
            else:
                s["active_comp"]["time"] = 7.5
            with self.subTest(change=change), self.assertRaises(ValueError):
                action_for("순차 등장", s)
        a = {"op": "stagger_layers", "comp": 10, "layers": [20, 21]}
        b = {"op": "set_transform", "comp": 10, "layer": 20, "values": {"opacity": 50}}
        with self.assertRaises(ValueError):
            core.validate_plan({"actions": [a, b]}, snapshot())

    def test_wave_changes_over_time_and_contours_loop(self):
        wave = action_for("흔들리는 격자 시드 7")
        measured = graphics.expected_items(wave)
        self.assertNotEqual(measured[0]["position"], measured[0]["probe_position"])
        contour = action_for("윤곽선 패턴 속도 0.125")
        item = contour["items"][0]
        self.assertTrue(core.equal_value(graphics.path_point(item, contour, 0), graphics.path_point(item, contour, 8)))
        self.assertFalse(core.equal_value(graphics.path_point(item, contour, 0), graphics.path_point(item, contour, 1)))

    def test_receipt_checks_native_geometry_colors_expression_evaluation_and_ids(self):
        for phrase in graphics.EXAMPLES[:5]:
            a = action_for(phrase)
            actual = {"op": a["op"], "comp_id": 10, "added_layers": a["added_layers"],
                      "created_layer_ids": list(range(100, 100+a["added_layers"])),
                      "element_count": len(a["items"]), "items": graphics.expected_items(a),
                      "layer_position": [640, 360], "layer_rotation_probe": 0}
            result = {"schema": core.VERSION, "job_id": "j", "status": "ok", "snapshot": snapshot(), "actions": [actual]}
            job = {"job_id": "j", "actions": [a]}
            self.assertTrue(core.verify_receipt(result, job))
            for field in ("geometry", "color", "id", "count", "target"):
                bad = copy.deepcopy(result)
                row = bad["actions"][0]
                if field == "geometry":
                    key = "first_vertex" if a["op"] == "contour_pattern" else "position"
                    row["items"][0][key] = [99999, 99999]
                elif field == "color":
                    row["items"][0]["color"] = [-1, -1, -1]
                elif field == "id":
                    row["created_layer_ids"][0] = 0
                elif field == "count":
                    row["element_count"] += 1
                else:
                    row["comp_id"] = 999
                with self.subTest(phrase=phrase, field=field), self.assertRaises(ValueError):
                    core.verify_receipt(bad, job)
            summary = core.summarize(result)
            self.assertNotIn("items", summary["action_results"][0])
            self.assertLess(len(json.dumps(summary)), 1800)

    def test_shape_rgba_readback_requires_opaque_alpha(self):
        a = action_for("초록색 원 그려줘")
        measured = copy.deepcopy(graphics.expected_items(a))
        measured[0]["color"] += [1]
        actual = dict(added_layers=1, created_layer_ids=[100], items=measured, element_count=1,
                      layer_position=[640, 360], layer_rotation_probe=0)
        self.assertTrue(graphics.verify(a, actual, core.equal_value))
        actual["items"][0]["color"][3] = 0.5
        with self.assertRaises(ValueError):
            graphics.verify(a, actual, core.equal_value)

    def test_trail_verification_checks_link_and_actual_delayed_samples(self):
        a = action_for("선택 레이어 잔상 개수 2")
        rows = [dict(source_id=20, delay=(i+1)*a["delay"], decay=a["decay"]**(i+1),
                     expressions_ok=True, sample_matches=True) for i in range(2)]
        actual = dict(added_layers=2, created_layer_ids=[100, 101], trails=rows)
        self.assertTrue(graphics.verify(a, actual, core.equal_value))
        for key, value in (("source_id", 99), ("sample_matches", False), ("expressions_ok", False), ("delay", 1)):
            bad = copy.deepcopy(actual);bad["trails"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                graphics.verify(a, bad, core.equal_value)

    def test_stagger_verifies_both_property_timelines_and_final_appearance(self):
        a = action_for("순차 등장")
        rows = [dict(layer_id=target, times=[i*a["delay"], i*a["delay"]+a["duration"]],
                     opacity_times=[i*a["delay"], i*a["delay"]+a["duration"]], offset=a["offset"],
                     initial_opacity=0, original_position=[100, 200], final_position=[100, 200],
                     original_opacity=75, final_opacity=75, easing_ok=True) for i, target in enumerate(a["layers"])]
        actual = dict(added_layers=0, created_layer_ids=[], stagger=rows)
        self.assertTrue(graphics.verify(a, actual, core.equal_value))
        for key, value in (("opacity_times", [2,3]), ("final_position", [0,0]), ("final_opacity", 100), ("easing_ok", False)):
            bad = copy.deepcopy(actual);bad["stagger"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                graphics.verify(a, bad, core.equal_value)

    def test_background_readback_accepts_native_eight_bit_quantization(self):
        action = {"op": "set_comp", "comp": 10, "changes": {"background_color": [0.025, 0.035, 0.06]}}
        actual = {"op": "set_comp", "comp_id": 10, "background_color": [6/255, 9/255, 15/255]}
        result = dict(schema=core.VERSION, job_id="j", status="ok", snapshot=snapshot(), actions=[actual])
        self.assertTrue(core.verify_receipt(result, {"job_id": "j", "actions": [action]}))


if __name__ == "__main__":
    unittest.main()
