# プロジェクト概要

## これは何か
テキサスホールデム初心者向けの 6-max RFI（Raise First In）レンジ学習 PWA。
ポジション別のオープンレンジを 13×13 ハンドグリッドで視覚的に学ぶ。

## 構成
- `index.html` — アプリ本体（CSS/JS インラインの単一ファイル）
- `manifest.webmanifest` — PWA マニフェスト（"id":"./" で識別子安定化）
- `sw.js` — Service Worker（プリキャッシュ・オフライン・更新管理）。
  プリキャッシュは `cache:"reload"` で HTTP キャッシュ迂回（GH Pages の max-age=600 対策）
- `icons/` — アイコン群（tools/make_icons.py で生成）
- `Makefile` — serve / icons / bump / check / bump-guard / dist / dist-pages /
  verify / deploy-netlify / clean
- `_headers` — Netlify・CF Pages 用ヘッダ（sw.js no-cache + セキュリティ）。GH Pages 公開物からは除外
- `.github/workflows/deploy.yml` — main push → dist-pages → bump-guard → Pages デプロイ → verify
- `tools/` — make_icons / bump_version / check_deploy / verify_live / deploy_netlify（全て stdlib）
- `.aidoc/` — 開発プロセス記録（_PLAN / AUDIT / REPORT / USERINPUT）

## 技術方針
- 依存ゼロ・ビルドなしの静的配信。相対パスのみでサブパス対応
- 公開物は `make dist`（Netlify 等）/ `make dist-pages`（GH Pages）が作る dist/ のみ
- デプロイ前は check_deploy.py（静的検証）と verify_live.py --bump-guard（公開版との比較）がゲート
- デプロイ後は verify_live.py が公開ファイルとローカルのバイト一致・開発ファイル非公開を検証
- リリースは `make bump` → push（GH Pages は自動）/ `make deploy-netlify`
- ローカル確認: `make serve`

## ドキュメント
- `README.md` — 概要・使い方・デプロイ概要
- `docs/DEPLOY_GITHUB_PAGES.md` — GitHub Pages デプロイ詳細マニュアル（iter5）
- `docs/DEPLOY_NETLIFY.md` — Netlify デプロイ詳細マニュアル（iter4、iter5 更新）
- `.aidoc/` — 開発プロセス記録

## 現状（Iteration 5 完了時点）
- **公開中（2系統・どちらも VERSION `rfi-v2`、`make verify` で一致確認済み）**:
  - GitHub Pages: https://ririumu.github.io/sixmax-range/（push で自動・CI で検証）
  - Netlify: https://rfi-range-grid.netlify.app（`make deploy-netlify` で手動、
    netlify.toml で git連携にも対応可）
- リポジトリ: https://github.com/ririumu/sixmax-range（public。旧名 poker_6max_rfi_range_grid）
  - 旧 Pages URL https://ririumu.github.io/poker_6max_rfi_range_grid/ は 404（転送なし）
- CI アクション: checkout@v7 / configure-pages@v6 / upload-pages-artifact@v5 / deploy-pages@v5（Node 24）
- Netlify サイトIDは `.netlify/state.json`（gitignore・ローカル状態。無ければ同名サイトを検索して再生成）
