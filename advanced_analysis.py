#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改良されたPyJoern分析スクリプト
より正確な条件分岐検出とコード特徴抽出
"""

from pyjoern import parse_source
import networkx as nx

def advanced_code_analysis(file_path="whiletest.py"):
    """高度なコード分析"""

    print("="*80)
    print("高度なPyJoernコード分析")
    print("="*80)

    functions = parse_source(file_path)

    for func_name, func_obj in functions.items():
        print(f"\n関数: {func_name}")
        print("-" * 40)

        # 基本情報
        print(f"開始行: {func_obj.start_line}")
        print(f"終了行: {func_obj.end_line}")

        if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):
            analyze_control_flow(func_obj.cfg, func_name)
            analyze_code_features(func_obj.cfg)
            calculate_advanced_metrics(func_obj.cfg)

def analyze_control_flow(cfg, func_name):
    """制御フロー分析"""

    print(f"\n=== 制御フロー分析 ({func_name}) ===")

    # 真の条件分岐を検出
    true_conditions = []
    loop_structures = []
    function_calls = []
    assignments = []

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                # 真の条件分岐のみを検出
                if stmt_type == 'Compare':
                    true_conditions.append({
                        'statement': stmt_str,
                        'type': stmt_type,
                        'node': node.addr
                    })

                # ループ構造（range関数呼び出し）
                elif stmt_type == 'Call' and 'range(' in stmt_str:
                    loop_structures.append({
                        'statement': stmt_str,
                        'type': 'LoopInit',
                        'node': node.addr
                    })

                # 関数呼び出し
                elif stmt_type == 'Call' and 'range(' not in stmt_str:
                    function_calls.append({
                        'statement': stmt_str,
                        'type': stmt_type,
                        'node': node.addr
                    })

                # 代入
                elif stmt_type == 'Assignment':
                    assignments.append({
                        'statement': stmt_str,
                        'type': stmt_type,
                        'node': node.addr
                    })

    # 結果表示
    print(f"真の条件分岐: {len(true_conditions)}個")
    for i, condition in enumerate(true_conditions, 1):
        print(f"  {i}. {condition['statement']} (ノード: {condition['node']})")

    print(f"\nループ構造: {len(loop_structures)}個")
    for i, loop in enumerate(loop_structures, 1):
        print(f"  {i}. {loop['statement']} (ノード: {loop['node']})")

    print(f"\n関数呼び出し: {len(function_calls)}個")
    for i, call in enumerate(function_calls, 1):
        print(f"  {i}. {call['statement']} (ノード: {call['node']})")

    print(f"\n代入: {len(assignments)}個")
    for i, assignment in enumerate(assignments, 1):
        print(f"  {i}. {assignment['statement']} (ノード: {assignment['node']})")

    return true_conditions, loop_structures, function_calls, assignments

def analyze_code_features(cfg):
    """コード特徴分析"""

    print(f"\n=== コード特徴分析 ===")

    # 制御構造の特徴
    control_features = {
        'conditional_branches': 0,
        'loops': 0,
        'function_calls': 0,
        'assignments': 0,
        'returns': 0
    }

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                if stmt_type == 'Compare':
                    control_features['conditional_branches'] += 1
                elif stmt_type == 'Call' and 'range(' in stmt_str:
                    control_features['loops'] += 1
                elif stmt_type == 'Call':
                    control_features['function_calls'] += 1
                elif stmt_type == 'Assignment':
                    control_features['assignments'] += 1
                elif stmt_type == 'Return':
                    control_features['returns'] += 1

    print("制御構造の特徴:")
    for feature, count in control_features.items():
        print(f"  - {feature}: {count}")

    return control_features

def calculate_advanced_metrics(cfg):
    """高度なメトリクス計算"""

    print(f"\n=== 高度なメトリクス ===")

    # ノードとエッジの数
    node_count = len(cfg.nodes)
    edge_count = len(cfg.edges)

    # 条件分岐数
    condition_count = sum(1 for node in cfg.nodes
                         if hasattr(node, 'statements') and node.statements
                         for stmt in node.statements
                         if type(stmt).__name__ == 'Compare')

    # ループ数
    loop_count = sum(1 for node in cfg.nodes
                    if hasattr(node, 'statements') and node.statements
                    for stmt in node.statements
                    if type(stmt).__name__ == 'Call' and 'range(' in str(stmt))

    # 循環複雑度
    cyclomatic_complexity = condition_count + loop_count + 1

    # 密度メトリクス
    if node_count > 0:
        edge_density = edge_count / node_count
        control_density = (condition_count + loop_count) / node_count
    else:
        edge_density = 0
        control_density = 0

    print(f"基本メトリクス:")
    print(f"  - ノード数: {node_count}")
    print(f"  - エッジ数: {edge_count}")
    print(f"  - 条件分岐数: {condition_count}")
    print(f"  - ループ数: {loop_count}")

    print(f"\n複雑度メトリクス:")
    print(f"  - 循環複雑度: {cyclomatic_complexity}")
    print(f"  - エッジ密度: {edge_density:.2f}")
    print(f"  - 制御構造密度: {control_density:.2f}")

    # パス複雑度
    try:
        entry_nodes = [n for n in cfg.nodes if n.is_entrypoint]
        exit_nodes = [n for n in cfg.nodes if n.is_exitpoint]

        if entry_nodes and exit_nodes:
            total_paths = 0
            for entry in entry_nodes:
                for exit in exit_nodes:
                    try:
                        simple_paths = list(nx.all_simple_paths(cfg, entry, exit))
                        total_paths += len(simple_paths)
                    except nx.NetworkXNoPath:
                        pass

            print(f"  - 単純パス数: {total_paths}")
            print(f"  - 推定実行パス数: {2 ** condition_count}")

    except Exception as e:
        print(f"  - パス分析エラー: {e}")

def generate_analysis_report(file_path="whiletest.py"):
    """分析レポートの生成"""

    print("\n" + "="*80)
    print("分析レポート生成")
    print("="*80)

    functions = parse_source(file_path)

    for func_name, func_obj in functions.items():
        if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):

            # 基本統計
            true_conditions, loops, calls, assignments = analyze_control_flow(func_obj.cfg, func_name)

            # レポート生成
            print(f"\n=== 分析レポート: {func_name} ===")
            print(f"ソースコード行数: {func_obj.end_line - func_obj.start_line + 1}")
            print(f"制御フローグラフ:")
            print(f"  - ノード数: {len(func_obj.cfg.nodes)}")
            print(f"  - エッジ数: {len(func_obj.cfg.edges)}")

            print(f"\n検出された制御構造:")
            print(f"  - 条件分岐: {len(true_conditions)}個")
            print(f"  - ループ: {len(loops)}個")
            print(f"  - 関数呼び出し: {len(calls)}個")
            print(f"  - 代入: {len(assignments)}個")

            # 循環複雑度
            complexity = len(true_conditions) + len(loops) + 1
            print(f"\n複雑度指標:")
            print(f"  - 循環複雑度: {complexity}")

            # 複雑度の評価
            if complexity <= 10:
                complexity_level = "低"
            elif complexity <= 20:
                complexity_level = "中"
            else:
                complexity_level = "高"

            print(f"  - 複雑度レベル: {complexity_level}")

            # 推奨事項
            print(f"\n推奨事項:")
            if complexity > 10:
                print("  - 関数を小さく分割することを検討してください")
            if len(true_conditions) > 5:
                print("  - 条件分岐を減らすことを検討してください")
            if len(loops) > 3:
                print("  - ネストしたループを避けることを検討してください")

            if complexity <= 10:
                print("  - 現在の複雑度は適切です")

if __name__ == "__main__":
    # 高度な分析を実行
    advanced_code_analysis()

    # 分析レポートを生成
    generate_analysis_report()

    print("\n" + "="*80)
    print("分析完了")
    print("="*80)
