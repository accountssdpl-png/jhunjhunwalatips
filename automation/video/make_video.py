#!/usr/bin/env python3
"""Make a BJ's Share Tips Hindi market video from a content JSON file.

Usage:  python3 make_video.py content.json OUT_DIR
Writes: OUT_DIR/<date>-<slot>.mp4 (720x1280, ~3-4 MB) and OUT_DIR/<date>-<slot>.jpg (poster)

content.json:
{
  "date": "2026-11-16", "slot": "morning" | "evening",
  "scenes": [ {"type": "...", "kicker": "...", "title": "...", "vo": "Hindi narration", ...}, ... ]
}
Scene types and their extra fields:
  intro     subtitle, bullets[str]                      (bright first slide with logo)
  tiles     items[{name, value, change, dir:"up"|"dn"}]  (index levels)
  reasons   items[{big, text, dir}]                      (big number + explanation)
  bars      items[{name, value(float, %)}], note         (weekly / sector moves)
  list      items[{name, sub, value, dir}], note         (results, stocks in news)
  calendar  items[{day, text}]
  big       items[{label, value, dir}]                   (2-4 large figures)
  levels    rows[{label, values[str], kind:"res"|"now"|"sup"}], note
  outro     url, disclaimer                              (website + disclaimer, logo)
Title markup: *gold words*  and  !red words!  ; use <br> for a line break.
Write narration numbers in Hindi words for natural speech.
"""
import asyncio, html, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "node_modules", "@fontsource")
VOICE, RATE = "hi-IN-MadhurNeural", "+14%"


def esc(s):
    return html.escape(str(s or ""))


def title(s):
    t = esc(s).replace("&lt;br&gt;", "<br>")
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return re.sub(r"!(.+?)!", r'<em class="r">\1</em>', t)


def dircls(d):
    return "up" if d == "up" else "dn" if d == "dn" else "gold"


def x_get(sc, k, d=""):
    return sc.get(k) or d


def body(sc):
    t, it = sc["type"], sc.get("items", [])
    note = f'<div class="note">{esc(sc["note"])}</div>' if sc.get("note") else ""
    if t == "intro":
        b = "<br>".join(esc(x) for x in sc.get("bullets", []))
        return f'<div class="date">{esc(sc.get("subtitle"))}</div><div class="bul">{b}</div><img class="heroimg" src="logo.jpg">'
    if t == "tiles":
        return '<div class="tiles">' + "".join(
            f'<div class="tile"><span>{esc(x["name"])}</span><b>{esc(x["value"])}</b><i class="{dircls(x.get("dir"))}">{"▲" if x.get("dir")=="up" else "▼" if x.get("dir")=="dn" else ""} {esc(x.get("change"))}</i></div>' for x in it) + "</div>" + note
    if t == "reasons":
        return '<div class="why">' + "".join(
            f'<div class="{dircls(x.get("dir"))}"><b>{esc(x["big"])}</b><p>{esc(x["text"])}</p></div>' for x in it) + "</div>" + note
    if t == "bars":
        mx = max([abs(float(x["value"])) for x in it] + [0.1])
        rows = "".join(
            f'<div class="br"><span>{esc(x["name"])}</span><div class="tr"><i class="{"u" if float(x["value"])>=0 else "d"}" style="width:{abs(float(x["value"]))/mx*50:.1f}%"></i></div><b class="{"up" if float(x["value"])>=0 else "dn"}">{"+" if float(x["value"])>=0 else "−"}{abs(float(x["value"])):g}%</b></div>' for x in it)
        return f'<div class="bars">{rows}</div>' + note
    if t == "list":
        return '<div class="tbl">' + "".join(
            f'<div class="tr2"><span>{esc(x["name"])}</span><p>{esc(x.get("sub"))}</p><b class="{dircls(x.get("dir"))}">{esc(x.get("value"))}</b></div>' for x in it) + "</div>" + note
    if t == "calendar":
        return '<div class="cal">' + "".join(f'<div><time>{esc(x["day"])}</time><p>{esc(x["text"])}</p></div>' for x in it) + "</div>" + note
    if t == "big":
        return '<div class="big3">' + "".join(
            f'<div><span>{esc(x["label"])}</span><b class="{dircls(x.get("dir"))}">{esc(x["value"])}</b></div>' for x in it) + "</div>" + note
    if t == "levels":
        return '<div class="lvls">' + "".join(
            f'<div class="{esc(r.get("kind","now"))}"><span>{esc(r["label"])}</span>' + "".join(f"<b>{esc(v)}</b>" for v in r.get("values", [])) + "</div>" for r in sc.get("rows", [])) + "</div>" + note
    if t == "call":
        side = esc(x_get(sc, "side", "BUY")).upper()
        return (f'<div class="call"><div class="ch"><b>{esc(sc.get("stock"))}</b><span class="sd {"sell" if side=="SELL" else ""}">{side}</span></div>'
                f'<div class="cm">{esc(sc.get("exchange","NSE"))}: {esc(sc.get("symbol"))} · {esc(sc.get("timeframe"))}</div>'
                f'<div class="lv"><div><span>{esc(sc.get("entryLabel","रिको प्राइस"))}</span><b>{esc(sc.get("entry"))}</b></div><div class="ctg"><span>टारगेट</span><b>{esc(sc.get("target"))}</b></div><div class="csl"><span>स्टॉप-लॉस</span><b>{esc(sc.get("sl"))}</b></div></div>'
                f'<div class="src">स्रोत: {esc(sc.get("firm"))}<br>SEBI RA {esc(sc.get("reg"))} · {esc(sc.get("date"))}</div></div>' + note)
    if t == "outro":
        return f'<div class="url">{esc(sc.get("url"))}</div><div class="disc">{esc(sc.get("disclaimer"))}</div><img class="heroimg" src="logo.jpg">'
    raise ValueError("unknown scene type " + t)


