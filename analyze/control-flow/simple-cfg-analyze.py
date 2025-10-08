from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx

def detect_recursion(cfg, func_name):
    """関数内で同名の関数を呼び出しているかを確認して再帰を検出"""
    recursion_count = 0
    debug_info = []  # デバッグ用

    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)

                # 関数定義文や関数開始文は除外
                if ('def ' in stmt_str.lower() or
                    'function_start' in stmt_str.lower() or
                    'FUNCTION_START' in stmt_str):
                    continue

                # シンプルな再帰検出: 関数名 + 括弧の組み合わせ
                if func_name in stmt_str and '(' in stmt_str:
                    recursion_count += 1
                    debug_info.append(f"再帰検出: {stmt_str[:50]}...")

    # デバッグ情報を表示
    if recursion_count > 0:
        print(f"    🔄 関数 '{func_name}' で {recursion_count} 回の再帰呼び出しを検出")
        for info in debug_info:
            print(f"      - {info}")

    return recursion_count

def extract_cfg_features(cfg, func_name):
    """CFGから必要な特徴量のみを抽出する"""
    features = {}

    print(f"\n🔍 '{func_name}' の解析:")

    # 1. Connected Components
    try:
        weakly_connected = list(nx.weakly_connected_components(cfg))
        features['connected_components'] = len(weakly_connected)
        print(f"  Connected Components: {features['connected_components']}")
    except Exception as e:
        features['connected_components'] = 0
        print(f"  Connected Components: 0 (エラー: {e})")

    # 2. Loop Statements (ループ文 + 再帰)
    loop_count = 0
    for_while_count = 0
    print(f"  📋 ステートメント解析:")

    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_lower = stmt_str.lower()
                print(f"    - {stmt_str[:80]}...")

                # まずはシンプルにforまたはwhileが含まれていれば検出（f-string除外のみ）
                if (('for' in stmt_lower or 'while' in stmt_lower) and
                    'formattedValue' not in stmt_str and           # f-string誤検出を除外
                    'formatString' not in stmt_str and            # f-string誤検出を除外
                    not stmt_str.startswith('<UnsupportedStmt: [\'formatted')):  # f-string誤検出を除外

                    # for文またはwhile文の検出（重複OK）
                    is_loop = False
                    loop_type = ""

                    if 'for' in stmt_lower:
                        is_loop = True
                        loop_type = 'for'
                    elif 'while' in stmt_lower:
                        is_loop = True
                        loop_type = 'while'

                    if is_loop:
                        loop_count += 1
                        for_while_count += 1
                        print(f"      ✓ ループ文検出: {loop_type}")
                        print(f"        詳細: {stmt_str[:60]}...")    # 再帰呼び出しもループとしてカウント
    recursion_count = detect_recursion(cfg, func_name)
    loop_count += recursion_count

    features['loop_statements'] = loop_count
    features['for_while_statements'] = for_while_count  # for/while文の数を別途記録
    features['recursion_statements'] = recursion_count  # 再帰数を別途記録

    # 3. Conditional Statements
    conditional_count = 0
    print(f"  🔍 条件文解析:")

    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_lower = stmt_str.lower()

                # まずはシンプルに条件文を検出（重複OK）
                is_conditional = False
                condition_type = ""

                # if文
                if 'if' in stmt_lower:
                    is_conditional = True
                    condition_type = "if"

                # while文の条件部分
                elif 'while' in stmt_lower:
                    is_conditional = True
                    condition_type = "while"

                # Compare文（比較演算）- イテレータ関連は除外
                elif ('Compare:' in stmt_str and
                      '__iter__' not in stmt_str and '__next__' not in stmt_str and
                      'FIELD_IDENTIFIER' not in stmt_str):
                    is_conditional = True
                    condition_type = "compare"

                # 比較演算子を含む文
                elif ('>' in stmt_str or '<' in stmt_str or '==' in stmt_str or '!=' in stmt_str or '%' in stmt_str):
                    # イテレータ関連やシステム文は除外
                    if ('__iter__' not in stmt_str and '__next__' not in stmt_str and
                        'FIELD_IDENTIFIER' not in stmt_str and 'TYPE_REF' not in stmt_str and
                        'FUNCTION_START' not in stmt_str and 'FUNCTION_END' not in stmt_str):
                        is_conditional = True
                        condition_type = "comparison"

                if is_conditional:
                    conditional_count += 1
                    print(f"    ✓ 条件文検出 ({condition_type}): {stmt_str[:60]}...")

    features['conditional_statements'] = conditional_count

    # 4. Cycles
    try:
        cycles = list(nx.simple_cycles(cfg))
        features['cycles'] = len(cycles)
    except Exception as e:
        features['cycles'] = 0

    # 5. Paths
    try:
        entry_nodes = []
        exit_nodes = []

        for node in cfg.nodes():
            predecessors = list(cfg.predecessors(node))
            successors = list(cfg.successors(node))

            if len(predecessors) == 0:
                entry_nodes.append(node)
            if len(successors) == 0:
                exit_nodes.append(node)

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
    except Exception as e:
        features['paths'] = 0

    # 6. Cyclomatic Complexity
    try:
        E = cfg.number_of_edges()
        N = cfg.number_of_nodes()
        P = features.get('connected_components', 1)

        cyclomatic_complexity = E - N + 2 * P
        features['cyclomatic_complexity'] = cyclomatic_complexity
    except Exception as e:
        features['cyclomatic_complexity'] = 0

    return features

