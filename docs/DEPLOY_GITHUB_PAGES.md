# GitHub Pages デプロイマニュアル

このドキュメントは、本プロジェクト（6-max RFIレンジグリッド PWA）を
GitHub Pages で公開・運用する手順をまとめたものです。

現在の公開先: **https://ririumu.github.io/sixmax-range/**
（リポジトリ: https://github.com/ririumu/sixmax-range ）

---

## 1. 仕組み

`main` への push で `.github/workflows/deploy.yml` が動き、
検証済みのアプリファイルだけを公開します。

```
push (main)
  └─ checkout
  └─ configure-pages        … 公開URL(base_url)を取得
  └─ make dist-pages        … check_deploy ゲート → dist/ 集約（_headers 除外）
  └─ make bump-guard        … VERSION 据え置きのままアプリが変わっていたら中止
  └─ upload-pages-artifact  … dist/ をアーティファクト化
  └─ deploy-pages           … 公開
  └─ make verify            … 公開ファイルがこのコミットとバイト一致するか検証
```

- 公開されるのは `index.html` / `manifest.webmanifest` / `sw.js` / `icons/` のみ
  （`.aidoc/`・`tools/`・`docs/`・`_headers` などは公開されません）
- `.aidoc/`・`docs/`・`README.md`・`AGENTS.md` だけの変更では再デプロイしません
- 同時実行は1件に制限し、進行中のデプロイは中断しません

---

## 2. 初期設定（新しいリポジトリ・フォークで使う場合）

本リポジトリは設定済みです。別リポジトリで使う場合のみ実施します。

1. リポジトリを **public** にする（private で Pages を使うには有料プランが必要）
2. Pages の公開元を **GitHub Actions** にする
   - UI: Settings → Pages → Build and deployment → Source: **GitHub Actions**
   - CLI:
     ```sh
     gh api -X POST repos/OWNER/REPO/pages -f build_type=workflow
     ```
3. 初回の push が設定前に走って失敗していたら再実行
   ```sh
   gh workflow run deploy.yml
   ```
4. `Makefile` の `LIVE_URL` を自分の公開URLに変更
   （CI は公開URLを自動取得するため、ワークフローの変更は不要）

---

## 3. 更新デプロイの手順

```sh
# 1. アプリを編集

# 2. sw.js のキャッシュバージョンを上げる（必須）
make bump

# 3. ローカルで事前確認
make check        # ファイル・manifest・SW資産・パスの検証
make bump-guard   # 公開版と比べて bump 忘れがないか

# 4. commit & push → 自動デプロイ
git commit -am "feat: ..." && git push

# 5. 結果確認
gh run watch      # CI の進行を表示
make verify       # 公開サイトがローカルと一致するか
```

手動で再デプロイしたい場合（ドキュメントのみの変更後など）:

```sh
gh workflow run deploy.yml
```

---

## 4. GitHub Pages 固有の制約と対策

| 制約 | 影響 | 本プロジェクトの対策 |
|---|---|---|
| HTTP ヘッダを設定できない（全ファイル `Cache-Control: max-age=600` 固定） | SW が更新時に HTTP キャッシュ上の古い index.html をプリキャッシュし、次の版まで古い画面が残る恐れ | `sw.js` のプリキャッシュは `cache: "reload"` で HTTP キャッシュを迂回。登録時に `updateViaCache: "none"` |
| `_headers` を解釈しない | ただの公開ファイルとして露出する | `make dist-pages` で除外（Netlify 用 `make dist` には同梱） |
| サブパス配信（`/sixmax-range/`） | `/` 始まりの絶対パスはリンク切れ | 相対パスのみ使用。`check_deploy.py` が絶対パス混入を検出 |
| セキュリティヘッダ（nosniff・X-Frame-Options 等）を付けられない | Netlify より防御が一段弱い | 外部リソース・入力フォームのない静的アプリのため許容 |
| Jekyll | Actions のアーティファクト公開では実行されない | `.nojekyll` は不要 |
| dotfile | `upload-pages-artifact` v4 以降は除外 | 公開物に dotfile なし |

HTTPS は強制（`https_enforced: true`）されており、PWA の要件を満たします。

---

## 5. 検証

### `make verify`（デプロイ後）

`tools/verify_live.py` が公開サイトを取得し、次を確認します。

