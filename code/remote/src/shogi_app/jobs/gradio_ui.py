import gradio as gr

from shogi_app.rag import rag_query


def main():
    """Gradio UIのメイン関数"""

    def query_rag(query: str, collection: str, n_results: int):
        """RAGクエリを実行

        Args:
            query: クエリテキスト
            collection: コレクション名
            n_results: 取得するドキュメント数

        Returns:
            回答と参照ドキュメント
        """
        result = rag_query(
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

    with gr.Blocks(title="盤上問答 - 将棋棋譜解析RAG") as demo:
        gr.Markdown("# 盤上問答 - 将棋棋譜解析RAG")
        gr.Markdown("将棋の棋譜情報を検索・分析するRAGアプリケーション")

        with gr.Row():
            collection = gr.Dropdown(
                choices=["positions", "floodgate_positions", "joseki_knowledge"],
                value="positions",
                label="検索対象コレクション",
            )
            n_results = gr.Slider(
                minimum=1,
                maximum=10,
                value=5,
                step=1,
                label="取得するドキュメント数",
            )

        query = gr.Textbox(
            placeholder="例: この局面で最善の手は何ですか？",
            label="質問を入力",
            lines=3,
        )

        submit_btn = gr.Button("検索", variant="primary")

        answer = gr.Textbox(label="回答", lines=5)
        docs = gr.Textbox(label="参照ドキュメント", lines=10)

        submit_btn.click(
            fn=query_rag,
            inputs=[query, collection, n_results],
            outputs=[answer, docs],
        )

        gr.Markdown("## 使用例")
        gr.Markdown("- この局面で最善の手は何ですか？")
        gr.Markdown("- 矢倉囲いの特徴を教えてください")
        gr.Markdown("- 振り飛車の戦法について説明してください")

    demo.launch()


if __name__ == "__main__":
    main()
