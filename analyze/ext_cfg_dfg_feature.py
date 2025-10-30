# CFG特徴量抽出モジュール
# ext-cfg-feature.pyからクラスタリングベクトルを簡潔に抽出
# ext_feature_data_flow.pyからデータフロー特徴量も抽出

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import matplotlib.colors as mcolors
import json
import pickle
from datetime import datetime

# ext-cfg-feature.pyから必要な関数をインポート
try:
    # control-flowディレクトリのパスを追加
    control_flow_path = os.path.join(os.path.dirname(__file__), 'control-flow')
    sys.path.append(control_flow_path)

    from ext_cfg_feature import analyze_accurate_cfg
except ImportError as e:
    print(f"❌ CFG特徴量モジュールのインポートエラー: {e}")
    print("ext-cfg-feature.pyが control-flow/ ディレクトリにあることを確認してください。")
    sys.exit(1)

# ext_feature_data_flow.pyから必要な関数をインポート
try:
    # data-flowディレクトリのパスを追加
    data_flow_path = os.path.join(os.path.dirname(__file__), 'data-flow')
    sys.path.append(data_flow_path)

    from ext_feature_data_flow import extract_dataflow_features_as_list, get_dataflow_feature_vector
except ImportError as e:
    print(f"❌ データフロー特徴量モジュールのインポートエラー: {e}")
    print("ext_feature_data_flow.pyが data-flow/ ディレクトリにあることを確認してください。")
    sys.exit(1)

def extract_dataflow_features_vector(source_file):
    """
    ソースコードからデータフロー特徴量ベクトルを抽出

    Args:
        source_file (str): 解析対象ファイルパス

    Returns:
        list: [total_reads, total_writes, max_reads, max_writes, var_count]
    """
    try:
        # ext_feature_data_flow.pyの関数を呼び出し
        dataflow_vector = get_dataflow_feature_vector(source_file)
        return dataflow_vector

    except Exception as e:
        print(f"❌ データフロー特徴量抽出エラー: {e}")
        return [0, 0, 0, 0, 0]

def get_dataflow_feature_names():
    """データフロー特徴量の名前リストを返す"""
    return [
        'total_reads',        # 総読み込み数
        'total_writes',       # 総書き込み数
        'max_reads',          # 読み込み数最大値
        'max_writes',         # 書き込み数最大値
        'var_count'           # 変数種類数
    ]

def extract_integrated_features_vector(source_file):
    """
    CFG特徴量とデータフロー特徴量を統合したベクトルを抽出

    Args:
        source_file (str): 解析対象ファイルパス

    Returns:
        list: 統合された特徴量ベクトル [CFG(6次元) + データフロー(5次元)]
    """
    try:
        # CFG特徴量を取得
        cfg_vector = extract_cfg_features_vector(source_file)

        # データフロー特徴量を取得
        dataflow_vector = extract_dataflow_features_vector(source_file)

        # 統合ベクトルを作成
        integrated_vector = cfg_vector + dataflow_vector

        return integrated_vector

    except Exception as e:
        print(f"❌ 統合特徴量抽出エラー: {e}")
        return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def extract_cfg_features_vector(source_file):
    """
    ソースコードからCFG特徴量ベクトルを抽出

    Args:
        source_file (str): 解析対象ファイルパス

    Returns:
        list: [connected_components, loop_statements, conditional_statements, cycles, paths, cyclomatic_complexity]
    """
    try:
        # print(f"🔄 CFG特徴量抽出中: {source_file}")

        # ext-cfg-feature.pyのanalyze_accurate_cfg関数を呼び出し
        all_features = analyze_accurate_cfg(source_file)

        if not all_features:
            print("⚠️  CFG特徴量が抽出できませんでした")
            return [0, 0, 0, 0, 0, 0]

        # 関数レベルの特徴量のみ使用（モジュールレベルは除外）
        function_features = {k: v for k, v in all_features.items()
                           if not (k.startswith('<module>') or k.startswith('&lt;module&gt;'))}

        # モジュールレベル特徴量（構造的特徴のみ）
        module_features = {k: v for k, v in all_features.items()
                         if k.startswith('<module>') or k.startswith('&lt;module&gt;')}

        # クラスタリングベクトルを計算
        # 1. connected_components: 論理積（1つでも0があれば0、全て1以上なら1）
        all_connected_components = [features.get('connected_components', 0) for features in all_features.values()]
        total_connected = 1 if all(cc > 0 for cc in all_connected_components) else 0

        # 2. ループと条件文: 関数単位で既に正確に計算済み（再帰含む）
        total_loops = sum(features.get('loop_statements', 0) for features in function_features.values())
        total_conditions = sum(features.get('conditional_statements', 0) for features in function_features.values())

        # モジュールレベルの分も追加
        total_loops += sum(features.get('loop_statements', 0) for features in module_features.values())
        total_conditions += sum(features.get('conditional_statements', 0) for features in module_features.values())

        # 3. 構造的特徴: 全体から計算（関数+モジュール）
        total_cycles = sum(features.get('cycles', 0) for features in all_features.values())
        total_paths = sum(features.get('paths', 0) for features in all_features.values())
        total_complexity = sum(features.get('cyclomatic_complexity', 0) for features in all_features.values())

        # クラスタリングベクトルを作成
        clustering_vector = [
            total_connected,     # 1. 連結成分数
            total_loops,         # 2. ループ文数（再帰含む）
            total_conditions,    # 3. 条件文数
            total_cycles,        # 4. サイクル数
            total_paths,         # 5. パス数（ループ考慮版）
            total_complexity     # 6. サイクロマティック複雑度
        ]

        # print(f"✅ CFG特徴量抽出完了: {clustering_vector}")
        return clustering_vector

    except Exception as e:
        print(f"❌ CFG特徴量抽出エラー: {e}")
        return [0, 0, 0, 0, 0, 0]

