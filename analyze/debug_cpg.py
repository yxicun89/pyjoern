# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# """
# PyJoernのCPG機能を検証するデバッグスクリプト
# AST, CFGがどのように実装され、連携しているかを詳細に分析
# """

# from pyjoern import parse_source, fast_cfgs_from_source
# import networkx as nx
# from collections import defaultdict
# import json
# import matplotlib.pyplot as plt
# import os

# def debug_cpg_capabilities():
#     """PyJoernのCPG機能を検証"""
#     print("="*80)
#     print("=== PyJoernのCPG機能検証 ===")
#     print("="*80)

#     file_path = "whiletest.py"

#     try:
#         print("\n1. 基本的なパース解析:")
#         functions = parse_source(file_path)

#         if not functions:
#             print("関数が検出されませんでした")
#             return

#         print(f"検出された関数: {list(functions.keys())}")

#         # 選択した関数を分析（最初の関数を使用）
#         func_name = list(functions.keys())[0]
#         func_obj = functions[func_name]

#         print(f"\n=== 関数 {func_name} の分析 ===")
#         print(f"開始行: {func_obj.start_line}")
#         print(f"終了行: {func_obj.end_line}")

#         # 利用可能な属性を調査
#         func_attrs = dir(func_obj)
#         print("\n利用可能な関数オブジェクトの属性:")
#         for attr in sorted(func_attrs):
#             if not attr.startswith('__'):
#                 print(f"- {attr}")

#         # CFG分析
#         if hasattr(func_obj, 'cfg') and func_obj.cfg:
#             analyze_cfg(func_obj.cfg, func_name)
#         else:
#             print("\nCFGが利用できません")

#         # AST分析
#         if hasattr(func_obj, 'ast') and func_obj.ast:
#             analyze_ast(func_obj.ast, func_name)
#         else:
#             print("\nASTが利用できません")

#         # CPG機能の検証
#         print("\n2. CPG機能の検証:")
#         verify_cpg_features(func_obj)

#         # CFG-ASTの接続を検証
#         print("\n3. CFG-AST連携の検証:")
#         verify_cfg_ast_connections(func_obj)

#         # データフローエッジの検証
#         print("\n4. データフロー分析の検証:")
#         verify_dataflow_capabilities(func_obj)

#         # 統合CPGの構築を試みる
#         print("\n5. 手動でのCPG構築:")
#         manual_cpg = build_manual_cpg(func_obj)
#         if manual_cpg:
#             print(f"手動で構築したCPG - ノード数: {len(manual_cpg.nodes)}, エッジ数: {len(manual_cpg.edges)}")
#             # CPGの可視化
#             visualize_graph(manual_cpg, f"{func_name}_manual_cpg")

#     except Exception as e:
#         print(f"エラーが発生しました: {e}")
#         import traceback
#         traceback.print_exc()

# def analyze_cfg(cfg, func_name):
#     """CFGの詳細分析"""
#     print(f"\n=== CFG分析 ({func_name}) ===")
#     print(f"グラフ型: {type(cfg)}")
#     print(f"ノード数: {len(cfg.nodes)}")
#     print(f"エッジ数: {len(cfg.edges)}")

#     # ノードタイプの分析
#     node_types = defaultdict(int)
#     node_attrs = defaultdict(int)

#     for node in cfg.nodes:
#         node_type = type(node).__name__
#         node_types[node_type] += 1

#         # 利用可能な属性を収集
#         for attr in dir(node):
#             if not attr.startswith('__'):
#                 node_attrs[attr] += 1

#     print("\nCFGノードタイプ:")
#     for ntype, count in node_types.items():
#         print(f"- {ntype}: {count}個")

#     print("\nCFGノード共通属性 (上位10):")
#     for attr, count in sorted(node_attrs.items(), key=lambda x: x[1], reverse=True)[:10]:
#         print(f"- {attr}: {count}個のノードに存在")

#     # エッジの特性
#     edge_attrs = set()
#     for u, v, data in cfg.edges(data=True):
#         for key in data:
#             edge_attrs.add(key)

#     print("\nCFGエッジ属性:")
#     for attr in sorted(edge_attrs):
#         print(f"- {attr}")

#     # CFGの可視化
#     visualize_graph(cfg, f"{func_name}_cfg")

# def analyze_ast(ast, func_name):
#     """ASTの詳細分析"""
#     print(f"\n=== AST分析 ({func_name}) ===")
#     print(f"グラフ型: {type(ast)}")
#     print(f"ノード数: {len(ast.nodes)}")
#     print(f"エッジ数: {len(ast.edges)}")

#     # ノードタイプの分析
#     node_types = defaultdict(int)
#     string_nodes = 0
#     object_nodes = 0

#     for node in ast.nodes:
#         if isinstance(node, str):
#             string_nodes += 1
#             node_type = "string"
#         else:
#             object_nodes += 1
#             node_type = type(node).__name__

#         node_types[node_type] += 1

#     print("\nASTノード分類:")
#     print(f"- 文字列ノード: {string_nodes}個")
#     print(f"- オブジェクトノード: {object_nodes}個")

#     print("\nASTノードタイプ:")
#     for ntype, count in node_types.items():
#         print(f"- {ntype}: {count}個")

#     # オブジェクトノードの詳細
#     object_attrs = defaultdict(int)
#     ast_node_types = set()

#     for node in ast.nodes:
#         if not isinstance(node, str) and hasattr(node, '__dict__'):
#             for attr in node.__dict__:
#                 object_attrs[attr] += 1

#             # ASTノードタイプ属性があれば抽出
#             if hasattr(node, 'ast_type'):
#                 ast_node_types.add(getattr(node, 'ast_type'))

#     print("\nASTオブジェクトノード共通属性 (上位10):")
#     for attr, count in sorted(object_attrs.items(), key=lambda x: x[1], reverse=True)[:10]:
#         print(f"- {attr}: {count}個のノードに存在")

#     if ast_node_types:
#         print("\nAST_TYPE値の種類:")
#         for ast_type in sorted(ast_node_types):
#             print(f"- {ast_type}")

#     # ASTの可視化
#     visualize_graph(ast, f"{func_name}_ast")

# def verify_cpg_features(func_obj):
#     """CPG特有の機能を検証"""
#     print("CPG特有の機能検証:")

