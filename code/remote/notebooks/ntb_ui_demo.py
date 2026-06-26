# Databricks notebook source
# MAGIC %md
# MAGIC # UI デモ用notebook
# MAGIC 
# MAGIC RAGチェーン検証用、デモ用UIを公開する

# COMMAND ----------

# MAGIC %md
# MAGIC python 3.12の制約のため serverless standard v4,5で使用すること

# COMMAND ----------

# MAGIC 
# MAGIC %pip install gradio chromadb sentence_transformers
# MAGIC 

# COMMAND ----------

# MAGIC 
# MAGIC %pip install /Workspace/Users/realnowhereman@icloud.com/.bundle/shogi-kifu-rag/dev/artifacts/.internal/shogiapp-0.1.0-py3-none-any.whl
# MAGIC 

# COMMAND ----------
import gradio as gr
from shogi_app.vector.chromadb_service import ChromadbService
from shogi_app.rag import rag_query

# COMMAND ----------
def query_rag(query: str, collection: str, n_results: int):
    """RAGクエリを実行

    Args:
        query: クエリテキスト
        collection: コレクション名
        n_results: 取得するドキュメント数

    Returns:
        回答と参照ドキュメント
    """

    chromadb = ChromadbService.get_instance(),

    result = rag_query(
        chromadb=chromadb,
        query=query,
        collection_name=collection,
        n_results=n_results,
    )
    answer = result["answer"]
    docs = result["documents"]
    doc_text = "\n\n".join([
        f"ドキュメント {i+1} (距離: {doc['distance']:.4f})\n{doc['text']}\nメタデータ: {doc['metadata']}"
        for i, doc in enumerate(docs)
    ])
    return answer, doc_text

# COMMAND ----------
def create_ui():
    with gr.Blocks(title="盤上問答 - 将棋棋譜解析RAG") as demo:
        gr.Markdown("# 盤上問答 - 将棋棋譜解析RAG")
        gr.Markdown("将棋の棋譜情報を検索・分析するRAGアプリケーション")

        with gr.Row():
            with gr.Column():
                query_input = gr.Textbox(
                    label="質問を入力",
                    placeholder="例: この局面で最善の手は何ですか？",
                    lines=2
                )
                collection_select = gr.Dropdown(
                    choices=["positions", "floodgate_positions", "joseki_knowledge"],
                    value="positions",
                    label="検索対象コレクション"
                )
                n_results_slider = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="取得するドキュメント数"
                )
                submit_btn = gr.Button("検索", variant="primary")

            with gr.Column():
                answer_output = gr.Textbox(
                    label="回答",
                    lines=5
                )
                context_output = gr.Textbox(
                    label="参照ドキュメント",
                    lines=10
                )

        submit_btn.click(
            fn=query_rag,
            inputs=[query_input, collection_select, n_results_slider],
            outputs=[answer_output, context_output]
        )

        gr.Markdown("## 使用例")
        gr.Markdown("- この局面で最善の手は何ですか？")
        gr.Markdown("- 矢倉囲いの特徴を教えてください")
        gr.Markdown("- 振り飛車の戦法について説明してください")
    return demo

# COMMAND ----------
demo = create_ui()
demo.launch(share=True)
