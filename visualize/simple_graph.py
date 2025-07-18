"""
簡単グラフ視覚化スクリプト
whiletest.pyのグラフを即座に表示します
"""

import os
from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def simple_visualize():
    """whiletest.pyの簡単な視覚化"""
    print("whiletest.py のグラフを生成中...")
    
    # 解析実行
    functions = parse_source("whiletest.py")
    
    # 最初の関数のCFGを取得
    func_name, func_obj = next(iter(functions.items()))
    cfg = func_obj.cfg
    
    if cfg and len(cfg.nodes()) > 0:
        plt.figure(figsize=(10, 8))
        
        # シンプルなレイアウト
        pos = nx.spring_layout(cfg, k=2, iterations=50)
        
        # ノードの色を設定
        node_colors = []
        labels = {}
        
        for node in cfg.nodes():
            # エントリーポイントは緑、エグジットポイントは赤、その他は青
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                node_colors.append('lightgreen')
            elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                node_colors.append('lightcoral')
            else:
                node_colors.append('lightblue')
            
            # ラベル作成
            if hasattr(node, 'addr'):
                labels[node] = f"Block {node.addr}"
            else:
                labels[node] = str(node)
        
        # グラフ描画
        nx.draw_networkx_edges(cfg, pos, edge_color='gray', arrows=True, arrowsize=20)
        nx.draw_networkx_nodes(cfg, pos, node_color=node_colors, node_size=2000, alpha=0.8)
        nx.draw_networkx_labels(cfg, pos, labels, font_size=10, font_weight='bold')
        
        plt.title(f"Control Flow Graph: {func_name}", fontsize=14, fontweight='bold')
        
        # 凡例
        legend_elements = [
            mpatches.Patch(color='lightgreen', label='Entry Point'),
            mpatches.Patch(color='lightcoral', label='Exit Point'),
            mpatches.Patch(color='lightblue', label='Regular Node')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.axis('off')
        plt.tight_layout()
        
        # WSL環境対応：画像として保存
        os.makedirs("simple_graph", exist_ok=True)
        filename = os.path.join("simple_graph", f"cfg_{func_name}_graph.png")
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📁 CFGグラフを保存しました: {filename}")

        # グラフィカル環境がある場合は表示も試行
        try:
            plt.show()
            print(f"✅ CFGグラフを表示しました: {func_name}")
        except Exception as e:
            print(f"ℹ️ グラフィカル表示はできませんが、画像ファイルに保存されました")
        
        print(f"   ノード数: {len(cfg.nodes())}")
        print(f"   エッジ数: {len(cfg.edges())}")
        
        plt.close()  # メモリリークを防ぐ
    else:
        print("❌ CFGデータが取得できませんでした")

if __name__ == "__main__":
    simple_visualize()
