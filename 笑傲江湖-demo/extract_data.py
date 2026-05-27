#!/usr/bin/env python3
"""
Extract chapter data from 笑傲江湖.html and generate JSON data files
for the 笑傲江湖-demo website.
"""
import re
import json
import os

INPUT_HTML = os.path.join(os.path.dirname(__file__), '..', '笑傲江湖.html')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data')

def strip_html(html: str) -> str:
    """Remove HTML tags and normalise whitespace."""
    text = re.sub(r'<[^>]+>', '', html)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    return text.strip()

def split_paragraphs(content_html: str) -> list[str]:
    """Split chapter HTML content into clean paragraph strings."""
    # Split on double <br> (paragraph boundaries)
    parts = re.split(r'(?:<br\s*/?>){2,}|\r?\n\r?\n', content_html, flags=re.IGNORECASE)
    result = []
    for part in parts:
        text = strip_html(part).strip()
        # Filter: skip empty, skip chapter header lines (《笑傲江湖》), skip short lines
        if not text:
            continue
        if re.match(r'^[《》〈〉「」『』【】\s]*笑傲江湖[《》〈〉「」『』【】\s]*金庸', text):
            continue
        if len(text) < 5:
            continue
        result.append(text)
    return result

def extract_chapters_from_html(html_path: str) -> list[dict]:
    """Parse 笑傲江湖.html and extract the chapters JS array."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the const chapters = [...] declaration
    # It's on a single very long line starting with "const chapters ="
    match = re.search(r'const chapters\s*=\s*(\[.*?\]);', content, re.DOTALL)
    if not match:
        # Try single-line match (the array may be on one long line)
        match = re.search(r'const chapters\s*=\s*(\[.+)', content)
        if match:
            # The array ends at ]); — find the last ]);
            start = match.start(1)
            # Find matching bracket
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

    chapters_raw = json.loads(raw)
    return chapters_raw

def build_data(chapters_raw: list[dict]) -> tuple[dict, dict, dict]:
    """Build ebook, search_index, and statistics dicts from raw chapter data."""
    ebook_chapters = []
    search_docs = []
    stat_chapters = []
    global_para_n = 0
    total_chars = 0
    total_paras = 0

    for ch_idx, ch in enumerate(chapters_raw):
        title = ch.get('title', '').strip()
        # Chapter number: skip index 0 if it's a table of contents
        ch_n = ch_idx  # keep as-is; index 0 = 目錄

        ch_id = f"xiaoyao_ch{ch_n:03d}"
        paragraphs_html = ch.get('content', '')
        paras = split_paragraphs(paragraphs_html)
        # Drop leading paragraph that is just the chapter title repeated
        if paras and paras[0].strip() == title.strip():
            paras = paras[1:]

        ch_paras = []
        ch_char_count = 0
        for p_idx, text in enumerate(paras):
            global_para_n += 1
            p_id = f"xiaoyao_p{global_para_n:05d}"
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
        "book": {
            "title": "笑傲江湖",
            "author": "金庸",
            "chapter_count": len(ebook_chapters),
        },
        "chapters": ebook_chapters,
    }
    search_index = {"documents": search_docs}
    statistics = {
        "book": {
            "title": "笑傲江湖",
            "author": "金庸",
            "chapter_count": len(ebook_chapters),
            "total_characters": total_chars,
            "total_paragraphs": total_paras,
        },
        "chapters": stat_chapters,
    }
    return ebook, search_index, statistics

def write_json_and_js(data: dict, key: str, out_dir: str) -> None:
    """Write foo.json and foo.json.js (fallback for file://)."""
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
