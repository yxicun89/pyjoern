from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os
from datetime import datetime
import ast
import keyword
import re

import ast
import keyword
import re

def analyze_python_construct(stmt_str):
    """Pythonの構文を詳細に解析"""

    # f-string関連の詳細解析
    if 'formatString' in stmt_str or 'formattedValue' in stmt_str:
        # f-stringのパターンを抽出
        fstring_patterns = {
            'f"Even:': '[STR] f"Even:{i}"',
            'f"Odd:': '[STR] f"Odd:{i}"',
            'f"Negative:': '[STR] f"Negative:{x}"',
            'formattedValue.*{i}': '[VAR] {i}',
            'formattedValue.*{x}': '[VAR] {x}',
            'formatString': '[STR] f-string template'
        }

        for pattern, description in fstring_patterns.items():
            if re.search(pattern, stmt_str):
                return description
        return '[STR] f-string'

    # 算術演算子
    arithmetic_ops = {
        'assignmentPlus': '[OP] +=',
        'assignmentMinus': '[OP] -=',
        'assignmentMultiply': '[OP] *=',
        'assignmentDivide': '[OP] /=',
        'modulo': '[OP] %',
        'plus': '[OP] +',
        'minus': '[OP] -',
        'multiply': '[OP] *',
        'divide': '[OP] /',
        'power': '[OP] **'
    }

    # 比較演算子
    comparison_ops = {
        'equals': '[CMP] ==',
        'notEquals': '[CMP] !=',
        'lessThan': '[CMP] <',
        'lessEquals': '[CMP] <=',
        'greaterThan': '[CMP] >',
        'greaterEquals': '[CMP] >=',
        'in': '[CMP] in',
        'notIn': '[CMP] not in'
    }

    # 論理演算子
    logical_ops = {
        'and': '[LOG] and',
        'or': '[LOG] or',
        'not': '[LOG] not'
    }

    # フィールドアクセス
    field_access = {
        '__iter__': '[ITER] get iterator',
        '__next__': '[ITER] next()',
        '__len__': '[FUNC] len()',
        '__str__': '[FUNC] str()',
        '__repr__': '[FUNC] repr()'
    }

    # 組み込み関数
    builtin_functions = {
        'range': '[FUNC] range()',
        'len': '[FUNC] len()',
        'print': '[FUNC] print()',
        'str': '[FUNC] str()',
        'int': '[FUNC] int()',
        'float': '[FUNC] float()',
        'list': '[FUNC] list()',
        'dict': '[FUNC] dict()',
        'enumerate': '[FUNC] enumerate()',
        'zip': '[FUNC] zip()'
    }

    # 制御構造キーワード
    control_keywords = {
        'if': '[CTRL] if',
        'elif': '[CTRL] elif',
        'else': '[CTRL] else',
        'for': '[CTRL] for',
        'while': '[CTRL] while',
        'break': '[CTRL] break',
        'continue': '[CTRL] continue',
        'return': '[CTRL] return',
        'yield': '[CTRL] yield'
    }    # 各カテゴリをチェック
    for ops_dict, category in [
        (arithmetic_ops, 'arithmetic'),
        (comparison_ops, 'comparison'),
        (logical_ops, 'logical'),
        (field_access, 'field'),
        (builtin_functions, 'builtin'),
        (control_keywords, 'control')
    ]:
        for pattern, description in ops_dict.items():
            if pattern in stmt_str:
                return description

    # 変数代入の検出
    if re.search(r'\w+\s*=', stmt_str) and 'UnsupportedStmt' not in stmt_str:
        return '[ASSIGN] Assignment'

    # 関数呼び出しの検出
    if re.search(r'\w+\(.*\)', stmt_str) and 'UnsupportedStmt' not in stmt_str:
        return '[CALL] Function call'

    return None

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

                # 特別処理: FUNCTION_START + 条件判定の場合
                has_function_start = any('FUNCTION_START' in str(stmt) for stmt in node.statements)
                has_condition = any('Compare:' in str(stmt) for stmt in node.statements if 'FUNCTION_START' not in str(stmt))

                if has_function_start and has_condition:
                    # 問題のノードの場合、明確に分離表示
                    base_label = "🚀 FUNCTION ENTRY\n────────────────"
                    for i, stmt in enumerate(node.statements):
                        if 'FUNCTION_START' in str(stmt):
                            base_label += f"\n[START] Function begins"
                        elif 'Compare:' in str(stmt):
                            condition = str(stmt).replace('Compare: ', '')
                            base_label += f"\n[CONDITION] if {condition}"
                        else:
                            stmt_str = str(stmt)
                            if len(stmt_str) > 25:
                                stmt_str = stmt_str[:22] + "..."
                            base_label += f"\n[{i}]: {stmt_str}"
                else:
                    # 通常のノードの場合
                    base_label += f"\n({stmt_count} stmts)"

                    # ステートメントタイプに応じたラベル付け
                    for i, stmt in enumerate(node.statements[:3]):  # 最初の3つのステートメント
                        stmt_str = str(stmt)

                        # ステートメントタイプを詳しく判定してアイコン付与
                        if 'Compare:' in stmt_str:
                            condition = stmt_str.replace('Compare: ', '')
                            base_label += f"\n🔍 CONDITION: {condition}"
                        elif 'Call:' in stmt_str:
                            call = stmt_str.replace('Call: ', '')
                            if len(call) > 20:
                                call = call[:17] + "..."
                            base_label += f"\n📞 CALL: {call}"
                        elif 'Assignment:' in stmt_str:
                            assign = stmt_str.replace('Assignment: ', '')
                            if len(assign) > 20:
                                assign = assign[:17] + "..."
                            base_label += f"\n📝 ASSIGN: {assign}"
                        elif 'FUNCTION_END' in stmt_str:
                            base_label += f"\n🏁 FUNCTION END"
                        elif 'FUNCTION_START' in stmt_str:
                            base_label += f"\n🚀 FUNCTION START"
                        elif 'UnsupportedStmt' in stmt_str:
                            # 新しい解析関数を使用
                            analyzed = analyze_python_construct(stmt_str)
                            if analyzed:
                                base_label += f"\n{analyzed}"
                            else:
                                # 従来の解析をフォールバック
                                if 'iteratorNonEmptyOrException' in stmt_str:
                                    base_label += f"\n[LOOP] FOR LOOP CONDITION"
                                elif 'range(' in stmt_str:
                                    base_label += f"\n[FUNC] range(x)"
                                else:
                                    base_label += f"\n[STMT] {stmt_str[:20]}..."
                                base_label += f"\n🔄 FOR LOOP CONDITION"
                            elif 'formatString' in stmt_str:
                                # f-string のフォーマット部分
                                if 'f"Even:' in stmt_str:
                                    base_label += f"\n📝 f\"Even:{{i}}\""
                                elif 'f"Odd:' in stmt_str:
                                    base_label += f"\n📝 f\"Odd:{{i}}\""
                                elif 'f"Negative:' in stmt_str:
                                    base_label += f"\n📝 f\"Negative:{{x}}\""
                                else:
                                    base_label += f"\n📝 f-string format"
                            elif 'formattedValue' in stmt_str:
                                # f-string の変数部分
                                if '{i}' in stmt_str:
                                    base_label += f"\n� variable: i"
                                elif '{x}' in stmt_str:
                                    base_label += f"\n🔢 variable: x"
                                else:
                                    base_label += f"\n🔢 f-string value"
                            elif 'assignmentPlus' in stmt_str:
                                base_label += f"\n➕ x += 1"
                            elif 'modulo' in stmt_str:
                                base_label += f"\n🔢 MODULO: i % 2"
                            elif 'fieldAccess' in stmt_str:
                                if '__next__' in stmt_str:
                                    base_label += f"\n🔄 iterator.next()"
                                elif '__iter__' in stmt_str:
                                    base_label += f"\n🔄 get iterator"
                                else:
                                    base_label += f"\n🔗 field access"
                            elif 'range(' in stmt_str:
                                base_label += f"\n🔢 range(x)"
                            else:
                                base_label += f"\n⚙️ {stmt_str[:20]}..."
                        # 条件判定の詳細表示
                        elif 'x > 0' in stmt_str:
                            base_label += f"\n🔍 IF: x > 0"
                        elif 'x < 0' in stmt_str:
                            base_label += f"\n🔄 WHILE: x < 0"
                        elif 'x > 10' in stmt_str:
                            base_label += f"\n🔍 IF: x > 10"
                        elif 'i % 2 == 0' in stmt_str or 'i%2 == 0' in stmt_str:
                            base_label += f"\n🔍 IF: i % 2 == 0 (Even/Odd)"
                        elif 'print(' in stmt_str:
                            # print文の詳細表示
                            if 'Done' in stmt_str:
                                base_label += f"\n📢 print(\"Done\")"
                            elif 'NotDone' in stmt_str:
                                base_label += f"\n📢 print(\"Not Done\")"
                            elif 'Even' in stmt_str:
                                base_label += f"\n📢 print(f\"Even:{{i}}\")"
                            elif 'Odd' in stmt_str:
                                base_label += f"\n📢 print(f\"Odd:{{i}}\")"
                            elif 'Negative' in stmt_str:
                                base_label += f"\n📢 print(f\"Negative:{{x}}\")"
                            else:
                                base_label += f"\n📢 print(...)"
                        else:
                            if len(stmt_str) > 25:
                                stmt_str = stmt_str[:22] + "..."
                            base_label += f"\n[{i}]: {stmt_str}"

                    if len(node.statements) > 3:
                        base_label += f"\n... ({len(node.statements)-3} more)"

            # エントリー/エグジットポイントの表示
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                if not ('FUNCTION ENTRY' in base_label):
                    base_label = "🚀 ENTRY\n" + base_label
            if hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                base_label = base_label + "\n🏁 EXIT"

            # ノードの行番号情報があれば追加
            if hasattr(node, 'line_number'):
                base_label += f"\nLine: {node.line_number}"

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

