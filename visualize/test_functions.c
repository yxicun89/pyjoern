#include <stdio.h>

// 値渡し
int add(int a, int b)
{
    return a + b;
}

// ポインタ渡し
void swap(int *a, int *b)
{
    int temp = *a;
    *a = *b;
    *b = temp;
}

// 関数ポインタ
int multiply(int a, int b)
{
    return a * b;
}

int main()
{
    int x = 5, y = 10;

    // 通常の関数呼び出し
    int sum = add(x, y);
    printf("Sum: %d\n", sum);

    // ポインタを使った関数呼び出し
    printf("Before swap: x=%d, y=%d\n", x, y);
    swap(&x, &y);
    printf("After swap: x=%d, y=%d\n", x, y);

    // 関数ポインタ
    int (*operation)(int, int) = multiply;
    int product = operation(x, y);
    printf("Product: %d\n", product);

    // 配列の処理
    int arr[5] = {1, 2, 3, 4, 5};
    int i;
    for (i = 0; i < 5; i++)
    {
        arr[i] = arr[i] * 2;
    }

    return 0;
}
