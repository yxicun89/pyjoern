# これが現時点での完成版
# 11次元でクラスタリングできます

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_distances
from sklearn.datasets import make_blobs, make_circles, make_moons, load_iris, load_wine
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
from datetime import datetime

# オプショナルライブラリのインポート
try:
    import seaborn as sns
    import pandas as pd
    ADVANCED_VIZ_AVAILABLE = True
except ImportError:
    ADVANCED_VIZ_AVAILABLE = False
    print("⚠️ seaborn/pandasが利用できません。基本的な可視化のみ実行します。")
    print("   高度な可視化には: pip install seaborn pandas を実行してください。")

# JSONファイル操作のインポート
import json

# 次元削減手法のインポート
try:
    from sklearn.manifold import TSNE
    TSNE_AVAILABLE = True
except ImportError:
    TSNE_AVAILABLE = False
    print("⚠️ t-SNEが利用できません。scikit-learnのバージョンを確認してください。")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    print("⚠️ UMAPが利用できません。インストールには: pip install umap-learn を実行してください。")

# ext_cfg_dfg_feature.pyから特徴量抽出関数をインポート
try:
    from ext_cfg_dfg_feature import (
        extract_integrated_features_vector,
        batch_extract_integrated_features,
        find_files_in_directory,
        load_feature_vectors,
        save_feature_vectors,
        check_cache_validity,
        analyze_file_groups
    )
    FEATURE_EXTRACTION_AVAILABLE = True
except ImportError as e:
    print(f"❌ 特徴量抽出モジュールのインポートエラー: {e}")
    print("ext_cfg_dfg_feature.pyが同じディレクトリにあることを確認してください。")
    FEATURE_EXTRACTION_AVAILABLE = False

# --- 特徴量の重みを定義 ---
# connected_components, loop_statements, conditional_statements, cycles, paths, cyclomatic_complexity
# variable_count, total_reads, total_writes, max_reads, max_writes に対応
FEATURE_WEIGHTS = np.array([
    1.0, # connected_components
    1.0, # loop_statements
    1.0, # conditional_statements
    1.0, # cycles
    1.0, # paths
    1.0, # cyclomatic_complexity
    0.6, # variable_count
    0.1, # total_reads
    0.1, # total_writes
    0.1, # max_reads
    0.1  # max_writes
])

# --- 距離関数（重み付きユークリッド距離、マンハッタン距離、コサイン距離） ---
def dist(c, s, metric='euclidean', weights=None):
    if metric == 'euclidean':
        if weights is None:
            return np.linalg.norm(c - s)
        else:
            # 重み付きユークリッド距離: sqrt(sum(w_i * (c_i - s_i)^2))
            return np.sqrt(np.sum(weights * (c - s)**2))
    elif metric == 'manhattan':
        if weights is None:
            return np.sum(np.abs(c - s))
        else:
            # 重み付きマンハッタン距離: sum(w_i * |c_i - s_i|)
            return np.sum(weights * np.abs(c - s))
    elif metric == 'cosine':
        if weights is None:
            return cosine_distances([c], [s])[0][0]
        else:
            # 重み付きコサイン距離: 重みをsqrt(w_i)で特徴量に適用してからコサイン距離を計算
            c_w = c * np.sqrt(weights)
            s_w = s * np.sqrt(weights)
            return cosine_distances([c_w], [s_w])[0][0]
    else:
        raise ValueError(f"未知の距離関数です: {metric}")

# --- K-means++ 初期化 ---
def initialize_centroids(X_data, k):
    kmeans = KMeans(n_clusters=k, init='k-means++', n_init='auto', random_state=42)
    kmeans.fit(X_data)
    return kmeans.cluster_centers_

# --- 一般的なK-meansクラスタリングアルゴリズム ---
def general_kmeans_algorithm(X_data, k, metric='euclidean', weights=None, max_iterations=100):
    C = initialize_centroids(X_data, k)

    for iteration in range(max_iterations):
        # ステップ 1: 各データポイントを最も近いセントロイドに割り当てる
        labels = np.zeros(len(X_data), dtype=int)
        for i, S in enumerate(X_data):
            dists = [dist(c, S, metric, weights=weights) for c in C]
            labels[i] = np.argmin(dists)

        # ステップ 2: 新しいクラスター割り当てに基づいてセントロイドを更新
        new_C = np.zeros((k, X_data.shape[1]))
        for i in range(k):
            points_in_cluster = X_data[labels == i]
            if len(points_in_cluster) > 0:
                new_C[i] = np.mean(points_in_cluster, axis=0)
            else:
                # クラスターが空になった場合、データ全体の範囲内でランダムに再初期化する
                min_val = np.min(X_data, axis=0)
                max_val = np.max(X_data, axis=0)
                new_C[i] = np.random.uniform(min_val, max_val, X_data.shape[1])

        # 収束判定: セントロイドがほとんど変化しなくなったら停止
        if np.allclose(C, new_C):
            break

        C = new_C

    # 最終的なラベル付け
    final_labels = np.zeros(len(X_data), dtype=int)
    for i, S in enumerate(X_data):
        dists = [dist(c, S, metric, weights=weights) for c in C]
        final_labels[i] = np.argmin(dists)

    return C, final_labels

