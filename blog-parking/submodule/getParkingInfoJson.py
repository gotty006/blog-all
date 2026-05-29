from submodule import seleniumWebScraping
import json
import re
import urllib.parse
import chardet
from time import sleep
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from bs4 import BeautifulSoup


# タグ情報を取得
def get_tag(area):
    # seleniumからareaで検索した結果のWEBデータを取得
    url = f"https://www.mapion.co.jp/s/q={urllib.parse.quote(area)}/"
    page_source = seleniumWebScraping.get_text_with_selenium(url)

    # BeautifulSoupを使ってHTMLを解析
    soup = BeautifulSoup(page_source, 'html.parser')

    # 最初に出現した class="floatL"のaタグの hrefの値を取得
    detail_path = soup.find('a', class_='floatL', title=area)
    if detail_path == None:
        detail_path = soup.find('a', class_='floatL')
    if detail_path == None:
        return ''

    # seleniumから検索結果から詳細に遷移した後のWEBデータを取得
    url = 'https://www.mapion.co.jp' + detail_path['href']
    page_source = seleniumWebScraping.get_text_with_selenium(url)

    # BeautifulSoupを使ってHTMLを解析
    soup = BeautifulSoup(page_source, 'html.parser')

    ## 市町村区を取得
    headline_title = soup.find('h1', class_='headline-title').get_text(strip=True)
    # 正規表現パターン
    pattern = r"(（.+都|道|府|県)(.+)）"
    # パターンにマッチする部分を抽出
    matches = re.search(pattern, headline_title)
    # マッチした部分があるか確認してから出力
    if matches:
        municipalities = matches.group(2)
        #print(municipalities)
    else:
        print("マッチする部分が見つかりませんでした。")
        exit(1)


    ## 路線名取得
    # class属性がlistsであるulタグの中の各liタグのテキストを取得
    target_ul_tag = soup.find('ul', class_='lists')
    if target_ul_tag:
        line_texts = [li.get_text(strip=True) for li in target_ul_tag.find_all('li')]
        #print(line_texts)
    else:
        print("指定した条件の要素が見つかりませんでした。")
        exit(1)
    
    tag = municipalities + ',' + ','.join(line_texts).replace('ＪＲ','JR')
    print(area + ': ' + tag)

    return tag

def log_filter(log_):
    return (
        # is an actual response
        log_["method"] == "Network.responseReceived"
        # and json
        and "json" in log_["params"]["response"]["mimeType"]
    )

# parking_json情報を取得
def get_parkinginfo_json(source_url_parking, weekend, weekday):
    # parking urls を生成
    # 正規表現パターン
    pattern = r'in_date=.*'
    # パターンにマッチする部分を削除
    base_url = re.sub(pattern, '', source_url_parking)
    input_parking_urls = {
        'dict_weekend_long' : base_url + "in_date=" + weekend + "&in_time=1100&minutes=360&as=1", 
        'dict_weekend_short' : base_url + "in_date=" + weekend + "&in_time=1100&minutes=60&as=1",
        'dict_weekday_long' : base_url + "in_date=" + weekday + "&in_time=1100&minutes=360&as=1",
        'dict_weekday_short' : base_url + "in_date=" + weekday + "&in_time=1100&minutes=60&as=1"
    }

    # parking_jsonをseleniumスクレイピングで取得
    dict_parking_json = {}
    for key,value in input_parking_urls.items():

        # make chrome log requests
        options = webdriver.ChromeOptions()
        options.set_capability("goog:loggingPrefs",{"performance": "ALL"})
        options.add_argument("--headless")
        driver = webdriver.Chrome( options=options)

        # リトライ処理（最大5回）
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                # fetch a site that does xhr requests
                print("URL: " + value)
                driver.get(value)
                sleep(5)  # wait for the requests to take place

                # 毎回ログを再取得して最初の target リクエストを見つける
                logs_raw = driver.get_log("performance")
                logs = [json.loads(lr["message"])["message"] for lr in logs_raw]

                target_log = next(
                    (log for log in filter(log_filter, logs)
                    if log["params"].get("response", {}).get("url") == 'https://api.pppark.com/search_v1.2'),
                    None
                )

                if not target_log:
                    raise ValueError("目的のレスポンスがログに見つかりませんでした。")

                request_id = target_log["params"]["requestId"]
                response_json = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                body = response_json['body']

                dict_parking_json[key] = json.loads(body)['result']['parkings']
                name = dict_parking_json[key][0]['name']
                print(f"index0 name: {name}")

                if '????' not in name:
                    break  # 成功 → 終了
                else:
                    print(f"文字化け検出: リトライ {attempt}")

            except Exception as e:
                print(f"リトライ {attempt} でエラー発生: {e}")
                if attempt == max_retries:
                    raise  # 最後の試行でも失敗 → 例外

            # if resp_url == 'https://api.pppark.com/search_v1.1':
            #     response_json = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            #     #print('===debug 1')
            #     #print( type(response_json))
            #     #print( json.dumps(response_json, indent=2))

            #     dict_parking_json[key] = json.loads(response_json['body'])['result']['parkings']
            #     #print('===debug 2')
            #     #print( type(dict_parking_json[key]))
            #     #print( json.dumps(dict_parking_json[key], indent=2))

    return dict_parking_json['dict_weekend_long'], dict_parking_json['dict_weekend_short'], dict_parking_json['dict_weekday_long'], dict_parking_json['dict_weekday_short']

