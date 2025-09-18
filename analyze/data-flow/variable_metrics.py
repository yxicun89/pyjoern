#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
変数メトリクス取得プログラム

pyjoernを使用してPythonコードから以下の5つの指標を取得します：
- variable_count: プログラムで使用されている変数の数（読み込まれない変数は除く）
- total_reads: 変数に対する読み取り操作の総数
- total_writes: 変数に対する書き込み操作の総数
- max_reads: 単一変数に対する読み取り操作の最大数
- max_writes: 単一変数に対する書き込み操作の最大数
"""

from pyjoern import parse_source, fast_cfgs_from_source
import re
import builtins


def get_variable_metrics(file_path):
    """
    指定されたPythonファイルから変数メトリクスを取得
    関数とトップレベルコード（<module>）の両方を解析

    Returns:
        dict: 5つの指標を含む辞書
    """
    try:
        # 1. 関数レベルの解析
        functions = parse_source(file_path)

        # 2. モジュールレベルの解析（fast_cfgs_from_source使用）
        all_cfgs = fast_cfgs_from_source(file_path)

        # <module> CFGを検索（エスケープされた形式も考慮）
        module_cfg = None
        for cfg_name in ['<module>', '&lt;module&gt;']:
            if cfg_name in all_cfgs:
                module_cfg = all_cfgs[cfg_name]
                break

        if not functions and not module_cfg:
            return {
                'variable_count': 0,
                'total_reads': 0,
                'total_writes': 0,
                'max_reads': 0,
                'max_writes': 0
            }

        # 全結果を統合
        all_read_counts = {}
        all_write_counts = {}

        # 関数レベルの解析
        for func_name, func_obj in functions.items():
            if hasattr(func_obj, 'ast') and func_obj.ast:
                # 変数分析
                user_defined_vars = extract_user_defined_variables(func_obj)

                # 読み込み・書き込み数を取得
                read_counts = count_variable_reads(func_obj, user_defined_vars)
                write_counts = count_variable_writes(func_obj, user_defined_vars)

                # デバッグ表示用
                print(f"🔧 関数 {func_name} の変数詳細:")
                print(f"  📋 検出された変数: {sorted(user_defined_vars)}")
                print(f"  📖 読み込み詳細: {read_counts}")
                print(f"  ✏️ 書き込み詳細: {write_counts}")

                # 統合（同じ変数名は合計する）
                for var, count in read_counts.items():
                    all_read_counts[var] = all_read_counts.get(var, 0) + count

                for var, count in write_counts.items():
                    all_write_counts[var] = all_write_counts.get(var, 0) + count

        # モジュールレベルの解析（<module> CFGから）
        if module_cfg:
            module_vars = extract_module_variables(module_cfg)
            module_reads = count_module_reads(module_cfg, module_vars)
            module_writes = count_module_writes(module_cfg, module_vars)

            # デバッグ表示用
            print(f"🔧 モジュールレベルの変数詳細:")
            print(f"  📋 検出された変数: {sorted(module_vars)}")
            print(f"  📖 読み込み詳細: {module_reads}")
            print(f"  ✏️ 書き込み詳細: {module_writes}")

            # 統合
            for var, count in module_reads.items():
                all_read_counts[var] = all_read_counts.get(var, 0) + count

            for var, count in module_writes.items():
                all_write_counts[var] = all_write_counts.get(var, 0) + count

        # 読み込まれない変数を除外（読み込み数が0の変数）
        used_variables = {var for var, count in all_read_counts.items() if count > 0}

        # 統合結果の詳細表示
        print(f"\n🔧 統合結果詳細:")
        print(f"  📖 全読み込み数: {all_read_counts}")
        print(f"  ✏️ 全書き込み数: {all_write_counts}")
        print(f"  🎯 使用される変数: {sorted(used_variables)}")
        print(f"  ❌ 除外される変数: {sorted(set(all_read_counts.keys()) - used_variables)}")

        # メトリクス計算
        variable_count = len(used_variables)
        total_reads = sum(all_read_counts.values())
        total_writes = sum(all_write_counts.values())
        max_reads = max(all_read_counts.values()) if all_read_counts else 0
        max_writes = max(all_write_counts.values()) if all_write_counts else 0

        return {
            'variable_count': variable_count,
            'total_reads': total_reads,
            'total_writes': total_writes,
            'max_reads': max_reads,
            'max_writes': max_writes
        }

    except Exception as e:
        print(f"エラー: {e}")
        return {
            'variable_count': 0,
            'total_reads': 0,
            'total_writes': 0,
            'max_reads': 0,
            'max_writes': 0
        }


def extract_user_defined_variables(func_obj):
    """
    関数から独自定義変数（パラメータ + ローカル変数）を抽出
    simple_ast_viewer.pyの実績あるロジックを使用
    """
    import builtins

    builtin_names = set(dir(builtins))
    builtin_names.update([
        'range', 'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
        'abs', 'max', 'min', 'sum', 'all', 'any', 'enumerate', 'zip', 'map', 'filter',
        'sorted', 'reversed', 'iter', 'next', 'open', 'input', 'round', 'pow', 'divmod'
    ])

    parameters = set()
    local_vars = set()

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # パラメータの抽出
                if 'PARAM,' in stmt_str:
                    try:
                        param_part = stmt_str.split('PARAM,')[1]
                        param_name = param_part.split(')')[0] if ')' in param_part else param_part.split('<')[0]
                        if param_name and param_name.isidentifier():
                            parameters.add(param_name)
                    except:
                        pass

                # ローカル変数の抽出
                elif 'LOCAL,' in stmt_str:
                    try:
                        local_part = stmt_str.split('LOCAL,')[1]
                        var_name = local_part.split(':')[0] if ':' in local_part else local_part.split('>')[0]

                        if var_name and var_name.isidentifier():
                            if var_name not in builtin_names and not var_name.startswith('tmp'):
                                local_vars.add(var_name)
                    except:
                        pass

    # tmpで始まる一時変数を除外した本当のユーザー定義変数
    real_local_vars = {var for var in local_vars if not var.startswith('tmp')}

    return parameters | real_local_vars


def extract_module_variables(module_cfg):
    """
    モジュールレベルのCFGから実際の変数のみを抽出
    関数呼び出しの引数は変数として扱うが、関数名自体は変数ではない
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

                # 関数呼び出しの引数は変数として扱う（例: example(5) の 5 は定数なので除外、example(x) の x は変数）
                # しかし、関数名（example）自体は変数ではない
                func_call_pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)'
                func_call_match = re.match(func_call_pattern, stmt_str)
                if func_call_match:
                    # 関数名は変数として扱わない
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


