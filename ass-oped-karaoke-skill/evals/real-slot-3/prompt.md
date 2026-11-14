---
tags: [ass-oped-karaoke, real, manual]
max_turns: 80
timeout_seconds: 5400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

幫我做《學生會也有洞！》（生徒会にも穴はある！）OP 的卡拉OK特效字幕。

- 影片：`nama-anaru_op_op.mp4`（1920x1080、24000/1001，有聲音；是帶 staff 字幕的 OP 本篇版，不是 NCOP）
- 歌詞：`nama-anaru_op_op.ass`，日文行與中文行一一對應，行的時間已經對好了，逐詞 `\k` 還沒抓。
  檔案裡現在有一套很陽春的現成模板（左到右擦出來）和它產生的 fx 行，可以整套換掉
- 檔案裡 `片頭曲` 和 `「在風中只能奔跑了！」` 那兩行請忽略：不用幫它們做特效，也不要因為它們去做 NC 版
- 字型沿用檔案裡的 Noto Sans CJK（系統已經裝了），開頭那幾行標題字（`學生會也有洞！`）維持原樣

先看影片決定設計（配色、字型、進退場節奏要跟原片對得上），再把逐詞時間抓出來，
最後給我可以直接交的檔案，附上驗證結果與幾張燒在影片上的截圖。

Input files: nama-anaru_op_op.mp4, nama-anaru_op_op.ass
