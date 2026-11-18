"""Bounded, seeded graphic recipes. Only data is accepted; never user code."""
import math
import random
import re
import shlex

CATALOG = {
    "radial_pattern": "comp; count,radius,size,length,shape,rotation,spin,color,seed. New editable shape layer.",
    "wave_grid": "comp; rows,columns,spacing,size,amplitude,speed,color,seed. Animated dot grid.",
    "contour_pattern": "comp; count,radius,spacing,distortion,stroke,speed,color,seed. Animated contour paths.",
    "scatter_pattern": "comp; count,min_size,max_size,distribution,palette,shape,seed. Seeded shape field.",
    "text_pattern": "comp; text,rows,columns,gap_x,gap_y,font_size,rotation,color,seed. Editable text tiles.",
    "motion_trail": "comp,layer; count,delay,decay. Duplicates follow the source's delayed 2D transforms.",
    "stagger_layers": "comp,layers; delay,duration,offset,order,seed. New position/opacity entrance keys.",
}
EXAMPLES = [
    "방사형 패턴 만들어줘 개수 36 반지름 260 색 초록색",
    "흔들리는 격자 만들어줘 행 8 열 14 간격 60 흔들림 35 속도 0.3",
    "윤곽선 패턴 만들어줘 선 32개 반지름 320 왜곡 55 두께 2",
    "도형 흩뿌리기 개수 80 최소크기 8 최대크기 60 팔레트 네온 시드 42",
    '텍스트 반복 "WAVE" 행 5 열 6 글자크기 48',
    "선택 레이어 잔상 만들어줘 개수 8 간격 0.08 감쇠 0.8",
    "선택 레이어들 0.05초 간격으로 등장시켜줘",
    "초록색 원 그려줘",
]
PALETTES = {
    "neon": [[0.25, 1, 0.65], [0.65, 0.35, 1], [1, 0.3, 0.55], [0.2, 0.75, 1]],
    "pastel": [[1, 0.65, 0.72], [0.7, 0.65, 1], [0.55, 0.9, 0.85], [1, 0.85, 0.55]],
    "mono": [[0.95, 0.95, 0.95], [0.6, 0.65, 0.7], [0.3, 0.35, 0.4]],
}
MINT = [0.25, 1, 0.65]
PREFIXES = [
    ("radial_pattern", ("방사형 패턴", "방사형 배열")),
    ("wave_grid", ("흔들리는 격자", "물결 격자")),
    ("contour_pattern", ("윤곽선 패턴", "윤곽선 겹치기", "등고선 패턴")),
    ("scatter_pattern", ("도형 흩뿌리기", "흩뿌리기", "입자 구름")),
    ("text_pattern", ("텍스트 반복", "텍스트 격자", "텍스트 패턴")),
    ("motion_trail", ("선택 레이어 잔상", "잔상 쌓기", "잔상 만들기", "잔상")),
    ("stagger_layers", ("선택 레이어들 순차 등장", "순차 등장")),
]
OPTIONS = {
    "개수": "count", "선": "count", "반지름": "radius", "도형": "shape",
    "크기": "size", "지름": "size", "길이": "length", "회전": "rotation", "각도": "rotation",
    "회전속도": "spin", "행": "rows", "열": "columns", "간격": "spacing",
    "흔들림": "amplitude", "강도": "amplitude", "진폭": "amplitude", "속도": "speed",
    "왜곡": "distortion", "두께": "stroke", "최소크기": "min_size", "최대크기": "max_size",
    "분포": "distribution", "팔레트": "palette", "문구": "text", "가로간격": "gap_x",
    "세로간격": "gap_y", "글자크기": "font_size", "감쇠": "decay", "시간차": "delay",
    "지연": "delay", "시간": "duration", "이동량": "offset", "순서": "order",
    "시드": "seed", "색": "color", "색상": "color",
}
ENUMS = {
    "shape": {"원": "circle", "사각형": "rectangle", "막대": "bar"},
    "palette": {"네온": "neon", "파스텔": "pastel", "모노": "mono"},
    "distribution": {"균등": "uniform", "중앙": "center"},
    "order": {"위에서": "top", "아래에서": "bottom", "랜덤": "random"},
}


