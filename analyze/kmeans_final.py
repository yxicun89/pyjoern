# cleanが使ってる方

# # 研究会の時に示していたコード
# # 11次元でクラスタリングできます

# import numpy as np
# from sklearn.cluster import KMeans
# from sklearn.metrics.pairwise import cosine_distances
# from sklearn.datasets import make_blobs, make_circles, make_moons, load_iris, load_wine
# from sklearn.decomposition import PCA
# import matplotlib.pyplot as plt
# import os
# from datetime import datetime

# # オプショナルライブラリのインポート
# try:
#     import seaborn as sns
#     import pandas as pd
#     ADVANCED_VIZ_AVAILABLE = True
# except ImportError:
#     ADVANCED_VIZ_AVAILABLE = False
#     print("⚠️ seaborn/pandasが利用できません。基本的な可視化のみ実行します。")
#     print("   高度な可視化には: pip install seaborn pandas を実行してください。")

# # ext_cfg_dfg_feature.pyから特徴量抽出関数をインポート
# try:
#     from ext_cfg_dfg_feature import (
#         extract_integrated_features_vector,
#         batch_extract_integrated_features,
#         find_files_in_directory,
#         load_feature_vectors,
#         save_feature_vectors,
#         check_cache_validity,
#         analyze_file_groups
#     )
#     FEATURE_EXTRACTION_AVAILABLE = True
# except ImportError as e:
#     print(f"❌ 特徴量抽出モジュールのインポートエラー: {e}")
#     print("ext_cfg_dfg_feature.pyが同じディレクトリにあることを確認してください。")
#     FEATURE_EXTRACTION_AVAILABLE = False

# # --- 特徴量の重みを定義 ---
# # connected_components, loop_statements, conditional_statements, cycles, paths, cyclomatic_complexity
# # variable_count, total_reads, total_writes, max_reads, max_writes に対応
# FEATURE_WEIGHTS = np.array([
#     1.0, # connected_components
#     1.0, # loop_statements
#     1.0, # conditional_statements
#     1.0, # cycles
#     1.0, # paths
#     1.0, # cyclomatic_complexity
#     0.6, # variable_count
#     0.1, # total_reads
#     0.1, # total_writes
#     0.1, # max_reads
#     0.1  # max_writes
# ])

# # --- 距離関数（重み付きユークリッド距離、マンハッタン距離、コサイン距離） ---
# def dist(c, s, metric='euclidean', weights=None):
#     if metric == 'euclidean':
#         if weights is None:
#             return np.linalg.norm(c - s)
#         else:
#             # 重み付きユークリッド距離: sqrt(sum(w_i * (c_i - s_i)^2))
#             return np.sqrt(np.sum(weights * (c - s)**2))
#     elif metric == 'manhattan':
#         if weights is None:
#             return np.sum(np.abs(c - s))
#         else:
#             # 重み付きマンハッタン距離: sum(w_i * |c_i - s_i|)
#             return np.sum(weights * np.abs(c - s))
#     elif metric == 'cosine':
#         if weights is None:
#             return cosine_distances([c], [s])[0][0]
#         else:
#             # 重み付きコサイン距離: 重みをsqrt(w_i)で特徴量に適用してからコサイン距離を計算
#             c_w = c * np.sqrt(weights)
#             s_w = s * np.sqrt(weights)
#             return cosine_distances([c_w], [s_w])[0][0]
#     else:
#         raise ValueError(f"未知の距離関数です: {metric}")

# # --- K-means++ 初期化 ---
# def initialize_centroids(X_data, k):
#     kmeans = KMeans(n_clusters=k, init='k-means++', n_init='auto', random_state=42)
#     kmeans.fit(X_data)
#     return kmeans.cluster_centers_

# # --- 一般的なK-meansクラスタリングアルゴリズム ---
# def general_kmeans_algorithm(X_data, k, metric='euclidean', weights=None, max_iterations=100):
#     C = initialize_centroids(X_data, k)

#     for iteration in range(max_iterations):
#         # ステップ 1: 各データポイントを最も近いセントロイドに割り当てる
#         labels = np.zeros(len(X_data), dtype=int)
#         for i, S in enumerate(X_data):
#             dists = [dist(c, S, metric, weights=weights) for c in C]
#             labels[i] = np.argmin(dists)

#         # ステップ 2: 新しいクラスター割り当てに基づいてセントロイドを更新
#         new_C = np.zeros((k, X_data.shape[1]))
#         for i in range(k):
#             points_in_cluster = X_data[labels == i]
#             if len(points_in_cluster) > 0:
#                 new_C[i] = np.mean(points_in_cluster, axis=0)
#             else:
#                 # クラスターが空になった場合、データ全体の範囲内でランダムに再初期化する
#                 min_val = np.min(X_data, axis=0)
#                 max_val = np.max(X_data, axis=0)
#                 new_C[i] = np.random.uniform(min_val, max_val, X_data.shape[1])

