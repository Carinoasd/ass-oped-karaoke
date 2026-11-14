# 範例專案（歌詞是自己編的，不是任何作品的）

一個**能真的跑**的最小骨架，用來試工具、也用來示範「資料放欄位、程式碼不認得歌詞」長什麼樣子。

| 檔案 | 內容 |
| --- | --- |
| `demo_op.ass` | 骨架：兩個樣式、四條卡拉OK來源行（日文／中文各兩句），還沒有 code／template 行 |
| `demo.lua` | 特效原始碼（`blank` 方言：空行分塊、`--@ 標籤`） |
| `templates_demo.txt` | 完整版的模板清單（光暈層＋本體層＋fxgroup 開關） |
| `templates_demo_lite.txt` | lite 版的模板清單（只有本體層；同一份 Lua，遞移裁剪） |
| `demo_op.built.ass` | 上面那些組起來並套用模板之後的樣子（驗證全過） |
| `demo_op.stale.ass` | 同上，但 code 行改過卻沒有重新渲染——`verify.py` 會說「最新 NO」 |

```bash
python -X utf8 ../../scripts/build.py demo_op.ass --lua demo.lua --templates templates_demo.txt --prune --render
python -X utf8 ../../scripts/verify.py demo_op.ass
python -X utf8 ../../scripts/variants.py lite demo_op.ass -o demo_op_lite.ass \
    --lua demo.lua --templates templates_demo_lite.txt --render
```

這個範例示範的三件事：

- **`top` 旗標**寫在 Name 欄位，位置由 `meta.res_y - line.middle` 鏡像**推算**出來，不手寫 y；
- **`\-hi` inline fx** 決定哪個詞換色，模板完全不看歌詞的文字；
- **`plain` 旗標**關掉 `fxgroup.glow`，整個光暈層就不產生——這是控制行數最有效的手段。
