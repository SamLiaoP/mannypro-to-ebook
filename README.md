# mannypro-to-ebook

把《曼報 Pro》（[pro.manny-li.com](https://pro.manny-li.com)）的會員文章備份成本機 Markdown，再合併成一本可以放進 Kobo（或任何 EPUB 閱讀器）的電子書的 Claude Code skill。

每篇文章一個章節、目錄可直接跳章、文字可調字級、可畫線做筆記，圖表與圖說都內嵌在書裡。

> [!IMPORTANT]
> **⚠️ 你需要自己有《曼報 Pro》的付費會員帳號。**
>
> 這個工具透過 [mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp) 用**你自己的帳號**讀取文章，不會繞過付費牆，也不附帶任何帳號或內容。
>
> **做出來的電子書只供你個人閱讀，請不要轉載或散布付費內容。**
>
> 👉 還不是會員？**[訂閱《曼報 Pro》](https://pro.manny-li.com/join)**，支持作者持續產出深度內容。
>
> 這是個人製作的**非官方工具**，與《曼報 Pro》、Manny Li、Firstory 沒有任何關係。

*English: a Claude Code skill that archives your own Manny Pro subscription articles as Markdown and bundles them into a reflowable EPUB / Kobo KEPUB, one chapter per article. Requires your own paid account and [mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp). For personal reading only.*

## 👀 用起來像這樣

裝好之後，在 Claude Code 裡直接用中文講就行：

- 「把曼報全部文章存下來，做成可以放 Kobo 的檔案」
- 「曼報有新文章了，更新到最新再重做一本」
- 「只要 2026 年 9 月以後的文章做成一本 EPUB」

Claude 會先比對本機已有的文章和網站清單，只補缺的那幾篇，再重新打包整本書。產出長這樣：

```
articles/
  20260925 名利雙收 I：別人出錢出力的高利潤生意.md
  20260925 名利雙收 II：學術出版業為何越來越集中化？.md
  ...
  assets/<slug>/...            ← 每篇文章的圖片
曼報Pro合輯 20250929-20261013.epub               ← 標準 EPUB 3，一般閱讀器用
曼報Pro合輯 20250929-20261013 for kobo.kepub.epub  ← Kobo 用這個
```

檔名的日期範圍是實際收錄文章的最早與最晚發布日。

## 📦 安裝

### 前置：mannypro-mcp

先照 [mannypro-mcp 的 README](https://github.com/nissenyeh/mannypro-mcp) 安裝並設定好帳密。這個 skill 只負責「抓下來之後」的事，讀文章全靠它。

### 方法一：複製 skill 資料夾（最簡單）

把 `skills/mannypro-to-ebook` 放進你專案的 `.claude/skills/`：

```bash
git clone https://github.com/SamLiaoP/mannypro-to-ebook.git
mkdir -p <你的專案>/.claude/skills
cp -R mannypro-to-ebook/skills/mannypro-to-ebook <你的專案>/.claude/skills/
```

想在所有專案都能用，就放到 `~/.claude/skills/` 而不是專案底下。

### 方法二：用 Claude Code plugin 安裝

```
/plugin marketplace add SamLiaoP/mannypro-to-ebook
/plugin install mannypro-to-ebook@mannypro-to-ebook
```

### 選配：Pillow

縮圖預設在 macOS 用內建的 `sips`。裝了 [Pillow](https://pypi.org/project/pillow/) 會改用它，Linux 也能跑，而且輸出的書會小兩到三成：

```bash
pip3 install pillow
```

## 🔧 它實際做了什麼

1. **比對**：`list_slugs.sh` 列出本機已有的文章 slug，和 MCP 的 `list_all_titles` 比對，只匯出還沒有的。
2. **抓文章**：呼叫 MCP 的 `export_articles`（`download_images: true`），每篇存成 Markdown，圖片存到 `assets/<slug>/`。
3. **整理檔名**：`rename_dates.sh` 把 `YYYY-MM-DD 標題.md` 改成 `YYYYMMDD 標題.md`。
4. **縮圖**：`shrink_images.py` 複製一份圖片，縮到最寬 1400px（Kobo 螢幕用不到更大），大 PNG 轉 JPEG。它看檔頭判斷真實格式，因為網站有不少 `.png` 其實是 JPEG 或 WebP，直接打包會讓部分閱讀器顯示不出來。
5. **打包**：`md2epub.py` 把 Markdown 轉成 XHTML 並組成 EPUB 3（含 nav 與 NCX 目錄）。加 `--kepub` 會包上 Kobo 原生引擎需要的 `koboSpan` 標記。轉換器只用 Python 標準函式庫，不需要 pandoc 或 calibre。

`build_epub.sh` 把第 4、5 步串起來，也可以手動跑：

```bash
skills/mannypro-to-ebook/scripts/build_epub.sh <articles 資料夾> <輸出資料夾> [--from 20260901] [--to 20261231]
```

## 🗂 Repo 結構

```
skills/mannypro-to-ebook/
  SKILL.md               ← Claude 讀的流程說明
  scripts/
    list_slugs.sh        ← 已匯出的文章 slug
    rename_dates.sh      ← 檔名日期改成 YYYYMMDD
    shrink_images.py     ← 縮圖、格式修正（Pillow 或 sips）
    md2epub.py           ← Markdown → EPUB / KEPUB
    build_epub.sh        ← 縮圖 + 打包一條龍
```

## 📄 授權

本專案的程式碼與文件以 [MIT License](LICENSE) 釋出。

這份授權**不包含**任何透過本工具取得的《曼報 Pro》文章、圖片與產出的電子書，那些內容的著作權屬於曼報 Pro 及其作者，請僅供個人閱讀使用。[mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp) 是 [Nissen](https://github.com/nissenyeh) 的獨立專案，請依其條款使用。

## 🙏 致謝

- [nissenyeh/mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp)：沒有它就沒有這個 skill。
- [曼報 Pro](https://pro.manny-li.com)：值得訂閱的深度商業分析。
