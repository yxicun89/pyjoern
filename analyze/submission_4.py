def example(x):
    if x < 0:
        x = -x
        print(x)
    else:
        print("Non-negative")

    while x > 0:
        x = x - 1
        print(x)

    for i in range(3):
        print(i)

    return x

if __name__ == "__main__":
    example(5)