def parse(request, color_names, colors):
    """Consume an entire supported phrase, rejecting unknown/duplicate options."""
    color_pattern = "|".join(re.escape(x) for x in color_names)
    circle = re.fullmatch(rf"(?:지름\s*(\d+(?:\.\d+)?)\s*)?({color_pattern})\s*원\s*그려줘", request)
    if circle:
        return {"kind": "mutate", "actions": [{"op": "radial_pattern", "comp": "$active",
                "count": 1, "radius": 0, "size": float(circle[1] or 300), "shape": "circle",
                "color": colors[color_names[circle[2]]]}]}
    stagger = re.fullmatch(r"선택 레이어들\s+(\d+(?:\.\d+)?)초\s+간격으로\s+등장시켜줘", request)
    if stagger:
        return {"kind": "mutate", "actions": [{"op": "stagger_layers", "comp": "$active",
                "layers": "$selected_many", "delay": float(stagger[1])}]}
    operation, rest = None, None
    for op, prefixes in PREFIXES:
        for prefix in prefixes:
            if request == prefix or request.startswith(prefix + " "):
                operation, rest = op, request[len(prefix):].strip()
                break
        if operation:
            break
    if operation is None:
        return None
    tokens = shlex.split(rest)
    action = {"op": operation, "comp": "$active"}
    if operation == "motion_trail":
        action["layer"] = "$selected"
    if operation == "stagger_layers":
        action["layers"] = "$selected_many"
    verbs = {"만들어줘", "추가해줘", "그려줘", "등장시켜줘"}
    if operation == "text_pattern" and tokens and tokens[0] not in OPTIONS and tokens[0] not in verbs:
        action["text"] = tokens.pop(0)
    seen_verb = False
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in verbs and not seen_verb:
            seen_verb = True
            i += 1
            continue
        if token not in OPTIONS or i + 1 >= len(tokens):
            raise ValueError("지원하지 않는 그래픽 옵션입니다: " + token + "; laya-ae --list 또는 docs/graphics.md 확인")
        key, value = OPTIONS[token], tokens[i + 1]
        if key == "spacing" and operation in {"motion_trail", "stagger_layers"}:
            key = "delay"
        if key in action:
            raise ValueError("같은 옵션을 두 번 지정할 수 없습니다: " + token)
        if key in ENUMS:
            action[key] = ENUMS[key].get(value, value)
        elif key == "color":
            if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                action[key] = [int(value[j:j+2], 16)/255 for j in (1, 3, 5)]
            elif value in color_names:
                action[key] = colors[color_names[value]]
            else:
                raise ValueError("지원하는 색 이름 또는 #RRGGBB를 사용하세요")
        elif key == "text":
            action[key] = value
        else:
            numeric = re.fullmatch(r"(-?\d+(?:\.\d+)?)(?:개|초|px|도)?", value)
            if not numeric:
                raise ValueError(token + ": 숫자가 필요합니다")
            action[key] = float(numeric[1]) if "." in numeric[1] else int(numeric[1])
        i += 2
    return {"kind": "mutate", "actions": [action]}


