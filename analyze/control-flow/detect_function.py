# loop_statementsとconditional_statementsの数を関数単位でカウントするコード

import re

# Define `source_file` at the beginning of the script
source_file = "whiletest.py"
# source_file = "detect_function.py"
test_files_number = 12

def read_source_file(source_file):
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"読み込みエラー: {e}")

def delete_comments(source_code):
    # コメントアウトを排除（空白行は保持）
    filtered_code = []
    in_multiline_comment = False
    for line in source_code.splitlines():
        stripped_line = line.strip()

        # マルチラインコメントの開始・終了を検出
        if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
            if in_multiline_comment:
                in_multiline_comment = False  # コメント終了
            else:
                in_multiline_comment = True  # コメント開始
            continue

        if in_multiline_comment:
            continue  # マルチラインコメント内はスキップ

        # 行の途中にあるコメントを削除
        code_without_comment = re.sub(r"#.*", "", line).rstrip()
        # コメントだけの行は除外、空白行はそのまま保持
        if code_without_comment.strip() or line.strip() == "":
            filtered_code.append(code_without_comment)

    return filtered_code

# 関数をidgetして表示
def extract_functions_and_others(filtered_code):
    functions = []
    other_code = []
    current_function = None
    current_body = []
    base_indent = None

    for line in filtered_code:
        stripped_line = line.strip()
        if stripped_line.startswith("def ") and (len(line) - len(line.lstrip()) == 0):  # Check for top-level function
            # If a new function starts, save the previous function
            if current_function:
                functions.append((current_function, "\n".join(current_body)))
            current_function = stripped_line  # Save the function signature
            current_body = [line]  # Start collecting the function body
            base_indent = len(line) - len(line.lstrip())  # Record the base indentation
        elif current_function:
            # Check if the line belongs to the current function
            current_indent = len(line) - len(line.lstrip())
            if stripped_line and current_indent > base_indent:
                current_body.append(line)
            elif stripped_line:  # If indentation decreases, the function ends
                functions.append((current_function, "\n".join(current_body)))
                current_function = None
                current_body = []
                base_indent = None
        else:
            # Collect non-function code
            other_code.append(line)

    # Save the last function if any
    if current_function:
        functions.append((current_function, "\n".join(current_body)))

    return functions, "\n".join(other_code)

def count_statements(function_body):
    """関数内の条件文とループ文の数を数える"""
    if_count = 0
    for_count = 0
    while_count = 0
    match_count = 0

    lines = function_body.splitlines()

    for line in lines:
        stripped_line = line.strip()

        # if文とelif文の検出
        if (stripped_line.startswith("if ") or stripped_line.startswith("elif ")) and ":" in stripped_line:
            if_count += 1

        # for文の検出
        if stripped_line.startswith("for ") and ":" in stripped_line:
            for_count += 1

        # while文の検出
        if stripped_line.startswith("while ") and ":" in stripped_line:
            while_count += 1

        # match文の検出
        if stripped_line.startswith("match ") and ":" in stripped_line:
            match_count += 1

    return if_count, for_count, while_count, match_count

def detect_nested_functions(function_body):
    """ネストされた関数を検出する"""
    nested_functions = []
    current_function = None
    current_body = []
    base_indent = None
    target_indent = None

    lines = function_body.splitlines()

    # 最初のネストされた関数のインデントレベルを見つける
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("def ") and (len(line) - len(line.lstrip()) > 0):
            target_indent = len(line) - len(line.lstrip())
            break

    if target_indent is None:
        return nested_functions

    for line in lines:
        stripped_line = line.strip()
        current_indent = len(line) - len(line.lstrip())

        if stripped_line.startswith("def ") and current_indent == target_indent:
            if current_function:
                # 再帰的にネストされた関数を検出
                deeper_nested = detect_nested_functions("\n".join(current_body[1:]))
                nested_functions.append((current_function, "\n".join(current_body), deeper_nested))
            current_function = stripped_line
            current_body = [line]
            base_indent = current_indent
        elif current_function:
            if stripped_line and current_indent > base_indent:
                current_body.append(line)
            elif stripped_line and current_indent <= base_indent:
                deeper_nested = detect_nested_functions("\n".join(current_body[1:]))
                nested_functions.append((current_function, "\n".join(current_body), deeper_nested))
                current_function = None
                current_body = []
                base_indent = None

                if stripped_line.startswith("def ") and current_indent == target_indent:
                    current_function = stripped_line
                    current_body = [line]
                    base_indent = current_indent

    if current_function:
        deeper_nested = detect_nested_functions("\n".join(current_body[1:]))
        nested_functions.append((current_function, "\n".join(current_body), deeper_nested))

    return nested_functions

def print_function_stats(func_name, func_body, indent_level=0):
    """関数の統計情報を表示する（再帰的）"""
    indent = "  " * indent_level
    if_count, for_count, while_count, match_count = count_statements(func_body)

    print(f"{indent}関数: {func_name}")
    print(f"{indent}  if文: {if_count}")
    print(f"{indent}  for文: {for_count}")
    print(f"{indent}  while文: {while_count}")
    print(f"{indent}  match文: {match_count}")

    return if_count, for_count, while_count, match_count

