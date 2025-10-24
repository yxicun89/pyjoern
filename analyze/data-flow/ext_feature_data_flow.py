#これがデータフローから特徴量抽出するコード

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx


def analyze_ast_node_types(file_path):

    try:
        functions = parse_source(file_path)

        for func_name, func_obj in functions.items():
            # statements解析による変数抽出
            var_analysis = analyze_variables_from_statements(func_obj)

            # 複合代入演算子解析
            compound_assignments = analyze_compound_assignments(func_obj, var_analysis)

            # 変数の読み込み数解析（複合代入演算子結果を渡す）
            read_counts = analyze_variable_reads(func_obj, var_analysis, compound_assignments)

            # 変数の書き込み数解析（複合代入演算子結果を渡す）
            write_counts = analyze_variable_writes(func_obj, var_analysis, compound_assignments)

    except Exception as e:
        print(f"ノードタイプ分析エラー: {e}")


def get_function_parameters(func_obj):
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


def analyze_top_level_variables(module_cfg):
    """トップレベル変数の読み書きをカウント（関数呼び出し解析なし）"""
    # 変数の読み込み・書き込みをカウント
    variable_reads = {}
    variable_writes = {}

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

    return {
        'variable_reads': variable_reads,
        'variable_writes': variable_writes,
        'total_reads': sum(variable_reads.values()),
        'total_writes': sum(variable_writes.values())
    }


def analyze_top_level_code(file_path):
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
            return {}

        # モジュール内のステートメントを表示

        for i, node in enumerate(module_cfg.nodes()):
            if hasattr(node, 'statements') and node.statements:
                for j, stmt in enumerate(node.statements):
                    stmt_str = str(stmt)

        top_level_vars = analyze_top_level_variables(module_cfg)

        # トップレベル変数を抽出
        top_level_vars = extract_top_level_variables(module_cfg)

        # トップレベル変数の読み込み・書き込み数を解析
        if top_level_vars:
            top_level_reads = count_top_level_reads(module_cfg, top_level_vars)
            top_level_writes = count_top_level_writes(module_cfg, top_level_vars)
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
                'max_writes': max(top_level_writes.values()) if top_level_vars else 0
            }
        else:
            return {
                'variable_count': 0,
                'total_reads': 0,
                'total_writes': 0
            }

    except Exception as e:
        print(f"トップレベル解析エラー: {e}")
        import traceback
        traceback.print_exc()
        return {
            'variable_count': 0,
            'total_reads': 0,
            'total_writes': 0
        }


def extract_top_level_variables(module_cfg):
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
    import re

    # 独自定義変数のリスト
    user_defined_vars = var_analysis['parameters'] | var_analysis['local_vars']

    if not user_defined_vars:
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
    return compound_assignments


def analyze_variable_reads(func_obj, var_analysis, compound_assignments=None):
    import re

    # 独自定義変数のリスト
    user_defined_vars = var_analysis['parameters'] | var_analysis['local_vars']

    if not user_defined_vars:
        return {}

    # 各変数の読み込み数をカウント
    read_counts = {var: 0 for var in user_defined_vars}

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # 変数の参照を検出
                for var in user_defined_vars:
                    var_refs = count_variable_references(stmt_str, var, node.addr)
                    if var_refs > 0:  # カウントされた場合のみ記録
                        read_counts[var] += var_refs

    # 🔄 複合代入演算子による読み込み数を加算（引数で渡された結果を使用）
    if compound_assignments:
        for var in user_defined_vars:
            compound_count = len(compound_assignments.get(var, []))
            if compound_count > 0:
                read_counts[var] += compound_count

    return read_counts