- `sw.js` と SW がプリキャッシュする全ファイルが 200 で、ローカルとバイト一致
- 開発用ファイル（`_headers`・`README.md`・`.aidoc/` など7種）が公開されていない
- 反映待ちを考慮して 10 秒間隔で最大 12 回リトライ

CI の最終ステップでも同じ検証が走ります。別ホストも検証できます:

```sh
make verify LIVE_URL=https://rfi-range-grid.netlify.app/
```

### `make bump-guard`（デプロイ前）

公開中の `sw.js` の VERSION がローカルと同じなのに、アプリファイルの中身が
違う場合に失敗します。この状態で公開すると、キャッシュ優先の SW が
既存ユーザーに更新を届けません。

### ブラウザでの確認

- グリッドが表示され、ポジション切替が動く
- DevTools → Application → Service Workers: scope が `/sixmax-range/`
- Cache Storage に現在の VERSION（例: `rfi-v2`）のキャッシュがある
- 機内モード（オフライン）で再読み込みしても表示される

---

## 6. リポジトリ名の変更・独自ドメイン

### リポジトリ名を変えた場合

- 公開URLは `https://OWNER.github.io/新しい名前/` に変わります
- **旧URLは 404 になり、転送されません**（git の URL は転送されるが Pages は対象外）
- 旧URLでホーム画面に追加したアプリは、旧キャッシュのままオフライン動作を続けますが、
  更新は届きません。新URLから入れ直してもらう必要があります
- 変更が必要な箇所: `Makefile` の `LIVE_URL`、`README.md`、本マニュアル、
  リポジトリの Website 欄（`gh repo edit --homepage URL`）
- ワークフローは公開URLを自動取得するため変更不要

> 実例: 本リポジトリは `poker_6max_rfi_range_grid` から `sixmax-range` に
> 改名済みです（旧 https://ririumu.github.io/poker_6max_rfi_range_grid/ は 404）。

### 独自ドメイン

Settings → Pages → Custom domain で設定します（DNS の CNAME 設定が必要）。
アプリは相対パスのみのため、ルート配信に変わってもそのまま動きます。
設定後は `LIVE_URL` を新しいドメインに変更してください。

---

## 7. ロールバック

```sh
git revert --no-commit <問題のコミット>
# VERSION は公開中より大きい値にする（revert で戻った古い名前や、
# 問題の版と同じキャッシュ名を再利用しないため）
python3 tools/bump_version.py --set rfi-vN
git commit -am "fix: roll back ..." && git push
```

VERSION を前進させることで、ロールバック版も既存ユーザーに確実に届きます。

---

## 8. トラブルシューティング

| 症状 | 原因と対処 |
|---|---|
| CI の **Bump guard** で失敗 | アプリを変えたのに VERSION が同じ。`make bump` → commit → push |
| CI の **Verify live site** で失敗 | 反映遅延なら `make verify` を再実行。続く場合は run のログで不一致ファイルを確認 |
| push しても run が起動しない | `.aidoc/`・`docs/`・`README.md`・`AGENTS.md` のみの変更。必要なら `gh workflow run deploy.yml` |
| `deploy-pages` が 404 / Pages 未設定エラー | 「2. 初期設定」で Source を GitHub Actions に |
| `Branch "main" is not allowed to deploy to github-pages` | Settings → Environments → github-pages の許可ブランチに `main` を追加 |
| Pages 有効化で 422（プラン非対応） | private リポジトリ。public にするか有料プランへ |
| デプロイ後も旧画面 | VERSION 未更新、または旧URLのアプリを使用中。新URLで開き直す。それでも駄目なら DevTools → Application → Unregister |
| Actions に Node.js 非推奨の警告 | 使用アクションのメジャー版を上げる（`gh api repos/actions/NAME/releases` で最新を確認） |

---

## 9. 参考: 現在のデプロイ状況

| 項目 | 値 |
|---|---|
| URL | https://ririumu.github.io/sixmax-range/ |
| リポジトリ | `ririumu/sixmax-range`（public） |
| 公開元 | GitHub Actions（`build_type: workflow`）、HTTPS 強制 |
| 使用アクション | checkout@v7 / configure-pages@v6 / upload-pages-artifact@v5 / deploy-pages@v5 |
| 公開中の VERSION | `rfi-v2`（CI の verify とローカル `make verify` で一致を確認） |
| 並行稼働 | Netlify（https://rfi-range-grid.netlify.app 、[マニュアル](DEPLOY_NETLIFY.md)） |
