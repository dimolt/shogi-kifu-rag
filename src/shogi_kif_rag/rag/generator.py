from typing import Dict, List

from .llm_client import LLMClient


def generate_response(query: str, context: List[Dict], llm_client: LLMClient) -> str:
    """コンテキストに基づいて回答を生成

    Args:
        query: クエリテキスト
        context: 関連ドキュメントリスト
        llm_client: LLMクライアント

    Returns:
        生成された回答
    """
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
