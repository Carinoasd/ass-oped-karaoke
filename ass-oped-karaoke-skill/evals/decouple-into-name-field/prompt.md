---
tags: [ass-oped-karaoke]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

我的 OP 模板 code 區塊裡有這樣一張表，用行號索引：

```lua
SHOTS = {[1]={960,283,"&H2A80F0&"}, [2]={1500,283,"&HD85E82&"}, [3]={420,348,"&H2A80F0&"}}
function shot() local s = SHOTS[line.i] return s end
```

每次在中間插一句歌詞，後面全部錯位；而且同一句換顏色還要回頭改程式碼。要怎麼改才對？給我具體的做法。