def get_all_function_stats(functions_list):
    """すべての関数の統計情報をリストで返す"""
    all_stats = []

    def collect_stats(functions_list, prefix=""):
        """再帰的に関数の統計を収集"""
        for func_name, func_body in functions_list:
            if_count, for_count, while_count, match_count = count_statements(func_body)

            # 関数の統計情報を辞書として保存
            func_stats = {
                'name': f"{prefix}{func_name}",
                'if_count': if_count,
                'for_count': for_count,
                'while_count': while_count,
                'match_count': match_count
            }
            all_stats.append(func_stats)

            # ネストされた関数を検出
            nested = detect_nested_functions(func_body)
            if nested:
                # ネストされた関数を直接処理（再帰呼び出しを避ける）
                for nested_name, nested_body, deeper_nested in nested:
                    nested_if_count, nested_for_count, nested_while_count, nested_match_count = count_statements(nested_body)

                    nested_func_stats = {
                        'name': f"{prefix}  {nested_name}",
                        'if_count': nested_if_count,
                        'for_count': nested_for_count,
                        'while_count': nested_while_count,
                        'match_count': nested_match_count
                    }
                    all_stats.append(nested_func_stats)

                    # さらに深いネストがある場合
                    if deeper_nested:
                        nested_functions_list = [(name, body) for name, body, _ in deeper_nested]
                        collect_stats(nested_functions_list, prefix + "    ")

    collect_stats(functions_list)
    return all_stats

def get_file_totals(all_stats):
    """ファイル全体の合計を計算"""
    total_if = sum(stat['if_count'] for stat in all_stats)
    total_for = sum(stat['for_count'] for stat in all_stats)
    total_while = sum(stat['while_count'] for stat in all_stats)
    total_match = sum(stat['match_count'] for stat in all_stats)

    return {
        'total_functions': len(all_stats),
        'total_if': total_if,
        'total_for': total_for,
        'total_while': total_while,
        'total_match': total_match
    }

# メイン実行部分をif __name__ == "__main__"で囲む
if __name__ == "__main__":
    source_code = read_source_file(source_file)
    filtered_code = delete_comments(source_code)

    # Extract top-level functions and other code
    functions, other_code = extract_functions_and_others(filtered_code)

    print("\n関数ごとの条件文・ループ文の数:")

    def analyze_functions(functions_list, indent_level=0):
        """関数とその中のネストされた関数を解析する"""
        for func_name, func_body in functions_list:
            # 現在の関数の統計を表示
            print_function_stats(func_name, func_body, indent_level)

            # ネストされた関数を検出
            nested = detect_nested_functions(func_body)

            # ネストされた関数がある場合は再帰的に解析
            if nested:
                print("  " * indent_level + "  ネストされた関数:")
                for nested_name, nested_body, deeper_nested in nested:
                    print_function_stats(nested_name, nested_body, indent_level + 1)

                    # さらに深いネストがある場合
                    if deeper_nested:
                        print("  " * (indent_level + 1) + "  ネストされた関数:")
                        nested_functions_list = [(name, body) for name, body, _ in deeper_nested]
                        analyze_functions(nested_functions_list, indent_level + 2)

            print("-" * 40)

    analyze_functions(functions)

    # 統計情報をリストで取得
    all_function_stats = get_all_function_stats(functions)

    # 関数以外のコードの統計も取得
    other_if_count, other_for_count, other_while_count, other_match_count = count_statements(other_code)

    # 関数以外のコードの統計を追加
    if other_code.strip():  # 関数以外のコードが存在する場合
        other_code_stats = {
            'name': '関数以外のコード',
            'if_count': other_if_count,
            'for_count': other_for_count,
            'while_count': other_while_count,
            'match_count': other_match_count
        }
        all_function_stats.append(other_code_stats)

    file_totals = get_file_totals(all_function_stats)

    print("\n=== 関数統計リスト ===")
    for stat in all_function_stats:
        print(f"{stat['name']}: if={stat['if_count']}, for={stat['for_count']}, while={stat['while_count']}, match={stat['match_count']}")

    print(f"\n=== ファイル合計 ===")
    print(f"関数数: {file_totals['total_functions']}")
    print(f"if文合計: {file_totals['total_if']}")
    print(f"for文合計: {file_totals['total_for']}")
    print(f"while文合計: {file_totals['total_while']}")
    print(f"match文合計: {file_totals['total_match']}")

    print("\n関数以外のコードの統計:")
    print(f"if文: {other_if_count}, for文: {other_for_count}, while文: {other_while_count}, match文: {other_match_count}")

    print("\n関数以外のコード:")
    print(other_code)


# for i in range(1, test_files_number + 1):
#     print(f"\n\n--- 試行中: test_case_{i}.py ---")
#     source_file = f"test_case_{i}.py"
#     source_code = read_source_file(source_file)
#     filtered_code = delete_comments(source_code)

#     functions, other_code = extract_functions_and_others(filtered_code)

#     print("\n関数ごとの条件文・ループ文の数:")

#     def analyze_functions(functions_list, indent_level=0):
#         """関数とその中のネストされた関数を解析する"""
#         for func_name, func_body in functions_list:
#             # 現在の関数の統計を表示
#             print_function_stats(func_name, func_body, indent_level)

#             # ネストされた関数を検出
#             nested = detect_nested_functions(func_body)

#             # ネストされた関数がある場合は再帰的に解析
#             if nested:
#                 print("  " * indent_level + "  ネストされた関数:")
#                 for nested_name, nested_body, deeper_nested in nested:
#                     print_function_stats(nested_name, nested_body, indent_level + 1)

#                     # さらに深いネストがある場合
#                     if deeper_nested:
#                         print("  " * (indent_level + 1) + "  ネストされた関数:")
#                         nested_functions_list = [(name, body) for name, body, _ in deeper_nested]
#                         analyze_functions(nested_functions_list, indent_level + 2)

#             print("-" * 40)

#     analyze_functions(functions)
