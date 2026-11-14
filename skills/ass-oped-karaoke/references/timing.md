# `\k` 逐詞時間

卡拉OK特效的品質有一半在時間。三條路，按可靠度排序：**耳朵 > 拍點 > 音訊對位**。
對位器只能產生初稿，確認過的詞要 pin 住，不然下一次重跑又被改掉。

## 來源行長什麼樣

```
Comment: 0,0:01:40.12,0:01:43.00,OPJP,OP market down,0,0,0,karaoke,{\k0}{\k74}ドル円ショート！　{\k68}ドル円ショート！
```

- 每個詞（或每個字）前面一個 `{\k…}`。半形空白併到前一個音節。
- 不打算真的做逐字變色時，`\k` 只是切段用的，但**不能沒有**
  （見 `pitfalls.md`：沒有 `\k` 的行只有一個長度 0 的音節）。
  這種「只分段、不切軸」的 `\k`，**數值取一幀的毫秒數四捨五入到整數**，也就是 `round(1000/fps)`：

  | fps | `\k` | fps | `\k` |
  | --- | --- | --- | --- |
  | 24000/1001、24 | `\k42` | 30000/1001、30 | `\k33` |
  | 25 | `\k40` | 50 | `\k20` |
  | 60000/1001、60 | `\k17` | 其他 | `round(1000/fps)` |

  所以逐字切段是 `{\k42\-n}字`（24000/1001）或 `{\k33\-n}字`（30000/1001）。
  **整首用同一個值**，換片源幀率時整份跟著換；看到一份檔裡混著 42 和 33，就是有人複製貼上忘了改。
- ED 的全形空白常常要自成一個零長度音節（`{\k0}　`），否則 `noblank` 的判斷和分詞會打架。

讀寫用 API，不要自己寫正規式：

```python
from aegisub_render.ass.karaoke import parse_karaoke_syllables
for syl in parse_karaoke_syllables(line):
    syl.start_time, syl.duration, syl.text
```

`scripts/ktime.py` 就是它的 CLI：

```bash
python -X utf8 scripts/ktime.py extract x.ass                 # 每行每詞的起點（cs，距行首）
python -X utf8 scripts/ktime.py extract x.ass --json t.json   # 存成表，手改數字
python -X utf8 scripts/ktime.py apply   x.ass --json t.json   # 寫回（只動 \k 的長度，不動文字與 inline fx）
python -X utf8 scripts/ktime.py shift   x.ass --line 0:01:40.12 --word 2 +30
```

## 拍點（BPM / B0）

歌詞的詞通常落在 1/4 拍的格點上。先把拍子量出來：

```bash
python -X utf8 scripts/bpm.py ep01.mp4 --start 183.975 --duration 90
# BPM=158.98   first beat 184.010s   ->   B0=184010
```

兩段式：先用頻譜起音的自相關抓粗略 tempo（連同 2×／4× 倍數一起加總，避免抓成半速），
再在它附近做 tempo×相位的細搜尋，讓起音正好落在格線上。回報的「拍點強度」低於平均的 2 倍
就是沒對上，不要硬用。

`B0` 是**本篇時間軸上第一拍的絕對毫秒**，寫進 Lua 當常數；NC 版要跟著平移（見 `variants.md`）。

有了格點之後，用眼睛對：

```bash
python -X utf8 scripts/spec.py ep01.mp4 229.5 234.2 out.png --bpm 158.98 --b0 184.010
```

頻譜圖上方紅色是拍線、下方藍色是 0.1 秒刻度，起音的亮柱對得上哪一條一眼就看得出來。

## 音訊對位器

`scripts/align.py` 做的事：

1. 從影片切出該段立體聲音訊（快取在 `--cache`），只取「置中聲像 × 有音高（HPSS 諧波）」的人聲成分；
2. 證據 ＝ 人聲頻帶的起音強度 ＋ 旋律音高變化（4096 點 chroma 的前後相似度）；
3. 歌詞拆成假名音拍（漢字查 `--readings` 給的讀音表），用 Viterbi 放到 1/4 拍格點上，
   評分 ＝ 證據 ＋ 節奏先驗（詞內偏八分／十六分，詞間可休止）＋ 目前時間的位置先驗（寬鬆）；
   「ー」不需要起音、且它所屬的音節偏好落在 ≥1 拍的長音上，「ん／っ」只弱要求起音；
4. 同一句型重複出現 ≥3 次且在行內位置相同時，先用互相關把各次對齊（並要求小節內位置一致），
   平均證據之後只解一次節奏，再套回每一次——重複樂句的對位因此穩定得多；
5. `--pin` 列出的詞固定不動，其餘詞排在它們之間。

```bash
python -X utf8 scripts/align.py x.ass --video ep01.mp4 --part OP \
    --grid 88659:162.96 --report                      # 只報告：每個詞 目前 → 對位結果（以拍為單位）
python -X utf8 scripts/align.py x.ass --video ep01.mp4 --part OP \
    --grid 88659:162.96 --write --only 0:22:39.17     # 把指定行的結果寫回 .ass 的 \k
```

**一定要 `--only`**：不指定行就整首重寫，已經用耳朵確認過的詞也會被動到。
聽起來不對的詞直接改數字（`ktime.py apply`）或在 Aegisub 調，確認過的加進 `--pin`。

漢字讀音表是作品自己的東西（`{"兌換": "だかん", "追証": "おいしょう"}`），放作品資料夾的 JSON，
不要塞進 skill。中文行不做對位：**中文行的 `\k` 從日文行複製過來**（同一句、同樣的分詞數），
這也是「日中行一一對應」這條規矩的來源。

## 常見錯誤

- **忘記把中文行的 `\k` 一起更新**：lite 版、繁簡版都是另一個檔，改完 `\k` 要複製過去。
  `build.py --keep-timing` 會保留現有的 `\k`，所以日常重建不會洗掉手調的時間。
- **行的起點被捨到 10ms 之後，行內 `\t` 的相對時間跟著差幾 ms**。時間一律用 `ass_formatted()`。
- **把對位器的輸出當成定稿**。它對起音清楚的日文很準，對長音、氣音、和聲重疊的段落會錯半拍。
- **換集數時整份重跑對位**。歌詞與逐詞時間不變，換集數只要平移（`macro offset`／`variants.py nc`）。