def display_features_summary(all_features):
    """特徴量を簡潔に表示"""
    if not all_features:
        print("特徴量データがありません")
        return

    print(f"\n{'='*80}")
    print(f"特徴量結果")
    print(f"{'='*80}")

    for func_name, features in all_features.items():
        print(f"\n{func_name}:")
        print(f"  connected_components: {features.get('connected_components', 0)}")

        # ループ文の詳細表示
        total_loops = features.get('loop_statements', 0)
        for_while_loops = features.get('for_while_statements', 0)
        recursion_loops = features.get('recursion_statements', 0)
        print(f"  loop_statements: {total_loops} (for/while: {for_while_loops}, recursion: {recursion_loops})")

        print(f"  conditional_statements: {features.get('conditional_statements', 0)}")
        print(f"  cycles: {features.get('cycles', 0)}")
        print(f"  paths: {features.get('paths', 0)}")
        print(f"  cyclomatic_complexity: {features.get('cyclomatic_complexity', 0)}")

    # プログラム全体の合計を計算・表示
    display_total_features(all_features)

def display_total_features(all_features):
    """プログラム全体の特徴量合計を表示"""
    if not all_features:
        return

    # 各特徴量の合計を計算
    total_features = {
        'connected_components': 0,  # 論理和で計算（1つでも1なら1）
        'loop_statements': 0,
        'for_while_statements': 0,
        'recursion_statements': 0,
        'conditional_statements': 0,
        'cycles': 0,
        'paths': 0,
        'cyclomatic_complexity': 0
    }

    for func_name, features in all_features.items():
        # connected_componentsは論理和（1つでも1なら1）
        if features.get('connected_components', 0) > 0:
            total_features['connected_components'] = 1

        # その他は合計
        for key in ['loop_statements', 'for_while_statements', 'recursion_statements',
                   'conditional_statements', 'cycles', 'paths', 'cyclomatic_complexity']:
            total_features[key] += features.get(key, 0)

    # 結果表示
    print(f"\n{'='*80}")
    print(f"プログラム全体の特徴量合計（静的解析）")
    print(f"{'='*80}")
    print(f"関数数: {len(all_features)}")
    print(f"connected_components: {total_features['connected_components']} (論理和: 1つでも使用されていれば1)")
    print(f"loop_statements合計: {total_features['loop_statements']} (for/while: {total_features['for_while_statements']}, recursion: {total_features['recursion_statements']})")
    print(f"conditional_statements合計: {total_features['conditional_statements']}")
    print(f"cycles合計: {total_features['cycles']}")
    print(f"paths合計: {total_features['paths']}")
    print(f"cyclomatic_complexity合計: {total_features['cyclomatic_complexity']}")

    return total_features

def analyze_file_cfg(source_file):
    """ソースファイルのCFGから特徴量を抽出"""
    print(f"ファイル '{source_file}' のCFG解析")

    all_features = {}

    # parse_sourceで解析
    try:
        functions = parse_source(source_file)
        print(f"📊 parse_source で検出された関数: {list(functions.keys())}")
        for func_name, func_obj in functions.items():
            cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
            if cfg and len(cfg.nodes()) > 0:
                print(f"  ✓ 解析対象: {func_name} (ノード数: {len(cfg.nodes())})")
                features = extract_cfg_features(cfg, func_name)
                all_features[func_name] = features
    except Exception as e:
        print(f"parse_source エラー: {e}")

    # fast_cfgs_from_sourceで解析
    try:
        cfgs = fast_cfgs_from_source(source_file)
        print(f"📊 fast_cfgs_from_source で検出されたCFG: {list(cfgs.keys())}")
        for cfg_name, cfg in cfgs.items():
            if (len(cfg.nodes()) > 0 and
                not cfg_name.startswith('<operator>') and
                not cfg_name.startswith('&lt;operator&gt;') and
                cfg_name not in all_features):

                print(f"  ✓ 追加解析対象: {cfg_name} (ノード数: {len(cfg.nodes())})")
                features = extract_cfg_features(cfg, cfg_name)
                all_features[cfg_name] = features
            elif cfg_name in all_features:
                print(f"  ⚠️  重複スキップ: {cfg_name}")
            elif cfg_name.startswith('<operator>') or cfg_name.startswith('&lt;operator&gt;'):
                print(f"  🚫 オペレータスキップ: {cfg_name}")
    except Exception as e:
        print(f"fast_cfgs_from_source エラー: {e}")

    display_features_summary(all_features)
    return all_features

def main():
    """メイン関数"""
    # テスト用ファイルを解析
    test_files = [
        "whiletest.py",
        "../whiletest.py",
        "../../visualize/whiletest.py"
    ]

    for test_file in test_files:
        try:
            print(f"\n試行中: {test_file}")
            features = analyze_file_cfg(test_file)
            break  # 成功したら終了
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"エラー: {e}")
            continue
    else:
        print("テストファイルが見つかりません。ファイルパスを確認してください。")

def extract_features_only(source_file):
    """特徴量のみを抽出する軽量版関数"""
    features_dict = {}

    try:
        # parse_sourceで解析
        functions = parse_source(source_file)
        for func_name, func_obj in functions.items():
            cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
            if cfg and len(cfg.nodes()) > 0:
                features = extract_cfg_features(cfg, func_name)
                features_dict[func_name] = features

        # fast_cfgs_from_sourceでも解析
        cfgs = fast_cfgs_from_source(source_file)
        for cfg_name, cfg in cfgs.items():
            if (len(cfg.nodes()) > 0 and
                not cfg_name.startswith('<operator>') and
                not cfg_name.startswith('&lt;operator&gt;') and
                cfg_name not in features_dict):

                features = extract_cfg_features(cfg, cfg_name)
                features_dict[cfg_name] = features

        display_features_summary(features_dict)

    except Exception as e:
        print(f"エラー: {e}")

    return features_dict

if __name__ == "__main__":
    main()