#         # 収束判定: セントロイドがほとんど変化しなくなったら停止
#         if np.allclose(C, new_C):
#             break

#         C = new_C

#     # 最終的なラベル付け
#     final_labels = np.zeros(len(X_data), dtype=int)
#     for i, S in enumerate(X_data):
#         dists = [dist(c, S, metric, weights=weights) for c in C]
#         final_labels[i] = np.argmin(dists)

#     return C, final_labels

# # --- クラスタリングアルゴリズム（正解判定関数利用)---
# # def clustering_algorithm_with_correctness(X_data, k, is_correct_fn, metric='euclidean', weights=None):
# #     C = initialize_centroids(X_data, k)
# #     N = np.zeros(k) # 各クラスターに割り当てられたデータポイントの数

# #     for S in X_data:
# #         # 各データポイント S を最も近いセントロイドに割り当てる
# #         dists = [dist(c, S, metric, weights=weights) for c in C]
# #         min_c = np.argmin(dists) # 割り当てられたクラスターのインデックス

# #         N[min_c] += 1

# #         # 正解判定関数がTrueを返した場合にのみセントロイドを更新
# #         if is_correct_fn(S, min_c):
# #             # オンライン学習に似たセントロイド更新（1点ごとの移動平均）
# #             C[min_c] = C[min_c] + (1 / N[min_c]) * (S - C[min_c])

# #     # 最終的なラベル付け
# #     final_labels = np.zeros(len(X_data), dtype=int)
# #     for i, S in enumerate(X_data):
# #         dists = [dist(c, S, metric, weights=weights) for c in C]
# #         final_labels[i] = np.argmin(dists)

# #     return C, final_labels

# # --- 正解判定関数を生成するファクトリ関数（教師あり） ---
# # def is_correct_fn_factory(true_centers):
# #     if true_centers is None:
# #         # 真のクラスター中心がない場合は、常にTrueを返す
# #         print("Warning: No true_centers provided for correctness check. The algorithm will always consider an assignment 'correct'. This might not be the intended use.")
# #         return lambda S, assigned_cluster_idx: True

# #     def is_correct(S, assigned_cluster_idx):
# #         # データポイント S がどの真のクラスター中心に最も近いかを判断
# #         true_dists = [np.linalg.norm(tc - S) for tc in true_centers]
# #         correct_cluster_idx = np.argmin(true_dists)

# #         # アルゴリズムが割り当てたクラスターと真のクラスターが一致するかどうかを返す
# #         return assigned_cluster_idx == correct_cluster_idx
# #     return is_correct

# # --- データセット作成関数 ---
# def create_dataset(dataset_name: str, n_samples: int = 300):
#     if dataset_name == 'real_code_features':
#         # 実際のコードファイルから特徴量を抽出（キャッシュ対応）
#         if not FEATURE_EXTRACTION_AVAILABLE:
#             raise ValueError("特徴量抽出モジュールが利用できません。ext_cfg_dfg_feature.pyのインポートを確認してください。")

#         # ディレクトリパスを指定（相対パスまたは絶対パス）
#         target_directory = "../atcoder/submissions_typical90_d_100"

#         if not os.path.exists(target_directory):
#             raise ValueError(f"指定されたディレクトリが存在しません: {target_directory}")

#         # キャッシュファイル名を生成
#         cache_file = f"feature_cache_{os.path.basename(target_directory)}.json"

#         # ファイルを検索
#         code_files = find_files_in_directory(target_directory)

#         if len(code_files) == 0:
#             raise ValueError(f"指定されたディレクトリにコードファイルが見つかりません: {target_directory}")

#         print(f"🔍 発見されたファイル数: {len(code_files)}")
#         for i, file in enumerate(code_files[:5]):  # 最初の5ファイルを表示
#             print(f"  {i+1}. {os.path.relpath(file, target_directory)}")
#         if len(code_files) > 5:
#             print(f"  ... および {len(code_files) - 5} 個のファイル")

#         # キャッシュの有効性をチェック
#         batch_results = None
#         use_cache = False

#         if os.path.exists(cache_file):
#             if check_cache_validity(target_directory, cache_file):
#                 print(f"📦 有効なキャッシュファイルを発見: {cache_file}")
#                 print("キャッシュを使用してクラスタリングを実行します。")
#                 use_cache = True
#             else:
#                 print(f"⚠️ キャッシュファイルは古いため、再抽出が必要です")

#         if use_cache:
#             # キャッシュから読み込み
#             print(f"📂 キャッシュから特徴量を読み込み中...")
#             cached_data = load_feature_vectors(cache_file)
#             if cached_data:
#                 batch_results = cached_data['data']
#                 print(f"✅ キャッシュから {len(batch_results)} ファイルの特徴量を読み込みました")

