"""
設定可能なグラフ視覚化プログラム
config.jsonで視覚化設定をカスタマイズ可能
"""

import json
import os
from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# 日本語フォント設定（文字化け対策）
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# デフォルト設定
DEFAULT_CONFIG = {
    "source_files": ["whiletest.py"],
    "output_directory": "graph_outputs",
    "visualization": {
        "figure_size": [12, 8],
        "node_size": 2000,
        "font_size": 10,
        "dpi": 300,
        "save_graphs": True,
        "show_graphs": True
    },
    "colors": {
        "cfg": {
            "entry": "#90EE90",
            "exit": "#FFB6C1", 
            "merge": "#FFD700",
            "regular": "#87CEEB"
        },
        "ast": {
            "function": "#98FB98",
            "call": "#DDA0DD",
            "assign": "#F0E68C",
            "default": "#B0C4DE"
        },
        "ddg": {
            "default": "#FFA07A"
        }
    },
    "layouts": {
        "cfg": "hierarchical",  # hierarchical, spring, circular
        "ast": "spring",
        "ddg": "spring"
    }
}

def load_config(config_file="config.json"):
    """設定ファイルを読み込み"""
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            # デフォルト設定とマージ
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    else:
        # デフォルト設定ファイルを作成
        save_config(DEFAULT_CONFIG, config_file)
        print(f"デフォルト設定ファイルを作成しました: {config_file}")
        return DEFAULT_CONFIG

def save_config(config, config_file="config.json"):
    """設定ファイルを保存"""
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_layout(graph, layout_type):
    """レイアウトを取得"""
    if layout_type == "hierarchical":
        try:
            return nx.nx_agraph.graphviz_layout(graph, prog='dot')
        except:
            return nx.spring_layout(graph, k=2, iterations=50)
    elif layout_type == "circular":
        return nx.circular_layout(graph)
    elif layout_type == "spring":
        return nx.spring_layout(graph, k=1.5, iterations=50)
    else:
        return nx.spring_layout(graph)

def create_enhanced_labels(graph, graph_type="CFG"):
    """拡張ラベル作成"""
    labels = {}
    
    for node in graph.nodes():
        if graph_type == "CFG":
            if hasattr(node, 'addr'):
                label = f"Block {node.addr}"
            else:
                label = str(node)
                
            # ステートメント情報
            if hasattr(node, 'statements') and node.statements:
                stmt_count = len(node.statements)
                label += f"\n[{stmt_count} statements]"
                
                # 最初のステートメントを短縮表示
                first_stmt = str(node.statements[0])
                if len(first_stmt) > 25:
                    first_stmt = first_stmt[:22] + "..."
                label += f"\n{first_stmt}"
                
            # 特殊ノードの表示
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                label = ">> ENTRY\n" + label
            if hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                label = label + "\n<< EXIT"
                
        elif graph_type == "AST":
            node_type = type(node).__name__
            label = f"{node_type}\n{str(node)[:20]}..."
            
        elif graph_type == "DDG":
            label = str(node)[:25]
            if len(str(node)) > 25:
                label += "..."
                
        labels[node] = label
    
    return labels

