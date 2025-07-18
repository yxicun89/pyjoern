#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyJoern包括的分析スクリプト
要求されたすべてのメトリクスを取得
"""

from pyjoern import parse_source
import networkx as nx
from collections import defaultdict
import re

def comprehensive_analysis(file_path="whiletest.py"):
    """包括的な分析を実行"""

    print("="*80)
    print("PyJoern包括的分析")
    print("="*80)

    functions = parse_source(file_path)

    for func_name, func_obj in functions.items():
        print(f"\n関数: {func_name}")
        print("-" * 40)

        if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):
            metrics = analyze_all_metrics(func_obj.cfg, func_name)
            display_metrics(metrics, func_name)

    return functions

def analyze_all_metrics(cfg, func_name):
    """すべてのメトリクスを分析"""

    metrics = {}

    # 1. Connected Components
    metrics['connected_components'] = analyze_connected_components(cfg)

    # 2. Loop Statements
    metrics['loop_statements'] = analyze_loop_statements(cfg)

    # 3. Conditional Statements
    metrics['conditional_statements'] = analyze_conditional_statements(cfg)

    # 4. Cycles
    metrics['cycles'] = analyze_cycles(cfg)

    # 5. Paths
    metrics['paths'] = analyze_paths(cfg)

    # 6. Cyclomatic Complexity
    metrics['cyclomatic_complexity'] = calculate_cyclomatic_complexity(cfg)

    # 7. Variable Analysis
    variable_metrics = analyze_variables(cfg)
    metrics.update(variable_metrics)

    return metrics

def analyze_connected_components(cfg):
    """接続されたコンポーネントの数を分析"""
    try:
        # 有向グラフを無向グラフに変換して接続成分を計算
        undirected_cfg = cfg.to_undirected()
        connected_components = nx.number_connected_components(undirected_cfg)
        return connected_components
    except Exception as e:
        print(f"Connected components分析エラー: {e}")
        return 0

def analyze_loop_statements(cfg):
    """ループステートメントの数を分析"""
    loop_count = 0
    loop_details = []

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                # ループの検出
                if ('range(' in stmt_str or
                    'for' in stmt_str.lower() or
                    'while' in stmt_str.lower() or
                    'iterator' in stmt_str.lower() or
                    '__iter__' in stmt_str or
                    '__next__' in stmt_str):

                    # 重複を避けるため、range()呼び出しのみをループとしてカウント
                    if stmt_type == 'Call' and 'range(' in stmt_str:
                        loop_count += 1
                        loop_details.append({
                            'type': 'for_loop',
                            'statement': stmt_str,
                            'node': node.addr
                        })
                    # iteratorの例外チェック（while文の一部）
                    elif 'iteratorNonEmptyOrException' in stmt_str:
                        loop_count += 1
                        loop_details.append({
                            'type': 'while_loop',
                            'statement': stmt_str,
                            'node': node.addr
                        })

    return {
        'count': loop_count,
        'details': loop_details
    }

def analyze_conditional_statements(cfg):
    """条件ステートメントの数を分析"""
    conditional_count = 0
    conditional_details = []

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                # 条件文の検出（Compare文のみ）
                if stmt_type == 'Compare':
                    conditional_count += 1
                    conditional_details.append({
                        'type': 'comparison',
                        'statement': stmt_str,
                        'node': node.addr
                    })

    return {
        'count': conditional_count,
        'details': conditional_details
    }

def analyze_cycles(cfg):
    """サイクルの数を分析"""
    try:
        # 単純サイクルの検出
        simple_cycles = list(nx.simple_cycles(cfg))
        cycle_count = len(simple_cycles)

        # 強連結成分（SCCs）の検出
        strongly_connected = list(nx.strongly_connected_components(cfg))
        scc_count = len([scc for scc in strongly_connected if len(scc) > 1])

        return {
            'simple_cycles': cycle_count,
            'strongly_connected_components': scc_count,
            'cycle_details': simple_cycles[:5]  # 最初の5つのサイクルを表示
        }
    except Exception as e:
        print(f"Cycles分析エラー: {e}")
        return {
            'simple_cycles': 0,
            'strongly_connected_components': 0,
            'cycle_details': []
        }

def analyze_paths(cfg):
    """パスの数を分析"""
    try:
        entry_nodes = [n for n in cfg.nodes if n.is_entrypoint]
        exit_nodes = [n for n in cfg.nodes if n.is_exitpoint]

        if not entry_nodes or not exit_nodes:
            return {
                'total_paths': 0,
                'path_details': []
            }

        total_paths = 0
        all_paths = []

        for entry in entry_nodes:
            for exit in exit_nodes:
                try:
                    simple_paths = list(nx.all_simple_paths(cfg, entry, exit))
                    total_paths += len(simple_paths)
                    all_paths.extend(simple_paths)
                except nx.NetworkXNoPath:
                    pass

        return {
            'total_paths': total_paths,
            'path_details': all_paths[:3]  # 最初の3つのパスを表示
        }
    except Exception as e:
        print(f"Paths分析エラー: {e}")
        return {
            'total_paths': 0,
            'path_details': []
        }

def calculate_cyclomatic_complexity(cfg):
    """サイクロマティック複雑度を計算"""
    try:
        # 条件分岐数
        conditional_count = 0
        for node in cfg.nodes:
            if hasattr(node, 'statements') and node.statements:
                for stmt in node.statements:
                    if type(stmt).__name__ == 'Compare':
                        conditional_count += 1

        # ループ数
        loop_count = 0
        for node in cfg.nodes:
            if hasattr(node, 'statements') and node.statements:
                for stmt in node.statements:
                    stmt_str = str(stmt)
                    if (type(stmt).__name__ == 'Call' and 'range(' in stmt_str) or \
                       'iteratorNonEmptyOrException' in stmt_str:
                        loop_count += 1

        # McCabe複雑度の計算
        # 方法1: 簡易版（条件分岐数 + ループ数 + 1）
        simple_complexity = conditional_count + loop_count + 1

        # 方法2: 正確な式 M = E - N + 2P
        # E = エッジ数, N = ノード数, P = 連結成分数
        E = len(cfg.edges)  # エッジ数
        N = len(cfg.nodes)  # ノード数

        # 連結成分数を計算
        try:
            undirected_cfg = cfg.to_undirected()
            P = nx.number_connected_components(undirected_cfg)
        except:
            P = 1  # エラーの場合は1とする

        # McCabe複雑度: M = E - N + 2P
        mccabe_complexity = E - N + 2 * P

        return {
            'complexity': mccabe_complexity,
            'simple_complexity': simple_complexity,
            'conditional_count': conditional_count,
            'loop_count': loop_count,
            'edges': E,
            'nodes': N,
            'connected_components': P,
            'formula': f"M = {E} - {N} + 2×{P} = {mccabe_complexity}"
        }
    except Exception as e:
        print(f"Cyclomatic complexity計算エラー: {e}")
        return {
            'complexity': 1,
            'simple_complexity': 1,
            'conditional_count': 0,
            'loop_count': 0,
            'edges': 0,
            'nodes': 0,
            'connected_components': 1,
            'formula': "計算エラー"
        }

def analyze_variables(cfg):
    """変数の読み書き分析"""
    variables = defaultdict(lambda: {'reads': 0, 'writes': 0})

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                # 代入の検出（書き込み）
                if stmt_type == 'Assignment':
                    # 代入文から変数名を抽出
                    match = re.match(r'(\w+)\s*=', stmt_str)
                    if match:
                        var_name = match.group(1)
                        variables[var_name]['writes'] += 1

                # += 演算子の検出（読み書き両方）
                elif stmt_type == 'UnsupportedStmt' and 'assignmentPlus' in stmt_str:
                    # x+=1 の形式から変数名を抽出
                    # パターン: <UnsupportedStmt: ['assignmentPlus', 'x+=1']>
                    match = re.search(r"'([a-zA-Z_]\w*)\s*\+=", stmt_str)
                    if match:
                        var_name = match.group(1)
                        variables[var_name]['reads'] += 1   # += は読み取りも行う
                        variables[var_name]['writes'] += 1  # += は書き込みも行う
                        print(f"[DEBUG] += 検出: {var_name} (読み書き両方)")

                # 他の複合代入演算子の検出 (-=, *=, /=, など)
                elif stmt_type == 'UnsupportedStmt' and any(op in stmt_str for op in ['assignmentMinus', 'assignmentMult', 'assignmentDiv', 'assignmentMod']):
                    # x-=1, x*=2, x/=3, x%=4 などから変数名を抽出
                    match = re.search(r"'([a-zA-Z_]\w*)\s*[+\-*/\%]=", stmt_str)
                    if match:
                        var_name = match.group(1)
                        variables[var_name]['reads'] += 1   # 複合代入は読み取りも行う
                        variables[var_name]['writes'] += 1  # 複合代入は書き込みも行う
                        operator = re.search(r'([+\-*/\%])=', stmt_str).group(0) if re.search(r'([+\-*/\%])=', stmt_str) else '?='
                        print(f"[DEBUG] {operator} 検出: {var_name} (読み書き両方)")

                # 変数読み取りの検出
                # Compare文での変数使用
                elif stmt_type == 'Compare':
                    # x > 0, x < 0 などから変数名を抽出
                    for var_name in re.findall(r'\b([a-zA-Z_]\w*)\b', stmt_str):
                        if var_name not in ['Compare', 'tmp0', 'tmp1']:  # 予約語を除外
                            variables[var_name]['reads'] += 1

                # 関数呼び出しでの変数使用
                elif stmt_type == 'Call':
                    # range(x), print(i) などから変数名を抽出
                    for var_name in re.findall(r'\b([a-zA-Z_]\w*)\b', stmt_str):
                        if var_name not in ['range', 'print', 'Call', 'tmp0', 'tmp1']:  # 関数名を除外
                            variables[var_name]['reads'] += 1

    # 統計の計算
    variable_count = len(variables)
    total_reads = sum(var_data['reads'] for var_data in variables.values())
    total_writes = sum(var_data['writes'] for var_data in variables.values())

    max_reads = max([var_data['reads'] for var_data in variables.values()] + [0])
    max_writes = max([var_data['writes'] for var_data in variables.values()] + [0])

    # デバッグ情報
    print(f"[DEBUG] 変数分析結果:")
    for var_name, var_data in variables.items():
        print(f"[DEBUG]   {var_name}: 読み取り={var_data['reads']}, 書き込み={var_data['writes']}")

    return {
        'variable_count': variable_count,
        'total_reads': total_reads,
        'total_writes': total_writes,
        'max_reads': max_reads,
        'max_writes': max_writes,
        'variable_details': dict(variables)
    }

def display_metrics(metrics, func_name):
    """メトリクスを表示"""

    print(f"\n=== {func_name} の包括的分析結果 ===")

    # 基本メトリクス
    print(f"\n1. Connected Components: {metrics['connected_components']}")

    # ループ
    loop_info = metrics['loop_statements']
    print(f"\n2. Loop Statements: {loop_info['count']}")
    for i, loop in enumerate(loop_info['details'], 1):
        print(f"   {i}. {loop['type']}: {loop['statement']} (ノード: {loop['node']})")

    # 条件文
    cond_info = metrics['conditional_statements']
    print(f"\n3. Conditional Statements: {cond_info['count']}")
    for i, cond in enumerate(cond_info['details'], 1):
        print(f"   {i}. {cond['type']}: {cond['statement']} (ノード: {cond['node']})")

    # サイクル
    cycle_info = metrics['cycles']
    print(f"\n4. Cycles:")
    print(f"   - Simple Cycles: {cycle_info['simple_cycles']}")
    print(f"   - Strongly Connected Components: {cycle_info['strongly_connected_components']}")

    # パス
    path_info = metrics['paths']
    print(f"\n5. Paths: {path_info['total_paths']}")
    for i, path in enumerate(path_info['path_details'], 1):
        path_desc = " -> ".join([f"Block:{n.addr}" for n in path])
        print(f"   パス {i}: {path_desc}")

    # 循環複雑度
    complexity_info = metrics['cyclomatic_complexity']
    print(f"\n6. Cyclomatic Complexity: {complexity_info['complexity']}")
    print(f"   - McCabe式: {complexity_info['formula']}")
    print(f"   - 簡易計算: {complexity_info['simple_complexity']}")
    print(f"   - 条件分岐: {complexity_info['conditional_count']}")
    print(f"   - ループ: {complexity_info['loop_count']}")
    print(f"   - エッジ数: {complexity_info['edges']}")
    print(f"   - ノード数: {complexity_info['nodes']}")
    print(f"   - 連結成分数: {complexity_info['connected_components']}")

    # 変数分析
    print(f"\n7. Variable Analysis:")
    print(f"   - Variable Count: {metrics['variable_count']}")
    print(f"   - Total Reads: {metrics['total_reads']}")
    print(f"   - Total Writes: {metrics['total_writes']}")
    print(f"   - Max Reads: {metrics['max_reads']}")
    print(f"   - Max Writes: {metrics['max_writes']}")

    print(f"\n   変数詳細:")
    for var_name, var_data in metrics['variable_details'].items():
        print(f"     {var_name}: 読み取り={var_data['reads']}, 書き込み={var_data['writes']}")

def create_summary_table(functions):
    """要約テーブルを作成"""

    print("\n" + "="*80)
    print("要約テーブル")
    print("="*80)

    for func_name, func_obj in functions.items():
        if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):
            metrics = analyze_all_metrics(func_obj.cfg, func_name)

            print(f"\n関数: {func_name}")
            print("-" * 40)

            # 要求されたメトリクスのみを表示
            required_metrics = [
                ('connected_components', 'Connected Components'),
                ('loop_statements', 'Loop Statements'),
                ('conditional_statements', 'Conditional Statements'),
                ('cycles', 'Cycles'),
                ('paths', 'Paths'),
                ('cyclomatic_complexity', 'Cyclomatic Complexity'),
                ('variable_count', 'Variable Count'),
                ('total_reads', 'Total Reads'),
                ('total_writes', 'Total Writes'),
                ('max_reads', 'Max Reads'),
                ('max_writes', 'Max Writes')
            ]

            for metric_key, metric_name in required_metrics:
                if metric_key in metrics:
                    if isinstance(metrics[metric_key], dict):
                        if metric_key == 'loop_statements':
                            value = metrics[metric_key]['count']
                        elif metric_key == 'conditional_statements':
                            value = metrics[metric_key]['count']
                        elif metric_key == 'cycles':
                            value = metrics[metric_key]['simple_cycles']
                        elif metric_key == 'paths':
                            value = metrics[metric_key]['total_paths']
                        elif metric_key == 'cyclomatic_complexity':
                            value = metrics[metric_key]['complexity']
                        else:
                            value = str(metrics[metric_key])
                    else:
                        value = metrics[metric_key]

                    print(f"{metric_name:25}: {value}")

            # McCabe複雑度の詳細を追加表示
            complexity_info = metrics['cyclomatic_complexity']
            print(f"{'McCabe Formula':25}: {complexity_info['formula']}")
            print(f"{'Simple Complexity':25}: {complexity_info['simple_complexity']}")
            print(f"{'Graph Edges (E)':25}: {complexity_info['edges']}")
            print(f"{'Graph Nodes (N)':25}: {complexity_info['nodes']}")
            print(f"{'Components (P)':25}: {complexity_info['connected_components']}")

if __name__ == "__main__":
    # 包括的分析を実行
    functions = comprehensive_analysis()

    # 要約テーブルを作成
    create_summary_table(functions)

    print("\n" + "="*80)
    print("包括的分析完了")
    print("="*80)