#     # 1. 単一グラフとしてのCPGが存在するか
#     has_cpg = hasattr(func_obj, 'cpg')
#     print(f"- 専用CPG属性の存在: {'あり' if has_cpg else 'なし'}")

#     if has_cpg:
#         cpg = func_obj.cpg
#         print(f"  CPGグラフ: ノード数={len(cpg.nodes)}, エッジ数={len(cpg.edges)}")

#     # 2. CFGとASTの連携を検証
#     cfg = getattr(func_obj, 'cfg', None)
#     ast = getattr(func_obj, 'ast', None)

#     if cfg and ast:
#         # CFGノードからASTノードへの参照があるか
#         cfg_to_ast_refs = False
#         for cfg_node in cfg.nodes:
#             if hasattr(cfg_node, 'ast_node') or hasattr(cfg_node, 'ast_nodes'):
#                 cfg_to_ast_refs = True
#                 break

#         print(f"- CFGノードからASTノードへの直接参照: {'あり' if cfg_to_ast_refs else 'なし'}")

#         # ASTノードからCFGノードへの参照があるか
#         ast_to_cfg_refs = False
#         for ast_node in ast.nodes:
#             if not isinstance(ast_node, str) and (hasattr(ast_node, 'cfg_node') or hasattr(ast_node, 'cfg_nodes')):
#                 ast_to_cfg_refs = True
#                 break

#         print(f"- ASTノードからCFGノードへの直接参照: {'あり' if ast_to_cfg_refs else 'なし'}")

#     # 3. エッジタイプの多様性
#     edge_types = set()

#     if cfg:
#         for u, v, data in cfg.edges(data=True):
#             if 'type' in data:
#                 edge_types.add(data['type'])

#     if ast:
#         for u, v, data in ast.edges(data=True):
#             if 'type' in data:
#                 edge_types.add(data['type'])

#     print(f"- エッジタイプの多様性: {'あり' if edge_types else 'なし'}")
#     if edge_types:
#         print(f"  検出されたエッジタイプ: {sorted(edge_types)}")

#     # 4. PDG（プログラム依存グラフ）の存在
#     has_pdg = hasattr(func_obj, 'pdg')
#     print(f"- PDG（プログラム依存グラフ）: {'あり' if has_pdg else 'なし'}")

#     # 5. データフロー分析機能
#     has_dataflow = hasattr(func_obj, 'dataflow') or hasattr(func_obj, 'data_flow')
#     print(f"- データフロー分析機能: {'あり' if has_dataflow else 'なし'}")

# def verify_cfg_ast_connections(func_obj):
#     """CFGとASTの接続を検証"""
#     print("CFG-AST連携検証:")

#     cfg = getattr(func_obj, 'cfg', None)
#     ast = getattr(func_obj, 'ast', None)

#     if not cfg or not ast:
#         print("- CFGまたはASTが利用できません")
#         return

#     # 1. CFGノード内のステートメントとASTノードの関連を調査
#     connections = []

#     for cfg_node in cfg.nodes:
#         if hasattr(cfg_node, 'statements') and cfg_node.statements:
#             for stmt in cfg_node.statements:
#                 stmt_str = str(stmt)
#                 stmt_type = type(stmt).__name__

#                 # AST内で類似の情報を検索
#                 for ast_node in ast.nodes:
#                     if not isinstance(ast_node, str) and hasattr(ast_node, '__dict__'):
#                         ast_dict = ast_node.__dict__

#                         # 文字列表現が一致するか確認
#                         ast_str = str(ast_node)
#                         if stmt_str in ast_str or ast_str in stmt_str:
#                             connections.append((cfg_node, ast_node))
#                             break

#     print(f"- 検出されたCFG-AST間の潜在的接続: {len(connections)}個")

#     # 詳細表示
#     for i, (cfg_node, ast_node) in enumerate(connections[:3]):  # 最初の3つだけ表示
#         print(f"\n  接続 {i+1}:")
#         print(f"  CFGノード: Block:{cfg_node.addr}")
#         if hasattr(cfg_node, 'statements'):
#             for stmt in cfg_node.statements:
#                 print(f"    - {stmt}")

#         print(f"  ASTノード: {type(ast_node).__name__}")
#         if hasattr(ast_node, '__dict__'):
#             for key, value in ast_node.__dict__.items():
#                 print(f"    - {key}: {value}")

#     if len(connections) > 3:
#         print(f"  ... 他 {len(connections) - 3} 個の接続")

# def verify_dataflow_capabilities(func_obj):
#     """データフロー分析機能を検証"""
#     print("データフロー分析機能検証:")

#     cfg = getattr(func_obj, 'cfg', None)

#     if not cfg:
#         print("- CFGが利用できません")
#         return

#     # 1. 変数定義と使用の検出
#     var_defs = {}  # 変数定義箇所
#     var_uses = defaultdict(list)  # 変数使用箇所

#     for node in cfg.nodes:
#         if hasattr(node, 'statements') and node.statements:
#             for stmt in node.statements:
#                 stmt_str = str(stmt)
#                 stmt_type = type(stmt).__name__

#                 # 変数定義
#                 if stmt_type == 'Assignment':
#                     var_match = stmt_str.split('=')[0].strip()
#                     if var_match:
#                         var_defs[var_match] = node

#                 # 変数使用
#                 elif stmt_type in ['Compare', 'Call']:
#                     for var_name in var_defs:
#                         if var_name in stmt_str:
#                             var_uses[var_name].append(node)

#     print(f"- 検出された変数定義: {len(var_defs)}個")
#     for var_name, node in list(var_defs.items())[:3]:  # 最初の3つだけ表示
#         print(f"  - {var_name}: Block:{node.addr}")

#     print(f"- 検出された変数使用: {sum(len(uses) for uses in var_uses.values())}個")
#     for var_name, nodes in list(var_uses.items())[:3]:  # 最初の3つだけ表示
#         print(f"  - {var_name}: {len(nodes)}箇所で使用")

#     # 2. データフロー分析が可能か検証
#     print("\nデータフロー経路:")
#     data_flows = []

#     for var_name, def_node in var_defs.items():
#         for use_node in var_uses.get(var_name, []):
#             if def_node != use_node:
#                 try:
#                     # 定義から使用へのパスがあるか
#                     if nx.has_path(cfg, def_node, use_node):
#                         paths = list(nx.all_simple_paths(cfg, def_node, use_node))
#                         data_flows.append((var_name, def_node, use_node, len(paths)))
#                 except Exception:
#                     pass

