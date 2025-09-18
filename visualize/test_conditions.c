#include <stdio.h>

int main()
{
    int x = 10;
    int y = 20;
    int z = 15;

    // 複雑なif-else if-else
    if (x > y && y > z)
    {
        printf("Case 1\n");
    }
    else if (x < y || z > y)
    {
        printf("Case 2\n");
        if (z > x)
        {
            printf("Nested case 2.1\n");
        }
        else
        {
            printf("Nested case 2.2\n");
        }
    }
    else if (x == 10)
    {
        printf("Case 3\n");
    }
    else
    {
        printf("Default case\n");
    }

    // switch文
    int option = 2;
    switch (option)
    {
    case 1:
        printf("Option 1\n");
        break;
    case 2:
        printf("Option 2\n");
        // fall through
    case 3:
        printf("Option 2 or 3\n");
        break;
    default:
        printf("Unknown option\n");
        break;
    }

    // 三項演算子
    int result = (x > y) ? x : y;
    printf("Max: %d\n", result);

    return 0;
}