# --- 正解判定関数を利用したクラスタリングアルゴリズム ---
def clustering_algorithm_with_correctness(X_data, k, is_correct_fn, metric='euclidean', weights=None, max_iterations=100):
    """
    正解判定関数を利用したK-meansクラスタリング

    Args:
        X_data: 特徴量データ
        k: クラスター数
        is_correct_fn: 正解判定関数
        metric: 距離計算方法
        weights: 特徴量の重み
        max_iterations: 最大反復回数

    Returns:
        C: 最終セントロイド
        final_labels: 最終ラベル
    """
    C = initialize_centroids(X_data, k)
    N = np.zeros(k)  # 各クラスターに割り当てられたデータポイントの数

    for S in X_data:
        # 各データポイント S を最も近いセントロイドに割り当てる
        dists = [dist(c, S, metric, weights=weights) for c in C]
        min_c = np.argmin(dists)  # 割り当てられたクラスターのインデックス

        N[min_c] += 1

        # 正解判定関数がTrueを返した場合にのみセントロイドを更新
        if is_correct_fn(S, min_c):
            # オンライン学習に似たセントロイド更新（1点ごとの移動平均）
            C[min_c] = C[min_c] + (1 / N[min_c]) * (S - C[min_c])

    # 最終的なラベル付け
    final_labels = np.zeros(len(X_data), dtype=int)
    for i, S in enumerate(X_data):
        dists = [dist(c, S, metric, weights=weights) for c in C]
        final_labels[i] = np.argmin(dists)

    return C, final_labels

# --- 正解判定関数を生成するファクトリ関数（教師あり） ---
def is_correct_fn_factory(true_centers):
    """
    真のセントロイドを基にした正解判定関数を生成

    Args:
        true_centers: 真のセントロイドの配列

    Returns:
        is_correct: 正解判定関数
    """
    if true_centers is None:
        # 真のクラスター中心がない場合は、常にTrueを返す
        print("Warning: No true_centers provided for correctness check. The algorithm will always consider an assignment 'correct'.")
        return lambda S, assigned_cluster_idx: True

    def is_correct(S, assigned_cluster_idx):
        # データポイント S がどの真のクラスター中心に最も近いかを判断
        true_dists = [np.linalg.norm(tc - S) for tc in true_centers]
        correct_cluster_idx = np.argmin(true_dists)

        # アルゴリズムが割り当てたクラスターと真のクラスターが一致するかどうかを返す
        return assigned_cluster_idx == correct_cluster_idx

    return is_correct

# --- JSONファイルから真のセントロイドを読み込み ---
def load_true_centroids_from_cache(cache_file):
    """
    キャッシュファイルから真のセントロイド（パターン別重心）を読み込み

    Args:
        cache_file: キャッシュファイルパス

    Returns:
        true_centers: 真のセントロイド配列
        pattern_labels: パターンラベルリスト
    """
    try:
        if FEATURE_EXTRACTION_AVAILABLE:
            cached_data = load_feature_vectors(cache_file)
        else:
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

        if cached_data and cached_data.get('pattern_centroids'):
            centroids_info = cached_data['pattern_centroids']

            if centroids_info and centroids_info.get('centroids'):
                pattern_centroids = []
                pattern_labels = []

                for pattern_name, centroid_info in centroids_info['centroids'].items():
                    pattern_centroids.append(centroid_info['centroid_vector'])
                    pattern_labels.append(pattern_name)

                true_centers = np.array(pattern_centroids)

                print(f"✅ 真のセントロイドを読み込みました:")
                print(f"   パターン数: {len(pattern_labels)}")
                print(f"   特徴量次元: {true_centers.shape[1]}")
                for i, label in enumerate(pattern_labels):
                    print(f"   {label}: {np.round(true_centers[i][:3], 3)}...")

                return true_centers, pattern_labels
            else:
                print("⚠️ キャッシュファイルにセントロイド情報がありません")
                return None, None
        else:
            print("⚠️ キャッシュファイルにパターンセントロイド情報がありません")
            return None, None

    except Exception as e:
        print(f"❌ 真のセントロイド読み込みエラー: {e}")
        return None, None

