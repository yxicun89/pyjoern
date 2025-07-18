from pyjoern import parse_source, fast_cfgs_from_source
import os
import json
import networkx as nx # NetworkXの例外を扱うためにインポート
from networkx.exception import NetworkXError # Specific exception for clarity

# 解析対象のPythonソースコード
source_code = """
# This is a sample Python program for feature extraction demonstration
import os
import sys

GLOBAL_VAR = "hello" # Global variable

class MyClass:
    CLASS_VAR = 10 # Class variable

    def __init__(self, value):
        self.instance_var = value # Instance variable

    def my_method(self, arg1: int, arg2: str) -> bool:
        local_var = arg1 + 5 # Local variable

        # Function call
        print(f"Arg1: {arg1}, Arg2: {arg2}")

        if local_var > MyClass.CLASS_VAR: # Conditional statement
            temp_result = True
            # Nested function call
            print("Greater!")
        else:
            temp_result = False
            # Loop (though this example doesn't have a direct loop structure for CFG)
            for i in range(3):
                pass

        return temp_result and (GLOBAL_VAR == "hello")

def standalone_function(data):
    if data is None:
        return 0
    return len(data)

if __name__ == "__main__":
    obj = MyClass(20)
    res = obj.my_method(5, "test")
    val = standalone_function([1,2,3])
    print(f"Result from my_method: {res}")
    print(f"Result from standalone_function: {val}")

"""
temp_file = "temp_code_for_features.py"

def print_section_header(title):
    print("\n" + "="*50)
    print(f"=== {title} ===")
    print("="*50)

