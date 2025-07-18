#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyJoern品質レポート生成スクリプト
使用例: python generate_quality_report.py whiletest.py
"""

import sys
import os
from pyjoern import parse_source
import networkx as nx
from collections import defaultdict
import re

def calculate_mccabe_complexity(cfg):
    """McCabe循環複雑度の計算"""
    E = len(cfg.edges)
    N = len(cfg.nodes)

    try:
        undirected_cfg = cfg.to_undirected()
        P = nx.number_connected_components(undirected_cfg)
    except:
        P = 1

    mccabe_complexity = E - N + 2 * P

    return {
        'mccabe_complexity': mccabe_complexity,
        'edges': E,
        'nodes': N,
        'components': P,
        'formula': f"M = {E} - {N} + 2×{P} = {mccabe_complexity}"
    }

def analyze_variables(cfg):
    """変数の読み書き分析"""
    variables = defaultdict(lambda: {'reads': 0, 'writes': 0})

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                if stmt_type == 'Assignment':
                    match = re.match(r'(\w+)\s*=', stmt_str)
                    if match:
                        var_name = match.group(1)
                        variables[var_name]['writes'] += 1

                elif stmt_type == 'UnsupportedStmt' and 'assignmentPlus' in stmt_str:
                    match = re.search(r"'([a-zA-Z_]\w*)\s*\+=", stmt_str)
                    if match:
                        var_name = match.group(1)
                        variables[var_name]['reads'] += 1
                        variables[var_name]['writes'] += 1

                elif stmt_type == 'Compare':
                    for var_name in re.findall(r'\b([a-zA-Z_]\w*)\b', stmt_str):
                        if var_name not in ['Compare', 'tmp0', 'tmp1']:
                            variables[var_name]['reads'] += 1

    return dict(variables)

def analyze_paths(cfg):
    """パス分析"""
    entry_nodes = [n for n in cfg.nodes if n.is_entrypoint]
    exit_nodes = [n for n in cfg.nodes if n.is_exitpoint]

    if not entry_nodes or not exit_nodes:
        return {'total_paths': 0}

    total_paths = 0
    for entry in entry_nodes:
        for exit in exit_nodes:
            try:
                simple_paths = list(nx.all_simple_paths(cfg, entry, exit))
                total_paths += len(simple_paths)
            except nx.NetworkXNoPath:
                pass

    return {'total_paths': total_paths}

def count_conditionals(cfg):
    """条件分岐の数を数える"""
    count = 0
    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                if type(stmt).__name__ == 'Compare':
                    count += 1
    return count

def count_loops(cfg):
    """ループの数を数える"""
    count = 0
    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                if (type(stmt).__name__ == 'Call' and 'range(' in stmt_str) or \
                   'iteratorNonEmptyOrException' in stmt_str:
                    count += 1
    return count

def generate_html_report(file_path, results):
    """HTML品質レポートの生成"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PyJoern品質レポート</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .high-complexity { background-color: #ffcccc; }
            .medium-complexity { background-color: #ffffcc; }
            .low-complexity { background-color: #ccffcc; }
            .summary { background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>PyJoern品質レポート</h1>
        <div class="summary">
            <h2>分析対象ファイル</h2>
            <p><strong>ファイル名:</strong> {}</p>
            <p><strong>分析関数数:</strong> {}</p>
        </div>

        <h2>関数別詳細</h2>
        <table>
            <tr>
                <th>関数名</th>
                <th>複雑度</th>
                <th>実行パス数</th>
                <th>変数数</th>
                <th>条件分岐数</th>
                <th>ループ数</th>
                <th>評価</th>
            </tr>
    """.format(file_path, len(results))

    for func_name, metrics in results.items():
        complexity = metrics['complexity']['mccabe_complexity']

        if complexity <= 10:
            css_class = "low-complexity"
            evaluation = "良好"
        elif complexity <= 20:
            css_class = "medium-complexity"
            evaluation = "注意"
        else:
            css_class = "high-complexity"
            evaluation = "改善必要"

        html_content += f"""
            <tr class="{css_class}">
                <td>{func_name}</td>
                <td>{complexity}</td>
                <td>{metrics['paths']['total_paths']}</td>
                <td>{len(metrics['variables'])}</td>
                <td>{metrics['conditionals']}</td>
                <td>{metrics['loops']}</td>
                <td>{evaluation}</td>
            </tr>
        """

    html_content += """
        </table>

        <h2>計算式の詳細</h2>
        <p><strong>McCabe循環複雑度:</strong> M = E - N + 2P</p>
        <ul>
            <li>E: エッジ数（制御フローの遷移数）</li>
            <li>N: ノード数（基本ブロック数）</li>
            <li>P: 連結成分数（通常は1）</li>
        </ul>

        <h2>評価基準</h2>
        <ul>
            <li><span style="background-color: #ccffcc; padding: 2px 4px;">良好</span>: 複雑度1-10（保守しやすい）</li>
            <li><span style="background-color: #ffffcc; padding: 2px 4px;">注意</span>: 複雑度11-20（注意が必要）</li>
            <li><span style="background-color: #ffcccc; padding: 2px 4px;">改善必要</span>: 複雑度21以上（リファクタリング推奨）</li>
        </ul>
    </body>
    </html>
    """

    output_file = f"{os.path.splitext(file_path)[0]}_quality_report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_file

def main():
    if len(sys.argv) != 2:
        print("使用方法: python generate_quality_report.py <pythonファイル>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"エラー: ファイル '{file_path}' が見つかりません")
        sys.exit(1)

    print(f"分析中: {file_path}")
    print("=" * 60)

    try:
        # PyJoernでファイルを解析
        functions = parse_source(file_path)
        results = {}

        for func_name, func_obj in functions.items():
            if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):
                print(f"関数 '{func_name}' を分析中...")

                # 各種メトリクスの計算
                complexity = calculate_mccabe_complexity(func_obj.cfg)
                variables = analyze_variables(func_obj.cfg)
                paths = analyze_paths(func_obj.cfg)
                conditionals = count_conditionals(func_obj.cfg)
                loops = count_loops(func_obj.cfg)

                results[func_name] = {
                    'complexity': complexity,
                    'variables': variables,
                    'paths': paths,
                    'conditionals': conditionals,
                    'loops': loops
                }

                # 結果を表示
                print(f"  複雑度: {complexity['mccabe_complexity']}")
                print(f"  実行パス数: {paths['total_paths']}")
                print(f"  変数数: {len(variables)}")
                print(f"  条件分岐数: {conditionals}")
                print(f"  ループ数: {loops}")
                print()

        # HTMLレポートの生成
        if results:
            report_file = generate_html_report(file_path, results)
            print(f"HTMLレポートを生成しました: {report_file}")
        else:
            print("分析可能な関数が見つかりませんでした")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
