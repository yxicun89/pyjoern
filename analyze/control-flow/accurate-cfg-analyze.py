# これが現状の最も正確なCFG解析コード

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx

def extract_accurate_features(cfg, cfg_name):
    """CFG構造分析に基づいた汎用的な特徴量抽出"""
    features = {}

    print(f"\n🔍 '{cfg_name}' の正確な解析:")

    # 1. Connected Components
    try:
        weakly_connected = list(nx.weakly_connected_components(cfg))
        features['connected_components'] = len(weakly_connected)
        print(f"  Connected Components: {features['connected_components']}")
    except Exception:
        features['connected_components'] = 0
        print(f"  Connected Components: 0")

    # 2. ループ文検出（汎用的な検出）
    loop_count = 0
    loop_details = []
    detected_loops = set()  # 重複検出を防ぐためのセット

    print(f"  🔄 ループ文解析:")

    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                # forループ検出: イテレータプロトコル関連のCall文
                if (stmt.__class__.__name__ == 'Call' and
                    hasattr(stmt, 'func') and
                    stmt.func in ['__iter__', '__next__', 'iter', 'next', 'range', 'enumerate', 'zip']):
                    loop_key = f"for-iter-{stmt.func}-{getattr(stmt, 'obj', getattr(stmt, 'args', ['unknown'])[0] if hasattr(stmt, 'args') and stmt.args else 'unknown')}"
                    if loop_key not in detected_loops:
                        loop_count += 1
                        loop_details.append(f"for-loop ({stmt.func}): {stmt}")
                        detected_loops.add(loop_key)
                        print(f"    ✓ forループ検出 ({stmt.func}): {stmt}")

                # イテラブルオブジェクトの代入を検出
                elif (stmt.__class__.__name__ == 'Assignment' and
                      hasattr(stmt, 'src') and
                      hasattr(stmt, 'dst')):
                    src_str = str(getattr(stmt, 'src', ''))
                    if (any(pattern in src_str for pattern in ['.items()', '.keys()', '.values()',
                                                               '.split()', '.readlines()']) or
                        any(var_pattern in src_str for var_pattern in ['list', 'dict', 'items', 'lines'])):
                        loop_key = f"for-assignment-{stmt.dst}-{src_str[:20]}"
                        if loop_key not in detected_loops:
                            loop_count += 1
                            loop_details.append(f"for-loop (iterable): {stmt}")
                            detected_loops.add(loop_key)
                            print(f"    ✓ forループ検出 (iterable): {stmt}")

                # whileループ検出: assignmentPlus（x+=1など）
                elif (stmt.__class__.__name__ == 'UnsupportedStmt' and
                      hasattr(stmt, 'raw_text') and
                      isinstance(stmt.raw_text, list) and
                      len(stmt.raw_text) > 0 and
                      stmt.raw_text[0] == 'assignmentPlus'):
                    loop_count += 1
                    loop_details.append(f"while-loop: {stmt}")
                    print(f"    ✓ whileループ検出: {stmt}")

    features['loop_statements'] = loop_count
    features['loop_details'] = loop_details

    # 3. 条件文検出（Compare文 + イテレータ条件）
    conditional_count = 0
    conditional_details = []
    detected_conditions = set()  # 重複検出を防ぐためのセット

    print(f"  🔍 条件文解析:")

    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                # Compare文を検出（従来の条件文）
                if (stmt.__class__.__name__ == 'Compare' and
                    hasattr(stmt, 'arg1') and hasattr(stmt, 'arg2')):
                    # __name__ == "__main__" は除外（システム条件）
                    if not ((stmt.arg1 == '__name__' and stmt.arg2 == '&quot;__main__&quot;') or
                           (stmt.arg1 == '__name__' and stmt.arg2 == '"__main__"')):
                        conditional_count += 1
                        conditional_details.append(f"condition: {stmt}")
                        print(f"    ✓ 条件文検出: {stmt} (type: {getattr(stmt, 'type', 'unknown')})")
                    else:
                        print(f"    🚫 システム条件除外: {stmt}")

                # forループ条件を検出（イテレータ関連の条件）
                elif (stmt.__class__.__name__ == 'Call' and
                      hasattr(stmt, 'func') and
                      stmt.func in ['__iter__', '__next__', 'iter', 'next', 'range', 'enumerate', 'zip']):
                    condition_key = f"for-condition-{stmt.func}-{getattr(stmt, 'args', ['x'])[0] if hasattr(stmt, 'args') and stmt.args else 'unknown'}"
                    if condition_key not in detected_conditions:
                        conditional_count += 1
                        conditional_details.append(f"for-condition ({stmt.func}): {stmt}")
                        detected_conditions.add(condition_key)
                        print(f"    ✓ forループ条件検出 ({stmt.func}): {stmt}")

                # イテラブルオブジェクトのメソッド呼び出し条件
                elif (stmt.__class__.__name__ == 'Call' and
                      hasattr(stmt, 'func') and
                      any(method in str(stmt.func) for method in ['.items', '.keys', '.values', '.split', '.readlines'])):
                    condition_key = f"for-condition-method-{str(stmt.func)[:20]}"
                    if condition_key not in detected_conditions:
                        conditional_count += 1
                        conditional_details.append(f"for-condition (method): {stmt}")
                        detected_conditions.add(condition_key)
                        print(f"    ✓ forループ条件検出 (method): {stmt}")
                    if condition_key not in detected_conditions:
                        conditional_count += 1
                        conditional_details.append(f"for-condition (method): {stmt}")
                        detected_conditions.add(condition_key)
                        print(f"    ✓ forループ条件検出 (method): {stmt}")

    features['conditional_statements'] = conditional_count
    features['conditional_details'] = conditional_details

    # 4. Cycles
    try:
        cycles = list(nx.simple_cycles(cfg))
        features['cycles'] = len(cycles)
    except Exception:
        features['cycles'] = 0

    # 5. Paths
    try:
        entry_nodes = [n for n in cfg.nodes() if len(list(cfg.predecessors(n))) == 0]
        exit_nodes = [n for n in cfg.nodes() if len(list(cfg.successors(n))) == 0]

        total_paths = 0
        if entry_nodes and exit_nodes:
            for entry in entry_nodes:
                for exit_node in exit_nodes:
                    try:
                        paths = list(nx.all_simple_paths(cfg, entry, exit_node, cutoff=20))
                        total_paths += len(paths)
                    except nx.NetworkXNoPath:
                        continue

        features['paths'] = total_paths
    except Exception:
        features['paths'] = 0

    # 6. Cyclomatic Complexity
    try:
        E = cfg.number_of_edges()
        N = cfg.number_of_nodes()
        P = features.get('connected_components', 1)
        features['cyclomatic_complexity'] = E - N + 2 * P
    except Exception:
        features['cyclomatic_complexity'] = 0

    return features

