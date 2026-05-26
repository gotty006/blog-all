"""
全サービスのSEO監視・自動リライトを実行するスクリプト。

各サービスのディレクトリに入り、seoMonitor.py を呼び出す。
新サービスは site_config.py に追加するだけで自動的に対象になる。

使い方:
  python3 seo_monitor_all.py report   # レポートのみ（WordPress更新なし）
  python3 seo_monitor_all.py update   # 自動更新実行

cron:
  0 3 * * * cd ~/dev/autoBlog && python3 _factory/seo_monitor_all.py update
"""
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from site_config import SITES

FACTORY_DIR = Path(__file__).parent
BASE_DIR = FACTORY_DIR.parent  # autoBlog/


def run_all(mode='report'):
    print(f"=== SEO Monitor ALL [{mode}] {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    for site in SITES:
        if not site.get('active'):
            print(f"[SKIP] {site['name']} (inactive)")
            continue

        site_dir = BASE_DIR / site['dir']
        seo_script = site_dir / 'seoMonitor.py'

        if not seo_script.exists():
            print(f"[SKIP] {site['name']} — seoMonitor.py が見つかりません: {seo_script}")
            continue

        print(f"\n--- {site['name']} ---")
        result = subprocess.run(
            ['python3', 'seoMonitor.py', mode],
            cwd=str(site_dir),
            capture_output=False,
            text=True,
        )
        if result.returncode != 0:
            print(f"  [ERROR] 終了コード: {result.returncode}")

    print("\n=== SEO Monitor ALL 完了 ===")


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'report'
    run_all(mode)
