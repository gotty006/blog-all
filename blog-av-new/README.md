# blog-av-new — 新AVブログ（SEO戦略特化）

## SEO戦略

### ターゲットキーワード方向性

既存サイト（av-deview, av-shiroto, av-new等）と被らない領域を狙う。

| 狙う領域 | 具体的なキーワード例 | 既存サイトとの差別化 |
|---|---|---|
| 名作・傑作レビュー | 「AV 名作 おすすめ」「絶対見るべき AV」「AV 歴代ベスト」 | 既存は「新作」中心。過去作品で差別化 |
| 評価・口コミ系 | 「[作品名] 感想」「[作品名] 評価」 | レビュー特化コンテンツ |
| 年別・シーズン別 | 「2024年 AV ベスト」「2023年 おすすめ AV」 | 年別まとめで検索需要あり |
| ジャンル×評価 | 「熟女 AV おすすめ」「コスプレ AV 傑作」 | ジャンル特化×高評価の組み合わせ |

### 基本設計

- **記事タイプ**: 作品レビュー + おすすめリスト
- **記事数目標**: 初期30〜50件 → 毎日自動投稿
- **アフィリエイト**: FANZA（niconavicom-001）
- **GPTプロンプト**: 評価・見どころ中心の文体（既存サイトと差別化）

---

## セットアップ手順

### 1. ドメイン取得（カラフルボックス）

カラフルボックスのコントロールパネルから新ドメインを取得。
候補: `av-review.jp` / `avreview.net` / `av-best.jp` 等

### 2. WordPress インストール（カラフルボックス）

カラフルボックスの「WordPress簡単インストール」から新ドメインにWPをインストール。

### 3. _settings.py の設定

```python
wordpress_url = "https://[新ドメイン]/xmlrpc.php"
search_console_url = "https://[新ドメイン]/"
spread_sheet_key = "[新しいスプレッドシートID]"
debug_flag['do_not_post'] = False
debug_flag['do_not_index'] = False
active = True
```

### 4. Search Console 登録

1. Google Search Console に新ドメインを追加
2. DNS認証またはHTMLファイルで所有権確認
3. Service Account（config/index_service_account.json のメールアドレス）をSearch Consoleのユーザーとして追加（権限: フル）

### 5. Google Spreadsheet 作成

以下の列を持つシートを作成し、spread_sheet_keyに設定：
- `input` シート: content_id, title, url, status, category, tags

### 6. site_config.py の更新

`autoBlog/_factory/site_config.py` の blog-av-new エントリを更新：
```python
"wp_url": "https://[新ドメイン]/xmlrpc.php",
"sc_url": "https://[新ドメイン]/",
"active": True,
```

---

## 実行方法

```bash
# 初期記事生成（30件）
python3 sendNewPost.py

# SEO監視・リライト
python3 seoMonitor.py report    # レポートのみ
python3 seoMonitor.py update    # 自動リライト実行
```

---

## cron（ColorfulBox）

```cron
# 毎朝2時: 記事自動生成
0 2 * * * cd ~/dev/autoBlog/blog-av-new && python3 sendNewPost.py

# 毎朝3時: SEO監視
0 3 * * * cd ~/dev/autoBlog/blog-av-new && python3 seoMonitor.py update
```
