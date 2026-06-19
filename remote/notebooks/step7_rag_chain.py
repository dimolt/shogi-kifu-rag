"""RAG Chain

ChromaDBとLLMを使用したRAGチェーンの実装
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict
import time

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
        """LLMによる生成
        
        Args:
            prompt: プロンプト
            
        Returns:
            生成されたテキスト
        """
        if self.use_gemini and self.gemini_api_key:
            try:
                # Gemini 2.5 Flashを使用
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini error: {e}, falling back to Groq")
                self.use_gemini = False
        
        # Groq Llama 3.3 70B fallback
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

def retrieve_relevant_documents(query: str, collection_name: str = "positions", n_results: int = 5) -> List[Dict]:
    """ChromaDBから関連ドキュメントを取得
    
    Args:
        query: クエリテキスト
        collection_name: コレクション名
        n_results: 取得するドキュメント数
        
    Returns:
        関連ドキュメントリスト
    """
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

def generate_response(query: str, context: List[Dict]) -> str:
    """コンテキストに基づいて回答を生成
    
    Args:
        query: クエリテキスト
        context: 関連ドキュメントリスト
        
    Returns:
        生成された回答
    """
    # コンテキストのフォーマット
    context_text = "\n\n".join([
        f"ドキュメント {i+1}:\n{doc['text']}\nメタデータ: {doc['metadata']}"
        for i, doc in enumerate(context)
    ])
    
    # プロンプトの構築
    prompt = f"""以下の将棋の棋譜情報を参考に、質問に答えてください。

質問: {query}

参考情報:
{context_text}

回答:"""
    
    return llm_client.generate(prompt)

def rag_query(query: str, collection_name: str = "positions", n_results: int = 5) -> Dict:
    """RAGクエリを実行
    
    Args:
        query: クエリテキスト
        collection_name: コレクション名
        n_results: 取得するドキュメント数
        
    Returns:
        RAG結果（回答と参照ドキュメント）
    """
    # 関連ドキュメントの取得
    documents = retrieve_relevant_documents(query, collection_name, n_results)
    
    if not documents:
        return {
            "answer": "関連する情報が見つかりませんでした。",
            "documents": [],
        }
    
    # 回答の生成
    answer = generate_response(query, documents)
    
    return {
        "answer": answer,
        "documents": documents,
    }

# テストクエリ
test_queries = [
    "この局面で最善の手は何ですか？",
    "矢倉囲いの特徴を教えてください",
    "振り飛車の戦法について説明してください",
]

for query in test_queries:
    print(f"\nQuery: {query}")
    result = rag_query(query, collection_name="positions", n_results=3)
    print(f"Answer: {result['answer']}")
    time.sleep(1)  # Rate limiting