def analyze_variable_writes(func_obj, var_analysis, compound_assignments=None):
    import re

    # 独自定義変数のリスト
    user_defined_vars = var_analysis['parameters'] | var_analysis['local_vars']

    if not user_defined_vars:
        return {}

    # 🆕 関数の引数（パラメータ）への書き込み数を+1でカウント
    parameters = var_analysis['parameters']

    # ループ変数を特定（複数の方法で検出）
    loop_variables = set()
    iterator_variables = set()
    range_loop_candidates = set()

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                # for文のパターンを直接検出
                import re

                for var in user_defined_vars:
                    # "for var in" パターンをチェック（UnsupportedStmtも含む）
                    for_pattern = rf'for\s+{re.escape(var)}\s+in\s+'
                    if re.search(for_pattern, stmt_str, re.IGNORECASE):
                        if var not in loop_variables:
                            loop_variables.add(var)
                        break

                    # CONTROL_STRUCTURE内のfor文も検出
                    if 'CONTROL_STRUCTURE,FOR' in stmt_str and var in stmt_str:
                        if var not in loop_variables:
                            loop_variables.add(var)
                        break

    # 各変数の書き込み数をカウント
    write_counts = {var: 0 for var in user_defined_vars}

    # 重複を防ぐため、既に検出したループ変数の書き込みを追跡
    detected_loop_writes = set()

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

                        # for文パターンでも検出
                        import re
                        for_pattern = rf'for\s+{re.escape(var)}\s+in\s+'
                        if re.search(for_pattern, stmt_str, re.IGNORECASE) and write_key not in detected_loop_writes:
                            write_count = 1
                            detected_loop_writes.add(write_key)

                    if write_count > 0:  # カウントされた場合のみ記録
                        write_counts[var] += write_count

    # 🆕 関数の引数（パラメータ）への自動書き込み加算
    parameters = var_analysis['parameters']
    for param in parameters:
        write_counts[param] += 1  # 引数として値を受け取るため+1

    return write_counts


