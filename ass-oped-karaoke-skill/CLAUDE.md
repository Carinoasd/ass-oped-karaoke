# 這包是什麼

`/ass-oped-karaoke` 技能的**測試案例**（`evals/`）。技能本體不在這裡——它在同一個 repo 的
`skills/ass-oped-karaoke/`，這包只放測試，不重複存一份技能。

技能內容是三個做完的 OP／ED 特效專案的整合：工作流程、Name 欄位規格、Lua ↔ `code` 行的同步、
lite／NC／繁簡衍生、`\k` 時間（BPM／強制對位／頻譜／音訊對位）、驗證與取幀。所有字幕與渲染相關的操作都走
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
| `aegisub_render` | `python-aegisub-render`（另一個專案，不在這個 repo 裡），以連結方式安裝：`uv add --editable <repo>`；或設環境變數 `AEGISUB_RENDER_ROOT=<repo>`（`scripts/oped.py` 會自己把它的 `src/` 加進 `sys.path`） |
| 原生模組 | `python-aegisub-render` 裡 commit 的 `.pyd` 是給 CPython 3.14 / win_amd64 用的；傳過去的壓縮檔**沒有包含**它們，所以測試機要先自己編：`uv run --group build python native/build.py`（Linux／WSL 見該專案的 README） |
| Aegisub 3.5.1 | 安裝目錄要有 `automation/autoload/kara-templater.lua`（預設 `C:\Program Files\Aegisub`，可用 `config.py` 或 `--config` 換） |
| ffmpeg（含 libass） | 取幀（`frames.py`）、量像素（`measure.py --ink`）、頻譜（`spec.py`）、對位（`align.py`／`falign.py`）要用 |
| numpy | `bpm.py`／`spec.py`／`align.py` 需要 |
| Pillow | `frames.py` 拼圖與 `measure.py --ink` 需要（只取一格不拼圖時不需要） |
| PyAV | 要從真的影片讀時間碼時需要（`uv add --editable "<repo>[video]"`）；給 `--fps` 就不用。**三個真實插槽會用到影片，建議裝** |
| 強制對位環境（選用） | `falign.py` 用的另一個 Python 環境（torch 2.5.1 CPU、torchaudio、demucs、soundfile），`falign.py setup` 用 uv 建在 `~/.cache/ass-oped-karaoke/fa-venv`（約 1 GB），第一次 `run` 再下載約 1.3 GB 的模型。沒有它技能退回 `align.py`＋頻譜目視；技能會先問使用者才裝，所以要測「強制對位」那條路就先在測試機建好 |

先確認環境：

```bash
python -X utf8 <技能資料夾>/scripts/verify.py env
```

每一項都會印出 OK 或缺什麼。`量字 OK` 那一行代表 `text_extents` 的原生模組載得起來
（Windows 走 GDI，Linux 走 fontconfig/HarfBuzz）。

## 跑測試

測試案例是 `claude plugin eval` 的格式（一個案例一個資料夾：`prompt.md`、`case.yaml`、
`graders/NN-*.md`、`files/`）。有兩種跑法，案例本身都一樣。
**兩種都是真的會計費的模型執行**，跑之前先確認是你要的。

### 用 `claude plugin eval`

前提是 CLI 的沙箱後端能用：Linux 要裝 bubblewrap 與 socat。
**WSL 上目前跑不起來**：裝好之後沙箱裡的 shell 對工作目錄仍是唯讀，也讀不到 `~/.local` 底下
uv 管理的 Python，每個案例都卡在環境。這種機器改用下面的子代理流程。

CLI 是從**技能資料夾**執行的，所以先把這裡的 `evals/` 放進技能資料夾底下（複製，或在支援的系統上做連結）：