def get_edge_colors_and_styles(graph, graph_type="CFG"):
    """エッジの色とスタイルを決定"""
    edge_colors = []
    edge_styles = []

    if graph_type != "CFG":
        return ['#333333'] * len(graph.edges()), ['-'] * len(graph.edges())

    for edge in graph.edges():
        source, target = edge

        # ループバックエッジの検出
        if hasattr(source, 'addr') and hasattr(target, 'addr'):
            if source.addr > target.addr:  # 後ろから前へのエッジはループバック
                edge_colors.append('#FF6B6B')  # 赤色でループを強調
                edge_styles.append('--')  # 破線
                continue

        # 条件分岐エッジ
        if hasattr(source, 'statements') and source.statements:
            source_stmts = [str(stmt) for stmt in source.statements]
            has_condition = any(
                'x > 0' in stmt or 'x < 0' in stmt or 'x > 10' in stmt or
                'i % 2 == 0' in stmt or 'Compare:' in stmt
                for stmt in source_stmts
            )

            if has_condition:
                edge_colors.append('#4169E1')  # 青色で条件分岐を強調
                edge_styles.append('-')
                continue

        # 通常のエッジ
        edge_colors.append('#333333')  # ダークグレー
        edge_styles.append('-')

    return edge_colors, edge_styles