# --- クラスタリング結果を保存 ---
def save_clustering_results(final_labels, C_final, true_centers, file_names, file_paths,
                           algorithm_type, dataset_name, k_clusters, centroid_distance,
                           feature_vectors=None, output_dir=None):
    """
    クラスタリング結果をJSONファイルに保存

    Args:
        final_labels: クラスターラベル
        C_final: 最終セントロイド
        true_centers: 真のセントロイド
        file_names: ファイル名リスト
        file_paths: ファイルパスリスト
        algorithm_type: アルゴリズムタイプ
        dataset_name: データセット名
        k_clusters: クラスター数
        centroid_distance: セントロイド距離
        feature_vectors: 特徴量ベクトル
        output_dir: 出力ディレクトリ
    """
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if output_dir is None:
            output_dir = f"clustering_results_{timestamp}"
            os.makedirs(output_dir, exist_ok=True)

        # 結果を整理
        clustering_results = {
            "metadata": {
                "algorithm_type": algorithm_type,
                "dataset_name": dataset_name,
                "timestamp": timestamp,
                "k_clusters": k_clusters,
                "total_samples": len(final_labels),
                "centroid_distance": float(centroid_distance) if not np.isnan(centroid_distance) else None
            },
            "final_centroids": C_final.tolist() if C_final is not None else None,
            "true_centroids": true_centers.tolist() if true_centers is not None else None,
            "cluster_assignments": {},
            "cluster_statistics": {}
        }

        # クラスター別の詳細情報を作成
        unique_labels = np.unique(final_labels)
        for cluster_id in unique_labels:
            cluster_mask = final_labels == cluster_id
            cluster_indices = np.where(cluster_mask)[0]

            # ファイル情報
            cluster_files = []
            if file_names and file_paths:
                for idx in cluster_indices:
                    file_info = {
                        "index": int(idx),
                        "filename": file_names[idx],
                        "filepath": file_paths[idx]
                    }

                    # 特徴量ベクトルを追加
                    if feature_vectors is not None:
                        file_info["feature_vector"] = feature_vectors[idx].tolist()

                    # パターン情報を抽出
                    filepath = file_paths[idx]
                    if 'pattern1' in filepath:
                        file_info["pattern"] = "pattern1"
                    elif 'pattern2' in filepath:
                        file_info["pattern"] = "pattern2"
                    elif 'pattern3' in filepath:
                        file_info["pattern"] = "pattern3"
                    elif 'pattern4' in filepath:
                        file_info["pattern"] = "pattern4"
                    else:
                        file_info["pattern"] = "other"

                    cluster_files.append(file_info)

            # クラスター統計情報
            cluster_stats = {
                "size": len(cluster_indices),
                "percentage": float(len(cluster_indices) / len(final_labels) * 100),
                "centroid": C_final[cluster_id].tolist() if C_final is not None else None
            }

            # パターン分布統計
            if file_paths:
                pattern_distribution = {}
                for file_info in cluster_files:
                    pattern = file_info.get("pattern", "other")
                    pattern_distribution[pattern] = pattern_distribution.get(pattern, 0) + 1
                cluster_stats["pattern_distribution"] = pattern_distribution

            clustering_results["cluster_assignments"][f"cluster_{cluster_id}"] = cluster_files
            clustering_results["cluster_statistics"][f"cluster_{cluster_id}"] = cluster_stats

        # ファイルに保存
        filename = f"clustering_results_{algorithm_type}_{dataset_name}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(clustering_results, f, ensure_ascii=False, indent=2)

        print(f"💾 クラスタリング結果を保存しました: {filepath}")

        # 統計情報をサマリー表示
        print(f"📊 保存された結果サマリー:")
        print(f"   アルゴリズム: {algorithm_type}")
        print(f"   データセット: {dataset_name}")
        print(f"   クラスター数: {k_clusters}")
        print(f"   総サンプル数: {len(final_labels)}")
        if not np.isnan(centroid_distance):
            print(f"   セントロイド距離: {centroid_distance:.4f}")

        return filepath

    except Exception as e:
        print(f"❌ クラスタリング結果保存エラー: {e}")
        return None

        C = new_C

    # 最終的なラベル付け
    final_labels = np.zeros(len(X_data), dtype=int)
    for i, S in enumerate(X_data):
        dists = [dist(c, S, metric, weights=weights) for c in C]
        final_labels[i] = np.argmin(dists)

    return C, final_labels

