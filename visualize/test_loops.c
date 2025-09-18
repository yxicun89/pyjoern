#include <stdio.h>

int main()
{
    int i, j, k;

    // ネストしたforループ
    for (i = 0; i < 3; i++)
    {
        for (j = 0; j < 2; j++)
        {
            printf("i=%d, j=%d\n", i, j);
        }
    }

    // while + break/continue
    k = 0;
    while (k < 10)
    {
        k++;
        if (k % 2 == 0)
        {
            continue;
        }
        if (k > 7)
        {
            break;
        }
        printf("k=%d\n", k);
    }

    // do-while ループ
    int m = 0;
    do
    {
        printf("m=%d\n", m);
        m++;
    } while (m < 3);

    return 0;
}
