def example(x):
    if x > 0 :          # x: 読み込み (1回目)
        for i in range(x): # x: 読み込み (2回目), i: ループ変数定義
            if i % 2 == 0: # i: 読み込み (1回目)
                print(i)  # i: 読み込み (2回目)
            else:
                print(i * 2) # i: 読み込み (3回目)
    else:
        while x < 0:  # x: 読み込み (3回目)
            x += 1   # x: 読み込み (4回目) + 代入
            print(x)  # x: 読み込み (5回目)
    t = x * 2 # x: 読み込み (6回目) + 代入, t: 代入
    if t > 10: # t: 読み込み (1回目)
        print("t is greater than 10")
    else:
        print("t is 10 or less")
        for j in range(t):  # t: 読み込み (2回目), j: ループ変数定義
            print(j) # j: 読み込み (1回目)
    my_list = [19, 3] # my_list: 代入
    for l in my_list: # my_list: 読み込み (1回目), l: ループ変数定義
        print(l) # l: 読み込み (4回目)

if __name__ == "__main__":
    example(5) # x: 代入
