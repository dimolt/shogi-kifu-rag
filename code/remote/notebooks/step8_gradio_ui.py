"""Gradio UI

RAGチェーンを使用したGradio UIの実装
"""

import os

import chromadb
import gradio as gr
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ChromaDBの初期化
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="/tmp/shogi/chromadb",
))

# Embeddingモデルの初期化
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# LLMの初期化（Gemini 2.5 Flash with Groq Llama 3.3 70B fallback）
class LLMClient:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.use_gemini = True

    def generate(self, prompt: str) -> str:
        if self.use_gemini and self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini error: {e}, falling back to Groq")
                self.use_gemini = False

        if self.groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_api_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1024,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Groq error: {e}")

        return "LLM generation failed"

llm_client = LLMClient()

def retrieve_relevant_documents(
    query: str,
    collection_name: str = "positions",
    n_results: int = 5,
):
    query_embedding = embedding_model.encode(query).tolist()

    try:
        collection = chroma_client.get_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        documents = []
        for i in range(len(results["documents"][0])):
            documents.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        return documents
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []

def generate_response(query: str, context):
    context_text = "\n\n".join([
        f"ドキュメント {i+1}:\n{doc['text']}\nメタデータ: {doc['metadata']}"
        for i, doc in enumerate(context)
    ])

    prompt = f"""以下の将棋の棋譜情報を参考に、質問に答えてください。

質問: {query}

参考情報:
{context_text}

回答:"""

    return llm_client.generate(prompt)

def rag_query(query: str, collection_name: str = "positions", n_results: int = 5):
    documents = retrieve_relevant_documents(query, collection_name, n_results)

    if not documents:
        return "関連する情報が見つかりませんでした。", []

    answer = generate_response(query, documents)

    context_display = "\n\n".join([
        f"【ドキュメント {i+1}】\n{doc['text']}\n"
        for i, doc in enumerate(documents)
    ])

    return answer, context_display

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
            fn=rag_query,
            inputs=[query_input, collection_select, n_results_slider],
            outputs=[answer_output, context_output]
        )

        gr.Markdown("## 使用例")
        gr.Markdown("- この局面で最善の手は何ですか？")
        gr.Markdown("- 矢倉囲いの特徴を教えてください")
        gr.Markdown("- 振り飛車の戦法について説明してください")

    return demo

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
