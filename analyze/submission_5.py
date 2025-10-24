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






# 試行中: whiletest.py
# ファイル 'whiletest.py' のCFG解析
# 📊 parse_source で検出された関数: ['example']
#   ✓ 解析対象: example (ノード数: 12)

# 🔍 'example' の解析:
#   Connected Components: 1
#   📋 ステートメント解析:
#     - x < 0...
#     - x > 10...
#     - print(&quot;Done&quot;)...
#     - print(&quot;NotDone&quot;)...
#     - FUNCTION_END...
#     - <UnsupportedStmt: UNKNOWN,iteratorNonEmptyOrException,iteratorNonEmptyOrExceptio...
#     - FUNCTION_START...
#     - x > 0...
#     - <UnsupportedStmt: ['formattedValue', '{x}']>...
#       ✓ ループ文検出: for
#     - <UnsupportedStmt: ['formatString', 'f&quot;Negative:{x}&quot;']>...
#       ✓ ループ文検出: for
#     - print(f&quot;Negative:{x}&quot;)...
#     - <UnsupportedStmt: ['assignmentPlus', 'x+=1']>...
#     - <UnsupportedStmt: ['formattedValue', '{i}']>...
#       ✓ ループ文検出: for
#     - <UnsupportedStmt: ['formatString', 'f&quot;Even:{i}&quot;']>...
#       ✓ ループ文検出: for
#     - print(f&quot;Even:{i}&quot;)...
#     - <UnsupportedStmt: ['formattedValue', '{i}']>...
#       ✓ ループ文検出: for
#     - <UnsupportedStmt: ['formatString', 'f&quot;Odd:{i}&quot;']>...
#       ✓ ループ文検出: for
#     - print(f&quot;Odd:{i}&quot;)...
#     - range(x)...
#     - tmp1 = range(x)...
#     - <UnsupportedStmt: FIELD_IDENTIFIER,__iter__,__iter__>...
#     - <UnsupportedStmt: ['fieldAccess', 'tmp1.__iter__']>...
#     - <UnsupportedStmt: __iter__,tmp1.__iter__()>...
#     - <UnsupportedStmt: >...
#     - <UnsupportedStmt: )>...
#     - <UnsupportedStmt: FIELD_IDENTIFIER,__next__,__next__>...
#     - <UnsupportedStmt: ['fieldAccess', 'tmp0.__next__']>...
#     - <UnsupportedStmt: __next__,tmp0.__next__()>...
#     - i = tmp0.__next__()...
#     - <UnsupportedStmt: ['modulo', 'i%2']>...
#     - i%2 == 0...
#   🔍 条件文解析:
#     ✓ 条件文検出: <UnsupportedStmt: FIELD_IDENTIFIER,__iter__,__iter__>...
#     ✓ 条件文検出: <UnsupportedStmt: FIELD_IDENTIFIER,__next__,__next__>...
# 📊 fast_cfgs_from_source で検出されたCFG: ['&lt;operator&gt;.fieldAccess', '&lt;module&gt;', '&lt;operator&gt;.assignmentPlus', '&lt;operator&gt;.greaterThan', '&lt;operator&gt;.formatString', '&lt;operator&gt;.lessThan', '&lt;operator&gt;.formattedValue', '&lt;operator&gt;.assignment', '&lt;operator&gt;.equals', '&lt;operator&gt;.modulo', 'example']
#   🚫 オペレータスキップ: &lt;operator&gt;.fieldAccess
#   ✓ 追加解析対象: &lt;module&gt; (ノード数: 3)

# 🔍 '&lt;module&gt;' の解析:
#   Connected Components: 1
#   📋 ステートメント解析:
#     - example(5)...
#     - FUNCTION_END...
#     - FUNCTION_START...
#     - <UnsupportedStmt: TYPE_REF,__builtins__.print,__builtins__.print>...
#     - print = __builtins__.print...
#     - <UnsupportedStmt: TYPE_REF,__builtins__.range,__builtins__.range>...
#     - range = __builtins__.range...
#     - <UnsupportedStmt: TYPE_REF,__builtins__.range,__builtins__.range>...
#     - range = __builtins__.range...
#     - FUNCTION_START...
#     - example = defexample(...)...
#     - __name__ == &quot;__main__&quot;...
#   🔍 条件文解析:
#   🚫 オペレータスキップ: &lt;operator&gt;.assignmentPlus
#   🚫 オペレータスキップ: &lt;operator&gt;.greaterThan
#   🚫 オペレータスキップ: &lt;operator&gt;.formatString
#   🚫 オペレータスキップ: &lt;operator&gt;.lessThan
#   🚫 オペレータスキップ: &lt;operator&gt;.formattedValue
#   🚫 オペレータスキップ: &lt;operator&gt;.assignment
#   🚫 オペレータスキップ: &lt;operator&gt;.equals
#   🚫 オペレータスキップ: &lt;operator&gt;.modulo
#   ⚠️  重複スキップ: example

# ================================================================================
# 特徴量結果
# ================================================================================

# example:
#   connected_components: 1
#   loop_statements: 6 (for/while: 6, recursion: 0)
#   conditional_statements: 2
#   cycles: 3
#   paths: 4
#   cyclomatic_complexity: 6

# &lt;module&gt;:
#   connected_components: 1
#   loop_statements: 0 (for/while: 0, recursion: 0)
#   conditional_statements: 0
#   cycles: 0
#   paths: 2
#   cyclomatic_complexity: 2

# ================================================================================
# プログラム全体の特徴量合計（静的解析）
# ================================================================================
# 関数数: 2
# connected_components: 1 (論理和: 1つでも使用されていれば1)
# loop_statements合計: 6 (for/while: 6, recursion: 0)
# conditional_statements合計: 2
# cycles合計: 3
# paths合計: 6
# cyclomatic_complexity合計: 8








# def example(x):
#     if x > 0 :          # x: 読み込み (1回目)
#         for i in range(x): # x: 読み込み (2回目), i: ループ変数定義
#             if i % 2 == 0: # i: 読み込み (1回目)
#                 print(i)  # i: 読み込み (2回目)
#             else:
#                 print(i * 2) # i: 読み込み (3回目)
#     else:
#         while x < 0:  # x: 読み込み (3回目)
#             x += 1   # x: 読み込み (4回目) + 代入
#             print(x)  # x: 読み込み (5回目)
#     t = x * 2 # x: 読み込み (6回目) + 代入, t: 代入
#     if t > 10: # t: 読み込み (1回目)
#         print("t is greater than 10")
#     else:
#         print("t is 10 or less")
#         for j in range(t):  # t: 読み込み (2回目), j: ループ変数定義
#             print(j) # j: 読み込み (1回目)
#     my_list = [19, 3] # my_list: 代入
#     for l in my_list: # my_list: 読み込み (1回目), l: ループ変数定義
#         print(l) # l: 読み込み (4回目)

# if __name__ == "__main__":
#     example(5) # x: 代入