def visualize_with_config(graph, title, graph_type, config):
    """設定に基づいてグラフを視覚化"""
    viz_config = config["visualization"]
    color_config = config["colors"][graph_type.lower()]
    layout_type = config["layouts"][graph_type.lower()]
    
    plt.figure(figsize=viz_config["figure_size"])
    
    # レイアウト計算
    pos = get_layout(graph, layout_type)
    
    # ノードの色を決定
    node_colors = []
    for node in graph.nodes():
        if graph_type == "CFG":
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                node_colors.append(color_config["entry"])
            elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                node_colors.append(color_config["exit"])
            elif hasattr(node, 'is_merged_node') and node.is_merged_node:
                node_colors.append(color_config["merge"])
            else:
                node_colors.append(color_config["regular"])
        elif graph_type == "AST":
            node_type = type(node).__name__.lower()
            if 'function' in node_type:
                node_colors.append(color_config["function"])
            elif 'call' in node_type:
                node_colors.append(color_config["call"])
            elif 'assign' in node_type:
                node_colors.append(color_config["assign"])
            else:
                node_colors.append(color_config["default"])
        else:  # DDG
            node_colors.append(color_config["default"])
    
    # グラフ描画
    nx.draw_networkx_edges(graph, pos, 
                          edge_color='gray', 
                          arrows=True, 
                          arrowsize=20, 
                          arrowstyle='->')
    
    nx.draw_networkx_nodes(graph, pos, 
                          node_color=node_colors,
                          node_size=viz_config["node_size"],
                          alpha=0.8)
    
    # ラベル描画
    labels = create_enhanced_labels(graph, graph_type)
    nx.draw_networkx_labels(graph, pos, labels, 
                           font_size=viz_config["font_size"], 
                           font_weight='bold')
    
    plt.title(f"{title}\n({graph_type}: {len(graph.nodes())} nodes, {len(graph.edges())} edges)", 
              fontsize=14, fontweight='bold')
    
    # 凡例追加（CFGの場合）
    if graph_type == "CFG":
        legend_elements = [
            mpatches.Patch(color=color_config["entry"], label='Entry Point'),
            mpatches.Patch(color=color_config["exit"], label='Exit Point'),
            mpatches.Patch(color=color_config["merge"], label='Merge Node'),
            mpatches.Patch(color=color_config["regular"], label='Regular Node')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
    
    plt.axis('off')
    plt.tight_layout()
    
    # 保存
    if viz_config["save_graphs"]:
        output_dir = config["output_directory"]
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title.replace(' ', '_')}.png"
        filepath = os.path.join(output_dir, filename)
        
        plt.savefig(filepath, dpi=viz_config["dpi"], bbox_inches='tight')
        print(f"💾 グラフを保存: {filepath}")
    
    # 表示
    if viz_config["show_graphs"]:
        plt.show()
    else:
        plt.close()

def main():
    """メイン実行関数"""
    print("🎨 設定可能グラフ視覚化プログラム")
    print("=" * 50)
    
    # 設定読み込み
    config = load_config()
    print(f"📋 設定を読み込みました")
    
    # 出力ディレクトリ作成
    if not os.path.exists(config["output_directory"]):
        os.makedirs(config["output_directory"])
        print(f"📁 出力ディレクトリを作成: {config['output_directory']}")
    
    # 各ソースファイルを処理
    for source_file in config["source_files"]:
        if not os.path.exists(source_file):
            print(f"⚠️ ファイルが見つかりません: {source_file}")
            continue
            
        print(f"\n🔍 解析中: {source_file}")
        
        try:
            # parse_sourceで解析
            functions = parse_source(source_file)
            
            for func_name, func_obj in functions.items():
                print(f"  📊 関数 '{func_name}' のグラフを生成...")
                
                # CFG
                if hasattr(func_obj, 'cfg') and func_obj.cfg and len(func_obj.cfg.nodes()) > 0:
                    visualize_with_config(
                        func_obj.cfg, 
                        f"CFG - {func_name} ({source_file})", 
                        "CFG", 
                        config
                    )
                
                # AST
                if hasattr(func_obj, 'ast') and func_obj.ast and len(func_obj.ast.nodes()) > 0:
                    visualize_with_config(
                        func_obj.ast, 
                        f"AST - {func_name} ({source_file})", 
                        "AST", 
                        config
                    )
                
                # DDG
                if hasattr(func_obj, 'ddg') and func_obj.ddg and len(func_obj.ddg.nodes()) > 0:
                    visualize_with_config(
                        func_obj.ddg, 
                        f"DDG - {func_name} ({source_file})", 
                        "DDG", 
                        config
                    )
            
            # 高速CFG解析
            print(f"  🚀 高速CFG解析...")
            cfgs = fast_cfgs_from_source(source_file)
            for cfg_name, cfg in cfgs.items():
                if len(cfg.nodes()) > 0:
                    visualize_with_config(
                        cfg, 
                        f"Fast CFG - {cfg_name} ({source_file})", 
                        "CFG", 
                        config
                    )
                    
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
    
    print(f"\n✅ 処理完了！")
    if config["visualization"]["save_graphs"]:
        print(f"📁 出力先: {config['output_directory']}")

if __name__ == "__main__":
    main()
