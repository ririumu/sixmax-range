# AUDIT_5 作業ログ

## 調査
- `git remote`: origin = https://github.com/ririumu/sixmax-range.git
  → `gh repo view ririumu/poker_6max_rfi_range_grid` が sixmax-range を返す＝リネーム済み
- `gh api repos/ririumu/sixmax-range/pages`: build_type=workflow,
  html_url=https://ririumu.github.io/sixmax-range/, https_enforced=true
- 直近 run 40250082189（workflow_dispatch, 2026-10-26）success。annotation:
  - `Node.js 20 is deprecated ... actions/checkout@v4, actions/configure-pages@v5,
    actions/deploy-pages@v4, actions/upload-artifact@v4`
  - `ubuntu-latest label will migrate to Ubuntu 26`（情報のみ・make/python3 は継続利用可）
- 実測（curl）:
  - https://ririumu.github.io/sixmax-range/ 配下 index/sw/manifest/icons → 200
  - https://ririumu.github.io/poker_6max_rfi_range_grid/ → 404
  - https://ririumu.github.io/sixmax-range/_headers → 200（不要な露出）
  - sw.js 応答: `cache-control: max-age=600`（GH Pages 固定・変更不可）
- アクション最新版（`gh api repos/<action>/releases`）:
  checkout v7.0.1 / configure-pages v6.0.0 / upload-pages-artifact v5.0.0 /
  deploy-pages v5.0.1。upload-pages-artifact v4+ は dotfile を除外（dist に dotfile なし）

## 作業経過（branch -> commit -> merge）
1. `iter5/01-init`: USERINPUT 追記・_PLAN_5・AUDIT_5
2. `iter5/02-sw-cache`: SW の GitHub Pages キャッシュ対策 + VERSION rfi-v1→rfi-v2
   - sw.js install: `c.addAll(ASSETS.map(u => new Request(u, {cache:"reload"})))`
   - index.html: `register("sw.js", {updateViaCache:"none"})`（SW 本体の更新確認も明示的に HTTP キャッシュ迂回）
   - 再現テスト（Chrome headless + playwright-core、全応答 `Cache-Control: max-age=600` を
     付ける GH Pages 模擬サーバで `/sixmax-range/` サブパス配信。ビルドA配信→制御下で
     ビルドB を「デプロイ」→再訪問→新キャッシュ t-B 内の `./` を検査）:
     - 修正前コード: t-B に **ビルドA の index.html** がプリキャッシュ（3/3回）= 不具合再現
     - 修正後コード: t-B にビルドB（3/3回）= 解消
   - 観察: 初回訪問時は clients.claim() → controllerchange でアプリが1回自動リロードする
     （既存挙動・全ホスト共通・実害は軽微のため本イテレーションでは変更せず）
3. `iter5/03-verify-live`: `tools/verify_live.py` + `make verify` / `make bump-guard`
   - smoke: sw.js + ASSETS 全件が 200 かつローカルとバイト一致、開発ファイル7種が
     非公開（200 かつ同一バイトなら漏洩扱い。SPA フォールバックは誤検知しない）。10秒×12回リトライ
   - bump-guard: 公開版 VERSION == ローカル VERSION なのにアプリファイルが異なれば失敗
   - 実サイトでの検証結果:
     - A: ローカル rfi-v2 vs GH Pages rfi-v1 → ok（bump 済み）
     - B: VERSION を rfi-v1 に戻した状態（bump 忘れ再現）→ FAILED（sw.js/index.html 検出）exit 1
     - C: デプロイ済みコミット 87ee16f の worktree → ok（同一内容の再デプロイ）
     - D: 同 worktree で GH Pages smoke → `_headers: dev file is publicly served` を検出 exit 1
     - E: 同 worktree で Netlify smoke → 全件 ok（ホスト非依存であることを確認）
     - F: 404 サイト → 初回デプロイ扱いで ok / 名前解決不可 → warn で skip
