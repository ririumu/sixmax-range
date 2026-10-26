# Netlify デプロイマニュアル

このドキュメントは、本プロジェクト（6-max RFIレンジグリッド PWA）を
Netlify にデプロイする手順をまとめたものです。

現在の公開先: **https://rfi-range-grid.netlify.app**

---

## 1. 前提条件

| 項目 | 内容 |
|---|---|
| Netlify アカウント | https://app.netlify.com で作成（無料枠で可） |
| ローカル環境 | `python3`（3.8+）と `make`（macOS/Linux 標準） |
| 認証 | 下記いずれか（後述） |

### 認証の用意（どれか一つ）

**A. Netlify CLI のログイン情報（本プロジェクト標準）**

`netlify login` 済みのマシンなら、`make deploy-netlify` が
`~/Library/Preferences/netlify/config.json` から自動でトークンを読みます。

**B. 環境変数 `NETLIFY_AUTH_TOKEN`**

Netlify 管理画面 → User settings → Applications →
Personal access tokens → **New access token** で発行し:

```sh
export NETLIFY_AUTH_TOKEN=nfp_xxxxxxxxxxxx
```

CI での自動化はこちらを使います（シークレット登録推奨）。

---

## 2. デプロイ方法

### 方法 A: `make deploy-netlify`（推奨・CLI不要）

```sh
make deploy-netlify
```

内部動作:

1. `make check` — デプロイ前チェックゲート（ファイル・manifest・SW資産検証）
2. `make dist` — 公開ファイルを `dist/` に集約
3. `tools/deploy_netlify.py` — REST API で zip アップロード → ready 待機

初回実行時にサイト `rfi-range-grid` が自動作成され、
サイトIDが `.netlify/state.json` に保存されます。
2回目以降は同一サイトへ差し替えデプロイされます。
（新しくクローンした環境など state.json が無い場合も、
アカウント内の同名サイトを探して再利用します）

> 別名でサイトを作りたい場合:
> `python3 tools/deploy_netlify.py --name your-site-name`

### 方法 B: netlify CLI を使う

```sh
npm install -g netlify-cli
netlify login
make dist
netlify deploy --dir=dist --prod
```

`netlify.toml` が同梱済みのため、リポジトリ連携済みサイトなら
`netlify deploy --build --prod` でも動作します。

### 方法 C: GitHub 連携（自動デプロイ）

1. Netlify 管理画面 → **Add new site** → **Import an existing project**
2. GitHub を選択し `ririumu/sixmax-range` を接続
3. ビルド設定は `netlify.toml` が自動適用:
   - Build command: `make dist`
   - Publish directory: `dist`
4. 以後 `main` への push で自動デプロイ

### 方法 D: Netlify Drop（最も手軽・手動）

```sh
make dist
```

生成された `dist/` フォルダを https://app.netlify.com/drop に
ドラッグ&ドロップ。アカウント作成直後でも数秒で公開されます。
（`_headers` も自動適用）

---

## 3. デプロイ後の検証

```sh
make verify LIVE_URL=https://rfi-range-grid.netlify.app/
```

`tools/verify_live.py` が、SW の全プリキャッシュ対象が 200 でローカルと
バイト一致すること、開発用ファイル（`_headers` 等）が非公開であることを
確認します（詳細は [GitHub Pages マニュアル](DEPLOY_GITHUB_PAGES.md#5-検証)）。

個別に確認する場合:

```sh
# 1. 全リソースが 200 を返すか
for p in "" manifest.webmanifest sw.js icons/icon-512.png; do
  curl -s -o /dev/null -w "%{http_code} /$p\n" \
    "https://rfi-range-grid.netlify.app/$p"
done

# 2. sw.js が no-cache で配信されているか（PWA更新の要）
curl -sI https://rfi-range-grid.netlify.app/sw.js | grep -i cache-control
# 期待値: cache-control: no-cache

# 3. セキュリティヘッダ
curl -sI https://rfi-range-grid.netlify.app/ | \
  grep -i "x-content-type\|referrer\|x-frame"
```

ブラウザでは:

- トップページでグリッドが表示・ポジション切替が動く
- アドレスバーに「インストール」アイコン（Chrome系）
- DevTools → Application → Service Workers が登録済み
- 機内モードで再読み込みしても動作（オフライン対応）

---

## 4. 運用

### 更新デプロイの手順

```sh
# 1. アプリを編集

# 2. sw.js のキャッシュバージョンを上げる（必須）
make bump

# 3. チェック＋パッケージ＋デプロイ
make deploy-netlify
```

`make bump` を忘れると、既存ユーザーの SW キャッシュが
旧バージョンのまま残り、更新が届きません。

### `.netlify/state.json`

サイトIDを保持するローカル状態ファイル（gitignore 済み）。
削除しても、次回デプロイ時にアカウント内の同名サイト（`--name`、
既定 `rfi-range-grid`）を探して再生成します。

### サイト名の変更・独自ドメイン

- サブドメイン変更: Netlify UI → Site settings → Change site name
- 独自ドメイン: Domain settings → Add custom domain（HTTPS 自動）

### ロールバック

Netlify UI → Deploys → 過去デプロイの **Publish deploy** で
任意バージョンに即時戻せます。

---

## 5. トラブルシューティング

| 症状 | 原因と対処 |
|---|---|
| `error: no Netlify token` | `NETLIFY_AUTH_TOKEN` を設定するか `netlify login` を実行 |
| `error: dist/ not found` | `make dist` を先に実行（`make deploy-netlify` なら自動） |
| サイト名が取れない | `rfi-range-grid` は取得済み。`--name` で別名を指定 |
| `POST /sites -> 422` | 名前が他アカウントで使用済み、または不正。別名で再試行（自アカウントの同名サイトは自動で再利用） |
| デプロイ後も旧画面 | `make bump` 忘れ。VERSIONを上げて再デプロイ。それでも駄目なら DevTools → Application → Unregister SW |
| `_headers` が効かない | `dist/` に `_headers` が含まれているか確認（`make dist` は自動同梱） |
| API 403 | トークン失効/権限不足 → 新しい PAT を発行 |

### チェックゲートで止まった場合

`make dist` 内部の `check_deploy.py` がエラーを出した場合は、
出力の `ERROR` 行を確認。manifest アイコン欠落・sw.js の
プリキャッシュ対象不存在・ルート絶対パス混入などを機械的に検出します。

---

## 6. 参考: 現在のデプロイ状況

| 項目 | 値 |
|---|---|
| サイト名 | `rfi-range-grid` |
| URL | https://rfi-range-grid.netlify.app |
| サイトID | `.netlify/state.json` 参照（gitignore 済み） |
| デプロイ実績 | REST API zip deploy ×4 回、すべて ready（最新は `rfi-v2`） |
| 並行稼働 | GitHub Pages（https://ririumu.github.io/sixmax-range/ 、push で自動デプロイ、[マニュアル](DEPLOY_GITHUB_PAGES.md)） |