#         if batch_results is None:
#             # 新規抽出
#             print("📊 特徴量抽出中...")
#             batch_results = batch_extract_integrated_features(code_files)

#             # 結果をキャッシュに保存
#             print(f"💾 特徴量をキャッシュに保存中...")
#             save_feature_vectors(batch_results, cache_file, format='json')

#         # 成功した結果のみを使用
#         successful_results = [r for r in batch_results if 'error' not in r]

#         if len(successful_results) == 0:
#             raise ValueError("すべてのファイルで特徴量抽出に失敗しました")

#         print(f"✅ 特徴量抽出成功: {len(successful_results)} / {len(code_files)} ファイル")

#         # 特徴量ベクトルを取得
#         X = np.array([r['integrated_vector'] for r in successful_results])

#         # クラスター数を自動決定（ファイル数に基づく）
#         # k_clusters = min(max(2, len(successful_results) // 5), 5)  # 2-5クラスター
#         k_clusters = 5
#         n_features = 11

#         # 実際のデータには真のラベルがないため、仮のラベルを作成
#         y_true = np.zeros(len(successful_results))  # すべて同じクラスターとして扱う

#         # ファイル名を保存（後で参照用）
#         file_names = [os.path.basename(r['source_file']) for r in successful_results]

#         # ファイルパスを保存（グループ分析用）
#         file_paths = [r['source_file'] for r in successful_results]

#         print(f"📈 データセット準備完了: {len(X)} サンプル, {n_features} 特徴量, {k_clusters} クラスター")

#         # ファイル名とパス情報を返り値に含める（デバッグ用）
#         return X, y_true, k_clusters, n_features, None, file_names, file_paths

#     else:
#         raise ValueError(f"不明なデータセット名です: {dataset_name}")

#     # # 真のセントロイドを計算（実際のコードデータには真のクラスターがない）
#     # true_centers_calc = None
#     # if dataset_name == 'random':
#     #     # randomデータには真のクラスターがないため、true_centersはNone
#     #     pass
#     # elif dataset_name == 'real_code_features':
#     #     # 実際のコードデータには真のクラスターがないため、true_centersはNone
#     #     pass
#     # else: # その他のデータセットではy_trueを基に計算される
#     #     true_centers_calc = np.array([X[y_true == i].mean(axis=0) for i in range(k_clusters)])

#     return X, y_true, k_clusters, n_features, true_centers_calc

# # --- 最終的なセントロイドと真のセントロイド間の平均最小距離を計算する---
# def calculate_average_min_centroid_distance(final_centroids, true_centers):
#     if final_centroids is None or true_centers is None:
#         return np.nan

#     num_final = final_centroids.shape[0]
#     num_true = true_centers.shape[0]

#     # クラスター数が異なる場合は警告（ただし計算は続行）
#     if num_final != num_true:
#         print(f"Warning: Number of final centroids ({num_final}) does not match number of true centers ({num_true}). "
#               "Distance calculation might be less meaningful.")

#     min_distances = []
#     for f_center in final_centroids:
#         # 各最終セントロイドについて、全ての真のセントロイドとの距離を計算
#         distances_to_true = [np.linalg.norm(f_center - t_center) for t_center in true_centers]
#         min_distances.append(np.min(distances_to_true))

#     return np.mean(min_distances)

# def display_clustering_results(final_labels, C_final, file_names=None, dataset_name="unknown"):
#     """
#     クラスタリング結果を詳細表示

#     Args:
#         final_labels: クラスターラベル
#         C_final: 最終セントロイド
#         file_names: ファイル名リスト
#         dataset_name: データセット名
#     """
#     print(f"\n📊 === {dataset_name.upper()} クラスタリング結果詳細 ===")

#     unique_labels = np.unique(final_labels)
#     print(f"🔢 総クラスター数: {len(unique_labels)}")
#     print(f"📁 総サンプル数: {len(final_labels)}")

#     print(f"\n🎯 各クラスターの詳細:")
#     print("-" * 80)

#     for cluster_id in unique_labels:
#         cluster_indices = np.where(final_labels == cluster_id)[0]
#         cluster_size = len(cluster_indices)

#         print(f"\n🏷️  クラスター {cluster_id}:")
#         print(f"   📊 サイズ: {cluster_size} サンプル ({cluster_size/len(final_labels)*100:.1f}%)")
#         print(f"   🎯 セントロイド: {np.round(C_final[cluster_id], 3)}")

#         # ファイル名を表示
#         if file_names:
#             print(f"   📄 含まれるファイル:")
#             cluster_files = [file_names[idx] for idx in cluster_indices]

