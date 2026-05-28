#!/usr/bin/env python3
"""
Generate NER entity annotations, entity index, and person social network
for 天龍八部-demo. Uses rule-based string matching on a curated character list.
"""
import json, re, os, copy

BASE = os.path.dirname(__file__)
DATA = os.path.join(BASE, 'data')

ENTITIES = [
    # ── 主角 ──
    {"key": "person_段譽",    "label": "段譽",    "type": "PERSON", "subtype": "main",      "faction": "dali",    "aliases": ["段譽"]},
    {"key": "person_喬峯",    "label": "喬峯",    "type": "PERSON", "subtype": "main",      "faction": "beggars", "aliases": ["喬峯", "蕭峯"]},
    {"key": "person_虛竹",    "label": "虛竹",    "type": "PERSON", "subtype": "main",      "faction": "xiaoyao", "aliases": ["虛竹"]},
    # ── 大理段氏 ──
    {"key": "person_段正淳",  "label": "段正淳",  "type": "PERSON", "subtype": "main",      "faction": "dali",    "aliases": ["段正淳", "鎮南王"]},
    {"key": "person_保定帝",  "label": "保定帝",  "type": "PERSON", "subtype": "secondary", "faction": "dali",    "aliases": ["保定帝", "段正明"]},
    {"key": "person_枯榮",    "label": "枯榮大師","type": "PERSON", "subtype": "secondary", "faction": "dali",    "aliases": ["枯榮大師", "枯榮"]},
    {"key": "person_段延慶",  "label": "段延慶",  "type": "PERSON", "subtype": "main",      "faction": "dali",    "aliases": ["段延慶", "惡貫滿盈"]},
    {"key": "person_朱丹臣",  "label": "朱丹臣",  "type": "PERSON", "subtype": "secondary", "faction": "dali",    "aliases": ["朱丹臣"]},
    {"key": "person_傅思歸",  "label": "傅思歸",  "type": "PERSON", "subtype": "secondary", "faction": "dali",    "aliases": ["傅思歸"]},
    # ── 丐幫 ──
    {"key": "person_馬大元",  "label": "馬大元",  "type": "PERSON", "subtype": "secondary", "faction": "beggars", "aliases": ["馬大元"]},
    {"key": "person_康敏",    "label": "康敏",    "type": "PERSON", "subtype": "main",      "faction": "beggars", "aliases": ["康敏", "馬夫人"]},
    {"key": "person_全冠清",  "label": "全冠清",  "type": "PERSON", "subtype": "secondary", "faction": "beggars", "aliases": ["全冠清"]},
    {"key": "person_奚長老",  "label": "奚長老",  "type": "PERSON", "subtype": "secondary", "faction": "beggars", "aliases": ["奚長老"]},
    # ── 姑蘇慕容 ──
    {"key": "person_慕容復",  "label": "慕容復",  "type": "PERSON", "subtype": "main",      "faction": "murong",  "aliases": ["慕容復"]},
    {"key": "person_王語嫣",  "label": "王語嫣",  "type": "PERSON", "subtype": "main",      "faction": "murong",  "aliases": ["王語嫣", "語嫣"]},
    {"key": "person_王夫人",  "label": "王夫人",  "type": "PERSON", "subtype": "main",      "faction": "murong",  "aliases": ["王夫人", "甘寶寶"]},
    {"key": "person_包不同",  "label": "包不同",  "type": "PERSON", "subtype": "secondary", "faction": "murong",  "aliases": ["包不同"]},
    {"key": "person_風波惡",  "label": "風波惡",  "type": "PERSON", "subtype": "secondary", "faction": "murong",  "aliases": ["風波惡"]},
    {"key": "person_公冶乾",  "label": "公冶乾",  "type": "PERSON", "subtype": "secondary", "faction": "murong",  "aliases": ["公冶乾"]},
    {"key": "person_慕容博",  "label": "慕容博",  "type": "PERSON", "subtype": "main",      "faction": "murong",  "aliases": ["慕容博"]},
    # ── 逍遙派 ──
    {"key": "person_無崖子",  "label": "無崖子",  "type": "PERSON", "subtype": "main",      "faction": "xiaoyao", "aliases": ["無崖子"]},
    {"key": "person_天山童姥","label": "天山童姥","type": "PERSON", "subtype": "main",      "faction": "xiaoyao", "aliases": ["天山童姥", "童姥"]},
    {"key": "person_李秋水",  "label": "李秋水",  "type": "PERSON", "subtype": "main",      "faction": "xiaoyao", "aliases": ["李秋水"]},
    # ── 星宿派 ──
    {"key": "person_丁春秋",  "label": "丁春秋",  "type": "PERSON", "subtype": "main",      "faction": "xingxiu", "aliases": ["丁春秋", "星宿老怪"]},
    # ── 少林寺 ──
    {"key": "person_玄慈",    "label": "玄慈",    "type": "PERSON", "subtype": "main",      "faction": "shaolin", "aliases": ["玄慈方丈", "玄慈"]},
    {"key": "person_掃地僧",  "label": "掃地僧",  "type": "PERSON", "subtype": "main",      "faction": "shaolin", "aliases": ["掃地僧"]},
    {"key": "person_玄難",    "label": "玄難",    "type": "PERSON", "subtype": "secondary", "faction": "shaolin", "aliases": ["玄難"]},
    {"key": "person_玄寂",    "label": "玄寂",    "type": "PERSON", "subtype": "secondary", "faction": "shaolin", "aliases": ["玄寂"]},
    # ── 吐蕃 ──
    {"key": "person_鳩摩智",  "label": "鳩摩智",  "type": "PERSON", "subtype": "main",      "faction": "tibet",   "aliases": ["鳩摩智"]},
    # ── 遼國 ──
    {"key": "person_耶律洪基","label": "耶律洪基","type": "PERSON", "subtype": "main",      "faction": "liao",    "aliases": ["耶律洪基"]},
    {"key": "person_蕭峯父",  "label": "蕭遠山",  "type": "PERSON", "subtype": "main",      "faction": "liao",    "aliases": ["蕭遠山"]},
    # ── 段正淳的女眷 ──
    {"key": "person_阿朱",    "label": "阿朱",    "type": "PERSON", "subtype": "main",      "faction": "murong",  "aliases": ["阿朱"]},
    {"key": "person_阿碧",    "label": "阿碧",    "type": "PERSON", "subtype": "secondary", "faction": "murong",  "aliases": ["阿碧"]},
    {"key": "person_阿紫",    "label": "阿紫",    "type": "PERSON", "subtype": "main",      "faction": "liao",    "aliases": ["阿紫"]},
    {"key": "person_木婉清",  "label": "木婉清",  "type": "PERSON", "subtype": "main",      "faction": "dali",    "aliases": ["木婉清"]},
    {"key": "person_鐘靈",    "label": "鐘靈",    "type": "PERSON", "subtype": "secondary", "faction": "dali",    "aliases": ["鐘靈"]},
    {"key": "person_秦紅棉",  "label": "秦紅棉",  "type": "PERSON", "subtype": "secondary", "faction": "other",   "aliases": ["秦紅棉"]},
    {"key": "person_阮星竹",  "label": "阮星竹",  "type": "PERSON", "subtype": "secondary", "faction": "other",   "aliases": ["阮星竹"]},
    {"key": "person_刀白鳳",  "label": "刀白鳳",  "type": "PERSON", "subtype": "secondary", "faction": "dali",    "aliases": ["刀白鳳"]},
    # ── 其他 ──
    {"key": "person_游坦之",  "label": "游坦之",  "type": "PERSON", "subtype": "secondary", "faction": "other",   "aliases": ["游坦之"]},
    {"key": "person_本因",    "label": "本因",    "type": "PERSON", "subtype": "secondary", "faction": "dali",    "aliases": ["本因"]},
    {"key": "person_南海鱷神","label": "南海鱷神","type": "PERSON", "subtype": "secondary", "faction": "dali",    "aliases": ["南海鱷神", "嶽老三"]},
    # ── 地點 ──
    {"key": "place_大理",     "label": "大理",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["大理"]},
    {"key": "place_燕京",     "label": "燕京",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["燕京"]},
    {"key": "place_姑蘇",     "label": "姑蘇",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["姑蘇"]},
    {"key": "place_無量山",   "label": "無量山",  "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["無量山"]},
    {"key": "place_少林寺",   "label": "少林寺",  "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["少林寺"]},
    {"key": "place_天山",     "label": "天山",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["天山"]},
    {"key": "place_西夏",     "label": "西夏",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["西夏"]},
    {"key": "place_雁門關",   "label": "雁門關",  "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["雁門關"]},
    {"key": "place_杏子林",   "label": "杏子林",  "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["杏子林"]},
    # ── 空間建築 ──
    {"key": "building_曼陀山莊",  "label": "曼陀山莊",  "type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["曼陀山莊"]},
    {"key": "building_參合莊",    "label": "參合莊",    "type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["參合莊"]},
    {"key": "building_藏經閣",    "label": "藏經閣",    "type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["藏經閣"]},
    {"key": "building_琅嬛福地",  "label": "琅嬛福地",  "type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["琅嬛福地"]},
    {"key": "building_無量玉洞",  "label": "無量玉洞",  "type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["無量玉洞"]},
    # ── 武功 ──
    {"key": "martial_六脈神劍",   "label": "六脈神劍",  "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["六脈神劍"]},
    {"key": "martial_北冥神功",   "label": "北冥神功",  "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["北冥神功"]},
    {"key": "martial_凌波微步",   "label": "凌波微步",  "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["凌波微步"]},
    {"key": "martial_降龍十八掌", "label": "降龍十八掌","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["降龍十八掌"]},
    {"key": "martial_化功大法",   "label": "化功大法",  "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["化功大法"]},
    {"key": "martial_小無相功",   "label": "小無相功",  "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["小無相功"]},
    {"key": "martial_斗轉星移",   "label": "斗轉星移",  "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["斗轉星移"]},
    {"key": "martial_易筋經",     "label": "易筋經",    "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["易筋經"]},
    {"key": "martial_一陽指",     "label": "一陽指",    "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["一陽指"]},
    {"key": "martial_天山六陽掌", "label": "天山六陽掌","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["天山六陽掌"]},
    # ── 組織 ──
    {"key": "org_丐幫",        "label": "丐幫",      "type": "ORG", "subtype": "org", "faction": None, "aliases": ["丐幫"]},
    {"key": "org_星宿派",      "label": "星宿派",    "type": "ORG", "subtype": "org", "faction": None, "aliases": ["星宿派"]},
    {"key": "org_逍遙派",      "label": "逍遙派",    "type": "ORG", "subtype": "org", "faction": None, "aliases": ["逍遙派"]},
    {"key": "org_少林",        "label": "少林",      "type": "ORG", "subtype": "org", "faction": None, "aliases": ["少林派", "少林寺"]},
    {"key": "org_姑蘇慕容",    "label": "姑蘇慕容",  "type": "ORG", "subtype": "org", "faction": None, "aliases": ["姑蘇慕容"]},
    {"key": "org_大理段氏",    "label": "大理段氏",  "type": "ORG", "subtype": "org", "faction": None, "aliases": ["大理段氏"]},
    {"key": "org_遼國",        "label": "遼國",      "type": "ORG", "subtype": "org", "faction": None, "aliases": ["遼國"]},
    {"key": "org_西夏",        "label": "西夏",      "type": "ORG", "subtype": "org", "faction": None, "aliases": ["西夏國"]},
]

ALIAS_MAP: list[tuple[str, dict]] = []
for ent in ENTITIES:
    for alias in sorted(ent["aliases"], key=len, reverse=True):
        ALIAS_MAP.append((alias, ent))
ALIAS_MAP.sort(key=lambda x: len(x[0]), reverse=True)


def annotate_paragraph(text: str) -> list[dict]:
    occupied = [False] * len(text)
    found = []
    for alias, ent in ALIAS_MAP:
        start = 0
        while True:
            pos = text.find(alias, start)
            if pos == -1:
                break
            end = pos + len(alias)
            if not any(occupied[pos:end]):
                found.append({
                    "key": ent["key"],
                    "label": ent["label"],
                    "type": ent["type"],
                    "text": alias,
                    "start": pos,
                    "end": end,
                })
                for i in range(pos, end):
                    occupied[i] = True
            start = pos + 1
    found.sort(key=lambda e: e["start"])
    return found


def build_ner(ebook: dict) -> tuple[dict, dict, dict]:
    entity_index: dict[str, dict] = {}
    for ent in ENTITIES:
        entity_index[ent["key"]] = {
            "key": ent["key"],
            "label": ent["label"],
            "entity_type": ent["type"],
            "subtype": ent["subtype"],
            "faction": ent.get("faction"),
            "frequency": 0,
            "paragraph_count": 0,
            "surface_forms": list(ent["aliases"]),
            "paragraphs": [],
        }

    cooccurrence: dict[tuple[str, str], int] = {}

    ebook_annotated = copy.deepcopy(ebook)
    for ch in ebook_annotated["chapters"]:
        for para in ch["paragraphs"]:
            text = para["text"]
            entities = annotate_paragraph(text)
            para["entities"] = entities

            keys_in_para = set()
            for ent_span in entities:
                k = ent_span["key"]
                entity_index[k]["frequency"] += 1
                keys_in_para.add(k)

            for k in keys_in_para:
                entity_index[k]["paragraph_count"] += 1
                entity_index[k]["paragraphs"].append({
                    "paragraph_id": para["id"],
                    "chapter_number": ch["n"],
                    "paragraph_number": para["n"],
                    "text": text[:120],
                })

            person_keys = sorted(k for k in keys_in_para if k.startswith("person_"))
            for i, ka in enumerate(person_keys):
                for kb in person_keys[i + 1:]:
                    pair = (ka, kb) if ka < kb else (kb, ka)
                    cooccurrence[pair] = cooccurrence.get(pair, 0) + 1

    for k, ent in entity_index.items():
        ent["paragraphs"] = ent["paragraphs"][:100]

    person_entities = [e for e in ENTITIES if e["type"] == "PERSON"]
    nodes = []
    for ent in person_entities:
        ei = entity_index[ent["key"]]
        if ei["frequency"] == 0:
            continue
        ch_set = set(p["chapter_number"] for p in ei["paragraphs"])
        nodes.append({
            "id": ent["key"],
            "name": ent["label"],
            "subtype": ent["subtype"],
            "faction": ent.get("faction", "other"),
            "frequency": ei["frequency"],
            "chapter_count": len(ch_set),
            "paragraph_count": ei["paragraph_count"],
            "degree": 0,
            "weighted_degree": 0,
        })

    node_ids = {n["id"] for n in nodes}
    links = []
    for (ka, kb), weight in cooccurrence.items():
        if ka not in node_ids or kb not in node_ids:
            continue
        links.append({
            "id": f"co_{ka}_{kb}",
            "source": ka,
            "target": kb,
            "source_name": entity_index[ka]["label"],
            "target_name": entity_index[kb]["label"],
            "weight": weight,
            "shared_paragraph_count": weight,
        })

    degree_map: dict[str, int] = {}
    weighted_map: dict[str, int] = {}
    for link in links:
        degree_map[link["source"]] = degree_map.get(link["source"], 0) + 1
        degree_map[link["target"]] = degree_map.get(link["target"], 0) + 1
        weighted_map[link["source"]] = weighted_map.get(link["source"], 0) + link["weight"]
        weighted_map[link["target"]] = weighted_map.get(link["target"], 0) + link["weight"]
    for node in nodes:
        node["degree"] = degree_map.get(node["id"], 0)
        node["weighted_degree"] = weighted_map.get(node["id"], 0)

    links.sort(key=lambda l: l["weight"], reverse=True)
    social_network = {"nodes": nodes, "links": links}
    ei_output = {"entities": entity_index}
    return ebook_annotated, ei_output, social_network


def write_json_and_js(data: dict, key: str) -> None:
    json_path = os.path.join(DATA, key)
    js_path = json_path + '.js'
    json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(f"window.DEMO_JSON=window.DEMO_JSON||{{}};window.DEMO_JSON['data/{key}']={json_str};")
    size_kb = os.path.getsize(json_path) / 1024
    print(f"  {key}: {size_kb:.0f} KB")


def main():
    print("Loading ebook.json ...")
    with open(os.path.join(DATA, 'ebook.json'), encoding='utf-8') as f:
        ebook = json.load(f)

    print("Annotating entities ...")
    ebook_ann, entity_index, social_network = build_ner(ebook)

    total_entities = sum(len(p.get("entities", [])) for ch in ebook_ann["chapters"] for p in ch["paragraphs"])
    print(f"  Total entity spans annotated: {total_entities:,}")
    print(f"  Network: {len(social_network['nodes'])} nodes, {len(social_network['links'])} edges")

    print("Writing data files ...")
    write_json_and_js(ebook_ann, 'ebook.json')
    write_json_and_js(entity_index, 'basic_entity_index.json')
    write_json_and_js(social_network, 'person_social_network.json')
    print("Done.")


if __name__ == '__main__':
    main()
