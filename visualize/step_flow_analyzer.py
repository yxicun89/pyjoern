"""
ステップバイステップ グラフ視覚化プログラム
初心者でも理解できるようにプログラムの実行フローを段階的に表示
"""

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os
from datetime import datetime

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class FlowVisualizer:
    def __init__(self):
        self.output_dir = "flow_analysis_results"
        self.ensure_output_dir()
        
    def ensure_output_dir(self):
        """出力ディレクトリを作成"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 結果保存ディレクトリを作成: {self.output_dir}")
    
    def analyze_control_flow(self, source_file):
        """制御フローを段階的に解析・説明"""
        print("=" * 80)
        print("🔍 プログラム制御フロー解析 - ステップバイステップガイド")
        print("=" * 80)
        print(f"📄 解析対象ファイル: {source_file}")
        
        # ステップ1: ソースコードの読み込みと基本情報
        print("\n📋 ステップ1: ソースコードの構造を理解する")
        print("-" * 50)
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
            print(f"✅ ソースコード読み込み完了")
            print(f"   📏 総行数: {len(source_lines)} 行")
            print(f"   📝 最初の数行:")
            for i, line in enumerate(source_lines[:5], 1):
                print(f"     {i:2d}: {line.rstrip()}")
            if len(source_lines) > 5:
                print(f"     ... (残り {len(source_lines) - 5} 行)")
        except Exception as e:
            print(f"❌ ファイル読み込みエラー: {e}")
            return
        
        # ステップ2: PyJoernでの解析
        print(f"\n🔬 ステップ2: PyJoernによる詳細解析")
        print("-" * 50)
        
        try:
            functions = parse_source(source_file)
            print(f"✅ PyJoern解析完了")
            print(f"   🎯 発見された関数数: {len(functions)}")
            
            for func_name in functions.keys():
                print(f"   📋 関数: '{func_name}'")
                
        except Exception as e:
            print(f"❌ PyJoern解析エラー: {e}")
            return
        
        # ステップ3: 各関数の詳細解析
        for func_name, func_obj in functions.items():
            self.analyze_single_function(func_name, func_obj, source_file)
    
    def analyze_single_function(self, func_name, func_obj, source_file):
        """単一関数の詳細解析"""
        print(f"\n🎯 ステップ3: 関数 '{func_name}' の詳細解析")
        print("-" * 50)
        
        # 基本情報
        print(f"📍 関数の位置情報:")
        print(f"   開始行: {func_obj.start_line}")
        print(f"   終了行: {func_obj.end_line}")
        print(f"   行数: {func_obj.end_line - func_obj.start_line + 1}")
        
        # CFG解析
        if hasattr(func_obj, 'cfg') and func_obj.cfg:
            self.analyze_cfg_flow(func_name, func_obj.cfg, source_file)
        
        # 実行フロー図の生成
        self.create_execution_flow_diagram(func_name, func_obj, source_file)
    
    def analyze_cfg_flow(self, func_name, cfg, source_file):
        """CFGの実行フローを詳細解析"""
        print(f"\n📊 CFG (制御フローグラフ) 解析:")
        print(f"   🔢 ノード数: {len(cfg.nodes())} 個")
        print(f"   🔗 エッジ数: {len(cfg.edges())} 個")
        
        # ノードの分類と説明
        entry_nodes = []
        exit_nodes = []
        merge_nodes = []
        regular_nodes = []
        
        print(f"\n📋 ノードの詳細分析:")
        for i, node in enumerate(cfg.nodes(), 1):
            node_type = "通常ノード"
            
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                entry_nodes.append(node)
                node_type = "🚀 エントリーポイント (プログラム開始)"
            elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                exit_nodes.append(node)
                node_type = "🏁 エグジットポイント (プログラム終了)"
            elif hasattr(node, 'is_merged_node') and node.is_merged_node:
                merge_nodes.append(node)
                node_type = "🔄 マージノード (複数の流れが合流)"
            else:
                regular_nodes.append(node)
            
            addr = getattr(node, 'addr', 'N/A')
            stmt_count = len(node.statements) if hasattr(node, 'statements') and node.statements else 0
            
            print(f"   ノード{i} (Block {addr}): {node_type}")
            print(f"     💬 含まれる文の数: {stmt_count}")
            
            # ステートメントの詳細
            if hasattr(node, 'statements') and node.statements:
                print(f"     📝 実行される処理:")
                for j, stmt in enumerate(node.statements[:3], 1):  # 最初の3つのみ
                    stmt_str = str(stmt)
                    if len(stmt_str) > 50:
                        stmt_str = stmt_str[:47] + "..."
                    print(f"       {j}. {stmt_str}")
                if len(node.statements) > 3:
                    print(f"       ... (他 {len(node.statements) - 3} 個の処理)")
        
        # フロー分析結果の要約
        print(f"\n📈 実行フロー要約:")
        print(f"   🚀 開始ポイント: {len(entry_nodes)} 個")
        print(f"   🏁 終了ポイント: {len(exit_nodes)} 個") 
        print(f"   🔄 分岐合流点: {len(merge_nodes)} 個")
        print(f"   📋 処理ブロック: {len(regular_nodes)} 個")
        
        # 実行パスの分析
        self.analyze_execution_paths(cfg, entry_nodes, exit_nodes)
    
    def analyze_execution_paths(self, cfg, entry_nodes, exit_nodes):
        """実行可能なパスを分析"""
        print(f"\n🛣️ 実行パス分析:")
        
        if not entry_nodes or not exit_nodes:
            print("   ⚠️ エントリーまたはエグジットノードが見つかりません")
            return
        
        path_count = 0
        for entry in entry_nodes:
            for exit in exit_nodes:
                if nx.has_path(cfg, entry, exit):
                    path_count += 1
                    try:
                        path = nx.shortest_path(cfg, entry, exit)
                        print(f"   パス{path_count}: {len(path)} ステップ")
                        print(f"     🚀 開始 → ", end="")
                        
                        for i, node in enumerate(path):
                            addr = getattr(node, 'addr', 'N/A')
                            if i < len(path) - 1:
                                print(f"Block{addr} → ", end="")
                            else:
                                print(f"Block{addr} 🏁 終了")
                                
                    except Exception as e:
                        print(f"     ❌ パス計算エラー: {e}")
        
        if path_count == 0:
            print("   ⚠️ 実行可能なパスが見つかりません")
        else:
            print(f"   📊 総実行パス数: {path_count} 通り")
    
    def create_execution_flow_diagram(self, func_name, func_obj, source_file):
        """実行フロー図を作成"""
        print(f"\n🎨 実行フロー図を生成中...")
        
        cfg = func_obj.cfg
        if not cfg or len(cfg.nodes()) == 0:
            print("   ❌ CFGデータが利用できません")
            return
        
        # 図のサイズを動的に調整
        node_count = len(cfg.nodes())
        fig_width = max(14, node_count * 2)
        fig_height = max(10, node_count * 1.5)
        
        plt.figure(figsize=(fig_width, fig_height))
        
        # レイアウト計算（階層的レイアウトを優先）
        try:
            pos = nx.nx_agraph.graphviz_layout(cfg, prog='dot')
        except:
            pos = nx.spring_layout(cfg, k=3, iterations=100)
        
        # ノードの色とラベル作成
        node_colors = []
        labels = {}
        node_types = {}
        
        for node in cfg.nodes():
            addr = getattr(node, 'addr', 'N/A')
            
            # ノードタイプの判定と色設定
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                node_colors.append('#90EE90')  # 明るい緑
                node_types[node] = "START"
                labels[node] = f">> START\nBlock {addr}"
            elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                node_colors.append('#FFB6C1')  # 明るいピンク
                node_types[node] = "END"
                labels[node] = f"<< END\nBlock {addr}"
            elif hasattr(node, 'is_merged_node') and node.is_merged_node:
                node_colors.append('#FFD700')  # ゴールド
                node_types[node] = "MERGE"
                labels[node] = f"<> MERGE\nBlock {addr}"
            else:
                node_colors.append('#87CEEB')  # スカイブルー
                node_types[node] = "PROCESS"
                labels[node] = f"[] PROCESS\nBlock {addr}"
            
            # ステートメント情報を追加
            if hasattr(node, 'statements') and node.statements:
                stmt_count = len(node.statements)
                labels[node] += f"\n({stmt_count} stmts)"
                
                # 主要な処理を表示
                if node.statements:
                    first_stmt = str(node.statements[0])
                    if len(first_stmt) > 25:
                        first_stmt = first_stmt[:22] + "..."
                    labels[node] += f"\n{first_stmt}"
        
        # エッジの描画（フロー方向を強調）
        nx.draw_networkx_edges(cfg, pos, 
                              edge_color='#666666', 
                              arrows=True, 
                              arrowsize=25, 
                              arrowstyle='-|>',
                              width=2,
                              alpha=0.8)
        
        # ノードの描画
        nx.draw_networkx_nodes(cfg, pos, 
                              node_color=node_colors,
                              node_size=4000,
                              alpha=0.9,
                              edgecolors='black',
                              linewidths=2)
        
        # ラベルの描画
        nx.draw_networkx_labels(cfg, pos, labels, 
                               font_size=10, 
                               font_weight='bold',
                               font_family='monospace')
        
        # タイトルとメタ情報
        plt.title(f"Execution Flow: {func_name} (File: {source_file})\n"
                 f"Nodes: {len(cfg.nodes())}, Edges: {len(cfg.edges())}, "
                 f"Complexity: {'Low' if len(cfg.nodes()) <= 5 else 'Medium' if len(cfg.nodes()) <= 10 else 'High'}", 
                 fontsize=16, fontweight='bold', pad=30)
        
        # 詳細な凡例
        legend_elements = [
            mpatches.Patch(color='#90EE90', label='START (Program Start)'),
            mpatches.Patch(color='#FFB6C1', label='END (Program End)'),
            mpatches.Patch(color='#FFD700', label='MERGE (Branch Merge)'),
            mpatches.Patch(color='#87CEEB', label='PROCESS (Normal Block)')
        ]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=12,
                  title="Node Type Description", title_fontsize=14)
        
        # 実行順序の説明を追加
        info_text = ("Reading Guide:\n"
                    "• Arrow direction shows execution flow\n"
                    "• Start from START, end at END\n"
                    "• PROCESS: sequential processing\n"
                    "• MERGE: convergence after branching")
        
        plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, 
                fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))
        
        plt.axis('off')
        plt.tight_layout()
        
        # ファイル保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"execution_flow_{func_name}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        print(f"   ✅ 実行フロー図を保存: {filepath}")
        
        # 統計情報の保存
        self.save_analysis_report(func_name, func_obj, cfg, filepath)
        
        plt.close()
    
    def save_analysis_report(self, func_name, func_obj, cfg, image_path):
        """解析レポートをテキストファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"analysis_report_{func_name}_{timestamp}.txt"
        report_filepath = os.path.join(self.output_dir, report_filename)
        
        with open(report_filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"プログラム実行フロー解析レポート\n")
            f.write(f"関数名: {func_name}\n")
            f.write(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("📋 基本情報:\n")
            f.write(f"  関数開始行: {func_obj.start_line}\n")
            f.write(f"  関数終了行: {func_obj.end_line}\n")
            f.write(f"  関数行数: {func_obj.end_line - func_obj.start_line + 1}\n\n")
            
            f.write("📊 制御フローグラフ統計:\n")
            f.write(f"  総ノード数: {len(cfg.nodes())}\n")
            f.write(f"  総エッジ数: {len(cfg.edges())}\n")
            
            # ノードタイプ別集計
            entry_count = sum(1 for node in cfg.nodes() if hasattr(node, 'is_entrypoint') and node.is_entrypoint)
            exit_count = sum(1 for node in cfg.nodes() if hasattr(node, 'is_exitpoint') and node.is_exitpoint)
            merge_count = sum(1 for node in cfg.nodes() if hasattr(node, 'is_merged_node') and node.is_merged_node)
            regular_count = len(cfg.nodes()) - entry_count - exit_count - merge_count
            
            f.write(f"  エントリーノード: {entry_count}\n")
            f.write(f"  エグジットノード: {exit_count}\n")
            f.write(f"  マージノード: {merge_count}\n")
            f.write(f"  通常ノード: {regular_count}\n\n")
            
            # 複雑度評価
            complexity = "低"
            if len(cfg.nodes()) > 10:
                complexity = "高"
            elif len(cfg.nodes()) > 5:
                complexity = "中"
            
            f.write(f"🎯 複雑度評価: {complexity}\n")
            f.write(f"  理由: ノード数が{len(cfg.nodes())}個\n\n")
            
            f.write("📈 推奨事項:\n")
            if len(cfg.nodes()) > 15:
                f.write("  - 関数が複雑すぎます。分割を検討してください\n")
            elif len(cfg.nodes()) > 10:
                f.write("  - やや複雑です。コメントを追加することを推奨\n")
            else:
                f.write("  - 適切な複雑度です\n")
            
            f.write(f"\n📸 対応する図: {os.path.basename(image_path)}\n")
        
        print(f"   📄 解析レポートを保存: {report_filepath}")

def main():
    """メイン実行関数"""
    print("🎯 ステップバイステップ グラフ視覚化プログラム")
    print("=" * 60)
    print("このプログラムは、コードの実行フローを分かりやすく視覚化します")
    print("初心者でも理解できるよう、段階的に説明を行います")
    print("=" * 60)
    
    visualizer = FlowVisualizer()
    
    # 解析対象ファイルの選択
    available_files = ["whiletest.py"]
    existing_files = [f for f in available_files if os.path.exists(f)]
    
    if not existing_files:
        print("❌ 解析対象ファイルが見つかりません")
        print(f"以下のファイルのいずれかを配置してください: {available_files}")
        return
    
    print(f"📁 利用可能なファイル:")
    for i, file in enumerate(existing_files, 1):
        print(f"  {i}. {file}")
    
    # ユーザー入力または自動選択
    try:
        choice = input(f"\n解析するファイルを選択してください (1-{len(existing_files)}, Enter=全て): ").strip()
        
        if choice == "":
            # 全ファイルを解析
            for file in existing_files:
                print(f"\n{'='*80}")
                visualizer.analyze_control_flow(file)
        else:
            # 指定ファイルを解析
            index = int(choice) - 1
            if 0 <= index < len(existing_files):
                visualizer.analyze_control_flow(existing_files[index])
            else:
                print("❌ 無効な選択です")
                return
                
    except KeyboardInterrupt:
        print("\n⏹️ プログラムを中断しました")
        return
    except ValueError:
        print("❌ 無効な入力です")
        return
    
    print(f"\n✅ 全ての解析が完了しました！")
    print(f"📁 結果は以下のディレクトリに保存されました:")
    print(f"   {os.path.abspath(visualizer.output_dir)}")
    
    # Windowsパス表示
    windows_path = os.path.abspath(visualizer.output_dir).replace('/mnt/c/', 'C:\\').replace('/', '\\')
    print(f"🪟 Windowsパス: {windows_path}")

if __name__ == "__main__":
    main()