def get_cfg_feature_names():
    """CFG特徴量の名前リストを返す"""
    return [
        'connected_components',    # 連結成分数
        'loop_statements',         # ループ文数（再帰含む）
        'conditional_statements',  # 条件文数
        'cycles',                  # サイクル数
        'paths',                   # パス数（ループ考慮版）
        'cyclomatic_complexity'    # サイクロマティック複雑度
    ]

def batch_extract_integrated_features(file_list):
    """
    複数ファイルの統合特徴量を一括抽出

    Args:
        file_list (list): 解析対象ファイルリスト

    Returns:
        list: 各ファイルの統合特徴量ベクトルリスト
    """
    results = []

    print(f"📂 統合特徴量一括抽出開始 ({len(file_list)}ファイル)")

    for i, source_file in enumerate(file_list, 1):
        try:
            result = extract_integrated_features_vector(source_file)
            results.append({
                'source_file': source_file,
                'integrated_vector': result
            })

        except Exception as e:
            print(f"❌ エラー: {e}")
            # エラー時はゼロベクトルを追加
            results.append({
                'source_file': source_file,
                'integrated_vector': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'error': str(e)
            })

    return results

def batch_extract_cfg_features(file_list):
    """
    複数ファイルのCFG特徴量を一括抽出

    Args:
        file_list (list): 解析対象ファイルリスト

    Returns:
        list: 各ファイルのCFG特徴量結果リスト
    """
    results = []

    print(f"📂 CFG特徴量一括抽出開始 ({len(file_list)}ファイル)")

    for i, source_file in enumerate(file_list, 1):
        try:
            result = extract_cfg_features_vector(source_file)
            results.append(result)

        except Exception as e:
            print(f"❌ エラー: {e}")
            # エラー時はゼロベクトルを追加
            error_result = {
                'source_file': source_file,
                'clustering_vector': [0, 0, 0, 0, 0, 0],
                'feature_names': get_cfg_feature_names(),
                'individual_features': {},
                'summary': {'total_functions': 0, 'total_modules': 0},
                'error': str(e)
            }
            results.append(error_result)

    return results

def find_files_in_directory(directory, file_extensions=['.py', '.c', '.cpp', '.java']):
    """
    指定されたディレクトリとサブディレクトリを再帰的に探索してファイルを発見

    Args:
        directory (str): 検索対象ディレクトリ
        file_extensions (list): 対象ファイル拡張子リスト

    Returns:
        list: 発見されたファイルパスのリスト
    """
    found_files = []

    def explore_directory(current_dir):
        try:
            # lsコマンド相当: ディレクトリの内容を取得
            contents = os.listdir(current_dir)

            # .から始まるファイル・ディレクトリを除外
            filtered_contents = [item for item in contents if not item.startswith('.')]

            for item in filtered_contents:
                item_path = os.path.join(current_dir, item)

                if os.path.isfile(item_path):
                    # ファイルの場合: 拡張子チェック
                    _, ext = os.path.splitext(item)
                    if ext.lower() in file_extensions:
                        found_files.append(item_path)

                elif os.path.isdir(item_path):
                    # ディレクトリの場合: 再帰的に探索
                    explore_directory(item_path)

        except (FileNotFoundError, PermissionError) as e:
            print(f"❌ エラー: {current_dir} - {e}")

    explore_directory(directory)

    return found_files

def analyze_file_groups(file_list, base_directory):
    """
    ファイルをpatternディレクトリ別にグループ分けして分析

    Args:
        file_list (list): ファイルパスのリスト
        base_directory (str): ベースディレクトリパス

    Returns:
        dict: グループ分析結果
    """
    groups = {}

    for file_path in file_list:
        relative_path = os.path.relpath(file_path, base_directory)
        path_parts = relative_path.split(os.sep)

        # patternディレクトリかどうかを判定
        if len(path_parts) > 1 and path_parts[0].startswith('pattern'):
            group_name = path_parts[0]  # pattern_1, pattern_2, etc.
        else:
            group_name = 'other'  # その他のファイル

        if group_name not in groups:
            groups[group_name] = []

        groups[group_name].append({
            'file_path': file_path,
            'relative_path': relative_path,
            'filename': os.path.basename(file_path)
        })

    return groups