def validate(action, info, layer_info, layer_count):
    # Lazy import avoids a circular dependency while keeping one validation policy.
    import ae_basic as core
    op = action["op"]
    defaults = {
        "radial_pattern": dict(count=36, radius=260, size=14, length=90, shape="bar", rotation=0, spin=0, color=MINT, seed=1),
        "wave_grid": dict(rows=8, columns=14, spacing=60, size=12, amplitude=35, speed=0.3, color=[0.25, 0.75, 1], seed=1),
        "contour_pattern": dict(count=32, radius=320, spacing=None, distortion=55, stroke=2, speed=0.125, color=MINT, seed=1),
        "scatter_pattern": dict(count=80, min_size=8, max_size=60, distribution="uniform", palette="neon", shape="circle", seed=42),
        "text_pattern": dict(text="WAVE", rows=5, columns=6, gap_x=230, gap_y=130, font_size=48, rotation=0, color=[0.95, 0.95, 0.95], seed=1),
        "motion_trail": dict(count=8, delay=0.08, decay=0.8),
        "stagger_layers": dict(delay=0.05, duration=0.6, offset=60, order="top", seed=1),
    }[op]
    required = {"op", "comp"} | ({"layer"} if op == "motion_trail" else {"layers"} if op == "stagger_layers" else set())
    core.exact(action, required, defaults)
    a = {**defaults, **action}
    width, height = info["width"], info["height"]
    if "seed" in a:
        core.number(a["seed"], "seed", 0, 2**31-1, integer=True)
    rng = random.Random(a.get("seed", 1))

    def num(key, low, high, integer=False):
        core.number(a[key], key, low, high, integer=integer)

    def color():
        if not isinstance(a["color"], list) or len(a["color"]) != 3:
            raise ValueError("color requires three RGB channels")
        for channel in a["color"]:
            core.number(channel, "color", 0, 1)

    def choice(key, choices):
        if not isinstance(a[key], str) or a[key] not in choices:
            raise ValueError(key + ": choose " + ", ".join(choices))

    items, added = [], 1
    if op == "radial_pattern":
        num("count", 1, 180, True); num("radius", 0, 4000); num("size", 1, 2000)
        num("length", 1, 3000); num("rotation", -36000, 36000); num("spin", -360, 360)
        choice("shape", ("circle", "rectangle", "bar")); color()
        for i in range(a["count"]):
            angle = a["rotation"] + i*360/a["count"]
            theta = math.radians(angle)
            items.append(dict(kind="ellipse" if a["shape"] == "circle" else "rectangle",
                              position=[a["radius"]*math.sin(theta), -a["radius"]*math.cos(theta)],
                              size=[a["size"], a["length"] if a["shape"] == "bar" else a["size"]],
                              rotation=angle, color=a["color"], opacity=100))
    elif op == "wave_grid":
        num("rows", 1, 30, True); num("columns", 1, 30, True)
        if a["rows"]*a["columns"] > 400:
            raise ValueError("물결 격자는 최대 400점입니다")
        num("spacing", 1, 1000); num("size", 1, 500); num("amplitude", 0, 1000); num("speed", 0, 5); color()
        phase = rng.random()*math.tau
        for row in range(a["rows"]):
            for column in range(a["columns"]):
                items.append(dict(kind="ellipse", position=[(column-(a["columns"]-1)/2)*a["spacing"], (row-(a["rows"]-1)/2)*a["spacing"]],
                                  size=[a["size"]]*2, rotation=0, color=a["color"], opacity=100,
                                  phase=phase+column*0.55+row*0.35))
    elif op == "contour_pattern":
        num("count", 1, 100, True); num("radius", 20, 4000)
        num("distortion", 0, 1000); num("stroke", 0.2, 100); num("speed", 0, 2); color()
        if a["spacing"] is None:
            a["spacing"] = a["radius"]*0.65/max(1, a["count"]-1)
        num("spacing", 0.2, 1000)
        inner = a["radius"]-(a["count"]-1)*a["spacing"]
        if inner < 10 or a["distortion"] > inner*0.8:
            raise ValueError("윤곽선 안쪽 반지름이 너무 작습니다. 반지름을 키우거나 간격·왜곡을 줄이세요")
        phase = rng.random()*math.tau
        for i in range(a["count"]):
            items.append(dict(kind="path", radius=inner+i*a["spacing"], phase=phase+i*0.035,
                              color=a["color"], stroke=a["stroke"], opacity=100))
    elif op == "scatter_pattern":
        num("count", 1, 400, True); num("min_size", 1, 1000); num("max_size", a["min_size"], 2000)
        choice("distribution", ("uniform", "center")); choice("palette", tuple(PALETTES)); choice("shape", ("circle", "rectangle"))
        for _ in range(a["count"]):
            size = rng.uniform(a["min_size"], a["max_size"])
            if a["distribution"] == "center":
                theta, radius = rng.random()*math.tau, rng.random()**1.7
                x, y = math.cos(theta)*radius, math.sin(theta)*radius
            else:
                x, y = rng.uniform(-1, 1), rng.uniform(-1, 1)
            items.append(dict(kind="ellipse" if a["shape"] == "circle" else "rectangle",
                              position=[x*max(0, width-size)/2, y*max(0, height-size)/2], size=[size]*2,
                              rotation=rng.uniform(-180, 180), color=rng.choice(PALETTES[a["palette"]]), opacity=rng.uniform(40, 100)))
    elif op == "text_pattern":
        core.text(a["text"], "text", 120); num("rows", 1, 20, True); num("columns", 1, 20, True)
        added = a["rows"]*a["columns"]
        if added > 100:
            raise ValueError("텍스트 격자는 최대 100개입니다")
        num("gap_x", 1, 2000); num("gap_y", 1, 2000); num("font_size", 1, 500); num("rotation", -36000, 36000); color()
        for row in range(a["rows"]):
            for column in range(a["columns"]):
                items.append(dict(position=[width/2+(column-(a["columns"]-1)/2)*a["gap_x"], height/2+(row-(a["rows"]-1)/2)*a["gap_y"]],
                                  rotation=a["rotation"], text=a["text"], font_size=a["font_size"], color=a["color"]))
    elif op == "motion_trail":
        num("count", 1, 32, True); num("delay", 0.001, 5); num("decay", 0.05, 1)
        target = layer_info(a["layer"], a["comp"])
        if target.get("three_d") or target.get("layer_type") in {"camera", "light"} or target.get("separated_position"):
            raise ValueError("잔상은 위치가 분리되지 않은 2D AV 레이어를 선택하세요")
        if a["count"]*a["delay"] >= info["duration"]:
            raise ValueError("전체 잔상 지연은 컴포지션 길이보다 짧아야 합니다")
        added = a["count"]
    else:
        num("delay", 0, 5); num("duration", 0.01, 30); num("offset", -4000, 4000)
        choice("order", ("top", "bottom", "random"))
        if not isinstance(a["layers"], list) or not 2 <= len(a["layers"]) <= 100 or len(set(a["layers"])) != len(a["layers"]):
            raise ValueError("순차 등장은 서로 다른 레이어 2~100개를 선택하세요")
        for target in a["layers"]:
            core.number(target, "selected layer ID", 1, integer=True)
        targets = [layer_info(target, a["comp"]) for target in a["layers"]]
        targets.sort(key=lambda row: row.get("index", row["id"]))
        if a["order"] == "bottom":
            targets.reverse()
        elif a["order"] == "random":
            rng.shuffle(targets)
        a["layers"] = [row["id"] for row in targets]
        a["start"] = info.get("time", 0)
        for i, target in enumerate(targets):
            if target.get("three_d") or target.get("layer_type") in {"camera", "light"} or target.get("separated_position"):
                raise ValueError("순차 등장은 위치가 분리되지 않은 2D 레이어만 지원합니다")
            if {"position", "opacity"} & (set(target.get("animated", [])) | set(target.get("expressions", []))):
                raise ValueError("기존 위치·불투명도 애니메이션을 보존합니다. 새 레이어를 선택하세요")
            start, end = a["start"]+i*a["delay"], a["start"]+i*a["delay"]+a["duration"]
            if start < target.get("in_point", 0) or end > min(info["duration"], target.get("out_point", info["duration"])):
                raise ValueError("순차 등장 키프레임이 레이어/컴포지션 범위를 벗어납니다. 재생 헤드·간격·시간을 조정하세요")
        added = 0
    if layer_count + added > 200:
        raise ValueError("실행 후 레이어가 200개를 넘습니다. 새 컴포지션에서 실행하세요")
    a.update(width=width, height=height, comp_duration=info["duration"], added_layers=added)
    if items:
        a["items"] = items
    return a


