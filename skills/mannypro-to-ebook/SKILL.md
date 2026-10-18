---
name: mannypro-to-ebook
description: 把曼報 Pro（pro.manny-li.com）的文章抓下來存成「YYYYMMDD 標題.md」加本機圖片，再合併成可放進 Kobo 閱讀器的 EPUB／KEPUB（每篇一章、可跳章、可調字級、可畫線做筆記）。只要使用者提到曼報、Manny、pro.manny-li.com，想把文章「存下來」「備份」「匯出」「更新到最新」，或想把文章放到 Kobo、電子書閱讀器、做成 EPUB，就用這個 skill，即使他沒有明說要哪一種格式。也適用於「只要某個日期區間」「只補最近幾篇」的要求。
---

# 曼報 Pro → 本機封存 → Kobo 電子書

整個流程分三段，每段都能單獨執行：**抓文章**（MCP 匯出）→ **整理檔名**（日期前綴）→ **打包電子書**（腳本）。
使用者通常是要「更新到最新」，所以先看現況，只補缺的文章，不要每次全部重抓。

需求：
- 已安裝並登入 [mannypro-mcp](https://github.com/nissenyeh/mannypro-mcp)（提供 `mcp__mannypro__*` 工具；需要使用者自己的曼報 Pro 會員帳號）。
- Python 3（只用標準函式庫）。縮圖用 Pillow，沒有的話在 macOS 會自動改用內建的 `sips`；兩者都沒有時圖片會原樣打包（檔案較大但仍可用）。
- 產出僅供使用者個人閱讀，付費內容不要散布。

## 0. 先弄清楚現況

1. 確認封存資料夾。慣例是專案根目錄的 `articles/`，裡面是 `YYYYMMDD 標題.md` 與 `assets/<slug>/` 圖片；還沒有就建立它。使用者另有指定就照他的。
2. 跑 `mcp__mannypro__login_status` 確認能讀全文。
3. 跑 `mcp__mannypro__list_all_titles` 拿到全部文章（日期｜分類｜標題｜slug）。
4. 跑 `scripts/list_slugs.sh <articles_dir>` 列出已經存在的 slug，和第 3 步比對，找出還沒匯出的文章。資料夾是空的就代表要全抓。

## 1. 抓文章（export_articles）

用 `mcp__mannypro__export_articles`，參數：
- `articles`：slug 清單，**一次 20 篇左右**（太多一次會跑很久；多個批次可以在同一回合平行呼叫）。
- `folder`：articles 資料夾的絕對路徑。
- `download_images: true`：圖片會存到 `folder/assets/<slug>/`，Markdown 改用相對路徑，這是後面能離線打包的關鍵。

匯出的檔名是 `YYYY-MM-DD 標題.md`，開頭有「原文 / 發布日期 / 分類」三行與封面圖。

## 2. 整理檔名

檔名日期不帶連字號：`20261013 標題.md`，這樣在檔案總管裡排序和肉眼辨識都比較乾淨。跑

```bash
scripts/rename_dates.sh <articles_dir>
```

可重複執行，只會改還沒改過的。圖片用相對路徑，改檔名不會斷圖。

驗證一下：`.md` 數量等於網站總篇數、沒有殘留 `YYYY-` 開頭的檔案、`grep -c 'https://.*\.(png|jpg)' *.md` 為 0（圖片都已本機化）。

## 3. 打包成電子書

```bash
scripts/build_epub.sh <articles_dir> <out_dir> [--from YYYYMMDD] [--to YYYYMMDD] [--name 曼報Pro合輯]
```

腳本會：`shrink_images.py` 複製一份圖片並縮到最寬 1400px、大 PNG 轉 JPEG（Kobo 螢幕不到 1300px 寬，整本書通常能縮到原來的六成以下）→ 呼叫 `md2epub.py` 兩次。縮圖腳本是看檔頭判斷真實格式，不信副檔名：網站有不少 `.png` 其實是 JPEG 或 WebP，直接打包的話 EPUB 的 media-type 會標錯、WebP 在部分閱讀器根本不顯示，所以不要跳過這一步自己 `cp` 圖片。產生：

- `曼報Pro合輯 <最早日期>-<最晚日期>.epub`：標準 EPUB 3，給一般閱讀器。
- `曼報Pro合輯 <最早日期>-<最晚日期> for kobo.kepub.epub`：加了 koboSpan 的 Kobo 版，**放到 Kobo 用這個**，字級、畫線、筆記、閱讀統計都走 Kobo 原生引擎。

日期範圍取自實際納入的文章（不是今天的日期）。使用者要「只做某段期間」時用 `--from/--to`。

轉換器 `md2epub.py` 是自寫的，不依賴 pandoc 或 calibre，所以在乾淨的機器上也能跑。它已處理：標題降階（內文 `#` 變 h2，章節標題才是 h1）、鬆散清單、巢狀清單、引言、圖片＋斜體圖說、兩個空白的硬換行、CJK 行合併不加空格、`***粗斜***`、`[**](url)` 這種壞掉的連結、裸露 URL 不被斜體誤判。每篇轉完都會用 minidom 檢查 XML 合法性，壞掉會直接報錯並指出哪篇。

## 4. 交付前驗證

做完至少確認：
- 兩個檔案都存在，大小合理（約 0.6MB／篇）。
- 章節數＝文章數（`unzip -l` 數 `OEBPS/text/ch*.xhtml`）。
- 隨機抽一章看清單、圖片、連結有轉成 HTML，沒有殘留 `**`、`](`。
- 提醒使用者：沒辦法在電腦上模擬 Kobo，請傳到裝置翻幾章確認。

## 常見狀況

- **只要補最新幾篇**：步驟 0 比對後只匯出缺的，再跑 rename 與 build；build 會重做整本（一百多篇約一分鐘），輸出檔名的日期範圍會自動更新，舊檔案可以刪掉或保留。
- **md2epub 報 XML error**：通常是新的 Markdown 寫法沒涵蓋。把錯誤那篇的 XHTML 印出來找不配對的標籤，修 `inline()` 或 `parse_blocks()`，不要手改文章。
- **想要官方驗證**：有 `epubcheck` 可以檢查 EPUB 規範、`kepubify` 可以產生官方版 Kobo 檔，但不是必要。
- **Podcast**：同一個 MCP 有 `list_episodes` / `download_episode` / `transcribe_episode`，不在這個流程內。
