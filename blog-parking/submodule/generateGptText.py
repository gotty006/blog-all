import inspect
import json
from submodule import executeGpt
from submodule import _settings

# 投稿に使うGPTテキストを作成
def generate_gpt_text(input_parking_data, index):
    # gpt 省略モードの場合は処理をスキップ
    if _settings.debug_flag['shrink_gpt_text_generation'] == True :
        return None

    # キャッシュからGPT文章を取得する場合    
    if _settings.debug_flag['use_cache_gpt_answer'] == True :
        # JSONファイルからデータを読み込む
        with open(_settings.gpt_text_data_dir + str(index) + '.json', 'r') as json_file:
            gpt_text = json.load(json_file)
        return gpt_text

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # parking
    gpt_text = {}
    parking_category = _settings.parking_category.keys()
    answer_history = {}
    for category in parking_category:
        print(f"parking category: {category}")

        # 解析対象のsource jsonをファイルアウトプット
        parking_data = input_parking_data[category][:7]
        with open(_settings.source_dir + 'gpt_source.json', 'w') as json_file:
            json.dump(parking_data, json_file, indent=2, ensure_ascii=False)

        # メタ情報を生成
        answers = []
        ## GPTで文章を生成
        for parking in parking_data[:5]:

            # すでに文章生成済みであれば、生成済みの文章を採用する
            if parking['name'] in answer_history:
                answers.append(answer_history[parking['name']])

                print("  answer (history): " + parking['name'])
                print(answer_history[parking['name']] + "\n")

                continue

            # 全体概要を生成
            prompt = f"""\
                100字以内で{parking['name']}について、他と比較した特徴を記載してください。
                制約事項:
                ・URL(httpから始まる文字列)を含んではならない。
                ・url,rank,distance,pricegap,addressについては言及しない。
                ・架空の地名や店名は使用しない。
                ・不確かな情報は出力しない。 """

            answer = executeGpt.execute_gpt_to_datafile(prompt, _settings.source_dir).response.replace("\n", "")
            answers.append(answer)

            # 生成済みの文章を履歴に格納する
            answer_history[parking['name']] = answer

            print("  answer: " + parking['name'])
            print(answer + "\n")
        
        gpt_text[category] = answers

    # 生成したgptテキストをキャッシュファイルに保存
    with open(_settings.gpt_text_data_dir + str(index) + '.json', 'w') as json_file:
        json.dump(gpt_text, json_file, indent=2, ensure_ascii=False) 

    print("Done: ", current_function_name)

    return gpt_text

