# autoBlog Factory — 共通管理基盤

## 概要

`autoBlog/` はアフィリエイトブログを量産・自動運用するためのファクトリー基盤。  
1サービス = 1ディレクトリ = 1GitHubリポジトリ で管理する。

## ディレクトリ構成

```
autoBlog/
├── _factory/               # 共通管理（このディレクトリ）
│   ├── README.md           # このファイル
│   ├── site_registry.md    # 全サービス台帳
│   ├── daily_report.py     # 全サービス横断の朝レポート生成（毎朝7時cron）
│   ├── seo_monitor_all.py  # 全サービスSEO一括監視（毎朝3時cron）
│   └── shared/             # 全サービス共通Pythonモジュール
│       ├── wordpressNewPost.py
│       ├── getSearchConsoleData.py
│       ├── requestGoogleIndex.py
│       ├── executeGpt.py
│       └── getInputDataSpreadsheet.py
│
├── blog-av-new/            # 第1弾: 新AVブログ（SEO戦略特化）
├── blog-hotel-new/         # 第2弾以降（随時追加）
└── ...
```

## 共通モジュール (shared/)

各サービスの `submodule/` からは `_factory/shared/` を参照する（symlinkまたはimport path調整）。

| ファイル | 機能 |
|---|---|
| `wordpressNewPost.py` | WordPress XML-RPC 記事投稿・更新・画像アップロード |
| `getSearchConsoleData.py` | Google Search Console データ取得・集計・分析 |
| `requestGoogleIndex.py` | Google Indexing API でURLをインデックスリクエスト |
| `executeGpt.py` | OpenAI / DeepSeek API 呼び出し |
| `getInputDataSpreadsheet.py` | Google Spreadsheet 読み書き |

## cron 設定（ColorfulBox）

```cron
# 毎朝2時: 全サービスの記事自動生成（各サービスのsendNewPost.pyを呼び出す）
0 2 * * * cd ~/dev/autoBlog && python3 _factory/run_all_generate.py

# 毎朝3時: 全サービスSEO監視・自動リライト
0 3 * * * cd ~/dev/autoBlog && python3 _factory/seo_monitor_all.py

# 毎朝7時: 朝レポート生成 → SESSION.mdに書き込み
0 7 * * * cd ~/dev/autoBlog && python3 _factory/daily_report.py
```

## 新サービスの立ち上げ方

Claude Codeに「新サービス: [ジャンル名]」と指示するだけで以下を半自動実行：

1. SEO戦略提案（ユーザー承認）
2. ドメイン候補提示 → カラフルボックスで取得（手動）
3. WordPress設定・ディレクトリ作成
4. Search Console登録手順提示
5. 初期記事30〜50件自動生成・投稿
6. site_registry.md に追加 → 翌日から朝レポートに追加

## Google Spreadsheet「BLOG_FACTORY」

スプレッドシートID: (作成後に記載)

| シート名 | 用途 |
|---|---|
| `sites` | 全サービス一覧・ステータス管理 |
| `daily_stats` | 日次パフォーマンス（クリック/インプレッション） |
| `autorun` | 自動実行制御フラグ |