# --- データセット作成関数 ---
def create_dataset(dataset_name: str, n_samples: int = 300):
    if dataset_name == 'real_code_features':
        # 実際のコードファイルから特徴量を抽出（キャッシュ対応）
        if not FEATURE_EXTRACTION_AVAILABLE:
            raise ValueError("特徴量抽出モジュールが利用できません。ext_cfg_dfg_feature.pyのインポートを確認してください。")

        # ディレクトリパスを指定（相対パスまたは絶対パス）
        target_directory = "../atcoder/submissions_typical90_d_100"

        if not os.path.exists(target_directory):
            raise ValueError(f"指定されたディレクトリが存在しません: {target_directory}")

        # キャッシュファイル名を生成
        cache_file = f"feature_cache_{os.path.basename(target_directory)}.json"

        # ファイルを検索
        code_files = find_files_in_directory(target_directory)

        if len(code_files) == 0:
            raise ValueError(f"指定されたディレクトリにコードファイルが見つかりません: {target_directory}")

        print(f"🔍 発見されたファイル数: {len(code_files)}")
        for i, file in enumerate(code_files[:5]):  # 最初の5ファイルを表示
            print(f"  {i+1}. {os.path.relpath(file, target_directory)}")
        if len(code_files) > 5:
            print(f"  ... および {len(code_files) - 5} 個のファイル")

        # キャッシュの有効性をチェック
        batch_results = None
        use_cache = False

        if os.path.exists(cache_file):
            if check_cache_validity(target_directory, cache_file):
                print(f"📦 有効なキャッシュファイルを発見: {cache_file}")
                print("キャッシュを使用してクラスタリングを実行します。")
                use_cache = True
            else:
                print(f"⚠️ キャッシュファイルは古いため、再抽出が必要です")

        if use_cache:
            # キャッシュから読み込み
            print(f"📂 キャッシュから特徴量を読み込み中...")
            cached_data = load_feature_vectors(cache_file)
            if cached_data:
                batch_results = cached_data['data']
                print(f"✅ キャッシュから {len(batch_results)} ファイルの特徴量を読み込みました")

        if batch_results is None:
            # 新規抽出
            print("📊 特徴量抽出中...")
            batch_results = batch_extract_integrated_features(code_files)

            # 結果をキャッシュに保存
            print(f"💾 特徴量をキャッシュに保存中...")
            save_feature_vectors(batch_results, cache_file, format='json')

        # 成功した結果のみを使用
        successful_results = [r for r in batch_results if 'error' not in r]

        if len(successful_results) == 0:
            raise ValueError("すべてのファイルで特徴量抽出に失敗しました")

        print(f"✅ 特徴量抽出成功: {len(successful_results)} / {len(code_files)} ファイル")

        # 特徴量ベクトルを取得
        X = np.array([r['integrated_vector'] for r in successful_results])

        # クラスター数を自動決定（ファイル数に基づく）
        k_clusters = 5
        n_features = 11

        # 実際のデータには真のラベルがないため、仮のラベルを作成
        y_true = np.zeros(len(successful_results))  # すべて同じクラスターとして扱う

        # ファイル名を保存（後で参照用）
        file_names = [os.path.basename(r['source_file']) for r in successful_results]

        # ファイルパスを保存（グループ分析用）
        file_paths = [r['source_file'] for r in successful_results]

        print(f"📈 データセット準備完了: {len(X)} サンプル, {n_features} 特徴量, {k_clusters} クラスター")

        # 真のセントロイドをキャッシュファイルから読み込み
        true_centers, pattern_labels = load_true_centroids_from_cache(cache_file)

        if true_centers is not None:
            # パターン数に基づいてクラスター数を調整
            k_clusters = len(true_centers)
            print(f"🎯 真のセントロイドに基づいてクラスター数を調整: {k_clusters}")

        # ファイル名とパス情報を返り値に含める（デバッグ用）
        return X, y_true, k_clusters, n_features, true_centers, file_names, file_paths

    else:
        raise ValueError(f"不明なデータセット名です: {dataset_name}")

# --- 最終的なセントロイドと真のセントロイド間の平均最小距離を計算する---
def calculate_average_min_centroid_distance(final_centroids, true_centers):
    if final_centroids is None or true_centers is None:
        return np.nan

    num_final = final_centroids.shape[0]
    num_true = true_centers.shape[0]

    # クラスター数が異なる場合は警告（ただし計算は続行）
    if num_final != num_true:
        print(f"Warning: Number of final centroids ({num_final}) does not match number of true centers ({num_true}). "
              "Distance calculation might be less meaningful.")

    min_distances = []
    for f_center in final_centroids:
        # 各最終セントロイドについて、全ての真のセントロイドとの距離を計算
        distances_to_true = [np.linalg.norm(f_center - t_center) for t_center in true_centers]
        min_distances.append(np.min(distances_to_true))

    return np.mean(min_distances)