CSS = """@font-face{font-family:M;src:url(F/mukta/files/mukta-devanagari-800-normal.woff2);font-weight:800}
@font-face{font-family:M;src:url(F/mukta/files/mukta-latin-800-normal.woff2);font-weight:800;unicode-range:U+0000-00FF,U+20B9,U+2013,U+2212,U+2248,U+25B2,U+25BC}
@font-face{font-family:M;src:url(F/mukta/files/mukta-devanagari-500-normal.woff2);font-weight:500}
@font-face{font-family:M;src:url(F/mukta/files/mukta-latin-500-normal.woff2);font-weight:500;unicode-range:U+0000-00FF,U+20B9,U+2013,U+2212,U+2248}
@font-face{font-family:G;src:url(F/space-grotesk/files/space-grotesk-latin-700-normal.woff2);font-weight:700}
*{box-sizing:border-box;margin:0}body{width:1080px;height:1920px;overflow:hidden;font-family:M,sans-serif;color:#eef2ff}
.s{position:absolute;inset:0;padding:110px 80px 80px;display:none;flex-direction:column;background:radial-gradient(900px 700px at 90% 0%,rgba(48,96,200,.55),transparent 60%),radial-gradient(800px 600px at 0% 100%,rgba(242,189,69,.12),transparent 60%),linear-gradient(180deg,#061230,#040b1f)}
.s.on{display:flex}
.s.light{background:radial-gradient(900px 700px at 100% 0%,rgba(255,215,122,.9),transparent 60%),radial-gradient(800px 700px at 0% 100%,rgba(47,209,122,.35),transparent 60%),linear-gradient(170deg,#fff8e6,#ffe7a8 55%,#f6c95a)}
.s.light,.s.light h1{color:#0b1f4a}.s.light h1 em{color:#c8231e}.s.light .top small,.s.light .foot{color:#3a4a6b}.s.light .bul{color:#1b2b4d}.s.light .date{color:#0d7a3e}.s.light .k{color:#0b1f4a;background:rgba(11,31,74,.08);border-color:rgba(11,31,74,.25)}.s.light .foot{border-color:rgba(11,31,74,.2)}.s.light .dots i{background:rgba(11,31,74,.2)}.s.light .dots i.a{background:#c8231e}.s.light .disc{color:#1b2b4d}
.top{display:flex;align-items:center;gap:22px}.top img{width:150px;border-radius:14px;border:2px solid rgba(242,189,69,.7)}.top b{font:700 40px G}.top small{display:block;font:500 28px M;color:#93a3c4}
.k{margin-top:80px;align-self:flex-start;font:800 36px M;color:#f2bd45;background:rgba(242,189,69,.12);border:2px solid rgba(242,189,69,.4);padding:8px 26px;border-radius:999px}
h1{font:800 104px/1.08 M;margin:30px 0 44px}h1 em{font-style:normal;color:#f2bd45}h1 em.r{color:#ff5d6c}
.date{font:800 54px M;color:#2fd17a;margin-bottom:34px}.bul{font:500 44px/1.8 M;color:#c9d3ea}
.heroimg{width:100%;border-radius:30px;border:3px solid rgba(242,189,69,.6);box-shadow:0 30px 80px rgba(0,0,0,.45);margin-top:50px}
.tiles{display:grid;gap:24px}.tile{background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.1);border-radius:30px;padding:26px 40px}.tile span{font:800 34px M;color:#f2bd45}.tile b{display:block;font:700 100px/1.1 G}.tile i{font:800 44px M;font-style:normal}
.up{color:#2fd17a}.dn{color:#ff5d6c}.gold{color:#f2bd45}
.why{display:grid;gap:24px}.why div{background:rgba(255,255,255,.06);border-left:10px solid #ff5d6c;border-radius:24px;padding:28px 40px}.why div.up{border-left-color:#2fd17a}.why div.gold{border-left-color:#f2bd45}.why b{font:700 80px/1.1 G}.why .dn b{color:#ff5d6c}.why .up b{color:#2fd17a}.why .gold b{color:#f2bd45}.why p{font:500 42px/1.4 M;color:#d6def2}
.bars{display:grid;gap:28px}.br{display:grid;grid-template-columns:330px 1fr 190px;align-items:center;gap:20px;font:800 44px M}.br b{text-align:right;font:700 50px G}
.tr{position:relative;height:46px;background:linear-gradient(rgba(255,255,255,.25),rgba(255,255,255,.25)) 50% 0/3px 100% no-repeat}.tr i{position:absolute;top:4px;height:38px;border-radius:8px}.tr i.u{left:50%;background:#2fd17a}.tr i.d{right:50%;background:#ff5d6c}
.big3{display:grid;gap:28px}.big3 div{background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.1);border-radius:30px;padding:34px 44px}.big3 span{font:500 40px M;color:#aab6d3}.big3 b{display:block;font:800 88px/1.2 M}
.tbl{display:grid;gap:14px}.tr2{display:grid;grid-template-columns:1fr auto;gap:0 20px;background:rgba(255,255,255,.06);border-radius:24px;padding:16px 36px}.tr2 span{font:800 50px M}.tr2 p{grid-column:1;font:500 36px M;color:#aab6d3}.tr2 b{grid-row:1/3;grid-column:2;align-self:center;font:800 60px M}
.note{margin-top:28px;font:500 36px M;color:#93a3c4}
.cal{display:grid;gap:18px}.cal div{display:grid;grid-template-columns:230px 1fr;gap:24px;align-items:center;background:rgba(255,255,255,.06);border-radius:24px;padding:24px 34px}.cal time{font:800 48px M;color:#f2bd45}.cal p{font:500 42px/1.3 M}
.lvls{display:grid;gap:22px}.lvls div{border-radius:28px;padding:26px 44px;display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 40px}.lvls span{width:100%;font:800 38px M}.lvls b{font:700 88px G}
.res{background:rgba(255,93,108,.12);border:2px solid rgba(255,93,108,.5)}.res span,.res b{color:#ff8a95}.now{background:rgba(242,189,69,.14);border:2px solid rgba(242,189,69,.6)}.now span,.now b{color:#f2bd45}.sup{background:rgba(47,209,122,.12);border:2px solid rgba(47,209,122,.5)}.sup span,.sup b{color:#5fe39a}
.url{font:700 58px G;color:#0b1430;background:linear-gradient(135deg,#ffd77a,#f2bd45);border-radius:999px;padding:24px 40px;text-align:center;margin:10px 0 40px}.disc{font:500 40px/1.5 M;color:#c9d3ea}
.call{background:rgba(255,255,255,.06);border:2px solid rgba(242,189,69,.45);border-radius:34px;padding:40px 44px}
.ch{display:flex;justify-content:space-between;align-items:center;gap:20px}.ch b{font:800 76px/1.1 M}.sd{font:700 44px G;background:#2fd17a;color:#04140b;border-radius:999px;padding:8px 30px}.sd.sell{background:#ff5d6c;color:#fff}
.cm{font:500 38px M;color:#aab6d3;margin:10px 0 30px}
.call .lv{display:grid;grid-template-columns:1fr;gap:18px}.call .lv div{display:flex;justify-content:space-between;align-items:baseline;background:rgba(0,0,0,.25);border-radius:22px;padding:22px 30px}.call .lv span{font:800 40px M;color:#c9d3ea}.call .lv b{font:700 72px G}.call .lv .ctg b{color:#2fd17a}.call .lv .csl b{color:#ff5d6c}
.src{margin-top:30px;font:500 36px/1.5 M;color:#f2bd45}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:center;border-top:2px solid rgba(255,255,255,.12);padding-top:30px;font:500 32px M;color:#93a3c4}.dots{display:flex;gap:10px}.dots i{width:16px;height:16px;border-radius:50%;background:rgba(255,255,255,.2)}.dots i.a{background:#f2bd45;width:44px;border-radius:8px}"""


