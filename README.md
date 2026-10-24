# mannypro-to-ebook

把《曼報 Pro》（[pro.manny-li.com](https://pro.manny-li.com)）的會員文章備份成本機 Markdown，再合併成一本可以放進 Kobo（或任何 EPUB 閱讀器）的電子書。這是一個 [Claude Code](https://claude.com/claude-code) skill，裝好之後用中文跟 AI 說一句話就能做完。

每篇文章一個章節、目錄可以直接跳章、文字可以調字級、可以畫線做筆記，文章裡的圖表和圖說都內嵌在書裡，離線也看得到。

> [!IMPORTANT]
> **你需要自己有《曼報 Pro》的付費會員帳號。**
>
> 這個工具透過 [mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp) 用**你自己的帳號**讀取文章，不會繞過付費牆，也不附帶任何帳號或文章。
>
> **做出來的電子書只供你個人閱讀，請不要轉載或散布付費內容。**
>
> 還不是會員？**[訂閱《曼報 Pro》](https://pro.manny-li.com/join)**，支持作者持續產出深度內容。
>
> 這是個人製作的**非官方工具**，與《曼報 Pro》、Manny Li、Firstory 沒有任何關係。

*English: a Claude Code skill that archives your own Manny Pro subscription articles as Markdown and bundles them into a reflowable EPUB / Kobo KEPUB, one chapter per article. Requires your own paid account and [mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp). For personal reading only.*

## 使用範例

裝好之後，在 Claude Code 裡直接說：

**範例一：第一次全部備份**——「把曼報全部文章存下來，做成可以放 Kobo 的檔案」

AI 會先列出網站全部文章，分批抓下來（一百多篇大約十分鐘，大多是在等圖片下載），整理檔名，再打包成兩個檔案：

```
曼報/
├── articles/
│   ├── 20250929 落槌之前 Ⅰ：解碼拍賣行的商業模式.md
│   ├── 20250929 落槌之前 Ⅱ：藝術投資的表與裡.md
│   ├── ...
│   ├── 20261013 2026 年 9 月你問我答.md
│   └── assets/<文章 slug>/...                       ← 每篇文章的圖片
├── 曼報Pro合輯 20250929-20261013.epub               ← 標準 EPUB 3，一般閱讀器用
└── 曼報Pro合輯 20250929-20261013 for kobo.kepub.epub  ← Kobo 用這個
```

**範例二：之後有新文章**——「曼報有新文章了，更新到最新再重做一本」

AI 會比對本機已有的文章和網站清單，只抓缺的那幾篇，然後重新打包整本（一分鐘內）。檔名的日期範圍會自動變成新的。

**範例三：只要一部分**——「只要 2026 年 9 月以後的文章做成一本 EPUB」

把 `.kepub.epub` 檔用 USB 線拖進 Kobo 的根目錄，退出後 Kobo 會自己建立書目。

---

## 第 0 步：先裝好 mannypro-mcp（必做）

這個 skill 只負責「抓下來之後」的事：整理檔名、縮圖、打包成書。**讀文章全靠 [mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp)**，請先照它的 README 裝好、設定帳密，確認 AI 能讀到曼報全文，再回來裝這個 skill。

快速確認：在 Claude Code 裡問「你可以讀到曼報的資料了嗎？」，看到「可以讀全文」就表示前置作業完成。

---

## 檔案存在哪裡？會上傳嗎？

**一句話：所有東西都只在你自己的電腦裡。這個 skill 不碰帳密、不連網站，也不會把任何檔案傳到任何地方。**

| 存什麼 | 存在哪裡 | 說明 |
|---|---|---|
| 文章 Markdown 與圖片 | 你指定的資料夾（預設是專案底下的 `articles/`） | mannypro-mcp 匯出時寫入的，就是一般檔案 |
| 縮圖後的圖片 | 系統暫存資料夾（`$TMPDIR/manbao-images-<pid>`） | 打包完就自動刪掉 |
| 做好的電子書 | 你指定的輸出資料夾 | 一般檔案，拖進閱讀器即可 |

- **帳密**：這個 skill 完全不處理帳密，登入是 mannypro-mcp 的事，請看[它的安全說明](https://github.com/nissenyeh/mannypro-mcp#-你的帳密和資料存在哪裡安全嗎)。
- **網路**：五個腳本都不連網，純粹處理本機檔案。
- **不會進 GitHub**：repo 的 `.gitignore` 已經排除 `articles/`、`assets/` 和 `*.epub`，就算你在 repo 資料夾裡操作也推不上去。
- **想刪掉**：刪掉 `articles/` 和電子書檔就好，沒有其他殘留。

---

## 最簡單的安裝方式：交給 AI 幫你裝（不用懂程式）

**開始前：** 確認你已經完成上面的「第 0 步」。

1. 打開終端機（Mac：按 `⌘ + 空白鍵`，輸入「終端機」或「Terminal」後按 Enter），`cd` 到你想放曼報文章的資料夾，輸入 `claude` 按 Enter。

2. 把下面這段**整段複製**，貼進去按 Enter：

   ```text
   幫我安裝這個 Claude Code skill：https://github.com/SamLiaoP/mannypro-to-ebook
   請讀 README，照最後面「給 AI agent 的安裝步驟」做完，裝在目前這個專案裡。
   裝好之後幫我把曼報全部文章存下來，做成可以放 Kobo 的檔案。
   ```

3. 過程中 AI 會請你允許它執行指令，選「Yes」或「允許」就好。最後它會回報兩個 `.epub` 檔的位置。

想自己一步步手動安裝的人，請看下面的完整說明。

---

## 腳本

skill 裡有五個腳本，AI 會照 `SKILL.md` 的流程呼叫它們，你也可以自己跑：

| 腳本 | 用途 |
|---|---|
| `list_slugs.sh <articles 資料夾>` | 列出本機已有的文章 slug，拿去和網站清單比對，只抓缺的 |
| `rename_dates.sh <articles 資料夾>` | 把匯出的 `YYYY-MM-DD 標題.md` 改成 `YYYYMMDD 標題.md`，可重複執行 |
| `shrink_images.py <assets> <輸出>` | 複製一份圖片並縮到最寬 1400px、大 PNG 轉 JPEG；看檔頭判斷真實格式 |
| `md2epub.py <articles> <圖片> <輸出.epub> [--kepub] [--from] [--to]` | Markdown → EPUB 3；加 `--kepub` 產生 Kobo 版 |
| `build_epub.sh <articles 資料夾> <輸出資料夾> [--from YYYYMMDD] [--to YYYYMMDD]` | 縮圖 + 打包一條龍，一次產出兩個檔案 |

---

## 1. 手動安裝

### 1-1 複製 skill 資料夾（最簡單）

```bash
git clone https://github.com/SamLiaoP/mannypro-to-ebook.git
mkdir -p <你的專案>/.claude/skills
cp -R mannypro-to-ebook/skills/mannypro-to-ebook <你的專案>/.claude/skills/
```

想在所有專案都能用，就放到 `~/.claude/skills/` 而不是專案底下。重新開 Claude Code 後，輸入 `/skills` 應該會看到 `mannypro-to-ebook`。

### 1-2 或用 plugin 方式安裝

```
/plugin marketplace add SamLiaoP/mannypro-to-ebook
/plugin install mannypro-to-ebook@mannypro-to-ebook
```

### 1-3 或把連結丟給 Claude Code / Codex

在你的專案目錄打開 Claude Code 或 Codex，貼這一句：

```text
請把 https://github.com/SamLiaoP/mannypro-to-ebook 這個 skill 安裝在這個專案裡，照它 README 最後面「給 AI agent 的安裝步驟」做。
```

AI 會自己 clone、把 skill 放進專案的 skills 資料夾並測試。裝完要重新開啟 Claude Code / Codex。

### 1-4 選配：Pillow

縮圖預設在 macOS 用內建的 `sips`。裝了 [Pillow](https://pypi.org/project/pillow/) 會自動改用它：Linux 也能跑，而且做出來的書小兩到三成。

```bash
pip3 install pillow
```

---

## 2. 怎麼用

直接用自然語言跟 AI 說，例如：

- 「把曼報全部文章存下來，做成可以放 Kobo 的檔案」
- 「曼報有新文章了，更新到最新再重做一本」
- 「只要 2026 年 9 月以後的文章做成一本 EPUB」
- 「曼報的『過路財神』系列單獨做成一本」

要知道的事：

- **兩個檔案的差別**：`.epub` 是標準格式，任何閱讀器都能開；`for kobo.kepub.epub` 多了 Kobo 原生引擎需要的標記，在 Kobo 上翻頁、字級、畫線、筆記和閱讀統計都會比較順。Kobo 使用者拿後者就好。
- **檔名的日期**：是實際收錄文章的最早與最晚發布日，不是製作當天。
- **檔案大小**：一百多篇約 65–85 MB（圖多），Kobo 可以正常開。
- **想自己調參數**：`shrink_images.py --max 1200` 可以把圖縮更小，`md2epub.py --from/--to` 可以只選一段期間。
- **電子書一樣是付費內容，請只供個人使用，不要分享出去。**

---

## 疑難排解

| 狀況 | 原因／解法 |
|---|---|
| AI 說找不到 `mcp__mannypro__*` 工具 | mannypro-mcp 沒裝好或沒重開 Claude Code；回到「第 0 步」 |
| `md2epub.py` 報 `XML error in 〈某篇〉` | 那篇文章用了轉換器沒見過的 Markdown 寫法；請開 issue 附上篇名 |
| 圖片在閱讀器裡是空白 | 沒經過 `shrink_images.py` 就打包（網站有些 `.png` 其實是 WebP）；用 `build_epub.sh` 重做一次 |
| 做出來的檔案特別大 | 用的是 `sips` 後端；`pip3 install pillow` 後重跑會小很多 |
| Kobo 目錄裡沒有章節 | 確認拖進去的是 `.kepub.epub`，而且副檔名沒被改掉 |
| `/skills` 看不到 skill | 資料夾名稱要是 `mannypro-to-ebook`，裡面要有 `SKILL.md`；改完要重開 Claude Code |

---

## 運作原理

1. **比對**：`list_slugs.sh` 從每篇 Markdown 的「原文」網址取出 slug，和 MCP 的 `list_all_titles` 比對，找出還沒匯出的文章。
2. **抓文章**：呼叫 MCP 的 `export_articles`（`download_images: true`），每篇存成 Markdown，圖片存到 `assets/<slug>/`，圖片連結改成相對路徑。
3. **整理檔名**：`rename_dates.sh` 把日期改成 `YYYYMMDD`。
4. **縮圖**：`shrink_images.py` 複製一份圖片，縮到最寬 1400px（Kobo 螢幕用不到更大），大 PNG 轉 JPEG。它看檔頭判斷真實格式，因為網站有不少 `.png` 其實是 JPEG 或 WebP，直接打包會讓 EPUB 的 media-type 標錯、部分閱讀器顯示不出來。
5. **打包**：`md2epub.py` 把 Markdown 轉成 XHTML，組成 EPUB 3（含 nav 和 NCX 兩種目錄），每篇文章一個章節，章節開頭有分類、日期和原文連結。章節先按日期排，同一天的系列文再按集數排，而且會把全形（Ⅰ Ⅱ Ⅲ）和 ASCII（I II III）兩種羅馬數字都換算成數字，否則同一天發的「II」會排到「I」前面。加 `--kepub` 會把每個段落包進 `koboSpan`，這是 Kobo 原生引擎定位和記錄筆記用的。轉換器只用 Python 標準函式庫，不需要 pandoc 或 calibre；每篇轉完都會檢查 XML 合法性。

網站改版或文章用了新的排版方式時，轉換可能會壞，歡迎開 issue。

---

## 給 AI agent 的安裝步驟

> 這一段是寫給 Claude Code 等 AI agent 看的：使用者請你安裝時，依序執行，每一步確認成功再進下一步。使用者多半不熟指令，請用白話跟他說明進度。

1. **確認前置**：呼叫 `mcp__mannypro__login_status`。如果沒有這個工具或回傳失敗，告訴使用者要先照 https://github.com/nissenyeh/mannypro-mcp 的 README 裝好 mannypro-mcp，不要繼續。
2. **取得 skill**：在使用者目前的專案目錄執行 `mkdir -p .claude/skills`，然後把 repo 的 `skills/mannypro-to-ebook` 複製進去（`git clone https://github.com/SamLiaoP/mannypro-to-ebook.git` 到暫存資料夾再 `cp -R`，或 clone 到 `~/mannypro-to-ebook` 後建立符號連結）。使用者若要求「所有專案都能用」，改放 `~/.claude/skills/`。如果你是 Codex 或其他 agent，改放該工具讀取 skill 的資料夾（SKILL.md 格式相同）。
3. **確認腳本可執行**：`chmod +x .claude/skills/mannypro-to-ebook/scripts/*.sh`，並執行 `python3 --version` 確認有 Python 3。macOS 不需要其他東西；Linux 請 `pip3 install pillow`。
4. **測試**：執行 `.claude/skills/mannypro-to-ebook/scripts/list_slugs.sh <articles 資料夾>`（資料夾不存在時輸出為空是正常的）。
5. **告訴使用者**：已經裝好；需要**重新開啟** Claude Code 才會載入 skill；附上兩三句可以直接說的範例（如「把曼報全部文章存下來，做成可以放 Kobo 的檔案」）。

---

## 授權與致謝

本專案的程式碼與文件以 [MIT License](LICENSE) 釋出。這份授權**不包含**任何透過本工具取得的《曼報 Pro》文章、圖片與做出來的電子書，那些內容的著作權屬於曼報 Pro 及其作者，請僅供個人閱讀使用。

- [nissenyeh/mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp)：[Nissen](https://github.com/nissenyeh) 的獨立專案，沒有它就沒有這個 skill。請依其條款使用。
- [曼報 Pro](https://pro.manny-li.com)：值得訂閱的深度商業分析。

## 關於作者

我是 Sam，這個工具是我想在 Kobo 上讀《曼報 Pro》、順手做筆記時做的。有問題或建議歡迎開 issue。

[GitHub](https://github.com/SamLiaoP) · [LinkedIn](https://www.linkedin.com/in/samliaotw/)