#     if data_flows:
#         print(f"- 検出されたデータフロー経路: {len(data_flows)}個")
#         for i, (var_name, def_node, use_node, path_count) in enumerate(data_flows[:3]):  # 最初の3つだけ表示
#             print(f"  {i+1}. {var_name}: Block:{def_node.addr} → Block:{use_node.addr} (経路数: {path_count})")

#         if len(data_flows) > 3:
#             print(f"  ... 他 {len(data_flows) - 3} 個のデータフロー")
#     else:
#         print("- データフロー経路は検出されませんでした")

#     # 3. 組み込みのデータフロー分析機能があるか
#     has_native_dataflow = False

#     # 関数オブジェクトにデータフロー分析メソッドがあるか
#     for attr in dir(func_obj):
#         if 'flow' in attr.lower() or 'depend' in attr.lower():
#             has_native_dataflow = True
#             print(f"- 潜在的なデータフロー分析関数: {attr}")

#     if not has_native_dataflow:
#         print("- 組み込みのデータフロー分析機能は見つかりませんでした")

# def build_manual_cpg(func_obj):
#     """CFGとASTを手動で統合してCPGを構築"""
#     print("手動CPG構築:")

#     cfg = getattr(func_obj, 'cfg', None)
#     ast = getattr(func_obj, 'ast', None)

#     if not cfg or not ast:
#         print("- CFGまたはASTが利用できません")
#         return None

#     try:
#         # 新しいグラフを作成
#         cpg = nx.DiGraph()

#         print("1. CFGノードとエッジをコピー中...")
#         # CFGのノードとエッジをコピー
#         for node in cfg.nodes:
#             cpg.add_node(node, type='CFG_NODE', source='cfg')

#         for u, v in cfg.edges:
#             cpg.add_edge(u, v, type='CFG_EDGE')

#         print("2. ASTノードとエッジをコピー中...")
#         # ASTのノードとエッジをコピー (IDの衝突を避けるため前置詞を追加)
#         ast_node_mapping = {}
#         for node in ast.nodes:
#             if isinstance(node, str):
#                 # 文字列ノードはそのままIDとして扱えない可能性があるため変換
#                 new_node = f"AST_STR_{hash(node) % 10000}"
#                 cpg.add_node(new_node, type='AST_NODE', source='ast', value=node)
#                 ast_node_mapping[node] = new_node
#             else:
#                 # オブジェクトノードには一意の識別子を割り当て
#                 new_node = f"AST_OBJ_{id(node) % 10000}"
#                 node_attrs = {k: str(v) for k, v in node.__dict__.items()} if hasattr(node, '__dict__') else {}
#                 cpg.add_node(new_node, type='AST_NODE', source='ast', **node_attrs)
#                 ast_node_mapping[node] = new_node

#         for u, v in ast.edges:
#             new_u = ast_node_mapping.get(u)
#             new_v = ast_node_mapping.get(v)
#             if new_u and new_v:
#                 cpg.add_edge(new_u, new_v, type='AST_EDGE')

#         print("3. データフローエッジを追加中...")
#         # 変数定義と使用の検出
#         var_defs = {}
#         var_uses = defaultdict(list)

#         for node in cfg.nodes:
#             if hasattr(node, 'statements') and node.statements:
#                 for stmt in node.statements:
#                     stmt_str = str(stmt)
#                     stmt_type = type(stmt).__name__

#                     # 変数定義
#                     if stmt_type == 'Assignment':
#                         var_match = stmt_str.split('=')[0].strip()
#                         if var_match:
#                             var_defs[var_match] = node

#                     # 変数使用
#                     elif stmt_type in ['Compare', 'Call']:
#                         for var_name in var_defs:
#                             if var_name in stmt_str:
#                                 var_uses[var_name].append(node)

#         # データフローエッジの追加
#         dataflow_edges = 0
#         for var_name, def_node in var_defs.items():
#             for use_node in var_uses.get(var_name, []):
#                 if def_node != use_node:
#                     cpg.add_edge(def_node, use_node, type='DATA_FLOW_EDGE', variable=var_name)
#                     dataflow_edges += 1

#         print(f"- 追加されたデータフローエッジ: {dataflow_edges}個")

#         # CFGノードとASTノード間のリンク（簡易的）
#         print("4. CFG-AST連携エッジを追加中...")
#         cfg_ast_links = 0

#         for cfg_node in cfg.nodes:
#             if hasattr(cfg_node, 'statements') and cfg_node.statements:
#                 stmt_strs = [str(stmt) for stmt in cfg_node.statements]

#                 # ASTノードとの類似度でリンク
#                 for ast_node_key, ast_node_val in cpg.nodes(data=True):
#                     if ast_node_val.get('source') == 'ast':
#                         # ASTノードの属性値を全てチェック
#                         for attr_val in ast_node_val.values():
#                             if isinstance(attr_val, str):
#                                 for stmt_str in stmt_strs:
#                                     # 文字列が含まれているか
#                                     if (len(stmt_str) > 3 and len(attr_val) > 3 and
#                                         (stmt_str in attr_val or attr_val in stmt_str)):
#                                         cpg.add_edge(cfg_node, ast_node_key, type='CFG_AST_LINK')
#                                         cfg_ast_links += 1
#                                         break

#         print(f"- 追加されたCFG-ASTリンク: {cfg_ast_links}個")

#         # 統計情報
#         node_types = defaultdict(int)
#         edge_types = defaultdict(int)

#         for _, attrs in cpg.nodes(data=True):
#             node_types[attrs.get('type', 'unknown')] += 1

#         for _, _, attrs in cpg.edges(data=True):
#             edge_types[attrs.get('type', 'unknown')] += 1

#         print("\nCPG統計:")
#         print(f"- 総ノード数: {len(cpg.nodes)}")
#         print(f"- 総エッジ数: {len(cpg.edges)}")

#         print("- ノード種類別内訳:")
#         for ntype, count in node_types.items():
#             print(f"  - {ntype}: {count}個")

#         print("- エッジ種類別内訳:")
#         for etype, count in edge_types.items():
#             print(f"  - {etype}: {count}個")

#         return cpg

