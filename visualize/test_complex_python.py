# Python版：複雑な制御構造のテスト

def test_nested_loops():
    """ネストしたループのテスト"""
    result = []

    for i in range(3):
        for j in range(2):
            if i == 1 and j == 0:
                continue
            result.append((i, j))

            # 内部の条件によるbreak
            if i == 2 and j == 1:
                break

    return result

def test_while_with_else():
    """while-else構文のテスト"""
    counter = 0

    while counter < 5:
        if counter == 3:
            break
        print(f"Counter: {counter}")
        counter += 1
    else:
        print("Loop completed normally")

    return counter

def test_exception_handling():
    """例外処理のテスト"""
    try:
        x = 10 / 0  # ZeroDivisionError
    except ZeroDivisionError as e:
        print(f"Caught error: {e}")
        try:
            y = int("not_a_number")  # ValueError
        except ValueError:
            print("Nested exception handled")
        finally:
            print("Inner finally block")
    except Exception as e:
        print(f"Other error: {e}")
    finally:
        print("Outer finally block")

def test_list_comprehension():
    """リスト内包表記のテスト"""
    # 条件付きリスト内包表記
    numbers = [x for x in range(10) if x % 2 == 0]

    # ネストしたリスト内包表記
    matrix = [[i + j for j in range(3)] for i in range(3)]

    return numbers, matrix

def test_generators():
    """ジェネレータのテスト"""
    def fibonacci_generator(n):
        a, b = 0, 1
        count = 0
        while count < n:
            yield a
            a, b = b, a + b
            count += 1

    # ジェネレータ式
    squares = (x**2 for x in range(5))

    fib_gen = fibonacci_generator(8)
    return list(fib_gen), list(squares)

def main():
    print("=== Nested Loops Test ===")
    nested_result = test_nested_loops()
    print(f"Result: {nested_result}")

    print("\n=== While-Else Test ===")
    while_result = test_while_with_else()
    print(f"Final counter: {while_result}")

    print("\n=== Exception Handling Test ===")
    test_exception_handling()

    print("\n=== List Comprehension Test ===")
    numbers, matrix = test_list_comprehension()
    print(f"Even numbers: {numbers}")
    print(f"Matrix: {matrix}")

    print("\n=== Generator Test ===")
    fib_seq, squares = test_generators()
    print(f"Fibonacci: {fib_seq}")
    print(f"Squares: {squares}")

if __name__ == "__main__":
    main()
