import os
import io
import base64
import PIL.Image
import numpy as np
import cohere
import requests
from .models import Day
from dotenv import load_dotenv

load_dotenv()

class VisionRAGSearcher:
    def __init__(self, cohere_api_key=None):
        self.max_pixels = 1568 * 1568  # 画像の最大解像度
        
        # Cohereクライアントの初期化
        api_key = cohere_api_key or os.getenv('COHERE_API_KEY')
        if not api_key:
            raise ValueError(
                "CohereのAPIキーが設定されていません。"
                "環境変数COHERE_API_KEYを設定するか、コンストラクタで指定してください。"
            )
        
        self.co = cohere.ClientV2(api_key=api_key)
    
    def resize_image(self, pil_image):
        """
        画像が大きすぎる場合はリサイズする
        
        Args:
            pil_image (PIL.Image): PIL画像オブジェクト
        """
        org_width, org_height = pil_image.size
        
        if org_width * org_height > self.max_pixels:
            scale_factor = (self.max_pixels / (org_width * org_height)) ** 0.5
            new_width = int(org_width * scale_factor)
            new_height = int(org_height * scale_factor)
            pil_image.thumbnail((new_width, new_height))
    
    def image_to_base64(self, image_source):
        """
        画像ファイルまたはURLをbase64文字列に変換
        
        Args:
            image_source (str): 画像ファイルのパスまたはURL
            
        Returns:
            str: base64エンコードされた画像データ
        """
        response = requests.get(image_source, timeout=30)
        response.raise_for_status()
        image_data = io.BytesIO(response.content)
        pil_image = PIL.Image.open(image_data)
        img_format = pil_image.format if pil_image.format else "PNG"
        
        self.resize_image(pil_image)
        
        with io.BytesIO() as img_buffer:
            pil_image.save(img_buffer, format=img_format)
            img_buffer.seek(0)
            img_data = f"data:image/{img_format.lower()};base64," + \
                        base64.b64encode(img_buffer.read()).decode("utf-8")
        
        return img_data

    def get_image_embedding(self, image_source):
        """
        画像の埋め込みベクトルを取得
        
        Args:
            image_source (str): 画像ファイルのパスまたはURL
            
        Returns:
            np.array: 画像の埋め込みベクトル（失敗時はNone）
        """
        try:
            base64_image = self.image_to_base64(image_source)
            if not base64_image:
                return None
            
            # APIリクエスト用のドキュメント形式
            api_input_document = {
                "content": [
                    {"type": "image", "image": base64_image},
                ]
            }
            
            # Cohere Embed v4.0を使用してベクトル化
            api_response = self.co.embed(
                model="embed-v4.0",
                input_type="search_document",
                embedding_types=["float"],
                inputs=[api_input_document],
            )
            
            # 埋め込みベクトルを取得
            embedding = np.asarray(api_response.embeddings.float[0])
            return embedding
            
        except Exception as e:
            print(f"画像の埋め込み取得に失敗しました: {image_source}, エラー: {e}")
            return None
    
    def get_query_embedding(self, query_text):
        """
        検索クエリの埋め込みベクトルを取得
        
        Args:
            query_text (str): 検索クエリ
            
        Returns:
            np.array: クエリの埋め込みベクトル
        """
        try:
            api_response = self.co.embed(
                model="embed-v4.0",
                input_type="search_query",
                embedding_types=["float"],
                texts=[query_text],
            )
            
            query_embedding = np.asarray(api_response.embeddings.float[0])
            return query_embedding
            
        except Exception as e:
            print(f"クエリの埋め込み取得に失敗しました: {query_text}, エラー: {e}")
            return None
    
    def compute_similarity(self, query_embedding, doc_embeddings):
        """
        コサイン類似度を計算
        
        Args:
            query_embedding (np.array): クエリの埋め込みベクトル
            doc_embeddings (np.array): ドキュメント（画像）の埋め込みベクトル行列
            
        Returns:
            np.array: 各ドキュメントとの類似度スコア
        """
        return np.dot(query_embedding, doc_embeddings.T)


