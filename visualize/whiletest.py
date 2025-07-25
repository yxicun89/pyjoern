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
