from googleapiclient.discovery import build # type: ignore
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from submodule import _settings
#import _settings

def request_google_index(url):
    # サービスアカウントキーのパス
    SERVICE_ACCOUNT_FILE = _settings.index_auth_file
    SCOPES = ["https://www.googleapis.com/auth/indexing"]

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    # サービスアカウントの認証情報を設定
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Google Indexing APIのサービスを構築
    service = build('indexing', 'v3', credentials=credentials)

    # インデックス登録のリクエストを作成
    body = {
        'url': url,
        'type': 'URL_UPDATED'
    }

    try:
        # リクエストを実行
        response = service.urlNotifications().publish(body=body).execute()

        # レスポンス結果表示
        if 'urlNotificationMetadata' in response:
            print("インデックスリクエスト成功:", response)
        else:
            print("インデックスリクエスト失敗:", response)
        
        return(0)
    
    except HttpError as e:
        error_code = e.resp.status
        error_message = e.content.decode()
        print(error_message)
        print(error_code)
        return(error_code)

if __name__ == '__main__':
    # 実行
    request_google_index("https://gotty.conohawing.com/d_513186/")
