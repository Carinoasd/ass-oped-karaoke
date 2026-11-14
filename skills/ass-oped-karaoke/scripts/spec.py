"""畫一段的頻譜圖，疊上拍點格線與時間尺——用眼睛對 `{\\k}` 的時候看這個。

    python -X utf8 spec.py ep01.mp4 229.5 234.2 out.png --bpm 158.98 --b0 184.010
    python -X utf8 spec.py ep01.mp4 229.5 234.2 out.png --mark 229.8 230.4 231.0   # 疊上目前的詞起點

上方紅色是拍線（`--bpm` / `--b0`，`b0` 是第一拍的絕對秒數），下方藍色是 0.1 秒刻度、每 0.5 秒標字，
綠色是 `--mark` 給的時間點。只畫到 4 kHz，人聲就在那裡。

需要 numpy、Pillow 與 ffmpeg。
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio as audio_mod  # noqa: E402

SR = 16000


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("start", type=float)
    ap.add_argument("end", type=float)
    ap.add_argument("out", type=Path)
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--b0", type=float, default=0, help="第一拍的絕對秒數")
    ap.add_argument("--mark", nargs="*", type=float, default=[], help="額外標出來的時間點（秒）")
    ap.add_argument("--height", type=int, default=512)
    a = ap.parse_args()

    import numpy as np
    from PIL import Image, ImageDraw

    x = audio_mod.pcm_mono(a.video, a.start, a.end - a.start, SR)
    hop, n = 40, 1024
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
    spec = np.abs(np.fft.rfft(frames, axis=1))[:, :256]
    lg = np.log1p(30 * spec).T[::-1]
    lg = np.clip((lg - lg.min()) / (np.percentile(lg, 99.5) - lg.min() + 1e-9), 0, 1)

    img = Image.fromarray((255 * (1 - lg)).astype(np.uint8)).convert("RGB")
    img = img.resize((img.width, a.height))
    d = ImageDraw.Draw(img)
    pps = SR / hop  # 每秒幾個像素

    if a.bpm:
        per = 60 / a.bpm
        k = int(np.ceil((a.start - a.b0) / per))
        while a.b0 + k * per < a.end:
            tx = (a.b0 + k * per - a.start) * pps
            d.line([(tx, 0), (tx, 20)], fill=(255, 0, 0), width=2)
            k += 1
    for m in a.mark:
        if a.start <= m <= a.end:
            tx = (m - a.start) * pps
            d.line([(tx, 0), (tx, a.height)], fill=(0, 170, 0), width=1)

    t = np.ceil(a.start * 10) / 10
    while t < a.end:
        tx = (t - a.start) * pps
        big = abs(t * 2 - round(t * 2)) < 1e-6
        d.line([(tx, a.height - (42 if big else 12)), (tx, a.height)], fill=(0, 0, 255), width=1)
        if big:
            d.text((tx + 2, a.height - 42), f"{t:.1f}", fill=(0, 0, 255))
        t = round(t + 0.1, 1)

    img.save(a.out)
    print(f"寫出 {a.out}（{img.width}x{img.height}，{pps:.0f} px/s）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
