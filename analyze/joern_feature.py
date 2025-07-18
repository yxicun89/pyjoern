# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# """
# DDGを活用した11個の特徴量の高精度抽出
# """

# from pyjoern import parse_source
# import networkx as nx
# from collections import defaultdict
# import pandas as pd
# import os
# import re

# def extract_11_features(file_path):
#     """11個の特徴量を高精度で抽出"""

#     try:
#         functions = parse_source(file_path)
#     except Exception as e:
#         print(f"パースエラー {file_path}: {e}")
#         return None

#     results = []

#     for func_name, func_obj in functions.items():
#         if not func_obj.cfg:
#             continue

#         print(f"関数 '{func_name}' を分析中...")

#         features = {
#             'file_path': file_path,
#             'function_name': func_name
#         }

#         # CFGから基本特徴量を抽出
#         cfg_features = extract_cfg_features(func_obj.cfg)
#         features.update(cfg_features)

#         # DDGからデータフロー特徴量を抽出
#         if hasattr(func_obj, 'ddg') and func_obj.ddg:
#             print(f"  DDGを使用してデータフロー特徴量を抽出...")
#             ddg_features = extract_ddg_features(func_obj.ddg)
#             features.update(ddg_features)
#         else:
#             print(f"  DDGが存在しないため、CFGから推定...")
#             fallback_features = extract_fallback_features(func_obj.cfg)
#             features.update(fallback_features)

#         results.append(features)

#         # 抽出結果を表示
#         print(f"  抽出された特徴量:")
#         for key, value in features.items():
#             if key not in ['file_path', 'function_name']:
#                 print(f"    {key}: {value}")
#         print()

#     return results

# def extract_cfg_features(cfg):
#     """CFGから基本的な5つの特徴量を抽出"""

#     features = {}

#     # 1. Connected Components
#     features['connected_components'] = nx.number_connected_components(cfg.to_undirected())

#     # 2. Loop Statements
#     features['loop_statements'] = count_loop_statements(cfg)

#     # 3. Conditional Statements
#     features['conditional_statements'] = count_conditional_statements(cfg)

#     # 4. Cycles
#     try:
#         features['cycles'] = len(list(nx.simple_cycles(cfg)))
#     except:
#         features['cycles'] = 0

#     # 5. Cyclomatic Complexity
#     E = len(cfg.edges)
#     N = len(cfg.nodes)
#     P = features['connected_components']
#     features['cyclomatic_complexity'] = E - N + 2 * P

#     # 6. Paths (推定)
#     features['paths'] = estimate_paths(cfg)

#     return features

# def extract_ddg_features(ddg):
#     """DDGから高精度なデータフロー特徴量を抽出"""

#     features = {}

#     # DDGの基本統計
#     print(f"    DDG統計: ノード数={len(ddg.nodes)}, エッジ数={len(ddg.edges)}")

#     # 変数の分析
#     variables = set()
#     read_operations = defaultdict(int)
#     write_operations = defaultdict(int)

#     # DDGノードからの変数抽出
#     for node in ddg.nodes:
#         node_str = str(node)

#         # 代入文（書き込み）の検出
#         if '=' in node_str and not any(op in node_str for op in ['==', '!=', '<=', '>=', '+=', '-=', '*=', '/=']):
#             # 左辺の変数名を抽出
#             left_side = node_str.split('=')[0].strip()
#             var_match = re.search(r'(\w+)', left_side)
#             if var_match:
#                 var_name = var_match.group(1)
#                 if var_name.isidentifier() and not var_name in ['if', 'for', 'while', 'def', 'class']:
#                     variables.add(var_name)
#                     write_operations[var_name] += 1
#                     print(f"      書き込み検出: {var_name}")

#         # 複合代入演算子（読み取り+書き込み）
#         elif any(op in node_str for op in ['+=', '-=', '*=', '/=']):
#             var_match = re.search(r'(\w+)\s*[+\-*/]=', node_str)
#             if var_match:
#                 var_name = var_match.group(1)
#                 if var_name.isidentifier():
#                     variables.add(var_name)
#                     read_operations[var_name] += 1
#                     write_operations[var_name] += 1
#                     print(f"      複合代入検出: {var_name}")

