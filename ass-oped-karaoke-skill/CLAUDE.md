# 這包是什麼

`/ass-oped-karaoke` 技能的**測試案例**（`evals/`）。技能本體不在這裡——它在同一個 repo 的
`skills/ass-oped-karaoke/`，這包只放測試，不重複存一份技能。

技能內容是三個做完的 OP／ED 特效專案的整合：工作流程、Name 欄位規格、Lua ↔ `code` 行的同步、
lite／NC／繁簡衍生、`\k` 時間（BPM／頻譜／音訊對位）、驗證與取幀。所有字幕與渲染相關的操作都走
`aegisub_render` 的 Python API，不呼叫 `aegisub-render.exe`、不自己解析 ASS。

兩個行為上的約定，測試時會看到：

- **預設交付範圍只有 OP／ED 的本篇完整版**（而且不一定兩首都有）。lite 版要等使用者抱怨太複雜，
  NC 版只在原始字幕本身帶著曲名 credit 時才主動做——技能不該自己把版本數量加碼。
- **沒有 force 這條路**：`ScriptRender` 不帶 `force=`，kara-templater 的 validation 不過就直接失敗。
  交付檔必須是「在 Aegisub 裡按下去就會動」的檔案。

## 安裝技能

把 repo 的 `skills/ass-oped-karaoke` 整個複製到下列任一處：

- 個人：`~/.claude/skills/ass-oped-karaoke`
- 專案：`<專案>/.claude/skills/ass-oped-karaoke`

然後在 Claude Code 裡用 `/ass-oped-karaoke`，或直接讓它被 description 觸發。

## 執行環境

| 需要 | 說明 |
| --- | --- |
| Python 3.14 | **一律 `-X utf8`／`PYTHONUTF8=1`**（開發機 locale 是 cp950，不帶旗標會炸或靜默亂碼） |
| `aegisub_render` | `python-aegisub-render` 這個 repo，以連結方式安裝：`uv add --editable <repo>`；或設環境變數 `AEGISUB_RENDER_ROOT=<repo>`（`scripts/oped.py` 會自己把它的 `src/` 加進 `sys.path`） |
| 原生模組 | repo 裡 commit 的 `.pyd` 是給 CPython 3.14 / win_amd64 用的；傳過去的壓縮檔**沒有包含**它們，所以測試機要先自己編：`uv run --group build python native/build.py`（Linux／WSL 見 repo README） |
| Aegisub 3.5.1 | 安裝目錄要有 `automation/autoload/kara-templater.lua`（預設 `C:\Program Files\Aegisub`，可用 `config.py` 或 `--config` 換） |
| ffmpeg（含 libass） | 取幀（`frames.py`）、量像素（`measure.py --ink`）、頻譜（`spec.py`）、對位（`align.py`）要用 |
| numpy | `bpm.py`／`spec.py`／`align.py` 需要 |
| Pillow | `frames.py` 拼圖與 `measure.py --ink` 需要（只取一格不拼圖時不需要） |
| PyAV | 要從真的影片讀時間碼時需要（`uv add --editable "<repo>[video]"`）；給 `--fps` 就不用。**三個真實插槽會用到影片，建議裝** |

先確認環境：

```bash
python -X utf8 <技能資料夾>/scripts/verify.py env
```

每一項都會印出 OK 或缺什麼。`量字 OK` 那一行代表 `text_extents` 的原生模組載得起來
（Windows 走 GDI，Linux 走 fontconfig/HarfBuzz）。

## 跑測試

測試案例是 `claude plugin eval` 的格式（一個案例一個資料夾：`prompt.md`、`case.yaml`、
`graders/NN-*.md`、`files/`）。CLI 是從**技能資料夾**執行的，所以先把這裡的 `evals/`
放進技能資料夾底下（複製，或在支援的系統上做連結）：