def save_feature_vectors(batch_results, groups=None, base_directory=None, output_file=None, format='json'):
    """
    特徴量ベクトルをファイルに保存（パターン別セントロイド情報も含む）

    Args:
        batch_results (list): 特徴量抽出結果
        groups (dict): グループ分析結果（セントロイド計算用）
        base_directory (str): ベースディレクトリパス（セントロイド計算用）
        output_file (str): 出力ファイル名（Noneの場合は自動生成）
        format (str): 保存形式 ('json' または 'pickle')
    """
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if format == 'json':
            output_file = f"feature_vectors_{timestamp}.json"
        else:
            output_file = f"feature_vectors_{timestamp}.pkl"

    try:
        # メタデータを追加
        save_data = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(batch_results),
            'successful_extractions': len([r for r in batch_results if 'error' not in r]),
            'feature_names': {
                'cfg_features': get_cfg_feature_names(),
                'dataflow_features': get_dataflow_feature_names()
            },
            'data': batch_results
        }

        # パターン別セントロイドも計算・保存
        if groups is not None and base_directory is not None:
            print("🎯 セントロイド情報を計算して追加中...")
            centroids_data = calculate_pattern_centroids(batch_results, groups, base_directory)

            if centroids_data and centroids_data['centroids']:
                save_data['pattern_centroids'] = centroids_data
                print(f"✅ {len(centroids_data['centroids'])}個のパターンセントロイドを追加しました")

                # セントロイド概要を表示
                for pattern_name, centroid_info in centroids_data['centroids'].items():
                    centroid = centroid_info['centroid_vector']
                    count = centroid_info['sample_count']
                    print(f"   {pattern_name}: {count}ファイル → 重心[{', '.join([f'{x:.3f}' for x in centroid[:3]])}...]")
            else:
                save_data['pattern_centroids'] = None
                print("⚠️ セントロイドが計算できませんでした")
        else:
            save_data['pattern_centroids'] = None

        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        elif format == 'pickle':
            with open(output_file, 'wb') as f:
                pickle.dump(save_data, f)
        else:
            raise ValueError("format は 'json' または 'pickle' を指定してください")

        print(f"💾 特徴量ベクトル{'とセントロイド' if save_data['pattern_centroids'] else ''}を '{output_file}' に保存しました")
        print(f"   形式: {format.upper()}")
        print(f"   総ファイル数: {save_data['total_files']}")
        print(f"   成功数: {save_data['successful_extractions']}")
        if save_data['pattern_centroids']:
            print(f"   セントロイド数: {len(save_data['pattern_centroids']['centroids'])}個のパターン")

        return output_file

    except Exception as e:
        print(f"❌ 保存エラー: {e}")
        return None

def load_feature_vectors(input_file):
    """
    保存された特徴量ベクトルをファイルから読み込み

    Args:
        input_file (str): 入力ファイル名

    Returns:
        dict: 読み込まれた特徴量データ
    """
    try:
        if input_file.endswith('.json'):
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif input_file.endswith('.pkl'):
            with open(input_file, 'rb') as f:
                data = pickle.load(f)
        else:
            raise ValueError("ファイル形式が不正です（.json または .pkl のみサポート）")

        print(f"📂 特徴量ベクトルを '{input_file}' から読み込みました")
        print(f"   保存日時: {data['timestamp']}")
        print(f"   総ファイル数: {data['total_files']}")
        print(f"   成功数: {data['successful_extractions']}")

        return data

    except Exception as e:
        print(f"❌ 読み込みエラー: {e}")
        return None

def calculate_pattern_centroids(batch_results, groups, base_directory):
    """
    各パターンディレクトリの重心（真のセントロイド）を計算

    Args:
        batch_results (list): 特徴量抽出結果
        groups (dict): グループ分析結果
        base_directory (str): ベースディレクトリパス

    Returns:
        dict: パターン別セントロイド情報
    """
    print("🎯 パターン別重心（真のセントロイド）計算中...")

    # 成功した結果のみを使用
    successful_results = [r for r in batch_results if 'error' not in r]

    if len(successful_results) == 0:
        print("❌ セントロイド計算対象のデータがありません")
        return {}

    # 特徴量ベクトルを取得
    feature_vectors = np.array([r['integrated_vector'] for r in successful_results])
    file_paths = [r['source_file'] for r in successful_results]

    # ファイルパスをグループにマッピング
    file_to_group = {}
    for group_name, group_files in groups.items():
        for file_info in group_files:
            file_to_group[file_info['file_path']] = group_name

    # パターングループのみを対象にする
    pattern_groups = {k: v for k, v in groups.items() if k.startswith('pattern')}

    # "other"グループ（rootファイル）も含める
    if 'other' in groups and len(groups['other']) > 0:
        pattern_groups['other'] = groups['other']
        print(f"📁 'other'グループ（rootファイル）も真のセントロイドに含めます: {len(groups['other'])}ファイル")

    centroids_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'base_directory': base_directory,
            'total_patterns': len(pattern_groups),
            'includes_other_group': 'other' in pattern_groups,
            'feature_dimension': len(feature_vectors[0]) if len(feature_vectors) > 0 else 0,
            'feature_names': {
                'cfg_features': get_cfg_feature_names(),
                'dataflow_features': get_dataflow_feature_names()
            }
        },
        'centroids': {}
    }

    print(f"📊 {len(pattern_groups)}個のパターンからセントロイドを計算中...")

    for pattern_name, pattern_files in pattern_groups.items():
        # パターンに属するファイルのインデックスを取得
        pattern_indices = []
        pattern_file_paths = []

        for i, file_path in enumerate(file_paths):
            if file_to_group.get(file_path) == pattern_name:
                pattern_indices.append(i)
                pattern_file_paths.append(file_path)

        if not pattern_indices:
            print(f"⚠️ {pattern_name}: データが見つかりません")
            continue

        # パターンの特徴量ベクトルを抽出
        pattern_vectors = feature_vectors[pattern_indices]

        # セントロイド（重心）を計算
        centroid = np.mean(pattern_vectors, axis=0).tolist()

        # セントロイド情報を保存（統計情報は削除）
        centroids_data['centroids'][pattern_name] = {
            'centroid_vector': centroid,
            'sample_count': len(pattern_indices),
            'file_paths': pattern_file_paths
        }

        print(f"✅ {pattern_name}: セントロイド計算完了 ({len(pattern_indices)} ファイル)")
        print(f"   重心ベクトル: {[f'{x:.3f}' for x in centroid[:6]][:3]}...")  # 最初の3要素のみ表示

    return centroids_data