#     # DDGエッジからの読み取り操作検出
#     for u, v, data in ddg.edges(data=True):
#         u_str = str(u)
#         v_str = str(v)

#         # エッジが表すデータフローを分析
#         for var_name in variables:
#             # 変数がエッジの両端に現れる場合、データフローがある
#             if var_name in u_str and var_name in v_str:
#                 read_operations[var_name] += 1
#                 print(f"      読み取り検出: {var_name} ({u_str} -> {v_str})")

#     # 特徴量の計算
#     features['variable_count'] = len(variables)
#     features['total_reads'] = sum(read_operations.values())
#     features['total_writes'] = sum(write_operations.values())

#     # 比率と平均の計算
#     if features['total_writes'] > 0:
#         features['read_write_ratio'] = features['total_reads'] / features['total_writes']
#     else:
#         features['read_write_ratio'] = 0

#     if features['variable_count'] > 0:
#         features['avg_variable_usage'] = (features['total_reads'] + features['total_writes']) / features['variable_count']
#     else:
#         features['avg_variable_usage'] = 0

#     print(f"    データフロー特徴量:")
#     print(f"      変数数: {features['variable_count']}")
#     print(f"      読み取り総数: {features['total_reads']}")
#     print(f"      書き込み総数: {features['total_writes']}")
#     print(f"      読み取り/書き込み比率: {features['read_write_ratio']:.2f}")
#     print(f"      平均変数使用回数: {features['avg_variable_usage']:.2f}")

#     return features

# def extract_fallback_features(cfg):
#     """DDGがない場合のフォールバック機能"""

#     features = {}

#     variables = defaultdict(lambda: {'reads': 0, 'writes': 0})

#     for node in cfg.nodes:
#         if hasattr(node, 'statements') and node.statements:
#             for stmt in node.statements:
#                 stmt_str = str(stmt)
#                 stmt_type = type(stmt).__name__

#                 # 代入文（書き込み）
#                 if stmt_type == 'Assignment':
#                     var_match = re.match(r'(\w+)\s*=', stmt_str)
#                     if var_match:
#                         var_name = var_match.group(1)
#                         if var_name.isidentifier():
#                             variables[var_name]['writes'] += 1

#                 # 変数使用（読み取り）
#                 elif stmt_type in ['Compare', 'Call']:
#                     for var_name in list(variables.keys()):
#                         if var_name in stmt_str:
#                             variables[var_name]['reads'] += 1

#     features['variable_count'] = len(variables)
#     features['total_reads'] = sum(v['reads'] for v in variables.values())
#     features['total_writes'] = sum(v['writes'] for v in variables.values())

#     if features['total_writes'] > 0:
#         features['read_write_ratio'] = features['total_reads'] / features['total_writes']
#     else:
#         features['read_write_ratio'] = 0

#     if features['variable_count'] > 0:
#         features['avg_variable_usage'] = (features['total_reads'] + features['total_writes']) / features['variable_count']
#     else:
#         features['avg_variable_usage'] = 0

#     return features

# def count_loop_statements(cfg):
#     """ループ文の数をカウント"""
#     count = 0
#     for node in cfg.nodes:
#         if hasattr(node, 'statements') and node.statements:
#             for stmt in node.statements:
#                 stmt_str = str(stmt).lower()
#                 if ('range(' in stmt_str or
#                     'iterator' in stmt_str or
#                     'while' in stmt_str or
#                     'for ' in stmt_str):
#                     count += 1
#     return count

# def count_conditional_statements(cfg):
#     """条件文の数をカウント"""
#     count = 0
#     for node in cfg.nodes:
#         if hasattr(node, 'statements') and node.statements:
#             for stmt in node.statements:
#                 if type(stmt).__name__ == 'Compare':
#                     count += 1
#     return count

