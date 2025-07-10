#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyjoern import parse_source, fast_cfgs_from_source
import json
import networkx as nx

def debug_whiletest():
    """whiletest.pyのノード構造を詳しく調べる"""

    print("="*60)
    print("=== whiletest.py のデバッグ解析 ===")
    print("="*60)

    file_path = "whiletest.py"

    try:
        # 完全なパース解析
        print("\n1. 完全なパース解析:")
        functions = parse_source(file_path)

        if functions:
            print(f"検出された関数: {list(functions.keys())}")

            for func_name, func_obj in functions.items():
                print(f"\n--- 関数: {func_name} ---")
                print(f"開始行: {func_obj.start_line}")
                print(f"終了行: {func_obj.end_line}")

                # CFGの全ノードを詳しく調べる
                if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):
                    print(f"\nCFG ノード数: {len(func_obj.cfg.nodes)}")
                    print(f"CFG エッジ数: {len(func_obj.cfg.edges)}")

                    print("\n=== 全CFGノードの詳細 ===")
                    for i, node in enumerate(func_obj.cfg.nodes):
                        print(f"\nノード {i+1}:")
                        print(f"  型: {type(node)}")
                        print(f"  repr: {repr(node)}")

                        if hasattr(node, '__dict__'):
                            node_dict = node.__dict__
                            print(f"  __dict__の内容:")
                            for key, value in node_dict.items():
                                print(f"    {key}: {value}")

                        # 利用可能な属性をすべて表示
                        print(f"  利用可能な属性: {dir(node)}")

                        # よくある属性をチェック
                        common_attrs = ['name', 'code', 'type', 'line_number', 'value', 'kind', 'node_type', 'ast_type']
                        for attr in common_attrs:
                            if hasattr(node, attr):
                                print(f"  {attr}: {getattr(node, attr)}")

                # ASTの全ノードも調べる
                if func_obj.ast and isinstance(func_obj.ast, nx.DiGraph):
                    print(f"\n=== AST ノード数: {len(func_obj.ast.nodes)} ===")
                    print("AST ノードの最初の10個:")
                    for i, node in enumerate(list(func_obj.ast.nodes)[:10]):
                        print(f"\nASTノード {i+1}:")
                        print(f"  型: {type(node)}")
                        print(f"  repr: {repr(node)}")

                        if hasattr(node, '__dict__'):
                            node_dict = node.__dict__
                            print(f"  __dict__の内容:")
                            for key, value in node_dict.items():
                                print(f"    {key}: {value}")

        # 高速CFG生成も調べる
        print("\n\n2. 高速CFG生成:")
        cfgs = fast_cfgs_from_source(file_path)

        if cfgs:
            print(f"検出されたCFG: {list(cfgs.keys())}")

            for func_name, cfg in cfgs.items():
                if isinstance(cfg, nx.DiGraph):
                    print(f"\n--- 高速CFG: {func_name} ---")
                    print(f"ノード数: {len(cfg.nodes)}")
                    print(f"エッジ数: {len(cfg.edges)}")

                    print("\n=== 高速CFG 全ノード詳細 ===")
                    for i, node in enumerate(cfg.nodes):
                        print(f"\nノード {i+1}:")
                        print(f"  型: {type(node)}")
                        print(f"  repr: {repr(node)}")

                        if hasattr(node, '__dict__'):
                            node_dict = node.__dict__
                            print(f"  __dict__の内容:")
                            for key, value in node_dict.items():
                                print(f"    {key}: {value}")

                        # 利用可能な属性をすべて表示
                        print(f"  利用可能な属性: {dir(node)}")

        # 改良されたクエリを試す
        print("\n\n3. 改良されたクエリ:")
        improved_query_analysis(functions)

        # 条件分岐検出の修正版
        fix_condition_detection()

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def improved_query_analysis(functions):
    """改良されたクエリ分析 - statementsを正しく解析"""
    print("改良されたクエリ分析:")

    for func_name, func_obj in functions.items():
        print(f"\n--- {func_name} の改良分析 ---")

        if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):
            # より正確な制御構造の検出
            condition_nodes = []
            loop_nodes = []
            call_nodes = []
            assignment_nodes = []
            compare_nodes = []

            for node in func_obj.cfg.nodes:
                # statementsを調べる
                if hasattr(node, 'statements') and node.statements:
                    for stmt in node.statements:
                        stmt_str = str(stmt)
                        stmt_repr = repr(stmt)
                        stmt_type = type(stmt).__name__

                        # 条件分岐の検出（Compare文とCONTROL_STRUCTURE）
                        if stmt_type == 'Compare' or 'Compare' in stmt_str:
                            condition_nodes.append((node, stmt_str, stmt_type))
                            print(f"[DEBUG] 条件分岐発見: {stmt_str}")

                        # 制御構造の検出（UnsupportedStmt内）
                        if 'CONTROL_STRUCTURE' in stmt_str:
                            condition_nodes.append((node, stmt_str, stmt_type))
                            print(f"[DEBUG] 制御構造発見: {stmt_str}")

                        # ループの検出（range呼び出し、iterator関連）
                        if any(keyword in stmt_str.lower() for keyword in ['range(', 'iterator', '__iter__', '__next__']):
                            loop_nodes.append((node, stmt_str, stmt_type))

                        # 関数呼び出しの検出
                        if stmt_type == 'Call' or 'Call' in stmt_str:
                            call_nodes.append((node, stmt_str, stmt_type))
                            print(f"[DEBUG] 関数呼び出し発見: {stmt_str}")

                        # 代入の検出
                        if stmt_type == 'Assignment' or 'Assignment' in stmt_str:
                            assignment_nodes.append((node, stmt_str, stmt_type))
                            print(f"[DEBUG] 代入発見: {stmt_str}")

            print(f"条件分岐ノード: {len(condition_nodes)}個")
            for i, (node, stmt, stmt_type) in enumerate(condition_nodes):
                print(f"  {i+1}. [{stmt_type}] {stmt}")

            print(f"ループ関連ノード: {len(loop_nodes)}個")
            for i, (node, stmt, stmt_type) in enumerate(loop_nodes):
                print(f"  {i+1}. [{stmt_type}] {stmt}")

            print(f"関数呼び出しノード: {len(call_nodes)}個")
            for i, (node, stmt, stmt_type) in enumerate(call_nodes):
                print(f"  {i+1}. [{stmt_type}] {stmt}")

            print(f"代入ノード: {len(assignment_nodes)}個")
            for i, (node, stmt, stmt_type) in enumerate(assignment_nodes):
                print(f"  {i+1}. [{stmt_type}] {stmt}")

            print(f"特殊ノード分析:")
            print(f"  - while文のx < 0: {'<Compare: x < 0>' in str([stmt for node in func_obj.cfg.nodes for stmt in node.statements if hasattr(node, 'statements')])}")
            print(f"  - if文のx > 0: {'<Compare: x > 0>' in str([stmt for node in func_obj.cfg.nodes for stmt in node.statements if hasattr(node, 'statements')])}")
            print(f"  - print(i)呼び出し: {'print(i)' in str([stmt for node in func_obj.cfg.nodes for stmt in node.statements if hasattr(node, 'statements')])}")

            # 循環複雑度の計算
            # 条件分岐 = Compare文の数
            # ループ = range呼び出しやiterator関連の数
            decision_points = len([stmt for _, stmt, _ in condition_nodes if 'Compare:' in stmt])
            loop_points = len([stmt for _, stmt, _ in loop_nodes if 'range(' in stmt])

            cyclomatic_complexity = decision_points + loop_points + 1
            print(f"循環複雑度（推定）: {cyclomatic_complexity}")
            print(f"  - 条件分岐: {decision_points}")
            print(f"  - ループ: {loop_points}")

            # 制御フロー分析
            print(f"\n制御フロー分析:")
            print(f"  - エントリーポイント: {len([n for n in func_obj.cfg.nodes if n.is_entrypoint])}個")
            print(f"  - エグジットポイント: {len([n for n in func_obj.cfg.nodes if n.is_exitpoint])}個")
            print(f"  - 総ノード数: {len(func_obj.cfg.nodes)}")
            print(f"  - 総エッジ数: {len(func_obj.cfg.edges)}")

            # パス分析を追加
            print(f"\nパス分析:")
            analyze_paths(func_obj.cfg)

