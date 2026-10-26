# 6-max RFIレンジグリッド（PWA）

テキサスホールデム初心者向けに、6-max・100bb のポジション別オープンレイズレンジ（RFI: Raise First In）を 13×13 ハンドグリッドで学べる PWA アプリです。

## 機能

- UTG / HJ / CO / BTN / SB のポジション切り替え
- 13×13 ハンドグリッド（上三角=スーテッド、対角=ペア、下三角=オフスーツ）
- レンジ内ハンドを種類別に色分け（ペア=黄 / スーテッド=緑 / オフスーツ=青）
- オープン率・コンボ数の自動計算表示
- セルタップでハンド詳細（種類・コンボ数・レンジ内外）を表示
- ポジション説明・凡例・座標軸ラベル付き
- 選択ポジションを localStorage に保存
- オフライン完全動作（Service Worker プリキャッシュ）
- ホーム画面追加対応（manifest + apple-touch-icon + maskable）
- 更新時トースト通知 → タップで即時アップデート

## ファイル構成

```
index.html               単一ファイルアプリ（CSS/JS インライン）
manifest.webmanifest     PWA マニフェスト
sw.js                    Service Worker（オフライン対応・更新管理）
icons/                   アイコン類（PNG 192/512/maskable/apple-touch + SVG favicon）
Makefile                 serve / icons / bump / check / bump-guard / dist /
                         dist-pages / verify / deploy-netlify / clean
_headers                 Netlify・CF Pages 用ヘッダ（sw.js no-cache 等。GH Pages では除外）
netlify.toml             Netlify git連携用ビルド設定
.github/workflows/       GitHub Pages 自動デプロイ（bump ガード・公開検証付き）
tools/make_icons.py      アイコン生成スクリプト（Python 標準ライブラリのみ）
tools/bump_version.py    sw.js の VERSION をインクリメント
tools/check_deploy.py    デプロイ前チェックゲート
tools/verify_live.py     公開サイトの検証・bump 忘れガード（ホスト共通）
tools/deploy_netlify.py  Netlify REST API デプロイ（CLI不要）
docs/DEPLOY_GITHUB_PAGES.md  GitHub Pages デプロイマニュアル
docs/DEPLOY_NETLIFY.md   Netlify デプロイマニュアル
.aidoc/                  開発プロセスドキュメント
```

## 使い方

### ローカルで試す

```sh
make serve    # = python3 -m http.server 8000
# → http://localhost:8000
```

PWA 機能（Service Worker・インストール）は `http(s)://` 配信時のみ有効です。
`index.html` を直接ブラウザで開いてもアプリ本体は動作します。

### デプロイ

公開対象は `dist/` に集約されます（公開されるのはアプリファイルのみ。
`.aidoc/`・`tools/`・ドキュメント類は含まれません）。

```sh
make dist      # デプロイ前チェック → dist/ へ公開ファイルを集約
```

#### GitHub Pages（自動デプロイ・稼働中）

**https://ririumu.github.io/sixmax-range/** で公開中です。
詳細手順は **[GitHub Pages デプロイマニュアル](docs/DEPLOY_GITHUB_PAGES.md)** を参照。

`.github/workflows/deploy.yml` により main への push で自動デプロイされます。

- 工程: `make dist-pages`（チェック＋集約）→ `make bump-guard` → デプロイ → `make verify`
- VERSION を上げ忘れたままアプリを変えた push は bump ガードで止まります
- `.aidoc/`・`docs/`・`README.md`・`AGENTS.md` のみの変更では再デプロイしません
  （手動実行: `gh workflow run deploy.yml`）
- 別リポジトリで利用する場合は Settings → Pages → Source を **GitHub Actions** に設定

#### Netlify（稼働中）

**https://rfi-range-grid.netlify.app** で公開中です。
詳細手順は **[Netlify デプロイマニュアル](docs/DEPLOY_NETLIFY.md)** を参照。

```sh
make deploy-netlify   # check → dist → REST API で zip デプロイ
make verify LIVE_URL=https://rfi-range-grid.netlify.app/   # 公開検証
```

- 認証: `netlify` CLI のログイン情報、または環境変数 `NETLIFY_AUTH_TOKEN`
- サイト情報は `.netlify/state.json` に保持（無い場合はアカウント内の同名サイトを再利用）
- `netlify.toml` 同梱のため、Netlify UI で GitHub 連携すれば自動デプロイにも対応
- `_headers` が同梱され、sw.js の no-cache・セキュリティヘッダが自動適用

#### Cloudflare Pages / その他の静的ホスト

- `make dist` 後、`dist/` を publish ディレクトリ or アップロード
- `_headers` は Cloudflare Pages でも適用。任意ホストでも HTTPS なら PWA 動作

#### リリース手順

```sh
# 1. アプリを変更したら必ずバージョンを上げる（sw.js のキャッシュ更新のため）
make bump

# 2. デプロイ前チェック（CIでも自動実行）
make check
make bump-guard   # 公開版と比較して bump 忘れを検出

# 3. デプロイ（GitHub Pages は push で自動。Netlify は make deploy-netlify）
git push

# 4. 公開サイトがローカルと一致するか確認（CIでも自動実行）
make verify
```

`make bump-guard` / `make verify` の対象は既定で GitHub Pages。
`LIVE_URL=...` で別ホストを指定できます。

その他のターゲット: `make serve`（ローカルプレビュー）、`make icons`、
`make dist`（`dist/` 生成のみ）、`make clean`。

### アイコン再生成

```sh
make icons   # または python3 tools/make_icons.py
```

## 対応環境

- iOS Safari（ホーム画面追加・フルスクリーン対応）
- Android Chrome / Edge（インストール可能）
- デスクトップ Chrome / Edge / Safari / Firefox
- Service Worker 非対応環境でもアプリ本体は動作

## 更新のしかた

`index.html` などを変更したら `make bump` で `sw.js` の `VERSION`
を上げてください（`tools/bump_version.py` が自動インクリメント）。
新キャッシュが配信され、利用中の画面に更新トーストが表示されます。
上げ忘れた場合は GitHub Pages の CI（bump ガード）がデプロイを止めます。

## レンジデータについて

代表的な GTO 寄りの簡略レンジ。SB はレイズオンリー簡略版です
（ソルバー出力はリンプ混合戦略が一般的）。学習用途向けであり、
実戦では対戦相手・スタック・レーキに応じて調整してください。