def build_html(c, workdir):
    S = c["scenes"]
    out = "<!doctype html><meta charset=utf-8><style>" + CSS.replace("url(F/", "url(file://" + F + "/") + "</style>"
    sub = {"morning": "सुबह की मार्केट खबर", "evening": "शाम की मार्केट खबर", "tips": "आज के 2 रिसर्च कॉल्स"}.get(c.get("slot"), "मार्केट खबर")
    for i, sc in enumerate(S):
        dots = "".join(f'<i class="{"a" if j == i else ""}"></i>' for j in range(len(S)))
        light = " light" if sc["type"] == "intro" else ""
        out += (f'<section class="s{light}" id="s{i}"><div class="top"><img src="logo.jpg"><div><b>BJ’s Share Tips</b><small>{sub} · हिंदी</small></div></div>'
                f'<div class="k">{esc(sc.get("kicker"))}</div><h1>{title(sc.get("title"))}</h1>{body(sc)}'
                f'<div class="foot"><span>जानकारी मात्र · निवेश सलाह नहीं</span><div class="dots">{dots}</div></div></section>')
    p = os.path.join(workdir, "slides.html")
    open(p, "w").write(out)
    subprocess.run(["cp", os.path.join(HERE, "logo.jpg"), workdir], check=True)
    return p


