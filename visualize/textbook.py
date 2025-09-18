# 中間後で表現されたプログラムをPythonに変換
def test():
    j = 10
    i = -8

    while True:
        i = i + 1
        j = j - 1
        c = (j != 0)
        if c:
            continue  # goto 3に相当

        j = i / 2
        c = (i < 8)
        if not c:  # if c then goto 11の否定
            i = 2

        # goto 4に相当する部分は、whileループの先頭に戻ることで表現される

if __name__ == "__main__":
    test()
