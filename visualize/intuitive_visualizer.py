"""
直感的グラフ視覚化プログラム
プログラムの流れを人間が理解しやすい形で表現
"""

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch, ConnectionPatch
import os
from datetime import datetime

# 日本語フォント設定（文字化け対策）
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class IntuitiveFlowVisualizer:
    def __init__(self):
        self.output_dir = "intuitive_graphs"
        self.ensure_output_dir()
        
        # 色テーマ定義
        self.colors = {
            'start': '#2ECC71',      # 鮮やかな緑
            'end': '#E74C3C',        # 鮮やかな赤  
            'process': '#3498DB',    # 鮮やかな青
            'decision': '#F39C12',   # オレンジ
            'merge': '#9B59B6',      # 紫
            'loop': '#1ABC9C',       # ターコイズ
            'edge': '#34495E'        # ダークグレー
        }
        
    def ensure_output_dir(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    def analyze_and_visualize(self, source_file):
        """ファイルを解析して直感的な図を生成"""
        print(f"🎨 直感的フロー図生成: {source_file}")
        print("=" * 50)
        
        try:
            functions = parse_source(source_file)
            
            for func_name, func_obj in functions.items():
                print(f"\n📊 関数 '{func_name}' を処理中...")
                
                if hasattr(func_obj, 'cfg') and func_obj.cfg:
                    self.create_flowchart_style_diagram(func_name, func_obj.cfg, source_file)
                    self.create_timeline_diagram(func_name, func_obj.cfg, source_file)
                    self.create_simplified_overview(func_name, func_obj.cfg, source_file)
                else:
                    print(f"   ⚠️ CFGデータが利用できません")
                    
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def create_flowchart_style_diagram(self, func_name, cfg, source_file):
        """フローチャート風の図を作成"""
        print("   🔄 フローチャート図を生成中...")
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # ノード位置の計算（縦方向の流れを重視）
        pos = self.calculate_vertical_layout(cfg)
        
        # ノードの描画
        node_info = {}
        for node in cfg.nodes():
            x, y = pos[node]
            
            # ノードタイプの判定
            node_type, shape, color = self.determine_node_style(node)
            
            # ノード情報の準備
            label, description = self.create_node_content(node, node_type)
            
            # ノードの描画
            if shape == 'rectangle':
                # 処理ブロック（長方形）
                rect = FancyBboxPatch((x-0.4, y-0.2), 0.8, 0.4,
                                    boxstyle="round,pad=0.02",
                                    facecolor=color, edgecolor='black',
                                    linewidth=2, alpha=0.9)
                ax.add_patch(rect)
            elif shape == 'diamond':
                # 判定ブロック（ダイヤモンド風）
                diamond = FancyBboxPatch((x-0.3, y-0.15), 0.6, 0.3,
                                       boxstyle="round,pad=0.02",
                                       facecolor=color, edgecolor='black',
                                       linewidth=2, alpha=0.9)
                ax.add_patch(diamond)
            elif shape == 'oval':
                # 開始/終了（楕円）
                oval = FancyBboxPatch((x-0.3, y-0.15), 0.6, 0.3,
                                    boxstyle="round,pad=0.05",
                                    facecolor=color, edgecolor='black',
                                    linewidth=3, alpha=0.9)
                ax.add_patch(oval)
            
            # ラベルの配置
            ax.text(x, y, label, ha='center', va='center',
                   fontsize=10, fontweight='bold', wrap=True)
            
            # 詳細説明（小さな文字で）
            if description:
                ax.text(x, y-0.35, description, ha='center', va='top',
                       fontsize=8, style='italic', alpha=0.8)
            
            node_info[node] = {'pos': (x, y), 'type': node_type}
        
        # エッジの描画（フローチャート風の矢印）
        self.draw_flowchart_edges(ax, cfg, pos, node_info)
        
        # タイトルと説明
        ax.set_title(f"📋 フローチャート: {func_name}\n"
                    f"プログラムの実行手順を図で表現",
                    fontsize=16, fontweight='bold', pad=20)
        
        # 凡例
        self.add_flowchart_legend(ax)
        
        # 軸の設定
        ax.set_xlim(-1, max(pos[node][0] for node in pos) + 1)
        ax.set_ylim(min(pos[node][1] for node in pos) - 1, 1)
        ax.axis('off')
        
        # 保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flowchart_{func_name}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        
        print(f"     ✅ 保存完了: {filename}")
        plt.close()
    
    def create_timeline_diagram(self, func_name, cfg, source_file):
        """タイムライン形式の実行順序図"""
        print("   ⏱️ タイムライン図を生成中...")
        
        fig, ax = plt.subplots(figsize=(18, 8))
        
        # 実行順序の推定
        execution_order = self.estimate_execution_order(cfg)
        
        if not execution_order:
            print("     ⚠️ 実行順序を推定できませんでした")
            plt.close()
            return
        
        # タイムラインの描画
        y_center = 0.5
        step_width = 2.0
        
        # メインタイムライン（水平線）
        timeline_start = 0
        timeline_end = len(execution_order) * step_width
        ax.plot([timeline_start, timeline_end], [y_center, y_center], 
               'k-', linewidth=3, alpha=0.7)
        
        # 各ステップの描画
        for i, (node, step_info) in enumerate(execution_order):
            x_pos = i * step_width + step_width/2
            
            # ステップマーカー
            marker_color = self.get_step_color(step_info['type'])
            ax.plot(x_pos, y_center, 'o', markersize=15, 
                   color=marker_color, markeredgecolor='black', markeredgewidth=2)
            
            # ステップ番号
            ax.text(x_pos, y_center, str(i+1), ha='center', va='center',
                   fontsize=10, fontweight='bold', color='white')
            
            # ステップ説明（上側）
            step_label = step_info['label']
            ax.text(x_pos, y_center + 0.3, step_label, ha='center', va='bottom',
                   fontsize=10, fontweight='bold', rotation=0)
            
            # 詳細説明（下側）
            detail = step_info.get('detail', '')
            if detail:
                ax.text(x_pos, y_center - 0.3, detail, ha='center', va='top',
                       fontsize=8, style='italic', alpha=0.8)
            
            # 実行時間の推定（仮想的）
            time_estimate = step_info.get('time', f"{i*0.1:.1f}ms")
            ax.text(x_pos, y_center - 0.5, f"⏱️ {time_estimate}", 
                   ha='center', va='top', fontsize=7, alpha=0.6)
        
        # タイトル
        ax.set_title(f"⏱️ 実行タイムライン: {func_name}\n"
                    f"プログラムが実行される順序と時系列",
                    fontsize=16, fontweight='bold', pad=30)
        
        # 説明テキスト
        explanation = ("💡 読み方: 左から右へ時間が進みます。\n"
                      "各番号がプログラムの実行ステップを表します。")
        ax.text(0.02, 0.95, explanation, transform=ax.transAxes,
               fontsize=12, verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))
        
        # 軸の調整
        ax.set_xlim(-0.5, timeline_end + 0.5)
        ax.set_ylim(-0.8, 1.2)
        ax.axis('off')
        
        # 保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"timeline_{func_name}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        
        print(f"     ✅ 保存完了: {filename}")
        plt.close()
    
    def create_simplified_overview(self, func_name, cfg, source_file):
        """超シンプルな概要図"""
        print("   🔍 概要図を生成中...")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 主要な処理ブロックのみ抽出
        important_nodes = self.extract_important_nodes(cfg)
        
        if len(important_nodes) <= 1:
            # シンプルすぎる場合は全ノードを使用
            important_nodes = list(cfg.nodes())
        
        # シンプルレイアウト
        y_positions = [i * -1.5 for i in range(len(important_nodes))]
        x_center = 0
        
        # ノード描画
        for i, node in enumerate(important_nodes):
            y = y_positions[i]
            
            # ノードタイプの判定
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                color = self.colors['start']
                symbol = "🚀"
                text = "プログラム開始"
            elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                color = self.colors['end']
                symbol = "🏁"
                text = "プログラム終了"
            else:
                color = self.colors['process']
                symbol = "⚙️"
                
                # 処理内容の要約
                if hasattr(node, 'statements') and node.statements:
                    stmt_summary = self.summarize_statements(node.statements)
                    text = f"処理: {stmt_summary}"
                else:
                    text = "処理ブロック"
            
            # ボックス描画
            box = FancyBboxPatch((x_center-1, y-0.3), 2, 0.6,
                               boxstyle="round,pad=0.1",
                               facecolor=color, edgecolor='black',
                               linewidth=2, alpha=0.9)
            ax.add_patch(box)
            
            # テキスト
            ax.text(x_center, y, f"{symbol} {text}", ha='center', va='center',
                   fontsize=11, fontweight='bold')
            
            # 矢印（最後以外）
            if i < len(important_nodes) - 1:
                ax.annotate('', xy=(x_center, y_positions[i+1] + 0.3),
                          xytext=(x_center, y - 0.3),
                          arrowprops=dict(arrowstyle='->', lw=3,
                                        color=self.colors['edge']))
        
        # タイトル
        ax.set_title(f"📝 概要: {func_name}\n"
                    f"プログラムの大まかな流れ",
                    fontsize=16, fontweight='bold', pad=20)
        
        # 統計情報
        stats_text = (f"📊 統計情報:\n"
                     f"• 処理ブロック数: {len(cfg.nodes())}\n"
                     f"• 主要処理: {len(important_nodes)}\n"
                     f"• 複雑度: {'簡単' if len(cfg.nodes()) <= 5 else '普通' if len(cfg.nodes()) <= 10 else '複雑'}")
        
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        
        # 軸調整
        ax.set_xlim(-2, 2)
        ax.set_ylim(min(y_positions) - 1, 1)
        ax.axis('off')
        
        # 保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"overview_{func_name}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        
        print(f"     ✅ 保存完了: {filename}")
        plt.close()
    
    def calculate_vertical_layout(self, cfg):
        """縦方向重視のレイアウト計算"""
        try:
            return nx.nx_agraph.graphviz_layout(cfg, prog='dot')
        except:
            # Graphvizが利用できない場合のフォールバック
            pos = {}
            nodes = list(cfg.nodes())
            
            # エントリーノードを上に配置
            entry_nodes = [n for n in nodes if hasattr(n, 'is_entrypoint') and n.is_entrypoint]
            if entry_nodes:
                start_node = entry_nodes[0]
                pos[start_node] = (0, 0)
                remaining_nodes = [n for n in nodes if n != start_node]
            else:
                remaining_nodes = nodes
            
            # 残りのノードを配置
            for i, node in enumerate(remaining_nodes):
                x = (i % 3) - 1  # -1, 0, 1 の繰り返し
                y = -(i // 3 + 1)
                pos[node] = (x, y)
            
            return pos
    
    def determine_node_style(self, node):
        """ノードのスタイルを決定"""
        if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
            return 'start', 'oval', self.colors['start']
        elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
            return 'end', 'oval', self.colors['end']
        elif hasattr(node, 'is_merged_node') and node.is_merged_node:
            return 'merge', 'diamond', self.colors['merge']
        else:
            # ステートメントの内容で判定
            if hasattr(node, 'statements') and node.statements:
                stmt_types = [type(stmt).__name__ for stmt in node.statements]
                if any('Compare' in t or 'If' in t for t in stmt_types):
                    return 'decision', 'diamond', self.colors['decision']
                elif any('Loop' in t or 'While' in t for t in stmt_types):
                    return 'loop', 'rectangle', self.colors['loop']
            
            return 'process', 'rectangle', self.colors['process']
    
    def create_node_content(self, node, node_type):
        """ノードの内容を作成"""
        addr = getattr(node, 'addr', 'N/A')
        
        if node_type == 'start':
            return ">> START", "Program execution start"
        elif node_type == 'end':
            return "<< END", "Program execution end"
        elif node_type == 'merge':
            return "<> MERGE", "Multiple flows converge"
        else:
            # 処理内容の要約
            if hasattr(node, 'statements') and node.statements:
                summary = self.summarize_statements(node.statements)
                return f"[] {summary}", f"Block {addr}"
            else:
                return f"[] Process {addr}", "Processing block"
    
    def summarize_statements(self, statements):
        """ステートメントを要約"""
        if not statements:
            return "Process"
        
        stmt_types = [type(stmt).__name__ for stmt in statements]
        
        # 主要な処理タイプを判定
        if any('Compare' in t for t in stmt_types):
            return "Condition"
        elif any('Assignment' in t for t in stmt_types):
            return "Assignment"
        elif any('Call' in t for t in stmt_types):
            return "Function Call"
        elif any('Return' in t for t in stmt_types):
            return "Return"
        else:
            return f"{len(statements)} ops"
    
    def draw_flowchart_edges(self, ax, cfg, pos, node_info):
        """フローチャート風のエッジを描画"""
        for source, target in cfg.edges():
            x1, y1 = pos[source]
            x2, y2 = pos[target]
            
            # 矢印の描画
            ax.annotate('', xy=(x2, y2 + 0.15), xytext=(x1, y1 - 0.15),
                       arrowprops=dict(arrowstyle='->', lw=2,
                                     color=self.colors['edge']))
    
    def add_flowchart_legend(self, ax):
        """フローチャートの凡例を追加"""
        legend_elements = [
            mpatches.Patch(color=self.colors['start'], label='>> Start'),
            mpatches.Patch(color=self.colors['end'], label='<< End'),
            mpatches.Patch(color=self.colors['process'], label='[] Process'),
            mpatches.Patch(color=self.colors['decision'], label='? Decision'),
            mpatches.Patch(color=self.colors['merge'], label='<> Merge'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=12,
                 title="Symbol Meanings", title_fontsize=14)
    
    def estimate_execution_order(self, cfg):
        """実行順序を推定"""
        try:
            # エントリーノードから開始
            entry_nodes = [n for n in cfg.nodes() if hasattr(n, 'is_entrypoint') and n.is_entrypoint]
            if not entry_nodes:
                return []
            
            start_node = entry_nodes[0]
            
            # トポロジカルソートを試行
            try:
                order = list(nx.topological_sort(cfg))
                # エントリーノードを最初に配置
                if start_node in order:
                    order.remove(start_node)
                order.insert(0, start_node)
            except:
                # 循環がある場合は幅優先探索
                order = list(nx.bfs_tree(cfg, start_node).nodes())
            
            # 実行順序の情報を作成
            execution_order = []
            for i, node in enumerate(order):
                step_info = {
                    'type': self.determine_node_style(node)[0],
                    'label': self.create_node_content(node, self.determine_node_style(node)[0])[0],
                    'detail': self.create_node_content(node, self.determine_node_style(node)[0])[1],
                    'time': f"{i*0.05:.2f}ms"  # 仮想的な実行時間
                }
                execution_order.append((node, step_info))
            
            return execution_order
            
        except Exception as e:
            print(f"     ⚠️ 実行順序推定エラー: {e}")
            return []
    
    def get_step_color(self, step_type):
        """ステップタイプに応じた色を返す"""
        return self.colors.get(step_type, self.colors['process'])
    
    def extract_important_nodes(self, cfg):
        """重要なノードのみを抽出"""
        important = []
        
        for node in cfg.nodes():
            # エントリー・エグジットは必ず含める
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                important.append(node)
            elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                important.append(node)
            # 複数のステートメントがあるノード
            elif hasattr(node, 'statements') and node.statements and len(node.statements) > 1:
                important.append(node)
            # 分岐のあるノード
            elif len(list(cfg.successors(node))) > 1:
                important.append(node)
        
        return important

def main():
    """メイン実行関数"""
    print("🎨 直感的グラフ視覚化プログラム")
    print("=" * 50)
    print("プログラムの流れを人間が理解しやすい形で視覚化します")
    print("3種類の図を生成:")
    print("  1. 📋 フローチャート図 - 標準的なフローチャート形式")
    print("  2. ⏱️ タイムライン図 - 実行順序を時系列で表示")
    print("  3. 🔍 概要図 - 主要な処理のみを簡潔に表示")
    print("=" * 50)
    
    visualizer = IntuitiveFlowVisualizer()
    
    # 利用可能ファイルの確認
    files = ["whiletest.py"]
    existing = [f for f in files if os.path.exists(f)]
    
    if not existing:
        print("❌ 解析対象ファイルが見つかりません")
        return
    
    # 全ファイルを処理
    for file in existing:
        print(f"\n{'='*60}")
        visualizer.analyze_and_visualize(file)
    
    print(f"\n✅ 全ての図を生成完了！")
    print(f"📁 出力先: {os.path.abspath(visualizer.output_dir)}")

if __name__ == "__main__":
    main()
