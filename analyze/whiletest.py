def example(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
            else:
                print(i * 2)
    else:
        print(x)
        x += 1

    # さらにcomplexなケース
    t = x * 2
    if t > 10:
        for j in range(t):
            print(j)

    my_list = [19, 3]
    for l in my_list:
        print(l)

    return x

if __name__ == "__main__":
    print(example(5))
