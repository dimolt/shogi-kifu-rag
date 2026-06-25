from shogi_app.rag import rag_query

import streamlit as st


def main():
    """Streamlit UIのメイン関数"""
    st.title("盤上問答 - 将棋棋譜解析RAG")
    st.markdown("将棋の棋譜情報を検索・分析するRAGアプリケーション")

    # サイドバーで設定
    st.sidebar.header("設定")
    collection_select = st.sidebar.selectbox(
        "検索対象コレクション",
        ["positions", "floodgate_positions", "joseki_knowledge"],
        index=0,
    )
    n_results = st.sidebar.slider(
        "取得するドキュメント数",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
    )

    # メイン画面
    st.header("質問入力")
    query = st.text_area(
        "質問を入力",
        placeholder="例: この局面で最善の手は何ですか？",
        height=100,
    )

    if st.button("検索", type="primary"):
        if not query:
            st.warning("質問を入力してください")
            return

        with st.spinner("検索中..."):
            result = rag_query(
                query=query,
                collection_name=collection_select,
                n_results=n_results,
            )

        # 回答表示
        st.header("回答")
        st.write(result["answer"])

        # 参照ドキュメント表示
        if result["documents"]:
            st.header("参照ドキュメント")
            for i, doc in enumerate(result["documents"]):
                with st.expander(f"ドキュメント {i+1} (距離: {doc['distance']:.4f})"):
                    st.write(doc["text"])
                    st.json(doc["metadata"])

    # 使用例
    st.header("使用例")
    st.markdown("- この局面で最善の手は何ですか？")
    st.markdown("- 矢倉囲いの特徴を教えてください")
    st.markdown("- 振り飛車の戦法について説明してください")


if __name__ == "__main__":
    main()