#     except Exception as e:
#         print(f"手動CPG構築エラー: {e}")
#         import traceback
#         traceback.print_exc()
#         return None

# def visualize_graph(graph, filename):
#     """グラフを可視化して保存"""
#     try:
#         plt.figure(figsize=(12, 8))

#         # ノードの色を設定
#         node_colors = []
#         for node in graph.nodes:
#             if isinstance(graph, nx.DiGraph) and hasattr(graph, 'nodes') and len(graph.nodes) > 0:
#                 # ノードに属性があるか確認
#                 if isinstance(graph.nodes, dict) and node in graph.nodes and isinstance(graph.nodes[node], dict):
#                     node_type = graph.nodes[node].get('type', '')
#                     if 'CFG_NODE' in str(node_type):
#                         node_colors.append('skyblue')
#                     elif 'AST_NODE' in str(node_type):
#                         node_colors.append('lightgreen')
#                     else:
#                         node_colors.append('lightgray')
#                 else:
#                     # CFGノードかどうかで色分け
#                     if hasattr(node, 'statements'):
#                         node_colors.append('skyblue')
#                     else:
#                         node_colors.append('lightgray')
#             else:
#                 node_colors.append('lightgray')

#         # エッジの色を設定
#         edge_colors = []
#         for u, v, data in graph.edges(data=True):
#             edge_type = data.get('type', '')
#             if 'CFG_EDGE' in str(edge_type):
#                 edge_colors.append('blue')
#             elif 'AST_EDGE' in str(edge_type):
#                 edge_colors.append('green')
#             elif 'DATA_FLOW_EDGE' in str(edge_type):
#                 edge_colors.append('red')
#             elif 'CFG_AST_LINK' in str(edge_type):
#                 edge_colors.append('purple')
#             else:
#                 edge_colors.append('gray')

#         # レイアウトを設定
#         pos = nx.spring_layout(graph, k=0.8, iterations=50)

#         # ノードを描画
#         nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=300, alpha=0.8)

#         # ノードラベルを設定
#         node_labels = {}
#         for node in graph.nodes:
#             if hasattr(node, 'addr'):
#                 node_labels[node] = f"Block:{node.addr}"
#             elif isinstance(node, str) and node.startswith('AST_'):
#                 node_labels[node] = node[:10]  # 最初の10文字
#             else:
#                 node_labels[node] = str(node)[:10]

#         # ラベルを描画
#         nx.draw_networkx_labels(graph, pos, labels=node_labels, font_size=8)

#         # エッジを描画
#         nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, arrowsize=15, alpha=0.6)

#         plt.title(f"{filename} Graph")
#         plt.axis('off')

#         # ディレクトリがなければ作成
#         os.makedirs('graph_images', exist_ok=True)

#         # 保存
#         plt.tight_layout()
#         plt.savefig(f"graph_images/{filename}.png", dpi=300, bbox_inches='tight')
#         plt.close()

#         print(f"グラフを graph_images/{filename}.png に保存しました")

#     except Exception as e:
#         print(f"グラフ可視化エラー: {e}")

# if __name__ == "__main__":
#     debug_cpg_capabilities()


# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# """
# PyJoernのデータフロー機能とPDG存在検証スクリプト
# """

# from pyjoern import parse_source
# import networkx as nx
# from collections import defaultdict
# import os
# import matplotlib.pyplot as plt
# import re

# class PyJoernGraphChecker:
#     def __init__(self, file_path):
#         """初期化"""
#         self.file_path = file_path
#         self.functions = None
#         self.dfg = None  # データフローグラフ
#         self.pdg = None  # プログラム依存グラフ

#     def parse_file(self):
#         """ファイルをパース"""
#         print(f"ファイル '{self.file_path}' をパース中...")
#         try:
#             self.functions = parse_source(self.file_path)
#             function_names = list(self.functions.keys())
#             print(f"検出された関数: {function_names}")
#             return len(function_names) > 0
#         except Exception as e:
#             print(f"パースエラー: {e}")
#             return False

#     def check_graphs_existence(self):
#         """各種グラフの存在をチェック"""
#         if not self.functions:
#             print("関数が見つかりません。先にparse_file()を実行してください。")
#             return

#         results = {}
#         for func_name, func_obj in self.functions.items():
#             print(f"\n==== 関数 '{func_name}' の解析 ====")

#             # 利用可能なグラフと属性を確認
#             graphs = {}
#             graphs["cfg"] = hasattr(func_obj, "cfg") and func_obj.cfg is not None
#             graphs["ast"] = hasattr(func_obj, "ast") and func_obj.ast is not None
#             graphs["dfg"] = hasattr(func_obj, "dfg") and func_obj.dfg is not None
#             graphs["pdg"] = hasattr(func_obj, "pdg") and func_obj.pdg is not None

#             # その他可能性のある名前のグラフも確認
#             for attr in dir(func_obj):
#                 if attr.lower().endswith(('graph', 'g', 'flow', 'depend')) and attr not in ['cfg', 'ast', 'dfg', 'pdg']:
#                     value = getattr(func_obj, attr)
#                     if isinstance(value, nx.Graph) or isinstance(value, nx.DiGraph):
#                         graphs[attr] = True

#             print("グラフ存在確認:")
#             for graph_name, exists in graphs.items():
#                 print(f"- {graph_name.upper()}: {'あり' if exists else 'なし'}")

#             results[func_name] = graphs

#         return results

#     def build_dataflow_graph(self, func_name=None):
#         """データフローグラフを構築"""
#         if not self.functions:
#             print("関数が見つかりません。先にparse_file()を実行してください。")
#             return None

#         # 関数名が指定されていない場合、最初の関数を使用
#         if func_name is None:
#             func_name = list(self.functions.keys())[0]
#             print(f"関数名が指定されていないため '{func_name}' を使用します。")

#         if func_name not in self.functions:
#             print(f"関数 '{func_name}' が見つかりません。")
#             return None

#         func_obj = self.functions[func_name]

#         # すでにDFGが存在するか確認
#         if hasattr(func_obj, 'dfg') and func_obj.dfg:
#             print(f"関数 '{func_name}' には既にDFGが存在します！")
#             self.dfg = func_obj.dfg
#             return func_obj.dfg

#         # CFGがなければ構築できない
#         if not hasattr(func_obj, 'cfg') or not func_obj.cfg:
#             print(f"関数 '{func_name}' にはCFGがありません。DFGを構築できません。")
#             return None

