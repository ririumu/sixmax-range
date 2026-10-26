# REPORT_5 イテレーション報告書

## 概要
GitHub Pages を本番配信経路として完成させた。リポジトリ改名に伴う URL の整理、
GitHub Pages 固有のキャッシュ問題の修正、CI のアクション更新、
デプロイ前後の自動検証を整備し、実サイトとブラウザで動作を確認した。

## 成果
- **SW の GitHub Pages キャッシュ対策**（rfi-v1 → rfi-v2）
  - GH Pages は全ファイル `max-age=600` 固定でヘッダ変更不可。従来の `cache.addAll()` は
    HTTP キャッシュ経由のため、リリース直後に旧 index.html をプリキャッシュし得た
  - `cache:"reload"` でのプリキャッシュ + `updateViaCache:"none"` で解消
  - GH Pages 模擬サーバ + Chrome headless で修正前の不具合を再現（3/3）、修正後に解消（3/3）
- **tools/verify_live.py**（`make verify` / `make bump-guard`、ホスト共通）
  - verify: 全アプリファイルが 200 かつローカルとバイト一致、開発ファイル7種が非公開
  - bump-guard: VERSION 据え置きのままアプリが変わった公開を阻止
- **ワークフロー刷新**
  - Node 24 版アクションへ更新 → Node.js 20 非推奨警告を解消
  - `make dist-pages` で `_headers` を公開物から除外（GH Pages で露出していた）
  - bump-guard → deploy → verify を CI に組み込み
  - 進行中のデプロイを中断しない concurrency、ドキュメントのみの push は再デプロイしない
- **tools/deploy_netlify.py**: state.json の無い新しいクローンでも同名の既存サイトを再利用
  （今回のクローンで 422 エラーとして発覚・修正）
- **docs/DEPLOY_GITHUB_PAGES.md** 新規作成、DEPLOY_NETLIFY.md・README を新リポジトリ名・新機能に合わせて更新

## 検証結果
- CI run 40251269353: 全ステップ success（bump-guard ok、verify 一致）
- `make verify`（GH Pages / Netlify とも）: 9 パス一致・開発ファイル非公開
- 実ブラウザ（Chrome headless）で GH Pages 公開版を確認: scope `/sixmax-range/`、
  cache `rfi-v2` に8資産、オフライン再読込でグリッド表示、JS エラー 0
- verify_live の異常系: bump 忘れ再現で FAILED、旧デプロイで `_headers` 露出を検出

## 残課題・運用メモ
- 旧 URL（poker_6max_rfi_range_grid）でインストールされた PWA は更新を受け取れない。
  旧名で転送用リポジトリを作るとリポジトリ改名の転送が壊れるため実施せず。
  必要なら利用者に新 URL での入れ直しを案内
- GitHub Pages ではセキュリティヘッダ（nosniff / X-Frame-Options 等）を付けられない。
  外部リソース・入力フォームのない静的アプリのため許容。必要なら Netlify を正とする
- 初回訪問時、`clients.claim()` → `controllerchange` でページが1回自動リロードされる
  （既存挙動・全ホスト共通）。気になるなら、既存 controller がある場合のみリロードする改修候補
- `ubuntu-latest` は Ubuntu 26 へ移行中（告知のみ。make/python3 のみ使用のため影響なし見込み）