def get_edge_labels(graph, graph_type="CFG"):
    """エッジにラベルを追加（True/False分岐など）"""
    edge_labels = {}

    if graph_type != "CFG":
        return edge_labels

    # 各ノードからの出力エッジ数をカウント
    for edge in graph.edges():
        source, target = edge

        # ループバックエッジの検出（優先）- より厳密な判定
        if hasattr(source, 'addr') and hasattr(target, 'addr'):
            # 実際のループバック：while/forループでの戻り
            source_stmts = [str(stmt) for stmt in source.statements] if hasattr(source, 'statements') and source.statements else []

            # WHILEループの戻り：print -> while条件への戻り
            if (source.addr > target.addr and
                any('print(' in stmt for stmt in source_stmts) and
                any('x < 0' in str(stmt) for stmt in (target.statements if hasattr(target, 'statements') else []))):
                edge_labels[edge] = "Loop"
                continue

            # FORループの戻り：print -> loop条件への戻り
            if (source.addr > target.addr and
                any('print(' in stmt for stmt in source_stmts) and
                any('iteratorNonEmptyOrException' in str(stmt) for stmt in (target.statements if hasattr(target, 'statements') else []))):
                edge_labels[edge] = "Loop"
                continue

        # ソースノードが条件判定ノードかチェック
        if hasattr(source, 'statements') and source.statements:
            source_stmts = [str(stmt) for stmt in source.statements]

            # 条件判定がある場合
            has_condition = any(
                'x > 0' in stmt or 'x < 0' in stmt or 'x > 10' in stmt or
                'i % 2 == 0' in stmt or 'i%2 == 0' in stmt or 'Compare:' in stmt
                for stmt in source_stmts
            )

            if has_condition:
                # そのノードから出るエッジの数を確認
                out_edges = list(graph.out_edges(source))

                if len(out_edges) == 2:  # 2つのエッジがある場合
                    source_addr = getattr(source, 'addr', 0)
                    target_addr = getattr(target, 'addr', 0)

                    # 条件の種類に応じた判定
                    if any('i % 2 == 0' in stmt or 'i%2 == 0' in stmt for stmt in source_stmts):
                        # i % 2 == 0 の場合：偶数なら"Even"出力、奇数なら"Odd"出力
                        target_stmts = [str(stmt) for stmt in target.statements] if hasattr(target, 'statements') and target.statements else []
                        if any('Even' in stmt for stmt in target_stmts):
                            edge_labels[edge] = "True"
                        elif any('Odd' in stmt for stmt in target_stmts):
                            edge_labels[edge] = "False"
                        else:
                            edge_labels[edge] = "True" if target_addr < source_addr else "False"
                    elif any('x > 0' in stmt for stmt in source_stmts):
                        # x > 0 の場合：Trueならfor文、Falseならwhile文
                        target_stmts = [str(stmt) for stmt in target.statements] if hasattr(target, 'statements') and target.statements else []
                        if any('range(' in stmt for stmt in target_stmts):
                            edge_labels[edge] = "True"
                        elif any('x < 0' in stmt for stmt in target_stmts):
                            edge_labels[edge] = "False"
                        else:
                            edge_labels[edge] = "True" if target_addr > source_addr else "False"
                    elif any('x < 0' in stmt for stmt in source_stmts):
                        # x < 0 の場合：Trueならwhile継続、Falseなら次へ
                        target_stmts = [str(stmt) for stmt in target.statements] if hasattr(target, 'statements') and target.statements else []
                        if any('Negative' in stmt for stmt in target_stmts):
                            edge_labels[edge] = "True"
                        else:
                            edge_labels[edge] = "False"
                    elif any('x > 10' in stmt for stmt in source_stmts):
                        # x > 10 の場合：TrueならDone、FalseならNot Done
                        target_stmts = [str(stmt) for stmt in target.statements] if hasattr(target, 'statements') and target.statements else []
                        if any('Done' in stmt and 'NotDone' not in stmt for stmt in target_stmts):
                            edge_labels[edge] = "True"
                        elif any('NotDone' in stmt for stmt in target_stmts):
                            edge_labels[edge] = "False"
                        else:
                            edge_labels[edge] = "True" if target_addr < source_addr else "False"
                    else:
                        # 一般的な判定
                        other_edges = [e for e in out_edges if e != edge]
                        if other_edges:
                            other_target_addr = getattr(other_edges[0][1], 'addr', 0)
                            edge_labels[edge] = "True" if target_addr < other_target_addr else "False"
                elif len(out_edges) == 1:  # 1つのエッジのみ
                    edge_labels[edge] = ""  # ラベルなし

    return edge_labels

