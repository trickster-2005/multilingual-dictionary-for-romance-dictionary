# Romance Multilingual Dictionary ｜ 羅曼多語言字典

**Live site / 網站：<https://trickster-2005.github.io/multilingual-dictionary-for-romance-dictionary/>**

[English](#english) ｜ [繁體中文](#繁體中文)

## English

Type one word and see, on a single page:

1. **A full English entry**: Traditional Chinese glosses, British and American IPA with 🔊 audio, senses grouped by part of speech (with Chinese glosses, examples and usage labels), inflections, synonyms, antonyms and common phrases.
2. **Four Romance languages side by side**: Français ｜ Italiano ｜ Español ｜ Português, aligned row by row with the English senses. Each word shows grammatical gender (text label and colour), definite article, plural, part of speech, IPA, 🔊 audio and a link to its Wiktionary entry.
3. **Etymology and cognates**: an ancestor chain for every word (`night ← Middle English nighte ← … ← Proto-Indo-European *nókʷts`), a “Cognates” badge, a cognate family tree, a short summary and the original etymology text.

You can search in English, French, Italian, Spanish, Portuguese or Chinese. Case and accents are ignored (`cafe` finds `café`), and inflected forms are recognised (`went` → go, `notti` → notte, `yeux` → œil).

The interface defaults to English with a dark theme, and the English entry starts collapsed (the headword and Chinese gloss stay visible). Users can switch to Traditional Chinese or a light theme; their choices are remembered in the browser.

**How lookups work**

1. **Offline dataset** (`data/`): about 9,100 common English headwords prebuilt from Kaikki.org / Wiktextract, with reverse indexes and inflected forms. Results appear almost instantly.
2. **Live Wiktionary lookup** (`wiktionary.js`): any word that is not in the dataset is fetched from the English Wiktionary API in the browser (about 2–4 s) and shown in the same layout, marked as fetched live.

**No backend.** It is a static site (HTML, CSS and vanilla JavaScript, no build step). The Python script in `tools/` is only run offline to regenerate `data/`.

**Run locally**

```bash
python -m http.server 8000
```

Then open <http://localhost:8000/>. Searches can be linked directly, e.g. `?q=summer` or `?q=夏天`.

**Rebuild the dataset**: download the Kaikki.org JSONL dumps (English, French, Italian, Spanish, Portuguese and Latin) into `raw/`, then run

```bash
pip install wordfreq opencc
python tools/build_dataset.py \
  --en raw/kaikki.org-dictionary-English.jsonl.gz \
  --fr raw/kaikki.org-dictionary-French.jsonl.gz \
  --it raw/kaikki.org-dictionary-Italian.jsonl.gz \
  --es raw/kaikki.org-dictionary-Spanish.jsonl.gz \
  --pt raw/kaikki.org-dictionary-Portuguese.jsonl.gz \
  --ancestors raw/kaikki.org-dictionary-Latin.jsonl.gz \
  --top 10000 --out data
```

The first run takes about 15 minutes and caches the extracted records in `raw/build_cache.pkl.gz`, so later rebuilds take a few minutes. `raw/` is git-ignored and must not be committed.

**Deploy**: push the repository (including `data/` and `.nojekyll`), then in **Settings → Pages** choose *Deploy from a branch*, branch `main`, folder `/ (root)`.

**License**: dictionary content comes from English Wiktionary contributors under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), extracted with [Wiktextract](https://github.com/tatuylonen/wiktextract) / [Kaikki.org](https://kaikki.org/). The generated `data/` is released under the same license, and every entry links to its source page.

---

## 繁體中文

輸入一個字，同一頁看到：

1. **完整英文詞條**：中文釋義、英式／美式 IPA 與 🔊 發音、依詞性分組的義項（附中文、例句、語體標籤）、詞形變化、同義詞、反義詞與常見片語。
2. **四種羅曼語對照**：Français｜Italiano｜Español｜Português。依英文詞義逐列對齊，列出陰陽性（文字 + 顏色）、定冠詞、複數、詞性、IPA、🔊 發音與原始詞條連結。
3. **詞源與同源詞**：五個詞各自的詞源鏈（`night ← 中古英語 night ← … ← 原始印歐語 *nókʷts`），以及自動判斷的「同源詞 / Cognates」徽章、同源家族樹、中文摘要和可展開的英文原文。

介面預設為英文、深色模式，英語詞條區預設收起（只顯示單字與中文釋義）；可切換成繁體中文、淺色模式，使用者的選擇會記在瀏覽器中。這是純靜態網站（HTML + CSS + 原生 JavaScript，不需要建置步驟），可以直接部署到 GitHub Pages。

查詢順序：

1. **離線詞庫**（`data/`）：由 Kaikki.org 預先建置的約九千個常用英文詞，含反查索引與詞形變化，載入後約 0.1 秒內顯示。
2. **維基詞典即時查詢**（`wiktionary.js`）：離線詞庫沒有的字，直接向英文維基詞典 API 查詢並轉成相同格式顯示（約 2～4 秒），任何英文字或法、義、西、葡、中文字都能查。頁面會標示「即時取得」，因為這類資料沒有經過預先整理。

---

## 專案結構

```
index.html            頁面骨架（sticky 搜尋列、safe-area、viewport-fit=cover）
style.css             Mobile-first 樣式（Grid/Flexbox、clamp() 字級、淺色/深色主題）
app.js                搜尋、自動完成、渲染、同源家族樹、語音、收藏與紀錄
wiktionary.js         離線詞庫查不到時的維基詞典即時查詢（MediaWiki API，CORS origin=*）
data/                 由 build_dataset.py 產生的 JSON
  meta.json           建置資訊、分片清單、語言名稱（英／中）
  words.json          [[英文詞目, 中文], …]，用於模糊比對
  index/<桶>.json     正規化查詢鍵 → 命中清單（反查索引＋詞形變化）
  entries/<xx>.json   英文詞目 → 完整詞條（依詞目前兩字母分片）
tools/
  build_dataset.py    資料處理腳本（Kaikki.org JSONL → data/）
  sample_seed.py      範例資料來源（56 個英文詞，Kaikki 格式；供測試用）
raw/                  下載的 Kaikki 檔與建置快取（已列入 .gitignore，不需上傳）
.nojekyll             讓 GitHub Pages 原樣提供所有檔案
```

## 本機執行

瀏覽器不允許 `file://` 頁面讀取 JSON，所以需要一個本機伺服器（任何靜態伺服器都可以）：

```bash
python -m http.server 8000
```

然後開啟 <http://localhost:8000/>。可以直接用網址查詢，例如 `?q=夏天`、`?q=summer`、`?q=notti`。

範例資料可以試試：`night`、`summer`、`water`、`bank`、`go`、`été`（同時對應 summer 和 être 的過去分詞）、`fue`（ir／ser）、`notti`、`went`、`cafe`、`夏天`、`brother`、`eat`、`coffee`。

## 重新產生資料

### 範例資料（不需下載，用於測試）

```bash
python tools/build_dataset.py --sample --out data_sample
```

需要 Python 3.9 以上，只用標準函式庫。範例資料寫在 `tools/sample_seed.py`：先展開成與 Kaikki.org 相同格式的紀錄，再經過**與正式資料完全相同的處理流程**。

### 完整資料（Kaikki.org / Wiktextract）

1. 從 <https://kaikki.org/dictionary/> 下載英文維基詞典擷取出的 JSONL（`.jsonl` 或 `.jsonl.gz` 都可以）：
   - English：`kaikki.org-dictionary-English.jsonl`
   - Italian、Portuguese、French、Spanish（各語言頁面的「all word senses」JSONL）
   - 祖先語言（用來延伸詞源鏈並補上詞義）：Latin
2. 準備詞頻表（每行一個英文字，依頻率排序），或安裝 `wordfreq` 讓腳本自動取得：
   ```bash
   pip install wordfreq        # 選用
   pip install opencc          # 選用：簡體中文翻譯自動轉繁體（s2twp）
   ```
3. 執行：
   ```bash
   python tools/build_dataset.py \
     --en raw/kaikki.org-dictionary-English.jsonl.gz \
     --it raw/kaikki.org-dictionary-Italian.jsonl.gz \
     --pt raw/kaikki.org-dictionary-Portuguese.jsonl.gz \
     --fr raw/kaikki.org-dictionary-French.jsonl.gz \
     --es raw/kaikki.org-dictionary-Spanish.jsonl.gz \
     --ancestors raw/kaikki.org-dictionary-Latin.jsonl.gz \
     --top 10000 --out data
   ```
   沒有 `--wordlist` 時會用 `wordfreq` 的英文詞頻表。第一次執行約 15 分鐘（主要是讀取 523 MB 的英文檔），並把抽出的紀錄存到 `raw/build_cache.pkl.gz`；之後調整程式再重建只需幾分鐘。要重新讀取原始檔時加上 `--refresh`。

腳本以串流方式逐行讀取大型檔案，並只保留需要的欄位與語言。處理步驟如下：

1. 從英文檔挑出前 N 個有羅曼語翻譯的詞目，同時收集 `went → go` 這類 form-of 紀錄。
2. 讀取四種羅曼語檔中被翻譯到的詞，取得陰陽性、複數、IPA 和詞源。
3. 反覆掃描祖先語言檔（`--ancestor-passes`，預設 3 次），把詞源鏈延伸到拉丁語、原始印歐語等。
4. 寫出分片檔。每次建置都會先清空輸出資料夾的 `entries/` 和 `index/`。

輸出分成數百個小檔，每次查詢只載入一個索引分片和一個詞條分片。

## 資料結構

### 詞條 `entries/<xx>.json`

```jsonc
{
  "bank": {
    "w": "bank",
    "zh": ["銀行", "河岸", "岸"],
    "ipa": { "uk": "/bæŋk/", "us": "/bæŋk/" },
    "ety": [                                   // 每個 Wiktionary 詞源段落一筆
      { "n": 1, "text": "From Middle English banke, …",
        "chain": [ Node, … ],                  // 由近到遠的祖先
        "cog": [ { "l": "de", "f": "Bank" } ],  // {{cog}} 列出的其他語言同源詞
        "unc": true }                          // 來源不確定（{{unc}}）
    ],
    "pos": [
      { "p": "noun", "e": 0,                   // e = ety 的索引
        "forms": [["pl", "banks"]],            // [代碼, 詞形, 標籤?]
        "senses": [ { "d": "An organization where …", "zh": "銀行",
                      "tags": ["informal"], "ex": ["…"], "syn": ["…"], "grp": 0 } ] }
    ],
    "syn": [], "ant": [], "phr": ["bank account", …],
    "grp": [                                   // 翻譯表 = 對照列，每列一個詞義
      { "label": "financial institution; …", "zh": ["銀行"], "p": "noun", "e": 0,
        "tr": { "it": ["it:banca"], "pt": ["pt:banco"], "fr": ["fr:banque"], "es": ["es:banco"] } }
    ],
    "lx": { "it:banca": Word, … }              // 每個羅曼語詞在詞條內只存一次，對照列以鍵參照
  }
}
```

（葡語變體詞的鍵會加上 `|BR`／`|PT`，例如 `pt:cachorro|BR`。）

**Word**（羅曼語詞）：

```jsonc
{ "w": "banca", "p": "noun", "g": "f",        // g: m | f | mf
  "art": "la", "pl": "banche", "plArt": "le", "fem": "…",
  "ipa": "/ˈbaŋ.ka/", "ipaBR": "…", "ipaPT": "…",   // 葡語分巴西／葡萄牙發音
  "v": "BR",                                   // 僅限某一變體（葡語）
  "gl": "bank (financial institution)",
  "ety": { "chain": [ Node, … ], "text": "…", "unc": false } }
```

**Node**（詞源鏈上的一個祖先）：

```jsonc
{ "l": "la",          // Wiktionary 語言代碼（la、la-vul、ine-pro…）
  "f": "noctem",      // 模板中的詞形
  "t": "inh",         // inh 繼承 | der 衍生 | bor 借用 | calque | ltc | root
  "lm": "nox",        // 詞目（此詞形屬於哪個詞）
  "lmt": "acc",       // 是詞目的哪一格／哪一種形式（acc = 賓格）
  "g": "night",       // 詞義
  "tr": "qahwa",      // 非拉丁字母的轉寫
  "unc": true }       // 此步驟不確定
```

### 索引 `index/<桶>.json`

```jsonc
{ "ete": [ { "h": "summer", "l": "fr", "f": "été", "r": "tr", "gi": 0 },
           { "h": "be", "l": "fr", "f": "été", "r": "trinf", "m": "être", "t": "pp" } ] }
```

- `r`：`hw` 英文詞目、`inf` 英文變化形、`tr` 羅曼語譯詞、`trinf` 譯詞的變化形、`zh` 中文。
- `gi` 指向對照列，用來標示查到的是哪個詞義。
- 查詢鍵先經過正規化：去除前後空白、轉小寫、`œ→oe`、NFKD 後移除所有附加符號（accent）。**`norm()` 在 Python 與 JS 兩邊必須完全一致。**
- 分桶規則：a–z 開頭取前兩個字母（第二個字元不是 a–z 時記為 `_`）；數字為 `0`；其他字元（中文等）為 `x` + (碼位 mod 32) 的十六進位。
- 輸入兩個字以上時，同一個前綴一定落在同一桶，所以自動完成只需載入一個檔案。
- 羅曼語詞只收常用變化形（複數、陰性、分詞、第一／第三人稱現在式、過去式），不收整張變位表。

## 詞源解析與同源判斷

- **新式 `{{etymon}}`／`{{ety}}`**：維基詞典近年改用這類模板，頁面上只寫上一代祖先（如 `:inh|la:nox`）。Kaikki 會把模組算好的整棵祖先樹以 JSON 形式留在 `expansion` 中（開頭被截斷），`etymon_tree()` 補回缺少的括號後還原成樹，再沿著樹取得完整的鏈。若樹的頂端被截斷，再以詞源原文中的「from <語言> <詞>」補上更早的祖先，語言名稱只接受維基詞典在同一份資料中對應過代碼的名稱。
- **傳統模板解析**（`parse_etymology`）：依序讀取 `etymology_templates`：
  - `{{inh}}`、`{{der}}`、`{{bor}}`、`{{lbor}}`、`{{calque}}`… 依序加入祖先鏈。
  - `{{m}}`／`{{l}}` 緊接在祖先之後時，視為補上詞目與詞義（例如 `noctem, accusative of {{m|la|nox}}`）。
  - `{{unc}}` 標記不確定。
  - 遇到 `{{cog}}`／`{{noncog}}`／`{{doublet}}` 即停止；`{{cog}}` 的內容另外收進 `cog`。
  - `{{root}}` 補在鏈尾。
- **鏈的延伸**（`AncestorIndex.extend`）：用鏈尾的 (語言代碼, 正規化詞形) 查祖先字典：
  - 拉丁語的變格形（如 `noctem`）會對應到詞目 `nox`，並記下 `lmt: "acc"`。
  - 查到後接上該詞目自己的詞源，直到查不到為止。
  - 羅曼語詞本身也會加入祖先字典，所以法語 `café ← 義大利語 caffè ← 鄂圖曼土耳其語 … ← 阿拉伯語` 能自動串起來。
- **同源判斷**（`app.js › buildForest`）：
  - 把五個詞（英文 + 各語言譯詞）的鏈轉成「子 → 父」的邊並合併成森林，節點鍵為 `語言代碼:正規化詞目`，**只比對結構化資料，不比對自由文字**。
  - 同一棵樹上有兩種以上語言的詞，就是一組同源詞，標記為 A、B…。
  - 最近共同祖先（LCA）用於產生中文摘要。
  - 例如 summer：義大利語 estate 和法語 été 來自拉丁語 aestās，葡語 verão 和西語 verano 來自通俗拉丁語 \*verānum，英語 summer 自成一支。

## 重複內容的處理（顯示時，`app.js › mergeRows`）

維基詞典把英文義項切得很細，每個細分義項各有一張翻譯表，但羅曼語常用同一組詞（例如 accent 的「韻律重音」和「音樂上的重音」）。

- **對照區**：詞性、英文詞源相同，且**四種語言的詞完全相同**的列才會合併成一列。第一個義項當作列標題，其餘義項以虛線標籤列出，中文釋義取聯集。只要有一個詞不同就不合併（例如 bank 的「分行」列多了西語 sucursal）。
- **詞源區**：詞源描述的是詞而不是義項，所以改成**每個英文詞源一張卡**（bank 有「銀行」和「河岸」兩個不同來源，就是兩張卡）。卡中收錄該詞源底下所有列出現過的羅曼語詞，每種語言最多 3 個，每個詞只出現一次，並註明涵蓋對照區的哪幾列。
- **英語詞條區**不合併：那些是真正不同的英文用法。
- 合併在顯示前進行，離線詞庫和即時查詢都適用。以目前的資料為例，9,099 個詞條中有 711 個（7.8%）含完全相同的列。

## 維基詞典即時查詢（`wiktionary.js`）

- 用 `action=query&prop=revisions` **批次**讀取原始 wikitext（不經伺服器渲染，很快），自己切出語言段落。
- 翻譯表、詞源模板、form-of（`went` → `go`、`notti` → `notte`）都從 wikitext 解析，規則與建置腳本相同。
- 義項、例句、語體標籤、詞形、IPA、陰陽性需要渲染後的 HTML：只把去掉翻譯表、引文、變位表的精簡段落送去 `action=parse` 渲染（這是最耗時的部分，因此與翻譯、羅曼語詞的查詢**並行**）。
- 渲染結果若帶有 `data-ety-tree-json`（etymon 的完整樹），就直接使用。
- 第二階段：把每條詞源鏈最末端的祖先批次查詢其頁面（例如拉丁語 `mōns` → `Reconstruction:Proto-Italic/…`），逐層往上接，完成後只更新詞源區塊。
- 查非英文字時，先找該語言段落的第一個英文釋義連結（`manzana` → apple），再查英文詞條。
- 所有回應都快取在記憶體中；查不到時列出維基詞典 opensearch 的相近標題。

## 版面（RWD）

| 寬度 | 版面 |
| --- | --- |
| < 640 px | 單欄；英文詞條在前。四種語言以 FR｜IT｜ES｜PT 分頁切換（可左右滑動，記住上次選擇）。 |
| 640–1023 px | 英文詞條全寬；四種語言排成 2 × 2；詞源在下方。 |
| ≥ 1024 px | 英文詞條分為「義項」與「側欄」兩欄；四種語言排成一列四欄；詞源鏈與家族樹左右並排。 |

- 搜尋列 sticky，並以 `env(safe-area-inset-*)` 避開瀏海與圓角。
- 字級使用 `clamp()`；釋義行寬約 70 字元。
- 可點擊目標至少 44 × 44 px。
- 家族樹在自己的容器內水平捲動，整個頁面不會出現橫向捲軸。
- 已在 320、375、768、1024、1440 px 檢查過。
- 主題跟隨系統的 `prefers-color-scheme`，也可以手動切換；手動選擇會記住。

## 無障礙

- 使用語意化 HTML，並提供跳至主要內容的連結。
- 搜尋框依 ARIA combobox 模式實作，可用 ↑↓ Enter Esc 操作。
- 語言分頁為 tablist，可用 ←→ Home End 切換。
- 所有圖示按鈕都有 `aria-label`；焦點外框清楚可見。
- 陰陽性同時以文字標示（陽性 m.／陰性 f.），不只靠顏色。
- 查詢結果由 `role="status"` 區域向讀屏軟體播報。
- 淺色與深色主題皆符合 WCAG AA 對比。

## 部署到 GitHub Pages

1. 把整個資料夾推到 GitHub repository（`data/` 與 `.nojekyll` 都要包含）。
2. 在 **Settings → Pages** 中，Source 選 **Deploy from a branch**，分支選 `main`，資料夾選 `/ (root)`。
3. 幾分鐘後即可從 `https://<帳號>.github.io/<repo>/` 開啟。所有路徑都是相對路徑，放在子目錄也能正常運作。

更新資料時，只要重新執行 `build_dataset.py` 並提交 `data/`。`raw/` 已列入 `.gitignore`，不要上傳（GitHub 單檔上限 100 MB）。

## 授權與出處

詞典內容來自英文維基詞典（Wiktionary）的貢獻者，依 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 授權，經 [Wiktextract](https://github.com/tatuylonen/wiktextract) / [Kaikki.org](https://kaikki.org/) 擷取。產生的 `data/` 同樣以 CC BY-SA 4.0 釋出。

頁尾有完整出處，每個詞條與譯詞也都連回原始頁面。`sample_seed.py` 的例句為原創，其餘內容整理自維基詞典。

發音使用瀏覽器內建的 Web Speech API。能否朗讀取決於作業系統是否安裝了該語言的語音；若沒有，會以預設語音朗讀並提示使用者。
