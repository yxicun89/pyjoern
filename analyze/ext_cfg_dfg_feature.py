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

    print(f"📂 統合特徴量抽出開始: {len(file_list)}ファイル")

    for i, source_file in enumerate(file_list, 1):
        try:
            result = extract_integrated_features_vector(source_file)
            results.append({
                'source_file': source_file,
                'integrated_vector': result
            })

        except Exception as e:
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

    print(f"📂 CFG特徴量抽出開始: {len(file_list)}ファイル")

    for i, source_file in enumerate(file_list, 1):
        try:
            result = extract_cfg_features_vector(source_file)
            results.append(result)

        except Exception as e:
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
    ファイルをパターン別にグループ分けして分析（動的パターン認識対応）

    Args:
        file_list (list): ファイルパスのリスト
        base_directory (str): ベースディレクトリパス

    Returns:
        dict: グループ分析結果
    """
    import re

    groups = {}

    for file_path in file_list:
        relative_path = os.path.relpath(file_path, base_directory)
        path_parts = relative_path.split(os.sep)

        # 動的パターン抽出（kmeans_final_clean.pyと同じロジック）
        group_name = extract_pattern_from_file_path(file_path)

        if group_name not in groups:
            groups[group_name] = []

        groups[group_name].append({
            'file_path': file_path,
            'relative_path': relative_path,
            'filename': os.path.basename(file_path),
            'pattern': group_name
        })

    return groups

def extract_pattern_from_file_path(filepath):
    """
    ファイルパスからパターン情報を動的に抽出

    Args:
        filepath: ファイルパス

    Returns:
        str: パターン名 (例: "typical90_aa", "typical90_d", "AC", "TLE")
    """
    import re

    # パスを正規化（バックスラッシュをスラッシュに変換）
    normalized_path = filepath.replace('\\', '/')

    # パターンを検出する正規表現のリスト（優先順位順）
    pattern_regexes = [
        # submissions_typical90_xx パターン（最優先）
        (r'submissions_typical90_([a-z]+)', lambda m: f"typical90_{m.group(1)}"),
        # pattern + 数字
        (r'pattern(\d+)', lambda m: f"pattern{m.group(1)}"),
        # AC, TLE などの結果パターン（明確なアンダースコア区切り）
        (r'_([A-Z]{2,3})(?:_|$|/)', lambda m: m.group(1)),
        # ディレクトリ名が結果を表す場合
        (r'/([A-Z]{2,3})/', lambda m: m.group(1)),
        # その他のsubmissions_パターン
        (r'submissions_([^/]+?)(?:_\d+)?/', lambda m: m.group(1) if not m.group(1).startswith('submission') else None),
    ]

    for pattern_regex, extract_func in pattern_regexes:
        match = re.search(pattern_regex, normalized_path)
        if match:
            result = extract_func(match)
            if result:
                # 一般的でない形式や短すぎるパターンを除外
                if len(result) >= 2 and not result.isdigit():
                    return result

    # どのパターンにも一致しない場合
    # ただし、明らかにファイル名パターンがある場合は再試行
    filename = os.path.basename(filepath)

    # ファイル名からパターンを抽出する最後の試行
    filename_patterns = [
        (r'^([a-z]+\d*)_', lambda m: m.group(1)),  # prefix_xxx形式
        (r'_([a-z]+\d*)\.', lambda m: m.group(1)), # xxx_suffix.ext形式
    ]

    for pattern_regex, extract_func in filename_patterns:
        match = re.search(pattern_regex, filename.lower())
        if match:
            result = extract_func(match)
            if result and len(result) >= 2:
                return result

    return "other"

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
        # ファイルメタデータを収集（差分検出用）
        file_metadata = {}
        for result in batch_results:
            if 'source_file' in result:
                file_path = result['source_file']
                try:
                    if os.path.exists(file_path):
                        mtime = os.path.getmtime(file_path)
                        size = os.path.getsize(file_path)
                        file_metadata[file_path] = {
                            'mtime': mtime,
                            'size': size,
                            'timestamp': datetime.fromtimestamp(mtime).isoformat()
                        }
                except Exception as e:
                    print(f"⚠️ ファイルメタデータ取得エラー {file_path}: {e}")

        # メタデータを追加
        save_data = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(batch_results),
            'successful_extractions': len([r for r in batch_results if 'error' not in r]),
            'feature_names': {
                'cfg_features': get_cfg_feature_names(),
                'dataflow_features': get_dataflow_feature_names()
            },
            'file_metadata': file_metadata,  # 差分検出用メタデータ
            'data': batch_results
        }

        # パターン別セントロイドも計算・保存
        if groups is not None and base_directory is not None:
            centroids_data = calculate_pattern_centroids(batch_results, groups, base_directory)

            if centroids_data and centroids_data['centroids']:
                save_data['pattern_centroids'] = centroids_data
                print(f"✅ セントロイド追加: {len(centroids_data['centroids'])}個")
            else:
                save_data['pattern_centroids'] = None
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

        print(f"💾 特徴量ベクトル保存: '{output_file}' ({format.upper()})")
        print(f"   総ファイル: {save_data['total_files']}, 成功: {save_data['successful_extractions']}")
        if save_data['pattern_centroids']:
            print(f"   セントロイド: {len(save_data['pattern_centroids']['centroids'])}個")

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

        print(f"📂 特徴量読み込み: '{input_file}'")
        print(f"   ファイル数: {data['total_files']}, 成功: {data['successful_extractions']}")

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
    # 成功した結果のみを使用
    successful_results = [r for r in batch_results if 'error' not in r]

    if len(successful_results) == 0:
        return {}

    # 特徴量ベクトルを取得
    feature_vectors = np.array([r['integrated_vector'] for r in successful_results])
    file_paths = [r['source_file'] for r in successful_results]

    # ファイルパスをグループにマッピング
    file_to_group = {}
    for group_name, group_files in groups.items():
        for file_info in group_files:
            file_to_group[file_info['file_path']] = group_name

    # パターングループのみを対象にする（外れ値otherは除外）
    pattern_groups = {k: v for k, v in groups.items() if k.startswith('pattern')}

    # 外れ値('other')グループは真のセントロイドに含めない
    if 'other' in groups and len(groups['other']) > 0:
        print(f"ℹ️  外れ値除外: {len(groups['other'])}ファイル (既存クラスターに分散配置)")

    centroids_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'base_directory': base_directory,
            'total_patterns': len(pattern_groups),
            'excludes_other_group': True,  # 外れ値(other)は除外
            'meaningful_patterns_only': True,  # 意味あるパターンのみ
            'feature_dimension': len(feature_vectors[0]) if len(feature_vectors) > 0 else 0,
            'feature_names': {
                'cfg_features': get_cfg_feature_names(),
                'dataflow_features': get_dataflow_feature_names()
            }
        },
        'centroids': {}
    }

    print(f"🎯 セントロイド計算: {len(pattern_groups)}個の意味あるパターン")

    for pattern_name, pattern_files in pattern_groups.items():
        # パターンに属するファイルのインデックスを取得
        pattern_indices = []
        pattern_file_paths = []

        for i, file_path in enumerate(file_paths):
            if file_to_group.get(file_path) == pattern_name:
                pattern_indices.append(i)
                pattern_file_paths.append(file_path)

        if not pattern_indices:
            continue

        # パターンの特徴量ベクトルを抽出
        pattern_vectors = feature_vectors[pattern_indices]

        # セントロイド（重心）を計算
        centroid = np.mean(pattern_vectors, axis=0).tolist()

        # セントロイド情報を保存
        centroids_data['centroids'][pattern_name] = {
            'centroid_vector': centroid,
            'sample_count': len(pattern_indices),
            'file_paths': pattern_file_paths
        }

        print(f"   {pattern_name}: {len(pattern_indices)}ファイル")

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

        print(f"💾 セントロイド保存: '{output_file}'")
        print(f"   パターン数: {centroids_data['metadata']['total_patterns']}")

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

        print(f"📂 セントロイド読み込み: '{input_file}'")
        print(f"   パターン数: {data['metadata']['total_patterns']}")

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

def detect_file_changes(target_directory, cache_file):
    """
    対象ディレクトリとキャッシュファイル間の差分を検出

    Args:
        target_directory (str): 対象ディレクトリ
        cache_file (str): キャッシュファイル

    Returns:
        dict: {
            'new_files': [],      # 新規追加されたファイル
            'modified_files': [], # 変更されたファイル
            'deleted_files': [],  # 削除されたファイル
            'unchanged_files': [] # 変更なしファイル
        }
    """
    print("🔍 ファイル差分検出中...")

    # 現在のディレクトリ内のファイルを取得
    current_files = find_files_in_directory(target_directory)
    current_file_info = {}

    for file_path in current_files:
        try:
            mtime = os.path.getmtime(file_path)
            size = os.path.getsize(file_path)
            current_file_info[file_path] = {
                'mtime': mtime,
                'size': size
            }
        except Exception as e:
            print(f"⚠️ ファイル情報取得エラー {file_path}: {e}")
            continue

    # キャッシュファイルから既存情報を読み込み
    cached_file_info = {}
    if os.path.exists(cache_file):
        try:
            cached_data = load_feature_vectors(cache_file)
            if cached_data and 'file_metadata' in cached_data:
                cached_file_info = cached_data['file_metadata']
            elif cached_data and 'data' in cached_data:
                # 既存のキャッシュから情報を再構築
                for item in cached_data['data']:
                    if 'source_file' in item:
                        file_path = item['source_file']
                        if os.path.exists(file_path):
                            try:
                                mtime = os.path.getmtime(file_path)
                                size = os.path.getsize(file_path)
                                cached_file_info[file_path] = {
                                    'mtime': mtime,
                                    'size': size
                                }
                            except:
                                pass
        except Exception as e:
            print(f"⚠️ キャッシュ読み込みエラー: {e}")

    # 差分を計算
    current_files_set = set(current_files)
    cached_files_set = set(cached_file_info.keys())

    # 新規ファイル
    new_files = list(current_files_set - cached_files_set)

    # 削除されたファイル
    deleted_files = list(cached_files_set - current_files_set)

    # 変更されたファイルと変更なしファイル
    modified_files = []
    unchanged_files = []

    for file_path in current_files_set & cached_files_set:
        current_info = current_file_info.get(file_path, {})
        cached_info = cached_file_info.get(file_path, {})

        # ファイルサイズまたは更新時刻が異なる場合は変更あり
        if (current_info.get('mtime', 0) != cached_info.get('mtime', 0) or
            current_info.get('size', 0) != cached_info.get('size', 0)):
            modified_files.append(file_path)
        else:
            unchanged_files.append(file_path)

    changes = {
        'new_files': new_files,
        'modified_files': modified_files,
        'deleted_files': deleted_files,
        'unchanged_files': unchanged_files
    }

    # 差分情報を表示
    print(f"📊 ファイル差分: 新規{len(new_files)} 変更{len(modified_files)} 削除{len(deleted_files)} 変更なし{len(unchanged_files)}")

    return changes

def update_cache_incrementally(target_directory, cache_file, file_changes):
    """
    ファイル差分に基づいてキャッシュを増分更新

    Args:
        target_directory (str): 対象ディレクトリ
        cache_file (str): キャッシュファイル
        file_changes (dict): detect_file_changes()の戻り値

    Returns:
        list: 更新後の特徴量データ
    """
    print("🔄 キャッシュ増分更新中...")

    # 既存キャッシュを読み込み
    existing_data = []
    existing_metadata = {}
    if os.path.exists(cache_file):
        try:
            cached_data = load_feature_vectors(cache_file)
            if cached_data and 'data' in cached_data:
                existing_data = cached_data['data']
            if cached_data and 'file_metadata' in cached_data:
                existing_metadata = cached_data['file_metadata']
        except Exception as e:
            print(f"⚠️ 既存キャッシュ読み込みエラー: {e}")

    # 変更なしファイルのデータを保持
    preserved_data = []
    for item in existing_data:
        if 'source_file' in item and item['source_file'] in file_changes['unchanged_files']:
            preserved_data.append(item)

    # 新規・変更ファイルを処理
    files_to_process = file_changes['new_files'] + file_changes['modified_files']
    new_data = []

    if files_to_process:
        new_data = batch_extract_integrated_features(files_to_process)

    # データを統合
    updated_data = preserved_data + new_data

    print(f"📦 保持: {len(preserved_data)}, 新規処理: {len(new_data)}, 総計: {len(updated_data)}")

    return updated_data

def visualize_feature_distribution(batch_results, groups, base_directory):
    """
    特徴量の分布をグループ別に可視化

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
    print("📊 PCA可視化中...")
    pca = PCA(n_components=2)
    feature_vectors_2d = pca.fit_transform(feature_vectors)

    # 全体プロット
    plt.figure(figsize=(12, 8))

    # グループごとにプロット
    for group_name in groups.keys():
        group_indices = [i for i, label in enumerate(labels) if label == group_name]
        if group_indices:
            group_points = feature_vectors_2d[group_indices]
            plt.scatter(group_points[:, 0], group_points[:, 1],
                       c=group_colors[group_name],
                       label=f'{group_name} ({len(group_indices)})',
                       alpha=0.7, s=60)

    plt.title(f'Feature Distribution\n{base_directory}', fontsize=14)
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontsize=12)
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"feature_distribution_{timestamp}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"📸 可視化保存: {filename}")

    plt.show()

    # 統計情報を出力
    print(f"📈 統計: {len(successful_results)}サンプル, {feature_vectors.shape[1]}次元")
    for group_name, group_files in groups.items():
        group_count = len([f for f in group_files if f['file_path'] in file_paths])
        print(f"  {group_name}: {group_count}ファイル")

