from llama_index.core import SimpleDirectoryReader, ServiceContext, PromptHelper, GPTVectorStoreIndex
from llama_index.llms.openai import OpenAI

# ファイルを指定して要約
def execute_gpt_to_datafile(prompt, scraping_data_dir):
    # GPTの環境設定（ChatOpenAI の代わりに llama-index 側の OpenAI を使用）
    llm = OpenAI(
        #model="gpt-4",
        model="gpt-4o-mini",
        max_tokens=512,
        temperature=0.0  # 必要なら調整
    )

    prompt_helper = PromptHelper(
        num_output=1024,
        chunk_overlap_ratio=0.2,
        separator="。"
    )

    service_context = ServiceContext.from_defaults(llm=llm, prompt_helper=prompt_helper)

    # WEBデータを解析(GPT)
    documents = SimpleDirectoryReader(input_dir=scraping_data_dir).load_data()
    list_index = GPTVectorStoreIndex.from_documents(documents, service_context=service_context)
    query_engine = list_index.as_query_engine()

    # 要約の実行
    answer = query_engine.query(prompt)
    return answer
