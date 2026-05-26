import os
import openai
from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import ServiceContext, SQLDatabase, VectorStoreIndex, PromptHelper, GPTVectorStoreIndex
from llama_index.core.indices.struct_store import SQLTableRetrieverQueryEngine
from llama_index.core.objects import SQLTableNodeMapping, ObjectIndex, SQLTableSchema
from llama_index.legacy import LLMPredictor

# Initialize DeepSeek client
deepseek_client = openai.OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")


#from llama_index import SimpleDirectoryReader
#from llama_index import LLMPredictor, ServiceContext, PromptHelper
#from llama_index import GPTVectorStoreIndex
#from llama_index.readers import BeautifulSoupWebReader

# ファイルを指定して要約
def execute_gpt_to_datafile(prompt, scraping_data_dir):
    # GPTの環境設定
    llm_predictor = LLMPredictor(llm=ChatOpenAI(
        #temperature=0,
        #model_name="gpt-3.5-turbo",
        #model_name="gpt-4",
        model="gpt-4o-mini",
        #max_tokens=512 #デフォルトは256
    ))

    prompt_helper = PromptHelper(
        num_output = 1024,
        chunk_overlap_ratio = 0.2,
        separator = "。"
    )
    #service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)

    # WEBデータを解析(GPT)
    documents = SimpleDirectoryReader(input_dir=scraping_data_dir).load_data()
    list_index = GPTVectorStoreIndex.from_documents(documents)
    query_engine = list_index.as_query_engine()

    # 要約の実行
    answer = query_engine.query(prompt)
    return answer


# フリーワードで文字列生成(chatGPT)
def execute_gpt_free_text(prompt):

    messages=[
    # {
    #     "role": "system",
    #     "content": "日本語で返答してください。"
    # },
    {
        "role": "user",
        "content": prompt
    },
    ]

    res = openai.chat.completions.create(
        #model="gpt-3.5-turbo",
        #model="gpt-4",
        model="gpt-4o-mini",
        #model="o1-mini",
        messages= messages,
    )
    #print(res)
    #response = res["choices"][0]["message"]["content"]
    response = res.choices[0].message.content
    return response


# フリーワードで文字列生成(deepseek)
def execute_deepseek_free_text(prompt):
    messages=[
    {
        "role": "system",
        "content": "日本語で返答してください。"
    },
    {
        "role": "user",
        "content": prompt
    },
    ]

    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )

    return response.choices[0].message.content


if __name__ == '__main__':
    prompt = """
下記の情報を使用して、おすすめのAV（アダルトビデオ）を紹介するWEBページのリード文を作成してください。
500文字程度で、閲覧者の興味をひくような内容の文章にしてください。

WEBページの基本情報：
今最も抜ける美少女系の人気AV(アダルトビデオ)を、口コミ情報と共にランキング形式で人気順に紹介します。
かわいいAV女優が出演する作品が上位にランクインしています！

ランキング情報：
1位 🥇田野憂「新人NO.1STYLE 田野憂AVデビュー L…」
2位 🥈白上咲花「超大型新人NO.1STYLE 白上咲花 AVデ…」
3位 🥉七海那美「新人 小麦肌の健やかGカップおひさま神BODY…」
4位 浅野こころ「キレかわ清楚の女子●生を我慢できずにメチャクチ…」
5位 兒玉七海「伝説の美少女 兒玉七海 復活デビュー～わたしが…」
6位 小野六花「人生初！ナマ挿入、そして中出し解禁！！ 小野六…」
7位 宮崎千尋「新人 1年かけてAV出演を決心した奇跡の逸材シ…」
8位 白上咲花「超大型新人 白上咲花の、初体験3本番。天才的A…」
9位 渚あいり「大きな瞳のド直球美少女 渚あいり 快感！初・体…」
10位 石川澪「引きニート喪女な妹のオナニーを目撃してしまった…」

"""

    text = execute_gpt_free_text(prompt)
    print('chatGPT output:') 
    print(text) 

    text = execute_deepseek_free_text(prompt)
    print('deepseek output:')
    print(text) 


# https://zenn.dev/umi_mori/books/chatbot-chatgpt/viewer/openai_chatgpt_api_python
# https://qiita.com/rio_0402/items/65cb7261f85099ec942a

# messages=[
# {
#     "role": "system",
#     "content": "日本語で返答してください。"
# },
# {
#     "role": "user",
#     "content": "What is AI?"
# },
#]

#    messages=[
#        {
#            "role": "system",
#            "content": "日本語で返答してください。"
#        },
#        {
#            "role": "user",
#            "content": "What is AI?"
#        },
#        {
#            "role": "assistant",
#            "content": "AIとは、人工知能(artificial intelligence)のことです。コンピューターやロボットなどに人間と同じように思考・判断・学習などの能力を与える技術や分野を示します。AI技術は、様々な分野で応用されており、自動運転車、言語処理、画像認識、医療など、私たちの生活に多大な影響を与えています。"
#        },
#        {
#            "role": "user",
#            "content": "英語に翻訳してください。"
#        },
#    ],