#         print(f"\n==== 関数 '{func_name}' のデータフローグラフ(DFG)を構築 ====")

#         # 新しいグラフを作成
#         dfg = nx.DiGraph(name=f"{func_name}_dfg")

#         # 変数の定義と使用を追跡
#         var_defs = {}  # 変数 -> 定義ノード
#         var_uses = defaultdict(list)  # 変数 -> 使用ノード

#         # CFGの各ノードを処理
#         for node in func_obj.cfg.nodes:
#             # ノードをDFGに追加
#             dfg.add_node(node, type='CFG_NODE')

#             if hasattr(node, 'statements') and node.statements:
#                 # 各ステートメントの変数定義・使用を検出
#                 for stmt in node.statements:
#                     stmt_str = str(stmt)
#                     stmt_type = type(stmt).__name__

#                     # 変数の定義を検出 (代入文)
#                     if stmt_type == 'Assignment':
#                         # 左辺(変数名)を取得
#                         var_match = re.match(r'(\w+)\s*=', stmt_str)
#                         if var_match:
#                             var_name = var_match.group(1)
#                             var_defs[var_name] = node
#                             print(f"  変数定義: '{var_name}' in Block:{node.addr}")

#                             # 右辺で使用されている変数を検出
#                             right_side = stmt_str.split('=', 1)[1]
#                             for v in var_defs:
#                                 if v in right_side:
#                                     var_uses[v].append(node)
#                                     print(f"  変数使用: '{v}' in Block:{node.addr} (代入右辺)")

#                     # 複合代入演算子 (+=, -=, etc.)
#                     elif 'assignment' in stmt_str.lower() and any(op in stmt_str for op in ['Plus', 'Minus', 'Mult', 'Div']):
#                         var_match = re.search(r'(\w+)\s*[+\-*/]?=', stmt_str)
#                         if var_match:
#                             var_name = var_match.group(1)
#                             # 同じノードで定義と使用
#                             var_defs[var_name] = node
#                             var_uses[var_name].append(node)
#                             print(f"  変数定義+使用: '{var_name}' in Block:{node.addr} (複合代入)")

#                     # 条件文での変数使用
#                     elif stmt_type == 'Compare':
#                         for var_name in var_defs:
#                             if var_name in stmt_str:
#                                 var_uses[var_name].append(node)
#                                 print(f"  変数使用: '{var_name}' in Block:{node.addr} (条件)")

#                     # 関数呼び出しでの変数使用
#                     elif stmt_type == 'Call':
#                         for var_name in var_defs:
#                             if var_name in stmt_str:
#                                 var_uses[var_name].append(node)
#                                 print(f"  変数使用: '{var_name}' in Block:{node.addr} (関数呼び出し)")

#         # データフローエッジを追加
#         flow_count = 0
#         for var_name, def_node in var_defs.items():
#             for use_node in var_uses.get(var_name, []):
#                 if def_node != use_node:  # 自己参照でない場合
#                     # 定義から使用へのパスが実行フロー上で存在するか確認
#                     try:
#                         if nx.has_path(func_obj.cfg, def_node, use_node):
#                             dfg.add_edge(def_node, use_node, type='DATA_FLOW', variable=var_name)
#                             flow_count += 1
#                             print(f"  データフロー: {var_name}: Block:{def_node.addr} -> Block:{use_node.addr}")
#                     except nx.NetworkXNoPath:
#                         pass

#         print(f"\n合計 {flow_count} 個のデータフローエッジを構築しました")

#         # DFGを保存
#         self.dfg = dfg
#         return dfg

#     def check_pdg_existence(self):
#         """PDG（プログラム依存グラフ）の存在を確認"""
#         if not self.functions:
#             print("関数が見つかりません。先にparse_file()を実行してください。")
#             return False

#         pdg_found = False
#         pdg_details = {}

#         print("\n==== PDG存在確認 ====")

#         for func_name, func_obj in self.functions.items():
#             # 直接的なPDG属性を確認
#             direct_pdg = hasattr(func_obj, 'pdg') and func_obj.pdg is not None

#             # PDGっぽい名前の属性を探す
#             pdg_like_attrs = []
#             for attr in dir(func_obj):
#                 if 'pdg' in attr.lower() or 'dependence' in attr.lower() or 'depend' in attr.lower():
#                     pdg_like_attrs.append(attr)

#             # PDG関連のメソッドを探す
#             pdg_methods = []
#             for method_name in dir(func_obj):
#                 if callable(getattr(func_obj, method_name)) and ('pdg' in method_name.lower() or 'depend' in method_name.lower()):
#                     pdg_methods.append(method_name)

#             print(f"関数 '{func_name}':")
#             print(f"  直接PDG属性: {'あり' if direct_pdg else 'なし'}")
#             print(f"  PDG関連属性: {pdg_like_attrs if pdg_like_attrs else 'なし'}")
#             print(f"  PDG関連メソッド: {pdg_methods if pdg_methods else 'なし'}")

#             if direct_pdg:
#                 pdg_found = True
#                 self.pdg = func_obj.pdg
#                 pdg_details[func_name] = {
#                     'nodes': len(func_obj.pdg.nodes),
#                     'edges': len(func_obj.pdg.edges)
#                 }
#                 print(f"  PDG詳細: ノード数={pdg_details[func_name]['nodes']}, エッジ数={pdg_details[func_name]['edges']}")

#         return pdg_found, pdg_details

#     def construct_pdg(self, func_name=None):
#         """CFGとDFGからPDGを手動で構築"""
#         if not self.functions:
#             print("関数が見つかりません。先にparse_file()を実行してください。")
#             return None

#         # 関数名が指定されていない場合、最初の関数を使用
#         if func_name is None:
#             func_name = list(self.functions.keys())[0]

#         if func_name not in self.functions:
#             print(f"関数 '{func_name}' が見つかりません。")
#             return None

#         func_obj = self.functions[func_name]

#         # 既にPDGが存在する場合
#         if hasattr(func_obj, 'pdg') and func_obj.pdg:
#             print(f"関数 '{func_name}' には既にPDGが存在します！")
#             self.pdg = func_obj.pdg
#             return func_obj.pdg

#         print(f"\n==== 関数 '{func_name}' のプログラム依存グラフ(PDG)を構築 ====")

