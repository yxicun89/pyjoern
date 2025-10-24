def recursive_sum(data_list, idx=0, total=0):
    if idx >= len(data_list):
        return total
    if data_list[idx] < 0:
        print(f"Negative value at {idx}: {data_list[idx]}")
    elif data_list[idx] == 0:
        print(f"Zero at {idx}")
    else:
        print(f"Positive value at {idx}: {data_list[idx]}")
    return recursive_sum(data_list, idx + 1, total + data_list[idx])

def analyze_list(data_list):
    for i in range(len(data_list)):
        if i % 2 == 0:
            print(f"Even index: {i}")
        else:
            print(f"Odd index: {i}")

    counter = 0
    while counter < len(data_list):
        if data_list[counter] > 50:
            print(f"Large number at {counter}: {data_list[counter]}")
        elif data_list[counter] < 0:
            print(f"Negative number at {counter}: {data_list[counter]}")
        else:
            print(f"Normal number at {counter}: {data_list[counter]}")
        counter += 1

    return recursive_sum(data_list)

if __name__ == "__main__":
    sample_list = [10, -5, 0, 60, 3]
    print("Recursive sum:", analyze_list(sample_list))
