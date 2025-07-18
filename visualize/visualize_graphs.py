from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os
from datetime import datetime

def create_node_labels(graph, graph_type="CFG"):
    """グラフノードのラベルを作成"""
    labels = {}
    
    for node in graph.nodes():
        if graph_type == "CFG":
            # CFGノードの場合
            if hasattr(node, 'addr'):
                base_label = f"Block {node.addr}"
            else:
                base_label = str(node)
                
            # ステートメント情報を追加
            if hasattr(node, 'statements') and node.statements:
                stmt_count = len(node.statements)
                base_label += f"\n({stmt_count} stmts)"
                
                # 最初のステートメントを表示（短縮版）
                first_stmt = str(node.statements[0])
                if len(first_stmt) > 20:
                    first_stmt = first_stmt[:17] + "..."
                base_label += f"\n{first_stmt}"
                
            # エントリー/エグジットポイントの表示
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                base_label = "ENTRY\n" + base_label
            if hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                base_label = base_label + "\nEXIT"
                
        elif graph_type == "AST":
            # ASTノードの場合
            base_label = str(node)
            if hasattr(node, '__dict__') and node.__dict__:
                # ノードタイプを取得
                node_type = type(node).__name__
                base_label = f"{node_type}\n{str(node)[:15]}..."
                
        elif graph_type == "DDG":
            # DDGノードの場合
            base_label = str(node)
            
        labels[node] = base_label
    
    return labels

def get_node_colors(graph, graph_type="CFG"):
    """グラフタイプに応じたノードの色を決定"""
    colors = []
    
    for node in graph.nodes():
        if graph_type == "CFG":
            # CFGの場合：エントリー/エグジット/通常ノードで色分け
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                colors.append('#90EE90')  # ライトグリーン
            elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                colors.append('#FFB6C1')  # ライトピンク
            elif hasattr(node, 'is_merged_node') and node.is_merged_node:
                colors.append('#FFD700')  # ゴールド
            else:
                colors.append('#87CEEB')  # スカイブルー
                
        elif graph_type == "AST":
            # ASTの場合：ノードタイプで色分け
            node_type = type(node).__name__
            if 'Function' in node_type:
                colors.append('#98FB98')  # ペールグリーン
            elif 'Call' in node_type:
                colors.append('#DDA0DD')  # プラム
            elif 'Assign' in node_type:
                colors.append('#F0E68C')  # カーキ
            else:
                colors.append('#B0C4DE')  # ライトスチールブルー
                
        elif graph_type == "DDG":
            # DDGの場合：統一色
            colors.append('#FFA07A')  # ライトサーモン
            
    return colors

def visualize_graph(graph, title, graph_type="CFG", save_path=None):
    """単一グラフの視覚化"""
    plt.figure(figsize=(12, 8))
    
    # レイアウトの選択
    if len(graph.nodes()) <= 10:
        pos = nx.spring_layout(graph, k=2, iterations=50)
    elif graph_type == "CFG":
        # CFGは階層的レイアウトが適している
        try:
            pos = nx.nx_agraph.graphviz_layout(graph, prog='dot')
        except:
            pos = nx.spring_layout(graph, k=3, iterations=50)
    else:
        pos = nx.spring_layout(graph, k=1.5, iterations=50)
    
    # ノードとエッジの描画
    node_colors = get_node_colors(graph, graph_type)
    labels = create_node_labels(graph, graph_type)
    
    # エッジを先に描画
    nx.draw_networkx_edges(graph, pos, 
                          edge_color='gray', 
                          arrows=True, 
                          arrowsize=20, 
                          arrowstyle='->')
    
    # ノードを描画
    nx.draw_networkx_nodes(graph, pos, 
                          node_color=node_colors,
                          node_size=2000,
                          alpha=0.8)
    
    # ラベルを描画
    nx.draw_networkx_labels(graph, pos, labels, 
                           font_size=8, 
                           font_weight='bold')
    
    plt.title(f"{title}\n({graph_type}: {len(graph.nodes())} nodes, {len(graph.edges())} edges)", 
              fontsize=14, fontweight='bold')
    
    # 凡例を追加
    if graph_type == "CFG":
        legend_elements = [
            mpatches.Patch(color='#90EE90', label='Entry Point'),
            mpatches.Patch(color='#FFB6C1', label='Exit Point'),
            mpatches.Patch(color='#FFD700', label='Merge Node'),
            mpatches.Patch(color='#87CEEB', label='Regular Node')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
    
    plt.axis('off')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"グラフを保存しました: {save_path}")
    
    plt.show()