#         # CFGが必要
#         if not hasattr(func_obj, 'cfg') or not func_obj.cfg:
#             print("CFGが存在しないためPDGを構築できません。")
#             return None

#         # DFGがなければ構築
#         if self.dfg is None:
#             self.build_dataflow_graph(func_name)

#         if self.dfg is None:
#             print("DFGを構築できなかったためPDGを構築できません。")
#             return None

#         # 新しいPDGグラフを作成
#         pdg = nx.DiGraph(name=f"{func_name}_pdg")

#         print("1. 制御依存関係を追加...")
#         # CFGからノードをコピー
#         for node in func_obj.cfg.nodes:
#             pdg.add_node(node, type='CFG_NODE')

#         # 制御依存エッジを追加（簡易版: 条件ブロックから直接の後続ブロックへ）
#         control_edges = 0
#         for node in func_obj.cfg.nodes:
#             if hasattr(node, 'statements') and node.statements:
#                 is_conditional = False
#                 for stmt in node.statements:
#                     # 条件文を含むノードを検出
#                     if type(stmt).__name__ == 'Compare' or 'Compare' in str(stmt):
#                         is_conditional = True
#                         break

#                 if is_conditional:
#                     # 条件ノードからの直接の後続ノードへ制御依存エッジを追加
#                     for succ in func_obj.cfg.successors(node):
#                         pdg.add_edge(node, succ, type='CONTROL_DEPENDENCE')
#                         control_edges += 1

#         print(f"  制御依存エッジ: {control_edges}個")

#         print("2. データ依存関係を追加...")
#         # DFGからデータ依存エッジをコピー
#         data_edges = 0
#         for u, v, data in self.dfg.edges(data=True):
#             pdg.add_edge(u, v, type='DATA_DEPENDENCE', **data)
#             data_edges += 1

#         print(f"  データ依存エッジ: {data_edges}個")

#         print(f"\n構築されたPDG: ノード数={len(pdg.nodes)}, エッジ数={len(pdg.edges)}")

#         # PDGを保存
#         self.pdg = pdg
#         return pdg

#     def visualize_graph(self, graph, filename, show_labels=True):
#         """グラフを可視化して保存"""
#         if graph is None:
#             print(f"グラフが存在しないため、可視化できません。")
#             return

#         try:
#             plt.figure(figsize=(12, 10))

#             # ノードの色を設定
#             node_colors = []
#             for node in graph.nodes:
#                 node_data = graph.nodes[node]
#                 node_type = str(node_data.get('type', ''))

#                 if 'CFG_NODE' in node_type:
#                     # 特殊なCFGノードをさらに分類
#                     if hasattr(node, 'statements') and node.statements:
#                         for stmt in node.statements:
#                             stmt_type = type(stmt).__name__
#                             if stmt_type == 'Compare':
#                                 node_colors.append('orange')  # 条件ノード
#                                 break
#                             elif 'range(' in str(stmt) or 'iterator' in str(stmt).lower():
#                                 node_colors.append('yellow')  # ループノード
#                                 break
#                         else:
#                             node_colors.append('lightblue')  # 通常のCFGノード
#                     else:
#                         node_colors.append('lightblue')
#                 else:
#                     node_colors.append('lightgray')  # その他のノード

#             # エッジの色とスタイルを設定
#             edge_colors = []
#             edge_styles = []

#             for u, v, data in graph.edges(data=True):
#                 edge_type = str(data.get('type', '')).upper()

#                 if 'CONTROL' in edge_type:
#                     edge_colors.append('red')
#                     edge_styles.append('solid')
#                 elif 'DATA' in edge_type:
#                     edge_colors.append('blue')
#                     edge_styles.append('dashed')
#                 else:
#                     edge_colors.append('gray')
#                     edge_styles.append('dotted')

#             # レイアウトを設定（大きなグラフでも見やすいように）
#             pos = nx.spring_layout(graph, k=0.9, iterations=50, seed=42)

#             # ノードを描画
#             nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=300, alpha=0.8)

#             # ラベルを設定
#             if show_labels:
#                 node_labels = {}
#                 for node in graph.nodes:
#                     if hasattr(node, 'addr'):
#                         node_labels[node] = f"Block:{node.addr}"
#                     else:
#                         node_labels[node] = str(node)[:10]  # 最初の10文字

#                 # ラベルを描画
#                 nx.draw_networkx_labels(graph, pos, labels=node_labels, font_size=8)

#             # エッジをスタイル別に描画
#             for i, (u, v) in enumerate(graph.edges()):
#                 nx.draw_networkx_edges(
#                     graph, pos, edgelist=[(u, v)],
#                     edge_color=[edge_colors[i]],
#                     style=edge_styles[i],
#                     arrows=True, arrowsize=10, alpha=0.7
#                 )

#             # エッジラベルを追加
#             if show_labels:
#                 edge_labels = {}
#                 for u, v, data in graph.edges(data=True):
#                     if 'variable' in data:
#                         edge_labels[(u, v)] = data['variable']

#                 if edge_labels:
#                     nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=7)

#             # グラフタイプに応じたタイトル
#             if hasattr(graph, 'name') and graph.name:
#                 plt.title(graph.name)
#             else:
#                 graph_type = "不明"
#                 if self.dfg is not None and graph == self.dfg:
#                     graph_type = "データフローグラフ (DFG)"
#                 elif self.pdg is not None and graph == self.pdg:
#                     graph_type = "プログラム依存グラフ (PDG)"

#                 plt.title(graph_type)

#             plt.axis('off')

#             # ディレクトリがなければ作成
#             os.makedirs('graph_images', exist_ok=True)

#             # 保存
#             plt.tight_layout()
#             output_path = f"graph_images/{filename}.png"
#             plt.savefig(output_path, dpi=300, bbox_inches='tight')
#             plt.close()

#             print(f"グラフを {output_path} に保存しました")

#         except Exception as e:
#             print(f"グラフ可視化エラー: {e}")
#             import traceback
#             traceback.print_exc()

#     def create_legends(self):
#         """グラフの凡例を別ファイルとして作成"""
#         try:
#             plt.figure(figsize=(8, 6))

#             # ノード凡例
#             plt.subplot(2, 1, 1)
#             plt.title("ノード凡例")

