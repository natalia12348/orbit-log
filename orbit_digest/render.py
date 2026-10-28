from html import escape

ORBIT_MARK = (
    "<svg class=\"mark\" viewBox=\"0 0 48 48\" width=\"44\" height=\"44\" aria-hidden=\"true\">"
    "<ellipse cx=\"24\" cy=\"24\" rx=\"21\" ry=\"9\" transform=\"rotate(-28 24 24)\" fill=\"none\" stroke=\"#ffb347\" stroke-width=\"1.5\"/>"
    "<circle cx=\"24\" cy=\"24\" r=\"7\" fill=\"#0e1422\" stroke=\"#d8deea\" stroke-width=\"1.5\"/>"
    "<circle cx=\"41\" cy=\"15.5\" r=\"2.6\" fill=\"#ffb347\"/></svg>"
)

STYLE = """
:root{--bg:#070a12;--panel:#0d1322;--line:#1f2a44;--text:#d8deea;--muted:#7f8aa3;--amber:#ffb347;--teal:#5fd3c4;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;--sans:-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background-color:var(--bg);color:var(--text);font:16px/1.65 var(--sans);
background-image:radial-gradient(1px 1px at 12% 18%,#ffffff99,transparent),radial-gradient(1px 1px at 38% 72%,#ffffff66,transparent),radial-gradient(1.4px 1.4px at 66% 34%,#ffffffaa,transparent),radial-gradient(1px 1px at 84% 80%,#ffffff55,transparent),radial-gradient(1px 1px at 52% 8%,#ffffff77,transparent),radial-gradient(1.2px 1.2px at 92% 52%,#ffffff88,transparent),radial-gradient(1px 1px at 24% 90%,#ffffff55,transparent);
background-size:420px 420px}
header{border-bottom:1px solid var(--line);padding:28px 0 20px}
.wrap{max-width:860px;margin:0 auto;padding:0 16px}
.top{display:flex;align-items:center;gap:16px}
.mark{flex:none}
h1{margin:0;font:600 26px var(--mono);letter-spacing:.28em;text-transform:uppercase}
.sub{margin:2px 0 0;font:12px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.strip{display:flex;flex-wrap:wrap;gap:6px 22px;margin-top:18px;padding-top:12px;border-top:1px dashed var(--line);font:12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.strip b{color:var(--amber);font-weight:600}
main{max-width:860px;margin:0 auto;padding:8px 16px 56px}
h2{margin:36px 0 14px;font:600 13px var(--mono);letter-spacing:.24em;text-transform:uppercase;color:var(--teal)}
h2::before{content:"// ";color:var(--muted)}
.packet{position:relative;margin-bottom:14px;padding:16px 20px 14px;background:var(--panel);border:1px solid var(--line)}
.packet::before,.packet::after{content:"";position:absolute;width:10px;height:10px;border:solid var(--amber);opacity:.8}
.packet::before{top:-1px;left:-1px;border-width:2px 0 0 2px}
.packet::after{right:-1px;bottom:-1px;border-width:0 2px 2px 0}
.tag{font:11px var(--mono);letter-spacing:.18em;text-transform:uppercase;color:var(--amber)}
.packet h3{margin:2px 0 4px;font:600 18px/1.4 var(--sans)}
.packet h3 a{color:#fff;text-decoration:none;background:linear-gradient(var(--amber),var(--amber)) 0 100%/0 1px no-repeat;transition:background-size .2s}
.packet h3 a:hover{background-size:100% 1px}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:4px 14px;margin-bottom:10px;font:12px var(--mono);color:var(--muted)}
.sig{display:inline-flex;align-items:flex-end;gap:2px;height:12px;margin-right:6px;vertical-align:-1px}
.sig i{display:block;width:4px;background:var(--line)}
.sig i:nth-child(1){height:5px}.sig i:nth-child(2){height:8px}.sig i:nth-child(3){height:12px}
.sig.s1 i:nth-child(-n+1),.sig.s2 i:nth-child(-n+2),.sig.s3 i:nth-child(-n+3){background:var(--teal)}
.sig.s3 i{background:var(--amber)}
.packet ul{margin:0 0 10px;padding-left:18px}.packet li{margin-bottom:4px;color:#c6cee0}
.packet li::marker{color:var(--amber)}
.why{margin:0;padding-top:10px;border-top:1px dashed var(--line);font-size:14px;color:#aeb8cf}
.why b{font:600 11px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--amber);margin-right:8px}
.empty{padding:18px 20px;border:1px dashed var(--line);font:13px var(--mono);color:var(--muted)}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
a.back{color:var(--teal)}
table{width:100%;border-collapse:collapse;font:14px var(--mono)}
td{padding:12px 8px;border-bottom:1px solid var(--line)}td a{color:#fff;text-decoration:none}td a:hover{color:var(--amber)}td.n{color:var(--amber);width:70px}td.c{color:var(--muted);text-align:right}
@media (max-width:560px){h1{font-size:20px}.strip{gap:4px 14px}}
"""

