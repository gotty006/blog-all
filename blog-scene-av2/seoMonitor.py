"""
SEO監視 + 記事自動更新スクリプト

使い方:
  # レポートのみ（WordPress更新なし）
  python3 seoMonitor.py report [site_type]

  # クイックウィン記事を自動更新
  python3 seoMonitor.py update [site_type]

  site_type: video / single_list / shiroto_list / jk_list / dojin_list 等
             省略時は全サイトをレポート出力

例:
  python3 seoMonitor.py report single_list
  python3 seoMonitor.py update single_list
"""
import sys
import os
import json
import csv
from datetime import datetime

from submodule import _settings
from submodule import getSearchConsoleData
from submodule import updateWordpressPost
from submodule import requestGoogleIndex

# --- GPT呼び出し（軽量版） ---
import openai

def _gpt_rewrite(original_content, top_queries, page_url):
    """Search Consoleのクエリをヒントに本文をリライトする。"""
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    query_str = '、'.join(top_queries[:5])
    prompt = f"""\
以下はAVレビューブログの記事本文（HTML）です。
検索クエリ「{query_str}」で検索しているユーザーに対してより役立つ内容になるよう、
本文を自然な日本語でリライトしてください。

制約:
- HTMLタグ構造は維持してください
- 200〜400字程度を目安に内容を充実させてください
- ネガティブな表現は避けてください
- 元の内容と大きくかけ離れないようにしてください

本文:
{original_content[:3000]}
"""
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1000,
    )
    return response.choices[0].message.content.strip()


# --- レポート出力 ---
def _save_report(site_type, quick_wins, low_ctr_pages):
    os.makedirs('data/seoReport', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    filepath = f'data/seoReport/{site_type}_{ts}.csv'

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category', 'page', 'clicks', 'impressions', 'ctr', 'avg_position', 'top_queries'])
        for p in quick_wins:
            writer.writerow(['quick_win', p['page'], p['clicks'], p['impressions'],
                             p['ctr'], p['avg_position'], ' / '.join(p['top_queries'])])
        for p in low_ctr_pages:
            writer.writerow(['low_ctr', p['page'], p['clicks'], p['impressions'],
                             p['ctr'], p['avg_position'], ' / '.join(p['top_queries'])])

    print(f"レポート保存: {filepath}")
    return filepath


# --- メイン処理 ---
def run(mode, site_type=None):
    cfg = _settings.seo_monitor
    sites = _settings.search_console_sites

    target_sites = (
        {site_type: sites[site_type]} if site_type and site_type in sites else sites
    )

    for s_type, site_url in target_sites.items():
        print(f"\n=== {s_type} ({site_url}) ===")

        rows = getSearchConsoleData.fetch_page_performance(site_url)
        if not rows:
            print("  データなし（Search Consoleの権限設定を確認してください）")
            continue

        pages = getSearchConsoleData.aggregate_by_page(rows)
        quick_wins = getSearchConsoleData.find_quick_wins(
            pages,
            min_impressions=cfg['quick_win_min_impressions'],
            pos_min=cfg['quick_win_pos_min'],
            pos_max=cfg['quick_win_pos_max'],
        )
        low_ctr = getSearchConsoleData.find_low_ctr(
            pages,
            ctr_threshold=cfg['low_ctr_threshold'],
            min_impressions=cfg['low_ctr_min_impressions'],
        )

        print(f"  全ページ: {len(pages)} / クイックウィン候補: {len(quick_wins)} / 低CTR: {len(low_ctr)}")

        # 上位N件を表示
        top_n = cfg['report_top_n']
        print(f"\n  【クイックウィン TOP{min(top_n, len(quick_wins))}】")
        for p in sorted(quick_wins, key=lambda x: x['impressions'], reverse=True)[:top_n]:
            print(f"    pos={p['avg_position']:5.1f} CTR={p['ctr']:4.1f}% imp={p['impressions']:5d} | {p['page']}")

        _save_report(s_type, quick_wins, low_ctr)

        if mode == 'update':
            _update_articles(s_type, quick_wins + low_ctr, cfg['dry_run'])


def _update_articles(site_type, target_pages, dry_run):
    wp_url = _settings.wordpress_url_list.get(site_type)
    if not wp_url:
        print(f"  WordPress URL未設定: {site_type}")
        return

    updated = 0
    for p in target_pages[:5]:  # 一度に最大5件
        page_url = p['page']
        print(f"\n  更新対象: {page_url}")

        post = updateWordpressPost.get_post_by_url(page_url, wordpress_url=wp_url)
        if not post:
            print(f"  → 投稿が見つかりません")
            continue

        new_content = _gpt_rewrite(post.content, p['top_queries'], page_url)

        if dry_run:
            print(f"  → [DRY RUN] 更新スキップ（{len(new_content)}文字生成）")
            continue

        ok = updateWordpressPost.update_post_content(post.id, new_content, wordpress_url=wp_url)
        if ok:
            requestGoogleIndex.request_google_index(page_url)
            updated += 1

    print(f"\n  更新完了: {updated}件")


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'report'
    site = sys.argv[2] if len(sys.argv) > 2 else None
    run(mode, site)