def path_point(item, action, time, index=0):
    angle = index*math.tau/96
    phase = item["phase"]
    t = math.tau*action["speed"]*time
    radius = item["radius"] + action["distortion"]*(0.62*math.sin(3*angle+phase+t)+0.38*math.sin(5*angle-phase-t))
    return [radius*math.cos(angle), radius*math.sin(angle)]


def expected_items(action):
    """Small native measurements per element, independent of creation metadata."""
    result = []
    probe = min(1.0, action["comp_duration"]/3)
    for item in action.get("items", []):
        if item.get("kind") == "path":
            result.append(dict(kind="path", vertices=96, first_vertex=path_point(item, action, 0),
                               probe_vertex=path_point(item, action, probe), color=item["color"], stroke=item["stroke"], expression_error=""))
        elif action["op"] == "text_pattern":
            result.append(dict(position=item["position"], rotation=item["rotation"], text=item["text"],
                               font_size=item["font_size"], color=item["color"]))
        else:
            base = item["position"]
            position, future = list(base), list(base)
            if action["op"] == "wave_grid":
                position[1] += action["amplitude"]*math.sin(item["phase"])
                future[1] += action["amplitude"]*math.sin(math.tau*action["speed"]*probe+item["phase"])
            result.append(dict(kind=item["kind"], size=item["size"], position=position, probe_position=future,
                               rotation=item["rotation"], color=item["color"], opacity=item["opacity"], expression_error=""))
    return result


