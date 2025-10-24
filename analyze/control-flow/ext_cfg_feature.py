# これが現状の最も正確なCFG解析コード
# - 関数単位でのループ・条件文検出（detect_function.py使用）
# - ループ考慮パス検出（path_dfs.py使用、2回まで訪問）
# - 再帰検出をloop_statementsに統合
# 関数単位でできた、パス数できた、あとは関数追跡出来たら完璧

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import os
import sys

# detect_function.pyから関数をインポート
try:
    from detect_function import (
        delete_comments,
        extract_functions_and_others,
        count_statements,
        get_all_function_stats,
        get_file_totals
    )
except ImportError:
    print("detect_function.pyが見つかりません。同じディレクトリに配置してください。")
    sys.exit(1)

# path_dfs.pyから関数をインポート
try:
    from path_dfs import (
        find_entry_exit_nodes,
        collect_all_paths
    )
except ImportError:
    print("path_dfs.pyが見つかりません。同じディレクトリに配置してください。")
    sys.exit(1)

def extract_function_level_features(source_code, cfg_name):
    """関数単位でのループ・条件文検出"""
    if not source_code:
        return {'loop_statements': 0, 'conditional_statements': 0}

    # コメントを除去
    filtered_code = delete_comments(source_code)

    # 関数とその他のコードを分離
    functions, other_code = extract_functions_and_others(filtered_code)

    # 特定の関数名に対応する統計を取得
    for func_name, func_body in functions:
        # 関数名マッチング（"def example(" → "example"）
        if func_name.startswith("def "):
            clean_func_name = func_name.split('(')[0].replace('def ', '').strip()
            if clean_func_name == cfg_name:
                if_count, for_count, while_count, match_count = count_statements(func_body)

                # ループ文：for + while
                loop_statements = for_count + while_count

                # 条件文：if/elif + while + for + match
                conditional_statements = if_count + while_count + for_count + match_count

                return {
                    'loop_statements': loop_statements,
                    'conditional_statements': conditional_statements,
                    'detail': {
                        'if_count': if_count,
                        'for_count': for_count,
                        'while_count': while_count,
                        'match_count': match_count
                    }
                }

    # 関数が見つからない場合（モジュールレベルなど）
    if cfg_name == '<module>' or cfg_name == '&lt;module&gt;':
        # モジュールレベルのコード（関数以外）から検出
        if_count, for_count, while_count, match_count = count_statements(other_code)
        loop_statements = for_count + while_count
        conditional_statements = if_count + while_count + for_count + match_count

        return {
            'loop_statements': loop_statements,
            'conditional_statements': conditional_statements,
            'detail': {
                'if_count': if_count,
                'for_count': for_count,
                'while_count': while_count,
                'match_count': match_count
            }
        }

    # 該当する関数が見つからない場合
    return {'loop_statements': 0, 'conditional_statements': 0}

def detect_language(source_code, filename):
    """ソースコードと拡張子から言語を判定"""
    if filename.endswith('.py'):
        return 'python'
    elif filename.endswith(('.c', '.cpp', '.cxx', '.cc', '.h', '.hpp')):
        return 'c_cpp'
    elif filename.endswith(('.java')):
        return 'java'
    elif filename.endswith(('.js', '.ts')):
        return 'javascript'
    else:
        # ソースコードの内容から推測
        if 'def ' in source_code and ':' in source_code:
            return 'python'
        elif '#include' in source_code:
            return 'c_cpp'
        elif 'public class' in source_code:
            return 'java'
        elif 'function ' in source_code or 'const ' in source_code:
            return 'javascript'
        else:
            return 'unknown'

def simple_remove_comments(source_code, language):
    """簡略化されたコメント除去（detect_function.pyのdelete_commentsを使用）"""
    return '\n'.join(delete_comments(source_code))