def display_clustering_results(final_labels, C_final, file_names=None, dataset_name="unknown", file_paths=None, feature_vectors=None):
    """
    クラスタリング結果を詳細表示

    Args:
        final_labels: クラスターラベル
        C_final: 最終セントロイド
        file_names: ファイル名リスト
        dataset_name: データセット名
        file_paths: ファイルパスリスト
        feature_vectors: 特徴量ベクトル
    """
    print(f"\n📊 === {dataset_name.upper()} クラスタリング結果詳細 ===")

    unique_labels = np.unique(final_labels)
    print(f"🔢 総クラスター数: {len(unique_labels)}")
    print(f"📁 総サンプル数: {len(final_labels)}")

    print(f"\n🎯 各クラスターの詳細:")
    print("=" * 100)

    for cluster_id in unique_labels:
        cluster_indices = np.where(final_labels == cluster_id)[0]
        cluster_size = len(cluster_indices)

        print(f"\n🏷️  クラスター {cluster_id}:")
        print(f"   📊 サイズ: {cluster_size} サンプル ({cluster_size/len(final_labels)*100:.1f}%)")
        print(f"   🎯 セントロイド: {np.round(C_final[cluster_id], 3)}")

        # ファイル詳細情報を表示
        if file_names and file_paths and feature_vectors is not None:
            print(f"   📄 含まれるファイルの詳細:")
            print(f"   {'No':<3} {'ファイル名':<25} {'パス':<50} {'特徴量ベクトル'}")
            print(f"   {'-'*3} {'-'*25} {'-'*50} {'-'*50}")

            cluster_data = []
            for idx in cluster_indices:
                cluster_data.append({
                    'index': idx,
                    'filename': file_names[idx],
                    'filepath': file_paths[idx] if file_paths else 'N/A',
                    'vector': feature_vectors[idx] if feature_vectors is not None else 'N/A'
                })

            # ファイル名でソート
            cluster_data.sort(key=lambda x: x['filename'])

            for i, data in enumerate(cluster_data, 1):
                filename = data['filename']
                filepath = data['filepath']
                vector = data['vector']

                # ファイルパスからディレクトリ部分を抽出
                if filepath != 'N/A':
                    path_parts = filepath.split('/')
                    if len(path_parts) > 2:
                        short_path = '/'.join(path_parts[-2:])  # 最後の2階層のみ表示
                    else:
                        short_path = filepath
                else:
                    short_path = 'N/A'

                # ベクトルを短縮表示
                if isinstance(vector, (list, np.ndarray)):
                    vector_str = str(vector).replace(' ', '')[1:-1]  # スペース削除、[]削除
                    if len(vector_str) > 50:
                        vector_str = vector_str[:47] + "..."
                else:
                    vector_str = str(vector)

                print(f"   {i:2d}. {filename:<25} {short_path:<50} [{vector_str}]")

                # 10個以上ある場合は省略表示
                if i >= 10 and len(cluster_data) > 10:
                    remaining = len(cluster_data) - 10
                    print(f"       ... および {remaining} 個のファイル")
                    break

        elif file_names:
            print(f"   📄 含まれるファイル:")
            cluster_files = [file_names[idx] for idx in cluster_indices]

            # ファイル名をソートして表示
            cluster_files.sort()
            for i, filename in enumerate(cluster_files, 1):
                print(f"      {i:2d}. {filename}")
                if i >= 10 and len(cluster_files) > 10:  # 最初の10ファイルのみ表示
                    remaining = len(cluster_files) - 10
                    print(f"      ... および {remaining} 個のファイル")
                    break
        else:
            print(f"   📄 サンプルインデックス: {cluster_indices[:10].tolist()}" +
                  (f" ... (+{len(cluster_indices)-10})" if len(cluster_indices) > 10 else ""))

    print("=" * 100)

def main(algorithm_type: str, dataset_name: str):
    # データセットの生成
    result = create_dataset(dataset_name)

    # 返り値の数に応じて適切に分割
    if len(result) == 7:
        X, y_true, k_clusters, n_features, true_centers, file_names, file_paths = result
    elif len(result) == 6:
        X, y_true, k_clusters, n_features, true_centers, file_names = result
        file_paths = None
    else:
        X, y_true, k_clusters, n_features, true_centers = result
        file_names = None
        file_paths = None

    # 結果保存用ディレクトリを作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f"clustering_results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # クラスタリングアルゴリズムの選択と実行
    C_final, final_labels = None, None
    if algorithm_type == 'general':
        C_final, final_labels = general_kmeans_algorithm(
            X_data=X,  # 元のデータを使用（前処理なし）
            k=k_clusters,
            metric='euclidean',
            weights=FEATURE_WEIGHTS if dataset_name == 'real_code_features' else None
        )
        algo_title = "General K-means"
    elif algorithm_type == 'correctness_guided':
        if true_centers is None:
            print("❌ 正解判定関数を利用したクラスタリングには真のセントロイドが必要です。")
            print("   キャッシュファイルにパターン別セントロイド情報があることを確認してください。")
            raise ValueError("真のセントロイドが見つかりません。先にext_cfg_dfg_feature.pyを実行してセントロイドを生成してください。")

        print(f"🎯 正解判定関数を利用したクラスタリングを実行 (真のセントロイド数: {len(true_centers)})")
        C_final, final_labels = clustering_algorithm_with_correctness(
            X_data=X,
            k=k_clusters,
            is_correct_fn=is_correct_fn_factory(true_centers),
            metric='euclidean',
            weights=FEATURE_WEIGHTS if dataset_name == 'real_code_features' else None
        )
        algo_title = "Correctness-Guided K-means"
    else:
        raise ValueError(f"不明なアルゴリズムタイプです: {algorithm_type}. 'general' または 'correctness_guided' を指定してください。")

    # セントロイド距離の計算
    centroid_distance = calculate_average_min_centroid_distance(C_final, true_centers)

    # 結果の出力
    print(f"--- {dataset_name.capitalize()} Dataset Results ({algo_title}, k={k_clusters}) ---")
    print(f"最終的なセントロイド:\n", np.round(C_final, 2))
    if true_centers is not None and not np.isnan(centroid_distance):
        print(f"最終セントロイドと真のセントロイド間の平均最小距離: {centroid_distance:.4f}")
    else:
        print("真のセントロイドが存在しないため、セントロイド距離は計算されません。")
    print("-" * 50)

    # クラスタリング結果を保存
    saved_file = save_clustering_results(
        final_labels=final_labels,
        C_final=C_final,
        true_centers=true_centers,
        file_names=file_names,
        file_paths=file_paths,
        algorithm_type=algorithm_type,
        dataset_name=dataset_name,
        k_clusters=k_clusters,
        centroid_distance=centroid_distance,
        feature_vectors=X,
        output_dir=output_dir
    )

    # クラスタリング結果の詳細表示
    display_clustering_results(final_labels, C_final, file_names, dataset_name, file_paths, X)

    # 可視化（2次元データまたはPCAで次元削減）
    visualize_clustering_results(X, y_true, final_labels, C_final, true_centers,
                               dataset_name, algo_title, k_clusters, n_features, file_paths, output_dir)

    return saved_file, output_dir

