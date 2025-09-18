# モジュールレベルのコード（関数なし）
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
        break  # 無限ループを避けるため

print("Done")
