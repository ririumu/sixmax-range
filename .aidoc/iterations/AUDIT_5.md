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