#             # ファイル名をソートして表示
#             cluster_files.sort()
#             for i, filename in enumerate(cluster_files, 1):
#                 print(f"      {i:2d}. {filename}")
#                 if i >= 10 and len(cluster_files) > 10:  # 最初の10ファイルのみ表示
#                     remaining = len(cluster_files) - 10
#                     print(f"      ... および {remaining} 個のファイル")
#                     break
#         else:
#             print(f"   📄 サンプルインデックス: {cluster_indices[:10].tolist()}" +
#                   (f" ... (+{len(cluster_indices)-10})" if len(cluster_indices) > 10 else ""))

#     print("-" * 80)

# def preprocess_data_for_visualization(X, file_names=None):
#     """
#     可視化のためのデータ前処理（外れ値対策）
#     注意: パス数などの極端な値も正当なコード特徴のため、通常は使用しない

#     Args:
#         X: 特徴量行列
#         file_names: ファイル名リスト

#     Returns:
#         X_processed: 前処理済み特徴量行列
#         outlier_info: 外れ値情報
#     """
#     # 機能をコメントアウト - 正当なコード特徴を維持するため
#     X_processed = X.copy()  # 変更せずそのまま返す
#     outlier_info = {
#         'outliers_found': False,
#         'n_outliers': 0,
#         'outlier_features': [],
#         'processing_method': 'なし'
#     }

#     # 以下、前処理機能はコメントアウト
#     """
#     # 特徴量名（パス数は4番目）
#     feature_names = [
#         'connected_components', 'loop_statements', 'conditional_statements',
#         'cycles', 'paths', 'cyclomatic_complexity',
#         'variable_count', 'total_reads', 'total_writes',
#         'max_reads', 'max_writes'
#     ]

#     # 外れ値検出と処理
#     for i, feature_name in enumerate(feature_names):
#         values = X[:, i]

#         # IQRによる外れ値検出
#         Q1 = np.percentile(values, 25)
#         Q3 = np.percentile(values, 75)
#         IQR = Q3 - Q1
#         lower_bound = Q1 - 1.5 * IQR
#         upper_bound = Q3 + 1.5 * IQR

#         # 外れ値のインデックスを特定
#         outlier_mask = (values < lower_bound) | (values > upper_bound)
#         n_outliers = np.sum(outlier_mask)

#         if n_outliers > 0:
#             outlier_info['outliers_found'] = True
#             outlier_info['n_outliers'] += n_outliers
#             outlier_info['outlier_features'].append(feature_name)

#             # 特に問題となるパス数などの大きな値を対処
#             if feature_name in ['paths', 'cycles'] and np.max(values) > 1000:
#                 # 対数変換 + 1（0値対策）
#                 X_processed[:, i] = np.log1p(values)
#                 outlier_info['processing_method'] = '対数変換'

#                 if file_names:
#                     max_idx = np.argmax(values)
#                     print(f"   📊 {feature_name}: 最大値 {values[max_idx]:.0f} ({file_names[max_idx]}) -> 対数変換適用")

#             elif np.max(values) > upper_bound * 2:
#                 # 極端に大きい値をクリッピング
#                 X_processed[:, i] = np.clip(values, lower_bound, upper_bound)
#                 outlier_info['processing_method'] = 'クリッピング'

#                 if file_names:
#                     extreme_mask = values > upper_bound * 2
#                     extreme_files = [file_names[idx] for idx in np.where(extreme_mask)[0]]
#                     print(f"   ✂️ {feature_name}: {len(extreme_files)}個の極端な値をクリッピング")
#                     for file in extreme_files[:3]:  # 最初の3つを表示
#                         print(f"      - {file}")
#                     if len(extreme_files) > 3:
#                         print(f"      ... および{len(extreme_files)-3}個")
#     """

#     return X_processed, outlier_info

# def main(algorithm_type: str, dataset_name: str):
#     # データセットの生成
#     result = create_dataset(dataset_name)

#     # 返り値の数に応じて適切に分割
#     if len(result) == 7:
#         X, y_true, k_clusters, n_features, true_centers, file_names, file_paths = result
#     elif len(result) == 6:
#         X, y_true, k_clusters, n_features, true_centers, file_names = result
#         file_paths = None
#     else:
#         X, y_true, k_clusters, n_features, true_centers = result
#         file_names = None
#         file_paths = None

#     # データの前処理（外れ値対策）- コメントアウト（正当なコード特徴を保持）
#     # X_processed, outlier_info = preprocess_data_for_visualization(X, file_names)

#     # 外れ値情報を表示 - コメントアウト
#     # if outlier_info['outliers_found']:
#     #     print(f"\n⚠️ 外れ値検出: {outlier_info['n_outliers']}個のサンプルで極端な値を検出")
#     #     print(f"   対象特徴量: {outlier_info['outlier_features']}")
#     #     print(f"   前処理方法: {outlier_info['processing_method']}")