def save_pattern_centroids(centroids_data, output_file=None):
    """
    パターン別セントロイドをJSONファイルに保存

    Args:
        centroids_data (dict): セントロイドデータ
        output_file (str): 出力ファイル名（Noneの場合は自動生成）

    Returns:
        str: 保存されたファイル名
    """
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_dir = centroids_data['metadata'].get('base_directory', 'unknown')
        base_name = os.path.basename(base_dir) if base_dir != 'unknown' else 'patterns'
        output_file = f"pattern_centroids_{base_name}_{timestamp}.json"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(centroids_data, f, indent=2, ensure_ascii=False)

        print(f"💾 パターン別セントロイドを '{output_file}' に保存しました")
        print(f"   パターン数: {centroids_data['metadata']['total_patterns']}")
        print(f"   特徴量次元: {centroids_data['metadata']['feature_dimension']}")

        # セントロイド一覧を表示
        print(f"📋 保存されたセントロイド:")
        for pattern_name, centroid_info in centroids_data['centroids'].items():
            sample_count = centroid_info['sample_count']
            centroid_vector = centroid_info['centroid_vector']
            print(f"   {pattern_name}: {sample_count}ファイル → [{', '.join([f'{x:.3f}' for x in centroid_vector[:3]])}...]")

        return output_file

    except Exception as e:
        print(f"❌ セントロイド保存エラー: {e}")
        return None

