#include <stdio.h>

// 再帰関数：階乗計算
int factorial(int n)
{
    if (n <= 1)
    {
        return 1;
    }
    else
    {
        return n * factorial(n - 1);
    }
}

// 再帰関数：フィボナッチ数列
int fibonacci(int n)
{
    if (n <= 0)
    {
        return 0;
    }
    else if (n == 1)
    {
        return 1;
    }
    else
    {
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
}

int main()
{
    int result1 = factorial(5);
    int result2 = fibonacci(6);
    printf("Factorial: %d, Fibonacci: %d\n", result1, result2);
    return 0;
}
