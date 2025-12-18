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

# Pyjoernを利用してPythonコードのCFG、AST、DDGを解析・視覚化するツール
# 関数レベルとモジュールレベルの両方に対応

def analyze_python_construct(stmt_str):
    """Pythonの構文を詳細に解析（絵文字なし）"""

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
    }

    # 各カテゴリをチェック
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
    """グラフノードのラベルを作成（絵文字なし）"""
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

                # 特別処理: FUNCTION_START を含むノードは常にすべて表示
                has_function_start = any('FUNCTION_START' in str(stmt) for stmt in node.statements)

                if has_function_start:
                    # FUNCTION_STARTを含むノードはすべてのステートメントを詳細表示
                    base_label = "[START] FUNCTION ENTRY\n" + "="*20

                    # デバッグ: コンソールにも詳細な情報を出力
                    print(f"\n=== FUNCTION_START NODE DEBUG ===")
                    print(f"Node: {node}")
                    print(f"Address: {getattr(node, 'addr', 'N/A')}")
                    print(f"Statement count: {len(node.statements)}")

                    for i, stmt in enumerate(node.statements):
                        stmt_str = str(stmt)
                        stmt_type = type(stmt).__name__ if hasattr(stmt, '__class__') else 'Unknown'

                        # UnsupportedStmtを含むステートメントはスキップ
                        if 'UnsupportedStmt' in stmt_str:
                            continue

                        # コンソール出力
                        print(f"[{i}] Type: {stmt_type} | Value: {stmt_str}")
                        if hasattr(stmt, '__dict__'):
                            print(f"    Attributes: {list(stmt.__dict__.keys())}")

                        # グラフ表示
                        if 'FUNCTION_START' in stmt_str:
                            base_label += f"\n[START] Function begins"
                        elif 'Compare:' in stmt_str:
                            condition = stmt_str.replace('Compare: ', '')
                            if len(condition) > 30:
                                condition = condition[:27] + "..."
                            base_label += f"\n[COND] if {condition}"
                        elif 'Assignment:' in stmt_str:
                            assign = stmt_str.replace('Assignment: ', '')
                            if len(assign) > 30:
                                assign = assign[:27] + "..."
                            base_label += f"\n[ASSIGN] {assign}"
                        elif 'Call:' in stmt_str:
                            call = stmt_str.replace('Call: ', '')
                            if len(call) > 30:
                                call = call[:27] + "..."
                            base_label += f"\n[CALL] {call}"
                        else:
                            # その他の意味のあるステートメント（実際のコード部分）
                            if len(stmt_str) > 30:
                                display_str = stmt_str[:27] + "..."
                            else:
                                display_str = stmt_str
                            base_label += f"\n{display_str}"

                    print(f"=== END DEBUG ===\n")
                else:
                    # 通常のノードの場合
                    base_label += f"\n({stmt_count} stmts)"

                    # ステートメントタイプに応じたラベル付け - 簡潔化
                    primary_stmt_type = None
                    primary_content = ""

                    # 主要なステートメントタイプを特定（汎用的なパターン検出）
                    for stmt in node.statements:
                        stmt_str = str(stmt)

                        # ループ構造の判定
                        if 'iteratorNonEmptyOrException' in stmt_str or 'iterator' in stmt_str.lower():
                            primary_stmt_type = "LOOP_ITERATION"
                            primary_content = "Loop iteration check"
                            break
                        # 条件比較の判定（汎用的）
                        elif 'Compare:' in stmt_str:
                            primary_stmt_type = "CONDITION"
                            # 条件の内容を簡潔に表示
                            condition = stmt_str.replace('Compare: ', '').strip()
                            if len(condition) > 25:
                                condition = condition[:22] + "..."
                            primary_content = f"Condition: {condition}"
                            break
                        # 関数呼び出しの判定（汎用的）
                        elif 'Call:' in stmt_str:
                            primary_stmt_type = "FUNCTION_CALL"
                            # 呼び出し内容を簡潔に表示
                            call = stmt_str.replace('Call: ', '').strip()
                            if len(call) > 25:
                                call = call[:22] + "..."
                            primary_content = f"Call: {call}"
                            break
                        # 代入の判定
                        elif 'Assignment:' in stmt_str:
                            primary_stmt_type = "ASSIGNMENT"
                            assign = stmt_str.replace('Assignment: ', '').strip()
                            if len(assign) > 25:
                                assign = assign[:22] + "..."
                            primary_content = f"Assign: {assign}"
                            break
                        # 関数の開始/終了
                        elif 'FUNCTION_START' in stmt_str:
                            primary_stmt_type = "FUNCTION_START"
                            primary_content = "Function Entry"
                            break
                        elif 'FUNCTION_END' in stmt_str:
                            primary_stmt_type = "FUNCTION_END"
                            primary_content = "Function End"
                            break

                    # プライマリタイプに基づくラベル設定はコメントアウト（詳細表示優先）
                    # if primary_stmt_type:
                    #     if primary_stmt_type == "LOOP_ITERATION":
                    #         base_label += f"\n[LOOP] {primary_content}"
                    #     elif primary_stmt_type == "CONDITION":
                    #         base_label += f"\n[COND] {primary_content}"
                    #     elif primary_stmt_type == "FUNCTION_CALL":
                    #         base_label += f"\n[CALL] {primary_content}"
                    #     elif primary_stmt_type == "ASSIGNMENT":
                    #         base_label += f"\n[ASSIGN] {primary_content}"
                    #     elif primary_stmt_type == "FUNCTION_START":
                    #         base_label += f"\n[START] {primary_content}"
                    #     elif primary_stmt_type == "FUNCTION_END":
                    #         base_label += f"\n[END] {primary_content}"
                    #     else:
                    #         base_label += f"\n[STMT] {primary_content}"
                    # else:

                    # 意味のあるステートメントのみを表示（UnsupportedStmtを除外）
                    for i, stmt in enumerate(node.statements):
                        stmt_str = str(stmt)

                        # UnsupportedStmtを含むステートメントはスキップ
                        if 'UnsupportedStmt' in stmt_str:
                            continue

                        # ステートメントタイプに応じたプレフィックスを追加
                        if 'Compare:' in stmt_str:
                            condition = stmt_str.replace('Compare: ', '')
                            if len(condition) > 30:
                                condition = condition[:27] + "..."
                            base_label += f"\n[COND] {condition}"
                        elif 'Assignment:' in stmt_str:
                            assign = stmt_str.replace('Assignment: ', '')
                            if len(assign) > 30:
                                assign = assign[:27] + "..."
                            base_label += f"\n[ASSIGN] {assign}"
                        elif 'Call:' in stmt_str:
                            call = stmt_str.replace('Call: ', '')
                            if len(call) > 30:
                                call = call[:27] + "..."
                            base_label += f"\n[CALL] {call}"
                        elif 'FUNCTION_END' in stmt_str:
                            base_label += f"\n[END] Function End"
                        elif 'iteratorNonEmptyOrException' in stmt_str:
                            base_label += f"\n[LOOP] Iterator check"
                        else:
                            # その他の意味のあるステートメント（実際のコード部分）
                            if len(stmt_str) > 30:
                                display_str = stmt_str[:27] + "..."
                            else:
                                display_str = stmt_str
                            base_label += f"\n{display_str}"

                    # すべてのステートメントを表示するため、制限をコメントアウト
                    # if len(node.statements) > 3:
                    #     # 複数ステートメントがある場合は総数のみ表示
                    #     additional_count = len(node.statements) - 1
                    #     if additional_count > 0:
                    #         base_label += f"\n(+ {additional_count} more stmts)"

            # エントリー/エグジットポイントの表示
            if hasattr(node, 'is_entrypoint') and node.is_entrypoint:
                if not ('[START]' in base_label):
                    base_label = "[ENTRY] ENTRY\n" + base_label
            if hasattr(node, 'is_exitpoint') and node.is_exitpoint:
                base_label = base_label + "\n[EXIT] EXIT"

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
                # ただし、関数終了ノードからのエッジは除外
                source_stmts = [str(stmt) for stmt in source.statements] if hasattr(source, 'statements') and source.statements else []

                # 関数終了や出口ノードからのエッジはループではない
                is_function_end_source = any('FUNCTION_END' in stmt for stmt in source_stmts)
                is_exit_source = hasattr(source, 'is_exitpoint') and source.is_exitpoint
                is_exit_target = hasattr(target, 'is_exitpoint') and target.is_exitpoint

                if not (is_function_end_source or is_exit_source or is_exit_target):
                    edge_colors.append('#FF6B6B')  # 赤色でループを強調
                    edge_styles.append('--')  # 破線
                    continue
                else:
                    # 関数終了関連のエッジは通常の色
                    edge_colors.append('#333333')  # ダークグレー
                    edge_styles.append('-')
                    continue

        # 条件分岐エッジ（汎用的な検出）
        if hasattr(source, 'statements') and source.statements:
            source_stmts = [str(stmt) for stmt in source.statements]
            # Compare文があるかどうかで条件分岐を判定（汎用的）
            has_condition = any('Compare:' in stmt for stmt in source_stmts)

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

        # ループバックエッジの検出（汎用的）
        if hasattr(source, 'addr') and hasattr(target, 'addr'):
            # 後ろから前へのエッジ（アドレスが逆順）はループバック
            if source.addr > target.addr:
                # ただし、関数終了ノードからのエッジは除外
                source_stmts = [str(stmt) for stmt in source.statements] if hasattr(source, 'statements') and source.statements else []
                target_stmts = [str(stmt) for stmt in target.statements] if hasattr(target, 'statements') and target.statements else []

                # 関数終了や出口ノードからのエッジはループではない
                is_function_end_source = any('FUNCTION_END' in stmt for stmt in source_stmts)
                is_exit_source = hasattr(source, 'is_exitpoint') and source.is_exitpoint
                is_exit_target = hasattr(target, 'is_exitpoint') and target.is_exitpoint

                if not (is_function_end_source or is_exit_source or is_exit_target):
                    edge_labels[edge] = "Loop"
                    continue

        # ソースノードが条件判定ノードかチェック（汎用的）
        if hasattr(source, 'statements') and source.statements:
            source_stmts = [str(stmt) for stmt in source.statements]

            # 条件判定がある場合（Compare文で汎用的に判定）
            has_condition = any('Compare:' in stmt for stmt in source_stmts)

            if has_condition:
                # 条件分岐ノードには特別なラベルは付けない
                # エッジの色分けは get_edge_colors_and_styles で処理される
                pass

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

