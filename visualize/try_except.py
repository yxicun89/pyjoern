import sys

def process_data(data_list):
    if not data_list:
        print("List is empty.")
        return 0

    total = 0
    for item in data_list:
        try:
            # エラーノード1: 型変換
            value = int(item)
            # ここから if 分岐まで（分析対象区間）
            if value % 2 == 0:
                print(f"{value} is even.")
                total += value
            else:
                print(f"{value} is odd.")
            try:
                result = value / (value % 3 or 1)
                if result > 10:
                    print(f"Result is large: {result}")
                    total += result
                else:
                    print(f"Result is small: {result}")
            except ZeroDivisionError:
                print(f"Division error for item: {item}", file=sys.stderr)
                continue
        except (ValueError, TypeError):
            print(f"Skipping invalid item: {item}", file=sys.stderr)
            continue
        except ZeroDivisionError:
            print(f"Division error for item: {item}", file=sys.stderr)
            continue
        except KeyError:
            print(f"Key error for item: {item}", file=sys.stderr)
            continue

    print("Processing complete.")
    return total

# シンプルなテストデータ
numbers = ["1", "2", "3", "four", "5", "6", "0"]
result = process_data(numbers)
print("Total sum of even numbers:", result)