def main():
    """メイン関数 - テスト実行"""
    print("🎯 統合特徴量抽出システム（CFG + データフロー）")

    target_directory = "submissions_typical90_d_15_AC_TLE"
    cache_file = f"feature_cache_{os.path.basename(target_directory)}.json"

    if not os.path.exists(target_directory):
        print(f"❌ ディレクトリが存在しません: {target_directory}")
        return

    target_files = find_files_in_directory(target_directory)
    if not target_files:
        print("⚠️  処理対象ファイルが見つかりません")
        return

    print(f"📁 発見ファイル: {len(target_files)}個")

    # ファイルをグループ分析
    groups = analyze_file_groups(target_files, target_directory)
    print(f"📂 グループ: {', '.join([f'{k}({len(v)})' for k, v in groups.items()])}")

    # キャッシュ処理
    batch_results = None
    if os.path.exists(cache_file):
        file_changes = detect_file_changes(target_directory, cache_file)

        if all(len(file_changes[key]) == 0 for key in ['new_files', 'modified_files', 'deleted_files']):
            print(f"📦 キャッシュ使用: {cache_file}")
            cached_data = load_feature_vectors(cache_file)
            if cached_data:
                batch_results = cached_data['data']
        elif len(file_changes['unchanged_files']) > 0:
            print("🔄 増分更新実行")
            batch_results = update_cache_incrementally(target_directory, cache_file, file_changes)
            save_feature_vectors(batch_results, groups, target_directory, cache_file, format='json')
        else:
            print("🆕 完全再実行")

    if batch_results is None:
        print("🔄 新規特徴量抽出")
        batch_results = batch_extract_integrated_features(target_files)
        save_feature_vectors(batch_results, groups, target_directory, cache_file, format='json')

    # 結果表示
    successful = len([r for r in batch_results if 'error' not in r])
    print(f"📊 結果: {successful}/{len(batch_results)} 成功")

    # 可視化
    try:
        visualize_feature_distribution(batch_results, groups, target_directory)
    except Exception as e:
        print(f"❌ 可視化エラー: {e}")

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