def analyze_paths(cfg):
    """CFGのパス分析を行う"""
    try:
        # エントリーポイントとエグジットポイントを特定
        entry_nodes = [n for n in cfg.nodes if n.is_entrypoint]
        exit_nodes = [n for n in cfg.nodes if n.is_exitpoint]

        print(f"  - エントリーポイント: {len(entry_nodes)}個")
        print(f"  - エグジットポイント: {len(exit_nodes)}個")

        if not entry_nodes or not exit_nodes:
            print("  - エントリーまたはエグジットポイントが見つかりません")
            return

        # 簡単なパス数の計算
        total_paths = 0
        for entry in entry_nodes:
            for exit in exit_nodes:
                try:
                    # NetworkXを使用してすべてのシンプルパスを取得
                    simple_paths = list(nx.all_simple_paths(cfg, entry, exit))
                    total_paths += len(simple_paths)
                    print(f"  - {entry} から {exit} への単純パス: {len(simple_paths)}個")

                    # 最初の3つのパスを表示
                    for i, path in enumerate(simple_paths[:3]):
                        path_desc = " -> ".join([f"Block:{n.addr}" for n in path])
                        print(f"    パス {i+1}: {path_desc}")

                    if len(simple_paths) > 3:
                        print(f"    ... 他 {len(simple_paths) - 3} 個のパス")

                except nx.NetworkXNoPath:
                    print(f"  - {entry} から {exit} への経路なし")
                except Exception as e:
                    print(f"  - パス計算エラー: {e}")

        print(f"  - 総パス数（単純パス）: {total_paths}個")

        # 実行可能パスの推定
        estimate_executable_paths(cfg)

    except Exception as e:
        print(f"  - パス分析エラー: {e}")

