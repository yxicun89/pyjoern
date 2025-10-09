# 包括的なPythonサンプルコード - 基本構文＋再帰
# CFG解析テスト用のコード

def fibonacci_recursive(n):
    """再帰を使ったフィボナッチ数列"""
    if n <= 1:  # 条件文1
        return n
    else:
        return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)  # 再帰呼び出し

def factorial_recursive(n):
    """再帰を使った階乗計算"""
    if n <= 1:  # 条件文2
        return 1
    return n * factorial_recursive(n-1)  # 再帰呼び出し

def comprehensive_analysis(data_list, target):
    """包括的な基本構文を使った関数"""

    # 1. 条件文 (if-elif-else)
    if not data_list:  # 条件文3
        print("Empty list")
        return None
    elif len(data_list) == 1:  # 条件文4
        return data_list[0]

    # 2. for文 - range使用
    for i in range(len(data_list)):  # forループ1
        if data_list[i] == target:  # 条件文5
            print(f"Found at index {i}")
            break

    # 3. for文 - リスト直接反復
    for item in data_list:  # forループ2
        if item > 100:  # 条件文6
            print(f"Large number: {item}")
            continue
        print(f"Normal number: {item}")

    # 4. while文
    counter = 0
    while counter < 5:  # whileループ1
        counter += 1  # compound assignment
        if counter == 3:  # 条件文7
            continue
        print(f"Counter: {counter}")

    # 5. for文 - enumerate使用
    for index, value in enumerate(data_list):  # forループ3
        if index % 2 == 0:  # 条件文8
            print(f"Even index {index}: {value}")

    # 6. for文 - zip使用
    indices = list(range(len(data_list)))
    for idx, val in zip(indices, data_list):  # forループ4
        if val < 0:  # 条件文9
            print(f"Negative at {idx}: {val}")

    # 7. 辞書操作のfor文
    data_dict = {f"key_{i}": i*2 for i in range(3)}
    for key in data_dict.keys():  # forループ5
        print(f"Key: {key}")

    for value in data_dict.values():  # forループ6
        if value > 2:  # 条件文10
            print(f"Large value: {value}")

    for k, v in data_dict.items():  # forループ7
        if v % 2 == 0:  # 条件文11
            print(f"Even pair: {k}={v}")

    # 8. ネストしたループと条件
    for outer in range(3):  # forループ8
        for inner in range(2):  # forループ9（ネスト）
            if outer + inner > 2:  # 条件文12
                break
            print(f"Nested: {outer}, {inner}")

    # 9. リスト内包表記は解析対象外だが、代替案
    result_list = []
    for x in data_list:  # forループ10
        if x % 2 == 0:  # 条件文13
            result_list.append(x * 2)

    return result_list

def string_processing_examples():
    """文字列処理の例"""
    text = "hello,world,python,programming"

    # split()を使ったfor文
    for word in text.split(','):  # forループ11
        if len(word) > 5:  # 条件文14
            print(f"Long word: {word}")

    # ファイル処理の例（実際のファイルがなくても構文チェック用）
    lines = ["line1", "line2", "line3"]
    for line in lines:  # forループ12（readlines()の代替）
        if "line" in line:  # 条件文15
            print(f"Processing: {line.strip()}")

def mathematical_operations(numbers):
    """数学的操作の例"""
    total = 0

    # while文による累積計算
    i = 0
    while i < len(numbers):  # whileループ2
        total += numbers[i]
        i += 1  # compound assignment
        if total > 1000:  # 条件文16
            print("Sum exceeded 1000")
            break

    # 条件による分岐処理
    if total > 500:  # 条件文17
        result = "high"
    elif total > 100:  # 条件文18
        result = "medium"
    else:
        result = "low"

    return result, total

def recursive_tree_traversal(node_dict, current_node, visited=None):
    """再帰を使った木構造の走査"""
    if visited is None:
        visited = set()

    if current_node in visited:  # 条件文19
        return

    visited.add(current_node)
    print(f"Visiting node: {current_node}")

    # 子ノードの再帰的走査
    if current_node in node_dict:  # 条件文20
        for child in node_dict[current_node]:  # forループ13
            recursive_tree_traversal(node_dict, child, visited)  # 再帰呼び出し

def main_comprehensive_test():
    """メイン関数 - 全ての機能をテスト"""

    # テストデータ
    test_data = [1, 2, 3, 4, 5, -1, 150, 75]
    target_value = 3

    print("=== 包括的CFG解析テスト ===")

    # 基本構文テスト
    result = comprehensive_analysis(test_data, target_value)
    print(f"Analysis result: {result}")

    # 文字列処理テスト
    string_processing_examples()

    # 数学的操作テスト
    math_result = mathematical_operations(test_data)
    print(f"Math result: {math_result}")

    # 再帰テスト
    print(f"Fibonacci(6): {fibonacci_recursive(6)}")
    print(f"Factorial(5): {factorial_recursive(5)}")

    # 木構造テスト
    tree = {
        'root': ['child1', 'child2'],
        'child1': ['leaf1'],
        'child2': ['leaf2', 'leaf3']
    }
    recursive_tree_traversal(tree, 'root')

if __name__ == "__main__":
    main_comprehensive_test()
