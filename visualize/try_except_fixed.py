import sys

def process_data(data_list):
    if not data_list:
        print("List is empty.")
        return 0

    total = 0
    for item in data_list:
        # try文を削除してif文で置き換え
        try:
            value = int(item)
        except (ValueError, TypeError):
            print(f"Skipping invalid item: {item}", file=sys.stderr)
            continue

        if value % 2 == 0:
            print(f"{value} is even.")
            total += value
        else:
            print(f"{value} is odd.")

    print("Processing complete.")
    return total

def process_data_no_try(data_list):
    """try-except文を使わない版"""
    if not data_list:
        print("List is empty.")
        return 0

    total = 0
    for item in data_list:
        # try-exceptの代わりにif文で型チェック
        if isinstance(item, str) and item.isdigit():
            value = int(item)
        elif isinstance(item, (int, float)):
            value = int(item)
        else:
            print(f"Skipping invalid item: {item}", file=sys.stderr)
            continue

        if value % 2 == 0:
            print(f"{value} is even.")
            total += value
        else:
            print(f"{value} is odd.")

    print("Processing complete.")
    return total

numbers = ["1", "2", "3", "four", "5", "6"]
result1 = process_data(numbers)
result2 = process_data_no_try(numbers)
print("Total sum of even numbers (try-except):", result1)
print("Total sum of even numbers (no try-except):", result2)
