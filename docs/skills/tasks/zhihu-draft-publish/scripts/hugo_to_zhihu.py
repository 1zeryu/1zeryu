#!/usr/bin/env python3
"""把 Hugo 文章（Markdown）转成知乎「导入文档」可用的 Markdown。

做的是机械转换，不改动正文文字：
  - 去掉 YAML front matter
  - 脚注 [^id] 改成正文编号 [n]，文末追加编号的「参考」列表
  - HTML <table> 转 Markdown 表格
  - <figure>/<img> 转 Markdown 图片占位 ![alt](IMG:xxx.png)（知乎读不到本地文件，导入后需手动插图）
  - Hugo {{< details >}}、<a id>、着色 <span> 等转成普通 Markdown

用法：
  python3 hugo_to_zhihu.py content/post/xxx/index.md -o /tmp/out.md
"""
import argparse
import re
from pathlib import Path


def split_front_matter(text: str):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = text[3:end]
    meta = {}
    for line in fm.splitlines():
        m = re.match(r"^(title|description|slug|date):\s*(.*)$", line.strip())
        if m:
            meta[m.group(1)] = m.group(2).strip().strip('"')
    return meta, text[end + 4:].lstrip("\n")


def extract_footnotes(body: str):
    defs = {}
    kept = []
    for line in body.splitlines():
        m = re.match(r"^\[\^([^\]]+)\]:\s*(.+)$", line)
        if m:
            defs[m.group(1)] = m.group(2).strip()
        else:
            kept.append(line)
    body = re.sub(r"\n{4,}", "\n\n\n", "\n".join(kept)).rstrip() + "\n"
    return defs, body


def html_table_to_md(block: str) -> str:
    def clean(c):
        c = re.sub(r"</?strong>", "**", c)
        c = re.sub(r"<[^>]+>", "", c)
        return c.strip()

    rows = re.findall(r"<tr>(.*?)</tr>", block, re.S)
    out = []
    for i, row in enumerate(rows):
        cells = [clean(c) for c in re.findall(r"<t[hd]>(.*?)</t[hd]>", row, re.S)]
        out.append("| " + " | ".join(cells) + " |")
        if i == 0:
            out.append("|" + "|".join(["---"] * len(cells)) + "|")
    return "\n".join(out)


def convert(body: str):
    body = re.sub(r"<table>(.*?)</table>", lambda m: html_table_to_md(m.group(1)), body, flags=re.S)

    def figure_repl(m):
        block = m.group(0)
        img = re.search(r'<img src="([^"]+)"[^>]*alt="([^"]*)"', block)
        cap = re.search(r"<figcaption>(.*?)</figcaption>", block, re.S)
        caption = re.sub(r"<[^>]+>", "", cap.group(1)).strip() if cap else ""
        if not img:
            inner = re.sub(r"<figcaption>.*?</figcaption>", "", block, flags=re.S)
            inner = re.sub(r"</?figure>", "", inner).strip()
            return inner + (f"\n\n*{caption}*" if caption else "")
        png = Path(img.group(1)).with_suffix(".png").name
        alt = img.group(2) or caption
        out = [f"![{alt}](IMG:{png})"]
        if caption:
            out += ["", f"*{caption}*"]
        return "\n".join(out)

    body = re.sub(r"<figure>.*?</figure>", figure_repl, body, flags=re.S)

    body = re.sub(
        r'<img src="([^"]+)"[^>]*/?>',
        lambda m: f"![图](IMG:{Path(m.group(1)).with_suffix('.png').name})",
        body,
    )
    body = re.sub(r'<a id="[^"]*"></a>', "", body)

    def span_repl(m):
        inner = m.group(1).strip()
        return "\n".join("> " + ln for ln in inner.splitlines())

    body = re.sub(r'<span style="[^"]*">(.*?)</span>', span_repl, body, flags=re.S)
    body = body.replace("<strong>", "**").replace("</strong>", "**")
    body = body.replace("<em>", "*").replace("</em>", "*")

    body = re.sub(r'\{\{<\s*details\s+"([^"]*)"\s*>\}\}', r"**\1**", body)
    body = re.sub(r"\{\{<\s*/details\s*>\}\}", "", body)
    body = re.sub(r"\{\{<.*?>\}\}", "", body)

    order = []

    def ref_repl(m):
        key = m.group(1)
        if key not in order:
            order.append(key)
        return f"[{order.index(key) + 1}]"

    body = re.sub(r"\[\^([^\]]+)\]", ref_repl, body)
    return body, order


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Hugo 文章的 index.md")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()

    text = Path(args.input).read_text(encoding="utf-8")
    meta, body = split_front_matter(text)
    defs, body = extract_footnotes(body)
    body, order = convert(body)
    body = re.sub(r"\n{4,}", "\n\n\n", body).strip() + "\n"

    if order:
        body += "\n---\n\n**参考**\n\n"
        for i, key in enumerate(order, 1):
            body += f"{i}. {defs.get(key, key)}\n"

    Path(args.output).write_text(body, encoding="utf-8")
    print(f"标题: {meta.get('title')}")
    print(f"输出: {args.output}  字符 {len(body)}  脚注 {len(order)}  图片占位 {body.count('IMG:')}")
    for name in sorted(set(re.findall(r"IMG:(\S+?\.png)", body))):
        print(f"  待插图: {name}")


if __name__ == "__main__":
    main()
