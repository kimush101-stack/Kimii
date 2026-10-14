"""Build system/index.html from template.html + roadmap.json + all docs/*.md.

Markdown is rendered to HTML here, at build time, so the page needs no
runtime library. Requires: pip install markdown
Run from the repo root:  python3 system/build.py
"""
import json
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYS = ROOT / "system"

LIST_OR_TABLE = re.compile(r"^\s*([-*+]\s|\d+[.)]\s|\|)")


def prep(md: str) -> str:
    """Python-Markdown needs a blank line before a list or table that follows a paragraph."""
    out, prev = [], ""
    for line in md.splitlines():
        if LIST_OR_TABLE.match(line) and prev.strip() and not LIST_OR_TABLE.match(prev) and not prev.lstrip().startswith(">"):
            out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def render(md: str) -> str:
    html = markdown.markdown(prep(md), extensions=["tables", "sane_lists", "fenced_code"])
    html = re.sub(r"<li>\s*\[ \]\s*", '<li class="task-list-item"><input type="checkbox" disabled> ', html)
    html = re.sub(r"<li>\s*\[[xX]\]\s*", '<li class="task-list-item"><input type="checkbox" checked disabled> ', html)
    return html


LETTERS = "אבגדהוזחטיכל"


def checklist(roadmap: dict) -> str:
    """Printable checklist version of the roadmap (docs/04-launch-checklist.md)."""
    out = ["# המסלול של קים: צ׳קליסט מא׳ עד ת׳", "",
           "*הקובץ נוצר אוטומטית מתוך system/roadmap.json. הגרסה האינטראקטיבית נמצאת ב־system/index.html.*", ""]
    for i, st in enumerate(roadmap["stages"]):
        out += [f"## {LETTERS[i]} · {st['title']} ({st['week_hint']})", "", st["goal"], ""]
        out += [f"- [ ] {LETTERS[i]}{n + 1} · {s['title']} ({s['time']})" for n, s in enumerate(st["steps"])]
        out += ["", f"**בסוף השלב:** {st['milestone']}", ""]
    out += ["## שגרות קבועות", ""]
    out += [f"- **{r['title']}** ({r['frequency']}): " + " ".join(r["actions"]) for r in roadmap["routines"]]
    return "\n".join(out) + "\n"


roadmap = json.loads((SYS / "roadmap.json").read_text(encoding="utf-8"))
(ROOT / "docs" / "04-launch-checklist.md").write_text(checklist(roadmap), encoding="utf-8")
docs = {}
for f in sorted((ROOT / "docs").glob("*.md")):
    md = f.read_text(encoding="utf-8")
    m = re.search(r"^#\s+(.+)$", md, re.M)
    docs[f"docs/{f.name}"] = {"title": re.sub(r"[*_`]", "", m.group(1)) if m else f.name, "html": render(md)}

payload = json.dumps({"roadmap": roadmap, "docs": docs}, ensure_ascii=False).replace("</", "<\\/")
html = (SYS / "template.html").read_text(encoding="utf-8").replace("/*__DATA__*/null", payload, 1)
(SYS / "index.html").write_text(html, encoding="utf-8")
print(f"built system/index.html: {len(roadmap['stages'])} stages, "
      f"{sum(len(s['steps']) for s in roadmap['stages'])} steps, {len(docs)} docs")
