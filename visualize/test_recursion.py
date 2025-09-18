# Python版：再帰関数のテスト

def factorial(n):
    """階乗の再帰計算"""
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def fibonacci(n):
    """フィボナッチ数列の再帰計算"""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

def hanoi(n, source, destination, auxiliary):
    """ハノイの塔の再帰解法"""
    if n == 1:
        print(f"Move disk 1 from {source} to {destination}")
        return

    hanoi(n - 1, source, auxiliary, destination)
    print(f"Move disk {n} from {source} to {destination}")
    hanoi(n - 1, auxiliary, destination, source)

def main():
    # 階乗テスト
    result1 = factorial(5)
    print(f"Factorial(5) = {result1}")

    # フィボナッチテスト
    result2 = fibonacci(6)
    print(f"Fibonacci(6) = {result2}")

    # ハノイの塔テスト
    print("Hanoi Tower (3 disks):")
    hanoi(3, "A", "C", "B")

if __name__ == "__main__":
    main()
