"""
WordPress 既存記事を更新するモジュール。
"""
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPost, EditPost, GetPosts
from submodule import _settings


def _client(wordpress_url=None):
    url = wordpress_url or _settings.wordpress_url
    return Client(url, _settings.wordpress_id, _settings.wordpress_pw)


def get_post_by_url(page_url, wordpress_url=None):
    """
    記事URLのスラッグからWordPress投稿データを取得する。
    例: https://1.av-deview.com/smuc124/ → slug='smuc124' で検索
    Returns: WordPressPost or None
    """
    from urllib.parse import urlparse
    slug = urlparse(page_url).path.strip('/')
    if not slug:
        return None

    wp = _client(wordpress_url)
    fetched = wp.call(GetPosts({'number': 1, 'post_status': 'publish', 'name': slug}))
    return fetched[0] if fetched else None


def update_post_content(post_id, new_content, new_title=None, wordpress_url=None):
    """
    指定IDの記事のコンテンツ（本文）を更新する。
    Returns: bool（成功/失敗）
    """
    wp = _client(wordpress_url)
    post = wp.call(GetPost(post_id))
    if not post:
        print(f"投稿ID {post_id} が見つかりません")
        return False

    post.content = new_content
    if new_title:
        post.title = new_title
    post.thumbnail = None  # EditPost時にサムネイルIDエラーを防ぐ

    result = wp.call(EditPost(post_id, post))
    print(f"記事更新 {'成功' if result else '失敗'}: post_id={post_id}")
    return result


def get_recent_posts(post_type_key, number=50, wordpress_url=None):
    """
    最近の投稿を取得する。
    Returns: list of WordPressPost
    """
    wp = _client(wordpress_url)
    return wp.call(GetPosts({'number': number, 'post_status': 'publish'}))
