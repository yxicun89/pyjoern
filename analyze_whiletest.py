#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyjoern import parse_source, fast_cfgs_from_source
import json
import networkx as nx

def analyze_whiletest():
    """whiletest.pyをJoernで解析する"""

    print("="*60)
    print("=== Joern による whiletest.py の解析 ===")
    print("="*60)

    file_path = "whiletest.py"

    try:
        # 1. 完全なパース（AST, CFG, DDGを含む）
        print("\n1. 完全なパース解析:")
        functions = parse_source(file_path)

        if functions:
            print(f"検出された関数: {list(functions.keys())}")

            for func_name, func_obj in functions.items():
                print(f"\n--- 関数: {func_name} ---")
                print(f"開始行: {func_obj.start_line}")
                print(f"終了行: {func_obj.end_line}")

                # CFG（制御フローグラフ）の情報
                if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):
                    print(f"CFG ノード数: {len(func_obj.cfg.nodes)}")
                    print(f"CFG エッジ数: {len(func_obj.cfg.edges)}")

                    # CFGノードの詳細情報
                    print("CFG ノード詳細:")
                    for i, node in enumerate(list(func_obj.cfg.nodes)[:10]):  # 最初の10個
                        print(f"  ノード {i+1}:")
                        print(f"    型: {type(node)}")
                        print(f"    repr: {repr(node)}")

                        # ノードの属性を表示
                        if hasattr(node, '__dict__'):
                            node_dict = node.__dict__
                            # 重要な属性のみ表示
                            important_attrs = ['name', 'code', 'type', 'line_number', 'value']
                            for attr in important_attrs:
                                if attr in node_dict:
                                    print(f"    {attr}: {node_dict[attr]}")

                # DDG（データフローグラフ）の情報
                if func_obj.ddg and isinstance(func_obj.ddg, nx.DiGraph):
                    print(f"DDG ノード数: {len(func_obj.ddg.nodes)}")
                    print(f"DDG エッジ数: {len(func_obj.ddg.edges)}")

                # AST（抽象構文木）の情報
                if func_obj.ast and isinstance(func_obj.ast, nx.DiGraph):
                    print(f"AST ノード数: {len(func_obj.ast.nodes)}")
                    print(f"AST エッジ数: {len(func_obj.ast.edges)}")

        # 2. 高速CFG生成
        print("\n\n2. 高速CFG生成:")
        cfgs = fast_cfgs_from_source(file_path)

        if cfgs:
            print(f"検出されたCFG: {list(cfgs.keys())}")

            for func_name, cfg in cfgs.items():
                if isinstance(cfg, nx.DiGraph):
                    print(f"\n--- 高速CFG: {func_name} ---")
                    print(f"ノード数: {len(cfg.nodes)}")
                    print(f"エッジ数: {len(cfg.edges)}")

                    # CFGの制御フロー分析
                    print("制御フロー分析:")
                    for i, node in enumerate(list(cfg.nodes)[:5]):
                        successors = list(cfg.successors(node))
                        predecessors = list(cfg.predecessors(node))
                        print(f"  ノード {i+1}: {repr(node)}")
                        print(f"    後続ノード: {len(successors)}個")
                        print(f"    前続ノード: {len(predecessors)}個")

        # 3. CPGクエリの例
        print("\n\n3. CPGクエリの例:")
        demonstrate_cpg_queries(functions)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_cpg_queries(functions):
    """CPGクエリの例を示す"""
    print("CPGクエリの例:")

    for func_name, func_obj in functions.items():
        print(f"\n--- {func_name} の分析 ---")

        # CFGを使った分析
        if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):
            # 条件分岐の検出
            condition_nodes = []
            loop_nodes = []

            for node in func_obj.cfg.nodes:
                if hasattr(node, '__dict__'):
                    node_dict = node.__dict__
                    # ノードの種類による分類
                    if 'type' in node_dict:
                        node_type = node_dict['type']
                        if node_type == 'CONTROL_STRUCTURE':
                            if 'code' in node_dict:
                                code = node_dict['code']
                                if 'if' in code:
                                    condition_nodes.append(node)
                                elif 'while' in code or 'for' in code:
                                    loop_nodes.append(node)

            print(f"条件分岐ノード: {len(condition_nodes)}個")
            print(f"ループノード: {len(loop_nodes)}個")

            # 循環複雑度の計算
            try:
                # McCabeの循環複雑度 = エッジ数 - ノード数 + 2
                cyclomatic_complexity = len(func_obj.cfg.edges) - len(func_obj.cfg.nodes) + 2
                print(f"循環複雑度: {cyclomatic_complexity}")
            except:
                print("循環複雑度の計算に失敗しました")

if __name__ == "__main__":
    analyze_whiletest()