def estimate_executable_paths(cfg):
    """実行可能パスの推定"""
    try:
        # 条件分岐の数を数える
        condition_count = 0
        loop_count = 0

        for node in cfg.nodes:
            if hasattr(node, 'statements') and node.statements:
                for stmt in node.statements:
                    stmt_str = str(stmt)
                    if 'Compare:' in stmt_str:
                        condition_count += 1
                    elif 'range(' in stmt_str or 'iterator' in stmt_str.lower():
                        loop_count += 1

        # 簡単な推定: 2^(条件分岐数) * ループ回数の概算
        estimated_paths = 2 ** condition_count
        if loop_count > 0:
            estimated_paths *= 3  # ループがある場合は3倍（0回、1回、複数回実行）

        print(f"  - 推定実行可能パス数: {estimated_paths}個")
        print(f"    (条件分岐: {condition_count}個, ループ: {loop_count}個)")

    except Exception as e:
        print(f"  - 実行可能パス推定エラー: {e}")

def fix_condition_detection():
    """条件分岐検出の修正版"""
    print("\n=== 条件分岐検出の修正デバッグ ===")

    file_path = "whiletest.py"
    functions = parse_source(file_path)

    for func_name, func_obj in functions.items():
        print(f"\n--- {func_name} の直接検出 ---")

        condition_count = 0
        compare_statements = []
        control_structures = []

        for i, node in enumerate(func_obj.cfg.nodes):
            print(f"ノード {i+1} (Block:{node.addr}):")

            if hasattr(node, 'statements') and node.statements:
                for j, stmt in enumerate(node.statements):
                    stmt_str = str(stmt)
                    stmt_type = type(stmt).__name__

                    print(f"  Statement {j+1}: [{stmt_type}] {stmt_str}")

                    # 条件分岐の直接検出 - 修正版
                    if (stmt_type == 'Compare' or
                        'Compare' in stmt_str or
                        'ast.Compare' in stmt_str or
                        ('>' in stmt_str and 'x' in stmt_str) or
                        ('<' in stmt_str and 'x' in stmt_str) or
                        'comparators' in stmt_str):
                        condition_count += 1
                        compare_statements.append(stmt_str)
                        print(f"    ★ 条件分岐検出: {stmt_str}")

                    # 制御構造の検出
                    if 'CONTROL_STRUCTURE' in stmt_str:
                        control_structures.append(stmt_str)
                        print(f"    ★ 制御構造検出: {stmt_str}")

        print(f"\n=== 検出結果サマリー ===")
        print(f"直接検出された条件分岐: {condition_count}個")
        print(f"Compare文の詳細:")
        for i, stmt in enumerate(compare_statements):
            print(f"  {i+1}. {stmt}")

        print(f"制御構造: {len(control_structures)}個")
        for i, stmt in enumerate(control_structures):
            print(f"  {i+1}. {stmt}")

        # 追加の分析
        print(f"\n=== 追加分析 ===")
        print(f"検出されたCompare文から推測される条件分岐:")

        # x > 0 と x < 0 の両方があるかチェック
        has_greater_than = any('x > 0' in stmt or 'x>0' in stmt for stmt in compare_statements)
        has_less_than = any('x < 0' in stmt or 'x<0' in stmt for stmt in compare_statements)

        print(f"  - if文 (x > 0): {'✓' if has_greater_than else '✗'}")
        print(f"  - while文 (x < 0): {'✓' if has_less_than else '✗'}")

        # 実際の制御フロー構造の推定
        estimated_branches = 0
        if has_greater_than:
            estimated_branches += 1  # if文
        if has_less_than:
            estimated_branches += 1  # while文

        print(f"  - 推定される分岐数: {estimated_branches}")

        # 循環複雑度の再計算
        loop_indicators = 0
        for node in func_obj.cfg.nodes:
            if hasattr(node, 'statements') and node.statements:
                for stmt in node.statements:
                    stmt_str = str(stmt)
                    if 'range(' in stmt_str or 'iterator' in stmt_str.lower():
                        loop_indicators += 1

        cyclomatic_complexity = estimated_branches + (1 if loop_indicators > 0 else 0) + 1
        print(f"  - 修正された循環複雑度: {cyclomatic_complexity}")
        print(f"    (条件分岐: {estimated_branches}, ループ: {1 if loop_indicators > 0 else 0})")

        return condition_count, compare_statements, control_structures

if __name__ == "__main__":
    debug_whiletest()

    # 修正された条件分岐検出を追加実行
    print("\n" + "="*80)
    print("修正された条件分岐検出を実行...")
    print("="*80)
    fix_condition_detection()