def get_node_colors(graph, graph_type="CFG"):
    """グラフタイプに応じたノードの色を決定"""
    colors = []

    for node in graph.nodes():
        if graph_type == "CFG":
            # CFGの場合：エントリー/エグジット/通常ノードで色分け

            # 特別処理: FUNCTION_START + 条件判定の組み合わせノード
            if hasattr(node, 'statements') and node.statements:
                has_function_start = any('FUNCTION_START' in str(stmt) for stmt in node.statements)
                has_condition = any('Compare:' in str(stmt) for stmt in node.statements if 'FUNCTION_START' not in str(stmt))

                if has_function_start and has_condition:
                    colors.append('#FF6B6B')  # 問題のノードは赤系で警告
                    continue

            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                colors.append('#90EE90')  # ライトグリーン
            elif hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                colors.append('#FFB6C1')  # ライトピンク
            elif hasattr(node, 'is_merged_node') and node.is_merged_node:
                colors.append('#FFD700')  # ゴールド
            else:
                # ステートメントタイプに応じた色分け
                if hasattr(node, 'statements') and node.statements:
                    stmt_types = [str(stmt) for stmt in node.statements]
                    if any('Compare:' in stmt for stmt in stmt_types):
                        colors.append('#87CEFA')  # 条件判定は薄い青
                    elif any('Call:' in stmt for stmt in stmt_types):
                        colors.append('#98FB98')  # 関数呼び出しは薄い緑
                    elif any('FUNCTION_END' in stmt for stmt in stmt_types):
                        colors.append('#FFB6C1')  # 関数終了はピンク
                    else:
                        colors.append('#87CEEB')  # スカイブルー（通常）
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

