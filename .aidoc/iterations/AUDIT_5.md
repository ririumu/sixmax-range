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