#     # クラスタリングアルゴリズムの選択と実行
#     C_final, final_labels = None, None
#     if algorithm_type == 'general':
#         C_final, final_labels = general_kmeans_algorithm(
#             X_data=X,  # 元のデータを使用（前処理なし）
#             k=k_clusters,
#             metric='euclidean',
#             weights=FEATURE_WEIGHTS if dataset_name == 'real_code_features' else None
#         )
#         algo_title = "General K-means"
#     # elif algorithm_type == 'correctness_guided':
#     #     if true_centers is None and dataset_name != 'random':
#     #         raise ValueError(f"'{dataset_name}' dataset does not have 'true_centers' to run 'correctness_guided' algorithm. "
#     #                          "Please ensure true_centers are generated for this dataset or choose 'general' algorithm.")
#     #     C_final, final_labels = clustering_algorithm_with_correctness(
#     #         X_data=X,
#     #         k=k_clusters,
#     #         is_correct_fn=is_correct_fn_factory(true_centers),
#     #         metric='euclidean',
#     #         weights=FEATURE_WEIGHTS if dataset_name == 'blobs' or dataset_name == 'code_features' else None
#     #     )
#     #     algo_title = "Correctness-Guided K-means"
#     else:
#         raise ValueError(f"不明なアルゴリズムタイプです: {algorithm_type}")

#     # セントロイド距離の計算
#     centroid_distance = calculate_average_min_centroid_distance(C_final, true_centers)

#     # 結果の出力
#     print(f"--- {dataset_name.capitalize()} Dataset Results ({algo_title}, k={k_clusters}) ---")
#     print(f"最終的なセントロイド:\n", np.round(C_final, 2))
#     if true_centers is not None and not np.isnan(centroid_distance):
#         print(f"最終セントロイドと真のセントロイド間の平均最小距離: {centroid_distance:.4f}")
#     elif dataset_name == 'random':
#         print("ランダムデータには真のクラスターがないため、セントロイド距離は計算されません。")
#     else:
#         print("真のセントロイドが存在しないため、セントロイド距離は計算されません。")
#     print("-" * 50)

#     # クラスタリング結果の詳細表示
#     display_clustering_results(final_labels, C_final, file_names, dataset_name)

#     # 可視化（2次元データまたはPCAで次元削減）
#     visualize_clustering_results(X, y_true, final_labels, C_final, true_centers,
#                                dataset_name, algo_title, k_clusters, n_features, file_paths)

# def visualize_clustering_results(X, y_true, final_labels, C_final, true_centers,
#                                dataset_name, algo_title, k_clusters, n_features, file_paths=None):
#     """クラスタリング結果の可視化（パターン別色分け対応）"""

#     # 結果保存用ディレクトリを作成（シンプルな1階層）
#     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#     output_dir = f"clustering_results_{timestamp}"
#     os.makedirs(output_dir, exist_ok=True)

#     # 2次元以上のデータの場合はPCAで次元削減
#     if n_features > 2:
#         pca = PCA(n_components=2)
#         X_2d = pca.fit_transform(X)
#         C_final_2d = pca.transform(C_final)
#         if true_centers is not None:
#             true_centers_2d = pca.transform(true_centers)
#         else:
#             true_centers_2d = None

#         # PCA情報を表示
#         explained_var_ratio = pca.explained_variance_ratio_
#         total_explained_var = np.sum(explained_var_ratio)
#         print(f"\n📊 PCA次元削減情報:")
#         print(f"   PC1の説明分散比: {explained_var_ratio[0]:.3f} ({explained_var_ratio[0]*100:.1f}%)")
#         print(f"   PC2の説明分散比: {explained_var_ratio[1]:.3f} ({explained_var_ratio[1]*100:.1f}%)")
#         print(f"   合計説明分散比: {total_explained_var:.3f} ({total_explained_var*100:.1f}%)")

#         plot_title_suffix = f" (PCA 2D: {total_explained_var*100:.1f}% variance)"
#     else:
#         X_2d = X
#         C_final_2d = C_final
#         true_centers_2d = true_centers
#         plot_title_suffix = ""

#     # パターンごとの色分け情報を取得
#     pattern_groups = None
#     pattern_colors = None
#     pattern_labels = None

#     if file_paths is not None and dataset_name == 'real_code_features':
#         # 対象ディレクトリを取得
#         target_directory = "../atcoder/submissions_typical90_d_100"

#         # ファイルをパターン別にグループ分け
#         pattern_groups = analyze_file_groups(file_paths, target_directory)

#         # 色の設定
#         color_palette = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'olive', 'cyan']
#         pattern_colors = {}
#         color_idx = 0

