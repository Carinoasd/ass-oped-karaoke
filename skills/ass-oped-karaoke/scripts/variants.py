"""衍生版：NCOP／NCED、lite、繁簡檢查。規則與理由見 references/variants.md。

    # NC 版：平移時間軸、平移拍點原點、關掉本篇專用的避讓、換片源、加 credit
    python -X utf8 variants.py nc op_kfx.ass -o op_ncop.ass --shift -1678 --fps 24000/1001 \\
        --video ncop.mp4 --title "<作品> - OP kfx (NCOP)" --const B0 --set OP_FINAL_SHIFT=0 \\
        --credit credit_op.ass --drop-fx --render

    # lite 版：同一份 Lua，另一張模板清單（遞移裁剪會把用不到的定義留在外面）
    python -X utf8 variants.py lite op_kfx.ass -o op_kfx_lite.ass \\
        --lua lua_common.lua lua_op.lua lua_op_lite.lua --templates templates_op_lite.txt --render

    # 繁簡：檢查 +TC/+SC 後綴與日中行一一對應
    python -X utf8 variants.py lang op_kfx.ass --check

`--shift` 同 `aegisub-render macro offset` 的語法：`[+-]影格數`（要 `--fps` 或能讀時間碼的影片）
或 `[+-][[[hh:]mm:]ss].ms`。**NC 的對應用影格數**，毫秒換算會差一格。
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build as build_mod  # noqa: E402
import luasync  # noqa: E402
import oped  # noqa: E402
from oped import AssFile, ass_formatted  # noqa: E402

from aegisub_render import parse_offset, shift_time_by_frames  # noqa: E402
from aegisub_render.ass.time import clamp_time  # noqa: E402


# --- NC ---------------------------------------------------------------------------------


def shift_events(ass: AssFile, spec: str, fps: str | None, video: Path | None) -> int:
    """平移每一行，回傳實際的毫秒位移（拍點原點要用同一個數字）。"""
    off = parse_offset(spec)
    if off.by_frames:
        fr = oped.framerate_of(video, fps)
        ms_delta = 0
        for ev in ass.events:
            new = shift_time_by_frames(ev.start, off.amount, fr)
            if ms_delta == 0:
                ms_delta = new - ev.start
            ev.start = new
            ev.end = shift_time_by_frames(ev.end, off.amount, fr)
        return ms_delta
    for ev in ass.events:
        ev.start = clamp_time(ev.start + off.amount)
        ev.end = clamp_time(ev.end + off.amount)
    return off.amount


def patch_consts(ass: AssFile, shift_ms: int, consts: list[str], sets: list[str]) -> int:
    """code 行裡的常數：`--const B0` 跟著平移，`--set NAME=VALUE` 直接換值。"""
    n = 0
    for ev in ass.events:
        if not oped.is_code(ev):
            continue
        text = ev.text
        for name in consts:
            text = re.sub(
                rf"\b{re.escape(name)}\s*=\s*(-?\d+)",
                lambda m, nm=name: f"{nm}={int(m.group(1)) + shift_ms}",
                text,
            )
        for s in sets:
            name, _, value = s.partition("=")
            text = re.sub(rf"\b{re.escape(name)}\s*=\s*-?[\d.]+", f"{name}={value}", text)
        if text != ev.text:
            ev.text = text
            n += 1
    return n


def set_links(ass: AssFile, video: Path | None, title: str | None) -> None:
    if video:
        ass.properties.video_file = video.name if video.parent == Path(".") else str(video)
        ass.properties.audio_file = ass.properties.video_file
    if title is not None:
        for info in ass.info:
            if info.key == "Title":
                info.value = title
                return


def append_credit(ass: AssFile, credit: Path) -> int:
    """把另一個 .ass 的事件行（通常是曲名 credit 與它的載體行）接到後面，樣式缺的補上。"""
    src = oped.load(credit)
    have = {s.name for s in ass.styles}
    for s in src.styles:
        if s.name not in have:
            ass.styles.append(s.copy())
    for ev in src.events:
        ass.events.append(ev.copy())
    return len(src.events)


def cmd_nc(a: argparse.Namespace) -> int:
    ass = oped.load(a.target)
    out = a.out or a.target
    if a.drop_fx:
        before = len(ass.events)
        ass.events[:] = [e for e in ass.events if not oped.is_fx(e)]
        print(f"丟掉 {before - len(ass.events)} 條 fx 行")
    delta = shift_events(ass, a.shift, a.fps, a.video) if a.shift else 0
    if a.shift:
        print(f"平移 {a.shift} → {delta} ms")
    if a.const or a.set:
        n = patch_consts(ass, delta, a.const, a.set)
        print(f"改了 {n} 條 code 行的常數（{'、'.join([*a.const, *a.set])}）")
    set_links(ass, a.video, a.title)
    if a.credit:
        print(f"加上 {append_credit(ass, a.credit)} 條 credit／載體行")
    save_ui_state = True
    if a.render:
        save_ui_state = oped.apply_template(ass, out, settings=oped.settings_for(a.font_dir)).save_ui_state
    oped.save(out, ass, save_ui_state=save_ui_state)
    print(f"{out.name}: {oped.stats(ass)}")
    return 0


# --- lite -------------------------------------------------------------------------------


def cmd_lite(a: argparse.Namespace) -> int:
    ass = oped.load(a.target)
    out = a.out or a.target
    blocks = luasync.read_blocks(a.lua, a.dialect, None) if a.lua else []
    templates = build_mod.read_templates(a.templates) if a.templates else []
    if not templates:
        raise SystemExit("lite 版需要 --templates：lite 的差別就是另一張模板清單")
    used = [e.text for e in templates if not e.effect.startswith("code once")]
    once = [b for b in blocks if b.effect.startswith("code once")]
    keep = {id(b) for b in luasync.code_once(once, used)}
    pruned = [b for b in blocks if not b.effect.startswith("code once") or id(b) in keep]
    print(f"遞移裁剪：{len(once)} 塊 code once → {len(once) - (len(blocks) - len(pruned))} 塊")
    ass.events[:] = [e for e in ass.events if not oped.is_fx(e)]
    n = build_mod.rebuild(ass, pruned, templates, order=a.order, style=a.style, labels=a.labels)
    print(f"換上 {n} 條 code／template 行")
    save_ui_state = True
    if a.render:
        save_ui_state = oped.apply_template(ass, out, settings=oped.settings_for(a.font_dir)).save_ui_state
    oped.save(out, ass, save_ui_state=save_ui_state)
    print(f"{out.name}: {oped.stats(ass)}")
    return 0


# --- 繁簡 -------------------------------------------------------------------------------

LANG = re.compile(r"^(.*)([+#])(TC|SC)$")


def cmd_lang(a: argparse.Namespace) -> int:
    ass = oped.load(a.target)
    rows = [e for e in oped.events_of(ass) if not oped.is_karaoke(e) or True]
    bad = 0
    marks: dict[str, int] = {}
    for e in rows:
        m = LANG.match(e.actor)
        if m:
            marks[m.group(2) + m.group(3)] = marks.get(m.group(2) + m.group(3), 0) + 1
    print("語言標記：" + ("、".join(f"{k} × {v}" for k, v in sorted(marks.items())) or "（沒有）"))

    # 日中行一一對應：同一句的 (Start, End, Name 去掉語言標記) 必須成對
    def key(e) -> tuple[int, int, str]:
        m = LANG.match(e.actor)
        return (e.start, e.end, m.group(1) if m else e.actor)

    jp = [e for e in rows if e.style.endswith("JP")]
    ch = [e for e in rows if e.style.endswith(("CHT", "CHS", "CH"))]
    jk, ck = {key(e) for e in jp}, {key(e) for e in ch}
    for k in sorted(jk - ck):
        print(f"  只有日文行：{ass_formatted(k[0])} {k[2]}")
        bad += 1
    for k in sorted(ck - jk):
        print(f"  只有中文行：{ass_formatted(k[0])} {k[2]}")
        bad += 1
    print(f"日文 {len(jp)} 行、中文 {len(ch)} 行，配對" + ("OK" if not bad else f"有 {bad} 處對不上"))
    if bad:
        print("對不上就是字幕的資料問題，不要放寬配對規則（例如改成比對時間重疊）。")
    return 1 if bad and a.check else 0


# --- CLI --------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("target", type=Path)
        p.add_argument("-o", "--out", type=Path)
        p.add_argument("--render", action="store_true")
        p.add_argument("--font-dir", type=Path, action="append", default=[])

    p_nc = sub.add_parser("nc", help="NCOP／NCED 版")
    common(p_nc)
    p_nc.add_argument("--shift", help="[+-]影格數 或 [+-][[[hh:]mm:]ss].ms")
    p_nc.add_argument("--fps", help="影格位移用的 fps（24000/1001）")
    p_nc.add_argument("--video", type=Path, help="NC 影片（同時寫進 Video File／Audio File）")
    p_nc.add_argument("--title", help="[Script Info] 的 Title")
    p_nc.add_argument("--const", action="append", default=[], help="跟著平移的常數名（例如 B0），可重複")
    p_nc.add_argument("--set", action="append", default=[], help="直接換值的常數（OP_FINAL_SHIFT=0），可重複")
    p_nc.add_argument("--credit", type=Path, help="要接上去的 credit 行（另一個 .ass）")
    p_nc.add_argument("--drop-fx", action="store_true")

    p_lite = sub.add_parser("lite", help="lite 版")
    common(p_lite)
    p_lite.add_argument("--lua", type=Path, nargs="+", default=[])
    p_lite.add_argument("--templates", type=Path, required=True)
    p_lite.add_argument("--dialect", choices=["blank", "at", "atat"])
    p_lite.add_argument("--order", choices=["auto", "lua"], default="auto")
    p_lite.add_argument("--style", default="Default")
    p_lite.add_argument("--labels", action="store_true", help="把 Lua 的區塊標籤寫進 code 行的 Name 欄")

    p_lang = sub.add_parser("lang", help="繁簡標記與日中行配對檢查")
    p_lang.add_argument("target", type=Path)
    p_lang.add_argument("--check", action="store_true", help="有問題時以 exit 1 結束")

    a = ap.parse_args()
    return {"nc": cmd_nc, "lite": cmd_lite, "lang": cmd_lang}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
