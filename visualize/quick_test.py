"""
簡単テスト用プログラム
visualizeディレクトリのプログラムを簡単にテストできる
"""

from pyjoern import parse_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

def quick_test():
    """クイックテスト実行"""
    print("🧪 クイックテスト開始")
    print("=" * 40)
    
    # テスト対象ファイルの確認
    test_files = ["whiletest.py"]
    available_files = [f for f in test_files if os.path.exists(f)]
    
    if not available_files:
        print("❌ テスト用ファイルが見つかりません")
        print(f"以下のファイルを用意してください: {test_files}")
        return False
    
    print(f"✅ 利用可能なファイル: {available_files}")
    
    # PyJoernの動作確認
    try:
        test_file = available_files[0]
        print(f"\n🔍 {test_file} を解析中...")
        
        functions = parse_source(test_file)
        print(f"✅ PyJoern解析成功: {len(functions)} 個の関数を検出")
        
        for func_name, func_obj in functions.items():
            print(f"  📋 関数: {func_name}")
            
            if hasattr(func_obj, 'cfg') and func_obj.cfg:
                cfg = func_obj.cfg
                print(f"    CFG: {len(cfg.nodes())} ノード, {len(cfg.edges())} エッジ")
                
                # 簡単な図を生成
                plt.figure(figsize=(8, 6))
                pos = nx.spring_layout(cfg, k=1, iterations=50)
                
                # ノード色の設定
                colors = []
                for node in cfg.nodes():
                    if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                        colors.append('lightgreen')
                    elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                        colors.append('lightcoral')
                    else:
                        colors.append('lightblue')
                
                # 描画
                nx.draw(cfg, pos, node_color=colors, node_size=1000, 
                       with_labels=True, labels={node: f"B{getattr(node, 'addr', 'N')}" 
                                               for node in cfg.nodes()},
                       font_size=8, arrows=True)
                
                plt.title(f"Quick Test: {func_name} CFG")
                
                # 保存
                os.makedirs("quick_test", exist_ok=True)
                filename = os.path.join("quick_test", f"quick_test_{func_name}.png")
                plt.savefig(filename, dpi=150, bbox_inches='tight')
                print(f"    💾 テスト図を保存: {filename}")
                plt.close()
            else:
                print("    ⚠️ CFGデータなし")
        
        print("\n✅ クイックテスト完了！")
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        return False

def check_environment():
    """環境確認"""
    print("🔧 環境確認")
    print("-" * 30)
    
    try:
        import pyjoern
        print("✅ pyjoern: OK")
    except ImportError:
        print("❌ pyjoern: 未インストール")
        return False
    
    try:
        import networkx
        print("✅ networkx: OK")
    except ImportError:
        print("❌ networkx: 未インストール")
        return False
    
    try:
        import matplotlib
        print("✅ matplotlib: OK")
    except ImportError:
        print("❌ matplotlib: 未インストール")
        return False
    
    return True

def main():
    """メイン実行"""
    print("🎯 Visualize ディレクトリ - クイックテスト")
    print("=" * 50)
    
    # 環境確認
    if not check_environment():
        print("\n❌ 必要なライブラリがインストールされていません")
        print("以下のコマンドでインストールしてください:")
        print("pip install pyjoern networkx matplotlib")
        return
    
    # クイックテスト実行
    print()
    if quick_test():
        print("\n🎉 テスト成功！")
        print("📋 次のステップ:")
        print("  1. step_flow_analyzer.py - 詳細解析")
        print("  2. intuitive_visualizer.py - 直感的な図")
    else:
        print("\n😞 テスト失敗")
        print("READMEを確認してトラブルシューティングを行ってください")

if __name__ == "__main__":
    main()
