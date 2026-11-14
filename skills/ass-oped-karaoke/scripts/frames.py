"""取幀：把字幕用 libass 燒在影片上，取出指定的幾格，拼成一張對照圖。

    # 指定時間點（秒或 h:mm:ss.cc），拼成 2 欄
    python -X utf8 frames.py out.png --ass x.ass -t 194.6 195.32 --cols 2

    # 指定影格編號（用影片真正的時間碼換算，VFR 也正確）
    python -X utf8 frames.py out.png --ass x.ass --frame 1678 1700 1722

    # 連續張：從 15.0 秒起 3 秒、每秒 4 張
    python -X utf8 frames.py sheet.png --ass x.ass --sheet 15.0 3 4 --cols 4

    # 本篇時間軸的交付檔，直接燒在 NC 影片上看（不必先做 NC 版）
    python -X utf8 frames.py shot.png --ass op_kfx.ass --video ncop.mp4 --shift -1678 --fps 24000/1001 -t 15 59

    # 只看畫面不燒字（量原片的 staff 字幕、找設計依據時）
    python -X utf8 frames.py ref.png --video ep01.mp4 -t 0:03:55.693 --crop 280:260:420:560

影片預設取字幕檔連結的 Video File（和 Aegisub 一樣相對於字幕檔解析），可用 `--video` 覆蓋。
`--shift` 的語法同 `aegisub-render macro offset`：`[+-]影格數`（要 `--fps` 或能讀時間碼的影片）
或 `[+-][[[hh:]mm:]ss].ms`；平移在記憶體裡做，不會動到你的檔案。

幾個 ffmpeg 的坑（都已經處理掉，改這支之前先看）：`subtitles=` 的 filtergraph 會把磁碟機代號的
冒號當參數分隔，中文與方括號也會出事 → 字幕一律複製到暫存資料夾用純 ASCII 檔名、以 cwd 切進去跑；
`-ss` 之後要 `-copyts`，濾鏡才看得到真正的時間。
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oped  # noqa: E402

from aegisub_render import parse_offset, shift_time_by_frames  # noqa: E402
from aegisub_render.ass.time import clamp_time  # noqa: E402


def seconds(spec: str) -> float:
    """`194.6`、`3:14.5`、`0:03:55.693` 都接受。"""
    return sum(float(x) * 60**i for i, x in enumerate(reversed(spec.split(":"))))


def prepare_ass(ass_path: Path, shift: str | None, fps: str | None, video: Path | None, dest: Path) -> None:
    """把字幕（必要時先平移）寫到暫存資料夾的純 ASCII 檔名。"""
    ass = oped.load(ass_path)
    if shift:
        off = parse_offset(shift)
        if off.by_frames:
            fr = oped.framerate_of(video, fps)
            for ev in ass.events:
                ev.start = shift_time_by_frames(ev.start, off.amount, fr)
                ev.end = shift_time_by_frames(ev.end, off.amount, fr)
        else:
            for ev in ass.events:
                ev.start = clamp_time(ev.start + off.amount)
                ev.end = clamp_time(ev.end + off.amount)
        shown = [ev for ev in ass.events if not ev.comment]
        if shown and all(ev.end <= 0 for ev in shown):
            raise SystemExit(
                f"{ass_path.name}: 平移 {shift} 之後所有字幕都落在 0 秒之前，畫面上不會有任何字。\n"
                "位移的方向或數值不對，或這份字幕不在你以為的那條時間軸上。"
            )
    dest.write_bytes(ass.serialize())


def grab(video: Path, times: list[float], work: Path, *, sub: str | None, crop: str | None, scale: float) -> list[Path]:
    out: list[Path] = []
    for i, t in enumerate(times):
        name = f"f{i:03d}.png"
        vf = []
        if sub:
            vf.append(f"subtitles={sub}")
        if crop:
            x, y, w, h = crop.split(":")
            vf.append(f"crop={w}:{h}:{x}:{y}")
        if scale != 1:
            vf.append(f"scale=iw*{scale}:-1")
        cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", f"{t:.3f}", "-copyts", "-i", str(video)]
        if vf:
            cmd += ["-vf", ",".join(vf)]
        cmd += ["-frames:v", "1", name]
        subprocess.run(cmd, check=True, cwd=work)
        out.append(work / name)
    return out


def tile(images: list[Path], out: Path, cols: int, labels: list[str]) -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if len(images) == 1:
            shutil.copyfile(images[0], out)
            return
        raise SystemExit("拼圖需要 Pillow（pip install pillow）；一次只取一格則不需要") from None
    ims = []
    for p, label in zip(images, labels):
        im = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 8 * len(label) + 8, 18], fill=(0, 0, 0))
        d.text((4, 3), label, fill=(255, 255, 0))
        ims.append(im)
    cols = max(1, min(cols, len(ims)))
    rows = (len(ims) + cols - 1) // cols
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * cols, h * rows))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", type=Path)
    ap.add_argument("--ass", type=Path, help="要燒上去的字幕（省略＝只取畫面）")
    ap.add_argument("--video", type=Path, help="影片（省略＝字幕連結的 Video File）")
    ap.add_argument("-t", "--times", nargs="+", default=[], help="時間點（秒或 h:mm:ss.cc）")
    ap.add_argument("--frame", nargs="+", type=int, default=[], help="影格編號（用影片時間碼換算）")
    ap.add_argument("--sheet", nargs=3, metavar=("START", "DUR", "FPS"), help="連續張：起點、長度(秒)、每秒張數")
    ap.add_argument("--shift", help="先平移字幕：[+-]影格數 或 [+-][[[hh:]mm:]ss].ms")
    ap.add_argument("--fps", help="影格換算用的 fps（24000/1001）")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--crop", help="x:y:w:h")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--font-dir", type=Path, help="額外字型目錄（libass 用）")
    a = ap.parse_args()

    video = a.video
    if video is None:
        if not a.ass:
            ap.error("需要 --video 或 --ass（從字幕的 Video File 取）")
        video = oped.video_of(oped.load(a.ass), a.ass)
        if video is None:
            ap.error("字幕裡沒有可用的 Video File，請用 --video")
    if not video.exists():
        ap.error(f"找不到影片：{video}")

    times: list[float] = [seconds(t) for t in a.times]
    labels: list[str] = [f"{t:.3f}s" for t in times]
    if a.frame:
        fr = oped.framerate_of(video, a.fps)
        for n in a.frame:
            ms = fr.time_at_frame(n, "start")
            times.append(ms / 1000)
            labels.append(f"#{n} {ms / 1000:.3f}s")
    if a.sheet:
        start, dur, fps = seconds(a.sheet[0]), float(a.sheet[1]), float(a.sheet[2])
        n = max(1, round(dur * fps))
        for i in range(n):
            t = start + i / fps
            times.append(t)
            labels.append(f"{t:.3f}s")
    if not times:
        ap.error("需要 -t／--frame／--sheet 其中之一")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        sub = None
        if a.ass:
            prepare_ass(a.ass, a.shift, a.fps, video, work / "s.ass")
            sub = "s.ass"
            if a.font_dir:
                sub += ":fontsdir=" + str(a.font_dir.resolve()).replace("\\", "/").replace(":", r"\:")
        images = grab(video.resolve(), times, work, sub=sub, crop=a.crop, scale=a.scale)
        tile(images, a.out.resolve(), a.cols, labels)
    print(f"寫出 {a.out}（{len(times)} 格）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
