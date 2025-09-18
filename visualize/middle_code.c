#include <stdio.h>
// #include <stdbool.h>

int main() {
    // 1 : j = 10
    int j = 10;
    // 2 : i = -8
    int i = -8;

    // 3 : i = i + 1
    line_3:
    i = i + 1;

    // 4 : j = j - 1
    line_4:
    j = j - 1;
    // 5 : c = (j ≠0)
    int c = (j != 0);
    // 6 : if c then goto 3
    if (c) {
        goto line_3;
    }

    // 7 : j = i / 2
    j = i / 2;
    // 8 : c = (i < 8)
    int c = (i < 8);
    // 9 : if c then goto 11
    if (c) {
        goto line_11;
    }

    // 10 : i = 2
    i = 2;

    // 11 : goto 4
    line_11:
    goto line_4;

    return 0;
}
