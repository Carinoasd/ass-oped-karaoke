"""交付前的驗證：環境、可套用、冪等、行數與同時事件數。

    python -X utf8 verify.py env                 # 環境：aegisub_render、Aegisub 安裝、ffmpeg、字型
    python -X utf8 verify.py x.ass               # 可套用 + 冪等（**交付前一定要跑**）
    python -X utf8 verify.py x.ass --stats       # 只看行數與同時事件數，不渲染
    python -X utf8 verify.py a.ass b.ass c.ass   # 一次驗好幾個

冪等＝「把套用過的結果再套用一次，結果逐位元組相同」。不相同代表模板吃到了自己上一次的輸出
（例如來源行被模板改到、或 fx 行沒有被正確地重建），那是會在下一次改稿爆開的問題。
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oped  # noqa: E402


def check_env() -> int:
    bad = 0
    import aegisub_render

    print(f"aegisub_render  {aegisub_render.__file__}")
    settings = oped.settings_for()
    root = settings.aegisub_root
    ok = (root / "automation").is_dir()
    print(f"Aegisub 安裝     {root}  {'OK' if ok else '找不到 automation/，用 --config 或 config.py 指定'}")
    bad += 0 if ok else 1
    kara = root / "automation" / "autoload" / "kara-templater.lua"
    print(f"kara-templater  {'OK' if kara.is_file() else '找不到：' + str(kara)}")
    bad += 0 if kara.is_file() else 1
    ff = shutil.which("ffmpeg")
    print(f"ffmpeg          {ff or '找不到（只有取幀／頻譜／對位需要）'}")
    try:
        import av  # noqa: F401

        print("PyAV            OK（可以讀影片時間碼）")
    except ImportError:
        print("PyAV            沒有（--fps 仍可用；要讀真影片請裝 video extra）")
    try:
        from aegisub_render import MeasureStyle, measure_text

        m = measure_text(MeasureStyle(font="Arial", fontsize=48), "Ag")
        print(f"量字            OK（Arial 'Ag' 寬 {m.width:g}）")
    except Exception as e:  # noqa: BLE001
        print(f"量字            失敗：{e}")
        bad += 1
    return bad


def verify_one(path: Path, *, font_dirs: list[Path], stats_only: bool) -> int:
    ass = oped.load(path)
    print(f"\n{path.name}: {oped.stats(ass, size=path.stat().st_size)}")
    if stats_only:
        return 0
    settings = oped.settings_for(font_dirs)
    bad = 0
    # 1) 能不能套用（validation 要過，沒有 force 這條路）；順便拿到第一次的結果
    try:
        once = oped.render_bytes(path, settings=settings)
    except SystemExit as e:
        print(f"  可套用    NO：{e}")
        return 1
    print("  可套用    OK（validation 通過）")
    # 2) 冪等：把結果寫出去再套一次
    with tempfile.TemporaryDirectory() as tmp:
        p2 = Path(tmp) / path.name
        p2.write_bytes(once)
        twice = oped.render_bytes(p2, settings=settings)
    if once == twice:
        print("  冪等      OK（重新套用逐位元組相同）")
    else:
        print(f"  冪等      NO（{len(once)} vs {len(twice)} bytes）")
        bad += 1
    # 3) 檔案裡存的結果是不是最新的
    if path.read_bytes() != once:
        print("  最新      NO：檔案裡的 fx 行和重新套用的結果不同，記得重新渲染並存檔")
        bad += 1
    else:
        print("  最新      OK（檔案裡存的就是重新套用的結果）")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", help="`env` 或要驗的 .ass")
    ap.add_argument("--stats", action="store_true", help="只看行數，不渲染")
    ap.add_argument("--font-dir", type=Path, action="append", default=[])
    a = ap.parse_args()

    if a.targets == ["env"]:
        return 1 if check_env() else 0
    bad = 0
    for t in a.targets:
        bad += verify_one(Path(t), font_dirs=a.font_dir, stats_only=a.stats)
    print("\n" + ("全部通過" if not bad else f"{bad} 項沒過"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