def count_variable_writes(stmt_str, var_name, node_addr, detected_loop_writes):
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

    #重要: tmp.__next__()からの代入（ループ変数の実際の書き込み）を検出
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
    関数の引数特定ロジックを改良
    """

    # builtinsライブラリで組み込み識別子を取得
    import builtins
    import re
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

    # 🆕 引数検出の詳細デバッグ情報
    param_detection_details = []

    for node in func_obj.ast.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # 🆕 改良された引数検出ロジック
                if 'PARAM,' in stmt_str:
                    # デバッグ情報を記録
                    param_detection_details.append({
                        'statement': stmt_str,
                        'node_addr': getattr(node, 'addr', 'unknown')
                    })

                    try:
                        # パターン1: <UnsupportedStmt: (PARAM,name)<SUB>1</SUB>>
                        pattern1 = r'PARAM,([a-zA-Z_][a-zA-Z0-9_]*)\)'
                        match1 = re.search(pattern1, stmt_str)
                        if match1:
                            param_name = match1.group(1)
                            if param_name.isidentifier():
                                parameters.add(param_name)
                                continue

                        # パターン2: PARAM,name:type>
                        pattern2 = r'PARAM,([a-zA-Z_][a-zA-Z0-9_]*):.*?>'
                        match2 = re.search(pattern2, stmt_str)
                        if match2:
                            param_name = match2.group(1)
                            if param_name.isidentifier():
                                parameters.add(param_name)
                                continue

                        # パターン3: 従来の分割方式（フォールバック）
                        param_part = stmt_str.split('PARAM,')[1]
                        param_name = param_part.split(')')[0] if ')' in param_part else param_part.split('<')[0]
                        if param_name and param_name.isidentifier():
                            parameters.add(param_name)

                    except Exception as e:
                        pass

                # ローカル変数の抽出: <UnsupportedStmt: LOCAL,i:ANY>
                elif 'LOCAL,' in stmt_str:
                    try:
                        # LOCAL,の後ろから:までを抽出
                        local_part = stmt_str.split('LOCAL,')[1]
                        var_name = local_part.split(':')[0] if ':' in local_part else local_part.split('>')[0]

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

    # tmpで始まる一時変数を除外した本当のユーザー定義変数
    real_local_vars = {var for var in local_vars if not var.startswith('tmp')}
    excluded_tmp_vars = local_vars - real_local_vars    # 結果表示

    # 独自定義変数の種類数を計算（一時変数除外）
    user_defined_count = len(parameters) + len(real_local_vars)

    return {
        'parameters': parameters,
        'local_vars': real_local_vars,  # 一時変数を除外
        'builtin_funcs': builtin_funcs,
        'user_defined_count': user_defined_count,  # 修正された数
        'control_structures': len(control_structures),
        'excluded_tmp_vars': excluded_tmp_vars  # 除外された一時変数
    }
def main():
    print("📊 データフロー特徴量抽出")

    # テストファイル - 複数のパスを試行
    test_files = [
        "whiletest.py",
        "../whiletest.py",
        "../../visualize/whiletest.py",
        "../control-flow/whiletest.py",
        "../../analyze/whiletest.py"
    ]

    for test_file in test_files:
        try:
            # 新しいメイン解析関数を使用
            all_results, top_level_results = analyze_dataflow_features(test_file)

            if all_results:
                print(f"✅ {test_file} の解析が完了しました")

                # 簡潔なサマリー表示
                print_summary(all_results, top_level_results)

                # リスト形式の結果も表示
                feature_list = extract_dataflow_features_as_list(test_file)
                print(f"\n📊 データフロー特徴量ベクトル（5つの特徴量）:")
                print(f"  [総読み込み数, 総書き込み数, 読み込み数最大値, 書き込み数最大値, 変数種類数]")
                print(f"  {feature_list}")

                break
            else:
                continue

        except FileNotFoundError:
            continue  # 次のファイルパスを試行
        except Exception as e:
            print(f"{test_file} の解析エラー: {e}")
            continue  # 次のファイルパスを試行

    # すべてのファイルが見つからなかった場合
    if not any(test_files):
        print("\n⚠️  解析可能なファイルが見つかりませんでした")
        print("以下のパスを確認してください：")
        for path in test_files:
            print(f"  - {path}")
        return


def extract_dataflow_features_as_list(file_path):
    """
    データフロー特徴量をリスト形式で返すメイン関数（5つの特徴量）
    他のモジュールからインポートしやすい形式

    Returns:
        list: [var_count, total_reads, total_writes, max_reads, max_writes]
              - var_count: 変数の種類数（関数+トップレベル
              - total_reads: 総読み込み数（関数+トップレベル）
              - total_writes: 総書き込み数（関数+トップレベル）
              - max_reads: 読み込み数の最大値（全変数の中で）
              - max_writes: 書き込み数の最大値（全変数の中で）
    """
    try:
        # 解析を実行
        all_results, top_level_results = analyze_dataflow_features(file_path)

        # 結果を集計
        total_reads = 0
        total_writes = 0
        all_read_counts = []  # 全ての読み込み数を記録
        all_write_counts = []  # 全ての書き込み数を記録
        total_var_count = 0

        # 関数レベル結果の処理
        for file_name, file_results in all_results.items():
            for func_name, result in file_results.items():
                # トップレベル結果は別途処理
                if func_name == '<top_level>':
                    continue

                # 関数レベル結果の処理
                user_count = result['user_defined_count']
                read_counts = result.get('read_counts', {})
                write_counts = result.get('write_counts', {})

                # 合計値を加算
                total_reads += sum(read_counts.values())
                total_writes += sum(write_counts.values())
                total_var_count += user_count

                # 個別の読み書き数を記録（最大値計算用）
                all_read_counts.extend(read_counts.values())
                all_write_counts.extend(write_counts.values())

        # トップレベル結果を処理
        if top_level_results:
            for file_name, result in top_level_results.items():
                top_level_var_count = result.get('variable_count', 0)
                top_level_reads = result.get('total_reads', 0)
                top_level_writes = result.get('total_writes', 0)

                # トップレベル結果を合計に加算
                total_reads += top_level_reads
                total_writes += top_level_writes
                total_var_count += top_level_var_count

                # トップレベルの個別読み書き数も記録
                top_level_read_counts = result.get('reads', {})
                top_level_write_counts = result.get('writes', {})
                if top_level_read_counts:
                    all_read_counts.extend(top_level_read_counts.values())
                if top_level_write_counts:
                    all_write_counts.extend(top_level_write_counts.values())

        # 最大値を計算
        max_reads = max(all_read_counts) if all_read_counts else 0
        max_writes = max(all_write_counts) if all_write_counts else 0

        # 5つの特徴量をリスト形式で返す
        return [
            total_var_count,  # 変数種類数
            total_reads,     # 総読み込み数
            total_writes,    # 総書き込み数
            max_reads,       # 読み込み数最大値
            max_writes      # 書き込み数最大値
        ]

    except Exception as e:
        print(f"データフロー特徴量抽出エラー: {e}")
        # エラー時はゼロで埋めたリストを返す
        return [0, 0, 0, 0, 0]

def analyze_dataflow_features(file_path):
    """
    データフロー特徴量を詳細に解析する内部関数

    Returns:
        tuple: (all_results, top_level_results)
    """
    all_results = {}
    top_level_results = {}

    try:
        # トップレベルコード解析
        top_level_analysis = analyze_top_level_code(file_path)
        if top_level_analysis:
            top_level_results[file_path] = top_level_analysis

        # 関数レベル解析
        functions = parse_source(file_path)
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

        all_results[file_path] = file_results

        return all_results, top_level_results

    except Exception as e:
        print(f"データフロー解析エラー: {e}")
        return {}, {}

def get_dataflow_feature_vector(file_path, include_top_level=True):
    """
    データフロー特徴量ベクトルを取得（クラスタリング用）
    新しい5つの特徴量に対応

    Args:
        file_path (str): 解析対象ファイルパス
        include_top_level (bool): トップレベル変数を含めるかどうか

    Returns:
        list: [total_reads, total_writes, max_reads, max_writes, var_count]
    """
    # 新しい5つの特徴量を取得
    features = extract_dataflow_features_as_list(file_path)

    # include_top_levelに関係なく、全体の5つの特徴量を返す
    # （関数レベルとトップレベルは既に統合されているため）
    return features

def print_summary(all_results, top_level_results=None):
    """簡潔なサマリー表示"""
    print(f"\n📊 解析結果サマリー")

    # 最終結果のみ表示
    total_user_vars = 0
    total_variable_reads = 0
    total_variable_writes = 0
    total_functions = 0

    for file_name, file_results in all_results.items():
        for func_name, result in file_results.items():
            if func_name == '<top_level>':
                continue

            user_count = result['user_defined_count']
            read_counts = result.get('read_counts', {})
            write_counts = result.get('write_counts', {})

            total_user_vars += user_count
            total_variable_reads += sum(read_counts.values())
            total_variable_writes += sum(write_counts.values())
            total_functions += 1

    # トップレベル結果を加算
    if top_level_results:
        for file_name, result in top_level_results.items():
            total_user_vars += result.get('variable_count', 0)
            total_variable_reads += result.get('total_reads', 0)
            total_variable_writes += result.get('total_writes', 0)

    print(f"  総関数数: {total_functions}個")
    print(f"  変数種類数: {total_user_vars}個")
    print(f"  総読み込み数: {total_variable_reads}回")
    print(f"  総書き込み数: {total_variable_writes}回")


if __name__ == "__main__":
    main()

# 他のモジュールからのインポート例:
#
# from ext_feature_data_flow import extract_dataflow_features_as_list, get_dataflow_feature_vector
#
# # 基本的な使用方法（5つの特徴量）
# features = extract_dataflow_features_as_list("sample.py")
# print(features)  # [総読み込み数, 総書き込み数, 読み込み数最大値, 書き込み数最大値, 変数種類数]
#
# # クラスタリング用ベクトル
# feature_vector = get_dataflow_feature_vector("sample.py")
# print(feature_vector)  # [総読み込み数, 総書き込み数, 読み込み数最大値, 書き込み数最大値, 変数種類数]
#
# # 詳細分析結果（内部用）
# all_results, top_level_results = analyze_dataflow_features("sample.py")
# print(all_results)  # 詳細な解析結果
