---
tags: [ass-oped-karaoke, real, manual]
max_turns: 80
timeout_seconds: 5400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

幫我做《關於我在無意間被隔壁的天使變成廢柴這件事》第一季 OP「ギフト」的卡拉OK特效字幕。

- 影片：`otonari-no-tenshisama_op_ncop_bdrip.mkv`（NCOP，1920x1080、24000/1001，有聲音）。字幕的時間就是對這支 NCOP 的
- 歌詞：`otonari-no-tenshisama_op_ncop_bdrip.ass`，日文行與中文行一一對應，行的時間已經對好了，逐詞 `\k` 還沒抓。
  現在的歌詞行只是普通的 Dialogue（淡入淡出加模糊），檔案裡另外有排好的標題字和曲名 credit
- `S01OP.mp4` 是帶 staff 字幕的 OP 本篇版，**只用來確認 staff 文字的風格**，不要拿它當底片、也不用另外做一份對它時間軸的版本
- 字型沿用檔案裡的設定

先看影片決定設計（配色、字型、進退場節奏要跟原片對得上），再把逐詞時間抓出來，
最後給我可以直接交的檔案，附上驗證結果與幾張燒在影片上的截圖。

Input files: otonari-no-tenshisama_op_ncop_bdrip.mkv, otonari-no-tenshisama_op_ncop_bdrip.ass, S01OP.mp4
