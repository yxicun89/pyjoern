#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルなAST構造表示プログラム

debug_analysis.pyのASTノード調査コードを元に、
AST構造を分かりやすく表示する
"""

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx

# デバッグ表示制御フラグ
VERBOSE_OUTPUT = True  # True: 詳細表示, False: サマリーのみ


def display_ast_structure(file_path):
    """
    指定されたファイルのAST構造を表示
    """
    if VERBOSE_OUTPUT:
        print(f"{'='*60}")
        print(f"AST構造表示: {file_path}")
        print(f"{'='*60}")

    try:
        # pyjoernでパース
        functions = parse_source(file_path)

        if not functions:
            if VERBOSE_OUTPUT:
                print("❌ 関数が見つかりませんでした")
            return

        if VERBOSE_OUTPUT:
            print(f"✅ 検出された関数: {list(functions.keys())}")

        # 各関数のAST構造を表示
        for func_name, func_obj in functions.items():
            if VERBOSE_OUTPUT:
                print(f"\n{'='*40}")
                print(f"関数: {func_name}")
                print(f"{'='*40}")

                print(f"開始行: {func_obj.start_line}")
                print(f"終了行: {func_obj.end_line}")

            # AST構造の詳細表示（コメントアウト）
            # display_ast_details(func_obj)

    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()


def display_ast_details(func_obj):
    """
    関数のAST詳細を表示
    """
    if not (hasattr(func_obj, 'ast') and func_obj.ast and isinstance(func_obj.ast, nx.DiGraph)):
        print("⚠️  AST情報が利用できません")
        return

    ast_graph = func_obj.ast
    print(f"📊 AST統計:")
    print(f"  - ノード数: {len(ast_graph.nodes)}")
    print(f"  - エッジ数: {len(ast_graph.edges)}")

    # AST ノードの詳細表示
    print(f"\n🌳 ASTノード一覧:")

    for i, node in enumerate(ast_graph.nodes):
        print(f"\n--- ASTノード {i+1} ---")
        print(f"  型: {type(node).__name__}")
        print(f"  repr: {repr(node)}")

        # ノードの属性を詳細表示
        if hasattr(node, '__dict__'):
            node_dict = node.__dict__
            print(f"  属性(__dict__):")
            for key, value in node_dict.items():
                # 値を適切に表示（長すぎる場合は切り詰め）
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"    {key}: {value_str}")

        # よく使われる属性を個別チェック
        important_attrs = ['name', 'code', 'type', 'line_number', 'value', 'kind', 'node_type', 'ast_type']
        print(f"  重要な属性:")
        for attr in important_attrs:
            if hasattr(node, attr):
                attr_value = getattr(node, attr)
                print(f"    {attr}: {attr_value}")

        # 利用可能なすべての属性を表示
        all_attrs = [attr for attr in dir(node) if not attr.startswith('_')]
        print(f"  利用可能な属性: {', '.join(all_attrs[:10])}")
        if len(all_attrs) > 10:
            print(f"    ... 他{len(all_attrs) - 10}個")

        # 最初の10ノードだけ詳細表示
        if i >= 9:
            remaining = len(ast_graph.nodes) - 10
            if remaining > 0:
                print(f"\n... 他{remaining}個のASTノードをスキップ")
            break


def analyze_ast_node_types(file_path):
    """
    AST内のノードタイプを分析
    """
    if VERBOSE_OUTPUT:
        print(f"\n{'='*40}")
        print("AST ノードタイプ分析")
        print(f"{'='*40}")

    try:
        functions = parse_source(file_path)

        for func_name, func_obj in functions.items():
            if not (hasattr(func_obj, 'ast') and func_obj.ast):
                continue

            if VERBOSE_OUTPUT:
                print(f"\n関数 {func_name} のノードタイプ統計:")

            # ノードタイプを集計
            node_types = {}
            for node in func_obj.ast.nodes:
                node_type = type(node).__name__
                node_types[node_type] = node_types.get(node_type, 0) + 1

            # 結果を表示
            if VERBOSE_OUTPUT:
                for node_type, count in sorted(node_types.items()):
                    print(f"  {node_type}: {count}個")

            # 代表的なノードの例を表示
            if VERBOSE_OUTPUT:
                print(f"\n代表的なノードの例:")
                examples = {}
                for node in func_obj.ast.nodes:
                    node_type = type(node).__name__
                    if node_type not in examples:
                        examples[node_type] = node

                for node_type, example_node in list(examples.items())[:5]:
                    print(f"  {node_type}:")
                    if hasattr(example_node, 'code') and example_node.code:
                        print(f"    コード: {example_node.code}")
                    elif hasattr(example_node, 'name') and example_node.name:
                        print(f"    名前: {example_node.name}")
                    else:
                        print(f"    repr: {repr(example_node)[:50]}")

            # 新機能: statements解析による変数抽出
            var_analysis = analyze_variables_from_statements(func_obj)

            # 新機能: 複合代入演算子解析（1回だけ）
            compound_assignments = analyze_compound_assignments(func_obj, var_analysis)

            # 新機能: 変数の読み込み数解析（複合代入演算子結果を渡す）
            read_counts = analyze_variable_reads(func_obj, var_analysis, compound_assignments)

            # 新機能: 変数の書き込み数解析（複合代入演算子結果を渡す）
            write_counts = analyze_variable_writes(func_obj, var_analysis, compound_assignments)

    except Exception as e:
        print(f"❌ ノードタイプ分析エラー: {e}")


def extract_function_arguments(call_statement, function_name):
    """
    関数呼び出しステートメントから引数を抽出
    例: "example(5)" → ["5"]
    """
    import re

    # 関数名(引数...)のパターンを抽出
    pattern = rf'{re.escape(function_name)}\s*\((.*?)\)'
    match = re.search(pattern, call_statement)

    if match:
        args_str = match.group(1).strip()
        if not args_str:
            return []

        # カンマで分割して引数リストを作成
        # 簡単な分割（ネストした括弧は考慮しない）
        args = [arg.strip() for arg in args_str.split(',')]
        return args

    return []


def get_function_parameters(func_obj):
    """
    pyjoernの関数オブジェクトからパラメータ名のリストを取得
    """
    parameters = []

    if hasattr(func_obj, 'ast') and func_obj.ast:
        for node in func_obj.ast.nodes:
            if hasattr(node, 'statements') and node.statements:
                for stmt in node.statements:
                    stmt_str = str(stmt)

                    # PARAMステートメントからパラメータを抽出
                    if stmt_str.startswith('<UnsupportedStmt: PARAM,'):
                        try:
                            # PARAM,parameter_name:type の形式
                            param_part = stmt_str.split('PARAM,')[1]
                            param_name = param_part.split(':')[0] if ':' in param_part else param_part.split('>')[0]
                            if param_name and param_name not in parameters:
                                parameters.append(param_name)
                        except:
                            pass

    return parameters


def analyze_top_level_variables(module_cfg, function_calls):
    """
    トップレベルでの変数読み込み・書き込みを解析
    関数呼び出しの引数から変数使用を検出
    """
    if VERBOSE_OUTPUT:
        print(f"\n🎯 トップレベル変数使用分析:")

    # 変数の読み込み・書き込みをカウント
    variable_reads = {}
    variable_writes = {}
    literal_values = []

    # 関数呼び出しから引数を分析
    for call_info in function_calls:
        stmt_str = call_info['statement']
        function_name = call_info['function_name']

        if VERBOSE_OUTPUT:
            print(f"\n📞 関数呼び出し分析: {stmt_str}")

        # 引数を抽出
        args = extract_function_arguments(stmt_str, function_name)
        if VERBOSE_OUTPUT:
            print(f"  📥 引数: {args}")

        # 各引数を分析
        for i, arg in enumerate(args):
            arg = arg.strip()

            # リテラル値（数値、文字列）の場合
            if arg.isdigit() or (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                literal_values.append(arg)
                if VERBOSE_OUTPUT:
                    print(f"    📌 引数[{i}]: リテラル値 '{arg}'")

            # 変数名の場合
            elif arg.isidentifier():
                # 変数の読み込みとしてカウント
                variable_reads[arg] = variable_reads.get(arg, 0) + 1
                if VERBOSE_OUTPUT:
                    print(f"    📖 引数[{i}]: 変数読み込み '{arg}' ({variable_reads[arg]}回目)")

            # 複雑な式の場合
            else:
                # 式の中の変数を抽出
                vars_in_expr = extract_variables_from_expression(arg)
                for var in vars_in_expr:
                    variable_reads[var] = variable_reads.get(var, 0) + 1
                    if VERBOSE_OUTPUT:
                        print(f"    🔍 引数[{i}]: 式 '{arg}' 内の変数読み込み '{var}' ({variable_reads[var]}回目)")

    # モジュール内の代入文を分析
    if VERBOSE_OUTPUT:
        print(f"\n✏️ トップレベル代入文分析:")
    for node in module_cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # 代入文を検出
                if '=' in stmt_str and not stmt_str.startswith('<UnsupportedStmt:') and not 'def' in stmt_str:
                    # 単純な代入文 (var = value)
                    import re
                    assignment_pattern = r'(\w+)\s*=\s*(.+)'
                    match = re.search(assignment_pattern, stmt_str)

                    if match:
                        var_name = match.group(1).strip()
                        value = match.group(2).strip()

                        # 組み込み変数や関数定義を除外
                        if var_name not in ['print', 'range', '__name__'] and not value.startswith('def'):
                            variable_writes[var_name] = variable_writes.get(var_name, 0) + 1
                            if VERBOSE_OUTPUT:
                                print(f"  ✏️ 変数書き込み: '{var_name}' = {value} ({variable_writes[var_name]}回目)")

    # 結果の表示
    if VERBOSE_OUTPUT:
        print(f"\n📊 トップレベル変数使用サマリー:")

        print(f"📖 変数読み込み:")
        if variable_reads:
            total_reads = sum(variable_reads.values())
            for var, count in sorted(variable_reads.items()):
                print(f"  - {var}: {count}回")
            print(f"  📊 総読み込み数: {total_reads}回")
        else:
            print(f"  なし")

        print(f"✏️ 変数書き込み:")
        if variable_writes:
            total_writes = sum(variable_writes.values())
            for var, count in sorted(variable_writes.items()):
                print(f"  - {var}: {count}回")
            print(f"  📊 総書き込み数: {total_writes}回")
        else:
            print(f"  なし")

        print(f"📌 リテラル値:")
        if literal_values:
            for literal in literal_values:
                print(f"  - {literal}")
        else:
            print(f"  なし")

    return {
        'variable_reads': variable_reads,
        'variable_writes': variable_writes,
        'literal_values': literal_values,
        'total_reads': sum(variable_reads.values()),
        'total_writes': sum(variable_writes.values())
    }


def extract_variables_from_expression(expression):
    """
    式から変数名を抽出
    例: "x + y" → ["x", "y"]
    """
    import re

    # 変数名のパターンを抽出（識別子）
    var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
    variables = re.findall(var_pattern, expression)

    # 組み込み関数や予約語を除外
    builtin_names = {'print', 'range', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
                     'and', 'or', 'not', 'in', 'is', 'if', 'else', 'for', 'while', 'def', 'class',
                     'True', 'False', 'None'}

    return [var for var in variables if var not in builtin_names and not var.isdigit()]


def analyze_top_level_code(file_path):
    """
    トップレベル（モジュールレベル）コードの変数使用を解析
    fast_cfgs_from_sourceを使用してモジュール全体の変数を検出
    """
    if VERBOSE_OUTPUT:
        print(f"\n{'='*40}")
        print("トップレベルコード解析 (fast_cfgs_from_source)")
        print(f"{'='*40}")

    try:
        # fast_cfgs_from_sourceでモジュール全体のCFGを取得
        all_cfgs = fast_cfgs_from_source(file_path)

        # <module> CFGを検索（エスケープされた形式も考慮）
        module_cfg = None
        module_cfg_name = None
        for cfg_name in ['<module>', '&lt;module&gt;']:
            if cfg_name in all_cfgs:
                module_cfg = all_cfgs[cfg_name]
                module_cfg_name = cfg_name
                break

        if not module_cfg:
            if VERBOSE_OUTPUT:
                print("❌ <module> CFGが見つかりませんでした")
                print(f"利用可能なCFG: {list(all_cfgs.keys())}")
            return {}

        if VERBOSE_OUTPUT:
            print(f"✅ {module_cfg_name} CFG検出: {len(module_cfg.nodes())}ノード, {len(module_cfg.edges())}エッジ")

        # モジュール内のステートメントを表示
        if VERBOSE_OUTPUT:
            print(f"\n📜 モジュールステートメント:")
        function_calls = []
        function_definitions = []

        for i, node in enumerate(module_cfg.nodes()):
            if hasattr(node, 'statements') and node.statements:
                for j, stmt in enumerate(node.statements):
                    stmt_str = str(stmt)
                    if VERBOSE_OUTPUT:
                        print(f"  [{i}-{j}] {stmt_str}")

                    # 汎用的な関数呼び出しを検出（識別子+括弧のパターン）
                    import re
                    call_pattern = r'(\w+)\s*\('
                    call_match = re.search(call_pattern, stmt_str)
                    if call_match and not any(keyword in stmt_str for keyword in ['def', 'UnsupportedStmt:', 'TYPE_REF', 'LOCAL,']):
                        function_name = call_match.group(1)
                        # 組み込み関数を除外
                        if function_name not in ['print', 'range', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple']:
                            function_calls.append({
                                'node_index': i,
                                'stmt_index': j,
                                'statement': stmt_str,
                                'function_name': function_name,
                                'node_addr': getattr(node, 'addr', 'unknown')
                            })

                    # 汎用的な関数定義を検出（= def... または deffunction パターン）
                    def_pattern = r'(\w+)\s*=\s*def(\w+)|def(\w+)'
                    def_match = re.search(def_pattern, stmt_str)
                    if def_match:
                        # どのグループにマッチしたかによって関数名を取得
                        function_name = def_match.group(1) or def_match.group(2) or def_match.group(3)
                        if function_name:
                            function_definitions.append({
                                'node_index': i,
                                'stmt_index': j,
                                'statement': stmt_str,
                                'function_name': function_name,
                                'node_addr': getattr(node, 'addr', 'unknown')
                            })

        # 関数呼び出しと定義の関連を分析
        if VERBOSE_OUTPUT:
            print(f"\n🔗 関数呼び出しと定義の関連分析:")
            print(f"📞 関数呼び出し: {len(function_calls)}個")
            for call in function_calls:
                print(f"  - {call['function_name']}() ノード[{call['node_index']}-{call['stmt_index']}] (addr:{call['node_addr']})")
                print(f"    ステートメント: {call['statement']}")

            print(f"🏗️ 関数定義: {len(function_definitions)}個")
            for defn in function_definitions:
                print(f"  - {defn['function_name']}() ノード[{defn['node_index']}-{defn['stmt_index']}] (addr:{defn['node_addr']})")
                print(f"    ステートメント: {defn['statement']}")

        # 関数名の対応関係を分析
        if function_calls and function_definitions:
            if VERBOSE_OUTPUT:
                print(f"\n🔄 関数名対応関係:")
            call_names = {call['function_name'] for call in function_calls}
            def_names = {defn['function_name'] for defn in function_definitions}

            matching_functions = call_names & def_names
            call_only = call_names - def_names
            def_only = def_names - call_names

            if matching_functions:
                if VERBOSE_OUTPUT:
                    print(f"  ✅ 呼び出し⇔定義が対応: {sorted(matching_functions)}")

                # 対応する関数の引数とパラメータの解析
                if VERBOSE_OUTPUT:
                    print(f"\n🔗 引数⇔パラメータ対応解析:")
                for func_name in matching_functions:
                    # 関数呼び出しから引数を抽出
                    call_info = next((call for call in function_calls if call['function_name'] == func_name), None)
                    def_info = next((defn for defn in function_definitions if defn['function_name'] == func_name), None)

                    if call_info and def_info:
                        if VERBOSE_OUTPUT:
                            print(f"  🎯 関数 {func_name}:")

                        # 呼び出しから引数を抽出
                        call_stmt = call_info['statement']
                        args = extract_function_arguments(call_stmt, func_name)
                        if VERBOSE_OUTPUT:
                            print(f"    📞 呼び出し: {call_stmt}")
                            print(f"    📥 引数: {args}")

                        # 関数定義からパラメータを取得（既に解析済みの関数情報を活用）
                        try:
                            functions = parse_source(file_path)
                            if func_name in functions:
                                func_obj = functions[func_name]

                                # analyze_variables_from_statementsで既に解析済みの結果を使用
                                var_analysis = analyze_variables_from_statements(func_obj)
                                params = list(var_analysis['parameters'])  # setをlistに変換

                                if VERBOSE_OUTPUT:
                                    print(f"    🏗️ 定義: {def_info['statement']}")
                                    print(f"    📤 パラメータ: {params}")

                                # 引数とパラメータの対応
                                if len(args) == len(params):
                                    if VERBOSE_OUTPUT:
                                        print(f"    🔗 対応関係:")
                                    for i, (arg, param) in enumerate(zip(args, params)):
                                        if VERBOSE_OUTPUT:
                                            print(f"      [{i}] 引数 '{arg}' → パラメータ '{param}'")
                                            print(f"          ✅ 値 {arg} がパラメータ {param} に渡される")
                                else:
                                    if VERBOSE_OUTPUT:
                                        print(f"    ⚠️ 引数数({len(args)})とパラメータ数({len(params)})が不一致")
                                        if len(args) > 0 and len(params) > 0:
                                            print(f"    🔍 部分対応:")
                                            min_len = min(len(args), len(params))
                                            for i in range(min_len):
                                                print(f"      [{i}] 引数 '{args[i]}' → パラメータ '{params[i]}'")
                        except Exception as e:
                            if VERBOSE_OUTPUT:
                                print(f"    ❌ パラメータ取得エラー: {e}")
                                import traceback
                                traceback.print_exc()

            if call_only:
                if VERBOSE_OUTPUT:
                    print(f"  📞 呼び出しのみ: {sorted(call_only)}")
            if def_only:
                if VERBOSE_OUTPUT:
                    print(f"  🏗️ 定義のみ: {sorted(def_only)}")

        # 🆕 トップレベル変数読み込み・書き込み解析
        if VERBOSE_OUTPUT:
            print(f"\n📊 トップレベル変数読み込み・書き込み解析:")
        top_level_vars = analyze_top_level_variables(module_cfg, function_calls)

        # ノードの詳細属性を調査
        if VERBOSE_OUTPUT:
            print(f"\n🔍 ノード詳細属性調査:")
            for i, node in enumerate(module_cfg.nodes()):
                print(f"\nノード {i} (addr: {getattr(node, 'addr', 'unknown')}):")
                print(f"  型: {type(node).__name__}")

                # 利用可能な属性を表示
                attrs = [attr for attr in dir(node) if not attr.startswith('_')]
                print(f"  属性: {', '.join(attrs[:10])}")
                if len(attrs) > 10:
                    print(f"    ... 他{len(attrs)-10}個")

                # 重要な属性の値を表示
                important_attrs = ['addr', 'code', 'type', 'name', 'line_number']
                for attr in important_attrs:
                    if hasattr(node, attr):
                        value = getattr(node, attr)
                        print(f"  {attr}: {value}")

                # ステートメント詳細
                if hasattr(node, 'statements') and node.statements:
                    print(f"  statements数: {len(node.statements)}")
                    for j, stmt in enumerate(node.statements[:3]):  # 最初の3つだけ表示
                        print(f"    [{j}] {type(stmt).__name__}: {str(stmt)[:100]}")
                    if len(node.statements) > 3:
                        print(f"    ... 他{len(node.statements)-3}個のステートメント")

                # 最初の3ノードだけ詳細表示
                if i >= 2:
                    print(f"  ... 他{len(module_cfg.nodes())-3}個のノード")
                    break

        # CFGエッジ情報を調査
        if VERBOSE_OUTPUT:
            print(f"\n🔗 CFGエッジ関係:")
            print(f"エッジ数: {len(module_cfg.edges())}")
            for i, (src, dst) in enumerate(module_cfg.edges()):
                src_addr = getattr(src, 'addr', 'unknown')
                dst_addr = getattr(dst, 'addr', 'unknown')
                edge_data = module_cfg.get_edge_data(src, dst)
                print(f"  エッジ {i}: {src_addr} -> {dst_addr}")
                if edge_data:
                    print(f"    データ: {edge_data}")

                # 最初の5エッジだけ表示
                if i >= 4:
                    print(f"  ... 他{len(module_cfg.edges())-5}個のエッジ")
                    break

        # トップレベル変数を抽出
        top_level_vars = extract_top_level_variables(module_cfg)
        if VERBOSE_OUTPUT:
            print(f"\n🎯 トップレベル変数: {sorted(top_level_vars)}")

        # トップレベル変数の読み込み・書き込み数を解析
        if top_level_vars:
            top_level_reads = count_top_level_reads(module_cfg, top_level_vars)
            top_level_writes = count_top_level_writes(module_cfg, top_level_vars)

            if VERBOSE_OUTPUT:
                print(f"\n📖 トップレベル読み込み数:")
                total_reads = 0
                for var in sorted(top_level_vars):
                    count = top_level_reads[var]
                    total_reads += count
                    print(f"  - {var}: {count}回")

                print(f"\n✏️ トップレベル書き込み数:")
                total_writes = 0
                for var in sorted(top_level_vars):
                    count = top_level_writes[var]
                    total_writes += count
                    print(f"  - {var}: {count}回")

                print(f"\n📊 トップレベル統計:")
                print(f"  変数種類数: {len(top_level_vars)}個")
                print(f"  総読み込み数: {total_reads}回")
                print(f"  総書き込み数: {total_writes}回")

                if top_level_vars:
                    max_reads = max(top_level_reads.values())
                    max_writes = max(top_level_writes.values())
                    print(f"  最大読み込み数: {max_reads}回")
                    print(f"  最大書き込み数: {max_writes}回")
            else:
                # VERBOSE_OUTPUTがFalseの場合でも統計は計算
                total_reads = sum(top_level_reads.values())
                total_writes = sum(top_level_writes.values())

            return {
                'variables': top_level_vars,
                'reads': top_level_reads,
                'writes': top_level_writes,
                'variable_count': len(top_level_vars),
                'total_reads': total_reads,
                'total_writes': total_writes,
                'max_reads': max(top_level_reads.values()) if top_level_vars else 0,
                'max_writes': max(top_level_writes.values()) if top_level_vars else 0,
                'top_level_analysis': top_level_vars  # 新しいトップレベル分析結果を追加
            }
        else:
            if VERBOSE_OUTPUT:
                print("⚠️ トップレベル変数が見つかりませんでした")
            return {'top_level_analysis': top_level_vars}  # 空でも分析結果を返す

    except Exception as e:
        print(f"❌ トップレベル解析エラー: {e}")
        import traceback
        traceback.print_exc()
        return {}


def extract_top_level_variables(module_cfg):
    """
    モジュールレベルのCFGから変数を抽出
    関数名は除外し、実際のデータ変数のみを対象とする
    """
    import builtins
    import re

    builtin_names = set(dir(builtins))
    builtin_names.update([
        'range', 'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
        'abs', 'max', 'min', 'sum', 'all', 'any', 'enumerate', 'zip', 'map', 'filter',
        'sorted', 'reversed', 'iter', 'next', 'open', 'input', 'round', 'pow', 'divmod'
    ])

    # pyjoernのCFGメタデータを除外
    exclude_keywords = {
        'FUNCTION_START', 'FUNCTION_END', 'TYPE_REF', 'UnsupportedStmt',
        'IDENTIFIER', 'LITERAL', 'BLOCK', 'CONTROL_STRUCTURE',
        'builtins', '__builtins__', '__name__', '__main__',
        'def', 'defexample', 'quot', 'amp', 'lt', 'gt'
    }

    variables = set()

    for node in module_cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # pyjoernのメタデータステートメントを除外
                if any(keyword in stmt_str for keyword in ['<UnsupportedStmt:', 'FUNCTION_', 'TYPE_REF', '__builtins__']):
                    continue

                # 関数呼び出しの引数は変数として扱う（例: example(x) の x）
                # しかし、関数名（example）自体は変数ではない
                func_call_pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)'
                func_call_match = re.match(func_call_pattern, stmt_str)
                if func_call_match:
                    # 引数部分から変数を抽出
                    args_part = func_call_match.group(2)
                    if args_part:
                        # 引数から変数を抽出（数値リテラルは除外）
                        var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
                        arg_matches = re.findall(var_pattern, args_part)
                        for var in arg_matches:
                            if (var.isidentifier() and
                                var not in builtin_names and
                                var not in exclude_keywords and
                                not var.startswith('__') and
                                len(var) > 1):
                                variables.add(var)
                    continue

                # 関数定義と条件式は変数として扱わない
                if ('def' in stmt_str or '==' in stmt_str):
                    continue

                # その他の変数使用（慎重に）
                var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
                matches = re.findall(var_pattern, stmt_str)
                for match in matches:
                    if (match.isidentifier() and
                        match not in builtin_names and
                        match not in exclude_keywords and
                        not match.startswith('__') and
                        len(match) > 1):  # 一文字変数は除外
                        # さらに厳格なフィルタリング
                        if not any(x in match.lower() for x in ['tmp', 'stmt', 'ref', 'start', 'end']):
                            variables.add(match)

    return variables


def count_top_level_reads(module_cfg, top_level_vars):
    """
    トップレベルでの変数読み込み数をカウント
    """
    import re

    read_counts = {var: 0 for var in top_level_vars}

    for node in module_cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # pyjoernのメタデータステートメントを除外
                if any(keyword in stmt_str for keyword in ['<UnsupportedStmt:', 'FUNCTION_', 'TYPE_REF', '__builtins__']):
                    continue

                for var in top_level_vars:
                    # 関数呼び出しでの引数としての読み込み
                    func_call_pattern = rf'{var}\s*\('
                    if re.search(func_call_pattern, stmt_str):
                        read_counts[var] += 1
                        continue

                    # 関数の引数としての読み込み
                    arg_pattern = rf'\w+\s*\(\s*[^)]*{var}[^)]*\)'
                    if re.search(arg_pattern, stmt_str):
                        read_counts[var] += 1
                        continue

                    # 条件文での読み込み
                    if var in stmt_str and '==' in stmt_str:
                        read_counts[var] += 1
                        continue

                    # その他の読み込み（代入の右辺など）
                    # 代入の左辺でない場合
                    assignment_pattern = rf'^[^=]*{var}\s*='
                    if not re.search(assignment_pattern, stmt_str) and var in stmt_str:
                        read_counts[var] += 1

    return read_counts


def count_top_level_writes(module_cfg, top_level_vars):
    """
    トップレベルでの変数書き込み数をカウント
    """
    import re

    write_counts = {var: 0 for var in top_level_vars}

    for node in module_cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # pyjoernのメタデータステートメントを除外
                if any(keyword in stmt_str for keyword in ['<UnsupportedStmt:', 'FUNCTION_', 'TYPE_REF', '__builtins__']):
                    continue

                for var in top_level_vars:
                    # 関数定義での書き込み: example = defexample(...)
                    func_def_pattern = rf'{var}\s*=\s*def{var}'
                    if re.search(func_def_pattern, stmt_str):
                        write_counts[var] += 1
                        continue

                    # 通常の代入での書き込み
                    assignment_pattern = rf'{var}\s*=\s*[^=]'
                    if re.search(assignment_pattern, stmt_str) and f'def{var}' not in stmt_str:
                        write_counts[var] += 1

    return write_counts


def analyze_compound_assignments(func_obj, var_analysis):
    """
    複合代入演算子の使用を分析
    +=, -=, *=, /= などの演算子を検出し、読み込みと書き込みの両方をカウント
    """
    import re

    if VERBOSE_OUTPUT:
        print(f"\n🔄 複合代入演算子解析:")

    # 独自定義変数のリスト
    user_defined_vars = var_analysis['parameters'] | var_analysis['local_vars']

    if not user_defined_vars:
        if VERBOSE_OUTPUT:
            print("  独自定義変数が見つかりません")
        return {}

    # 複合代入演算子のパターン
    compound_operators = ['+=', '-=', '*=', '/=', '//=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=']

    compound_assignments = {var: [] for var in user_defined_vars}
    all_compound_refs = []  # デバッグ用

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # pyjoernの内部表現を除外
                exclude_patterns = [
                    r'<UnsupportedStmt:.*IDENTIFIER,',     # 低レベル識別子表現
                    r'<UnsupportedStmt:.*LITERAL,',        # リテラル表現
                    r'<UnsupportedStmt:.*BLOCK,',          # ブロック表現
                    r'PARAM,',                             # パラメータ定義
                    r'LOCAL,',                             # ローカル変数定義
                ]

                # 除外パターンに一致する場合はスキップ
                should_exclude = False
                for pattern in exclude_patterns:
                    if re.search(pattern, stmt_str, re.IGNORECASE):
                        should_exclude = True
                        break

                if should_exclude:
                    continue

                # 各変数について複合代入演算子をチェック
                for var in user_defined_vars:
                    for op in compound_operators:
                        # var += ... の形式を検出
                        pattern = rf'\b{re.escape(var)}\s*{re.escape(op)}\s*'
                        if re.search(pattern, stmt_str):
                            compound_info = {
                                'variable': var,
                                'operator': op,
                                'statement': stmt_str[:100],
                                'node_addr': node.addr
                            }
                            compound_assignments[var].append(compound_info)
                            all_compound_refs.append(compound_info)

    # 結果表示
    total_compound_ops = sum(len(ops) for ops in compound_assignments.values())
    if VERBOSE_OUTPUT:
        print(f"  🎯 複合代入演算子の使用数:")

        for var in sorted(user_defined_vars):
            ops = compound_assignments[var]
            if ops:
                print(f"    - {var}: {len(ops)}回")
                for op_info in ops:
                    print(f"      {op_info['operator']} (ノード {op_info['node_addr']})")
            else:
                print(f"    - {var}: 0回")

        print(f"  📊 総複合代入演算子数: {total_compound_ops}回")

    # 詳細デバッグ情報（コメントアウト）
    # if all_compound_refs:
    #     print(f"\n  🔍 複合代入詳細 (デバッグ情報):")
    #     for ref in all_compound_refs:
    #         print(f"    {ref['variable']} {ref['operator']} (ノード {ref['node_addr']})")
    #         print(f"      Statement: {ref['statement'][:80]}...")

    return compound_assignments


def analyze_variable_reads(func_obj, var_analysis, compound_assignments=None):
    """
    独自定義変数の読み込み数を解析
    代入演算子の左辺以外で登場する変数の数をカウント
    複合代入演算子の場合は読み込みとしてもカウント
    """
    import re

    if VERBOSE_OUTPUT:
        print(f"\n📖 変数読み込み数解析:")

    # 独自定義変数のリスト
    user_defined_vars = var_analysis['parameters'] | var_analysis['local_vars']

    if not user_defined_vars:
        if VERBOSE_OUTPUT:
            print("  独自定義変数が見つかりません")
        return {}

    # 各変数の読み込み数をカウント
    read_counts = {var: 0 for var in user_defined_vars}
    all_references = []  # デバッグ用

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # 変数の参照を検出
                for var in user_defined_vars:
                    var_refs = count_variable_references(stmt_str, var, node.addr)
                    if var_refs > 0:  # カウントされた場合のみ記録
                        read_counts[var] += var_refs

                        # デバッグ用: 参照詳細を記録
                        all_references.append({
                            'variable': var,
                            'count': var_refs,
                            'statement': stmt_str[:100],  # 長い文は切り詰め
                            'node_addr': node.addr
                        })

    # 🔄 複合代入演算子による読み込み数を加算（引数で渡された結果を使用）
    if compound_assignments:
        for var in user_defined_vars:
            compound_count = len(compound_assignments.get(var, []))
            if compound_count > 0:
                read_counts[var] += compound_count
                if VERBOSE_OUTPUT:
                    print(f"  🔄 {var}の複合代入演算子による読み込み: +{compound_count}回")

    # 結果表示
    if VERBOSE_OUTPUT:
        print(f"  🎯 独自定義変数の読み込み数:")
        total_reads = 0
        for var in sorted(user_defined_vars):
            count = read_counts[var]
            total_reads += count
            print(f"    - {var}: {count}回")

        print(f"  📊 総読み込み数: {total_reads}回")

    # 詳細デバッグ情報（コメントアウト）
    print(f"\n  🔍 読み込み詳細 (デバッグ情報):")
    for ref in all_references:
        print(f"    {ref['variable']}: {ref['count']}回 (ノード {ref['node_addr']})")
        print(f"      Statement: {ref['statement'][:80]}...")

    return read_counts


def analyze_variable_writes(func_obj, var_analysis, compound_assignments=None):
    """
    独自定義変数の書き込み数を解析
    代入演算子の左辺、複合代入演算子、for文のループ変数をカウント
    """
    import re

    if VERBOSE_OUTPUT:
        print(f"\n✏️ 変数書き込み数解析:")

    # 独自定義変数のリスト
    user_defined_vars = var_analysis['parameters'] | var_analysis['local_vars']

    if not user_defined_vars:
        if VERBOSE_OUTPUT:
            print("  独自定義変数が見つかりません")
        return {}

    # ループ変数を特定（複数の方法で検出）
    loop_variables = set()
    iterator_variables = set()
    range_loop_candidates = set()

    if VERBOSE_OUTPUT:
        print(f"\n  🔍 ループ変数の特定:")

    # 方法1: LOCAL定義でloop関連の型を持つ変数を特定（コメントアウト）
    # for node in func_obj.ast.nodes:
    #     if hasattr(node, 'statements') and node.statements:
    #         for stmt in node.statements:
    #             stmt_str = str(stmt)
    #
    #             # LOCAL定義でloop関連の型を持つ変数を特定
    #             if 'LOCAL,' in stmt_str:
    #                 try:
    #                     local_part = stmt_str.split('LOCAL,')[1]
    #                     var_name = local_part.split(':')[0] if ':' in local_part else local_part.split('>')[0]
    #
    #                     if var_name in user_defined_vars:
    #                         # 型情報をチェック
    #                         if any(keyword in stmt_str.lower() for keyword in ['__iter__', '__next__', 'returnvalue']):
    #                             loop_variables.add(var_name)
    #                             print(f"    - {var_name}: ループ変数として検出 (型情報)")
    #                             print(f"      型情報: {stmt_str}")
    #                         elif 'iterator' in stmt_str.lower() or '__iter__' in stmt_str:
    #                             iterator_variables.add(var_name)
    #                             print(f"    - {var_name}: イテレータ変数として検出")
    #                 except:
    #                     pass

    # 方法2: range()関連のステートメントからループ変数を推定（コメントアウト）
    # print(f"\n  🔍 range()ベースのループ変数推定:")
    # for node in func_obj.ast.nodes:
    #     if hasattr(node, 'statements') and node.statements:
    #         for stmt in node.statements:
    #             stmt_str = str(stmt)
    #
    #             # range()呼び出しと関連するANY型のLOCAL変数を関連付け
    #             if 'range(' in stmt_str and any(var in stmt_str for var in user_defined_vars):
    #                 print(f"    Range関連ステートメント (ノード {node.addr}): {stmt_str}")
    #
    #                 # 同じノードでANY型のLOCAL変数を探す
    #                 for stmt2 in node.statements:
    #                     stmt2_str = str(stmt2)
    #                     if 'LOCAL,' in stmt2_str and ':ANY' in stmt2_str:
    #                         try:
    #                             local_part = stmt2_str.split('LOCAL,')[1]
    #                             var_name = local_part.split(':')[0]
    #                             if var_name in user_defined_vars and var_name not in loop_variables:
    #                                 range_loop_candidates.add(var_name)
    #                                 print(f"      候補変数: {var_name} (ANY型)")
    #                         except:
    #                             pass

    # 追加: 条件分岐内のrange()ループ変数も検出（コメントアウト）
    # print(f"\n  🔍 条件分岐内のrange()ループ変数推定:")
    # for node in func_obj.ast.nodes:
    #     if hasattr(node, 'statements') and node.statements:
    #         # ノード内のすべてのANY型LOCAL変数を収集
    #         any_locals = set()
    #         has_range = False
    #
    #         for stmt in node.statements:
    #             stmt_str = str(stmt)
    #
    #             # range()があるかチェック
    #             if 'range(' in stmt_str:
    #                 has_range = True
    #
    #             # ANY型のLOCAL変数を収集
    #             if 'LOCAL,' in stmt_str and ':ANY' in stmt_str:
    #                 try:
    #                     local_part = stmt_str.split('LOCAL,')[1]
    #                     var_name = local_part.split(':')[0]
    #                     if var_name in user_defined_vars and not var_name.startswith('tmp'):
    #                         any_locals.add(var_name)
    #                 except:
    #                     pass
    #
    #         # range()があるノードのANY型変数は候補とする
    #         if has_range and any_locals:
    #             print(f"    ノード {node.addr}: range()あり + ANY型変数 {sorted(any_locals)}")
    #             for var in any_locals:
    #                 if var not in loop_variables:
    #                     range_loop_candidates.add(var)
    #                     print(f"      候補追加: {var}")    # range()ループ候補を分析して確定（コメントアウト）
    # for var in range_loop_candidates:
    #     # より詳細な分析：その変数がrange()と同じノードに出現し、
    #     # かつ他の証拠（print文での使用など）があるかチェック
    #     evidence_count = 0
    #
    #     for node in func_obj.ast.nodes:
    #         if hasattr(node, 'statements') and node.statements:
    #             for stmt in node.statements:
    #                 stmt_str = str(stmt)
    #                 if var in stmt_str:
    #                     if 'range(' in stmt_str:
    #                         evidence_count += 2  # range()との関連は強い証拠
    #                     elif f'print({var})' in stmt_str:
    #                         evidence_count += 1  # ループ内での使用
    #                     elif f'{var}%' in stmt_str or f'{var}*' in stmt_str:
    #                         evidence_count += 1  # 演算での使用
    #
    #     if evidence_count >= 2:  # 十分な証拠がある場合
    #         loop_variables.add(var)
    #         print(f"    - {var}: range()ループ変数として確定 (証拠度: {evidence_count})")
    #     else:
    #         print(f"    - {var}: range()ループ変数候補 (証拠度: {evidence_count}, 要検討)")

    # 方法3: 静的解析による強制的なループ変数検出（コメントアウト）
    # print(f"\n  🔍 静的解析によるループ変数検出:")
    # # i, j などのANY型変数で、読み込み数が1以上あり、通常の代入がない変数は
    # # ループ変数の可能性が高い
    # for var in user_defined_vars:
    #     if var not in loop_variables and not var.startswith('tmp'):
    #         # この変数のLOCAL定義を探す
    #         var_type = None
    #         for node in func_obj.ast.nodes:
    #             if hasattr(node, 'statements') and node.statements:
    #                 for stmt in node.statements:
    #                     stmt_str = str(stmt)
    #                     if f'LOCAL,{var}:ANY' in stmt_str:
    #                         var_type = 'ANY'
    #                         break
    #
    #         # ANY型で読み込みがあり、通常の代入がない変数を検出
    #         if var_type == 'ANY':
    #             has_reads = False
    #             has_assignment = False
    #
    #             # 読み込みチェック
    #             for node in func_obj.ast.nodes:
    #                 if hasattr(node, 'statements') and node.statements:
    #                     for stmt in node.statements:
    #                         stmt_str = str(stmt)
    #                         # UnsupportedStmt以外で変数が使用されているかチェック
    #                         if not stmt_str.startswith('<UnsupportedStmt:') and var in stmt_str:
    #                             if f'print({var})' in stmt_str or f'{var}%' in stmt_str or f'{var}*' in stmt_str:
    #                                 has_reads = True
    #
    #             # 通常の代入チェック（=は除外、for文は別途チェック）
    #             for node in func_obj.ast.nodes:
    #                 if hasattr(node, 'statements') and node.statements:
    #                     for stmt in node.statements:
    #                         stmt_str = str(stmt)
    #                         if f'{var} =' in stmt_str and not stmt_str.startswith('<UnsupportedStmt:') and 'for ' not in stmt_str:
    #                             has_assignment = True
    #
    #             # 読み込みはあるが通常の代入がない → ループ変数の可能性
    #             if has_reads and not has_assignment:
    #                 loop_variables.add(var)
    #                 print(f"    - {var}: ANY型+読み込みあり+代入なし → ループ変数と推定")
    #             elif has_reads:
    #                 print(f"    - {var}: ANY型+読み込みあり+代入あり → 通常変数")
    #             else:
    #                 print(f"    - {var}: ANY型+読み込みなし → 未使用変数")

    # 方法4: for文の直接検出によるループ変数識別
    if VERBOSE_OUTPUT:
        print(f"\n  🔍 for文パターンマッチングによるループ変数検出:")

    # デバッグ: i, j, l を含む全てのステートメントを調査
    if VERBOSE_OUTPUT:
        print(f"\n  🔍 デバッグ: i, j, l を含む全ステートメント調査:")
    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                # i, j, l のいずれかを含むステートメントを全て表示
                if any(var in stmt_str for var in ['i', 'j', 'l']):
                    if VERBOSE_OUTPUT:
                        print(f"    ノード {node.addr}: {stmt_str}")
                        print(f"      Type: {type(stmt).__name__}")

                        # 特にfor文に関連しそうなキーワードをチェック
                        for_keywords = ['for', 'FOR', 'CONTROL_STRUCTURE', 'iterator', 'iter']
                        found_keywords = [kw for kw in for_keywords if kw.lower() in stmt_str.lower()]
                        if found_keywords:
                            print(f"      🎯 for関連キーワード: {found_keywords}")

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                # for文のパターンを直接検出
                import re

                # デバッグ: すべてのstatementを詳しく調査
                if any(var in stmt_str for var in ['i', 'j', 'l']) and 'for' in stmt_str.lower():
                    if VERBOSE_OUTPUT:
                        print(f"    🔍 for文関連ステートメント発見 (ノード {node.addr}):")
                        print(f"      Full Statement: {stmt_str}")
                        print(f"      Statement Type: {type(stmt).__name__}")

                for var in user_defined_vars:
                    # "for var in" パターンをチェック（UnsupportedStmtも含む）
                    for_pattern = rf'for\s+{re.escape(var)}\s+in\s+'
                    if re.search(for_pattern, stmt_str, re.IGNORECASE):
                        if var not in loop_variables:
                            loop_variables.add(var)
                            if VERBOSE_OUTPUT:
                                print(f"    - {var}: for文パターンで検出 → ループ変数確定")
                                print(f"      Statement: {stmt_str[:100]}...")
                        break

                    # CONTROL_STRUCTURE内のfor文も検出
                    if 'CONTROL_STRUCTURE,FOR' in stmt_str and var in stmt_str:
                        if var not in loop_variables:
                            loop_variables.add(var)
                            if VERBOSE_OUTPUT:
                                print(f"    - {var}: CONTROL_STRUCTURE内のfor文で検出 → ループ変数確定")
                                print(f"      Statement: {stmt_str[:100]}...")
                        break

    if VERBOSE_OUTPUT:
        print(f"\n  ✅ 確定したループ変数: {sorted(loop_variables)}")

    # for文関連のステートメントを詳しく調査（簡潔版）（コメントアウト）
    # print(f"\n  🔍 for文構造の概要:")
    # range_calls = []
    # for node in func_obj.ast.nodes:
    #     if hasattr(node, 'statements') and node.statements:
    #         for stmt in node.statements:
    #             stmt_str = str(stmt)
    #             # range()呼び出しを特定
    #             if 'range(' in stmt_str and 'tmp' in stmt_str and '=' in stmt_str:
    #                 range_calls.append({
    #                     'node_addr': node.addr,
    #                     'statement': stmt_str
    #                 })
    #
    # for i, range_call in enumerate(range_calls):
    #     print(f"    Range呼び出し {i+1} (ノード {range_call['node_addr']}):")
    #     print(f"      {range_call['statement']}")

    # 各変数の書き込み数をカウント
    write_counts = {var: 0 for var in user_defined_vars}
    all_writes = []  # デバッグ用

    # 重複を防ぐため、既に検出したループ変数の書き込みを追跡
    detected_loop_writes = set()  # (変数名, ノードアドレス) のタプルを格納

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # 変数の書き込みを検出
                for var in user_defined_vars:
                    write_count = count_variable_writes(stmt_str, var, node.addr, detected_loop_writes)

                    # ループ変数の場合は追加で書き込みとしてカウント
                    if write_count == 0 and var in loop_variables:
                        # 重複チェック：同じ変数の同じノードでの書き込みは1回だけカウント
                        write_key = (var, node.addr)

                        # LOCAL定義でループ変数と判定された場合は1回の書き込みとしてカウント
                        if f'LOCAL,{var}:' in stmt_str and write_key not in detected_loop_writes:
                            write_count = 1
                            detected_loop_writes.add(write_key)
                            if VERBOSE_OUTPUT:
                                print(f"      ⭐ ループ変数書き込み検出 (LOCAL定義): {var} (ノード {node.addr})")

                        # for文パターンでも検出
                        import re
                        for_pattern = rf'for\s+{re.escape(var)}\s+in\s+'
                        if re.search(for_pattern, stmt_str, re.IGNORECASE) and write_key not in detected_loop_writes:
                            write_count = 1
                            detected_loop_writes.add(write_key)
                            if VERBOSE_OUTPUT:
                                print(f"      ⭐ ループ変数書き込み検出 (for文パターン): {var} (ノード {node.addr})")

                    if write_count > 0:  # カウントされた場合のみ記録
                        write_counts[var] += write_count

                        # デバッグ用: 書き込み詳細を記録
                        all_writes.append({
                            'variable': var,
                            'count': write_count,
                            'statement': stmt_str[:100],  # 長い文は切り詰め
                            'node_addr': node.addr,
                            'is_loop_var': var in loop_variables
                        })

    # 結果表示
    if VERBOSE_OUTPUT:
        print(f"\n  🎯 独自定義変数の書き込み数:")
        total_writes = 0
        for var in sorted(user_defined_vars):
            count = write_counts[var]
            total_writes += count
            loop_mark = " [ループ変数]" if var in loop_variables else ""
            print(f"    - {var}: {count}回{loop_mark}")

        print(f"  📊 総書き込み数: {total_writes}回")

    # 詳細デバッグ情報（コメントアウト）
    print(f"\n  🔍 書き込み詳細 (デバッグ情報):")
    for write in all_writes:
        loop_mark = " [ループ変数]" if write['is_loop_var'] else ""
        print(f"    {write['variable']}: {write['count']}回{loop_mark} (ノード {write['node_addr']})")
        print(f"      Statement: {write['statement'][:80]}...")

    return write_counts


def count_variable_writes(stmt_str, var_name, node_addr, detected_loop_writes):
    """
    ステートメント内での変数書き込み回数をカウント
    代入演算子の左辺、複合代入演算子、for文のループ変数を検出
    """
    import re

    # まずfor文パターンを先にチェック（UnsupportedStmt内でも検出）
    for_patterns = [
        # 通常のfor文パターン
        rf'for\s+{re.escape(var_name)}\s+in\s+',
        # CONTROL_STRUCTURE内のfor文
        rf'CONTROL_STRUCTURE,FOR,.*for\s+{re.escape(var_name)}\s+in\s+',
        # UnsupportedStmt内のfor文
        rf'<UnsupportedStmt:.*for\s+{re.escape(var_name)}\s+in\s+',
    ]

    # for文パターンが見つかったら、除外チェックをスキップ
    is_for_loop = False
    for pattern in for_patterns:
        if re.search(pattern, stmt_str, re.IGNORECASE):
            is_for_loop = True
            break

    if is_for_loop:
        return 1  # for文のループ変数なので書き込み1回

    # ⭐ 重要: tmp.__next__()からの代入（ループ変数の実際の書き込み）を検出
    loop_assignment_pattern = rf'\b{re.escape(var_name)}\s*=\s*tmp\d+\.__next__\(\)'
    if re.search(loop_assignment_pattern, stmt_str):
        # 重複チェック：同じ変数の同じノードでの書き込みは1回だけカウント
        write_key = (var_name, node_addr)
        if write_key not in detected_loop_writes:
            detected_loop_writes.add(write_key)
            print(f"      ⭐ ループ変数書き込み検出 (tmp.__next__代入): {var_name} (ノード {node_addr})")
            return 1
        else:
            # 既に検出済みの場合はカウントしない
            return 0

    # pyjoernの内部表現による重複を避けるため、低レベル表現のみ除外
    # ただし、for文の情報は保持する
    exclude_patterns = [
        r'<UnsupportedStmt:.*IDENTIFIER,',     # 低レベル識別子表現
        r'<UnsupportedStmt:.*LITERAL,',        # リテラル表現
        r'<UnsupportedStmt:.*BLOCK,',          # ブロック表現
        r'PARAM,',                             # パラメータ定義
        r'LOCAL,',                             # ローカル変数定義
        r'CONTROL_STRUCTURE',                  # 制御構造（for文以外）
        r"^\s*tmp\d+\s*=",                     # 一時変数への代入
        r"^\s*\w+\)\s*$",                      # 単一の変数名＋閉じ括弧のみ
    ]

    # 除外パターンに一致する場合はカウントしない
    for pattern in exclude_patterns:
        if re.search(pattern, stmt_str, re.IGNORECASE):
            return 0

    # 書き込みパターンの検出
    write_patterns = [
        # 通常の代入演算子 (var = ...)
        rf'\b{re.escape(var_name)}\s*=\s*[^=]',

        # 複合代入演算子 (var +=, -=, *=, /=, etc.)
        rf'\b{re.escape(var_name)}\s*(\+=|-=|\*=|/=|//=|%=|\*\*=|&=|\|=|\^=|<<=|>>=)\s*',
    ]

    # 書き込みパターンに一致する場合は1回としてカウント
    for pattern in write_patterns:
        if re.search(pattern, stmt_str, re.IGNORECASE):
            return 1

    return 0


def count_variable_references(stmt_str, var_name, node_addr):
    """
    ステートメント内での変数参照回数をカウント
    代入の左辺は除外し、重複も除去する
    複合代入演算子の場合は読み込みとしてカウント
    ループ変数は条件判定での読み込みも追加カウント
    """
    import re

    # pyjoernの内部表現による重複を避けるため、低レベル表現のみ除外
    # 有効な変数読み込みは保持する

    # 除外すべきステートメントパターン（pyjoern内部表現のみ）
    exclude_patterns = [
        r'PARAM,',                             # パラメータ定義
        r'LOCAL,',                             # ローカル変数定義
        r'CONTROL_STRUCTURE',                  # 制御構造
        r"^\s*tmp\d+\s*=",                     # 一時変数への代入
        r"^\s*\w+\)\s*$",                      # 単一の変数名＋閉じ括弧のみ
        r"__next__\(\)",                       # イテレータ内部メソッド
        r'<UnsupportedStmt:',                  # UnsupportedStmt（複合代入演算子を含む）
    ]

    # 除外パターンに一致する場合はカウントしない
    for pattern in exclude_patterns:
        if re.search(pattern, stmt_str, re.IGNORECASE):
            return 0

    # for文のループ変数の特殊処理
    # for var in range(...): の場合、varは条件判定で暗黙的に読み込まれる
    for_loop_pattern = rf'for\s+{re.escape(var_name)}\s+in\s+'
    if re.search(for_loop_pattern, stmt_str):
        return 1  # ループ変数の条件判定での読み込み

    # 通常の代入文の検出（左辺は読み込みではない）
    assignment_patterns = [
        rf'{re.escape(var_name)}\s*=\s*[^=]',  # var = ... (==, !=は除外)
    ]

    # 通常の代入文の場合は除外
    for pattern in assignment_patterns:
        if re.search(pattern, stmt_str):
            return 0

    # 変数名が含まれているかチェック
    var_pattern = rf'\b{re.escape(var_name)}\b'
    if re.search(var_pattern, stmt_str):
        return 1

    return 0
def analyze_variables_from_statements(func_obj):
    """
    statements属性から変数情報を抽出・分析
    実行結果で分かったstatements構造を基に変数を特定
    """
    if VERBOSE_OUTPUT:
        print(f"\n🔍 変数解析 (statements基準):")

    # builtinsライブラリで組み込み識別子を取得
    import builtins
    builtin_names = set(dir(builtins))

    # 追加の組み込み関数/変数
    builtin_names.update([
        'range', 'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
        'abs', 'max', 'min', 'sum', 'all', 'any', 'enumerate', 'zip', 'map', 'filter',
        'sorted', 'reversed', 'iter', 'next', 'open', 'input', 'round', 'pow', 'divmod'
    ])

    # 変数情報を収集
    parameters = set()
    local_vars = set()
    builtin_funcs = set()
    control_structures = []

    # デバッグ用: すべてのLOCAL変数の詳細情報
    all_local_details = []

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # パラメータの抽出: <UnsupportedStmt: (PARAM,x)<SUB>1</SUB>>
                if 'PARAM,' in stmt_str:
                    try:
                        # PARAM,の後ろから)までを抽出
                        param_part = stmt_str.split('PARAM,')[1]
                        param_name = param_part.split(')')[0] if ')' in param_part else param_part.split('<')[0]
                        if param_name and param_name.isidentifier():
                            parameters.add(param_name)
                    except:
                        pass

                # ローカル変数の抽出: <UnsupportedStmt: LOCAL,i:ANY>
                elif 'LOCAL,' in stmt_str:
                    try:
                        # LOCAL,の後ろから:までを抽出
                        local_part = stmt_str.split('LOCAL,')[1]
                        var_name = local_part.split(':')[0] if ':' in local_part else local_part.split('>')[0]

                        # デバッグ情報を保存
                        all_local_details.append({
                            'variable': var_name,
                            'full_statement': stmt_str,
                            'node_addr': node.addr,
                            'is_temp': var_name.startswith('tmp')
                        })

                        if var_name and var_name.isidentifier():
                            if var_name in builtin_names:
                                builtin_funcs.add(var_name)
                            else:
                                local_vars.add(var_name)
                    except:
                        pass

                # 制御構造の抽出
                elif 'CONTROL_STRUCTURE' in stmt_str:
                    control_structures.append(stmt_str)

    # デバッグ情報を表示（コメントアウト）
    # print(f"  🔍 デバッグ: すべてのLOCAL変数詳細:")
    # for detail in all_local_details:
    #     temp_mark = " [一時変数]" if detail['is_temp'] else ""
    #     print(f"    - {detail['variable']}{temp_mark}")
    #     print(f"      ノード: {detail['node_addr']}, Statement: {detail['full_statement']}")

    # tmpで始まる一時変数を除外した本当のユーザー定義変数
    real_local_vars = {var for var in local_vars if not var.startswith('tmp')}
    excluded_tmp_vars = local_vars - real_local_vars    # 結果表示
    if VERBOSE_OUTPUT:
        print(f"  📋 パラメータ: {len(parameters)}個")
        if parameters:
            for param in sorted(parameters):
                print(f"    - {param}")
        else:
            print(f"    なし")

        print(f"  🎯 ユーザー定義ローカル変数: {len(real_local_vars)}個")
        if real_local_vars:
            for var in sorted(real_local_vars):
                print(f"    - {var}")
        else:
            print(f"    なし")

        if excluded_tmp_vars:
            print(f"  ⚠️  除外された一時変数: {len(excluded_tmp_vars)}個")
            for var in sorted(excluded_tmp_vars):
                print(f"    - {var} (pyjoern内部生成)")

        print(f"  🔧 組み込み関数/変数: {len(builtin_funcs)}個")
        if builtin_funcs:
            for func in sorted(builtin_funcs):
                print(f"    - {func}")
        else:
            print(f"    なし")

        print(f"  🔀 制御構造: {len(control_structures)}個")
        if control_structures:
            for i, ctrl in enumerate(control_structures[:3]):
                print(f"    {i+1}. {ctrl}")
            if len(control_structures) > 3:
                print(f"    ... 他{len(control_structures) - 3}個")
        else:
            print(f"    なし")

    # 独自定義変数の種類数を計算（一時変数除外）
    user_defined_count = len(parameters) + len(real_local_vars)
    if VERBOSE_OUTPUT:
        print(f"\n✨ 独自定義変数の種類数: {user_defined_count}個")
        print(f"   (パラメータ: {len(parameters)}個 + ローカル変数: {len(real_local_vars)}個)")
        print(f"   ※ pyjoern内部生成の一時変数({len(excluded_tmp_vars)}個)は除外")

        # 詳細統計
        total_vars = user_defined_count + len(builtin_funcs)
        if total_vars > 0:
            user_ratio = (user_defined_count / total_vars) * 100
            print(f"   ユーザー定義率: {user_ratio:.1f}% ({user_defined_count}/{total_vars})")

    return {
        'parameters': parameters,
        'local_vars': real_local_vars,  # 一時変数を除外
        'builtin_funcs': builtin_funcs,
        'user_defined_count': user_defined_count,  # 修正された数
        'control_structures': len(control_structures),
        'excluded_tmp_vars': excluded_tmp_vars  # 除外された一時変数
    }
def main():
    """
    メイン関数
    """
    print("🔍 シンプルAST構造表示ツール")
    print("📖 pyjoernのAST構造を詳しく調査")
    print("🎯 独自定義変数の種類数を取得")

    # テストファイル
    test_files = ["whiletest.py"]

    all_results = {}
    top_level_results = {}  # トップレベル分析結果を保存

    for test_file in test_files:
        try:
            if VERBOSE_OUTPUT:
                print(f"\n{'='*60}")
                print(f"📄 ファイル: {test_file}")
                print(f"{'='*60}")

            # AST構造表示
            display_ast_structure(test_file)

            # ノードタイプ分析（変数解析を含む）
            analyze_ast_node_types(test_file)

            # 🆕 トップレベルコード解析を追加
            top_level_analysis = analyze_top_level_code(test_file)

            # トップレベル結果を保存
            if top_level_analysis:
                top_level_results[test_file] = top_level_analysis

            # 結果をファイル別に保存
            functions = parse_source(test_file)
            file_results = {}

            for func_name, func_obj in functions.items():
                if hasattr(func_obj, 'ast') and func_obj.ast:
                    # 変数解析結果を取得
                    var_analysis = analyze_variables_from_statements(func_obj)

                    # 複合代入演算子解析を取得
                    compound_assignments = analyze_compound_assignments(func_obj, var_analysis)

                    # 読み込み数解析を取得（複合代入演算子結果を渡す）
                    read_counts = analyze_variable_reads(func_obj, var_analysis, compound_assignments)

                    # 書き込み数解析を取得（複合代入演算子結果を渡す）
                    write_counts = analyze_variable_writes(func_obj, var_analysis, compound_assignments)

                    # 結果を結合
                    var_analysis['read_counts'] = read_counts
                    var_analysis['write_counts'] = write_counts
                    var_analysis['compound_assignments'] = compound_assignments
                    file_results[func_name] = var_analysis

            # トップレベル解析結果も追加
            if top_level_analysis:
                file_results['<top_level>'] = top_level_analysis

            all_results[test_file] = file_results

        except FileNotFoundError:
            print(f"\n❌ ファイルが見つかりません: {test_file}")
        except Exception as e:
            print(f"\n❌ {test_file} の解析エラー: {e}")
            import traceback
            traceback.print_exc()

    # 総合結果サマリー
    print_summary(all_results, top_level_results)


def print_summary(all_results, top_level_results=None):
    """
    全体の分析結果サマリーを表示
    """
    print(f"\n{'='*60}")
    print("📊 総合分析結果サマリー")
    print(f"{'='*60}")

    # トップレベル分析結果の表示
    if top_level_results:
        print(f"\n📊 トップレベル分析結果:")
        for file_name, result in top_level_results.items():
            print(f"  📄 {file_name}:")
            # user_defined_countの代わりにvariable_countを使用
            var_count = result.get('variable_count', 0)
            print(f"    - トップレベル変数: {var_count}個")
            top_level_reads = result.get('total_reads', 0)
            top_level_writes = result.get('total_writes', 0)
            print(f"    - 読み込み数: {top_level_reads}回")
            print(f"    - 書き込み数: {top_level_writes}回")
            if result.get('variables'):
                print(f"    - 検出された変数: {', '.join(result['variables'])}")

    total_user_vars = 0
    total_builtin_vars = 0
    total_functions = 0
    total_variable_reads = 0
    total_variable_writes = 0

    for file_name, file_results in all_results.items():
        print(f"\n📄 {file_name}:")

        file_user_vars = 0
        file_builtin_vars = 0
        file_reads = 0
        file_writes = 0

        for func_name, result in file_results.items():
            # トップレベル結果は構造が異なるので分岐
            if func_name == '<top_level>':
                # トップレベル結果の処理
                var_count = result.get('variable_count', 0)
                total_reads = result.get('total_reads', 0)
                total_writes = result.get('total_writes', 0)

                print(f"  🌐 トップレベル:")
                print(f"    - トップレベル変数: {var_count}個")
                print(f"    - 読み込み数: {total_reads}回")
                print(f"    - 書き込み数: {total_writes}回")

                file_reads += total_reads
                file_writes += total_writes
                continue

            # 関数レベル結果の処理
            user_count = result['user_defined_count']
            builtin_count = len(result['builtin_funcs'])
            read_counts = result.get('read_counts', {})
            write_counts = result.get('write_counts', {})
            compound_assignments = result.get('compound_assignments', {})

            print(f"  🔧 関数 {func_name}:")
            print(f"    - 独自定義変数: {user_count}個")
            print(f"    - 組み込み変数: {builtin_count}個")
            print(f"    - 制御構造: {result['control_structures']}個")

            if result['parameters']:
                print(f"    - パラメータ: {', '.join(sorted(result['parameters']))}")
            if result['local_vars']:
                print(f"    - ローカル変数: {', '.join(sorted(result['local_vars']))}")

            # 複合代入演算子の表示
            if compound_assignments:
                total_compound = sum(len(ops) for ops in compound_assignments.values())
                print(f"    - 複合代入演算子: {total_compound}回")
                for var in sorted(compound_assignments.keys()):
                    ops = compound_assignments[var]
                    if ops:
                        operators = [op_info['operator'] for op_info in ops]
                        print(f"      {var}: {', '.join(operators)}")

            # 読み込み数の表示
            if read_counts:
                func_total_reads = sum(read_counts.values())
                print(f"    - 変数読み込み総数: {func_total_reads}回")
                for var in sorted(read_counts.keys()):
                    count = read_counts[var]
                    print(f"      {var}: {count}回")
                file_reads += func_total_reads

            # 書き込み数の表示
            if write_counts:
                func_total_writes = sum(write_counts.values())
                print(f"    - 変数書き込み総数: {func_total_writes}回")
                for var in sorted(write_counts.keys()):
                    count = write_counts[var]
                    print(f"      {var}: {count}回")
                file_writes += func_total_writes

            file_user_vars += user_count
            file_builtin_vars += builtin_count
            total_functions += 1

        print(f"  📈 ファイル合計: 独自定義{file_user_vars}個, 組み込み{file_builtin_vars}個, 読み込み{file_reads}回, 書き込み{file_writes}回")
        total_user_vars += file_user_vars
        total_builtin_vars += file_builtin_vars
        total_variable_reads += file_reads
        total_variable_writes += file_writes

    print(f"\n🎯 【最終結果】")
    print(f"  総関数数: {total_functions}個")
    print(f"  独自定義変数の総種類数: {total_user_vars}個")
    print(f"  組み込み変数の総種類数: {total_builtin_vars}個")
    print(f"  独自定義変数の総読み込み数: {total_variable_reads}回")
    print(f"  独自定義変数の総書き込み数: {total_variable_writes}回")

    if total_user_vars + total_builtin_vars > 0:
        ratio = (total_user_vars / (total_user_vars + total_builtin_vars)) * 100
        print(f"  独自定義率: {ratio:.1f}%")

    if total_user_vars > 0:
        avg_reads = total_variable_reads / total_user_vars
        avg_writes = total_variable_writes / total_user_vars
        print(f"  変数あたり平均読み込み数: {avg_reads:.1f}回")
        print(f"  変数あたり平均書き込み数: {avg_writes:.1f}回")

    print(f"\n✅ 目標達成: Pythonの組み込み関数以外の独自定義変数の種類数 = {total_user_vars}個")
    print(f"✅ 新機能: 独自定義変数の読み込み数 = {total_variable_reads}回")
    print(f"✅ 新機能: 独自定義変数の書き込み数 = {total_variable_writes}回")
    print(f"✅ 新機能: 複合代入演算子解析機能を追加")


if __name__ == "__main__":
    main()