# def estimate_paths(cfg):
#     """実行パス数を推定"""
#     try:
#         # 入口ノードを特定
#         entry_nodes = [n for n in cfg.nodes if cfg.in_degree(n) == 0]
#         if not entry_nodes:
#             entry_nodes = [next(iter(cfg.nodes))]

#         # 出口ノードを特定
#         exit_nodes = [n for n in cfg.nodes if cfg.out_degree(n) == 0]
#         if not exit_nodes:
#             exit_nodes = entry_nodes

#         total_paths = 0
#         for entry in entry_nodes[:1]:  # 最初の入口のみ
#             for exit in exit_nodes[:3]:   # 最初の3つの出口のみ
#                 try:
#                     paths = list(nx.all_simple_paths(cfg, entry, exit))
#                     total_paths += len(paths)
#                     if total_paths > 1000:  # 計算量制限
#                         return total_paths
#                 except:
#                     pass

#         return max(total_paths, 1)
#     except:
#         return 1

# def batch_process(directory_path, output_file="features_final.csv"):
#     """ディレクトリ内の全Pythonファイルを一括処理"""

#     all_features = []
#     processed_files = 0
#     error_files = []

#     print(f"ディレクトリ '{directory_path}' 内のPythonファイルを処理中...")

#     for root, dirs, files in os.walk(directory_path):
#         for file in files:
#             if file.endswith('.py'):
#                 file_path = os.path.join(root, file)
#                 print(f"\n[{processed_files + 1}] 処理中: {file_path}")

#                 try:
#                     features = extract_11_features(file_path)
#                     if features:
#                         all_features.extend(features)
#                         print(f"  ✓ {len(features)} 個の関数から特徴量を抽出")
#                     else:
#                         print(f"  ⚠ 特徴量を抽出できませんでした")
#                 except Exception as e:
#                     print(f"  ✗ エラー: {e}")
#                     error_files.append(file_path)

#                 processed_files += 1

#     # 結果をCSVに保存
#     if all_features:
#         df = pd.DataFrame(all_features)
#         df.to_csv(output_file, index=False)

#         print(f"\n=== 処理完了 ===")
#         print(f"処理ファイル数: {processed_files}")
#         print(f"エラーファイル数: {len(error_files)}")
#         print(f"抽出された関数数: {len(all_features)}")
#         print(f"結果ファイル: {output_file}")

#         # 統計情報
#         print(f"\n=== 特徴量統計 ===")
#         feature_cols = [col for col in df.columns if col not in ['file_path', 'function_name']]
#         print(df[feature_cols].describe())

#         return df
#     else:
#         print("\n特徴量が抽出されませんでした")
#         return None

# if __name__ == "__main__":
#     # 単一ファイルのテスト
#     test_file = "whiletest.py"
#     if os.path.exists(test_file):
#         print("=== 単一ファイルテスト ===")
#         features = extract_11_features(test_file)

#         if features:
#             print(f"\n抽出された特徴量一覧:")
#             for feature_set in features:
#                 print(f"\n関数: {feature_set['function_name']}")
#                 for i, (key, value) in enumerate(feature_set.items()):
#                     if key not in ['file_path', 'function_name']:
#                         print(f"  {i+1:2d}. {key:25}: {value}")