def verify(action, actual, equal):
    import ae_basic as core
    if actual.get("added_layers") != action["added_layers"]:
        raise ValueError("Native graphic layer count differs from plan")
    ids = actual.get("created_layer_ids", [])
    if len(ids) != action["added_layers"] or len(set(ids)) != len(ids):
        raise ValueError("Native graphic IDs are missing or repeated")
    for layer_id in ids:
        core.number(layer_id, "created layer ID", 1, integer=True)
    op = action["op"]
    if "items" in action:
        # AE shape color properties may return RGBA, while TextDocument returns RGB.
        actual = dict(actual)
        actual["items"] = [dict(row) for row in actual.get("items", [])]
        for row in actual["items"]:
            channels = row.get("color", [])
            if len(channels) == 4:
                if not equal(channels[3], 1):
                    raise ValueError("Unexpected native shape color alpha")
                row["color"] = channels[:3]
        wanted = dict(items=expected_items(action), element_count=len(action["items"]))
        if op != "text_pattern":
            wanted["layer_position"] = [action["width"]/2, action["height"]/2]
            wanted["layer_rotation_probe"] = action.get("spin", 0)*min(1.0, action["comp_duration"]/3)
        if not equal(wanted, actual):
            raise ValueError("Native geometry/text/expression readback differs from " + op)
    elif op == "motion_trail":
        trails = actual.get("trails", [])
        if len(trails) != action["count"]:
            raise ValueError("Native trail count mismatch")
        for i, row in enumerate(trails):
            wanted = dict(source_id=action["layer"], delay=(i+1)*action["delay"], decay=action["decay"]**(i+1),
                          expressions_ok=True, sample_matches=True)
            if not equal(wanted, row):
                raise ValueError("Native trail source/delay/expression mismatch")
    else:
        rows = actual.get("stagger", [])
        if len(rows) != len(action["layers"]):
            raise ValueError("Native stagger layer count mismatch")
        for i, row in enumerate(rows):
            start = action["start"]+i*action["delay"]
            if not equal(dict(layer_id=action["layers"][i], times=[start, start+action["duration"]], opacity_times=[start, start+action["duration"]],
                              offset=action["offset"], initial_opacity=0, easing_ok=True), row):
                raise ValueError("Native stagger timing/easing mismatch")
            if not isinstance(row.get("original_position"), list) or len(row["original_position"]) != 2:
                raise ValueError("Native stagger original position is missing")
            core.number(row.get("original_opacity"), "original opacity", 0, 100)
            if not equal(row.get("final_position"), row.get("original_position")) or not equal(row.get("final_opacity"), row.get("original_opacity")):
                raise ValueError("Native stagger changed the final appearance")
    return True
