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