def visualize_clustering_results(X, y_true, final_labels, C_final, true_centers,
                               dataset_name, algo_title, k_clusters, n_features, file_paths=None, output_dir=None):
    """クラスタリング結果の可視化（パターン別色分け対応）"""

    # 結果保存用ディレクトリを作成（シンプルな1階層）
    if output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"clustering_results_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

    # 複数の次元削減手法を試行
    reduction_results = {}

    if n_features > 2:
        print(f"\n📊 次元削減手法の比較実行:")

        # 1. PCA
        print("   🔄 PCA実行中...")
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X)
        C_pca = pca.transform(C_final)
        explained_var_ratio = pca.explained_variance_ratio_
        total_explained_var = np.sum(explained_var_ratio)

        reduction_results['PCA'] = {
            'X_2d': X_pca,
            'C_2d': C_pca,
            'title_suffix': f" (PCA 2D: {total_explained_var*100:.1f}% variance)",
            'info': f"PC1: {explained_var_ratio[0]*100:.1f}%, PC2: {explained_var_ratio[1]*100:.1f}%"
        }

        # 2. t-SNE
        if TSNE_AVAILABLE:
            print("   🔄 t-SNE実行中...")
            tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(X)-1), max_iter=1000)
            X_tsne = tsne.fit_transform(X)
            # t-SNEは学習したモデルでは変換できないため、セントロイドは別途計算
            C_tsne = np.array([np.mean(X_tsne[final_labels == i], axis=0) for i in range(len(C_final))])

            reduction_results['t-SNE'] = {
                'X_2d': X_tsne,
                'C_2d': C_tsne,
                'title_suffix': f" (t-SNE 2D)",
                'info': f"perplexity: {min(30, len(X)-1)}, max_iter: 1000"
            }
        else:
            print("   ⚠️ t-SNEは利用できません")

        # 3. UMAP
        if UMAP_AVAILABLE:
            print("   🔄 UMAP実行中...")
            umap_reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=min(15, len(X)-1))
            X_umap = umap_reducer.fit_transform(X)
            # UMAPもセントロイドは別途計算
            C_umap = np.array([np.mean(X_umap[final_labels == i], axis=0) for i in range(len(C_final))])

            reduction_results['UMAP'] = {
                'X_2d': X_umap,
                'C_2d': C_umap,
                'title_suffix': f" (UMAP 2D)",
                'info': f"n_neighbors: {min(15, len(X)-1)}"
            }
        else:
            print("   ⚠️ UMAPは利用できません")

        print(f"   ✅ 利用可能な次元削減手法: {list(reduction_results.keys())}")
    else:
        # 2次元データの場合
        reduction_results['Original'] = {
            'X_2d': X,
            'C_2d': C_final,
            'title_suffix': "",
            'info': "Original 2D data"
        }

    # パターンごとの色分け情報を取得
    pattern_groups = None
    pattern_colors = None
    pattern_labels = None

    if file_paths is not None and dataset_name == 'real_code_features':
        # 対象ディレクトリを取得
        target_directory = "../atcoder/submissions_typical90_d_100"

        # ファイルをパターン別にグループ分け
        pattern_groups = analyze_file_groups(file_paths, target_directory)

        # 色の設定
        color_palette = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'olive', 'cyan']
        pattern_colors = {}
        color_idx = 0

        for group_name in pattern_groups.keys():
            if group_name == 'other':
                pattern_colors[group_name] = 'gray'
            else:
                pattern_colors[group_name] = color_palette[color_idx % len(color_palette)]
                color_idx += 1

        # 各ファイルのパターンラベルを決定
        file_to_group = {}
        for group_name, group_files in pattern_groups.items():
            for file_info in group_files:
                file_to_group[file_info['file_path']] = group_name

        pattern_labels = [file_to_group.get(fp, 'other') for fp in file_paths]

    # 各次元削減手法ごとに可視化を実行
    for method_name, result in reduction_results.items():
        X_2d = result['X_2d']
        C_final_2d = result['C_2d']
        title_suffix = result['title_suffix']
        method_info = result['info']

        print(f"\n📈 {method_name}可視化実行中... ({method_info})")

        # 図を作成（情報表示スペースも確保）
        plt.figure(figsize=(18, 8))

        # 密集度に応じてプロット設定を調整
        n_points = len(X_2d)
        if n_points > 100:
            point_size = max(30, 100 - n_points // 10)  # 点数が多いほど小さく
            alpha_val = max(0.6, 1.0 - n_points / 500)  # 点数が多いほど透明に
        else:
            point_size = 60
            alpha_val = 0.8

        # 左側: パターン別色分け（全体表示）
        plt.subplot(1, 2, 1)
        if pattern_groups is not None:
            # パターンごとに色分けしてプロット
            for group_name in pattern_groups.keys():
                group_indices = [i for i, label in enumerate(pattern_labels) if label == group_name]
                if group_indices:
                    group_points = X_2d[group_indices]
                    plt.scatter(group_points[:, 0], group_points[:, 1],
                               c=pattern_colors[group_name],
                               label=f'{group_name} ({len(group_indices)})',
                               alpha=alpha_val, s=point_size, edgecolors='black', linewidth=0.5)

            plt.title(f"Pattern-based Grouping ({method_name})\n{dataset_name.capitalize()} Dataset{title_suffix}", fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)

        else:
            plt.scatter(X_2d[:, 0], X_2d[:, 1], c='gray', alpha=alpha_val, s=point_size)
            plt.title(f"Original Data ({method_name})\n{dataset_name.capitalize()} Dataset{title_suffix}")

        # 軸の範囲を適切に設定（負の値も見やすく）
        x_margin = (np.max(X_2d[:, 0]) - np.min(X_2d[:, 0])) * 0.05
        y_margin = (np.max(X_2d[:, 1]) - np.min(X_2d[:, 1])) * 0.05
        plt.xlim(np.min(X_2d[:, 0]) - x_margin, np.max(X_2d[:, 0]) + x_margin)
        plt.ylim(np.min(X_2d[:, 1]) - y_margin, np.max(X_2d[:, 1]) + y_margin)

        plt.xlabel(f"{method_name} Component 1" if n_features > 2 else "Feature 1", fontsize=11)
        plt.ylabel(f"{method_name} Component 2" if n_features > 2 else "Feature 2", fontsize=11)
        plt.grid(True, alpha=0.4)

        # 右側: クラスタリング結果（全体表示）
        plt.subplot(1, 2, 2)
        scatter2 = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=final_labels, cmap='tab10',
                              alpha=alpha_val, s=point_size, edgecolors='black', linewidth=0.5)
        plt.title(f"{algo_title} Results ({method_name})\n{dataset_name.capitalize()} Dataset{title_suffix}", fontsize=12)

        # クラスター情報を見やすく表示（カラーバーの代わり）
        unique_clusters = np.unique(final_labels)

        # 各クラスターの色を取得（tab10カラーマップを使用）
        tab10_colors = cm.get_cmap('tab10')

        # 色の凡例を個別に作成（右上に配置）
        legend_elements = []
        for cluster_id in unique_clusters:
            cluster_count = np.sum(final_labels == cluster_id)
            color_rgb = tab10_colors(cluster_id / 10.0)
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                            markerfacecolor=color_rgb, markersize=8,
                                            label=f'Cluster {cluster_id} ({cluster_count} files)'))

        # 最終セントロイドをプロット
        scatter_centroids = plt.scatter(C_final_2d[:, 0], C_final_2d[:, 1],
                   c='red', s=250, marker='X', edgecolor='black', linewidth=2,
                   alpha=1.0)

        # セントロイドの凡例を追加
        legend_elements.append(plt.Line2D([0], [0], marker='X', color='w',
                                        markerfacecolor='red', markersize=12, markeredgecolor='black',
                                        label='Final Centroids'))

        # 統合された凡例を表示
        plt.legend(handles=legend_elements, loc='upper right', fontsize=9,
                  bbox_to_anchor=(0.98, 0.98), framealpha=0.9)

        # 軸の範囲を適切に設定（負の値も見やすく）
        plt.xlim(np.min(X_2d[:, 0]) - x_margin, np.max(X_2d[:, 0]) + x_margin)
        plt.ylim(np.min(X_2d[:, 1]) - y_margin, np.max(X_2d[:, 1]) + y_margin)

        plt.xlabel(f"{method_name} Component 1" if n_features > 2 else "Feature 1", fontsize=11)
        plt.ylabel(f"{method_name} Component 2" if n_features > 2 else "Feature 2", fontsize=11)
        plt.grid(True, alpha=0.4)

        plt.tight_layout()

        # 画像として保存（タイムスタンプと手法名付き）
        method_filename = method_name.lower().replace('-', '_')
        # output_dirからタイムスタンプを抽出
        timestamp = output_dir.split('_')[-1] if 'clustering_results_' in output_dir else datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f"clustering_result_{dataset_name}_{algo_title.lower().replace(' ', '_').replace('-', '_')}_{method_filename}_{timestamp}.png")
        plt.savefig(filename, dpi=200, bbox_inches='tight')
        print(f"📸 {method_name}可視化結果を '{filename}' として保存しました。")

        plt.show()

        # 手法別の統計情報を表示
        print(f"\n📊 {method_name}統計情報:")
        print(f"  データ範囲 Dim1: [{np.min(X_2d[:, 0]):.2f}, {np.max(X_2d[:, 0]):.2f}]")
        print(f"  データ範囲 Dim2: [{np.min(X_2d[:, 1]):.2f}, {np.max(X_2d[:, 1]):.2f}]")
        print(f"  標準偏差 Dim1: {np.std(X_2d[:, 0]):.2f}")
        print(f"  標準偏差 Dim2: {np.std(X_2d[:, 1]):.2f}")
        print(f"  手法情報: {method_info}")

    # パターン分析結果の出力（プロットの外で表示）
    if pattern_groups is not None:
        print(f"\n🎨 パターン分析結果:")
        for group_name, group_files in pattern_groups.items():
            group_count = len([f for f in group_files if f['file_path'] in file_paths])
            print(f"  {group_name}: {group_count} ファイル (色: {pattern_colors[group_name]})")

    # クラスター分析結果の出力（プロットの外で表示）
    unique_clusters = np.unique(final_labels)
    print(f"\n📊 クラスター分析結果（詳細）:")
    print("=" * 80)

    if file_paths is not None:
        # ファイル名のリストを作成（JSONデータから）
        file_names_from_paths = [path.split('/')[-1] for path in file_paths]

        for cluster_id in unique_clusters:
            cluster_mask = final_labels == cluster_id
            cluster_files = [file_names_from_paths[i] for i in range(len(file_names_from_paths)) if cluster_mask[i]]
            cluster_paths = [file_paths[i] for i in range(len(file_paths)) if cluster_mask[i]]

            print(f"\n🏷️ Cluster {cluster_id} ({len(cluster_files)} ファイル):")

            # パターン別の分布を分析
            pattern_distribution = {}
            for path in cluster_paths:
                if 'pattern1' in path:
                    pattern_distribution['pattern1'] = pattern_distribution.get('pattern1', 0) + 1
                elif 'pattern2' in path:
                    pattern_distribution['pattern2'] = pattern_distribution.get('pattern2', 0) + 1
                elif 'pattern3' in path:
                    pattern_distribution['pattern3'] = pattern_distribution.get('pattern3', 0) + 1
                elif 'pattern4' in path:
                    pattern_distribution['pattern4'] = pattern_distribution.get('pattern4', 0) + 1
                else:
                    pattern_distribution['other'] = pattern_distribution.get('other', 0) + 1

            # パターン分布を表示
            if pattern_distribution:
                pattern_info = ", ".join([f"{pattern}: {count}" for pattern, count in pattern_distribution.items()])
                print(f"   📂 パターン分布: {pattern_info}")

            # ファイル一覧を表示
            print(f"   📄 ファイル一覧:")
            sorted_files = sorted(zip(cluster_files, cluster_paths))
            for i, (filename, filepath) in enumerate(sorted_files, 1):
                # パスからパターン情報を抽出
                if 'pattern' in filepath:
                    pattern_info = filepath.split('/')[-2] if '/' in filepath else 'unknown'
                else:
                    pattern_info = 'root'
                print(f"      {i:2d}. {filename:<25} ({pattern_info})")

                if i >= 15 and len(sorted_files) > 15:  # 15個まで表示
                    remaining = len(sorted_files) - 15
                    print(f"         ... および {remaining} 個のファイル")
                    break
    else:
        for cluster_id in unique_clusters:
            cluster_count = np.sum(final_labels == cluster_id)
            print(f"  Cluster {cluster_id}: {cluster_count} ファイル")

    print("=" * 80)

