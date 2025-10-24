# CFGの深さ優先探索ツール
# 2回まで同じノードを訪問可能（ループ考慮）
# パス数解決

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx

def find_entry_exit_nodes(cfg):
    """エントリーノードと出口ノードを特定"""
    entry_nodes = []
    exit_nodes = []

    for node in cfg.nodes():
        # エントリーノード: 前ノードがない、または_is_entrypointがTrue
        if (len(list(cfg.predecessors(node))) == 0 or
            getattr(node, '_is_entrypoint', False)):
            entry_nodes.append(node)

        # 出口ノード: 後ノードがない、または_is_exitpointがTrue
        if (len(list(cfg.successors(node))) == 0 or
            getattr(node, '_is_exitpoint', False)):
            exit_nodes.append(node)

    return entry_nodes, exit_nodes

def dfs_traverse_simple(cfg, start_node, visited_count=None, path=None, max_visits=2):
    """シンプルなループ考慮DFS（パス記録のみ）"""
    if visited_count is None:
        visited_count = {}
    if path is None:
        path = []

    # 訪問回数を記録
    visited_count[start_node] = visited_count.get(start_node, 0) + 1
    path.append(start_node)

    # 後続ノードを探索（最大訪問回数制限あり）
    for successor in cfg.successors(start_node):
        if visited_count.get(successor, 0) < max_visits:
            dfs_traverse_simple(cfg, successor, visited_count, path, max_visits)

    return path

def collect_all_paths(cfg, start_node, end_node, visited_count=None, current_path=None, all_paths=None, max_visits=2):
    """全実行パスを収集（ループ考慮）"""
    if visited_count is None:
        visited_count = {}
    if current_path is None:
        current_path = []
    if all_paths is None:
        all_paths = []

    # 訪問回数チェック
    if visited_count.get(start_node, 0) >= max_visits:
        return all_paths

    # 現在のパスに追加
    new_visited = visited_count.copy()
    new_visited[start_node] = new_visited.get(start_node, 0) + 1
    new_path = current_path + [start_node]

    # 終了ノードに到達した場合
    if start_node == end_node:
        all_paths.append(new_path)
        return all_paths

    # 後続ノードを探索
    for successor in cfg.successors(start_node):
        collect_all_paths(cfg, successor, end_node, new_visited, new_path, all_paths, max_visits)

    return all_paths



def dfs_cfg_analysis(source_file):
    """CFGの深さ優先探索解析"""
    print(f"🚀 CFG深さ優先探索解析: {source_file}")
    print("="*80)

    # CFGを取得
    try:
        cfgs = fast_cfgs_from_source(source_file)

        for cfg_name, cfg in cfgs.items():
            # オペレータCFGはスキップ
            if cfg_name.startswith('<operator>'):
                continue

            print(f"\n📊 CFG: {cfg_name}")

            if cfg.number_of_nodes() == 0:
                print("  空のCFGです")
                continue

            # エントリーと出口ノードを特定
            entry_nodes, exit_nodes = find_entry_exit_nodes(cfg)

            if not entry_nodes or not exit_nodes:
                print("  エントリーまたは出口ノードが見つかりません")
                continue

            # 全パスを収集
            all_execution_paths = []
            for entry in entry_nodes:
                for exit_node in exit_nodes:
                    paths = collect_all_paths(cfg, entry, exit_node, max_visits=2)
                    all_execution_paths.extend(paths)

            # 結果表示
            print(f"\nパス総数: {len(all_execution_paths)}")
            for i, path in enumerate(all_execution_paths, 1):
                # ノードのアドレス部分のみ抽出（例: "1.0" → "1"）
                node_ids = []
                for node in path:
                    node_str = str(node)
                    if '.' in node_str:
                        node_id = node_str.split('.')[0]
                    else:
                        node_id = node_str
                    node_ids.append(node_id)

                path_str = "->".join(node_ids)
                print(f"{path_str}")

            print("\n" + "="*80)

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    # テストファイル（実際のファイル名に変更）
    test_files = ["while.py"]

    for test_file in test_files:
        try:
            dfs_cfg_analysis(test_file)
        except FileNotFoundError:
            print(f"ファイルが見つかりません: {test_file}")
        except Exception as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    main()
