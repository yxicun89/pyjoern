def count_evens(numbers):
    count = 0              # ① 開始・初期化 (Block)

    for n in numbers:      # ② ループ条件 (Decision / 菱形)
                           #    (リストにまだ要素があるか？)

        if n % 2 == 0:     # ③ 分岐条件 (Decision / 菱形)
                           #    (偶数か？)

            count += 1     # ④ 処理 (Block / 長方形)

    return count           # ⑤ 終了 (Block)


# def example(x):
#   if x > 0:
#       for i in range(x):
#           if i % 3 == 0:
#               print(f"Divisible by 3: {i}")
#           elif i % 3 == 1:
#               print(f"Remainder 1: {i}")
#           else:
#               print(f"Remainder 2: {i}")
#   else:
#       while x < 0:
#           print(f"Negative: {x}")
#           x += 1

#   if x > 10:
#       print("Done")
#   else:
#       print("Not Done")

# if __name__ == "__main__":
#   example(5)