```bash
cp -r evals <技能資料夾>/evals
cd <技能資料夾>
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

它會把每個案例跑「有技能」與「沒技能」兩次，報告寫在 `evals/results/`。
**這是真的會計費的模型執行**，跑之前先確認是你要的。

| 案例 | 測什麼 | 需要什麼 |
| --- | --- | --- |
| `luasync-sync-and-render` | Lua 改了之後同步進交付檔、重新套模板、回報驗證 | Aegisub |
| `verify-before-delivery` | 認出「fx 行不是最新的」，修好再驗一次 | Aegisub |
| `nc-variant-from-episode` | NC 版：用影格平移、拍點原點跟著平移、換片源 | Aegisub |
| `burn-frames-on-nc` | 用 `frames.py --shift` 直接燒在 NC 上，不產生中間檔 | 無（只問指令） |
| `decouple-into-name-field` | 把行號索引的硬編碼表搬進 Name 欄位 | 無 |
| `ktiming-workflow` | `\k` 時間的流程：BPM → 對位（只是初稿）→ 中文行用複製的 | 無 |
| `real-slot-1` ~ `real-slot-3` | **端到端：從影片做出一首真的 kfx**（見下） | 影片＋歌詞、Aegisub、ffmpeg、numpy、Pillow |

前六個是單點測試，用 `evals/*/files/` 裡附的小範例（虛構歌詞，從技能的 `assets/example/`
複製出來的），不需要影片。

### 三個真實素材插槽

`real-slot-1` ~ `real-slot-3` 是留給真實 OP／ED 的**端到端**案例：從影片一路做到可以交的 kfx
（看畫面決定設計 → 抓逐詞時間 → 組裝渲染 → 驗證 → 燒字截圖）。
**這三個案例需要影片**：設計要對得上原片、逐詞時間要對得上音訊、截圖要燒在畫面上，
這三件事沒有影片就測不出來。

每個插槽的 `files/README.md` 寫了要放什麼（影片、歌詞 `.ass`、參考畫面、字型），
放完之後把 `prompt.md`、`case.yaml`、`graders/*.md` 裡的 `<填入…>` 換成真正的題目與判準。

影片**不要**跟著進版控或壓縮檔；這包裡那三個 `files/` 只有說明檔。
沒填之前這三個案例會失敗，所以平常跑測試要排除它們——它們多帶了 `real` 與 `manual` 兩個 tag：

```bash
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold --tags ass-oped-karaoke --exclude-tags real
```

（旗標名稱以你這版 CLI 的 `claude plugin eval --help` 為準；也可以直接把那三個資料夾移走再跑。）

### 小案例的測試資料

技能的 `assets/example/` 是一個能真的跑的最小範例（歌詞是自己編的，不是任何作品的）：

```bash
cd <技能資料夾>/assets/example
python -X utf8 ../../scripts/build.py demo_op.ass --lua demo.lua --templates templates_demo.txt --prune --render
python -X utf8 ../../scripts/verify.py demo_op.ass
```

### 一件要注意的事

`demo_op.built.ass` 與 `demo_op.stale.ass` 裡的 fx 行是**在 Windows 上用 GDI 的字型度量**算出來的。
`verify.py` 的「最新」那一項會重新套用模板再比對，所以：

- 在 **Windows** 上跑：`built` 三項全過、`stale` 只有「最新」不過——這就是案例預期的結果。
- 在 **Linux／WSL** 上跑：量字方式不同（fontconfig/HarfBuzz），座標會差一點，
  兩個檔都會是「最新 NO」。要在 Linux 上測就先重新產生 fixture：

  ```bash
  cd <技能資料夾>/assets/example
  cp demo_op.ass demo_op.built.ass
  python -X utf8 ../../scripts/build.py demo_op.built.ass --lua demo.lua --templates templates_demo.txt --prune --render
  # stale：把 built 的 code 行裡 DEMO_POP = 120 改成 150，不要重新渲染
  ```

  然後把兩個檔複製回對應案例的 `files/`。

範例用的字型是 Arial（歌詞雖然是日文，但測試只在乎「輸出是不是一致」，不在乎好不好看），
所以不需要特別安裝 CJK 字型。真實插槽就不一樣：那首歌要用的字型得真的裝起來，或用 `--font-dir` 指過去。

## 已經驗證過的事（在開發機上）

這些不是自動化測試，是作者拿三個真實專案的交付檔跑過的結果，列在這裡當回歸基準：

- `luasync.py`：三種分段方言（`blank`／`at`／`atat`）壓出來的 code 行，與三個專案交付檔裡的
  code／template 行**逐字相同**；遞移裁剪的結果（110 塊）與原專案用自己的腳本裁出來的**完全一致**。
- `ktime.py`：四個真實交付檔 `extract → apply` 之後**一個位元組都沒變**；
  `segk` 在 24000/1001 的專案裡看到的 905 個 `\k` 全是 `\k42`（符合 `round(1000/fps)`）。
- `build.py`：把某專案的 Lua 重新同步進交付檔並重新套用模板之後，**整個檔與原本逐位元組相同**。
- `verify.py`：真實交付檔三項全過（1382 條 fx 行、同時最多 127 個事件）。
- `frames.py`：把本篇時間軸的交付檔以 `--shift -1678 --fps 24000/1001` 燒在 NCOP 上取兩格拼圖，
  畫面與原專案的 `nc_shot.sh` 相同。
