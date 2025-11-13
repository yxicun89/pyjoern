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

# JSONファイル操作のインポート
import json

# 次元削減手法のインポート
try:
    from sklearn.manifold import TSNE
    TSNE_AVAILABLE = True
except ImportError:
    TSNE_AVAILABLE = False

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False

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
                return true_centers, pattern_labels
            else:
                return None, None
        else:
            return None, None

    except Exception as e:
        return None, None

# --- パターン情報を動的に検出する関数 ---
def extract_pattern_from_filepath(filepath):
    """
    ファイルパスからパターン情報を動的に抽出

    Args:
        filepath: ファイルパス

    Returns:
        str: パターン名 (例: "pattern4", "pattern5", "AC", "TLE", "other")
    """
    import re

    # パスを正規化（バックスラッシュをスラッシュに変換）
    normalized_path = filepath.replace('\\', '/')

    # ファイル名も確認
    filename = os.path.basename(filepath)

    # パターンを検出する正規表現のリスト（優先順位順）
    pattern_regexes = [
        # pattern + 数字（ファイル名またはパス内）
        (r'pattern(\d+)', lambda m: f"pattern{m.group(1)}"),
        # AC, TLE などの結果パターン（明確なアンダースコア区切り）
        (r'_([A-Z]{2,3})(?:_|$|/|\.)', lambda m: m.group(1)),
        # ディレクトリ名が結果を表す場合
        (r'/([A-Z]{2,3})/', lambda m: m.group(1)),
        # ファイル名の数字部分をパターンとして利用（submission_数字.py）
        (r'submission_(\d+)\.py', lambda m: f"sub{m.group(1)}"),
        # submissions_typical90_xx パターン
        (r'submissions_typical90_([a-z]+)', lambda m: f"typical90_{m.group(1)}"),
        # その他のsubmissions_パターン
        (r'submissions_([^/]+?)(?:_\d+)?/', lambda m: m.group(1) if not m.group(1).startswith('submission') else None),
    ]

    # ファイル全体のパスで検索
    for pattern_regex, extract_func in pattern_regexes:
        match = re.search(pattern_regex, normalized_path)
        if match:
            result = extract_func(match)
            if result:
                # 一般的でない形式や短すぎるパターンを除外
                if len(result) >= 2 and not result.isdigit():
                    return result

    # ファイル名からパターンを抽出する最後の試行
    filename_patterns = [
        (r'^([a-z]+\d*)_', lambda m: m.group(1)),  # prefix_xxx形式
        (r'_([a-z]+\d*)\.', lambda m: m.group(1)), # xxx_suffix.ext形式
        (r'(\d+)', lambda m: f"num{m.group(1)}"),  # 数字のみの場合
    ]

    for pattern_regex, extract_func in filename_patterns:
        match = re.search(pattern_regex, filename.lower())
        if match:
            result = extract_func(match)
            if result and len(result) >= 2:
                return result

    return "other"

def get_all_patterns_from_paths(file_paths):
    """
    ファイルパスのリストから全ての利用可能なパターンを取得

    Args:
        file_paths: ファイルパスのリスト

    Returns:
        set: 検出されたパターンの集合
    """
    patterns = set()
    for filepath in file_paths:
        pattern = extract_pattern_from_filepath(filepath)
        patterns.add(pattern)
    return patterns

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

                    # パターン情報を動的に抽出
                    filepath = file_paths[idx]
                    file_info["pattern"] = extract_pattern_from_filepath(filepath)

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

    #     C = new_C

    # # 最終的なラベル付け
    # final_labels = np.zeros(len(X_data), dtype=int)
    # for i, S in enumerate(X_data):
    #     dists = [dist(c, S, metric, weights=weights) for c in C]
    #     final_labels[i] = np.argmin(dists)

    # return C, final_labels