LEVELS = {"Beginner": 1, "Intermediate": 2, "Hard": 3}


def page(title: str, subtitle: str, strip: str, body: str) -> str:
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<meta name=\"robots\" content=\"noindex,nofollow\">"
        f"<title>{escape(title)}</title><style>{STYLE}</style></head><body>"
        f"<header><div class=\"wrap\"><div class=\"top\">{ORBIT_MARK}<div><h1>{escape(title)}</h1>"
        f"<p class=\"sub\">{escape(subtitle)}</p></div></div>{strip}</div></header>"
        f"<main>{body}</main></body></html>"
    )


def packet(item, number: int) -> str:
    label = f"{'Research' if item.kind == 'paper' else 'Field news'} {number:02d}"
    authors = ""
    if item.authors:
        shown = ", ".join(item.authors[:3]) + (" et al." if len(item.authors) > 3 else "")
        authors = f"<span>{escape(shown)}</span>"
    level = LEVELS.get(item.difficulty)
    signal = (
        f"<span><span class=\"sig s{level}\"><i></i><i></i><i></i></span>{escape(item.difficulty)}</span>"
        if level
        else f"<span>{escape(item.difficulty)}</span>"
    )
    bullets = "".join(f"<li>{escape(line)}</li>" for line in item.summary)
    return (
        "<article class=\"packet\">"
        f"<div class=\"tag\">{label}</div>"
        f"<h3><a href=\"{escape(item.link, quote=True)}\" target=\"_blank\" rel=\"noopener\">{escape(item.title)}</a></h3>"
        f"<div class=\"meta\"><span>{escape(item.source)}</span>{authors}{signal}</div>"
        f"<ul>{bullets}</ul>"
        f"<p class=\"why\"><b>Why it matters</b>{escape(item.why)}</p>"
        "</article>"
    )


def section(heading: str, items: list, empty: str) -> str:
    body = "".join(packet(item, n) for n, item in enumerate(items, 1)) if items else f"<div class=\"empty\">{escape(empty)}</div>"
    return f"<h2>{escape(heading)}</h2>{body}"


def render_day(day_label: str, entry: int, papers: list, news: list, engine: str, errors: list, sources: int) -> str:
    online = max(sources - len(errors), 0)
    strip = (
        "<div class=\"strip\">"
        f"<span>Papers <b>{len(papers)}</b></span>"
        f"<span>News <b>{len(news)}</b></span>"
        f"<span>Sources online <b>{online}/{sources}</b></span>"
        f"<span>Summaries <b>{escape(engine)}</b></span>"
        "</div>"
    )
    notes = "".join(f"<div class=\"empty\">Signal lost: {escape(e)}</div>" for e in errors)
    footer = (
        "<footer><a class=\"back\" href=\"index.html\">&larr; Log archive</a><br>"
        "Built from arXiv and public RSS feeds. Summaries are machine-made and can be wrong; "
        "open the link for the full text.</footer>"
    )
    body = (
        section("Research transmissions", papers, "No new relevant papers in this window.")
        + section("Field news", news, "No new relevant stories in this window.")
        + notes
        + footer
    )
    return page("Orbit Log", f"Entry {entry:03d} · {day_label}", strip, body)


def render_index(entries: list) -> str:
    rows = "".join(
        f"<tr><td class=\"n\">{number:03d}</td><td><a href=\"{escape(name)}\">{escape(label)}</a></td>"
        f"<td class=\"c\">{papers} papers · {news} stories</td></tr>"
        for number, name, label, papers, news in entries
    )
    body = (
        f"<h2>Log archive</h2><table>{rows}</table>"
        if rows
        else "<h2>Log archive</h2><div class=\"empty\">No entries yet.</div>"
    )
    return page("Orbit Log", "Archive", "", body)