#             node_types = [
#                 {"label": "条件ブロック", "color": "orange"},
#                 {"label": "ループブロック", "color": "yellow"},
#                 {"label": "通常ブロック", "color": "lightblue"},
#                 {"label": "その他ノード", "color": "lightgray"}
#             ]

#             for i, node in enumerate(node_types):
#                 plt.scatter([i], [0], s=300, c=node["color"], label=node["label"], alpha=0.8)

#             plt.legend(loc="center", ncol=2)
#             plt.axis('off')

#             # エッジ凡例
#             plt.subplot(2, 1, 2)
#             plt.title("エッジ凡例")

#             edge_types = [
#                 {"label": "制御依存", "color": "red", "style": "solid"},
#                 {"label": "データ依存", "color": "blue", "style": "dashed"},
#                 {"label": "その他エッジ", "color": "gray", "style": "dotted"}
#             ]

#             for i, edge in enumerate(edge_types):
#                 plt.plot([0, 1], [i, i], c=edge["color"], linestyle=edge["style"], label=edge["label"])

#             plt.legend(loc="center")
#             plt.axis('off')

#             # 保存
#             os.makedirs('graph_images', exist_ok=True)
#             plt.tight_layout()
#             plt.savefig("graph_images/legend.png", dpi=300, bbox_inches='tight')
#             plt.close()

#             print("凡例を graph_images/legend.png に保存しました")

#         except Exception as e:
#             print(f"凡例作成エラー: {e}")

# def main():
#     """メイン関数"""
#     test_file = "whiletest.py"

#     # ファイルが存在しない場合、サンプルを作成
#     if not os.path.exists(test_file):
#         print(f"テストファイル '{test_file}' が見つかりません。サンプルを作成します。")
#         with open(test_file, "w") as f:
#             f.write("""
# def simple_function():
#     a = 5
#     b = 10
#     c = a + b

#     if c > 10:
#         d = c * 2
#     else:
#         d = c / 2

#     for i in range(d):
#         if i % 2 == 0:
#             print(i)

#     return d

# def data_flow_test():
#     x = 1      # 定義
#     y = x + 1  # 使用 + 定義

#     if y > 5:  # 使用
#         z = y  # 使用 + 定義
#     else:
#         z = x  # 使用 + 定義

#     return z   # 使用
# """)
#         print(f"サンプルファイル '{test_file}' を作成しました。")

#     checker = PyJoernGraphChecker(test_file)

#     # 1. ファイルをパース
#     if not checker.parse_file():
#         print("ファイルのパースに失敗しました。終了します。")
#         return

#     # 2. グラフの存在を確認
#     checker.check_graphs_existence()

#     # 3. PDGが存在するか確認
#     pdg_exists, pdg_details = checker.check_pdg_existence()

#     # 4. DFG（データフローグラフ）を構築
#     dfg = checker.build_dataflow_graph()
#     if dfg:
#         # DFGを可視化
#         checker.visualize_graph(dfg, "dataflow_graph", show_labels=True)

#     # 5. PDGが存在しなければ構築を試みる
#     if not pdg_exists:
#         print("\nPDGが存在しないため、手動で構築します。")
#         pdg = checker.construct_pdg()
#         if pdg:
#             # PDGを可視化
#             checker.visualize_graph(pdg, "program_dependence_graph", show_labels=True)

#     # 6. 凡例の作成
#     checker.create_legends()

#     print("\n分析完了！")

