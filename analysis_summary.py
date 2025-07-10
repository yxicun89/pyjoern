#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyJoern分析結果の要約とまとめ
whiletest.pyの静的解析結果
"""

def print_analysis_summary():
    """分析結果の要約を表示"""

    print("="*80)
    print("PyJoern分析結果の要約")
    print("="*80)

    print("\n1. 検出された制御構造:")
    print("   - if文: x > 0 ✓")
    print("   - while文: x < 0 ✓")
    print("   - for文: for i in range(x) ✓")

    print("\n2. 条件分岐の詳細:")
    conditions = [
        "x < 0",  # while文の条件
        "x > 0",  # if文の条件
    ]

    for i, condition in enumerate(conditions, 1):
        print(f"   {i}. {condition}")

    print("\n3. 関数呼び出し:")
    function_calls = [
        "print(i)",      # ループ内での出力
        "range(x)",      # for文での範囲生成
    ]

    for i, call in enumerate(function_calls, 1):
        print(f"   {i}. {call}")

    print("\n4. 代入操作:")
    assignments = [
        "i = tmp0.__next__()",  # イテレータからの値取得
        "tmp1 = range(x)",      # range関数の結果
    ]

    for i, assignment in enumerate(assignments, 1):
        print(f"   {i}. {assignment}")

    print("\n5. 制御フロー分析:")
    print("   - CFGノード数: 7")
    print("   - CFGエッジ数: 9")
    print("   - エントリーポイント: 1個")
    print("   - エグジットポイント: 1個")
    print("   - 単純パス数: 2個")

    print("\n6. 循環複雑度:")
    print("   - 条件分岐: 2個")
    print("   - ループ: 1個")
    print("   - 循環複雑度: 4")

    print("\n7. 実行パス:")
    execution_paths = [
        "Block:1 -> Block:6 -> Block:8 (if文でreturn)",
        "Block:1 -> Block:3 -> Block:3 -> Block:8 (for文を実行してreturn)"
    ]

    for i, path in enumerate(execution_paths, 1):
        print(f"   パス {i}: {path}")

    print("\n8. 検出されたコード特徴:")
    features = {
        "条件分岐": 2,
        "ループ": 1,
        "関数呼び出し": 2,
        "代入": 2,
        "return文": 1
    }

    for feature, count in features.items():
        print(f"   - {feature}: {count}個")

    print("\n9. PyJoernの利点:")
    advantages = [
        "Pythonコードの詳細な制御フロー分析",
        "Compare文の正確な検出",
        "ループ構造の識別",
        "関数呼び出しとの区別",
        "CFGとASTの両方の分析",
        "NetworkXとの統合によるパス分析"
    ]

    for advantage in advantages:
        print(f"   - {advantage}")

def calculate_complexity_metrics():
    """複雑度メトリクスの計算"""

    print("\n" + "="*80)
    print("複雑度メトリクス")
    print("="*80)

    # 基本メトリクス
    conditions = 2      # if文とwhile文
    loops = 1          # for文
    functions = 1      # example関数

    # 循環複雑度（McCabe複雑度）
    cyclomatic_complexity = conditions + loops + 1

    # 推定実行パス数
    estimated_paths = 2 ** conditions  # 各条件分岐で2つの経路

    print(f"1. 循環複雑度 (McCabe): {cyclomatic_complexity}")
    print(f"   - 条件分岐: {conditions}")
    print(f"   - ループ: {loops}")
    print(f"   - 基本値: 1")

    print(f"\n2. 推定実行パス数: {estimated_paths}")
    print(f"   - 条件分岐による分岐: 2^{conditions} = {2**conditions}")

    print(f"\n3. 関数複雑度:")
    print(f"   - 関数数: {functions}")
    print(f"   - 平均複雑度: {cyclomatic_complexity / functions}")

    print(f"\n4. 制御構造密度:")
    cfg_nodes = 7
    control_structures = conditions + loops
    density = control_structures / cfg_nodes
    print(f"   - 制御構造数: {control_structures}")
    print(f"   - CFGノード数: {cfg_nodes}")
    print(f"   - 密度: {density:.2f}")

if __name__ == "__main__":
    print_analysis_summary()
    calculate_complexity_metrics()
