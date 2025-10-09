def example(x):
  if x > 0:
      for i in range(x):
          if i % 3 == 0:
              print(f"Divisible by 3: {i}")
          elif i % 3 == 1:
              print(f"Remainder 1: {i}")
          else:
              print(f"Remainder 2: {i}")
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
