"""
全サービス横断 朝レポート生成スクリプト。

使い方:
  python3 daily_report.py              # レポート生成 + SESSION.mdに書き込み
  python3 daily_report.py --no-session # SESSION.md書き込みをスキップ

cron:
  0 7 * * * cd ~/dev/autoBlog && python3 _factory/daily_report.py
"""
import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path

# _factory/shared をパスに追加
sys.path.insert(0, str(Path(__file__).parent / 'shared'))
sys.path.insert(0, str(Path(__file__).parent))

from site_config import get_active_sites
import search_console

FACTORY_DIR = Path(__file__).parent
REPORT_DIR = FACTORY_DIR / 'data' / 'reports'
SESSION_MD = Path(__file__).parent.parent.parent / 'CLAUDE_CODE' / 'SESSION.md'
BASE_DIR = FACTORY_DIR.parent  # autoBlog/


def generate_report(write_session=True):
    today = date.today().isoformat()
    lines = [
        f"# 朝レポート {today}",
        f"生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## サービス別パフォーマンス（過去28日）",
        "",
    ]

    all_ok = True
    site_summaries = []

    for site in get_active_sites():
        sc_url = site.get('sc_url', '')
        if not sc_url:
            lines.append(f"### ⚠️ {site['name']} — Search Console URL未設定")
            lines.append("")
            continue

        # index_auth はサービスdir or 絶対パスで解決
        auth_path = site.get('index_auth', '')
        if not os.path.isabs(auth_path):
            service_dir = BASE_DIR / site.get('dir', '')
            auth_file = str(service_dir / auth_path) if service_dir.exists() else str(FACTORY_DIR / auth_path)
        else:
            auth_file = auth_path

        # レガシーサイトは _factory からの相対パスで解決
        if not os.path.exists(auth_file):
            # レガシーサイトは ../aiBlog/ 配下
            auth_file = str(FACTORY_DIR.parent / auth_path.lstrip('../'))

        if not os.path.exists(auth_file):
            lines.append(f"### ⚠️ {site['name']} — Service Account ファイルが見つかりません: {auth_file}")
            lines.append("")
            all_ok = False
            continue

        rows = search_console.fetch_page_performance(auth_file, sc_url)
        if not rows:
            lines.append(f"### ⚠️ {site['name']} ({sc_url})")
            lines.append("  - データなし（Search Console権限を確認してください）")
            lines.append("")
            all_ok = False
            continue

        pages = search_console.aggregate_by_page(rows)
        summary = search_console.summarize(pages)
        qw = search_console.find_quick_wins(pages)
        low_ctr = search_console.find_low_ctr(pages)

        lines.append(f"### ✅ {site['name']} ({sc_url})")
        lines.append(f"- ページ数: {summary['total_pages']}")
        lines.append(f"- クリック: {summary['total_clicks']:,} / インプレッション: {summary['total_impressions']:,}")
        lines.append(f"- 平均CTR: {summary['avg_ctr']}% / 平均順位: {summary['avg_position']}")
        lines.append(f"- クイックウィン候補: {len(qw)}件 / 低CTR: {len(low_ctr)}件")

        if qw:
            lines.append("")
            lines.append("  **クイックウィン TOP5（リライト推奨）:**")
            for p in sorted(qw, key=lambda x: x['impressions'], reverse=True)[:5]:
                lines.append(f"  - 順位{p['avg_position']:4.1f} CTR{p['ctr']:4.1f}% imp{p['impressions']:5d} | {p['page']}")

        lines.append("")
        site_summaries.append({
            'name': site['name'],
            'clicks': summary['total_clicks'],
            'impressions': summary['total_impressions'],
            'quick_wins': len(qw),
        })

    # サマリーセクション
    lines.append("---")
    lines.append("## 全体サマリー")
    total_clicks = sum(s['clicks'] for s in site_summaries)
    total_impressions = sum(s['impressions'] for s in site_summaries)
    lines.append(f"- 合計クリック（28日）: {total_clicks:,}")
    lines.append(f"- 合計インプレッション: {total_impressions:,}")
    lines.append(f"- 全体CTR: {round(total_clicks / total_impressions * 100, 2) if total_impressions else 0}%")
    lines.append(f"- クイックウィン合計: {sum(s['quick_wins'] for s in site_summaries)}件")
    lines.append("")
    lines.append("---")
    lines.append(f"*by autoBlog/_factory/daily_report.py*")

    report = '\n'.join(lines)

    # レポートファイル保存
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"{today}.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"レポート保存: {report_path}")

    # SESSION.md に書き込み
    if write_session and SESSION_MD.exists():
        _write_to_session(today, site_summaries, report_path)

    return report


def _write_to_session(today, site_summaries, report_path):
    """SESSION.mdの「## 朝レポート」セクションを上書きする。"""
    content = SESSION_MD.read_text(encoding='utf-8')
    section_header = '## 📊 朝レポート（自動更新）'

    new_section_lines = [
        section_header,
        f"最終更新: {today}  [詳細レポート]({report_path})",
        "",
    ]
    for s in site_summaries:
        new_section_lines.append(
            f"- **{s['name']}**: {s['clicks']:,}クリック / QW{s['quick_wins']}件"
        )
    new_section_lines.append("")

    new_section = '\n'.join(new_section_lines)

    if section_header in content:
        # 既存セクションを置換
        start = content.index(section_header)
        # 次の ## セクションまでを探す
        next_section = content.find('\n## ', start + len(section_header))
        if next_section == -1:
            updated = content[:start] + new_section
        else:
            updated = content[:start] + new_section + '\n' + content[next_section:]
    else:
        # 末尾に追加
        updated = content.rstrip() + '\n\n' + new_section

    SESSION_MD.write_text(updated, encoding='utf-8')
    print(f"SESSION.md 更新完了")


if __name__ == '__main__':
    write_session = '--no-session' not in sys.argv
    report = generate_report(write_session=write_session)
    print("\n--- REPORT PREVIEW ---")
    print(report[:1000])