#         for group_name in pattern_groups.keys():
#             if group_name == 'other':
#                 pattern_colors[group_name] = 'gray'
#             else:
#                 pattern_colors[group_name] = color_palette[color_idx % len(color_palette)]
#                 color_idx += 1

#         # 各ファイルのパターンラベルを決定
#         file_to_group = {}
#         for group_name, group_files in pattern_groups.items():
#             for file_info in group_files:
#                 file_to_group[file_info['file_path']] = group_name

#         pattern_labels = [file_to_group.get(fp, 'other') for fp in file_paths]

#     plt.figure(figsize=(12, 5))

#     # 密集度に応じてプロット設定を調整
#     n_points = len(X_2d)
#     if n_points > 100:
#         point_size = max(20, 100 - n_points // 10)  # 点数が多いほど小さく
#         alpha_val = max(0.4, 1.0 - n_points / 500)  # 点数が多いほど透明に
#     else:
#         point_size = 50
#         alpha_val = 0.7

#     # 左側: パターン別色分け（または真のクラスター）
#     plt.subplot(1, 2, 1)
#     if pattern_groups is not None:
#         # パターンごとに色分けしてプロット
#         for group_name in pattern_groups.keys():
#             group_indices = [i for i, label in enumerate(pattern_labels) if label == group_name]
#             if group_indices:
#                 group_points = X_2d[group_indices]
#                 plt.scatter(group_points[:, 0], group_points[:, 1],
#                            c=pattern_colors[group_name],
#                            label=f'{group_name} ({len(group_indices)})',
#                            alpha=alpha_val, s=point_size)

#         plt.title(f"Pattern-based Grouping\n{dataset_name.capitalize()} Dataset{plot_title_suffix}")
#         plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)

#         # パターン別の詳細情報をプロット上に表示
#         if pattern_groups:
#             info_text = "Pattern Colors:\n"
#             for group_name in sorted(pattern_groups.keys()):
#                 group_count = len([f for f in pattern_groups[group_name] if f['file_path'] in file_paths])
#                 info_text += f"• {group_name}: {group_count} files\n"

#             # テキストボックスを左下に配置
#             plt.text(0.02, 0.02, info_text, transform=plt.gca().transAxes,
#                     fontsize=8, verticalalignment='bottom',
#                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

#     elif y_true is not None and dataset_name != 'random':
#         scatter1 = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=y_true, cmap='viridis', alpha=alpha_val, s=point_size)
#         plt.title(f"True Clusters\n{dataset_name.capitalize()} Dataset{plot_title_suffix}")
#         plt.colorbar(scatter1, label='True Cluster')

#         # 真のセントロイドをプロット
#         if true_centers_2d is not None:
#             plt.scatter(true_centers_2d[:, 0], true_centers_2d[:, 1],
#                        c='blue', s=200, marker='o', edgecolor='black',
#                        label='True Centers', alpha=0.8)
#             plt.legend()
#     else:
#         plt.scatter(X_2d[:, 0], X_2d[:, 1], c='gray', alpha=alpha_val, s=point_size)
#         plt.title(f"Original Data\n{dataset_name.capitalize()} Dataset{plot_title_suffix}")

#     plt.xlabel("Component 1" if n_features > 2 else "Feature 1")
#     plt.ylabel("Component 2" if n_features > 2 else "Feature 2")
#     plt.grid(True, alpha=0.3)

#     # 右側: クラスタリング結果
#     plt.subplot(1, 2, 2)
#     scatter2 = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=final_labels, cmap='tab10', alpha=alpha_val, s=point_size)
#     plt.title(f"{algo_title} Results\n{dataset_name.capitalize()} Dataset{plot_title_suffix}")
#     plt.colorbar(scatter2, label='Predicted Cluster')

#     # 最終セントロイドをプロット
#     plt.scatter(C_final_2d[:, 0], C_final_2d[:, 1],
#                c='red', s=200, marker='X', edgecolor='black',
#                label='Final Centroids', alpha=0.9)

#     # クラスター別の詳細情報をプロット上に表示
#     unique_clusters = np.unique(final_labels)
#     cluster_info_text = "Cluster Info:\n"
#     for cluster_id in unique_clusters:
#         cluster_count = np.sum(final_labels == cluster_id)
#         cluster_info_text += f"• Cluster {cluster_id}: {cluster_count} files\n"

#     # テキストボックスを右下に配置
#     plt.text(0.98, 0.02, cluster_info_text, transform=plt.gca().transAxes,
#             fontsize=8, verticalalignment='bottom', horizontalalignment='right',
#             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

#     # 真のセントロイドも表示（比較用）
#     if true_centers_2d is not None:
#         plt.scatter(true_centers_2d[:, 0], true_centers_2d[:, 1],
#                    c='blue', s=150, marker='o', edgecolor='black',
#                    label='True Centers', alpha=0.7)