def compare_graphs_side_by_side(cfg, ast, ddg, func_name, save_dir=None):
    """3つのグラフを横並びで比較表示"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    graphs = [
        (cfg, "CFG (Control Flow Graph)", "CFG"),
        (ast, "AST (Abstract Syntax Tree)", "AST"),
        (ddg, "DDG (Data Dependence Graph)", "DDG")
    ]
    
    for i, (graph, title, graph_type) in enumerate(graphs):
        if graph and len(graph.nodes()) > 0:
            plt.sca(axes[i])
            
            # レイアウト計算
            if len(graph.nodes()) <= 8:
                pos = nx.spring_layout(graph, k=1.5, iterations=50)
            else:
                pos = nx.spring_layout(graph, k=1, iterations=30)
            
            # グラフ描画
            node_colors = get_node_colors(graph, graph_type)
            labels = create_node_labels(graph, graph_type)
            
            nx.draw_networkx_edges(graph, pos, 
                                  edge_color='gray', 
                                  arrows=True, 
                                  arrowsize=15, 
                                  arrowstyle='->')
            
            nx.draw_networkx_nodes(graph, pos, 
                                  node_color=node_colors,
                                  node_size=1500,
                                  alpha=0.8)
            
            nx.draw_networkx_labels(graph, pos, labels, 
                                   font_size=7, 
                                   font_weight='bold')
            
            plt.title(f"{title}\n({len(graph.nodes())} nodes, {len(graph.edges())} edges)", 
                     fontsize=12, fontweight='bold')
            plt.axis('off')
        else:
            axes[i].text(0.5, 0.5, f'{title}\n(No data available)', 
                        ha='center', va='center', fontsize=12,
                        transform=axes[i].transAxes)
            axes[i].axis('off')
    
    plt.suptitle(f"Graph Comparison for Function: {func_name}", 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    if save_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(save_dir, f"graph_comparison_{func_name}_{timestamp}.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"比較グラフを保存しました: {save_path}")
    
    plt.show()

def analyze_and_visualize_file(source_file, output_dir="graph_images"):
    """ソースファイルを解析してすべてのグラフを視覚化"""
    print(f"=" * 80)
    print(f"ファイル '{source_file}' のグラフ解析・視覚化")
    print(f"=" * 80)
    
    # 出力ディレクトリの作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"出力ディレクトリを作成しました: {output_dir}")
    
    # parse_sourceで詳細解析
    print("\n--- Parse Source Analysis ---")
    functions = parse_source(source_file)
    
    for func_name, func_obj in functions.items():
        print(f"\n🔍 関数 '{func_name}' を解析中...")
        
        cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
        ast = func_obj.ast if hasattr(func_obj, 'ast') else None
        ddg = func_obj.ddg if hasattr(func_obj, 'ddg') else None
        
        # 個別グラフの視覚化
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if cfg and len(cfg.nodes()) > 0:
            print("  ✅ CFG グラフを視覚化...")
            save_path = os.path.join(output_dir, f"cfg_{func_name}_{timestamp}.png")
            visualize_graph(cfg, f"CFG for function '{func_name}'", "CFG", save_path)
        
        if ast and len(ast.nodes()) > 0:
            print("  ✅ AST グラフを視覚化...")
            save_path = os.path.join(output_dir, f"ast_{func_name}_{timestamp}.png")
            visualize_graph(ast, f"AST for function '{func_name}'", "AST", save_path)
        
        if ddg and len(ddg.nodes()) > 0:
            print("  ✅ DDG グラフを視覚化...")
            save_path = os.path.join(output_dir, f"ddg_{func_name}_{timestamp}.png")
            visualize_graph(ddg, f"DDG for function '{func_name}'", "DDG", save_path)
        
        # 比較グラフの表示
        print("  ✅ 比較グラフを生成...")
        compare_graphs_side_by_side(cfg, ast, ddg, func_name, output_dir)
    
    # fast_cfgs_from_sourceで高速CFG解析
    print("\n--- Fast CFG Analysis ---")
    cfgs = fast_cfgs_from_source(source_file)
    
    for cfg_name, cfg in cfgs.items():
        if len(cfg.nodes()) > 0:
            print(f"\n🚀 高速CFG '{cfg_name}' を視覚化...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(output_dir, f"fast_cfg_{cfg_name}_{timestamp}.png")
            visualize_graph(cfg, f"Fast CFG: {cfg_name}", "CFG", save_path)

def interactive_menu():
    """対話式メニュー"""
    print("=" * 60)
    print("🎨 PyJoern Graph Visualizer")
    print("=" * 60)
    print("1. whiletest.py を解析")
    print("2. test.c を解析")
    print("3. カスタムファイルを指定")
    print("4. すべてのファイルを解析")
    print("0. 終了")
    
    choice = input("\n選択してください (0-4): ").strip()
    
    if choice == "1":
        analyze_and_visualize_file("whiletest.py")
    elif choice == "2":
        analyze_and_visualize_file("test.c")
    elif choice == "3":
        filename = input("ファイル名を入力してください: ").strip()
        if os.path.exists(filename):
            analyze_and_visualize_file(filename)
        else:
            print(f"❌ ファイル '{filename}' が見つかりません。")
    elif choice == "4":
        files = ["whiletest.py", "test.c"]
        for file in files:
            if os.path.exists(file):
                analyze_and_visualize_file(file)
            else:
                print(f"⚠️ ファイル '{file}' をスキップしました（存在しません）")
    elif choice == "0":
        print("👋 プログラムを終了します。")
        return False
    else:
        print("❌ 無効な選択です。")
    
    return True

if __name__ == "__main__":
    # インタラクティブモードまたは直接実行
    import sys
    
    if len(sys.argv) > 1:
        # コマンドライン引数でファイル指定
        source_file = sys.argv[1]
        if os.path.exists(source_file):
            analyze_and_visualize_file(source_file)
        else:
            print(f"❌ ファイル '{source_file}' が見つかりません。")
    else:
        # インタラクティブメニュー
        while interactive_menu():
            print("\n" + "="*40)
            input("Enterキーを押して続行...")
            print()
