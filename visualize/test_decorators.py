# Python版：デコレータと高階関数のテスト

import time
import functools

def timing_decorator(func):
    """実行時間を測定するデコレータ"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

def retry_decorator(max_attempts=3):
    """リトライ機能付きデコレータ"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    print(f"Attempt {attempt + 1} failed: {e}")
            return None
        return wrapper
    return decorator

def cache_decorator(func):
    """キャッシュ機能付きデコレータ"""
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        if args in cache:
            print(f"Cache hit for {args}")
            return cache[args]

        result = func(*args)
        cache[args] = result
        print(f"Cache miss for {args}, computed: {result}")
        return result

    return wrapper

@timing_decorator
@cache_decorator
def fibonacci_slow(n):
    """非効率なフィボナッチ計算（キャッシュとタイミングのテスト用）"""
    if n <= 1:
        return n
    else:
        return fibonacci_slow(n - 1) + fibonacci_slow(n - 2)

@retry_decorator(max_attempts=3)
def unreliable_function(success_rate=0.3):
    """不安定な関数（リトライのテスト用）"""
    import random
    if random.random() < success_rate:
        return "Success!"
    else:
        raise RuntimeError("Function failed randomly")

def apply_operation(numbers, operation):
    """高階関数：リストに操作を適用"""
    return [operation(x) for x in numbers]

def compose_functions(*functions):
    """関数合成"""
    def composed(x):
        result = x
        for func in reversed(functions):
            result = func(result)
        return result
    return composed

def filter_and_map(data, predicate, mapper):
    """フィルタとマップの組み合わせ"""
    filtered = filter(predicate, data)
    mapped = map(mapper, filtered)
    return list(mapped)

def test_decorators_and_higher_order():
    print("=== Decorator Tests ===")

    # フィボナッチのキャッシュテスト
    print("Computing fibonacci(10) twice:")
    result1 = fibonacci_slow(10)
    result2 = fibonacci_slow(10)  # キャッシュヒット

    # リトライテスト
    print("\n=== Retry Tests ===")
    try:
        result = unreliable_function(0.8)  # 高い成功率
        print(f"Result: {result}")
    except RuntimeError as e:
        print(f"Final failure: {e}")

    # 高階関数テスト
    print("\n=== Higher Order Function Tests ===")
    numbers = [1, 2, 3, 4, 5]

    # 各数値を2倍にする
    doubled = apply_operation(numbers, lambda x: x * 2)
    print(f"Doubled: {doubled}")

    # 関数合成：x -> x*2 -> x+1
    double = lambda x: x * 2
    increment = lambda x: x + 1
    double_then_increment = compose_functions(increment, double)

    composed_result = double_then_increment(5)
    print(f"Composed function result: {composed_result}")

    # フィルタとマップ
    data = range(1, 11)
    even_squares = filter_and_map(
        data,
        lambda x: x % 2 == 0,  # 偶数のみ
        lambda x: x ** 2       # 2乗
    )
    print(f"Even squares: {even_squares}")

if __name__ == "__main__":
    test_decorators_and_higher_order()
