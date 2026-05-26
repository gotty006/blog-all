import sys
import inspect
from submodule import _settings
from submodule import getInputDataSpreadsheet
from submodule import generateGptText
from submodule import generatePostHtml
from submodule import googleTranslate
from submodule import sendEyeCatchImage
from submodule import wordpressNewPost

def main():
    # コマンドライン引数の数をチェック  'video' or 'actress'
    if len(sys.argv) > 1:
        # コマンドライン引数が指定されている場合
        type = sys.argv[1]
    else:
        # コマンドライン引数が指定されていない場合
        type = 'video'  # デフォルト値
    print('Type: ' + type)

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # スプレッドシートからINPUT情報を取得
    sheet_id = _settings.spread_sheet_key
    input_data_list = getInputDataSpreadsheet.get_input_data_spreadsheet(sheet_id, type)

    # 1記事ごとに処理
    for index, input_data in enumerate(input_data_list):
        print("######################################################")
        print(f"# process start: {index+1} / {len(input_data_list)}")

        # 情報取得 webデータスクレイピング
        video_ranking_data = getInputDataSpreadsheet.get_ranking_data(input_data, index, type)

        # 投稿に使うレビュー要約テキストを作成
        gpt_text = generateGptText.generate_gpt_text(video_ranking_data, index, type)

        # 投稿に使うHTMLを作成
        if type == 'actress':
            generatePostHtml.generate_post_html_actress(video_ranking_data, gpt_text, index)
        else:
            generatePostHtml.generate_post_html_video(video_ranking_data, gpt_text, index)

        # URLを取得
        url = type + '-' + googleTranslate.translate_japanese_to_english(video_ranking_data['category']).lower().replace(' ','-').replace('--','-').replace('/', '') + video_ranking_data['year'] + '-' + video_ranking_data['month']

        # アイキャッチ画像の設定
        attachment_id = sendEyeCatchImage.send_eye_catch_image(video_ranking_data, url, index, type)

        # wordpressへ投稿
        new_post = wordpressNewPost.create_new_post(video_ranking_data, attachment_id, url, str(index), type)

        print("newPost Success. postId: " + new_post)

    print("Done: ", current_function_name)


if __name__ == '__main__':
    main()