4. `iter5/04-workflow`: deploy.yml 刷新 + `make dist-pages`
   - アクションを Node 24 版へ: checkout@v7 / configure-pages@v6 /
     upload-pages-artifact@v5 / deploy-pages@v5（release notes 確認: 破壊的変更は
     pull_request_target 系・dotfile 除外のみで本ワークフローに影響なし）
   - 工程: checkout → configure-pages(base_url) → `make dist-pages` →
     `make bump-guard`(LIVE_URL=base_url) → upload → deploy → `make verify`(LIVE_URL=page_url)
   - LIVE_URL は `env:` 経由で渡す（`run:` への式埋め込みを避ける）
   - concurrency cancel-in-progress: false（GitHub 公式スターター準拠）
   - paths-ignore: .aidoc/** docs/** README.md AGENTS.md（ドキュメントのみの push で再デプロイしない）
   - `make dist-pages` = dist から `_headers` を除去（8ファイル）。Netlify 用 `make dist` は従来通り
   - YAML 妥当性: ruby psych で steps 7件をパース確認（actionlint 未導入のため実 CI で最終確認）
5. push → CI → 公開検証、Netlify 同版化（`iter5/05-netlify-fresh-clone`）
   - `git push origin main`（87ee16f..143914f）→ run 40251269353 success（全ステップ ✓）
     - Node.js 20 deprecation annotation は解消。残る annotation は Ubuntu 26 移行告知のみ
     - CI 内 bump-guard: `VERSION rfi-v1 (live) -> rfi-v2 (local)` ok
     - CI 内 verify: 9 パス全一致・dev ファイル7種非公開（`_headers` 露出解消）
   - ローカルから `make verify` 再実行 → 一致
   - 実ブラウザ（Chrome headless）で https://ririumu.github.io/sixmax-range/ を検証:
     controller 取得、scope=/sixmax-range/、updateViaCache=none、cache=rfi-v2 に8資産、
     manifest id/start_url 解決先=/sixmax-range/、オフライン再読込でグリッド196セル表示、JSエラー0
   - Netlify 再デプロイで不具合発覚: `make deploy-netlify` → `POST /sites -> 422 subdomain must be unique`
     - 原因: 本作業ディレクトリは新規クローンで、gitignore 対象の `.netlify/state.json` が無い
       → 既存サイトを見つけられず同名サイト新規作成を試みていた
     - 修正: state.json / NETLIFY_SITE_ID が無いとき `GET /sites?filter=all&name=` で同名サイトを
       検索して再利用し state.json を再生成
     - 再実行 → 既存サイト（siteId 2311da9f…、AUDIT_3 と同一）へ ready
   - `make verify LIVE_URL=https://rfi-range-grid.netlify.app/` → rfi-v2 一致、
     sw.js `cache-control: no-cache`（_headers 適用継続）、実ブラウザでオフライン動作 ok
6. `iter5/06-pages-manual`: `docs/DEPLOY_GITHUB_PAGES.md` 新規 + 旧名参照の修正
   - 構成: 仕組み（CI 工程図）→ 初期設定 → 更新手順 → GH Pages 固有の制約と対策表 →
     検証（verify / bump-guard / ブラウザ）→ 改名・独自ドメイン → ロールバック →
     トラブルシュート → 現状
   - ロールバック手順: 当初 `revert → make bump` と書いたが、revert で戻った VERSION から
     bump すると問題版と同じキャッシュ名を再利用し得るため `bump_version.py --set` で
     公開中より大きい値を明示する手順に修正
   - 「セキュリティヘッダ不可は許容」の根拠確認: index.html に外部 URL・form/input なし
   - DEPLOY_NETLIFY.md: リポジトリ名、state.json 無しでも同名サイト再利用、`make verify`、
     422 の説明、デプロイ実績×4、GH Pages への相互リンク
   - README: GitHub Pages の公開 URL を新 URL に修正
   - 旧名 `poker_6max` の残存は GH Pages マニュアル内の改名事例のみ（意図的）。
     過去イテレーションの記録（AUDIT/REPORT 1〜3）は当時の証跡として改変しない