def create_hierarchical_layout(graph, graph_type="CFG"):
    """コードの実行順序に基づいた階層的レイアウトを作成"""
    if graph_type != "CFG":
        # CFG以外は通常のspring layoutを使用
        return nx.spring_layout(graph, k=1.5, iterations=50)

    # GraphvizのDOTレイアウトを試行（上から下への階層構造）
    try:
        # DOTレイアウト：上から下へのフロー
        pos = nx.nx_agraph.graphviz_layout(graph, prog='dot')
        return pos
    except:
        # Graphvizが利用できない場合は、手動で階層的レイアウトを作成
        return create_manual_hierarchical_layout(graph)

def create_manual_hierarchical_layout(graph):
    """手動で階層的レイアウトを作成（上から下への配置）"""
    pos = {}

    # ノードをアドレス順にソート（実行順序に対応）
    nodes_with_addr = []
    nodes_without_addr = []

    for node in graph.nodes():
        if hasattr(node, 'addr') and node.addr is not None:
            nodes_with_addr.append((node.addr, node))
        else:
            nodes_without_addr.append(node)

    # アドレス順にソート
    nodes_with_addr.sort(key=lambda x: x[0])
    sorted_nodes = [node for addr, node in nodes_with_addr] + nodes_without_addr

    # 縦方向に配置（Y座標を上から下へ）
    y_positions = {}
    current_y = len(sorted_nodes)  # 上から開始

    for i, node in enumerate(sorted_nodes):
        y_positions[node] = current_y - i  # 上から順に配置

    # 横方向の配置を計算（同じレベルの分岐を考慮）
    x_positions = {}
    level_counts = {}

    for node in sorted_nodes:
        y = y_positions[node]
        if y not in level_counts:
            level_counts[y] = 0
        x_positions[node] = level_counts[y]
        level_counts[y] += 1

    # 座標を正規化
    for node in sorted_nodes:
        y = y_positions[node]
        x = x_positions[node]

        # 同一レベルのノードを中央揃え
        level_width = level_counts[y]
        if level_width > 1:
            x_offset = (x - (level_width - 1) / 2) * 2  # 横方向の間隔を調整
        else:
            x_offset = 0

        pos[node] = (x_offset, y)

    return pos