# --- データセット作成関数 ---
def create_dataset(dataset_name: str, n_samples: int = 300, target_directory: str = None, k_clusters: int = None):
    if dataset_name == 'real_code_features':
        # 実際のコードファイルから特徴量を抽出（キャッシュ対応）
        if not FEATURE_EXTRACTION_AVAILABLE:
            raise ValueError("特徴量抽出モジュールが利用できません。ext_cfg_dfg_feature.pyのインポートを確認してください。")

        # ディレクトリパスを指定（ユーザー入力または対話式入力）
        if target_directory is None:
            # 利用可能なディレクトリを自動検出
            atcoder_base = "../atcoder"
            if os.path.exists(atcoder_base):
                available_dirs = []
                try:
                    for item in os.listdir(atcoder_base):
                        item_path = os.path.join(atcoder_base, item)
                        if os.path.isdir(item_path) and item.startswith("submissions_typical90_"):
                            available_dirs.append(item)

                    if available_dirs:
                        available_dirs.sort()
                        for i, dirname in enumerate(available_dirs, 1):
                            print(f"  {i}. {dirname}")

                        user_input = input("選択 (数字またはパス): ").strip()

                        # 数字での選択の場合
                        try:
                            choice_num = int(user_input)
                            if 1 <= choice_num <= len(available_dirs):
                                target_directory = os.path.join(atcoder_base, available_dirs[choice_num - 1])
                            else:
                                target_directory = user_input
                        except ValueError:
                            target_directory = user_input
                    else:
                        target_directory = input("ディレクトリパスを直接入力: ").strip()
                except Exception:
                    target_directory = input("ディレクトリパスを直接入力: ").strip()
            else:
                target_directory = input("ディレクトリパス: ").strip()

            if not target_directory:
                target_directory = "../atcoder/submissions_typical90_d_15_AC_TLE"

        if not os.path.exists(target_directory):
            raise ValueError(f"指定されたディレクトリが存在しません: {target_directory}")

        # キャッシュファイル名を生成
        cache_file = f"feature_cache_{os.path.basename(target_directory)}.json"

        # ファイルを検索
        code_files = find_files_in_directory(target_directory)

        if len(code_files) == 0:
            raise ValueError(f"指定されたディレクトリにコードファイルが見つかりません: {target_directory}")

        # ファイルをグループ分析（セントロイド計算用）
        groups = analyze_file_groups(code_files, target_directory)

        # キャッシュの有効性をチェック
        batch_results = None
        use_cache = False

        if os.path.exists(cache_file):
            if check_cache_validity(target_directory, cache_file):
                use_cache = True
            else:
                use_cache = False
        else:
            use_cache = False

        if use_cache:
            # キャッシュから読み込み
            cached_data = load_feature_vectors(cache_file)
            if cached_data:
                batch_results = cached_data['data']

        if batch_results is None:
            # 新規抽出
            batch_results = batch_extract_integrated_features(code_files)
            # 結果をキャッシュに保存
            save_feature_vectors(batch_results, groups=groups, base_directory=target_directory, output_file=cache_file, format='json')

        # 成功した結果のみを使用
        successful_results = [r for r in batch_results if 'error' not in r]

        if len(successful_results) == 0:
            raise ValueError("すべてのファイルで特徴量抽出に失敗しました")

        # 特徴量ベクトルを取得
        X = np.array([r['integrated_vector'] for r in successful_results])

        # クラスター数を指定（ユーザー入力または自動決定）
        if k_clusters is None:
            while True:
                try:
                    k_input = input(f"クラスター数K (デフォルト: 2, 推奨範囲: 2～{min(10, len(successful_results)//2)}): ").strip()
                    if not k_input:
                        k_clusters = 2
                        break

                    k_clusters = int(k_input)
                    if k_clusters < 2:
                        print("❌ クラスター数は2以上である必要があります")
                        continue
                    elif k_clusters > len(successful_results):
                        print(f"❌ クラスター数はデータ数({len(successful_results)})以下である必要があります")
                        continue
                    else:
                        break
                except ValueError:
                    print("❌ 有効な整数を入力してください")

        n_features = 11

        # 実際のデータには真のラベルがないため、仮のラベルを作成
        y_true = np.zeros(len(successful_results))  # すべて同じクラスターとして扱う

        # ファイル名を保存（後で参照用）
        file_names = [os.path.basename(r['source_file']) for r in successful_results]

        # ファイルパスを保存（グループ分析用）
        file_paths = [r['source_file'] for r in successful_results]

        # 真のセントロイドをキャッシュファイルから読み込み
        true_centers, pattern_labels = load_true_centroids_from_cache(cache_file)

        # 外れ値（otherパターン）の処理方針確認
        other_count = len([fp for fp in file_paths if extract_pattern_from_filepath(fp) == "other"])

        if true_centers is not None:
            # 真のセントロイドから'other'パターンを除外（意味あるパターンのみでクラスタリング）
            filtered_pattern_labels = []
            filtered_true_centers = []

            for i, label in enumerate(pattern_labels):
                if label != "other":  # 'other'以外のパターンのみを使用
                    filtered_pattern_labels.append(label)
                    filtered_true_centers.append(true_centers[i])

            if filtered_true_centers:
                true_centers = np.array(filtered_true_centers)
                pattern_labels = filtered_pattern_labels
            else:
                true_centers = None

            # パターン数に基づいてクラスター数を提案
            if true_centers is not None:
                suggested_k = len(true_centers)

                if k_clusters != suggested_k:
                    adjust_choice = input(f"推奨クラスター数: {suggested_k} (意味あるパターン: {pattern_labels}). 調整しますか？ (y/n): ").strip().lower()
                    if adjust_choice in ['y', 'yes', '']:
                        k_clusters = suggested_k

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
    クラスタリング結果のサマリー表示（簡潔版）

    Args:
        final_labels: クラスターラベル
        C_final: 最終セントロイド
        file_names: ファイル名リスト
        dataset_name: データセット名
        file_paths: ファイルパスリスト
        feature_vectors: 特徴量ベクトル
    """
    print(f"\n📊 {dataset_name.upper()} クラスタリング結果")
    print("=" * 80)

    unique_labels = np.unique(final_labels)
    print(f"総クラスター数: {len(unique_labels)} | 総サンプル数: {len(final_labels)}")

    for cluster_id in unique_labels:
        cluster_indices = np.where(final_labels == cluster_id)[0]
        cluster_size = len(cluster_indices)

        print(f"\n🏷️ Cluster {cluster_id} ({cluster_size} ファイル):")

        if file_names and file_paths:
            # ファイル名でソート
            cluster_data = []
            for idx in cluster_indices:
                cluster_data.append({
                    'filename': file_names[idx],
                    'filepath': file_paths[idx],
                    'pattern': extract_pattern_from_filepath(file_paths[idx])
                })
            cluster_data.sort(key=lambda x: x['filename'])

            # パターン別統計
            pattern_counts = {}
            for data in cluster_data:
                pattern = data['pattern']
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

            # パターン分布を表示（個数とクラスター内%）
            if pattern_counts:
                pattern_details = []
                for pattern, count in sorted(pattern_counts.items()):
                    pattern_details.append(f"{pattern}: {count}")
                pattern_info = ", ".join(pattern_details)
                print(f"   📂 パターン分布: {pattern_info}")

                # パーセンテージ表示を追加
                percentage_details = []
                for pattern, count in sorted(pattern_counts.items()):
                    percentage = (count / cluster_size) * 100
                    percentage_details.append(f"{pattern}: {percentage:.4f}%")
                percentage_info = ", ".join(percentage_details)
                print(f"   📊 パーセンテージ: {percentage_info}")

            # ファイル一覧を表示（全ファイル詳細表示）
            print(f"   📄 ファイル一覧:")
            for i, data in enumerate(cluster_data, 1):
                pattern_mark = "⚠️" if data['pattern'] == 'other' else ""
                print(f"       {i:2d}. {data['filename']:<25} ({data['pattern']}){pattern_mark}")

    print("=" * 80)

def main(algorithm_type: str, dataset_name: str, preloaded_data=None, target_directory: str = None, k_clusters: int = None):
    # データセットの生成または事前ロード済みデータの使用
    if preloaded_data is None:
        result = create_dataset(dataset_name, target_directory=target_directory, k_clusters=k_clusters)
    else:
        result = preloaded_data

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
            raise ValueError("正解判定関数を利用したクラスタリングには真のセントロイドが必要です。")

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
    print(f"\n📊 {dataset_name} - {algo_title} (k={k_clusters})")
    if true_centers is not None and not np.isnan(centroid_distance):
        print(f"セントロイド距離: {centroid_distance:.4f}")
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
        # 1. PCA
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
            tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(X)-1), max_iter=1000)
            X_tsne = tsne.fit_transform(X)
            C_tsne = np.array([np.mean(X_tsne[final_labels == i], axis=0) for i in range(len(C_final))])

            reduction_results['t-SNE'] = {
                'X_2d': X_tsne,
                'C_2d': C_tsne,
                'title_suffix': f" (t-SNE 2D)",
                'info': f"perplexity: {min(30, len(X)-1)}, max_iter: 1000"
            }

        # 3. UMAP
        if UMAP_AVAILABLE:
            umap_reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=min(15, len(X)-1))
            X_umap = umap_reducer.fit_transform(X)
            C_umap = np.array([np.mean(X_umap[final_labels == i], axis=0) for i in range(len(C_final))])

            reduction_results['UMAP'] = {
                'X_2d': X_umap,
                'C_2d': C_umap,
                'title_suffix': f" (UMAP 2D)",
                'info': f"n_neighbors: {min(15, len(X)-1)}"
            }
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
        # 動的パターン検出を使用
        all_patterns = get_all_patterns_from_paths(file_paths)

        # パターン別にグループ化
        pattern_groups = {}
        for pattern in all_patterns:
            pattern_groups[pattern] = []

        for i, filepath in enumerate(file_paths):
            pattern = extract_pattern_from_filepath(filepath)
            pattern_groups[pattern].append({
                'file_path': filepath,
                'index': i
            })

        # 色の設定
        color_palette = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'olive', 'cyan']
        pattern_colors = {}
        color_idx = 0

        # パターン別の色割り当て（'other'も通常の色で表示）
        for group_name in sorted(pattern_groups.keys()):
            if group_name == 'other':
                pattern_colors[group_name] = 'lightcoral'
            else:
                pattern_colors[group_name] = color_palette[color_idx % len(color_palette)]
                color_idx += 1

        # 各ファイルのパターンラベルを決定
        pattern_labels = [extract_pattern_from_filepath(fp) for fp in file_paths]

    # 各次元削減手法ごとに可視化を実行
    for method_name, result in reduction_results.items():
        X_2d = result['X_2d']
        C_final_2d = result['C_2d']
        title_suffix = result['title_suffix']
        method_info = result['info']

        # 図を作成
        plt.figure(figsize=(18, 8))

        # 密集度に応じてプロット設定を調整
        n_points = len(X_2d)
        point_size = max(30, 100 - n_points // 10) if n_points > 100 else 60
        alpha_val = max(0.6, 1.0 - n_points / 500) if n_points > 100 else 0.8

        # 左側: パターン別色分け
        plt.subplot(1, 2, 1)
        if pattern_groups is not None:
            for group_name in pattern_groups.keys():
                group_indices = [i for i, label in enumerate(pattern_labels) if label == group_name]
                if group_indices:
                    group_points = X_2d[group_indices]
                    if group_name == 'other':
                        plt.scatter(group_points[:, 0], group_points[:, 1],
                                   c=pattern_colors[group_name],
                                   label=f'{group_name} (外れ値, {len(group_indices)})',
                                   alpha=alpha_val, s=point_size,
                                   edgecolors='black', linewidth=0.8, marker='^')
                    else:
                        plt.scatter(group_points[:, 0], group_points[:, 1],
                                   c=pattern_colors[group_name],
                                   label=f'{group_name} ({len(group_indices)})',
                                   alpha=alpha_val, s=point_size, edgecolors='black', linewidth=0.5)

            plt.title(f"Pattern-based Grouping ({method_name})", fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        else:
            plt.scatter(X_2d[:, 0], X_2d[:, 1], c='gray', alpha=alpha_val, s=point_size)
            plt.title(f"Original Data ({method_name})")

        plt.xlabel(f"{method_name} Component 1" if n_features > 2 else "Feature 1")
        plt.ylabel(f"{method_name} Component 2" if n_features > 2 else "Feature 2")
        plt.grid(True, alpha=0.4)

        # 右側: クラスタリング結果
        plt.subplot(1, 2, 2)
        plt.scatter(X_2d[:, 0], X_2d[:, 1], c=final_labels, cmap='tab10',
                   alpha=alpha_val, s=point_size, edgecolors='black', linewidth=0.5)
        plt.title(f"{algo_title} Results ({method_name})", fontsize=12)

        # セントロイドをプロット
        plt.scatter(C_final_2d[:, 0], C_final_2d[:, 1],
                   c='red', s=250, marker='X', edgecolor='black', linewidth=2, alpha=1.0)

        # クラスター統計を凡例として表示
        unique_clusters = np.unique(final_labels)
        legend_elements = []
        for cluster_id in unique_clusters:
            cluster_count = np.sum(final_labels == cluster_id)
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                            markerfacecolor=cm.get_cmap('tab10')(cluster_id / 10.0), markersize=8,
                                            label=f'C{cluster_id} ({cluster_count})'))
        legend_elements.append(plt.Line2D([0], [0], marker='X', color='w',
                                        markerfacecolor='red', markersize=12, markeredgecolor='black',
                                        label='Centroids'))
        plt.legend(handles=legend_elements, loc='upper right', fontsize=9)

        plt.xlabel(f"{method_name} Component 1" if n_features > 2 else "Feature 1")
        plt.ylabel(f"{method_name} Component 2" if n_features > 2 else "Feature 2")
        plt.grid(True, alpha=0.4)

        plt.tight_layout()

        # 画像として保存
        method_filename = method_name.lower().replace('-', '_')
        timestamp = output_dir.split('_')[-1] if 'clustering_results_' in output_dir else datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f"clustering_result_{dataset_name}_{algo_title.lower().replace(' ', '_').replace('-', '_')}_{method_filename}_{timestamp}.png")
        plt.savefig(filename, dpi=200, bbox_inches='tight')

        print(f"\n📈 {method_name}可視化結果を '{filename}' として保存しました。")

        plt.show()

if __name__ == '__main__':

    # --- 実際のコード特徴量を使ったクラスタリング ---
    if FEATURE_EXTRACTION_AVAILABLE:
        # 実行履歴を追跡
        executed_directories = []
        all_saved_files = []

        # 連続実行ループ
        while True:
            saved_files = []
            shared_data = None

            try:
                # データセット作成
                shared_data = create_dataset('real_code_features')
            except Exception as e:
                print(f"❌ データセット作成エラー: {e}")
                shared_data = None

            if shared_data is not None:
                # 実行したディレクトリを記録
                if len(shared_data) >= 7:
                    current_dir = os.path.basename(os.path.dirname(shared_data[6][0])) if shared_data[6] else "unknown"
                    if current_dir not in executed_directories:
                        executed_directories.append(current_dir)

                try:
                    # 1. 一般的なK-meansアルゴリズム
                    general_result_file, general_output_dir = main(algorithm_type='general', dataset_name='real_code_features', preloaded_data=shared_data)
                    saved_files.append(('general', general_result_file, general_output_dir))
                    all_saved_files.append(('general', general_result_file, general_output_dir, current_dir))
                except Exception as e:
                    print(f"❌ 一般的なK-meansクラスタリングエラー: {e}")

                try:
                    # 2. 正解判定関数を利用したクラスタリング
                    correctness_result_file, correctness_output_dir = main(algorithm_type='correctness_guided', dataset_name='real_code_features', preloaded_data=shared_data)
                    saved_files.append(('correctness_guided', correctness_result_file, correctness_output_dir))
                    all_saved_files.append(('correctness_guided', correctness_result_file, correctness_output_dir, current_dir))
                except Exception as e:
                    print(f"❌ 正解判定関数クラスタリングエラー: {e}")

                # 結果サマリー
                print(f"\n{'='*60}")
                print("🎉 クラスタリング完了")
                if saved_files:
                    for algorithm_type, result_file, output_dir in saved_files:
                        if result_file:
                            print(f"✅ {algorithm_type.upper()}: {os.path.basename(result_file)}")
                        else:
                            print(f"❌ {algorithm_type.upper()}: 保存失敗")
                print(f"{'='*60}")

            # 次の実行選択
            atcoder_base = "../atcoder"
            available_dirs = []
            if os.path.exists(atcoder_base):
                try:
                    for item in os.listdir(atcoder_base):
                        item_path = os.path.join(atcoder_base, item)
                        if os.path.isdir(item_path) and item.startswith("submissions_typical90_"):
                            available_dirs.append(item)
                    available_dirs.sort()
                except Exception:
                    pass

            # 選択肢を表示
            if available_dirs:
                print(f"\n利用可能ディレクトリ:")
                for i, dirname in enumerate(available_dirs, 1):
                    status = " (✅)" if dirname in executed_directories else ""
                    print(f"  {i}. {dirname}{status}")
                print(f"  0. 終了")

                choice = input(f"\n選択 (0-{len(available_dirs)}): ").strip()

                if choice == "0" or choice.lower() in ['exit', 'quit', 'q']:
                    # 全体のサマリーを表示
                    if all_saved_files:
                        print(f"\n{'='*80}")
                        print("🎊 全実行サマリー")
                        print(f"{'='*80}")
                        print(f"📊 実行ディレクトリ数: {len(executed_directories)}")
                        print(f"📁 実行済みディレクトリ: {', '.join(executed_directories)}")
                        print(f"� 生成ファイル数: {len(all_saved_files)}")

                        print(f"\n📂 ディレクトリ別結果:")
                        current_dir_files = {}
                        for algo_type, result_file, output_dir, dir_name in all_saved_files:
                            if dir_name not in current_dir_files:
                                current_dir_files[dir_name] = []
                            current_dir_files[dir_name].append((algo_type, result_file, output_dir))

                        for dir_name, files in current_dir_files.items():
                            print(f"   📁 {dir_name}:")
                            for algo_type, result_file, output_dir in files:
                                if result_file:
                                    print(f"      ✅ {algo_type}: {os.path.basename(result_file)}")
                                else:
                                    print(f"      ❌ {algo_type}: 保存失敗")
                        print(f"{'='*80}")

                    print("�👋 プログラムを終了します。")
                    break
                elif choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(available_dirs):
                        # 選択されたディレクトリで次回実行
                        selected_dir = available_dirs[choice_num - 1]
                        if selected_dir in executed_directories:
                            confirm = input(f"⚠️ {selected_dir} は既に実行済みです。再実行しますか？ (y/n): ").strip().lower()
                            if confirm not in ['y', 'yes', '']:
                                continue
                        print(f"📁 次回実行ディレクトリ: {selected_dir}")
                        continue
                    elif choice_num == len(available_dirs) + 1:
                        print("📝 別のディレクトリパスを次回入力で指定できます。")
                        continue
                    else:
                        print("❌ 無効な選択です。終了します。")
                        break
                else:
                    print("❌ 無効な入力です。終了します。")
                    break
            else:
                # ディレクトリが見つからない場合
                print("📂 利用可能なディレクトリ情報を取得できませんでした。")
                continue_choice = input("別のディレクトリで続行しますか？ (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes', '']:
                    print("👋 プログラムを終了します。")
                    break

    else:
        print("⚠️ 特徴量抽出モジュールが利用できないため、実際のコードファイル解析をスキップします。")