#     plt.xlabel("Component 1" if n_features > 2 else "Feature 1")
#     plt.ylabel("Component 2" if n_features > 2 else "Feature 2")
#     plt.legend()
#     plt.grid(True, alpha=0.3)

#     plt.tight_layout()

#     # 画像として保存（タイムスタンプ付き）
#     filename = os.path.join(output_dir, f"clustering_result_{dataset_name}_{algo_title.lower().replace(' ', '_').replace('-', '_')}_{timestamp}.png")
#     plt.savefig(filename, dpi=150, bbox_inches='tight')
#     print(f"📸 可視化結果を '{filename}' として保存しました。")

#     plt.show()
#     # データの実際の範囲を確認
#     x_data_min = np.min(X_2d[:, 0])
#     x_data_max = np.max(X_2d[:, 0])
#     y_data_min = np.min(X_2d[:, 1])
#     y_data_max = np.max(X_2d[:, 1])

#     print(f"\n📈 実際のデータ分布:")
#     print(f"  PC1範囲: [{x_data_min:.1f}, {x_data_max:.1f}]")
#     print(f"  PC2範囲: [{y_data_min:.1f}, {y_data_max:.1f}]")

#     # データの最大値に基づいて上限を設定（少し余裕を持たせる）
#     x_max_fixed = max(500, x_data_max * 1.1)  # 最低500、またはデータ最大値の1.1倍
#     y_max_fixed = max(50, y_data_max * 1.1)   # 最低50、またはデータ最大値の1.1倍
#     x_min = x_data_min  # 横軸下限はデータの最小値
#     y_min = y_data_min  # 縦軸下限はデータの最小値

#     x_max = x_max_fixed
#     y_max = y_max_fixed    # 密集範囲内のデータを抽出（両軸とも上限のみ、下限なし）
#     in_range_mask = (X_2d[:, 0] <= x_max) & (X_2d[:, 1] <= y_max)
#     out_range_count = np.sum(~in_range_mask)
#     in_range_count = np.sum(in_range_mask)

#     print(f"\n📊 データ適応型上限設定の範囲分析:")
#     print(f"  フォーカス範囲: PC1=[{x_min:.1f}, {x_max:.1f}] (上限: {x_max_fixed:.0f})")
#     print(f"  フォーカス範囲: PC2=[{y_min:.1f}, {y_max:.1f}] (上限: {y_max_fixed:.0f})")
#     print(f"  密集範囲内: {in_range_count} ファイル")
#     print(f"  密集範囲外: {out_range_count} ファイル")
#     print(f"📍 密集範囲の詳細表示を作成中...")

#     if in_range_count > 5:  # 密集範囲に十分なデータがある場合のみ
#         # 密集範囲用の点サイズと透明度を調整
#         dense_point_size = min(80, max(30, 300 // in_range_count))  # 密集度に応じて調整
#         dense_alpha = max(0.6, min(0.9, 50 / in_range_count))  # 透明度調整

#         plt.figure(figsize=(15, 6))  # より大きなフィギュアサイズ

#         # 左側: パターン別色分け（密集範囲のみ）
#         plt.subplot(1, 2, 1)
#         if pattern_groups is not None:
#             # 密集範囲内のデータのみプロット
#             for group_name in pattern_groups.keys():
#                 group_indices = [i for i, label in enumerate(pattern_labels)
#                                if label == group_name and in_range_mask[i]]
#                 if group_indices:
#                     group_points = X_2d[group_indices]
#                     plt.scatter(group_points[:, 0], group_points[:, 1],
#                                c=pattern_colors[group_name],
#                                label=f'{group_name} ({len(group_indices)})',
#                                alpha=dense_alpha, s=dense_point_size, edgecolors='black', linewidth=0.3)

#             plt.title(f"Pattern-based Grouping (Dense Region Focus)\n{in_range_count} files in range", fontsize=12)
#             plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)

#             # パターン別の詳細情報をプロット上に表示（密集範囲内のみ）
#             info_text = "Dense Region Patterns:\n"
#             for group_name in sorted(pattern_groups.keys()):
#                 group_in_range = len([i for i, label in enumerate(pattern_labels)
#                                     if label == group_name and in_range_mask[i]])
#                 if group_in_range > 0:
#                     info_text += f"• {group_name}: {group_in_range} files\n"

#             plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes,
#                     fontsize=9, verticalalignment='top',
#                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))

#         # 表示範囲を密集範囲に設定
#         plt.xlim(x_min, x_max)
#         plt.ylim(y_min, y_max)
#         plt.xlabel("Component 1" if n_features > 2 else "Feature 1", fontsize=11)
#         plt.ylabel("Component 2" if n_features > 2 else "Feature 2", fontsize=11)
#         plt.grid(True, alpha=0.4)

