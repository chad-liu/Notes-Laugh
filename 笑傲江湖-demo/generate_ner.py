#!/usr/bin/env python3
"""
Generate NER entity annotations, entity index, and person social network
for 笑傲江湖-demo. Uses rule-based string matching on a curated character list.
"""
import json, re, os, copy

BASE = os.path.dirname(__file__)
DATA = os.path.join(BASE, 'data')

# ── Curated entity dictionary ──────────────────────────────────────────────
# Each entry: key, label, type, subtype, aliases (longest first to avoid partial matches)
ENTITIES = [
    # ── 主角 ──
    {"key": "person_令狐冲",  "label": "令狐冲",  "type": "PERSON", "subtype": "main",    "faction": "huashan",  "aliases": ["令狐冲"]},
    {"key": "person_任盈盈",  "label": "任盈盈",  "type": "PERSON", "subtype": "main",    "faction": "shengjiao","aliases": ["任盈盈", "盈盈", "聖姑"]},
    # ── 華山派 ──
    {"key": "person_岳不群",  "label": "岳不群",  "type": "PERSON", "subtype": "main",    "faction": "huashan",  "aliases": ["岳不群"]},
    {"key": "person_寧中則",  "label": "寧中則",  "type": "PERSON", "subtype": "secondary","faction": "huashan", "aliases": ["寧中則", "寧師娘"]},
    {"key": "person_岳靈珊",  "label": "岳靈珊",  "type": "PERSON", "subtype": "main",    "faction": "huashan",  "aliases": ["岳靈珊", "靈珊"]},
    {"key": "person_勞德諾",  "label": "勞德諾",  "type": "PERSON", "subtype": "secondary","faction": "huashan", "aliases": ["勞德諾"]},
    {"key": "person_風清揚",  "label": "風清揚",  "type": "PERSON", "subtype": "secondary","faction": "huashan", "aliases": ["風清揚"]},
    # ── 嵩山派 ──
    {"key": "person_左冷禪",  "label": "左冷禪",  "type": "PERSON", "subtype": "main",    "faction": "songshan", "aliases": ["左冷禪"]},
    {"key": "person_費彬",    "label": "費彬",    "type": "PERSON", "subtype": "secondary","faction": "songshan", "aliases": ["費彬"]},
    {"key": "person_封不平",  "label": "封不平",  "type": "PERSON", "subtype": "secondary","faction": "songshan", "aliases": ["封不平"]},
    {"key": "person_成不憂",  "label": "成不憂",  "type": "PERSON", "subtype": "secondary","faction": "songshan", "aliases": ["成不憂"]},
    # ── 衡山派 ──
    {"key": "person_莫大",    "label": "莫大",    "type": "PERSON", "subtype": "secondary","faction": "hengshan_m","aliases": ["莫大先生", "莫大"]},
    {"key": "person_劉正風",  "label": "劉正風",  "type": "PERSON", "subtype": "secondary","faction": "hengshan_m","aliases": ["劉正風"]},
    {"key": "person_曲洋",    "label": "曲洋",    "type": "PERSON", "subtype": "secondary","faction": "hengshan_m","aliases": ["曲洋"]},
    # ── 恆山派 ──
    {"key": "person_定靜",    "label": "定靜",    "type": "PERSON", "subtype": "secondary","faction": "hengshan_f","aliases": ["定靜師太", "定靜"]},
    {"key": "person_定逸",    "label": "定逸",    "type": "PERSON", "subtype": "secondary","faction": "hengshan_f","aliases": ["定逸師太", "定逸"]},
    {"key": "person_儀琳",    "label": "儀琳",    "type": "PERSON", "subtype": "main",    "faction": "hengshan_f","aliases": ["儀琳"]},
    {"key": "person_儀和",    "label": "儀和",    "type": "PERSON", "subtype": "secondary","faction": "hengshan_f","aliases": ["儀和"]},
    # ── 日月神教 ──
    {"key": "person_任我行",  "label": "任我行",  "type": "PERSON", "subtype": "main",    "faction": "shengjiao","aliases": ["任我行"]},
    {"key": "person_向問天",  "label": "向問天",  "type": "PERSON", "subtype": "main",    "faction": "shengjiao","aliases": ["向問天"]},
    {"key": "person_東方不敗","label": "東方不敗","type": "PERSON", "subtype": "main",    "faction": "shengjiao","aliases": ["東方不敗"]},
    {"key": "person_楊蓮亭",  "label": "楊蓮亭",  "type": "PERSON", "subtype": "secondary","faction": "shengjiao","aliases": ["楊蓮亭"]},
    # ── 泰山派/少林/武當 ──
    {"key": "person_天門道人","label": "天門道人","type": "PERSON", "subtype": "secondary","faction": "taishan",  "aliases": ["天門道人", "天門"]},
    {"key": "person_方證",    "label": "方證",    "type": "PERSON", "subtype": "secondary","faction": "shaolin",  "aliases": ["方證大師", "方證"]},
    # ── 福建 / 林家 ──
    {"key": "person_林震南",  "label": "林震南",  "type": "PERSON", "subtype": "secondary","faction": "fujian",   "aliases": ["林震南"]},
    {"key": "person_林平之",  "label": "林平之",  "type": "PERSON", "subtype": "main",    "faction": "fujian",   "aliases": ["林平之"]},
    {"key": "person_余滄海",  "label": "余滄海",  "type": "PERSON", "subtype": "main",    "faction": "fujian",   "aliases": ["余滄海"]},
    # ── 桃谷六仙 ──
    {"key": "person_桃根仙",  "label": "桃根仙",  "type": "PERSON", "subtype": "secondary","faction": "taogu",    "aliases": ["桃根仙"]},
    {"key": "person_桃幹仙",  "label": "桃幹仙",  "type": "PERSON", "subtype": "secondary","faction": "taogu",    "aliases": ["桃幹仙"]},
    {"key": "person_桃枝仙",  "label": "桃枝仙",  "type": "PERSON", "subtype": "secondary","faction": "taogu",    "aliases": ["桃枝仙"]},
    {"key": "person_桃葉仙",  "label": "桃葉仙",  "type": "PERSON", "subtype": "secondary","faction": "taogu",    "aliases": ["桃葉仙"]},
    {"key": "person_桃花仙",  "label": "桃花仙",  "type": "PERSON", "subtype": "secondary","faction": "taogu",    "aliases": ["桃花仙"]},
    {"key": "person_桃實仙",  "label": "桃實仙",  "type": "PERSON", "subtype": "secondary","faction": "taogu",    "aliases": ["桃實仙"]},
    # ── 江湖散人 ──
    {"key": "person_田伯光",  "label": "田伯光",  "type": "PERSON", "subtype": "secondary","faction": "other",    "aliases": ["田伯光"]},
    {"key": "person_祖千秋",  "label": "祖千秋",  "type": "PERSON", "subtype": "secondary","faction": "other",    "aliases": ["祖千秋"]},
    {"key": "person_不戒",    "label": "不戒",    "type": "PERSON", "subtype": "secondary","faction": "other",    "aliases": ["不戒和尚", "不戒"]},
    {"key": "person_木高峰",  "label": "木高峰",  "type": "PERSON", "subtype": "secondary","faction": "other",    "aliases": ["木高峰"]},
    {"key": "person_平一指",  "label": "平一指",  "type": "PERSON", "subtype": "secondary","faction": "other",    "aliases": ["平一指"]},
    {"key": "person_丹青生",  "label": "丹青生",  "type": "PERSON", "subtype": "secondary","faction": "other",    "aliases": ["丹青生"]},
    {"key": "person_黑白子",  "label": "黑白子",  "type": "PERSON", "subtype": "secondary","faction": "other",    "aliases": ["黑白子"]},
    # ── 地點 ──
    {"key": "place_華山",     "label": "華山",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["華山"]},
    {"key": "place_嵩山",     "label": "嵩山",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["嵩山"]},
    {"key": "place_恆山",     "label": "恆山",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["恆山"]},
    {"key": "place_衡山",     "label": "衡山",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["衡山"]},
    {"key": "place_少林寺",   "label": "少林寺",  "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["少林寺"]},
    {"key": "place_武當",     "label": "武當",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["武當山", "武當"]},
    {"key": "place_西湖",     "label": "西湖",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["西湖"]},
    {"key": "place_洛陽",     "label": "洛陽",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["洛陽"]},
    {"key": "place_福州",     "label": "福州",    "type": "PLACE",    "subtype": "place",    "faction": None, "aliases": ["福州"]},
    # ── 空間建築 ──
    {"key": "building_思過崖",  "label": "思過崖",  "type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["思過崖"]},
    {"key": "building_福威鏢局","label": "福威鏢局","type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["福威鏢局"]},
    {"key": "building_黑木崖",  "label": "黑木崖",  "type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["黑木崖"]},
    {"key": "building_梅莊",    "label": "梅莊",    "type": "BUILDING", "subtype": "building", "faction": None, "aliases": ["梅莊"]},
    # ── 武功秘笈 ──
    {"key": "martial_辟邪劍法", "label": "辟邪劍法","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["辟邪劍法", "辟邪劍譜"]},
    {"key": "martial_獨孤九劍", "label": "獨孤九劍","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["獨孤九劍"]},
    {"key": "martial_吸星大法", "label": "吸星大法","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["吸星大法"]},
    {"key": "martial_葵花寶典", "label": "葵花寶典","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["葵花寶典"]},
    {"key": "martial_易筋經",   "label": "易筋經",  "type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["易筋經"]},
    {"key": "martial_紫霞神功", "label": "紫霞神功","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["紫霞神功", "紫霞功"]},
    {"key": "martial_嵩山劍法", "label": "嵩山劍法","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["嵩山劍法"]},
    {"key": "martial_華山劍法", "label": "華山劍法","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["華山劍法"]},
    {"key": "martial_北冥神功", "label": "北冥神功","type": "MARTIAL",  "subtype": "martial",  "faction": None, "aliases": ["北冥神功"]},
    # ── 組織派別 ──
    {"key": "org_日月神教",  "label": "日月神教", "type": "ORG", "subtype": "org", "faction": None, "aliases": ["日月神教", "魔教"]},
    {"key": "org_五嶽劍派",  "label": "五嶽劍派", "type": "ORG", "subtype": "org", "faction": None, "aliases": ["五嶽劍派", "五岳劍派"]},
    {"key": "org_華山派",    "label": "華山派",   "type": "ORG", "subtype": "org", "faction": None, "aliases": ["華山派"]},
    {"key": "org_少林",      "label": "少林",     "type": "ORG", "subtype": "org", "faction": None, "aliases": ["少林派"]},
    {"key": "org_嵩山派",    "label": "嵩山派",   "type": "ORG", "subtype": "org", "faction": None, "aliases": ["嵩山派"]},
    {"key": "org_恆山派",    "label": "恆山派",   "type": "ORG", "subtype": "org", "faction": None, "aliases": ["恆山派"]},
    {"key": "org_衡山派",    "label": "衡山派",   "type": "ORG", "subtype": "org", "faction": None, "aliases": ["衡山派"]},
    {"key": "org_丐幫",      "label": "丐幫",     "type": "ORG", "subtype": "org", "faction": None, "aliases": ["丐幫"]},
]

# Build lookup: alias → entity (longest aliases first to avoid partial match)
ALIAS_MAP: list[tuple[str, dict]] = []
for ent in ENTITIES:
    for alias in sorted(ent["aliases"], key=len, reverse=True):
        ALIAS_MAP.append((alias, ent))
# Sort overall by alias length descending so longer matches win
ALIAS_MAP.sort(key=lambda x: len(x[0]), reverse=True)


def annotate_paragraph(text: str) -> list[dict]:
    """Return list of entity spans found in text, non-overlapping (greedy longest match)."""
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
    """Annotate ebook, build entity_index, build social network."""
    # entity_index: key → {label, type, subtype, faction, frequency, para_count, surface_forms, paragraphs}
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

    # co-occurrence: (key_a, key_b) → count
    cooccurrence: dict[tuple[str,str], int] = {}

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

            # co-occurrence (only PERSON keys)
            person_keys = sorted(k for k in keys_in_para if k.startswith("person_"))
            for i, ka in enumerate(person_keys):
                for kb in person_keys[i+1:]:
                    pair = (ka, kb) if ka < kb else (kb, ka)
                    cooccurrence[pair] = cooccurrence.get(pair, 0) + 1

    # Trim paragraph lists to top 100 per entity (by chapter order)
    for k, ent in entity_index.items():
        ent["paragraphs"] = ent["paragraphs"][:100]

    # Build social network nodes & links (PERSON only, frequency > 0)
    person_entities = [e for e in ENTITIES if e["type"] == "PERSON"]
    nodes = []
    for ent in person_entities:
        ei = entity_index[ent["key"]]
        if ei["frequency"] == 0:
            continue
        # Count unique chapters
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

    # Compute degree stats
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
