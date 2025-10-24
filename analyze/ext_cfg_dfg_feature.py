# CFG特徴量抽出モジュール
# ext-cfg-feature.pyからクラスタリングベクトルを簡潔に抽出
# ext_feature_data_flow.pyからデータフロー特徴量も抽出

import sys
import os

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

def main():
    """メイン関数 - 複数ファイル一括処理のテスト実行"""
    print("🎯 統合特徴量抽出システム（CFG + データフロー）")

    # submission ファイルの設定
    submission_start = 1  # 開始番号
    submission_end = 5    # 終了番号
    submission_prefix = "submission_"  # ファイル名のプレフィックス

    # 解析対象ファイルリスト
    target_files = ["whiletest.py"]  # 追加したいファイル

    # submission_1 から submission_5 まで自動追加
    for i in range(submission_start, submission_end + 1):
        submission_file = f"{submission_prefix}{i}.py"
        target_files.append(submission_file)

    # 存在するファイルのみをフィルタリング
    found_files = []
    for file in target_files:
        if os.path.exists(file):
            found_files.append(file)
        else:
            print(f"⚠️  ファイルが見つかりません: {file}")

    if found_files:
        print(f"\n📁 処理対象ファイル: {len(found_files)}個")
        for i, file in enumerate(found_files, 1):
            print(f"  {i:2d}. {file}")

        # 複数ファイルの一括処理を実行
        print(f"\n� 複数ファイル一括処理開始")
        batch_results = batch_extract_integrated_features(found_files)

        # 結果を表示
        print(f"\n📊 一括処理結果:")
        # print(f"クラスタリングベクトル: {batch_results}")
        for i, result in enumerate(batch_results, 1):
            filename = os.path.basename(result['source_file'])

            if 'error' in result:
                print(f"  {i:2d}. ❌ {filename}: エラー")
            else:
                print(f"  {i:2d}. ✅ {filename}: {result['integrated_vector']}")

    else:
        print("⚠️  処理対象ファイルが見つかりませんでした")

if __name__ == "__main__":
    main()

# 使用例:
#
# from cfg_feature_extractor import (
#     extract_cfg_features_vector,
#     extract_dataflow_features_vector,
#     extract_integrated_features_vector,
#     batch_extract_integrated_features
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
# for result in batch_results:
#     if 'error' not in result:
#         print(f"{result['source_file']}: {result['integrated_vector']}")
#     else:
#         print(f"{result['source_file']}: エラー - {result['error']}")
#
# # 結合ベクトルのみを取得
# vectors = [r['integrated_vector'] for r in batch_results if 'error' not in r]
# print(f"取得された結合ベクトル数: {len(vectors)}")
# for i, vector in enumerate(vectors):
#     print(f"  submission_{i+1}: {vector}")  # 11次元ベクトル [CFG(6次元) + データフロー(5次元)]