def extract_accurate_features(cfg, cfg_name, source_code=None, filename=None):
    """CFG構造分析に基づいた最適化された特徴量抽出（関数単位検出使用）"""
    features = {}

    # 1. Connected Components
    try:
        weakly_connected = list(nx.weakly_connected_components(cfg))
        features['connected_components'] = len(weakly_connected)
    except Exception:
        features['connected_components'] = 0

    # 2. ループ文と条件文検出（関数単位の正確な検出）
    if source_code:
        function_features = extract_function_level_features(source_code, cfg_name)
        base_loop_statements = function_features.get('loop_statements', 0)
        features['conditional_statements'] = function_features.get('conditional_statements', 0)

        # 詳細情報も保存
        if 'detail' in function_features:
            features['detail'] = function_features['detail']
    else:
        base_loop_statements = 0
        features['conditional_statements'] = 0

    # 3. 再帰検出（CFGから）
    recursive_loops = 0
    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                if (stmt.__class__.__name__ == 'Call' and
                    hasattr(stmt, 'func') and
                    stmt.func == cfg_name):
                    recursive_loops += 1

    # ループ文に再帰も含める
    features['loop_statements'] = base_loop_statements + recursive_loops
    features['recursive_loops'] = recursive_loops  # デバッグ用（表示は控える）

    # 4. Cycles
    try:
        cycles = list(nx.simple_cycles(cfg))
        features['cycles'] = len(cycles)
    except Exception:
        features['cycles'] = 0

    # 5. Paths（ループ考慮版 - path_dfs.pyから）
    try:
        entry_nodes, exit_nodes = find_entry_exit_nodes(cfg)

        total_paths = 0
        if entry_nodes and exit_nodes:
            for entry in entry_nodes:
                for exit_node in exit_nodes:
                    # path_dfs.pyのループ考慮パス検出を使用（2回まで訪問）
                    paths = collect_all_paths(cfg, entry, exit_node, max_visits=2)
                    total_paths += len(paths)

        features['paths'] = total_paths
    except Exception as e:
        print(f"パス計算エラー: {e}")
        features['paths'] = 0

    # 6. Cyclomatic Complexity
    try:
        E = cfg.number_of_edges()
        N = cfg.number_of_nodes()
        P = features.get('connected_components', 1)
        features['cyclomatic_complexity'] = E - N + 2 * P
    except Exception:
        features['cyclomatic_complexity'] = 0

    return features

def analyze_function_metadata(func_obj):
    """関数オブジェクトのメタデータも活用"""
    metadata = {}

    if hasattr(func_obj, 'control_structures'):
        control_structures = func_obj.control_structures

        # control_structuresからループと条件を推定
        loop_indicators = ['iteratorNonEmptyOrException']
        condition_indicators = ['>', '<', '==', '!=', '%']

        metadata_loops = sum(1 for cs in control_structures if any(li in cs for li in loop_indicators))

        # 従来の条件文 + forループ条件
        traditional_conditions = sum(1 for cs in control_structures
                                   if any(ci in cs for ci in condition_indicators)
                                   and not any(li in cs for li in loop_indicators))
        for_loop_conditions = sum(1 for cs in control_structures if any(li in cs for li in loop_indicators))

        metadata_conditions = traditional_conditions + for_loop_conditions

        metadata['metadata_loops'] = metadata_loops
        metadata['metadata_conditions'] = metadata_conditions
        metadata['traditional_conditions'] = traditional_conditions
        metadata['for_loop_conditions'] = for_loop_conditions
        metadata['control_structures'] = control_structures

    return metadata