def analyze_function_metadata(func_obj):
    """関数オブジェクトのメタデータも活用"""
    metadata = {}

    if hasattr(func_obj, 'control_structures'):
        control_structures = func_obj.control_structures
        print(f"  📊 制御構造メタデータ: {control_structures}")

        # control_structuresからループと条件を推定
        loop_indicators = ['iteratorNonEmptyOrException']
        condition_indicators = ['>', '<', '==', '!=', '%']

        metadata_loops = sum(1 for cs in control_structures if any(li in cs for li in loop_indicators))

        # 従来の条件文 + forループ条件
        traditional_conditions = sum(1 for cs in control_structures
                                   if any(ci in cs for ci in condition_indicators)
                                   and not any(li in cs for li in loop_indicators))
        for_loop_conditions = sum(1 for cs in control_structures if any(li in cs for li in loop_indicators))

        metadata_conditions = traditional_conditions + for_loop_conditions

        metadata['metadata_loops'] = metadata_loops
        metadata['metadata_conditions'] = metadata_conditions
        metadata['traditional_conditions'] = traditional_conditions
        metadata['for_loop_conditions'] = for_loop_conditions
        metadata['control_structures'] = control_structures

        print(f"    - メタデータ推定ループ: {metadata_loops}")
        print(f"    - メタデータ推定条件: {metadata_conditions}")
        print(f"      └ 従来条件: {traditional_conditions}")
        print(f"      └ forループ条件: {for_loop_conditions}")

    return metadata