def visualize_graph(graph, title, graph_type="CFG", save_path=None):
    """単一グラフの視覚化（コード実行順序に基づいた配置）"""
    plt.figure(figsize=(14, 10))  # サイズを少し大きく

    # 階層的レイアウトを使用
    pos = create_hierarchical_layout(graph, graph_type)

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

    # エッジラベルを描画（Loopなど）
    if edge_labels:
        # 空でないラベルのみを描画
        non_empty_labels = {k: v for k, v in edge_labels.items() if v}
        if non_empty_labels:
            nx.draw_networkx_edge_labels(graph, pos, non_empty_labels,
                                       font_size=10,  # フォントサイズを大きく
                                       font_color='darkred',  # より濃い色
                                       font_weight='bold',
                                       bbox=dict(boxstyle="round,pad=0.3",
                                               facecolor='white',  # 白い背景
                                               edgecolor='darkred',
                                               alpha=0.9))  # 背景を濃く

    plt.title(f"{title}\n({graph_type}: {len(graph.nodes())} nodes, {len(graph.edges())} edges)",
              fontsize=14, fontweight='bold')

    # 凡例を追加
    if graph_type == "CFG":
        legend_elements = [
            mpatches.Patch(color='#FF6B6B', label='[WARN] Function Start + Condition'),
            mpatches.Patch(color='#90EE90', label='[START] Entry Point'),
            mpatches.Patch(color='#FFB6C1', label='[END] Exit Point'),
            mpatches.Patch(color='#FFD700', label='[MERGE] Merge Node'),
            mpatches.Patch(color='#87CEFA', label='[COND] Condition'),
            mpatches.Patch(color='#98FB98', label='[CALL] Function Call'),
            mpatches.Patch(color='#87CEEB', label='[STMT] Regular Node'),
            # エッジの凡例を追加
            mpatches.Patch(color='#333333', label='-> Normal Flow'),
            mpatches.Patch(color='#4169E1', label='-> Conditional Branch'),
            mpatches.Patch(color='#FF6B6B', label='-> Loop Back')
        ]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=8)

    plt.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"グラフを保存しました: {save_path}")

    plt.show()