if __name__ == '__main__':

    # --- 実際のコード特徴量を使ったクラスタリング ---
    if FEATURE_EXTRACTION_AVAILABLE:
        print("\n=== Real Code Features Dataset: 実際のコードファイルからの特徴量クラスタリング ===")

        saved_files = []

        try:
            # 1. 一般的なK-meansアルゴリズムを実行
            print("\n🔄 一般的なK-meansクラスタリングを実行中...")
            general_result_file, general_output_dir = main(algorithm_type='general', dataset_name='real_code_features')
            saved_files.append(('general', general_result_file, general_output_dir))

        except Exception as e:
            print(f"❌ 一般的なK-meansクラスタリングでエラー: {e}")
            print("エラーの詳細を確認してください。")

        try:
            # 2. 正解判定関数を利用したクラスタリングを実行
            print("\n🎯 正解判定関数を利用したクラスタリングを実行中...")
            correctness_result_file, correctness_output_dir = main(algorithm_type='correctness_guided', dataset_name='real_code_features')
            saved_files.append(('correctness_guided', correctness_result_file, correctness_output_dir))

        except Exception as e:
            print(f"❌ 正解判定関数を利用したクラスタリングでエラー: {e}")
            print("エラーの詳細を確認してください。")

        # 結果サマリーの表示
        print(f"\n{'='*80}")
        print("🎉 クラスタリング実行完了サマリー")
        print(f"{'='*80}")

        if saved_files:
            for algorithm_type, result_file, output_dir in saved_files:
                if result_file:
                    print(f"✅ {algorithm_type.upper()}:")
                    print(f"   📁 結果ディレクトリ: {output_dir}")
                    print(f"   📄 結果ファイル: {os.path.basename(result_file)}")
                else:
                    print(f"❌ {algorithm_type.upper()}: 結果保存に失敗")
        else:
            print("❌ すべてのアルゴリズムで実行に失敗しました")

        print(f"{'='*80}")

    else:
        print("⚠️ 特徴量抽出モジュールが利用できないため、実際のコードファイル解析をスキップします。")