def draw_edges_with_curves(graph, pos, edge_colors, edge_styles):
    """エッジを適切なカーブで描画（重複エッジも考慮）"""
    edge_counts = {}

    # 同じノード間のエッジをカウント（アドレスベースで比較）
    for edge in graph.edges():
        source, target = edge
        # addrがない場合はid()を使用し、Noneの場合は0を使用
        source_id = getattr(source, 'addr', None)
        if source_id is None:
            source_id = id(source)
        target_id = getattr(target, 'addr', None)
        if target_id is None:
            target_id = id(target)

        key = tuple(sorted([source_id, target_id]))
        if key not in edge_counts:
            edge_counts[key] = 0
        edge_counts[key] += 1

    # エッジを描画
    for i, edge in enumerate(graph.edges()):
        source, target = edge
        # 同じ方法でIDを取得
        source_id = getattr(source, 'addr', None)
        if source_id is None:
            source_id = id(source)
        target_id = getattr(target, 'addr', None)
        if target_id is None:
            target_id = id(target)

        key = tuple(sorted([source_id, target_id]))

        # カーブの角度を決定
        if edge_counts[key] > 1:
            # 複数エッジの場合、異なるカーブを使用
            curve_rad = 0.1 + (i % 2) * 0.2  # 0.1 または 0.3
        else:
            # 単一エッジの場合、小さなカーブ
            curve_rad = 0.1

        # 個別にエッジを描画
        nx.draw_networkx_edges(graph, pos,
                              edgelist=[edge],
                              edge_color=[edge_colors[i]],
                              arrows=True,
                              arrowsize=20,
                              arrowstyle='-|>',
                              width=2,
                              alpha=0.8,
                              node_size=2000,
                              connectionstyle=f"arc3,rad={curve_rad}")

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
    edge_labels = get_edge_labels(graph, graph_type)
    edge_colors, edge_styles = get_edge_colors_and_styles(graph, graph_type)

    # エッジを先に描画（改良された矢印スタイル）
    if graph_type == "CFG":
        # CFGの場合は複雑なカーブ描画を使用
        draw_edges_with_curves(graph, pos, edge_colors, edge_styles)
    else:
        # AST/DDGの場合はシンプルな描画
        nx.draw_networkx_edges(graph, pos,
                              edge_color=edge_colors,
                              arrows=True,
                              arrowsize=15,
                              arrowstyle='-|>',
                              width=1.5,
                              alpha=0.8,
                              connectionstyle="arc3,rad=0.1")

    # ノードを描画
    nx.draw_networkx_nodes(graph, pos,
                          node_color=node_colors,
                          node_size=2000,
                          alpha=0.8)

    # ラベルを描画
    nx.draw_networkx_labels(graph, pos, labels,
                           font_size=8,
                           font_weight='bold')

    # エッジラベルを描画（True/False/Loopなど）
    if edge_labels:
        nx.draw_networkx_edge_labels(graph, pos, edge_labels,
                                   font_size=8,  # フォントサイズを少し大きく
                                   font_color='darkred',  # より濃い色
                                   font_weight='bold',
                                   bbox=dict(boxstyle="round,pad=0.2",
                                           facecolor='white',
                                           edgecolor='darkred',
                                           alpha=0.8))  # 背景付きで見やすく

    plt.title(f"{title}\n({graph_type}: {len(graph.nodes())} nodes, {len(graph.edges())} edges)",
              fontsize=14, fontweight='bold')

    # 凡例を追加
    if graph_type == "CFG":
        legend_elements = [
            mpatches.Patch(color='#FF6B6B', label='⚠️ Function Start + Condition'),
            mpatches.Patch(color='#90EE90', label='🚀 Entry Point'),
            mpatches.Patch(color='#FFB6C1', label='🏁 Exit Point'),
            mpatches.Patch(color='#FFD700', label='🔗 Merge Node'),
            mpatches.Patch(color='#87CEFA', label='🔍 Condition'),
            mpatches.Patch(color='#98FB98', label='📞 Function Call'),
            mpatches.Patch(color='#87CEEB', label='📝 Regular Node'),
            # エッジの凡例を追加
            mpatches.Patch(color='#333333', label='→ Normal Flow'),
            mpatches.Patch(color='#4169E1', label='→ Conditional Branch'),
            mpatches.Patch(color='#FF6B6B', label='↺ Loop Back')
        ]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=8)

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
            edge_labels = get_edge_labels(graph, graph_type)
            edge_colors, edge_styles = get_edge_colors_and_styles(graph, graph_type)

            nx.draw_networkx_edges(graph, pos,
                                  edge_color=edge_colors,  # 動的な色分け
                                  arrows=True,
                                  arrowsize=15,  # 比較グラフ用のサイズ（小さめ）
                                  arrowstyle='-|>',  # より目立つ矢印
                                  width=1.5,  # エッジの太さ
                                  alpha=0.8,
                                  node_size=1500,  # ノードサイズを考慮
                                  connectionstyle="arc3,rad=0.1")  # カーブ

            nx.draw_networkx_nodes(graph, pos,
                                  node_color=node_colors,
                                  node_size=1500,
                                  alpha=0.8)

            nx.draw_networkx_labels(graph, pos, labels,
                                   font_size=7,
                                   font_weight='bold')

            # エッジラベル（True/False/Loop）
            if edge_labels:
                nx.draw_networkx_edge_labels(graph, pos, edge_labels,
                                           font_size=7,
                                           font_color='darkred',
                                           font_weight='bold',
                                           bbox=dict(boxstyle="round,pad=0.1",
                                                   facecolor='white',
                                                   edgecolor='darkred',
                                                   alpha=0.8))

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

