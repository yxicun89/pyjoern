from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx

def display_cfg_structure(cfg, cfg_name):
    """CFGの構造を詳細に表示する"""
    print(f"\n{'='*80}")
    print(f"CFG: {cfg_name}")
    print(f"{'='*80}")

    print(f"ノード数: {len(cfg.nodes())}")
    print(f"エッジ数: {len(cfg.edges())}")

    print(f"\n🔍 全ノード情報:")
    for i, node in enumerate(cfg.nodes()):
        print(f"\n--- ノード {i+1} ---")
        print(f"ノード: {node}")
        print(f"ノード型: {type(node)}")

        # ノードの属性を全て表示
        if hasattr(node, '__dict__'):
            print(f"ノード属性: {vars(node)}")

        # ステートメント情報
        if hasattr(node, 'statements'):
            print(f"ステートメント数: {len(node.statements) if node.statements else 0}")
            if node.statements:
                for j, stmt in enumerate(node.statements):
                    print(f"  ステートメント {j+1}:")
                    print(f"    内容: {stmt}")
                    print(f"    型: {type(stmt)}")
                    print(f"    文字列: {str(stmt)}")

                    # ステートメントの属性も表示
                    if hasattr(stmt, '__dict__'):
                        attrs = vars(stmt)
                        if attrs:
                            print(f"    属性: {attrs}")
        else:
            print("ステートメント情報なし")

        # 前後のノード情報
        predecessors = list(cfg.predecessors(node))
        successors = list(cfg.successors(node))
        print(f"前ノード数: {len(predecessors)}")
        print(f"後ノード数: {len(successors)}")

        print("-" * 40)

def analyze_cfg_structure(source_file):
    """CFG構造を完全に解析する"""
    print(f"ファイル '{source_file}' のCFG構造解析")
    print(f"{'='*100}")

    # parse_sourceで解析
    print(f"\n🔍 parse_source による解析:")
    try:
        functions = parse_source(source_file)
        print(f"検出関数: {list(functions.keys())}")

        for func_name, func_obj in functions.items():
            print(f"\n📊 関数: {func_name}")
            print(f"関数オブジェクト型: {type(func_obj)}")

            if hasattr(func_obj, '__dict__'):
                print(f"関数属性: {vars(func_obj)}")

            cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
            if cfg:
                display_cfg_structure(cfg, func_name)
            else:
                print(f"❌ CFGが見つかりません")

    except Exception as e:
        print(f"parse_source エラー: {e}")
        import traceback
        traceback.print_exc()

    # fast_cfgs_from_sourceで解析
    print(f"\n🔍 fast_cfgs_from_source による解析:")
    try:
        cfgs = fast_cfgs_from_source(source_file)
        print(f"検出CFG: {list(cfgs.keys())}")

        for cfg_name, cfg in cfgs.items():
            if len(cfg.nodes()) > 0:
                display_cfg_structure(cfg, cfg_name)

    except Exception as e:
        print(f"fast_cfgs_from_source エラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    # テスト用ファイルを解析
    test_files = [
        "while.py"
        # "noi.py"
        # "whiletest.py",
        # "../whiletest.py",
        # "../../visualize/whiletest.py"
    ]

    for test_file in test_files:
        try:
            print(f"\n試行中: {test_file}")
            analyze_cfg_structure(test_file)
            break  # 成功したら終了
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"エラー: {e}")
            continue
    else:
        print("テストファイルが見つかりません。ファイルパスを確認してください。")

if __name__ == "__main__":
    main()