def count_module_reads(module_cfg, module_vars):
    """
    モジュールレベルCFGでの変数読み込み数をカウント
    実際のPythonステートメントのみ対象とする
    """
    read_counts = {var: 0 for var in module_vars}

    for node in module_cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # pyjoernのメタデータステートメントを除外
                if any(keyword in stmt_str for keyword in ['<UnsupportedStmt:', 'FUNCTION_', 'TYPE_REF', '__builtins__']):
                    continue

                for var in module_vars:
                    # 関数呼び出しでの読み込み: example(5)
                    if f'{var}(' in stmt_str and stmt_str.startswith(var):
                        read_counts[var] += 1
                    # 条件文での読み込み: __name__ (特殊ケース、通常は除外)
                    elif var in stmt_str and '==' in stmt_str and var != 'name':
                        read_counts[var] += 1

    return read_counts


def count_module_writes(module_cfg, module_vars):
    """
    モジュールレベルCFGでの変数書き込み数をカウント
    実際のPythonステートメントのみ対象とする
    """
    write_counts = {var: 0 for var in module_vars}

    for node in module_cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # pyjoernのメタデータステートメントを除外
                if any(keyword in stmt_str for keyword in ['<UnsupportedStmt:', 'FUNCTION_', 'TYPE_REF', '__builtins__']):
                    continue

                for var in module_vars:
                    # 関数定義での書き込み: example = defexample(...)
                    if f'{var} = def{var}' in stmt_str:
                        write_counts[var] += 1
                    # 通常の代入での書き込み
                    elif f'{var} =' in stmt_str and f'def{var}' not in stmt_str:
                        write_counts[var] += 1

    return write_counts


def count_variable_reads(func_obj, user_defined_vars):
    """
    変数の読み込み数をカウント
    """
    read_counts = {var: 0 for var in user_defined_vars}

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                for var in user_defined_vars:
                    var_refs = count_variable_references(stmt_str, var)
                    if var_refs > 0:
                        read_counts[var] += var_refs

    return read_counts


def count_variable_writes(func_obj, user_defined_vars):
    """
    変数の書き込み数をカウント
    """
    write_counts = {var: 0 for var in user_defined_vars}
    detected_loop_writes = set()

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                for var in user_defined_vars:
                    write_count = count_variable_write_operations(stmt_str, var, node.addr, detected_loop_writes)
                    if write_count > 0:
                        write_counts[var] += write_count

    return write_counts