def load_pattern_centroids(input_file):
    """
    保存されたパターン別セントロイドをファイルから読み込み

    Args:
        input_file (str): 入力ファイル名

    Returns:
        dict: 読み込まれたセントロイドデータ
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📂 パターン別セントロイドを '{input_file}' から読み込みました")
        print(f"   保存日時: {data['metadata']['timestamp']}")
        print(f"   パターン数: {data['metadata']['total_patterns']}")
        print(f"   特徴量次元: {data['metadata']['feature_dimension']}")

        return data

    except Exception as e:
        print(f"❌ セントロイド読み込みエラー: {e}")
        return None

def check_cache_validity(target_directory, cache_file):
    """
    キャッシュファイルの有効性をチェック

    Args:
        target_directory (str): 対象ディレクトリ
        cache_file (str): キャッシュファイル

    Returns:
        bool: キャッシュが有効かどうか
    """
    if not os.path.exists(cache_file):
        return False

    try:
        # キャッシュファイルの更新時刻を取得
        cache_mtime = os.path.getmtime(cache_file)

        # 対象ディレクトリ内のファイルの最新更新時刻をチェック
        latest_file_mtime = 0
        for root, dirs, files in os.walk(target_directory):
            for file in files:
                if file.endswith(('.py', '.c', '.cpp', '.java')):
                    file_path = os.path.join(root, file)
                    file_mtime = os.path.getmtime(file_path)
                    latest_file_mtime = max(latest_file_mtime, file_mtime)

        # キャッシュが対象ファイルより新しければ有効
        return cache_mtime > latest_file_mtime

    except Exception as e:
        print(f"⚠️ キャッシュ有効性チェックエラー: {e}")
        return False

def visualize_feature_distribution(batch_results, groups, base_directory):
    """
    特徴量の分布をグループ別に可視化（全体＋パターン別個別プロット）

    Args:
        batch_results (list): 特徴量抽出結果
        groups (dict): グループ分析結果
        base_directory (str): ベースディレクトリパス
    """
    # 成功した結果のみを使用
    successful_results = [r for r in batch_results if 'error' not in r]

    if len(successful_results) == 0:
        print("❌ 可視化対象のデータがありません")
        return

    # 特徴量ベクトルを取得
    feature_vectors = np.array([r['integrated_vector'] for r in successful_results])
    file_paths = [r['source_file'] for r in successful_results]

    # ファイルパスをグループにマッピング
    file_to_group = {}
    group_colors = {}
    color_palette = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'olive', 'cyan']

    # otherグループは灰色に設定
    color_idx = 0
    for group_name, group_files in groups.items():
        if group_name == 'other':
            group_colors[group_name] = 'gray'
        else:
            group_colors[group_name] = color_palette[color_idx % len(color_palette)]
            color_idx += 1

        for file_info in group_files:
            file_to_group[file_info['file_path']] = group_name

    # 各ファイルの色とラベルを決定
    colors = []
    labels = []
    for file_path in file_paths:
        group = file_to_group.get(file_path, 'other')
        colors.append(group_colors[group])
        labels.append(group)

    # PCAで2次元に次元削減
    print("📊 PCAで次元削減中...")
    pca = PCA(n_components=2)
    feature_vectors_2d = pca.fit_transform(feature_vectors)

    # タイムスタンプを生成（全プロットで共通）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 結果保存用ディレクトリを作成
    output_dir = f"feature_visualization_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 可視化結果保存ディレクトリ: {output_dir}")

    # 1. 全体プロット（すべてのグループを含む）
    print("🎨 全体プロット作成中...")
    plt.figure(figsize=(12, 8))

    # グループごとにプロット
    for group_name in groups.keys():
        group_indices = [i for i, label in enumerate(labels) if label == group_name]
        if group_indices:
            group_points = feature_vectors_2d[group_indices]
            plt.scatter(group_points[:, 0], group_points[:, 1],
                       c=group_colors[group_name],
                       label=f'{group_name} ({len(group_indices)} files)',
                       alpha=0.7, s=60)

    plt.title(f'Feature Distribution Visualization (All Patterns)\n{base_directory}', fontsize=14)
    plt.xlabel(f'PC1 (Explained Variance: {pca.explained_variance_ratio_[0]:.2%})', fontsize=12)
    plt.ylabel(f'PC2 (Explained Variance: {pca.explained_variance_ratio_[1]:.2%})', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)

    # 統計情報を表示
    total_variance = sum(pca.explained_variance_ratio_)
    plt.figtext(0.02, 0.02, f'Total Explained Variance: {total_variance:.2%}', fontsize=10)

    plt.tight_layout()

    # 全体プロットを保存
    all_filename = os.path.join(output_dir, f"feature_distribution_all_{timestamp}.png")
    plt.savefig(all_filename, dpi=150, bbox_inches='tight')
    print(f"📸 全体プロットを '{all_filename}' として保存しました。")

    plt.show()

    # 2. パターン別個別プロット
    pattern_groups = {k: v for k, v in groups.items() if k.startswith('pattern')}

    if pattern_groups:
        print(f"\n🎨 パターン別個別プロット作成中... ({len(pattern_groups)}個のパターン)")

        for pattern_name, pattern_files in pattern_groups.items():
            # パターンに属するファイルのインデックスを取得
            pattern_indices = [i for i, label in enumerate(labels) if label == pattern_name]

            if not pattern_indices:
                print(f"⚠️ {pattern_name}: データが見つかりません")
                continue

            # パターン用のデータを抽出
            pattern_vectors_2d = feature_vectors_2d[pattern_indices]
            pattern_vectors_original = feature_vectors[pattern_indices]

            # パターン別PCAを実行（そのパターンのデータのみで）
            if len(pattern_indices) > 1:  # 2つ以上のサンプルが必要
                pattern_pca = PCA(n_components=min(2, len(pattern_indices)-1))
                try:
                    pattern_vectors_pca = pattern_pca.fit_transform(pattern_vectors_original)
                    use_pattern_pca = True
                    pattern_explained_var = pattern_pca.explained_variance_ratio_
                except:
                    # PCAが失敗した場合は全体PCAの結果を使用
                    pattern_vectors_pca = pattern_vectors_2d
                    use_pattern_pca = False
                    pattern_explained_var = [0, 0]
            else:
                pattern_vectors_pca = pattern_vectors_2d
                use_pattern_pca = False
                pattern_explained_var = [0, 0]

            # プロット作成
            plt.figure(figsize=(10, 8))

            # パターン内でのファイル名による色分け（グラデーション）
            pattern_color_base = group_colors[pattern_name]
            n_files = len(pattern_indices)

            if n_files > 1:
                # 複数ファイルがある場合はグラデーション
                cmap = plt.cm.get_cmap('viridis')
                colors_pattern = [cmap(i / (n_files - 1)) for i in range(n_files)]
            else:
                colors_pattern = [pattern_color_base]

            scatter = plt.scatter(pattern_vectors_pca[:, 0], pattern_vectors_pca[:, 1],
                                c=colors_pattern, s=100, alpha=0.8, edgecolors='black', linewidth=0.5)

            # ファイル名をアノテーション
            pattern_file_paths = [file_paths[i] for i in pattern_indices]
            for i, (x, y) in enumerate(pattern_vectors_pca):
                filename = os.path.basename(pattern_file_paths[i])
                plt.annotate(filename, (x, y), xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.8)

            # タイトルと軸ラベル
            pca_info = ""
            if use_pattern_pca and len(pattern_explained_var) >= 2:
                pca_info = f"\nPattern-specific PCA: PC1={pattern_explained_var[0]:.2%}, PC2={pattern_explained_var[1]:.2%}"
            else:
                pca_info = f"\nUsing global PCA projection"

            plt.title(f'{pattern_name.upper()} Feature Distribution\n{len(pattern_files)} files{pca_info}',
                     fontsize=14)

            if use_pattern_pca:
                plt.xlabel(f'{pattern_name} PC1', fontsize=12)
                plt.ylabel(f'{pattern_name} PC2', fontsize=12)
            else:
                plt.xlabel(f'Global PC1', fontsize=12)
                plt.ylabel(f'Global PC2', fontsize=12)

            plt.grid(True, alpha=0.3)

            # 統計情報テキストボックス
            stats_text = f"Files: {n_files}\n"
            if len(pattern_vectors_original) > 0:
                avg_vector = np.mean(pattern_vectors_original, axis=0)
                std_vector = np.std(pattern_vectors_original, axis=0)
                stats_text += f"Avg complexity: {avg_vector[5]:.1f}\n"  # cyclomatic_complexity
                stats_text += f"Avg paths: {avg_vector[4]:.1f}"  # paths

            plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

            plt.tight_layout()

            # パターン別プロットを保存
            pattern_filename = os.path.join(output_dir, f"feature_distribution_{pattern_name}_{timestamp}.png")
            plt.savefig(pattern_filename, dpi=150, bbox_inches='tight')
            print(f"📸 {pattern_name}プロットを '{pattern_filename}' として保存しました。")

            plt.show()

    # 3. 比較サマリープロット（パターン別セントロイド）
    if len(pattern_groups) > 1:
        print(f"\n🎨 パターン比較サマリープロット作成中...")
        plt.figure(figsize=(12, 8))

        # 各パターンのセントロイド（平均）を計算
        pattern_centroids = []
        pattern_names_list = []
        pattern_colors_list = []

        for pattern_name, pattern_files in pattern_groups.items():
            pattern_indices = [i for i, label in enumerate(labels) if label == pattern_name]
            if pattern_indices:
                pattern_vectors = feature_vectors[pattern_indices]
                centroid = np.mean(pattern_vectors, axis=0)
                pattern_centroids.append(centroid)
                pattern_names_list.append(pattern_name)
                pattern_colors_list.append(group_colors[pattern_name])

        if pattern_centroids:
            # セントロイドをPCAで可視化
            centroids_array = np.array(pattern_centroids)
            centroids_2d = pca.transform(centroids_array)

            # セントロイドをプロット
            scatter = plt.scatter(centroids_2d[:, 0], centroids_2d[:, 1],
                                c=pattern_colors_list, s=200, alpha=0.8,
                                edgecolors='black', linewidth=2, marker='D')

            # パターン名をアノテーション
            for i, (x, y) in enumerate(centroids_2d):
                plt.annotate(pattern_names_list[i], (x, y), xytext=(10, 10),
                           textcoords='offset points', fontsize=12, fontweight='bold')

            plt.title(f'Pattern Centroids Comparison\n{base_directory}', fontsize=14)
            plt.xlabel(f'PC1 (Explained Variance: {pca.explained_variance_ratio_[0]:.2%})', fontsize=12)
            plt.ylabel(f'PC2 (Explained Variance: {pca.explained_variance_ratio_[1]:.2%})', fontsize=12)
            plt.grid(True, alpha=0.3)

            plt.tight_layout()

            # 比較プロットを保存
            comparison_filename = os.path.join(output_dir, f"feature_comparison_centroids_{timestamp}.png")
            plt.savefig(comparison_filename, dpi=150, bbox_inches='tight')
            print(f"📸 パターン比較プロットを '{comparison_filename}' として保存しました。")

            plt.show()

    # 詳細統計情報を出力
    print(f"\n📈 特徴量分布統計:")
    print(f"  総サンプル数: {len(successful_results)}")
    print(f"  特徴量次元数: {feature_vectors.shape[1]}")
    print(f"  PCA説明分散: PC1={pca.explained_variance_ratio_[0]:.2%}, PC2={pca.explained_variance_ratio_[1]:.2%}")

    for group_name, group_files in groups.items():
        group_count = len([f for f in group_files if f['file_path'] in file_paths])
        print(f"  {group_name}: {group_count} ファイル (色: {group_colors[group_name]})")

def main():
    """メイン関数 - 複数ファイル一括処理のテスト実行（キャッシュ機能付き）"""
    print("🎯 統合特徴量抽出システム（CFG + データフロー）")

    # 対象ディレクトリを指定
    # target_directory = r"C:\Users\yxicu\python\pyjoern\atcoder\submissions_typical90_d_100"
    target_directory = "../atcoder/submissions_typical90_d_100"

    # キャッシュファイル名を生成
    cache_file = f"feature_cache_{os.path.basename(target_directory)}.json"

    # ディレクトリが存在するかチェック
    if not os.path.exists(target_directory):
        print(f"❌ 指定されたディレクトリが存在しません: {target_directory}")
        print("処理を終了します。")
        return

    # lsコマンド風でファイルを自動発見
    target_files = find_files_in_directory(target_directory)

    if not target_files:
        print("⚠️  処理対象ファイルが見つかりませんでした")
        return

    print(f"\n📁 発見されたファイル: {len(target_files)}個")

    # ファイルをグループ分析（キャッシュ処理前に実行）
    print(f"\n🔍 ファイルグループ分析中...")
    groups = analyze_file_groups(target_files, target_directory)

    print(f"📂 発見されたグループ:")
    for group_name, group_files in groups.items():
        print(f"  {group_name}: {len(group_files)} ファイル")
        for file_info in group_files[:3]:  # 最初の3ファイルを表示
            print(f"    - {file_info['relative_path']}")
        if len(group_files) > 3:
            print(f"    ... および {len(group_files) - 3} 個のファイル")

    # キャッシュの有効性をチェック
    use_cache = False
    if os.path.exists(cache_file):
        if check_cache_validity(target_directory, cache_file):
            print(f"📦 有効なキャッシュファイルを発見: {cache_file}")
            use_cache_input = input("キャッシュを使用しますか？ (y/n): ").lower().strip()
            use_cache = use_cache_input in ['y', 'yes', '']
        else:
            print(f"⚠️ キャッシュファイルは古いため、再抽出が必要です")

    batch_results = None
    cached_data = None

    if use_cache:
        # キャッシュから読み込み
        print(f"📂 キャッシュから特徴量を読み込み中...")
        cached_data = load_feature_vectors(cache_file)
        if cached_data:
            batch_results = cached_data['data']
            print(f"✅ キャッシュから {len(batch_results)} ファイルの特徴量を読み込みました")

    if batch_results is None:
        # 新規抽出
        for i, file in enumerate(target_files, 1):
            relative_path = os.path.relpath(file, target_directory)
            print(f"  {i:2d}. {relative_path}")

        # 複数ファイルの一括処理を実行
        print(f"\n🔄 複数ファイル一括処理開始")
        batch_results = batch_extract_integrated_features(target_files)

        # 結果をキャッシュに保存
        print(f"\n💾 特徴量をキャッシュに保存中...")
        save_feature_vectors(batch_results, groups, target_directory, cache_file, format='json')

        # 新規作成されたキャッシュファイルを読み込んで cached_data を設定
        cached_data = load_feature_vectors(cache_file)

    # 結果を表示
    print(f"\n📊 一括処理結果:")
    for i, result in enumerate(batch_results, 1):
        filename = os.path.basename(result['source_file'])
        relative_path = os.path.relpath(result['source_file'], target_directory)

        if 'error' in result:
            print(f"  {i:2d}. ❌ {relative_path}: エラー")
        else:
            print(f"  {i:2d}. ✅ {relative_path}: {result['integrated_vector']}")

    # 特徴量分布の可視化
    print(f"\n🎨 特徴量分布可視化開始...")
    try:
        visualize_feature_distribution(batch_results, groups, target_directory)
    except ImportError as e:
        print(f"❌ 可視化に必要なライブラリが不足しています: {e}")
        print("以下のコマンドでインストールしてください:")
        print("pip install matplotlib scikit-learn numpy")
    except Exception as e:
        print(f"❌ 可視化エラー: {e}")

    # パターン別セントロイド（真のセントロイド）を計算・保存
    print(f"\n🎯 パターン別セントロイド計算・保存開始...")
    try:
        # セントロイド情報がキャッシュファイルに含まれているかチェック
        if batch_results and cached_data and cached_data.get('pattern_centroids'):
            print("✅ セントロイド情報はキャッシュファイルに含まれています")
            centroids_data = cached_data['pattern_centroids']

            # セントロイド概要を表示
            print(f"\n📈 セントロイド概要（キャッシュから読み込み）:")
            for pattern_name, centroid_info in centroids_data['centroids'].items():
                centroid = centroid_info['centroid_vector']
                count = centroid_info['sample_count']
                print(f"   {pattern_name} ({count}ファイル):")
                print(f"     CFG特徴量: [{', '.join([f'{x:.2f}' for x in centroid[:6]])}]")
                print(f"     データフロー特徴量: [{', '.join([f'{x:.2f}' for x in centroid[6:]])}]")
        else:
            # セントロイドを新規計算してキャッシュファイルに追加
            print("🔄 セントロイド情報をキャッシュファイルに追加中...")
            centroids_data = calculate_pattern_centroids(batch_results, groups, target_directory)

            if centroids_data and centroids_data['centroids']:
                # 既存のキャッシュデータを読み込み
                try:
                    if os.path.exists(cache_file):
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                    else:
                        # キャッシュファイルが存在しない場合は新規作成用データ
                        cache_data = {
                            'timestamp': datetime.now().isoformat(),
                            'total_files': len(batch_results),
                            'successful_extractions': len([r for r in batch_results if 'error' not in r]),
                            'feature_names': {
                                'cfg_features': get_cfg_feature_names(),
                                'dataflow_features': get_dataflow_feature_names()
                            },
                            'data': batch_results
                        }

                    # セントロイド情報を追加
                    cache_data['pattern_centroids'] = centroids_data

                    # キャッシュファイルを更新
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, indent=2, ensure_ascii=False)

                    print(f"✅ セントロイド情報をキャッシュファイル '{cache_file}' に追加しました")
                    print(f"   パターン数: {len(centroids_data['centroids'])}個")

                    # セントロイド概要を表示
                    print(f"\n📈 セントロイド概要:")
                    for pattern_name, centroid_info in centroids_data['centroids'].items():
                        centroid = centroid_info['centroid_vector']
                        count = centroid_info['sample_count']
                        print(f"   {pattern_name} ({count}ファイル):")
                        print(f"     CFG特徴量: [{', '.join([f'{x:.2f}' for x in centroid[:6]])}]")
                        print(f"     データフロー特徴量: [{', '.join([f'{x:.2f}' for x in centroid[6:]])}]")

                except Exception as file_error:
                    print(f"❌ キャッシュファイル更新エラー: {file_error}")
                    print("⚠️ セントロイド情報を別ファイルに保存します")
                    centroid_file = save_pattern_centroids(centroids_data)
                    if centroid_file:
                        print(f"✅ セントロイドファイル生成成功: {centroid_file}")
            else:
                print("⚠️ 計算可能なパターンセントロイドがありませんでした")

    except Exception as e:
        print(f"❌ セントロイド計算エラー: {e}")

    # 手動保存オプション
    save_option = input("\n💾 結果を別ファイルにも保存しますか？ (y/n): ").lower().strip()
    if save_option in ['y', 'yes']:
        format_option = input("保存形式を選択してください (json/pickle): ").lower().strip()
        if format_option in ['json', 'pickle']:
            save_feature_vectors(batch_results, groups, target_directory, format=format_option)
        else:
            print("デフォルトでJSONで保存します")
            save_feature_vectors(batch_results, groups, target_directory, format='json')

if __name__ == "__main__":
    main()

# 使用例（キャッシュ機能付き + セントロイド計算）:
#
# from ext_cfg_dfg_feature import (
#     extract_cfg_features_vector,
#     extract_dataflow_features_vector,
#     extract_integrated_features_vector,
#     batch_extract_integrated_features,
#     save_feature_vectors,
#     load_feature_vectors,
#     calculate_pattern_centroids,
#     save_pattern_centroids,
#     load_pattern_centroids
# )
#
# # 単一ファイルの場合
# cfg_vector = extract_cfg_features_vector("submission_1.py")
# print(cfg_vector)  # [connected_components, loop_statements, conditional_statements, cycles, paths, cyclomatic_complexity]
#
# dataflow_vector = extract_dataflow_features_vector("submission_1.py")
# print(dataflow_vector)  # [total_reads, total_writes, max_reads, max_writes, var_count]
#
# integrated_vector = extract_integrated_features_vector("submission_1.py")
# print(integrated_vector)  # 11次元の統合ベクトル [CFG(6次元) + データフロー(5次元)]
#
# # 複数submissionファイルの一括処理
# submission_files = [f"submission_{i}.py" for i in range(1, 6)]  # submission_1.py to submission_5.py
# batch_results = batch_extract_integrated_features(submission_files)
#
# # 結果をファイルに保存（セントロイド付き）
# save_feature_vectors(batch_results, groups, base_directory, "my_features.json", format='json')
# # または
# save_feature_vectors(batch_results, groups, base_directory, "my_features.pkl", format='pickle')
#
# # 保存した結果を読み込み
# cached_data = load_feature_vectors("my_features.json")
# if cached_data:
#     cached_results = cached_data['data']
#
#     # 特徴量データ
#     for result in cached_results:
#         if 'error' not in result:
#             print(f"{result['source_file']}: {result['integrated_vector']}")
#         else:
#             print(f"{result['source_file']}: エラー - {result['error']}")
#
#     # セントロイドデータ（k-means教師データ）
#     if cached_data.get('pattern_centroids'):
#         centroids_info = cached_data['pattern_centroids']
#         pattern_centroids = []
#         pattern_labels = []
#
#         for pattern_name, centroid_info in centroids_info['centroids'].items():
#             pattern_centroids.append(centroid_info['centroid_vector'])
#             pattern_labels.append(pattern_name)
#
#         # k-meansクラスタリングで使用
#         from sklearn.cluster import KMeans
#         kmeans = KMeans(n_clusters=len(pattern_centroids),
#                        init=np.array(pattern_centroids),
#                        n_init=1)  # 真のセントロイドなので1回で十分
#         # これで真のセントロイドを初期値とするクラスタリングが可能
#
# # 結合ベクトルのみを取得
# vectors = [r['integrated_vector'] for r in batch_results if 'error' not in r]
# print(f"取得された結合ベクトル数: {len(vectors)}")
# for i, vector in enumerate(vectors):
#     print(f"  submission_{i+1}: {vector}")  # 11次元ベクトル [CFG(6次元) + データフロー(5次元)]