#         # 右側: クラスタリング結果（密集範囲のみ）
#         plt.subplot(1, 2, 2)
#         # 密集範囲内のデータのみプロット
#         in_range_X_2d = X_2d[in_range_mask]
#         in_range_labels = final_labels[in_range_mask]

#         scatter3 = plt.scatter(in_range_X_2d[:, 0], in_range_X_2d[:, 1],
#                               c=in_range_labels, cmap='tab10',
#                               alpha=dense_alpha, s=dense_point_size, edgecolors='black', linewidth=0.3)
#         plt.title(f"{algo_title} Results (Dense Region Focus)\n{in_range_count} files in range", fontsize=12)
#         plt.colorbar(scatter3, label='Predicted Cluster')

#         # 密集範囲内にあるセントロイドをプロット
#         in_range_centroids_mask = (C_final_2d[:, 0] >= x_min) & (C_final_2d[:, 0] <= x_max) & \
#                                   (C_final_2d[:, 1] >= y_min) & (C_final_2d[:, 1] <= y_max)
#         if np.any(in_range_centroids_mask):
#             plt.scatter(C_final_2d[in_range_centroids_mask, 0], C_final_2d[in_range_centroids_mask, 1],
#                        c='red', s=250, marker='X', edgecolor='black', linewidth=2,
#                        label='Centroids (in dense region)', alpha=1.0)

#         # クラスター別の詳細情報（密集範囲内のみ）
#         unique_clusters_in_range = np.unique(in_range_labels)
#         cluster_info_text = "Dense Region Clusters:\n"
#         for cluster_id in unique_clusters_in_range:
#             cluster_count = np.sum(in_range_labels == cluster_id)
#             cluster_info_text += f"• Cluster {cluster_id}: {cluster_count} files\n"

#         plt.text(0.02, 0.98, cluster_info_text, transform=plt.gca().transAxes,
#                 fontsize=9, verticalalignment='top',
#                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))

#         # 表示範囲を密集範囲に設定
#         plt.xlim(x_min, x_max)
#         plt.ylim(y_min, y_max)
#         plt.xlabel("Component 1" if n_features > 2 else "Feature 1", fontsize=11)
#         plt.ylabel("Component 2" if n_features > 2 else "Feature 2", fontsize=11)
#         plt.legend(fontsize=9)
#         plt.grid(True, alpha=0.4)

#         plt.tight_layout()

#         # 密集範囲の画像として保存
#         dense_filename = os.path.join(output_dir, f"clustering_result_dense_{dataset_name}_{algo_title.lower().replace(' ', '_').replace('-', '_')}_{timestamp}.png")
#         plt.savefig(dense_filename, dpi=200, bbox_inches='tight')
#         print(f"📸 密集範囲の可視化結果を '{dense_filename}' として保存しました。")
#         print(f"   密集範囲設定: 点サイズ={dense_point_size}, 透明度={dense_alpha:.2f}")

#         plt.show()
#     else:
#         print(f"⚠️ 密集範囲内のデータが少なすぎます({in_range_count}個)。密集範囲グラフをスキップします。")    # パターン分析結果の出力
#     if pattern_groups is not None:
#         print(f"\n🎨 パターン分析結果:")
#         for group_name, group_files in pattern_groups.items():
#             group_count = len([f for f in group_files if f['file_path'] in file_paths])
#             print(f"  {group_name}: {group_count} ファイル (色: {pattern_colors[group_name]})")

#     # データ分布の統計情報を表示
#     print(f"\n📈 データ分布統計:")
#     print(f"  データ範囲 PC1: [{np.min(X_2d[:, 0]):.2f}, {np.max(X_2d[:, 0]):.2f}]")
#     print(f"  データ範囲 PC2: [{np.min(X_2d[:, 1]):.2f}, {np.max(X_2d[:, 1]):.2f}]")
#     print(f"  標準偏差 PC1: {np.std(X_2d[:, 0]):.2f}")
#     print(f"  標準偏差 PC2: {np.std(X_2d[:, 1]):.2f}")

# if __name__ == '__main__':

#     # --- 実際のコード特徴量を使ったクラスタリング ---
#     if FEATURE_EXTRACTION_AVAILABLE:
#         print("\n=== Real Code Features Dataset: 実際のコードファイルからの特徴量クラスタリング ===")
#         try:
#             # 一般的なK-meansアルゴリズムのみ実行（高速化のため）
#             main(algorithm_type='general', dataset_name='real_code_features')
#             # main(algorithm_type='correctness_guided', dataset_name='real_code_features')  # コメントアウト
#         except Exception as e:
#             print(f"❌ 実際のコード特徴量クラスタリングでエラー: {e}")
#             print("エラーの詳細を確認してください。")
#     else:
#         print("⚠️ 特徴量抽出モジュールが利用できないため、実際のコードファイル解析をスキップします。")
