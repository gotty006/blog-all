# autoBlog タスク管理

最終更新: 2026-05-29

---

## 🔥 直近アクション（優先順）

### ① 既存サービスのcron設定（ColorfulBox）
```cron
OPENAI_API_KEY=sk-xxxx

0 2 * * *  cd ~/dev/autoBlog/blog-scene-av2 && python3 sendNewPost.py
0 2 * * 0  cd ~/dev/autoBlog/blog-vod-av2   && python3 sendNewPost.py all
0 3 * * *  cd ~/dev/autoBlog && python3 _factory/seo_monitor_all.py update
0 7 * * *  cd ~/dev/autoBlog && python3 _factory/daily_report.py
```

### ② vod.av2.jp ハウツー記事を投稿（コード実装済み・未実行）
```bash
cd ~/dev/autoBlog/blog-vod-av2 && python3 sendNewPost.py howto
```

### ③ 新サービス立ち上げ（ColorfulBoxで作業）
1. 7つのサブドメインを作成 → WordPress インストール
   - `onsen.niconavi.com`, `hotel.niconavi.com`, `golf.niconavi.com`
   - `camp.niconavi.com`, `gourmet.niconavi.com`, `movie.niconavi.com`
   - `parking.niconavi.com`
2. 各サービスの `submodule/_settings.py` を作成（sampleを参考）
3. APIキーを取得して設定

### ④ 新サービス起動コマンド（settings完成後）
```bash
cd ~/dev/autoBlog/blog-onsen   && python3 sendNewPost.py --all
cd ~/dev/autoBlog/blog-hotel   && python3 sendNewPost.py --all
cd ~/dev/autoBlog/blog-golf    && python3 sendNewPost.py --all
cd ~/dev/autoBlog/blog-camp    && python3 sendNewPost.py --all
cd ~/dev/autoBlog/blog-gourmet && python3 sendNewPost.py --all
cd ~/dev/autoBlog/blog-movie   && python3 sendNewPost.py --all
cd ~/dev/autoBlog/blog-parking && python3 sendNewPost.py
```

---

## 📋 サービス別タスク

### vod.av2.jp（VOD比較サイト）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | 初期記事15件投稿 | - |
| ✅ 完了 | ハウツー記事機能実装（登録/解約/無料体験 × 5サービス） | - |
| ✅ 完了 | 重複投稿防止ロジック | - |
| 🔴 未着手 | ハウツー記事を実際に投稿（`sendNewPost.py howto`） | 高 |
| 🔴 未着手 | アフィリエイトリンクの本番URLに差し替え | 高 |
| 🔴 未着手 | cron設定（毎週日曜2時） | 中 |

### scene.av2.jp（シーン特化ランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | 初期記事15件投稿 | - |
| ✅ 完了 | 50シーン拡張・優先度スケジューラー | - |
| ✅ 完了 | 日替わりFANZAソート実装 | - |
| ✅ 完了 | サムネイル自動設定 | - |
| 🔴 未着手 | cron設定（毎日2時） | 高 |

### blog-onsen（温泉ランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | sendNewPost.py 実装（20ターゲット・楽天API） | - |
| 🔴 未着手 | ColorfulBoxでWPサイト作成（onsen.niconavi.com） | 高 |
| 🔴 未着手 | 楽天RWSアプリID取得 → _settings.py作成 | 高 |
| 🔴 未着手 | 初期記事投稿（`--all`） | 中 |
| 🔴 未着手 | cron設定 | 低 |

### blog-hotel（ホテルランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | sendNewPost.py 実装（20ターゲット・楽天API） | - |
| 🔴 未着手 | ColorfulBoxでWPサイト作成（hotel.niconavi.com） | 高 |
| 🔴 未着手 | 楽天RWSアプリID取得 → _settings.py作成 | 高 |
| 🔴 未着手 | 初期記事投稿（`--all`） | 中 |
| 🔴 未着手 | cron設定 | 低 |

### blog-golf（ゴルフ場ランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | sendNewPost.py 実装（15ターゲット・楽天GORA API） | - |
| 🔴 未着手 | ColorfulBoxでWPサイト作成（golf.niconavi.com） | 高 |
| 🔴 未着手 | 楽天RWSアプリID取得 → _settings.py作成 | 高 |
| 🔴 未着手 | 初期記事投稿（`--all`） | 中 |
| 🔴 未着手 | cron設定 | 低 |

