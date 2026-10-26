# Iteration 5 計画: GitHub Pages 対応の完了

## ゴール
GitHub Pages を「push すれば安全に更新が届き、公開結果が自動検証される」
本番配信経路として完成させる。

## 調査結果（現状の課題）
- リポジトリが `poker_6max_rfi_range_grid` → `sixmax-range` にリネーム済み
  - 新 URL https://ririumu.github.io/sixmax-range/ は稼働（全リソース200）
  - 旧 URL は 404（GitHub はプロジェクト Pages のリネーム転送をしない）
  - README / OVERVIEW / DEPLOY_NETLIFY.md が旧 URL・旧リポジトリ名のまま
- CI 警告: `Node.js 20 is deprecated`（checkout@v4 / configure-pages@v5 /
  upload-pages-artifact@v3 / deploy-pages@v4 が Node 20 ターゲット）
  - 最新メジャー: checkout@v7 / configure-pages@v6 / upload-pages-artifact@v5 /
    deploy-pages@v5（いずれも Node 24）
- GitHub Pages はカスタムヘッダ不可。全ファイル `cache-control: max-age=600`
  - `_headers` は効かず、むしろ公開ファイルとして露出（/_headers が 200）
  - sw.js の `cache.addAll()` は HTTP キャッシュを経由するため、リリース直後
    の install で最大10分古い index.html をプリキャッシュし得る
    → cache-first のため次の VERSION まで古い版に固定される
- push で自動デプロイされるが `make bump` 忘れの検知がない
  （VERSION 据え置きで中身だけ変わると既存ユーザーに更新が届かない）
- デプロイ後の公開結果検証が手動（curl）のみ
- concurrency `cancel-in-progress: true` は進行中の本番デプロイを中断し得る
  （GitHub 公式スターターは false 推奨）

## 作業アイテム（直列チェックリスト）
- [x] 1. イテレーション初期化（USERINPUT追記・_PLAN_5・AUDIT_5）
- [ ] 2. SW の GitHub Pages キャッシュ対策（precache を `cache:'reload'`、
       register に `updateViaCache:'none'`）+ `make bump`
- [ ] 3. `tools/verify_live.py`（公開検証 smoke + bump忘れガード）+ `make verify`
- [ ] 4. ワークフロー刷新（Node 24 版アクション、`make dist-pages` で `_headers`
       除外、bump ガード → デプロイ → smoke、concurrency、paths-ignore）
- [ ] 5. push → CI 実行確認 → 公開検証（GH Pages）＋ Netlify も同版へ再デプロイ
- [ ] 6. `docs/DEPLOY_GITHUB_PAGES.md` マニュアル作成 + 旧URL/旧リポジトリ名の修正
- [ ] 7. README 見直し・OVERVIEW・AUDIT_5・REPORT_5 更新 + push

## 設計方針
- アプリは相対パスのみ（サブパス `/sixmax-range/` 配信に既に対応）を維持
- パッケージは引き続き Makefile が単一ソース（CI は make ターゲットを呼ぶだけ）
- verify_live.py は stdlib のみ・ホスト非依存（Netlify にも使える）
- 旧 URL のリダイレクト用リポジトリ作成は行わない（リネーム転送を壊すため）
