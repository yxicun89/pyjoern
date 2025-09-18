#!/usr/bin/env python3
"""
CFG生成テスト用スクリプト
様々なC言語の構造がCFGで正しく表現されているかテストする
"""

from visualize_module_and_functions import analyze_and_visualize_file
import os

def test_cfg_generation():
    """CFG生成のテスト"""
    test_files = [
        "test.c",                    # 基本的なif-else
        "middle_code.c",             # gotoとループ
        "test_recursion.c",          # 再帰関数
        "test_loops.c",              # 複雑なループ
        "test_conditions.c",         # 複雑な条件分岐
        "test_functions.c",          # 関数呼び出し
        "test_goto_error.c",         # エラーハンドリングとgoto
        "module_test.py",         # モジュールレベルのコード
        "textbook.py",            # 教科書の例
        "test_complex_python.py", # 複雑なPython構造
        "test_algorithms.py",     # アルゴリズムの例
        "test_classes.py" ,        # クラスとオブジェクト指向
        "test_decorators.py",   # デコレータの例
        "test_recursion.py"          # 再帰関数
    ]

    print("="*80)
    print("CFG生成テスト開始")
    print("="*80)

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n{'='*50}")
            print(f"テスト中: {test_file}")
            print(f"{'='*50}")

            try:
                analyze_and_visualize_file(test_file)
                print(f"✅ {test_file} - 成功")
            except Exception as e:
                print(f"❌ {test_file} - エラー: {e}")
        else:
            print(f"⚠️  {test_file} - ファイルが見つかりません")

    print(f"\n{'='*80}")
    print("CFG生成テスト完了")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_cfg_generation()
