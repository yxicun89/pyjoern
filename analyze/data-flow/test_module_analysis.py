#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyjoernがモジュール全体をどう解析するかテスト
"""

from pyjoern import parse_source, fast_cfgs_from_source

def test_module_parsing():
    print("🔍 whiletest.py の詳細解析")

    try:
        # 1. 通常のparse_source
        print("--- 1. parse_source による解析 ---")
        functions = parse_source("whiletest.py")

        print(f"検出された関数数: {len(functions)}")

        for func_name, func_obj in functions.items():
            print(f"\n📋 関数: {func_name}")
            print(f"  開始行: {func_obj.start_line}")
            print(f"  終了行: {func_obj.end_line}")

            # 詳細属性を確認
            print(f"  利用可能な属性: {[attr for attr in dir(func_obj) if not attr.startswith('_')]}")

            # ASTノード数を確認
            if hasattr(func_obj, 'ast') and func_obj.ast:
                print(f"  ASTノード数: {len(func_obj.ast.nodes)}")

                # 各ノードの行番号範囲を確認
                line_numbers = []
                for node in func_obj.ast.nodes:
                    if hasattr(node, 'line_number'):
                        line_numbers.append(node.line_number)
                    elif hasattr(node, 'start_line'):
                        line_numbers.append(node.start_line)

                if line_numbers:
                    print(f"  実際のノード行番号範囲: {min(line_numbers)} ~ {max(line_numbers)}")

                # ステートメントで "example(5)" や "__main__" を含むものを探す
                print(f"\n  🔍 トップレベルコード関連ステートメント検索:")
                found_toplevel = False
                for node in func_obj.ast.nodes:
                    if hasattr(node, 'statements') and node.statements:
                        for stmt in node.statements:
                            stmt_str = str(stmt)
                            if any(keyword in stmt_str for keyword in ['__main__', 'example(', 'example(5)']):
                                print(f"    見つかった: {stmt_str}")
                                found_toplevel = True

                if not found_toplevel:
                    print(f"    トップレベルコード関連のステートメントは見つかりませんでした")

        # 2. fast_cfgs_from_source による解析
        print(f"\n--- 2. fast_cfgs_from_source による解析 ---")
        cfgs = fast_cfgs_from_source("whiletest.py")

        print(f"検出されたCFG数: {len(cfgs)}")
        print(f"CFG名一覧: {list(cfgs.keys())}")

        for cfg_name, cfg in cfgs.items():
            print(f"\n📋 CFG: {cfg_name}")
            print(f"  ノード数: {len(cfg.nodes())}")
            print(f"  エッジ数: {len(cfg.edges())}")

            # CFGノードから行番号を取得
            line_numbers = []
            has_toplevel_hints = False

            for node in cfg.nodes():
                if hasattr(node, 'line_number'):
                    line_numbers.append(node.line_number)
                elif hasattr(node, 'start_line'):
                    line_numbers.append(node.start_line)

                # ノードのステートメントをチェック
                if hasattr(node, 'statements') and node.statements:
                    for stmt in node.statements:
                        stmt_str = str(stmt)
                        if any(keyword in stmt_str for keyword in ['__main__', 'example(', '5']):
                            print(f"    🎯 トップレベル関連ステートメント: {stmt_str}")
                            has_toplevel_hints = True

            if line_numbers:
                print(f"  行番号範囲: {min(line_numbers)} ~ {max(line_numbers)}")

            if has_toplevel_hints:
                print(f"    ✅ トップレベルコードの痕跡が見つかりました！")
            else:
                print(f"    ❌ トップレベルコードの痕跡は見つかりませんでした")

        # 追加: pyjoernが他の解析方法を提供しているかチェック
        print(f"\n--- 3. pyjoernモジュールの利用可能な機能 ---")
        import pyjoern
        pyjoern_functions = [attr for attr in dir(pyjoern) if not attr.startswith('_')]
        print(f"  利用可能な関数/クラス: {pyjoern_functions}")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_module_parsing()