def compare_graphs_side_by_side(cfg, ast, ddg, func_name, save_dir=None):
    """3つのグラフを横並びで比較表示（絵文字なし）"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    graphs = [
        (cfg, "CFG (Control Flow Graph)", "CFG"),
        (ast, "AST (Abstract Syntax Tree)", "AST"),
        (ddg, "DDG (Data Dependence Graph)", "DDG")
    ]

    for i, (graph, title, graph_type) in enumerate(graphs):
        if graph and len(graph.nodes()) > 0:
            plt.sca(axes[i])

            # 階層的レイアウトを使用（コンパクト版）
            if graph_type == "CFG":
                try:
                    # DOTレイアウトを試行
                    pos = nx.nx_agraph.graphviz_layout(graph, prog='dot')
                except:
                    # フォールバック：手動階層レイアウト（縮小版）
                    pos = create_manual_hierarchical_layout(graph)
                    # 比較表示用に座標をスケール調整
                    for node in pos:
                        x, y = pos[node]
                        pos[node] = (x * 0.8, y * 0.8)
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

    plt.suptitle(f"Graph Comparison for: {func_name}",
                fontsize=16, fontweight='bold')
    plt.tight_layout()

    if save_dir:
        save_path = os.path.join(save_dir, f"graph_comparison_{func_name}.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"比較グラフを保存しました: {save_path}")

    plt.show()

def debug_cfg_structure(cfg, func_name):
    """CFG構造を詳細にデバッグ（try-except構造の問題検出）"""
    print(f"\n{'='*60}")
    print(f"CFG構造デバッグ: {func_name}")
    print(f"{'='*60}")

    print(f"基本情報: {cfg.number_of_nodes()} nodes, {cfg.number_of_edges()} edges")

    # ノードをアドレスでソート
    nodes_with_addr = []
    for node in cfg.nodes():
        addr = getattr(node, 'addr', 0)  # アドレスがない場合は0
        nodes_with_addr.append((addr, node))

    # アドレス順にソート
    nodes_with_addr.sort(key=lambda x: x[0])

    # 全ノードの詳細分析
    for addr, node in nodes_with_addr:
        successors = list(cfg.successors(node))
        predecessors = list(cfg.predecessors(node))

        print(f"\n--- Node {addr} (ID: {id(node)}) ---")

        # ノードオブジェクト自体の詳細情報
        print(f"Node object: {node}")
        print(f"Node type: {type(node)}")
        print(f"Node attributes: {dir(node) if hasattr(node, '__dict__') else 'No attributes'}")

        # ステートメント詳細
        if hasattr(node, 'statements') and node.statements:
            print(f"Statements ({len(node.statements)}個):")
            for i, stmt in enumerate(node.statements):
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__
                print(f"  [{i}] {stmt_type}: {stmt_str}")

                # try-except関連キーワードの検出
                keywords = ['try', 'except', 'ValueError', 'TypeError', 'continue', 'Compare:', 'value % 2']
                for keyword in keywords:
                    if keyword in stmt_str:
                        print(f"      *** {keyword} detected ***")
        else:
            print("Statements: ノードに直接アクセスできない、またはstatements属性なし")

        print(f"In: {[getattr(p, 'addr', 'N/A') for p in predecessors]} | Out: {[getattr(s, 'addr', 'N/A') for s in successors]}")

        # 問題検出 - 最大アドレスのノードを取得
        max_addr = max(getattr(n, 'addr', 0) for n in cfg.nodes())
        if len(successors) == 0 and addr != max_addr:
            print(f"  🚨 WARNING: Node {addr} has no successors!")

            # try-except内のif文の検出
            if hasattr(node, 'statements') and node.statements:
                for stmt in node.statements:
                    if 'Compare:' in str(stmt) and 'value % 2' in str(stmt):
                        print(f"  🔍 ANALYSIS: This appears to be the if statement inside try block")
                        print(f"      Expected: Should have True/False branches")
                        print(f"      Reality: No outgoing edges found")
                        print(f"      Possible cause: try-except CFG generation issue")    # エッジ分析
    print(f"\n--- エッジ分析 ---")

    # エッジをソート可能にする
    edges_with_addr = []
    for edge in cfg.edges():
        source, target = edge
        source_addr = getattr(source, 'addr', 0)
        target_addr = getattr(target, 'addr', 0)
        edges_with_addr.append((source_addr, target_addr, source, target))

    # ソート
    edges_with_addr.sort(key=lambda x: (x[0], x[1]))

    for source_addr, target_addr, source, target in edges_with_addr:
        source_data = cfg.nodes[source]

        # ソースノードの最後のステートメント
        if hasattr(source_data, 'statements') and source_data.statements:
            last_stmt = str(source_data.statements[-1])
            edge_type = "Normal"

            if 'Compare:' in last_stmt:
                edge_type = "Conditional"
            elif 'try' in last_stmt.lower():
                edge_type = "Try-block"
            elif 'except' in last_stmt.lower():
                edge_type = "Exception-handler"

            print(f"{source_addr} -> {target_addr} ({edge_type})")
            if 'Compare:' in last_stmt and 'value % 2' in last_stmt:
                print(f"  ⚠️  Conditional node with potential branching issue")

    # 構造的問題の検出
    print(f"\n--- 構造的問題検出 ---")

    # デッドエンドノード（出口以外で後続なし）
    max_addr = max(getattr(n, 'addr', 0) for n in cfg.nodes())
    exit_node = None
    for node in cfg.nodes():
        if getattr(node, 'addr', 0) == max_addr:
            exit_node = node
            break

    deadend_nodes = [node for node in cfg.nodes()
                    if node != exit_node and len(list(cfg.successors(node))) == 0]

    if deadend_nodes:
        print(f"🚨 デッドエンドノード数: {len(deadend_nodes)}")
        for node in deadend_nodes:
            node_addr = getattr(node, 'addr', 'N/A')
            node_data = cfg.nodes[node]
            print(f"   Node {node_addr}:")
            if hasattr(node_data, 'statements') and node_data.statements:
                for stmt in node_data.statements:
                    print(f"     - {stmt}")
    else:
        print("✅ デッドエンドノードなし")

    # 強連結成分
    try:
        sccs = list(nx.strongly_connected_components(cfg))
        non_trivial_sccs = [scc for scc in sccs if len(scc) > 1]

        if non_trivial_sccs:
            print(f"🔄 ループ検出: {non_trivial_sccs}")
        else:
            print("✅ ループなし（DAG構造）")
    except:
        print("⚠️ 強連結成分分析でエラー")

def analyze_and_visualize_file(source_file, output_dir="graph_images"):
    """ソースファイルを解析してすべてのグラフを視覚化（関数・モジュール両対応）"""
    print(f"=" * 80)
    print(f"ファイル '{source_file}' のグラフ解析・視覚化（関数・モジュール両対応版）")
    print(f"=" * 80)

    # 実行ごとに一意のディレクトリを作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source_name = os.path.splitext(os.path.basename(source_file))[0]  # ファイル名（拡張子なし）
    unique_output_dir = os.path.join(output_dir, f"{source_name}_{timestamp}")

    # 出力ディレクトリの作成
    if not os.path.exists(unique_output_dir):
        os.makedirs(unique_output_dir)
        print(f"実行専用ディレクトリを作成しました: {unique_output_dir}")

    # ベースディレクトリも作成（存在しない場合）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # parse_sourceで詳細解析
    print("\n--- Parse Source Analysis ---")
    functions = parse_source(source_file)

    for func_name, func_obj in functions.items():
        print(f"\n[ANALYZE] '{func_name}' を解析中...")

        cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
        ast = func_obj.ast if hasattr(func_obj, 'ast') else None
        ddg = func_obj.ddg if hasattr(func_obj, 'ddg') else None

        # CFG構造のデバッグ分析を追加
        if cfg and len(cfg.nodes()) > 0:
            debug_cfg_structure(cfg, func_name)

        # 個別グラフの視覚化（タイムスタンプは不要、ディレクトリで区別）
        if cfg and len(cfg.nodes()) > 0:
            print("  [CFG] CFG グラフを視覚化...")
            # ファイル名に適さない文字を置換
            safe_name = func_name.replace('<', '').replace('>', '').replace('&lt;', '').replace('&gt;', '')
            save_path = os.path.join(unique_output_dir, f"cfg_{safe_name}.png")
            visualize_graph(cfg, f"CFG for '{func_name}'", "CFG", save_path)

        if ast and len(ast.nodes()) > 0:
            print("  [AST] AST グラフを視覚化...")
            safe_name = func_name.replace('<', '').replace('>', '').replace('&lt;', '').replace('&gt;', '')
            save_path = os.path.join(unique_output_dir, f"ast_{safe_name}.png")
            visualize_graph(ast, f"AST for '{func_name}'", "AST", save_path)

        if ddg and len(ddg.nodes()) > 0:
            print("  [DDG] DDG グラフを視覚化...")
            safe_name = func_name.replace('<', '').replace('>', '').replace('&lt;', '').replace('&gt;', '')
            save_path = os.path.join(unique_output_dir, f"ddg_{safe_name}.png")
            visualize_graph(ddg, f"DDG for '{func_name}'", "DDG", save_path)

        # 比較グラフの表示
        print("  [COMPARE] 比較グラフを生成...")
        safe_name = func_name.replace('<', '').replace('>', '').replace('&lt;', '').replace('&gt;', '')
        compare_graphs_side_by_side(cfg, ast, ddg, safe_name, unique_output_dir)

    # fast_cfgs_from_sourceで高速CFG解析
    print("\n--- Fast CFG Analysis ---")
    cfgs = fast_cfgs_from_source(source_file)

    # デバッグ用：利用可能なCFGを表示
    print(f"利用可能なCFG: {list(cfgs.keys())}")

    # 関数とモジュールのCFGをフィルタリング（演算子系のみ除外）
    function_cfgs = {}
    for name, cfg in cfgs.items():
        # 除外する条件：
        # - <operator> で始まるもの
        # - &lt;operator&gt; で始まるもの（HTMLエンコード）
        # モジュールレベルのコードも含める
        if (not name.startswith('<operator>') and
            not name.startswith('&lt;operator&gt;')):
            function_cfgs[name] = cfg

    print(f"フィルタリング後のCFG: {list(function_cfgs.keys())}")

    if not function_cfgs:
        print("  [INFO] 解析可能なCFGが見つかりませんでした。")

    for cfg_name, cfg in function_cfgs.items():
        if len(cfg.nodes()) > 0:
            print(f"\n[FAST-CFG] '{cfg_name}' のCFGを視覚化...")

            # Fast CFGでもデバッグ分析を追加
            debug_cfg_structure(cfg, cfg_name)

            # ファイル名に適さない文字を置換
            safe_name = cfg_name.replace('<', '').replace('>', '').replace('&lt;', '').replace('&gt;', '')
            save_path = os.path.join(unique_output_dir, f"fast_cfg_{safe_name}.png")
            visualize_graph(cfg, f"Fast CFG: {cfg_name}", "CFG", save_path)

    # 実行結果のサマリー表示
    print(f"\n" + "="*80)
    print(f"解析完了！ 結果は以下に保存されました:")
    print(f"📁 {unique_output_dir}")
    print(f"="*80)

if __name__ == "__main__":
    # # モジュールレベルのコードテスト
    # print("=== モジュールレベルコードのテスト ===")
    # analyze_and_visualize_file("module_test.py")

    # print("\n" + "="*50 + "\n")

    # # 関数化されたコードもテスト
    # print("=== 関数化されたコードのテスト ===")
    # analyze_and_visualize_file("textbook.py")

    # analyze_and_visualize_file("middle_code.c")
    # analyze_and_visualize_file("try_except.py")
    # analyze_and_visualize_file("try_except_fixed.py")
    # analyze_and_visualize_file("try_except.java")
    # analyze_and_visualize_file("whiletest.py")
    analyze_and_visualize_file("while.py")
