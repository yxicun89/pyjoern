#!/usr/bin/env python3
"""
CFG構造の詳細デバッグ用スクリプト
PyJoernがどのようにCFGを構築しているかを詳しく調査
"""

from pyjoern import parse_source, fast_cfgs_from_source
import json

def analyze_cfg_detailed(source_file):
    """CFGの詳細な構造解析"""
    print(f"=" * 80)
    print(f"CFG詳細解析: {source_file}")
    print(f"=" * 80)

    # parse_sourceで解析
    print("\n--- parse_source による解析 ---")
    try:
        functions = parse_source(source_file)

        for func_name, func_obj in functions.items():
            print(f"\n🔍 関数: {func_name}")
            print(f"関数オブジェクト型: {type(func_obj)}")

            # CFGの詳細解析
            if hasattr(func_obj, 'cfg') and func_obj.cfg:
                cfg = func_obj.cfg
                print(f"\n--- CFG情報 ---")
                print(f"ノード数: {len(cfg.nodes())}")
                print(f"エッジ数: {len(cfg.edges())}")
                print(f"CFG型: {type(cfg)}")

                print(f"\n--- ノード詳細解析 ---")
                for i, node in enumerate(cfg.nodes()):
                    print(f"\n[ノード {i}]")
                    print(f"  オブジェクト: {repr(node)}")
                    print(f"  型: {type(node)}")
                    print(f"  文字列表現: {str(node)}")

                    # ノードの属性を詳細表示
                    if hasattr(node, '__dict__'):
                        print(f"  属性:")
                        for attr, value in node.__dict__.items():
                            if not attr.startswith('_'):
                                print(f"    {attr}: {value}")

                    # よく使われる属性の特別チェック
                    special_attrs = ['addr', 'statements', 'is_entrypoint', 'is_exitpoint',
                                   'is_merged_node', 'code', 'line_number', 'ast_node']
                    for attr in special_attrs:
                        if hasattr(node, attr):
                            value = getattr(node, attr)
                            print(f"    {attr}: {value}")

                print(f"\n--- エッジ詳細解析 ---")
                for i, edge in enumerate(cfg.edges()):
                    print(f"[エッジ {i}] {edge[0]} -> {edge[1]}")

                    # エッジデータがある場合
                    edge_data = cfg.get_edge_data(edge[0], edge[1])
                    if edge_data:
                        print(f"  エッジデータ: {edge_data}")

            else:
                print("❌ CFGが見つかりません")

    except Exception as e:
        print(f"❌ parse_source でエラー: {e}")
        import traceback
        traceback.print_exc()

    # fast_cfgs_from_sourceで解析
    print(f"\n{'='*50}")
    print("--- fast_cfgs_from_source による解析 ---")
    try:
        cfgs = fast_cfgs_from_source(source_file)

        for cfg_name, cfg in cfgs.items():
            print(f"\n🚀 CFG: {cfg_name}")
            print(f"ノード数: {len(cfg.nodes())}")
            print(f"エッジ数: {len(cfg.edges())}")

            print(f"\n--- ノード詳細 ---")
            for i, node in enumerate(cfg.nodes()):
                print(f"[ノード {i}] {repr(node)} (型: {type(node)})")

                # ノード属性の詳細
                if hasattr(node, '__dict__'):
                    for attr, value in node.__dict__.items():
                        if not attr.startswith('_'):
                            print(f"  {attr}: {value}")

            print(f"\n--- エッジ詳細 ---")
            for edge in cfg.edges():
                print(f"{edge[0]} -> {edge[1]}")
                edge_data = cfg.get_edge_data(edge[0], edge[1])
                if edge_data:
                    print(f"  データ: {edge_data}")

    except Exception as e:
        print(f"❌ fast_cfgs_from_source でエラー: {e}")
        import traceback
        traceback.print_exc()

def analyze_whiletest_specific():
    """whiletest.pyの特定の問題を調査"""
    print(f"\n{'='*60}")
    print("whiletest.py の問題特定調査")
    print(f"{'='*60}")

    # whiletest.pyの内容を表示
    try:
        with open('whiletest.py', 'r', encoding='utf-8') as f:
            content = f.read()

        print("\n--- whiletest.py の内容 ---")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:2d}: {line}")

        print(f"\n--- 期待されるCFGの流れ ---")
        print("1. function_start (example関数の開始)")
        print("2. 条件判定: if x > 0")
        print("3a. True分岐: for i in range(x)")
        print("3b. False分岐: while x < 0")
        print("4. 合流点: if x > 10")
        print("5. function_end")

    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")

if __name__ == "__main__":
    # whiletest.pyの詳細解析
    analyze_whiletest_specific()
    analyze_cfg_detailed('whiletest.py')
