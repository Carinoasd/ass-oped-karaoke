# ass-oped-karaoke

Claude Code 技能：用 Aegisub kara-templater 做動畫 OP／ED 的卡拉OK特效字幕——逐詞 `\k`、
Name 欄位與 inline fx、Lua ↔ code 行同步、套模板、驗證、取幀、NC／lite 衍生版。

| 路徑 | 內容 |
| --- | --- |
| `skills/ass-oped-karaoke/` | 技能本體（`SKILL.md`、`references/`、`scripts/`、`assets/example/`） |
| `ass-oped-karaoke-skill/` | 測試案例（`evals/`）與執行環境、跑測試的說明（`CLAUDE.md`） |

## 安裝

把 `skills/ass-oped-karaoke` 複製到 `~/.claude/skills/`，或用 Releases 裡的 `ass-oped-karaoke.skill`。

## 需要另外準備

- `python-aegisub-render`（`aegisub_render` 函式庫）。它是另一個專案，**不在這個 repo 裡**；
  裝好後以連結方式安裝，或設 `AEGISUB_RENDER_ROOT` 指過去。
- Aegisub 3.5.1、含 libass 的 ffmpeg、numpy、Pillow；讀影片時間碼要 PyAV。
- 選用：強制對位（`falign.py`）需要另一個約 1 GB 的 Python 環境，第一次使用時下載 demucs `htdemucs`
  （約 80 MB）與 torchaudio `MMS_FA`（約 1.2 GB）。兩個模型各有自己的授權，使用前請自行確認。

細節見 [ass-oped-karaoke-skill/CLAUDE.md](ass-oped-karaoke-skill/CLAUDE.md)。

## 測試方式

- 測試執行（第二至四輪，每輪 15 次）：Claude Fable 5.2（`claude-fable-5-2`）子代理，在本機 WSL 上
  有技能與沒技能各一次。第一輪在另一台機器上執行，當時沒有記錄模型。
- 評分是逐條對照判準並輔以程式檢查，不是獨立評分員；每個案例每種設定只跑一次。
- 逐詞時間的準確度是對照人工聽過的參考時點量的（參考時點不在這個 repo 裡）。

## 授權

MIT，見 [LICENSE](LICENSE)。
