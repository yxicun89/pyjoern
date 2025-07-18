from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np


# parse_sourceの詳細情報を取得
functions = parse_source("whiletest.py")
for func_name, func_obj in functions.items():
    print(f"=" * 60)
    print(f"関数名: {func_name}")
    print(f"=" * 60)

    # === 基本情報 ===
    print(f"\n--- 基本情報 ---")
    print(f"開始行: {func_obj.start_line}")
    print(f"終了行: {func_obj.end_line}")
    print(f"関数オブジェクトの型: {type(func_obj)}")

    # func_objの全属性を調べる
    print(f"\n--- 利用可能な属性/メソッド ---")
    all_attrs = [attr for attr in dir(func_obj) if not attr.startswith('_')]
    print(f"属性一覧: {all_attrs}")

    # === CFG詳細 ===
    if hasattr(func_obj, 'cfg') and func_obj.cfg:
        print(f"\n--- CFG (制御フローグラフ) 詳細 ---")
        cfg = func_obj.cfg
        print(f"CFG型: {type(cfg)}")
        print(f"CFGノード数: {len(cfg.nodes)}")
        print(f"CFGエッジ数: {len(cfg.edges)}")

        # === ステートメント分析セクション ===
        print(f"\n--- ステートメント詳細分析 ---")

        # ステートメントタイプの統計
        stmt_stats = {}
        all_statements = []

        # CFGノードの詳細
        print(f"\nCFGノード詳細:")
        for i, node in enumerate(cfg.nodes):
            print(f"  ノード{i+1}: Block:{node.addr}")
            print(f"    型: {type(node)}")
            print(f"    エントリー: {node.is_entrypoint}")
            print(f"    エグジット: {node.is_exitpoint}")
            print(f"    マージノード: {node.is_merged_node}")

            # ノードの全属性
            node_attrs = [attr for attr in dir(node) if not attr.startswith('_')]
            print(f"    ノード属性: {node_attrs}")

            # ステートメント詳細
            if hasattr(node, 'statements') and node.statements:
                print(f"    ステートメント数: {len(node.statements)}")
                for j, stmt in enumerate(node.statements):
                    stmt_type = type(stmt).__name__
                    print(f"      文{j+1}: [{stmt_type}] {stmt}")

                    # ステートメント統計収集
                    stmt_stats[stmt_type] = stmt_stats.get(stmt_type, 0) + 1
                    all_statements.append((stmt_type, stmt, node.addr))

                    # ステートメントの属性
                    stmt_attrs = [attr for attr in dir(stmt) if not attr.startswith('_')]
                    print(f"        ステートメント属性: {stmt_attrs}")

                    # ステートメントの詳細プロパティ
                    print(f"        詳細プロパティ:")
                    for attr in stmt_attrs:
                        try:
                            value = getattr(stmt, attr)
                            if not callable(value):
                                print(f"          {attr}: {value} (型: {type(value)})")
                        except Exception as e:
                            print(f"          {attr}: <アクセスエラー: {e}>")

        # === ステートメント統計とサマリー ===
        print(f"\n--- ステートメント統計サマリー ---")
        print(f"総ステートメント数: {len(all_statements)}")
        print(f"ステートメントタイプ別集計:")
        for stmt_type, count in sorted(stmt_stats.items()):
            print(f"  {stmt_type}: {count}回")

        # === ステートメントタイプ別詳細分析 ===
        print(f"\n--- ステートメントタイプ別詳細分析 ---")

        # Compare文の分析
        compare_stmts = [stmt for stmt_type, stmt, addr in all_statements if stmt_type == 'Compare']
        if compare_stmts:
            print(f"\nCompare文の詳細 ({len(compare_stmts)}個):")
            for i, stmt in enumerate(compare_stmts):
                print(f"  Compare{i+1}: {stmt}")
                # Compare文の詳細属性
                if hasattr(stmt, 'operator'):
                    print(f"    演算子: {stmt.operator}")
                if hasattr(stmt, 'left'):
                    print(f"    左辺: {stmt.left}")
                if hasattr(stmt, 'right'):
                    print(f"    右辺: {stmt.right}")

        # Call文の分析
        call_stmts = [stmt for stmt_type, stmt, addr in all_statements if stmt_type == 'Call']
        if call_stmts:
            print(f"\nCall文の詳細 ({len(call_stmts)}個):")
            for i, stmt in enumerate(call_stmts):
                print(f"  Call{i+1}: {stmt}")
                # Call文の詳細属性
                if hasattr(stmt, 'function_name'):
                    print(f"    関数名: {stmt.function_name}")
                if hasattr(stmt, 'arguments'):
                    print(f"    引数: {stmt.arguments}")

        # Assignment文の分析
        assignment_stmts = [stmt for stmt_type, stmt, addr in all_statements if stmt_type == 'Assignment']
        if assignment_stmts:
            print(f"\nAssignment文の詳細 ({len(assignment_stmts)}個):")
            for i, stmt in enumerate(assignment_stmts):
                print(f"  Assignment{i+1}: {stmt}")
                # Assignment文の詳細属性
                if hasattr(stmt, 'target'):
                    print(f"    代入先: {stmt.target}")
                if hasattr(stmt, 'value'):
                    print(f"    値: {stmt.value}")

        # Return文の分析
        return_stmts = [stmt for stmt_type, stmt, addr in all_statements if stmt_type == 'Return']
        if return_stmts:
            print(f"\nReturn文の詳細 ({len(return_stmts)}個):")
            for i, stmt in enumerate(return_stmts):
                print(f"  Return{i+1}: {stmt}")
                # Return文の詳細属性
                if hasattr(stmt, 'value'):
                    print(f"    戻り値: {stmt.value}")

        # Nop文の分析
        nop_stmts = [stmt for stmt_type, stmt, addr in all_statements if stmt_type == 'Nop']
        if nop_stmts:
            print(f"\nNop文の詳細 ({len(nop_stmts)}個):")
            for i, stmt in enumerate(nop_stmts):
                print(f"  Nop{i+1}: {stmt}")
                # Nop文の詳細属性
                if hasattr(stmt, 'operation'):
                    print(f"    操作: {stmt.operation}")

        # UnsupportedStmt文の分析
        unsupported_stmts = [stmt for stmt_type, stmt, addr in all_statements if stmt_type == 'UnsupportedStmt']
        if unsupported_stmts:
            print(f"\nUnsupportedStmt文の詳細 ({len(unsupported_stmts)}個):")
            for i, stmt in enumerate(unsupported_stmts):
                print(f"  UnsupportedStmt{i+1}: {stmt}")
                # UnsupportedStmt文の詳細属性
                if hasattr(stmt, 'raw_statement'):
                    print(f"    生ステートメント: {stmt.raw_statement}")

        # === ステートメントマッピング表示 ===
        print(f"\n--- ステートメント→ノードマッピング ---")
        print("各ステートメントがどのノードに含まれているかの対応表:")
        for stmt_type, stmt, node_addr in all_statements:
            print(f"  [{stmt_type}] {stmt} → ノード:{node_addr}")

    # === AST詳細 ===
    if hasattr(func_obj, 'ast') and func_obj.ast:
        print(f"\n--- AST (抽象構文木) 詳細 ---")
        ast = func_obj.ast
        print(f"AST型: {type(ast)}")
        print(f"ASTノード数: {len(ast.nodes)}")
        print(f"ASTエッジ数: {len(ast.edges)}")

        # ASTノードのサンプル（最初の5個）
        print(f"\nASTノードサンプル（最初の5個）:")
        for i, node in enumerate(list(ast.nodes)[:5]):
            print(f"  ASTノード{i+1}: {node}")
            print(f"    型: {type(node)}")

            # ASTノードの属性
            if hasattr(node, '__dict__'):
                print(f"    属性: {node.__dict__}")

    # === DDG詳細 ===
    if hasattr(func_obj, 'ddg') and func_obj.ddg:
        print(f"\n--- DDG (データ依存グラフ) 詳細 ---")
        ddg = func_obj.ddg
        print(f"DDG型: {type(ddg)}")
        print(f"DDGノード数: {len(ddg.nodes)}")
        print(f"DDGエッジ数: {len(ddg.edges)}")

        # DDGノードのサンプル（最初の5個）
        print(f"\nDDGノードサンプル（最初の5個）:")
        for i, node in enumerate(list(ddg.nodes)[:5]):
            print(f"  DDGノード{i+1}: {node}")
            print(f"    型: {type(node)}")

    # === その他の属性 ===
    print(f"\n--- その他の属性値 ---")
    for attr in all_attrs:
        if attr not in ['cfg', 'ast', 'ddg', 'start_line', 'end_line']:
            try:
                value = getattr(func_obj, attr)
                if not callable(value):
                    print(f"  {attr}: {value} (型: {type(value)})")
                else:
                    print(f"  {attr}: <メソッド>")
            except Exception as e:
                print(f"  {attr}: <アクセスエラー: {e}>")

    # === 関数シグネチャ情報 ===
    if hasattr(func_obj, 'parameters'):
        print(f"\n--- 関数パラメータ ---")
        print(f"パラメータ: {func_obj.parameters}")

    if hasattr(func_obj, 'name'):
        print(f"関数名（内部）: {func_obj.name}")

    if hasattr(func_obj, 'file_path'):
        print(f"ファイルパス: {func_obj.file_path}")

    print(f"\n" + "=" * 60)