def display_accurate_summary(all_features):
    """正確な特徴量結果を表示"""
    print(f"\n{'='*80}")
    print(f"正確な特徴量結果")
    print(f"{'='*80}")

    for cfg_name, features in all_features.items():
        print(f"\n{cfg_name}:")
        print(f"  connected_components: {features.get('connected_components', 0)}")
        print(f"  loop_statements: {features.get('loop_statements', 0)}")
        print(f"  conditional_statements: {features.get('conditional_statements', 0)}")
        print(f"  cycles: {features.get('cycles', 0)}")
        print(f"  paths: {features.get('paths', 0)}")
        print(f"  cyclomatic_complexity: {features.get('cyclomatic_complexity', 0)}")

        # 詳細情報
        if 'loop_details' in features:
            print(f"  ループ詳細:")
            for detail in features['loop_details']:
                print(f"    - {detail}")

        if 'conditional_details' in features:
            print(f"  条件詳細:")
            for detail in features['conditional_details']:
                print(f"    - {detail}")

        if 'metadata_loops' in features:
            print(f"  メタデータ検証:")
            print(f"    - ループ: {features['metadata_loops']}")
            print(f"    - 条件: {features['metadata_conditions']}")
            if 'traditional_conditions' in features and 'for_loop_conditions' in features:
                print(f"      └ 従来条件: {features['traditional_conditions']}")
                print(f"      └ forループ条件: {features['for_loop_conditions']}")

def analyze_accurate_cfg(source_file):
    """構造に基づいた正確なCFG解析"""
    print(f"ファイル '{source_file}' の正確なCFG解析")
    print(f"{'='*100}")

    all_features = {}

    # parse_sourceで解析
    try:
        functions = parse_source(source_file)
        print(f"📊 検出関数: {list(functions.keys())}")

        for func_name, func_obj in functions.items():
            print(f"\n🎯 関数: {func_name}")

            # メタデータ解析
            metadata = analyze_function_metadata(func_obj)

            # CFG解析
            cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
            if cfg and len(cfg.nodes()) > 0:
                features = extract_accurate_features(cfg, func_name)
                features.update(metadata)  # メタデータを統合
                all_features[func_name] = features

    except Exception as e:
        print(f"parse_source エラー: {e}")
        import traceback
        traceback.print_exc()

    # fast_cfgs_from_sourceで追加解析（モジュールレベル）
    try:
        cfgs = fast_cfgs_from_source(source_file)
        print(f"\n📊 fast_cfgs_from_source 検出CFG: {list(cfgs.keys())}")

        for cfg_name, cfg in cfgs.items():
            # オペレータCFGを除外（空のノードのみ）
            if (cfg_name.startswith('<operator>') or
                cfg_name.startswith('&lt;operator&gt;')):
                print(f"  🚫 オペレータスキップ: {cfg_name}")
                continue

            # 既に解析済みの関数は除外
            if cfg_name in all_features:
                print(f"  ⚠️  重複スキップ: {cfg_name}")
                continue

            # 意味のあるノードを持つCFGのみ解析
            if len(cfg.nodes()) > 0:
                print(f"  ✓ 追加解析対象: {cfg_name}")
                features = extract_accurate_features(cfg, cfg_name)
                all_features[cfg_name] = features

    except Exception as e:
        print(f"fast_cfgs_from_source エラー: {e}")
        import traceback
        traceback.print_exc()

    display_accurate_summary(all_features)
    return all_features

def main():
    """メイン関数"""
    test_files = [
        "whiletest.py",
        "../whiletest.py",
        "../../visualize/whiletest.py"
    ]

    for test_file in test_files:
        try:
            print(f"\n試行中: {test_file}")
            features = analyze_accurate_cfg(test_file)
            break
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"エラー: {e}")
            continue
    else:
        print("テストファイルが見つかりません。")

if __name__ == "__main__":
    main()
