# def comprehensive_analysis(data_list, target):

#     if not data_list:
#         print("Empty list")
#         return None
#     elif len(data_list) == 1:
#         return data_list[0]

#     for i in range(len(data_list)):
#         if data_list[i] == target:
#             print(f"Found at index {i}")
#             break

#     for item in data_list:
#         if item > 100:
#             print(f"Large number: {item}")
#             continue
#         print(f"Normal number: {item}")

#     counter = 0
#     while counter < 5:
#         counter += 1
#         if counter == 3:
#             continue
#         print(f"Counter: {counter}")

#     for index, value in enumerate(data_list):
#         if index % 2 == 0:
#             print(f"Even index {index}: {value}")

#     indices = list(range(len(data_list)))
#     for idx, val in zip(indices, data_list):
#         if val < 0:
#             print(f"Negative at {idx}: {val}")

#     data_dict = {f"key_{i}": i*2 for i in range(3)}
#     for key in data_dict.keys():
#         print(f"Key: {key}")

#     for value in data_dict.values():
#         if value > 2:
#             print(f"Large value: {value}")

#     for k, v in data_dict.items():
#         if v % 2 == 0:
#             print(f"Even pair: {k}={v}")

#     for outer in range(3):
#         for inner in range(2):
#             if outer + inner > 2:
#                 break
#             print(f"Nested: {outer}, {inner}")

#     result_list = []
#     for x in data_list:
#         if x % 2 == 0:
#             result_list.append(x * 2)

#     return result_list


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