print("\n" + "=" * 80)
print("FAST CFG ANALYSIS")
print("=" * 80)

# 現在のコードを拡張
cfgs = fast_cfgs_from_source("whiletest.py")
for cfg_name, cfg in cfgs.items():
    print(f"CFG名: {cfg_name}")
    print(f"ノード数: {len(cfg.nodes)}")
    print(f"エッジ数: {len(cfg.edges)}")

    # === 追加で取得できる情報 ===

    print(f"\n=== CFG詳細情報: {cfg_name} ===")

    # 1. CFGオブジェクトの型と属性
    print(f"CFG型: {type(cfg)}")
    print(f"CFG名前: {cfg.name if hasattr(cfg, 'name') else 'なし'}")
    print(f"有向グラフ: {cfg.is_directed()}")

    # 2. ノードの詳細情報
    print(f"\n--- ノード詳細 ---")
    for i, node in enumerate(cfg.nodes()):
        print(f"ノード{i+1}: {node}")
        print(f"  型: {type(node)}")

        # ノードの属性を確認
        if hasattr(node, '__dict__'):
            print(f"  属性: {list(node.__dict__.keys())}")

        # 利用可能な属性を調べる
        attrs = [attr for attr in dir(node) if not attr.startswith('_')]
        print(f"  利用可能メソッド/属性: {attrs}")

        # 特定の属性があるかチェック
        if hasattr(node, 'addr'):
            print(f"  アドレス: {node.addr}")
        if hasattr(node, 'idx'):
            print(f"  インデックス: {node.idx}")
        if hasattr(node, 'statements'):
            print(f"  ステートメント数: {len(node.statements) if node.statements else 0}")

    # 3. エッジの詳細情報
    print(f"\n--- エッジ詳細 ---")
    for i, (source, target) in enumerate(cfg.edges()):
        print(f"エッジ{i+1}: {source} -> {target}")

        # エッジの属性があるかチェック
        edge_data = cfg.get_edge_data(source, target)
        if edge_data:
            print(f"  エッジデータ: {edge_data}")

    # 4. NetworkXグラフとしての情報
    print(f"\n--- NetworkX情報 ---")
    print(f"密度: {nx.density(cfg):.4f}")

    if cfg.nodes():
        # 連結性チェック（無向グラフとして扱う）
        undirected = cfg.to_undirected()
        print(f"連結成分数: {nx.number_connected_components(undirected)}")

        # 最短パス（エラーチェック付き）
        try:
            nodes_list = list(cfg.nodes())
            if len(nodes_list) >= 2:
                if nx.has_path(cfg, nodes_list[0], nodes_list[-1]):
                    path_length = nx.shortest_path_length(cfg, nodes_list[0], nodes_list[-1])
                    print(f"最初から最後のノードへの最短パス長: {path_length}")
                else:
                    print("最初から最後のノードへのパスなし")
        except Exception as e:
            print(f"パス計算エラー: {e}")

    # 5. ノードとエッジの実際のデータ構造
    print(f"\n--- データ構造詳細 ---")
    if cfg.nodes():
        first_node = list(cfg.nodes())[0]
        print(f"最初のノードの詳細:")
        print(f"  repr: {repr(first_node)}")
        print(f"  str: {str(first_node)}")

        # ノードの全属性を表示
        for attr in dir(first_node):
            if not attr.startswith('_'):
                try:
                    value = getattr(first_node, attr)
                    if not callable(value):
                        print(f"  {attr}: {value}")
                except:
                    print(f"  {attr}: <アクセス不可>")

    print("\n" + "="*50)