async def shoot(htmlp, n, workdir):
    from playwright.async_api import async_playwright
    chrome = next((x for x in ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"] if os.path.exists(x)), None)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=chrome, args=["--no-sandbox", "--allow-file-access-from-files"]) if chrome else await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + htmlp)
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(800)
        for i in range(n):
            await pg.evaluate(f"document.querySelectorAll('.s').forEach((e,j)=>e.classList.toggle('on',j=={i}))")
            await pg.wait_for_timeout(120)
            await pg.screenshot(path=os.path.join(workdir, f"s{i}.png"))
        await b.close()


async def voice(S, workdir):
    import edge_tts
    for i, sc in enumerate(S):
        out = os.path.join(workdir, f"vo{i}.mp3")
        for k in range(6):
            try:
                await edge_tts.Communicate(sc["vo"], VOICE, rate=RATE).save(out + ".tmp")
                if os.path.getsize(out + ".tmp") > 4000:
                    os.replace(out + ".tmp", out)
                    break
            except Exception as e:
                print("voice retry", i, k, e)
            await asyncio.sleep(3)
        else:
            raise RuntimeError(f"voice failed for scene {i}")


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def render(n, workdir, outmp4):
    lst = os.path.join(workdir, "list.txt")
    with open(lst, "w") as L:
        for i in range(n):
            d = round(dur(os.path.join(workdir, f"vo{i}.mp3")) + 0.6, 2)
            fo = round(d - 0.25, 2)
            fin = "" if i == 0 else "fade=t=in:st=0:d=0.25,"
            dl = 150 if i == 0 else 250
            tmp, fin_name = os.path.join(workdir, f"tmp_{i}.mp4"), os.path.join(workdir, f"scene_{i}.mp4")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", os.path.join(workdir, f"s{i}.png"), "-i", os.path.join(workdir, f"vo{i}.mp3"),
                            "-filter_complex", f"[0:v]scale=720:1280,format=yuv420p,loop=-1:1,trim=duration={d},setpts=PTS-STARTPTS,{fin}fade=t=out:st={fo}:d=0.25[v];[1:a]adelay={dl}|{dl},apad,atrim=duration={d},aresample=44100,aformat=channel_layouts=mono[a]",
                            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "30", "-r", "30", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "64k", "-ar", "44100", tmp], check=True)
            os.replace(tmp, fin_name)
            L.write(f"file '{fin_name}'\n")
    tmpout = outmp4 + ".part.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", tmpout], check=True)
    os.replace(tmpout, outmp4)


def main():
    c = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    S = c["scenes"]
    assert S and S[0]["type"] == "intro" and S[-1]["type"] == "outro", "first scene must be intro, last must be outro"
    name = f'{c["date"]}-{c["slot"]}'
    with tempfile.TemporaryDirectory() as w:
        hp = build_html(c, w)
        asyncio.run(shoot(hp, len(S), w))
        asyncio.run(voice(S, w))
        mp4 = os.path.join(outdir, name + ".mp4")
        render(len(S), w, mp4)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(w, "s0.png"), "-vf", "scale=540:960", "-q:v", "4", os.path.join(outdir, name + ".jpg")], check=True)
    print(json.dumps({"video": mp4, "poster": os.path.join(outdir, name + ".jpg"), "seconds": round(dur(mp4), 1), "bytes": os.path.getsize(mp4)}))


if __name__ == "__main__":
    main()