def build_image_embeddings_cache(user_id):
    """
    特定ユーザーの画像付き日記の埋め込みベクトルをキャッシュとして構築
    
    Args:
        user_id (int): ユーザーID
        
    Returns:
        tuple: (day_ids, embeddings_matrix) または (None, None)
    """
    searcher = VisionRAGSearcher()
    
    # 指定ユーザーの画像付き日記を取得
    days_with_images = Day.objects.filter(
        author_id=user_id,
        image__isnull=False
    ).exclude(image='')
    
    if not days_with_images.exists():
        print(f"ユーザーID {user_id} の画像付き日記が見つかりません")
        return None, None
    
    day_ids = []
    embeddings_list = []
    
    for day in days_with_images:
        try:
            # 画像ソース（URLまたはパス）を取得
            image_source = None
            
            if day.image:
                image_source = day.image.url
                print(f"画像URL使用: {image_source}")

            if not image_source:
                print(f"日記ID {day.id}: 画像ソースが取得できませんでした")
                continue
            
            # 埋め込みベクトルを取得
            embedding = searcher.get_image_embedding(image_source)
            if embedding is not None:
                day_ids.append(day.id)
                embeddings_list.append(embedding)
                print(f"日記ID {day.id} の埋め込みを取得しました")
            else:
                print(f"日記ID {day.id}: 埋め込み取得に失敗")
            
        except Exception as e:
            print(f"日記ID {day.id} の処理中にエラーが発生しました: {e}")
            continue
    
    if not embeddings_list:
        print("有効な画像埋め込みが取得できませんでした")
        return None, None
    
    # 埋め込み行列を作成
    embeddings_matrix = np.vstack(embeddings_list)
    
    print(f"構築完了: {len(day_ids)}件の画像埋め込み")
    return day_ids, embeddings_matrix


def search_days_by_image_content(query_text, user_id, top_k=10, similarity_threshold=0.3):
    """
    画像内容に基づいて日記を検索
    
    Args:
        query_text (str): 検索クエリ（自然言語）
        user_id (int): ユーザーID
        top_k (int): 返す結果の最大数
        similarity_threshold (float): 類似度の最小閾値（デフォルト0.3）
        
    Returns:
        list: マッチした日記のリスト（類似度順）
    """
    searcher = VisionRAGSearcher()
    
    # 画像埋め込みキャッシュを構築
    day_ids, embeddings_matrix = build_image_embeddings_cache(user_id)
    
    if day_ids is None or embeddings_matrix is None:
        print("画像埋め込みの構築に失敗しました")
        return []
    
    # クエリの埋め込みを取得
    query_embedding = searcher.get_query_embedding(query_text)
    if query_embedding is None:
        print("クエリの埋め込み取得に失敗しました")
        return []
    
    # 類似度を計算
    similarity_scores = searcher.compute_similarity(query_embedding, embeddings_matrix)
    
    # デバッグ情報：類似度スコアを表示
    print(f"類似度スコア: min={similarity_scores.min():.4f}, max={similarity_scores.max():.4f}, mean={similarity_scores.mean():.4f}")
    for i, score in enumerate(similarity_scores):
        print(f"  日記ID {day_ids[i]}: {score:.4f}")
    
    # 閾値以上の結果のみを取得
    valid_indices = np.where(similarity_scores >= similarity_threshold)[0]
    
    if len(valid_indices) == 0:
        print(f"類似度閾値 {similarity_threshold:.4f} 以上の結果がありませんでした")
        return []
    
    # 有効な結果の中から上位を選択
    valid_scores = similarity_scores[valid_indices]
    valid_day_ids = [day_ids[i] for i in valid_indices]
    
    # 上位結果を取得（有効な結果の中から）
    top_indices_in_valid = np.argsort(valid_scores)[::-1][:top_k]
    result_day_ids = [valid_day_ids[i] for i in top_indices_in_valid]
    result_scores = [valid_scores[i] for i in top_indices_in_valid]
    
    # 結果の日記オブジェクトを取得
    matched_days = Day.objects.filter(id__in=result_day_ids)
    
    # 元の順序を保持するために並び替え
    day_dict = {day.id: day for day in matched_days}
    sorted_days = [day_dict[day_id] for day_id in result_day_ids if day_id in day_dict]
    
    print(f"検索完了: クエリ「{query_text}」で{len(sorted_days)}件の結果")
    print(f"使用した閾値: {similarity_threshold:.4f}")
    print(f"結果の類似度スコア: {[f'{score:.4f}' for score in result_scores]}")
    return sorted_days