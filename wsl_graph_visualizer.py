"""
WSL環境対応グラフ視覚化プログラム
X11フォワーディングや画像保存に対応
"""

import os
import matplotlib
# WSL環境でのバックエンド設定
if os.environ.get('DISPLAY') is None:
    matplotlib.use('Agg')  # 非インタラクティブバックエンド
else:
    try:
        matplotlib.use('TkAgg')  # X11フォワーディング使用時
    except:
        matplotlib.use('Agg')

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime

def wsl_visualize():
    """WSL環境対応の視覚化"""
    print("🖥️ WSL環境でのグラフ生成を開始...")
    print("whiletest.py のグラフを生成中...")
    
    # 出力ディレクトリ作成
    output_dir = "wsl_graphs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 出力ディレクトリを作成: {output_dir}")
    
    # 解析実行
    functions = parse_source("whiletest.py")
    
    for func_name, func_obj in functions.items():
        print(f"\n🔍 関数 '{func_name}' を処理中...")
        cfg = func_obj.cfg
        
        if cfg and len(cfg.nodes()) > 0:
            plt.figure(figsize=(12, 8))
            
            # レイアウト計算
            pos = nx.spring_layout(cfg, k=2, iterations=50)
            
            # ノードの色とラベル設定
            node_colors = []
            labels = {}
            
            for node in cfg.nodes():
                # ノードタイプによる色分け
                if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                    node_colors.append('#90EE90')  # ライトグリーン
                elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                    node_colors.append('#FFB6C1')  # ライトピンク
                elif hasattr(node, 'is_merged_node') and node.is_merged_node:
                    node_colors.append('#FFD700')  # ゴールド
                else:
                    node_colors.append('#87CEEB')  # スカイブルー
                
                # ラベル作成（詳細情報付き）
                if hasattr(node, 'addr'):
                    label = f"Block {node.addr}"
                else:
                    label = str(node)
                
                # ステートメント情報を追加
                if hasattr(node, 'statements') and node.statements:
                    stmt_count = len(node.statements)
                    label += f"\n[{stmt_count} stmts]"
                    
                    # 最初のステートメントを表示
                    if node.statements:
                        first_stmt = str(node.statements[0])
                        if len(first_stmt) > 20:
                            first_stmt = first_stmt[:17] + "..."
                        label += f"\n{first_stmt}"
                
                # エントリー/エグジットマーカー
                if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                    label = "🚀 ENTRY\n" + label
                if hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                    label = label + "\n🏁 EXIT"
                
                labels[node] = label
            
            # グラフ描画
            nx.draw_networkx_edges(cfg, pos, 
                                  edge_color='gray', 
                                  arrows=True, 
                                  arrowsize=20, 
                                  arrowstyle='->')
            
            nx.draw_networkx_nodes(cfg, pos, 
                                  node_color=node_colors,
                                  node_size=2500,
                                  alpha=0.8,
                                  edgecolors='black',
                                  linewidths=1)
            
            nx.draw_networkx_labels(cfg, pos, labels, 
                                   font_size=9, 
                                   font_weight='bold')
            
            # タイトルと情報
            plt.title(f"Control Flow Graph: {func_name}\n"
                     f"Nodes: {len(cfg.nodes())}, Edges: {len(cfg.edges())}", 
                     fontsize=16, fontweight='bold', pad=20)
            
            # 凡例
            legend_elements = [
                mpatches.Patch(color='#90EE90', label='🚀 Entry Point'),
                mpatches.Patch(color='#FFB6C1', label='🏁 Exit Point'),
                mpatches.Patch(color='#FFD700', label='🔄 Merge Node'),
                mpatches.Patch(color='#87CEEB', label='📋 Regular Node')
            ]
            plt.legend(handles=legend_elements, loc='upper right', fontsize=10)
            
            plt.axis('off')
            plt.tight_layout()
            
            # ファイル保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cfg_{func_name}_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            print(f"💾 CFGグラフを保存: {filepath}")
            
            # X11表示を試行
            if os.environ.get('DISPLAY'):
                try:
                    plt.show()
                    print(f"🖥️ X11でグラフを表示しました")
                except Exception as e:
                    print(f"ℹ️ X11表示に失敗しましたが、ファイルに保存されました")
            else:
                print(f"ℹ️ グラフィカル環境が利用できません（DISPLAYが設定されていません）")
            
            # 統計情報
            print(f"📊 グラフ統計:")
            print(f"   ノード数: {len(cfg.nodes())}")
            print(f"   エッジ数: {len(cfg.edges())}")
            
            # ノードタイプ別統計
            entry_count = sum(1 for node in cfg.nodes() if hasattr(node, 'is_entrypoint') and node.is_entrypoint)
            exit_count = sum(1 for node in cfg.nodes() if hasattr(node, 'is_exitpoint') and node.is_exitpoint)
            merge_count = sum(1 for node in cfg.nodes() if hasattr(node, 'is_merged_node') and node.is_merged_node)
            regular_count = len(cfg.nodes()) - entry_count - exit_count - merge_count
            
            print(f"   🚀 エントリーノード: {entry_count}")
            print(f"   🏁 エグジットノード: {exit_count}")
            print(f"   🔄 マージノード: {merge_count}")
            print(f"   📋 通常ノード: {regular_count}")
            
            plt.close()  # メモリ解放
            
        else:
            print(f"❌ 関数 '{func_name}' のCFGデータが取得できませんでした")
    
    print(f"\n✅ 全ての処理が完了しました！")
    print(f"📁 出力先: {os.path.abspath(output_dir)}")
    
    # Windowsパスに変換して表示
    windows_path = os.path.abspath(output_dir).replace('/mnt/c/', 'C:\\').replace('/', '\\')
    print(f"🪟 Windowsパス: {windows_path}")

def setup_x11_instructions():
    """X11設定の手順を表示"""
    print("\n" + "="*60)
    print("🖥️ WSLでグラフィカル表示を有効にする方法")
    print("="*60)
    print("1. Windows側でXサーバーをインストール:")
    print("   - VcXsrv: https://sourceforge.net/projects/vcxsrv/")
    print("   - Xming: https://sourceforge.net/projects/xming/")
    print()
    print("2. WSLで環境変数を設定:")
    print("   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0")
    print("   または")
    print("   export DISPLAY=:0")
    print()
    print("3. Xサーバーを起動してからプログラムを再実行")
    print("="*60)

if __name__ == "__main__":
    wsl_visualize()
    
    # X11設定の説明
    if not os.environ.get('DISPLAY'):
        setup_x11_instructions()