def extract_and_print_features():
    try:
        with open(temp_file, "w") as f:
            f.write(source_code)
        print(f"一時ファイル '{temp_file}' を作成しました。")

        # --- プログラム要素の抽出 (Full Parse) ---
        print_section_header("1. プログラム要素 (parse_source)")
        functions = parse_source(temp_file)

        if functions:
            print(f"  見つかった関数: {list(functions.keys())}")
            for func_name, func_obj in functions.items():
                print(f"\n--- 関数: {func_name} ---")
                print(f"  タイプ (Pythonクラスの場合はクラス名): {type(func_obj)}")
                print(f"  開始行: {func_obj.start_line}, 終了行: {func_obj.end_line}")
                print(f"  PyJoernオブジェクトの repr(): {repr(func_obj)}")
                print(f"  PyJoernオブジェクトの dir(): {dir(func_obj)}")
                if hasattr(func_obj, '__dict__'):
                    print(f"  PyJoernオブジェクトの __dict__:")
                    print(json.dumps(func_obj.__dict__, indent=2, default=str))

                # 関数のコード内容 (もし取得できるなら)
                # func_obj.code, func_obj.text, func_obj.statements は Function オブジェクトには通常ないかもしれません
                # これらは内部のASTノードなどに含まれる可能性が高いです
                # ただし、__dict__で'code'や'text'があれば表示
                if 'code' in func_obj.__dict__:
                    print(f"  関数コードスニペット (func_obj.code): \n{func_obj.code}")
                elif 'text' in func_obj.__dict__:
                    print(f"  関数コードスニペット (func_obj.text): \n{func_obj.text}")
                # statementsはリストなので、存在するかどうかで判断
                if 'statements' in func_obj.__dict__ and isinstance(func_obj.statements, list):
                     print(f"  関数ステートメントのリスト (func_obj.statements): \n{func_obj.statements[:5]}...")

                # CFG情報の表示
                if func_obj.cfg: # func_obj.cfg が NetworkX の DiGraph オブジェクトのインスタンスであることが期待されます
                    # ノードとエッジの数が0の場合も考慮
                    if not isinstance(func_obj.cfg, nx.DiGraph):
                         print(f"  警告: func_obj.cfg は NetworkX.DiGraph オブジェクトではありません。型: {type(func_obj.cfg)}")
                         # string表示の場合は、nodesやedges属性に直接アクセスできない
                         print(f"  CFG情報が文字列形式です: {func_obj.cfg}")
                         cfg_nodes_list = [] # 空リストで続行
                         cfg_edges_list = [] # 空リストで続行
                    else:
                        print(f"  制御フローグラフ (CFG) ノード数: {len(func_obj.cfg.nodes)}")
                        print(f"  制御フローグラフ (CFG) エッジ数: {len(func_obj.cfg.edges)}")

                        # エラー修正: NodeViewをリストに変換してからスライス
                        cfg_nodes_list = list(func_obj.cfg.nodes)
                        cfg_edges_list = list(func_obj.cfg.edges)

                        print(f"  最初の5つのCFGノード情報:")
                        for i, node in enumerate(cfg_nodes_list[:5]): # 修正適用
                            print(f"    ノード {i+1} ({type(node)}):")
                            print(f"      repr: {repr(node)}")
                            print(f"      dir(): {dir(node)}")
                            if hasattr(node, '__dict__'):
                                print(f"      __dict__:")
                                print(json.dumps(node.__dict__, indent=2, default=str))

                            # CFGノードのコードスニペットの推測
                            node_code_snippet = getattr(node, 'name', None) # 'name'を試す
                            if node_code_snippet is None:
                                node_code_snippet = getattr(node, 'value', None) # 'value'を試す
                            if node_code_snippet is None:
                                node_code_snippet = getattr(node, 'text', None) # 'text'を試す

                            if node_code_snippet:
                                print(f"      コードスニペット: {node_code_snippet}")
                            else:
                                print(f"      コードスニペット: (直接取得できる属性なし)")

                        print(f"  最初の5つのCFGエッジ情報:")
                        for i, edge in enumerate(cfg_edges_list[:5]): # 修正適用
                            print(f"    エッジ {i+1} ({type(edge)}):")
                            print(f"      repr: {repr(edge)}")
                            print(f"      dir(): {dir(edge)}")
                            if hasattr(edge, '__dict__'):
                                print(f"      __dict__:")
                                print(json.dumps(edge.__dict__, indent=2, default=str))
                            # エッジのソースとデスティネーションノードのID (もしあれば)
                            src_id = getattr(getattr(edge, 'src', None), 'id', None)
                            dst_id = getattr(getattr(edge, 'dst', None), 'id', None)
                            if src_id is not None and dst_id is not None:
                                print(f"      ソースノードID: {src_id}, デスティネーションノードID: {dst_id}")

                else:
                    print("  この関数のCFGは生成されませんでした。")

                # DDG情報の表示
                if func_obj.ddg and isinstance(func_obj.ddg, nx.DiGraph):
                    print(f"  データフローグラフ (DDG) ノード数: {len(func_obj.ddg.nodes)}")
                    print(f"  データフローグラフ (DDG) エッジ数: {len(func_obj.ddg.edges)}")
                    # DDGノード/エッジの詳細も同様に表示可能ですが、ここでは省略
                elif func_obj.ddg: # DDGが文字列形式の場合
                    print(f"  データフローグラフ (DDG) 情報が文字列形式です: {func_obj.ddg}")
                else:
                    print("  この関数のDDGは生成されませんでした。")

                # AST情報の表示
                if func_obj.ast and isinstance(func_obj.ast, nx.DiGraph):
                    print(f"  抽象構文木 (AST) ノード数: {len(func_obj.ast.nodes)}")
                    print(f"  抽象構文木 (AST) エッジ数: {len(func_obj.ast.edges)}")
                    # ASTノード/エッジの詳細も同様に表示可能ですが、ここでは省略
                elif func_obj.ast: # ASTが文字列形式の場合
                    print(f"  抽象構文木 (AST) 情報が文字列形式です: {func_obj.ast}")
                else:
                    print("  この関数のASTは生成されませんでした。")


        else:
            print("  解析によって関数が見つかりませんでした。")

        # --- 高速CFG生成 (fast_cfgs_from_source) ---
        print_section_header("2. 高速CFG生成 (fast_cfgs_from_source)")
        cfgs_fast = fast_cfgs_from_source(temp_file)

        if cfgs_fast:
            print(f"  見つかった高速CFG: {list(cfgs_fast.keys())}")
            # 高速CFGの詳細も同様に表示可能ですが、フルパースと重複するためここでは簡潔に
            for func_name, cfg_obj in cfgs_fast.items():
                if isinstance(cfg_obj, nx.DiGraph):
                    print(f"\n--- 高速CFG: {func_name} ---")
                    print(f"  ノード数: {len(cfg_obj.nodes)}, エッジ数: {len(cfg_obj.edges)}")
                    print("  最初の3つのノードrepr:")
                    for node in list(cfg_obj.nodes)[:3]:
                        print(f"    {repr(node)}")
                else:
                     print(f"\n--- 高速CFG: {func_name} ---")
                     print(f"  高速CFG情報が文字列形式です: {cfg_obj}")

        else:
            print("  高速CFG生成によってCFGが見つかりませんでした。")

        # --- その他の可能性のある情報 (CPGノードの種類) ---
        print_section_header("3. その他のJoern CPGノードの種類とプロパティの探索ヒント")
        print("  上記の 'dir()' や '__dict__' の出力で、ノードオブジェクトが持つ多様な情報が見つかります。")
        print("  特に、ノードやエッジの 'type' (文字列) 属性に注目してください。")
        print("  例: node.type (e.g., 'METHOD', 'CALL', 'LOCAL', 'IDENTIFIER', 'LITERAL', 'CONTROL_STRUCTURE', 'UNKNOWN')")
        print("  また、ノードオブジェクトに直接プロパティが存在しない場合でも、")
        print("  Joernの内部的なプロパティが '__dict__' や 'properties' (もしあれば) の中に")
        print("  辞書形式で格納されていることがあります (例: node.properties['CODE'], node.properties['NAME'])。")
        print("  これらの情報を活用することで、変数、リテラル、呼び出し、制御構造などの詳細な情報を抽出できます。")
        print("\nJoernのCPGクエリ言語 (Scala) のドキュメントも参考になります。PyJoernはそれらの概念をPythonオブジェクトとして公開しようとします。")


    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        print("PyJoernまたはJoernバックエンドに問題がある可能性があります。")

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"\n一時ファイル '{temp_file}' を削除しました。")

# スクリプト実行
if __name__ == "__main__":
    extract_and_print_features()