```bash
cp -r evals <技能資料夾>/evals
cd <技能資料夾>
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

它會把每個案例跑「有技能」與「沒技能」兩組，預設每案跑 3 次（`--runs` 可改），報告寫在 `evals/results/`。
從 Claude Code session 裡啟動時，報告預設不發佈。

### 用子代理流程（skill-creator）

目前三輪測試都是這樣跑的。每個案例各開一個子代理、在本機環境執行，有技能與沒技能各一次
（真實插槽只跑有技能那一組）。工作區在 `~/ass/ass-oped-karaoke-workspace/iteration-N/`，
由 `~/ass/_local/work/setup_iter.py <N>` 建立：每個案例一個資料夾，底下 `with_skill/`、`without_skill/`
各有 `TASK.md`（環境說明＋`prompt.md` 的題目）、`work/`（`files/` 複製進來）、`outputs/`
（子代理寫回 `response.md` 與 `commands.md`），另有 `eval_metadata.json` 收錄判準。

- 有沒有技能的對照**靠子代理的指示**，不是工具強制的：有技能的 `TASK.md` 給技能路徑、要它先讀 `SKILL.md`；
  沒技能的禁止讀 `skills/` 與這包 `ass-oped-karaoke-skill/`。
- 評分是人工對照 `graders/`，再加程式檢查產出的檔案（驗證結果、時間、常數值等）。

### 案例

| 案例 | 測什麼 | 判準 | 附檔 | 需要什麼 |
| --- | --- | --- | --- | --- |
| `luasync-sync-and-render` | Lua 改了之後同步進交付檔、重新套模板、回報驗證 | 4 | `demo_op.built.ass`、`demo.lua`、`templates_demo.txt` | Aegisub |
| `verify-before-delivery` | 認出「fx 行不是最新的」與 Lua 和檔內 code 行不一致，兩邊弄成一致、修好再驗一次，不擅改別的 | 6 | `demo_op_kfx.ass`、`demo.lua`、`templates_demo.txt` | Aegisub |
| `nc-variant-from-episode` | 本篇時間軸的範例做 NC 版：用影格平移、拍點原點跟著平移、換片源 | 4 | `demo_op.built.ass`（本篇時間軸） | Aegisub |
| `burn-frames-on-nc` | 本篇時間軸的範例用 `frames.py --shift` 直接燒在 NC 上，不產生中間檔 | 2 | `demo_op.built.ass`（本篇時間軸） | 無（只問指令） |
| `decouple-into-name-field` | 把行號索引的硬編碼表搬進 Name 欄位 | 3 | 無 | 無 |
| `ktiming-workflow` | `\k` 時間的流程：強制對位或 BPM＋對位器出初稿、逐句對頻譜確認；哪些行需要 `\k`；中文行不另外對位 | 3 | 無 | 無 |
| `real-slot-1` ~ `real-slot-3` | **端到端：從影片做出一首真的 kfx**（見下） | 各 8 | 只有 `README.md` | 影片＋歌詞、Aegisub、ffmpeg、numpy、Pillow |

前六個是單點測試，不需要影片；有附檔的四題用的是虛構歌詞的小範例（從技能的 `assets/example/`
複製出來的）。

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

`demo_op.built.ass` 與 `demo_op.stale.ass` 裡的 fx 行是**在 Linux（WSL，fontconfig/HarfBuzz）上**算出來的。
那台機器沒有 Arial，量字退到 Liberation Sans；兩者字寬相容，用 `--font-dir` 指到 Arial 重算也逐位元組相同。
`verify.py` 的「最新」那一項會重新套用模板再比對，所以：

- 在 **Linux／WSL** 上跑：`built` 三項全過；`stale` 在有 Arial（`--font-dir`）時只有「最新」NO，
  沒有 Arial 時「最新」是無法判定（exit 2）——前者才是案例預期的結果。
- 在 **Windows** 上跑：GDI 量字（中日文字連結到別的字型），座標不同，兩個檔都會是「最新 NO」。
  要在 Windows 上測就先在那台機器重新產生（evals 那四份用 Noto CJK 的也一樣）：

  ```bash
  cd <技能資料夾>/assets/example
  cp demo_op.ass demo_op.built.ass
  python -X utf8 ../../scripts/build.py demo_op.built.ass --lua demo.lua --templates templates_demo.txt --prune --render
  # stale：把 built 的 code 行裡 DEMO_POP = 120 改成 150，不要重新渲染
  # （用一份 DEMO_POP = 150 的 demo.lua 跑 luasync.py apply 寫回，不要手改 .ass）
  ```

  evals 的四份是同一套做法，但先把 `demo_op.ass` 兩個樣式的字型換成 Noto Sans CJK JP／TC 再 build。
  然後把兩個檔複製回對應案例的 `files/`（`verify-before-delivery` 用的是 stale 那份，檔名改成
  `demo_op_kfx.ass`，旁邊另放 `DEMO_POP = 120` 的 `demo.lua`——這一題同時考「Lua 與檔內不一致」）。
  `luasync-sync-and-render` 用 built 那份，旁邊放 `DEMO_POP = 135` 的 `demo.lua`；兩題都附新版 `templates_demo.txt`。

  `nc-variant-from-episode` 與 `burn-frames-on-nc` 的 `demo_op.built.ass` 是**本篇時間軸**的版本
  （歌詞在 1:10.97 起、`DEMO_B0 = 70987`），做法是 built 之後再往後移 1678 格：

  ```bash
  python -X utf8 ../../scripts/variants.py nc demo_op.built.ass --shift +1678 --fps 24000/1001 \
      --const DEMO_B0 --drop-fx --render
  ```

範例用的字型是 Arial（歌詞雖然是日文，但測試只在乎「輸出是不是一致」，不在乎好不好看），
所以不需要特別安裝 CJK 字型。
**例外是 `evals/*/files/` 裡的四份範例字幕**：它們的樣式改用 Noto Sans CJK JP／TC。Arial 沒有日文與中文字，
在 Linux 上量字拿到的是缺字方框的寬度、libass 燒字卻退到別的字型，詞會互相重疊；執行者會花時間處理這件
與題目無關的事，沒技能的執行甚至會因此去換字型。跑這四題的機器要裝 Noto CJK（`fonts-noto-cjk`）。真實插槽就不一樣：那首歌要用的字型得真的裝起來，或用 `--font-dir` 指過去。

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
