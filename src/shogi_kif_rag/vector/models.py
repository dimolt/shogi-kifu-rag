from __future__ import annotations

from typing import TypedDict


class DocumentMetadata(TypedDict, total=False):
    """ドキュメントのメタデータ。

    将棋棋譜に関連する情報を格納するための辞書。
    すべてのフィールドはオプション（total=False）。
    """
    game_id: str
    move_number: int
    sfen: str
    move_usi: str
    player: str
    move_quality: str
    score_cp: int
    strategy: str
    source: str


class Document(TypedDict):
    """VectorStoreに格納するドキュメント。

    Attributes:
        id: ドキュメントの一意識別子。
        text: ドキュメントのテキスト内容。
        metadata: ドキュメントのメタデータ。
    """
    id: str
    text: str
    metadata: DocumentMetadata


class SearchResult(TypedDict):
    """検索結果のアイテム。

    Attributes:
        document: ヒットしたドキュメント。
        score: 類似度スコア（小さいほど類似度が高い）。
    """
    document: Document
    score: float