### blog-camp（キャンプ場ランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | sendNewPost.py 実装（15ターゲット・楽天Travel API） | - |
| 🔴 未着手 | ColorfulBoxでWPサイト作成（camp.niconavi.com） | 高 |
| 🔴 未着手 | 楽天RWSアプリID取得 → _settings.py作成 | 高 |
| 🔴 未着手 | 初期記事投稿（`--all`） | 中 |
| 🔴 未着手 | cron設定 | 低 |

### blog-gourmet（グルメランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | sendNewPost.py 実装（15ターゲット・Hotpepper API） | - |
| 🔴 未着手 | ColorfulBoxでWPサイト作成（gourmet.niconavi.com） | 高 |
| 🔴 未着手 | Hotpepper APIキー取得 → _settings.py作成 | 高 |
| 🔴 未着手 | 初期記事投稿（`--all`） | 中 |
| 🔴 未着手 | cron設定 | 低 |

### blog-movie（映画ランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | sendNewPost.py 実装（15ターゲット・TMDB API） | - |
| 🔴 未着手 | ColorfulBoxでWPサイト作成（movie.niconavi.com） | 高 |
| 🔴 未着手 | TMDB APIキー取得（無料・要登録）→ _settings.py作成 | 高 |
| 🔴 未着手 | 初期記事投稿（`--all`） | 中 |
| 🔴 未着手 | cron設定 | 低 |

### blog-parking（駐車場ランキング）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | sendNewPost.py 移植（aiBlogから） | - |
| 🔴 未着手 | ColorfulBoxでWPサイト作成（parking.niconavi.com） | 高 |
| 🔴 未着手 | _settings.py作成（spread_sheet_key等を設定） | 高 |
| 🔴 未着手 | wordpress_urlをparking.niconavi.comに変更 | 高 |
| 🔴 未着手 | 初期記事投稿 | 中 |

### _factory（共通基盤）

| ステータス | タスク | 優先度 |
|---|---|---|
| ✅ 完了 | site_config.py に全9サービス登録 | - |
| ✅ 完了 | daily_report.py・seo_monitor_all.py 実装 | - |
| ✅ 完了 | blog-all.git で全サービス統合管理 | - |
| 🔴 未着手 | 新サービスをactive:True に切り替え（WP作成後） | 高 |
| 🔴 未着手 | daily_report.py cronテスト | 中 |

---

## 🔑 APIキー取得先

| サービス | API | URL | 対象 |
|---|---|---|---|
| 楽天RWS | アプリID | https://webservice.rakuten.co.jp/ | onsen/hotel/golf/camp |
| Hotpepper | APIキー | https://webservice.recruit.co.jp/ | gourmet |
| TMDB | APIキー（無料） | https://www.themoviedb.org/settings/api | movie |

---

## 🚀 cron全サービス設定（最終形）

```cron
OPENAI_API_KEY=sk-xxxx

# 既存AV系
0 2 * * *  cd ~/dev/autoBlog/blog-scene-av2 && python3 sendNewPost.py
0 2 * * 0  cd ~/dev/autoBlog/blog-vod-av2   && python3 sendNewPost.py all

# 新サービス（毎日15件ローテ）
0 3 * * *  cd ~/dev/autoBlog/blog-onsen   && python3 sendNewPost.py
0 3 * * *  cd ~/dev/autoBlog/blog-hotel   && python3 sendNewPost.py
0 4 * * *  cd ~/dev/autoBlog/blog-golf    && python3 sendNewPost.py
0 4 * * *  cd ~/dev/autoBlog/blog-camp    && python3 sendNewPost.py
0 5 * * *  cd ~/dev/autoBlog/blog-gourmet && python3 sendNewPost.py
0 5 * * *  cd ~/dev/autoBlog/blog-movie   && python3 sendNewPost.py

# 共通
0 6 * * *  cd ~/dev/autoBlog && python3 _factory/seo_monitor_all.py update
0 7 * * *  cd ~/dev/autoBlog && python3 _factory/daily_report.py
```

---

## 📝 運用メモ

- 記事は重複チェック後に上書き更新（同テーマを毎月最新データで更新）
- WordPress認証: `niconavi.com@gmail.com`
- FANZA affiliate_id: `niconavicom-999`（API用）、`niconavicom-001`（リンク用）
- 楽天アフィリエイトID: 要設定（affiliate tag）
- colorfulbox で日本レンタル → サブドメイン追加 → WordPress一発インストール
