#!/usr/bin/env python3
"""
実際のCFG構造を分析して問題を可視化
"""

def analyze_actual_cfg_flow():
    """実際のCFGフローを解析"""
    print("=" * 80)
    print("実際のCFG構造解析")
    print("=" * 80)

    # 実行結果から判明した実際のノード構造
    nodes = {
        0: "9.0: x < 0 (while文の条件)",
        1: "13.0: x > 10 (最後のif文)",
        2: "14.0: print('Done')",
        3: "16.0: print('NotDone')",
        4: "1.1: FUNCTION_END",
        5: "3.0: for文のイテレータチェック",
        6: "1.0: FUNCTION_START + x > 0 ⚠️問題のノード",
        7: "10.2: while文の本体 (print + x+=1)",
        8: "5.2: Even分岐 print(f'Even:{i}')",
        9: "7.2: Odd分岐 print(f'Odd:{i}')",
        10: "3.4: for文初期化 range(x)",
        11: "3.9: for文の各イテレーション (i%2==0判定)"
    }

    # 実際のエッジ関係
    edges = [
        (6, 0, "FALSE分岐: x <= 0"),
        (6, 10, "TRUE分岐: x > 0"),
        (0, 1, "while文終了: x >= 0"),
        (0, 7, "while文継続: x < 0"),
        (7, 0, "while文ループバック"),
        (10, 5, "for文開始"),
        (5, 1, "for文終了"),
        (5, 11, "for文継続"),
        (11, 8, "偶数分岐: i%2 == 0"),
        (11, 9, "奇数分岐: i%2 != 0"),
        (8, 5, "Even後、for文に戻る"),
        (9, 5, "Odd後、for文に戻る"),
        (1, 2, "x > 10: TRUE"),
        (1, 3, "x > 10: FALSE"),
        (2, 4, "Done -> END"),
        (3, 4, "NotDone -> END")
    ]

    print("\n=== 実際のノード構造 ===")
    for node_id, description in nodes.items():
        marker = "⚠️ 問題" if node_id == 6 else ""
        print(f"[{node_id:2d}] {description} {marker}")

    print("\n=== 実際のエッジ構造 ===")
    for src, dst, desc in edges:
        marker = "⚠️ 問題の分岐" if src == 6 else ""
        print(f"[{src:2d}] -> [{dst:2d}] {desc} {marker}")

    print("\n=== 問題の詳細分析 ===")
    print("🔍 問題のノード [6]: FUNCTION_START + x > 0")
    print("   - 本来なら分離されるべき2つの処理が統合されている")
    print("   - FUNCTION_START: 関数の開始点")
    print("   - x > 0: 最初の条件判定")
    print()
    print("🔍 結果として起こる問題:")
    print("   - CFGの視覚化で関数開始点から直接分岐が見える")
    print("   - 論理的な流れが不明確")
    print("   - デバッグ時に混乱を招く")

    print("\n=== 理想的なCFG構造 ===")
    print("本来あるべき構造:")
    print("[START] -> [条件判定: x > 0] -> [TRUE分岐] / [FALSE分岐]")
    print()
    print("実際の構造:")
    print("[START + x > 0] -> [TRUE分岐] / [FALSE分岐]")

    print("\n=== PyJoernの動作推測 ===")
    print("PyJoernは以下の理由で統合している可能性:")
    print("1. 最適化: 単純な条件判定を関数開始と統合")
    print("2. 内部処理: Joernの中間表現の制約")
    print("3. Python特有: def文の処理方法")

    print("\n=== 解決策の検討 ===")
    print("1. 視覚化レベルでの対応:")
    print("   - ノードラベルでFUNCTION_STARTと条件を分離表示")
    print("   - 色分けで区別")
    print("   - 説明テキストを追加")
    print()
    print("2. PyJoern設定の調整:")
    print("   - より詳細なCFG生成オプションがあるか調査")
    print("   - 別のCFG構築方法の検討")

def create_corrected_visualization_labels():
    """修正された視覚化ラベル案"""
    print("\n" + "=" * 80)
    print("修正された視覚化ラベル案")
    print("=" * 80)

    corrected_labels = {
        6: """ENTRY POINT
────────────
Function: example
Initial condition:
  if x > 0""",
        0: """WHILE CONDITION
─────────────
  while x < 0""",
        10: """FOR LOOP START
──────────────
  for i in range(x)""",
        11: """FOR LOOP BODY
─────────────
Check: i % 2 == 0""",
        1: """FINAL CONDITION
───────────────
  if x > 10"""
    }

    print("提案する改良ラベル:")
    for node_id, label in corrected_labels.items():
        print(f"\n[ノード {node_id}]")
        print(label)

if __name__ == "__main__":
    analyze_actual_cfg_flow()
    create_corrected_visualization_labels()
