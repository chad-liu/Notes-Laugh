#!/usr/bin/env python3
"""
Extract chapter data from 天龍八部.html and generate JSON data files
for the 天龍八部-demo website.
"""
import re
import json
import os

INPUT_HTML = os.path.join(os.path.dirname(__file__), '..', '天龍八部.html')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data')

def strip_html(html: str) -> str:
    text = re.sub(r'<[^>]+>', '', html)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    return text.strip()

def split_paragraphs(content_html: str) -> list[str]:
    parts = re.split(r'(?:<br\s*/?>){2,}|\r?\n\r?\n', content_html, flags=re.IGNORECASE)
    result = []
    for part in parts:
        text = strip_html(part).strip()
        if not text:
            continue
        if re.match(r'^[《》〈〉「」『』【】\s]*天龍八部[《》〈〉「」『』【】\s]*金庸', text):
            continue
        if len(text) < 5:
            continue
        result.append(text)
    return result

def extract_chapters_from_html(html_path: str) -> list[dict]:
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'const chapters\s*=\s*(\[.*?\]);', content, re.DOTALL)
    if not match:
        match = re.search(r'const chapters\s*=\s*(\[.+)', content)
        if match:
            start = match.start(1)
            depth = 0
            end = start
            for i, c in enumerate(content[start:], start):
                if c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            raw = content[start:end]
        else:
            raise ValueError("Cannot find 'const chapters' in HTML")
    else:
        raw = match.group(1)

    return json.loads(raw)

def build_data(chapters_raw: list[dict]) -> tuple[dict, dict, dict]:
    ebook_chapters = []
    search_docs = []
    stat_chapters = []
    global_para_n = 0
    total_chars = 0
    total_paras = 0

    for ch_idx, ch in enumerate(chapters_raw):
        title = ch.get('title', '').strip()
        ch_n = ch_idx
        ch_id = f"tlbb_ch{ch_n:03d}"
        paragraphs_html = ch.get('content', '')
        paras = split_paragraphs(paragraphs_html)
        if paras and paras[0].strip() == title.strip():
            paras = paras[1:]

        ch_paras = []
        ch_char_count = 0
        for p_idx, text in enumerate(paras):
            global_para_n += 1
            p_id = f"tlbb_p{global_para_n:05d}"
            para_obj = {"id": p_id, "n": p_idx + 1, "text": text}
            ch_paras.append(para_obj)
            ch_char_count += len(text)
            search_docs.append({
                "id": p_id,
                "chapter_id": ch_id,
                "chapter_number": ch_n,
                "chapter_title": title,
                "paragraph_number": p_idx + 1,
                "text": text,
            })

        total_chars += ch_char_count
        total_paras += len(ch_paras)

        ebook_chapters.append({
            "id": ch_id,
            "n": ch_n,
            "title": title,
            "paragraphs": ch_paras,
        })
        stat_chapters.append({
            "id": ch_id,
            "n": ch_n,
            "title": title,
            "character_count": ch_char_count,
            "paragraph_count": len(ch_paras),
        })

    ebook = {
        "book": {"title": "天龍八部", "author": "金庸", "chapter_count": len(ebook_chapters)},
        "chapters": ebook_chapters,
    }
    search_index = {"documents": search_docs}
    statistics = {
        "book": {
            "title": "天龍八部",
            "author": "金庸",
            "chapter_count": len(ebook_chapters),
            "total_characters": total_chars,
            "total_paragraphs": total_paras,
        },
        "chapters": stat_chapters,
    }
    return ebook, search_index, statistics

def write_json_and_js(data: dict, key: str, out_dir: str) -> None:
    json_path = os.path.join(out_dir, key)
    js_path = json_path + '.js'
    json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(f"window.DEMO_JSON=window.DEMO_JSON||{{}};window.DEMO_JSON['data/{key}']={json_str};")
    size_kb = os.path.getsize(json_path) / 1024
    print(f"  {key}: {size_kb:.0f} KB  ({js_path.split('/')[-1]} also written)")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Reading {INPUT_HTML} ...")
    chapters_raw = extract_chapters_from_html(INPUT_HTML)
    print(f"  Found {len(chapters_raw)} chapters in source HTML")

    print("Building data structures ...")
    ebook, search_index, statistics = build_data(chapters_raw)

    ch_count = len(ebook['chapters'])
    total_paras = statistics['book']['total_paragraphs']
    total_chars = statistics['book']['total_characters']
    print(f"  Chapters: {ch_count}, Paragraphs: {total_paras}, Characters: {total_chars:,}")

    print(f"Writing to {OUTPUT_DIR}/")
    write_json_and_js(ebook, 'ebook.json', OUTPUT_DIR)
    write_json_and_js(search_index, 'search_index.json', OUTPUT_DIR)
    write_json_and_js(statistics, 'statistics.json', OUTPUT_DIR)
    print("Done.")

if __name__ == '__main__':
    main()