#     # 大量処理の例（コメントアウト）
#     # batch_process(".", "extracted_features_final.csv")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyJoernのDDGを活用した11個の正確な特徴量抽出
"""

from pyjoern import parse_source
import networkx as nx
from collections import defaultdict
import pandas as pd
import os
import re

def extract_11_features(file_path):
    """11個の特徴量を正確に抽出"""

    try:
        functions = parse_source(file_path)
    except Exception as e:
        print(f"パースエラー {file_path}: {e}")
        return None

    if not functions:
        print(f"関数が見つかりませんでした: {file_path}")
        return None

    results = []

    for func_name, func_obj in functions.items():
        print(f"\n=== 関数 '{func_name}' の特徴量抽出 ===")

        # CFGが必要
        if not hasattr(func_obj, 'cfg') or not func_obj.cfg:
            print(f"  CFGが存在しません。スキップします。")
            continue

        features = {
            'file_path': file_path,
            'function_name': func_name
        }

        # CFGベースの特徴量（1-6）
        cfg_features = extract_cfg_features(func_obj.cfg, func_name)
        features.update(cfg_features)

        # DDGベースの変数特徴量（7-11）
        if hasattr(func_obj, 'ddg') and func_obj.ddg:
            print(f"  DDGを使用してデータフロー特徴量を抽出")
            ddg_features = extract_ddg_features(func_obj.ddg, func_name)
            features.update(ddg_features)
        else:
            print(f"  DDGが存在しないため、CFGから変数特徴量を推定")
            fallback_features = extract_variable_features_from_cfg(func_obj.cfg, func_name)
            features.update(fallback_features)

        results.append(features)

        # 結果を表示
        print(f"  抽出された特徴量:")
        for i, (key, value) in enumerate(features.items()):
            if key not in ['file_path', 'function_name']:
                print(f"    {i+1:2d}. {key:25}: {value}")

    return results

def extract_cfg_features(cfg, func_name):
    """CFGから基本的な6つの特徴量を抽出"""

    print(f"  CFGから基本特徴量を抽出中...")
    features = {}

    # 1. Connected Components
    features['connected_components'] = nx.number_connected_components(cfg.to_undirected())
    print(f"    connected_components: {features['connected_components']}")

    # 2. Loop Statements
    features['loop_statements'] = count_loop_statements(cfg)
    print(f"    loop_statements: {features['loop_statements']}")

    # 3. Conditional Statements
    features['conditional_statements'] = count_conditional_statements(cfg)
    print(f"    conditional_statements: {features['conditional_statements']}")

    # 4. Cycles
    try:
        cycles = list(nx.simple_cycles(cfg))
        features['cycles'] = len(cycles)
        print(f"    cycles: {features['cycles']}")
    except Exception as e:
        print(f"    cycles計算エラー: {e}")
        features['cycles'] = 0

    # 5. Paths
    features['paths'] = count_paths(cfg)
    print(f"    paths: {features['paths']}")

    # 6. Cyclomatic Complexity
    E = len(cfg.edges)
    N = len(cfg.nodes)
    P = features['connected_components']
    features['cyclomatic_complexity'] = E - N + 2 * P
    print(f"    cyclomatic_complexity: {features['cyclomatic_complexity']} (E:{E} - N:{N} + 2*P:{P})")

    return features

def extract_ddg_features(ddg, func_name):
    """DDGから変数関連の5つの特徴量を抽出"""

    print(f"    DDG統計: ノード数={len(ddg.nodes)}, エッジ数={len(ddg.edges)}")

    # 変数ごとの読み書きカウント
    variable_stats = defaultdict(lambda: {'reads': 0, 'writes': 0})

    # DDGノードから変数の書き込み操作を検出
    for node in ddg.nodes:
        node_str = str(node)

        # 代入文の検出（書き込み操作）
        if '=' in node_str and not any(op in node_str for op in ['==', '!=', '<=', '>=', '+=', '-=', '*=', '/=']):
            # 左辺の変数名を抽出
            left_side = node_str.split('=')[0].strip()
            var_match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', left_side)
            if var_match:
                var_name = var_match.group(1)
                # Python予約語やビルトイン関数は除外
                if var_name not in ['if', 'for', 'while', 'def', 'class', 'print', 'range', 'len', 'str', 'int', 'float']:
                    variable_stats[var_name]['writes'] += 1
                    print(f"      書き込み検出: {var_name}")

        # 複合代入演算子（読み取り + 書き込み）
        elif any(op in node_str for op in ['+=', '-=', '*=', '/=', '%=', '**=', '//=']):
            var_match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b\s*[+\-*/%]*=', node_str)
            if var_match:
                var_name = var_match.group(1)
                if var_name not in ['if', 'for', 'while', 'def', 'class', 'print', 'range', 'len', 'str', 'int', 'float']:
                    variable_stats[var_name]['reads'] += 1
                    variable_stats[var_name]['writes'] += 1
                    print(f"      複合代入検出: {var_name}")

    # DDGエッジから変数の読み取り操作を検出
    for u, v, data in ddg.edges(data=True):
        u_str = str(u)
        v_str = str(v)

        # 既知の変数がエッジで使用されているかチェック
        for var_name in variable_stats.keys():
            # 変数がエッジの終点（使用側）に現れる場合
            if var_name in v_str and var_name not in u_str:
                variable_stats[var_name]['reads'] += 1
                print(f"      読み取り検出: {var_name} (DDGエッジ)")

    # DDGノードで明示的な変数使用を検出
    for node in ddg.nodes:
        node_str = str(node)

        # 条件文、関数呼び出しでの変数使用
        if any(keyword in node_str.lower() for keyword in ['compare', 'call', 'if', 'while']):
            for var_name in variable_stats.keys():
                if var_name in node_str:
                    variable_stats[var_name]['reads'] += 1
                    print(f"      読み取り検出: {var_name} (条件/呼び出し)")

    # 読み込まれない変数を除外
    used_variables = {var: stats for var, stats in variable_stats.items() if stats['reads'] > 0}

    # 特徴量計算
    features = {}
    features['variable_count'] = len(used_variables)
    features['total_reads'] = sum(stats['reads'] for stats in used_variables.values())
    features['total_writes'] = sum(stats['writes'] for stats in used_variables.values())

    if used_variables:
        features['max_reads'] = max(stats['reads'] for stats in used_variables.values())
        features['max_writes'] = max(stats['writes'] for stats in used_variables.values())
    else:
        features['max_reads'] = 0
        features['max_writes'] = 0

    print(f"    変数統計:")
    print(f"      総変数数: {len(variable_stats)}")
    print(f"      使用される変数数: {features['variable_count']}")
    print(f"      総読み取り数: {features['total_reads']}")
    print(f"      総書き込み数: {features['total_writes']}")
    print(f"      最大読み取り数: {features['max_reads']}")
    print(f"      最大書き込み数: {features['max_writes']}")

    # 変数詳細を表示（最初の5つ）
    if used_variables:
        print(f"    変数詳細 (上位5個):")
        for i, (var_name, stats) in enumerate(list(used_variables.items())[:5]):
            print(f"      {var_name}: 読み取り={stats['reads']}, 書き込み={stats['writes']}")

    return features

def extract_variable_features_from_cfg(cfg, func_name):
    """DDGがない場合のフォールバック：CFGから変数特徴量を推定"""

    print(f"    CFGから変数特徴量を推定中...")

    variable_stats = defaultdict(lambda: {'reads': 0, 'writes': 0})

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                # 代入文（書き込み）
                if stmt_type == 'Assignment':
                    var_match = re.match(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b\s*=', stmt_str)
                    if var_match:
                        var_name = var_match.group(1)
                        if var_name not in ['if', 'for', 'while', 'def', 'class', 'print', 'range', 'len', 'str', 'int', 'float']:
                            variable_stats[var_name]['writes'] += 1

                # 変数使用（読み取り）
                elif stmt_type in ['Compare', 'Call']:
                    for var_name in list(variable_stats.keys()):
                        if var_name in stmt_str:
                            variable_stats[var_name]['reads'] += 1

    # 読み込まれない変数を除外
    used_variables = {var: stats for var, stats in variable_stats.items() if stats['reads'] > 0}

    features = {}
    features['variable_count'] = len(used_variables)
    features['total_reads'] = sum(stats['reads'] for stats in used_variables.values())
    features['total_writes'] = sum(stats['writes'] for stats in used_variables.values())

    if used_variables:
        features['max_reads'] = max(stats['reads'] for stats in used_variables.values())
        features['max_writes'] = max(stats['writes'] for stats in used_variables.values())
    else:
        features['max_reads'] = 0
        features['max_writes'] = 0

    return features

def count_loop_statements(cfg):
    """ループ文の数をカウント"""
    count = 0
    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt).lower()
                # ループ関連のキーワードを検出
                if ('range(' in stmt_str or
                    'iterator' in stmt_str or
                    'while' in stmt_str or
                    'for ' in stmt_str or
                    '__iter__' in stmt_str or
                    '__next__' in stmt_str):
                    count += 1
    return count

def count_conditional_statements(cfg):
    """条件文の数をカウント"""
    count = 0
    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_type = type(stmt).__name__
                stmt_str = str(stmt)
                # 条件文を検出
                if (stmt_type == 'Compare' or
                    'Compare' in stmt_str or
                    'if ' in stmt_str.lower() or
                    'elif ' in stmt_str.lower()):
                    count += 1
    return count

def count_paths(cfg):
    """実行パス数をカウント（計算量制限付き）"""
    try:
        # 入口ノードを特定
        entry_nodes = [n for n in cfg.nodes if cfg.in_degree(n) == 0]
        if not entry_nodes:
            entry_nodes = [next(iter(cfg.nodes))]

        # 出口ノードを特定
        exit_nodes = [n for n in cfg.nodes if cfg.out_degree(n) == 0]
        if not exit_nodes:
            exit_nodes = entry_nodes

        total_paths = 0
        max_paths_per_pair = 100  # 計算量制限

        for entry in entry_nodes[:2]:  # 最初の2つの入口のみ
            for exit in exit_nodes[:3]:   # 最初の3つの出口のみ
                try:
                    # すべての単純パスを列挙（制限付き）
                    paths = list(nx.all_simple_paths(cfg, entry, exit))
                    path_count = min(len(paths), max_paths_per_pair)
                    total_paths += path_count

                    if total_paths > 1000:  # 全体の計算量制限
                        return total_paths
                except Exception:
                    pass

        return max(total_paths, 1)
    except Exception:
        return 1

def batch_process(directory_path, output_file="extracted_features.csv"):
    """ディレクトリ内の全Pythonファイルを一括処理"""

    all_features = []
    processed_files = 0
    error_files = []

    print(f"ディレクトリ '{directory_path}' 内のPythonファイルを処理中...")

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f"\n[{processed_files + 1}] 処理中: {file_path}")

                try:
                    features = extract_11_features(file_path)
                    if features:
                        all_features.extend(features)
                        print(f"  ✓ {len(features)} 個の関数から特徴量を抽出")
                    else:
                        print(f"  ⚠ 特徴量を抽出できませんでした")
                except Exception as e:
                    print(f"  ✗ エラー: {e}")
                    error_files.append(file_path)

                processed_files += 1

    # 結果をCSVに保存
    if all_features:
        df = pd.DataFrame(all_features)
        df.to_csv(output_file, index=False)

        print(f"\n=== 処理完了 ===")
        print(f"処理ファイル数: {processed_files}")
        print(f"エラーファイル数: {len(error_files)}")
        print(f"抽出された関数数: {len(all_features)}")
        print(f"結果ファイル: {output_file}")

        # 統計情報
        print(f"\n=== 特徴量統計 ===")
        feature_cols = [col for col in df.columns if col not in ['file_path', 'function_name']]
        print(df[feature_cols].describe())

        return df
    else:
        print("\n特徴量が抽出されませんでした")
        return None

if __name__ == "__main__":
    # 単一ファイルのテスト
    test_file = "whiletest.py"
    if os.path.exists(test_file):
        print("=== 単一ファイルテスト ===")
        features = extract_11_features(test_file)

        if features:
            print(f"\n=== 最終結果 ===")
            for feature_set in features:
                print(f"\n関数: {feature_set['function_name']}")
                for i, (key, value) in enumerate(feature_set.items()):
                    if key not in ['file_path', 'function_name']:
                        print(f"  {i+1:2d}. {key:30}: {value}")

    # 大量処理の例（コメントアウト）
    # batch_process(".", "final_features.csv")
