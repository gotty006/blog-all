# autoBlog タスク管理

最終更新: 2026-05-27

---

## 🔥 直近アクション

- [ ] **vod.av2.jp ハウツー記事を実際に投稿**（コード実装済み・未実行）
  ```
  cd ~/dev/autoBlog/blog-vod-av2 && python3 sendNewPost.py howto
  ```
- [ ] **アフィリエイトURLを本番に差し替え**（blog-vod-av2/submodule/_settings.py の affiliate_url）
- [ ] **ColorfulBoxでcron設定**（全サイト自動化の最終ステップ）
  ```
  0 2 * * *  cd ~/dev/autoBlog/blog-scene-av2 && python3 sendNewPost.py
  0 2 * * *  cd ~/dev/autoBlog/blog-vod-av2   && python3 sendNewPost.py all
  0 3 * * *  cd ~/dev/autoBlog && python3 _factory/seo_monitor_all.py update
  0 7 * * *  cd ~/dev/autoBlog && python3 _factory/daily_report.py
  ```

---

## 📋 サービス別タスク

### vod.av2.jp（VOD比較サイト）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | 初期記事15件投稿（サービスレビュー5件＋比較10件） | - |
| ✅ 完了 | Google Indexing API 登録（15件） | - |
| ✅ 完了 | ハウツー記事機能実装（登録/解約/無料体験 × 5サービス = 15記事） | - |
| 🔴 未着手 | ハウツー記事を実際に投稿（`sendNewPost.py howto`） | 高 |
| 🔴 未着手 | アフィリエイトリンクの本番URLに差し替え（現在はプレースホルダー） | 高 |
| 🔴 未着手 | cron設定（毎朝2時・自動実行） | 中 |
| 🟡 後回し | Google Analytics 設置 | 低 |
| 🟡 後回し | AdSense 申請 | 低 |

### scene.av2.jp（シーン特化ランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | 初期記事15件投稿（全シーン） | - |
| ✅ 完了 | Google Indexing API 登録（15件） | - |
| ✅ 完了 | 重複投稿防止ロジック実装 | - |
| ✅ 完了 | 50シーンに拡張・優先度スケジューラー実装 | - |
| ✅ 完了 | 日替わりFANZAソート（新着/人気/評価/注目）実装 | - |
| 🔴 未着手 | cron設定（毎朝2時・自動実行） | 高 |
| 🔴 未着手 | サムネイル画像のWordPressへのアップロード対応 | 中 |
| 🟡 後回し | Google Analytics 設置 | 低 |
| 🟡 後回し | AdSense 申請 | 低 |

### _factory（共通基盤）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | site_config.py・daily_report.py・seo_monitor_all.py 実装 | - |
| ✅ 完了 | shared/ モジュール整備 | - |
| ✅ 完了 | blog-all.git で全サービス統合管理 | - |
| 🔴 未着手 | daily_report.py → SESSION.md 自動書き込みのcronテスト | 中 |
| 🟡 後回し | Google Spreadsheet「BLOG_FACTORY」作成（日次stats管理） | 低 |

---

## 🚀 新サービス候補（追加検討）

| ジャンル | URL候補 | 優先度 | メモ |
|---|---|---|---|
| 温泉旅館ランキング | onsen.av2.jp 等 | 中 | 楽天/一休アフィリエイト・SEO競合低め |
| キャンプ場ランキング | camp.niconavi.com 等 | 低 | ファミリー層・季節変動あり |
| AV名作レビュー（blog-av-new） | TBD | 低 | ドメイン未取得 |

新サービスを追加する場合は Claude Code に「新サービス: [ジャンル名]」と指示。

---

## 📝 運用ルール

- 記事は重複チェック後に**上書き更新**（同じシーンを毎日最新FANZAデータで更新）
- FANZA affiliate_id: `niconavicom-999`（APIリクエスト用）
- WordPress 認証: `niconavi.com@gmail.com`
- cron が動き出したら毎朝7時に `_factory/daily_report.py` が SESSION.md を更新