def count_variable_references(stmt_str, var_name):
    """
    ステートメント内での変数参照回数をカウント（読み込み）
    simple_ast_viewer.pyの実績あるロジックを使用
    """
    import re

    # pyjoernの内部表現による重複を避けるため、低レベル表現のみ除外
    exclude_patterns = [
        r'<UnsupportedStmt:',                  # 全てのUnsupportedStmt（内部表現）
        r'PARAM,',                             # パラメータ定義
        r'LOCAL,',                             # ローカル変数定義
        r'CONTROL_STRUCTURE',                  # 制御構造
        r"^\s*tmp\d+\s*=",                     # 一時変数への代入
        r"^\s*\w+\)\s*$",                      # 単一の変数名＋閉じ括弧のみ
        r"__next__\(\)",                       # イテレータ内部メソッド
    ]

    # 除外パターンに一致する場合はカウントしない
    for pattern in exclude_patterns:
        if re.search(pattern, stmt_str, re.IGNORECASE):
            return 0

    # 複合代入演算子のチェック（読み込みとしてカウント）
    compound_operators = ['+=', '-=', '*=', '/=', '//=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=']
    for op in compound_operators:
        pattern = rf'\b{re.escape(var_name)}\s*{re.escape(op)}\s*'
        if re.search(pattern, stmt_str):
            return 1  # 複合代入演算子は読み込みとしてカウント

    # for文のループ変数の特殊処理
    # for var in range(...): の場合、varは条件判定で暗黙的に読み込まれる
    for_loop_pattern = rf'for\s+{re.escape(var_name)}\s+in\s+'
    if re.search(for_loop_pattern, stmt_str):
        return 1  # ループ変数の条件判定での読み込み

    # for文でのターゲット変数（for l in my_list の my_list）
    for_loop_target_pattern = rf'for\s+\w+\s+in\s+{re.escape(var_name)}\b'
    if re.search(for_loop_target_pattern, stmt_str):
        return 1  # ループ対象変数の読み込み

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


def count_variable_write_operations(stmt_str, var_name, node_addr, detected_loop_writes):
    """
    ステートメント内での変数書き込み回数をカウント
    simple_ast_viewer.pyの実績あるロジックを使用
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
            return 1
        else:
            # 既に検出済みの場合はカウントしない
            return 0

    # pyjoernの内部表現による重複を避けるため、低レベル表現のみ除外
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


def print_metrics(metrics, file_path):
    """
    メトリクスを見やすく表示
    """
    print(f"📄 ファイル: {file_path}")
    print("📊 変数メトリクス:")
    print(f"  variable_count: {metrics['variable_count']}")
    print(f"  total_reads: {metrics['total_reads']}")
    print(f"  total_writes: {metrics['total_writes']}")
    print(f"  max_reads: {metrics['max_reads']}")
    print(f"  max_writes: {metrics['max_writes']}")


def main():
    """
    メイン関数
    """
    test_files = ["whiletest.py"]

    for test_file in test_files:
        print(f"🔍 解析中: {test_file}")

        # デバッグ: どの部分が検出されているか表示
        try:
            # 1. 関数解析
            functions = parse_source(test_file)
            if functions:
                print(f"📋 関数解析で検出: {list(functions.keys())}")
                for func_name, func_obj in functions.items():
                    print(f"  - {func_name}: 開始行{func_obj.start_line} ~ 終了行{func_obj.end_line}")
            else:
                print("❌ 関数解析では検出されませんでした")

            # 2. モジュールレベル解析
            print(f"\n🔍 モジュールレベル解析:")
            all_cfgs = fast_cfgs_from_source(test_file)

            # <module> CFGを検索（エスケープされた形式も考慮）
            module_cfg = None
            module_cfg_name = None
            for cfg_name in ['<module>', '&lt;module&gt;']:
                if cfg_name in all_cfgs:
                    module_cfg = all_cfgs[cfg_name]
                    module_cfg_name = cfg_name
                    break

            if module_cfg:
                print(f"✅ {module_cfg_name} CFG検出: {len(module_cfg.nodes())}ノード, {len(module_cfg.edges())}エッジ")

                # モジュール内のステートメントを表示
                print(f"  📜 モジュールステートメント:")
                for i, node in enumerate(module_cfg.nodes()):
                    if hasattr(node, 'statements') and node.statements:
                        for j, stmt in enumerate(node.statements):
                            stmt_str = str(stmt)
                            print(f"    [{i}-{j}] {stmt_str}")

                # 抽出された変数を表示
                module_vars = extract_module_variables(module_cfg)
                print(f"  🎯 抽出された変数: {sorted(module_vars)}")

                if module_vars:
                    module_reads = count_module_reads(module_cfg, module_vars)
                    module_writes = count_module_writes(module_cfg, module_vars)
                    print(f"  📖 読み込み数: {module_reads}")
                    print(f"  ✏️ 書き込み数: {module_writes}")
                else:
                    print(f"  ⚠️ モジュールレベル変数が見つかりませんでした")
            else:
                print("❌ <module> CFGが見つかりませんでした")
                print(f"  利用可能なCFG: {list(all_cfgs.keys())}")

                # デバッグ: すべてのCFGの詳細を表示
                print(f"  📝 CFG詳細:")
                for cfg_name, cfg in all_cfgs.items():
                    node_count = len(cfg.nodes()) if hasattr(cfg, 'nodes') else 'N/A'
                    edge_count = len(cfg.edges()) if hasattr(cfg, 'edges') else 'N/A'
                    print(f"    - {cfg_name}: {node_count}ノード, {edge_count}エッジ")

        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()

        # メトリクス計算
        print(f"\n📊 最終変数メトリクス:")
        metrics = get_variable_metrics(test_file)
        print_metrics(metrics, test_file)
        print()  # 空行


if __name__ == "__main__":
    main()