def debug_cfg_structure(cfg, func_name):
    """CFG構造のデバッグ情報を出力"""
    print(f"\n🔍 CFG構造デバッグ - 関数: {func_name}")
    print(f"ノード数: {len(cfg.nodes())}, エッジ数: {len(cfg.edges())}")

    print(f"\n📋 詳細なノード解析:")
    for i, node in enumerate(cfg.nodes()):
        print(f"  ノード[{i}] (Block {getattr(node, 'addr', 'N/A')}): {str(node)[:50]}...")

        if hasattr(node, 'statements') and node.statements:
            print(f"    ステートメント数: {len(node.statements)}")
            for j, stmt in enumerate(node.statements):
                stmt_str = str(stmt)
                print(f"      [{j}]: {stmt_str}")

                # ステートメントの詳細解析
                if 'UnsupportedStmt' in stmt_str:
                    if 'iteratorNonEmptyOrException' in stmt_str:
                        print(f"         → 🔄 これはFORループの継続条件です")
                    elif 'formatString' in stmt_str:
                        print(f"         → 📝 これはf-stringのフォーマット部分です")
                    elif 'formattedValue' in stmt_str:
                        print(f"         → 🔢 これはf-string内の変数値です")
                    elif 'assignmentPlus' in stmt_str:
                        print(f"         → ➕ これは += 演算子です")
                    elif 'modulo' in stmt_str:
                        print(f"         → 🔢 これは % (剰余)演算子です")
                    elif 'fieldAccess' in stmt_str:
                        print(f"         → 🔗 これはオブジェクトのフィールドアクセスです")
                elif 'x < 0' in stmt_str:
                    print(f"         → 🔄 これはWHILEループの条件です")
                elif 'x > 0' in stmt_str:
                    print(f"         → 🔍 これはIF文の条件です")
                elif 'x > 10' in stmt_str:
                    print(f"         → 🔍 これは最後のIF文の条件です")

        # 特別な属性をチェック
        special_attrs = ['is_entrypoint', 'is_exitpoint', 'addr']
        for attr in special_attrs:
            if hasattr(node, attr):
                print(f"    {attr}: {getattr(node, attr)}")

    print(f"\n🔗 エッジ解析:")
    for i, edge in enumerate(cfg.edges()):
        source_addr = getattr(edge[0], 'addr', 'N/A')
        target_addr = getattr(edge[1], 'addr', 'N/A')
        print(f"    [{i}] Block {source_addr} -> Block {target_addr}")
        print(f"        {str(edge[0])[:40]}... -> {str(edge[1])[:40]}...")

def analyze_missing_conditions():
    """欠けている条件を分析"""
    print(f"\n🔍 欠けている条件の分析:")
    print(f"  1. ✅ 'i % 2 == 0' の条件ノードを発見！")
    print(f"     → Block 3 (ノード[11]) の最後に 'i%2 == 0' があります")
    print(f"     → これがFORループ内の条件分岐です")
    print(f"  2. WHILEループの条件 'x < 0' はBlock 9にあります")
    print(f"  3. f-stringの処理が複数のUnsupportedStmtに分散されています")
    print(f"     → formatString + formattedValue + print の組み合わせ")
    print(f"  4. 🔧 Block 14→Block 1, Block 16→Block 1 は通常の終了フロー")
    print(f"     → これらは'Loop'ではなく通常の制御フローです")

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

        # CFGのデバッグ情報を出力
        if cfg and len(cfg.nodes()) > 0:
            debug_cfg_structure(cfg, func_name)
            analyze_missing_conditions()

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
