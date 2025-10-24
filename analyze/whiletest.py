def example(x):
  if x > 0:
      for i in range(x):
          if i % 2 == 0:
              print(f"Even: {i}")
          else:
              print(f"Odd: {i}")
  else:
      while x < 0:
          print(f"Negative: {x}")
          x += 1
  if x > 10:
      print("Done")
  else:
      print("Not Done")

if __name__ == "__main__":
  example(5)

  
# def comprehensive_analysis(data_list, target):
#     """包括的な基本構文を使った関数"""

#     # 1. 条件文 (if-elif-else)
#     if not data_list:  # 条件文3
#         print("Empty list")
#         return None
#     elif len(data_list) == 1:  # 条件文4
#         return data_list[0]

#     # 2. for文 - range使用
#     for i in range(len(data_list)):  # forループ1
#         if data_list[i] == target:  # 条件文5
#             print(f"Found at index {i}")
#             break

#     # 3. for文 - リスト直接反復
#     for item in data_list:  # forループ2
#         if item > 100:  # 条件文6
#             print(f"Large number: {item}")
#             continue
#         print(f"Normal number: {item}")

#     # 4. while文
#     counter = 0
#     while counter < 5:  # whileループ1
#         counter += 1  # compound assignment
#         if counter == 3:  # 条件文7
#             continue
#         print(f"Counter: {counter}")

#     # 5. for文 - enumerate使用
#     for index, value in enumerate(data_list):  # forループ3
#         if index % 2 == 0:  # 条件文8
#             print(f"Even index {index}: {value}")

#     # 6. for文 - zip使用
#     indices = list(range(len(data_list)))
#     for idx, val in zip(indices, data_list):  # forループ4
#         if val < 0:  # 条件文9
#             print(f"Negative at {idx}: {val}")

#     # 7. 辞書操作のfor文
#     data_dict = {f"key_{i}": i*2 for i in range(3)}
#     for key in data_dict.keys():  # forループ5
#         print(f"Key: {key}")

#     for value in data_dict.values():  # forループ6
#         if value > 2:  # 条件文10
#             print(f"Large value: {value}")

#     for k, v in data_dict.items():  # forループ7
#         if v % 2 == 0:  # 条件文11
#             print(f"Even pair: {k}={v}")

#     # 8. ネストしたループと条件
#     for outer in range(3):  # forループ8
#         for inner in range(2):  # forループ9（ネスト）
#             if outer + inner > 2:  # 条件文12
#                 break
#             print(f"Nested: {outer}, {inner}")

#     # 9. リスト内包表記は解析対象外だが、代替案
#     result_list = []
#     for x in data_list:  # forループ10
#         if x % 2 == 0:  # 条件文13
#             result_list.append(x * 2)

#     return result_list


# def example(x):
#     if x > 0:
#         for i in range(x):
#             if i % 2 == 0:
#                 print(i)
#             else:
#                 print(i * 2)
#     else:
#         print(x)
#         x += 1

#     # さらにcomplexなケース
#     t = x * 2
#     if t > 10:
#         for j in range(t):
#             print(j)

#     my_list = [19, 3]
#     for l in my_list:
#         print(l)

#     return x

# if __name__ == "__main__":
#     print(example(5))
