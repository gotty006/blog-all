import sys
import inspect
from submodule import _settings
from submodule import getParkingDataSpreadsheet
from submodule import generateGptText
from submodule import generatePostHtml
from submodule import wordpressNewPost
from submodule import sendEyecatchImage

def main():
    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # スプレッドシートからINPUT情報を取得
    sheet_id = _settings.spread_sheet_key
    input_parking_data_list = getParkingDataSpreadsheet.get_parking_data_spreadsheet(sheet_id)

    # parkingカテゴリーごとに処理
    for index, input_parking_data in enumerate(input_parking_data_list):

        # 投稿に使うMeta情報を作成
        gpt_text = generateGptText.generate_gpt_text(input_parking_data, index)

        # 投稿に使うHTMLを作成
        generatePostHtml.generate_post_html(input_parking_data, gpt_text, index)

        # アイキャッチ画像の設定
        attachment_id = sendEyecatchImage.send_eyecatch_image(input_parking_data, index)

        # wordpressへ投稿
        new_post = wordpressNewPost.create_new_post(input_parking_data, attachment_id, index)

        print("newPost Success. postId: ")
        print(new_post)

    print("Done: ", current_function_name)


if __name__ == '__main__':
    main()