# if __name__ == "__main__":
#     main()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyJoernのDDG（Data Dependence Graph）を活用したデータフロー解析
"""

from pyjoern import parse_source
import networkx as nx
from collections import defaultdict
import os
import matplotlib.pyplot as plt

class DDGAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.functions = None

    def parse_and_analyze(self):
        """ファイルをパースしてDDGを分析"""
        print(f"ファイル '{self.file_path}' をパース中...")

        try:
            self.functions = parse_source(self.file_path)
            function_names = list(self.functions.keys())
            print(f"検出された関数: {function_names}")

            for func_name, func_obj in self.functions.items():
                print(f"\n=== 関数 '{func_name}' のDDG分析 ===")
                self.analyze_ddg(func_obj, func_name)

        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()

    def analyze_ddg(self, func_obj, func_name):
        """DDGの詳細分析"""

        # DDGが存在するか確認
        if not hasattr(func_obj, 'ddg') or func_obj.ddg is None:
            print(f"DDGが存在しません")
            return

        ddg = func_obj.ddg
        print(f"DDG情報:")
        print(f"- グラフタイプ: {type(ddg)}")
        print(f"- ノード数: {len(ddg.nodes)}")
        print(f"- エッジ数: {len(ddg.edges)}")

        # ノードの詳細分析
        print(f"\nDDGノードの詳細:")
        for i, node in enumerate(ddg.nodes):
            if i >= 5:  # 最初の5つだけ表示
                print(f"... 他 {len(ddg.nodes) - 5} 個のノード")
                break

            print(f"ノード {i+1}:")
            print(f"  タイプ: {type(node).__name__}")
            print(f"  文字列表現: {str(node)}")

            # ノードの属性を調査
            if hasattr(node, '__dict__'):
                for attr, value in node.__dict__.items():
                    print(f"  {attr}: {value}")
            print()

        # エッジの詳細分析
        print(f"DDGエッジの詳細:")
        edge_count = 0
        for u, v, data in ddg.edges(data=True):
            if edge_count >= 10:  # 最初の10個だけ表示
                print(f"... 他 {len(ddg.edges) - 10} 個のエッジ")
                break

            edge_count += 1
            print(f"エッジ {edge_count}: {u} -> {v}")
            if data:
                for key, value in data.items():
                    print(f"  {key}: {value}")
            print()

        # データフロー情報の抽出
        self.extract_dataflow_from_ddg(ddg, func_name)

        # DDGの可視化
        self.visualize_ddg(ddg, func_name)

    def extract_dataflow_from_ddg(self, ddg, func_name):
        """DDGからデータフロー情報を抽出"""
        print(f"\n=== {func_name} のデータフロー情報 ===")

        # 変数ごとのデータフロー
        variable_flows = defaultdict(list)

        for u, v, data in ddg.edges(data=True):
            # エッジから変数情報を抽出
            variable = None

            # データ属性から変数名を探す
            if 'variable' in data:
                variable = data['variable']
            elif 'label' in data:
                variable = data['label']

            # ノードから変数名を推測
            if variable is None:
                u_str = str(u)
                v_str = str(v)

                # 代入文から変数名を抽出
                if '=' in u_str:
                    parts = u_str.split('=')
                    if len(parts) >= 2:
                        variable = parts[0].strip()
                elif '=' in v_str:
                    parts = v_str.split('=')
                    if len(parts) >= 2:
                        variable = parts[0].strip()

            if variable:
                variable_flows[variable].append({
                    'from': u,
                    'to': v,
                    'data': data
                })

        # 結果表示
        if variable_flows:
            print(f"検出されたデータフロー:")
            for var, flows in variable_flows.items():
                print(f"\n変数 '{var}':")
                for i, flow in enumerate(flows):
                    print(f"  フロー {i+1}: {flow['from']} -> {flow['to']}")
                    if flow['data']:
                        for key, value in flow['data'].items():
                            print(f"    {key}: {value}")
        else:
            print("明示的なデータフローは検出されませんでした")

        # 特徴量抽出のためのメトリクス計算
        self.calculate_dataflow_metrics(ddg, variable_flows, func_name)

    def calculate_dataflow_metrics(self, ddg, variable_flows, func_name):
        """データフローメトリクスを計算"""
        print(f"\n=== {func_name} のデータフローメトリクス ===")

        metrics = {}

        # 基本メトリクス
        metrics['total_dataflow_edges'] = len(ddg.edges)
        metrics['unique_variables'] = len(variable_flows)
        metrics['total_variable_flows'] = sum(len(flows) for flows in variable_flows.values())

        # 変数ごとの統計
        if variable_flows:
            flow_counts = [len(flows) for flows in variable_flows.values()]
            metrics['max_variable_flows'] = max(flow_counts)
            metrics['avg_variable_flows'] = sum(flow_counts) / len(flow_counts)
        else:
            metrics['max_variable_flows'] = 0
            metrics['avg_variable_flows'] = 0

        # ノードの入次数・出次数分析
        in_degrees = [ddg.in_degree(node) for node in ddg.nodes]
        out_degrees = [ddg.out_degree(node) for node in ddg.nodes]

        metrics['max_in_degree'] = max(in_degrees) if in_degrees else 0
        metrics['max_out_degree'] = max(out_degrees) if out_degrees else 0
        metrics['avg_in_degree'] = sum(in_degrees) / len(in_degrees) if in_degrees else 0
        metrics['avg_out_degree'] = sum(out_degrees) / len(out_degrees) if out_degrees else 0

        # 結果表示
        print("データフローメトリクス:")
        for key, value in metrics.items():
            print(f"- {key}: {value}")

        return metrics

    def visualize_ddg(self, ddg, func_name):
        """DDGを可視化"""
        try:
            plt.figure(figsize=(14, 10))

            # ノードの色とサイズを設定
            node_colors = []
            node_sizes = []

            for node in ddg.nodes:
                # ノードの種類に応じて色分け
                node_str = str(node)

                if '=' in node_str and any(op in node_str for op in ['+', '-', '*', '/']):
                    node_colors.append('lightcoral')  # 演算ノード
                    node_sizes.append(400)
                elif '=' in node_str:
                    node_colors.append('lightblue')   # 代入ノード
                    node_sizes.append(350)
                elif 'compare' in node_str.lower() or '<' in node_str or '>' in node_str:
                    node_colors.append('orange')      # 比較ノード
                    node_sizes.append(300)
                elif 'call' in node_str.lower() or '(' in node_str:
                    node_colors.append('lightgreen')  # 関数呼び出しノード
                    node_sizes.append(300)
                else:
                    node_colors.append('lightgray')   # その他
                    node_sizes.append(250)

            # エッジの色を設定
            edge_colors = []
            for u, v, data in ddg.edges(data=True):
                if 'type' in data:
                    edge_type = str(data['type']).lower()
                    if 'data' in edge_type:
                        edge_colors.append('blue')
                    elif 'control' in edge_type:
                        edge_colors.append('red')
                    else:
                        edge_colors.append('gray')
                else:
                    edge_colors.append('blue')  # デフォルトはデータフロー

            # レイアウト計算
            if len(ddg.nodes) > 20:
                # 大きなグラフの場合は階層レイアウト
                pos = nx.spring_layout(ddg, k=1.5, iterations=100)
            else:
                # 小さなグラフの場合はより詳細なレイアウト
                pos = nx.spring_layout(ddg, k=1.0, iterations=200)

            # ノードを描画
            nx.draw_networkx_nodes(ddg, pos,
                                 node_color=node_colors,
                                 node_size=node_sizes,
                                 alpha=0.8)

            # エッジを描画
            nx.draw_networkx_edges(ddg, pos,
                                 edge_color=edge_colors,
                                 arrows=True,
                                 arrowsize=15,
                                 alpha=0.6,
                                 width=1.5)

            # ラベルを描画（ノード数が少ない場合のみ）
            if len(ddg.nodes) <= 15:
                node_labels = {}
                for node in ddg.nodes:
                    label = str(node)
                    if len(label) > 20:
                        label = label[:17] + "..."
                    node_labels[node] = label

                nx.draw_networkx_labels(ddg, pos, labels=node_labels, font_size=8)

            plt.title(f"DDG (Data Dependence Graph) - {func_name}", fontsize=14)
            plt.axis('off')

            # 凡例を追加
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightcoral',
                          markersize=10, label='演算ノード'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue',
                          markersize=10, label='代入ノード'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange',
                          markersize=10, label='比較ノード'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen',
                          markersize=10, label='関数呼び出し'),
                plt.Line2D([0], [0], color='blue', label='データフローエッジ'),
                plt.Line2D([0], [0], color='red', label='制御フローエッジ')
            ]

            plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))

            # 保存
            os.makedirs('graph_images', exist_ok=True)
            output_path = f"graph_images/ddg_{func_name}.png"
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            print(f"DDGを {output_path} に保存しました")

        except Exception as e:
            print(f"DDG可視化エラー: {e}")
            import traceback
            traceback.print_exc()

def main():
    """メイン実行関数"""
    test_file = "whiletest.py"

    analyzer = DDGAnalyzer(test_file)
    analyzer.parse_and_analyze()

if __name__ == "__main__":
    main()
