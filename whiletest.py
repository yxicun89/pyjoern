def example(x):
    if x > 0:
        for i in range(x):
            print(i)
    else:
        while x < 0:
            x += 1
    return x

if __name__ == "__main__":
    print(example(5))