def display_accurate_summary(all_features, source_code="", source_file=""):
    """正確な特徴量結果を表示（関数単位検出版）"""
    # print(f"\n{'='*80}")
    # print(f"CFG特徴量結果（関数単位検出）")
    # print(f"{'='*80}")

    # 全体集計（クラスタリング用メトリクス）
    if all_features:
        # print(f"\n🎯 全体集計 (クラスタリング用):")

        # 重複除去: 関数レベルの特徴量のみ使用（モジュールレベルは除外）
        function_features = {k: v for k, v in all_features.items()
                           if not (k.startswith('<module>') or k.startswith('&lt;module&gt;'))}

        # モジュールレベル特徴量（構造的特徴のみ）
        module_features = {k: v for k, v in all_features.items()
                         if k.startswith('<module>') or k.startswith('&lt;module&gt;')}

        # print(f"  📊 関数レベル特徴量: {len(function_features)}個")
        # print(f"  📊 モジュールレベル特徴量: {len(module_features)}個")

        # connected_components: 論理積（1つでも0があれば0、全て1以上なら1）
        all_connected_components = [features.get('connected_components', 0) for features in all_features.values()]
        total_connected = 1 if all(cc > 0 for cc in all_connected_components) else 0

        # ループと条件文: 関数単位で既に正確に計算済み（再帰含む）
        total_loops = sum(features.get('loop_statements', 0) for features in function_features.values())
        total_conditions = sum(features.get('conditional_statements', 0) for features in function_features.values())

        # モジュールレベルの分も追加
        total_loops += sum(features.get('loop_statements', 0) for features in module_features.values())
        total_conditions += sum(features.get('conditional_statements', 0) for features in module_features.values())

        # 構造的特徴: 全体から計算（関数+モジュール）
        total_cycles = sum(features.get('cycles', 0) for features in all_features.values())
        total_paths = sum(features.get('paths', 0) for features in all_features.values())
        total_complexity = sum(features.get('cyclomatic_complexity', 0) for features in all_features.values())

        # print(f"  total_connected_components: {total_connected}")
        # print(f"  function_level_loop_statements: {total_loops} (関数単位正確検出、再帰含む)")
        # print(f"  function_level_conditional_statements: {total_conditions} (関数単位正確検出)")
        # print(f"  total_cycles: {total_cycles}")
        # print(f"  total_paths: {total_paths} (ループ考慮版、2回まで訪問)")
        # print(f"  total_cyclomatic_complexity: {total_complexity}")

        # クラスタリング用ベクトル表示（関数単位検出版）
        # clustering_vector = [total_connected, total_loops, total_conditions, total_cycles, total_paths, total_complexity]
        # print(f"  📊 クラスタリング用ベクトル: {clustering_vector}")

    # print(f"\n個別CFG詳細:")
    # for cfg_name, features in all_features.items():
    #     print(f"\n{cfg_name}:")
    #     print(f"  connected_components: {features.get('connected_components', 0)}")
    #     print(f"  loop_statements: {features.get('loop_statements', 0)} (再帰含む)")
    #     print(f"  conditional_statements: {features.get('conditional_statements', 0)}")
    #     print(f"  cycles: {features.get('cycles', 0)}")
    #     print(f"  paths: {features.get('paths', 0)} (ループ考慮)")
    #     print(f"  cyclomatic_complexity: {features.get('cyclomatic_complexity', 0)}")

        # 詳細情報があれば表示
        # if 'detail' in features:
        #     detail = features['detail']
        #     recursive_count = features.get('recursive_loops', 0)
            # print(f"  詳細: if={detail.get('if_count', 0)}, for={detail.get('for_count', 0)}, while={detail.get('while_count', 0)}, match={detail.get('match_count', 0)}, recursive={recursive_count}")

def analyze_accurate_cfg(source_file):
    """CFG解析"""
    print(f"解析中: {source_file}")
    all_features = {}

    # ソースコード読み込み
    source_code = ""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        print(f"読み込みエラー: {e}")

    # 関数レベル解析
    try:
        functions = parse_source(source_file)
        for func_name, func_obj in functions.items():
            metadata = analyze_function_metadata(func_obj)
            cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
            if cfg and len(cfg.nodes()) > 0:
                features = extract_accurate_features(cfg, func_name, source_code, source_file)
                features.update(metadata)
                all_features[func_name] = features
    except Exception as e:
        print(f"関数解析エラー: {e}")

    # モジュールレベル解析
    try:
        cfgs = fast_cfgs_from_source(source_file)
        for cfg_name, cfg in cfgs.items():
            if (cfg_name.startswith('<operator>') or cfg_name.startswith('&lt;operator&gt;')):
                continue
            if cfg_name in all_features:
                continue
            if len(cfg.nodes()) > 0:
                features = extract_accurate_features(cfg, cfg_name, source_code, source_file)
                all_features[cfg_name] = features
    except Exception as e:
        print(f"モジュール解析エラー: {e}")

    display_accurate_summary(all_features, source_code, source_file)
    return all_features

def main():
    test_files = ["whiletest.py"]

    for test_file in test_files:
        try:
            analyze_accurate_cfg(test_file)
        except FileNotFoundError:
            print(f"ファイルが見つかりません: {test_file}")
        except Exception as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    main()
