import inspect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

def get_text_with_selenium(url):
    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name, " - ", url)

    try:
        # Chromeブラウザのオプションを設定
        chrome_options = Options()
        # ヘッドレスモードでブラウザを起動する場合は以下をコメントアウト解除
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)

        # ページの読み込みを最大30秒待機
        driver.implicitly_wait(30)

        # 指定したURLを開く
        driver.get(url)

        # ページ全体のHTMLを取得
        page_source = driver.page_source

        # ブラウザを終了
        driver.quit()

        print("Done: ", current_function_name)
        return page_source


    except WebDriverException as e:
        # WebDriverに関するエラーが発生した場合の例外処理
        print(f"Selenium WebDriver Error: {e}")
        return None
    except Exception as e:
        # その他の例外処理
        print(f"Error: {e}")
        return None

if __name__ == '__main__':
    # テスト用のURL
    url = "https://www.rurubu.travel/theme/area/kanto/nasu_shiobara/?cid=1839115"  # ここにテスト用のURLを指定してください

    # URLから取得した文字列を出力
    result_text = get_text_with_selenium(url)
    if result_text:
        print(result_text)
    else:
        print("文字列を取得できませんでした。")

