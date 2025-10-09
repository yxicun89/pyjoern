# これが現状の最も正確なCFG解析コード

from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx

def detect_language(source_code, filename):
    """ソースコードと拡張子から言語を判定"""
    if filename.endswith('.py'):
        return 'python'
    elif filename.endswith(('.c', '.cpp', '.cxx', '.cc', '.h', '.hpp')):
        return 'c_cpp'
    elif filename.endswith(('.java')):
        return 'java'
    elif filename.endswith(('.js', '.ts')):
        return 'javascript'
    else:
        # ソースコードの内容から推測
        if 'def ' in source_code and ':' in source_code:
            return 'python'
        elif '#include' in source_code:
            return 'c_cpp'
        elif 'public class' in source_code:
            return 'java'
        elif 'function ' in source_code or 'const ' in source_code:
            return 'javascript'
        else:
            return 'unknown'

def remove_comments(source_code, language):
    """言語別にコメントを除去"""
    import re

    lines = source_code.split('\n')
    clean_lines = []

    if language == 'python':
        # Python: # で始まる行コメント、'''や"""の複数行コメント
        in_multiline_single = False
        in_multiline_double = False

        for line in lines:
            clean_line = line

            # 複数行コメント処理
            if '"""' in line:
                if not in_multiline_double:
                    # 開始
                    parts = line.split('"""')
                    clean_line = parts[0]
                    in_multiline_double = True
                    if len(parts) > 2:  # 同じ行で終了
                        clean_line = parts[0] + ''.join(parts[2:])
                        in_multiline_double = False
                else:
                    # 終了
                    parts = line.split('"""', 1)
                    if len(parts) > 1:
                        clean_line = parts[1]
                        in_multiline_double = False
                    else:
                        clean_line = ""
            elif "'''" in line:
                if not in_multiline_single:
                    parts = line.split("'''")
                    clean_line = parts[0]
                    in_multiline_single = True
                    if len(parts) > 2:
                        clean_line = parts[0] + ''.join(parts[2:])
                        in_multiline_single = False
                else:
                    parts = line.split("'''", 1)
                    if len(parts) > 1:
                        clean_line = parts[1]
                        in_multiline_single = False
                    else:
                        clean_line = ""

            # 複数行コメント中はスキップ
            if in_multiline_single or in_multiline_double:
                continue

            # 行コメント除去 (#)
            if '#' in clean_line:
                # 文字列リテラル内の#は除外
                in_string = False
                quote_char = None
                for i, char in enumerate(clean_line):
                    if char in ['"', "'"] and (i == 0 or clean_line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            quote_char = char
                        elif char == quote_char:
                            in_string = False
                    elif char == '#' and not in_string:
                        clean_line = clean_line[:i]
                        break

            clean_lines.append(clean_line)

    elif language in ['c_cpp', 'java', 'javascript']:
        # C/C++/Java/JS: // 行コメント、/* */ ブロックコメント
        in_block_comment = False

        for line in lines:
            clean_line = line

            # ブロックコメント処理
            while '/*' in clean_line or '*/' in clean_line or in_block_comment:
                if in_block_comment:
                    if '*/' in clean_line:
                        end_pos = clean_line.find('*/')
                        clean_line = clean_line[end_pos + 2:]
                        in_block_comment = False
                    else:
                        clean_line = ""
                        break
                else:
                    if '/*' in clean_line:
                        start_pos = clean_line.find('/*')
                        if '*/' in clean_line[start_pos:]:
                            end_pos = clean_line.find('*/', start_pos)
                            clean_line = clean_line[:start_pos] + clean_line[end_pos + 2:]
                        else:
                            clean_line = clean_line[:start_pos]
                            in_block_comment = True
                            break
                    else:
                        break

            # 行コメント除去 (//)
            if '//' in clean_line:
                # 文字列リテラル内の//は除外
                in_string = False
                quote_char = None
                for i, char in enumerate(clean_line):
                    if char in ['"', "'"] and (i == 0 or clean_line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            quote_char = char
                        elif char == quote_char:
                            in_string = False
                    elif char == '/' and i < len(clean_line) - 1 and clean_line[i+1] == '/' and not in_string:
                        clean_line = clean_line[:i]
                        break

            clean_lines.append(clean_line)
    else:
        # 不明な言語はそのまま
        clean_lines = lines

    return '\n'.join(clean_lines)

def extract_accurate_features(cfg, cfg_name, source_code=None, filename=None):
    """CFG構造分析に基づいた最適化された特徴量抽出"""
    features = {}

    # 1. Connected Components
    try:
        weakly_connected = list(nx.weakly_connected_components(cfg))
        features['connected_components'] = len(weakly_connected)
    except Exception:
        features['connected_components'] = 0

    # 2. ループ文検出（ソースコード検索 + CFG再帰検出）
    loop_count = 0

    # 言語判定
    language = detect_language(source_code, filename) if source_code and filename else 'unknown'

    # 方法1: ソースコードからfor/while文字列検索
    source_loops = 0
    if source_code:
        clean_source = remove_comments(source_code, language)
        while_count = clean_source.count('while ')
        for_count = clean_source.count('for ')
        do_count = 0
        if language in ['c_cpp', 'java']:
            do_count = clean_source.count('do ')
        source_loops = while_count + for_count + do_count

    # 方法2: CFGから再帰検出
    recursive_loops = 0
    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                if (stmt.__class__.__name__ == 'Call' and
                    hasattr(stmt, 'func') and
                    stmt.func == cfg_name):
                    recursive_loops += 1

    loop_count = source_loops + recursive_loops
    features['loop_statements'] = loop_count

    # 3. 条件文検出（言語別ソースコード検索）
    conditional_count = 0

    if source_code:
        clean_source = remove_comments(source_code, language)
        elif_count = 0
        match_count = 0
        switch_count = 0

        if language == 'python':
            elif_count = clean_source.count('elif ')
            match_count = clean_source.count('match ')
        elif language in ['c_cpp', 'java', 'javascript']:
            switch_count = clean_source.count('switch ')

        if_count = clean_source.count('if ') - elif_count
        while_count = clean_source.count('while ')
        for_count = clean_source.count('for ')

        conditional_count = if_count + elif_count + while_count + match_count + switch_count + for_count

    features['conditional_statements'] = conditional_count    # 4. Cycles
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

    return metadata

def display_accurate_summary(all_features):
    """正確な特徴量結果を表示（簡潔版）"""
    print(f"\n{'='*80}")
    print(f"CFG特徴量結果")
    print(f"{'='*80}")

    # 全体集計（クラスタリング用メトリクス）
    if all_features:
        print(f"\n🎯 全体集計 (クラスタリング用):")

        # 重複除去: 関数レベルの特徴量のみ使用（モジュールレベルは除外）
        function_features = {k: v for k, v in all_features.items()
                           if not (k.startswith('<module>') or k.startswith('&lt;module&gt;'))}

        # モジュールレベル特徴量（構造的特徴のみ）
        module_features = {k: v for k, v in all_features.items()
                         if k.startswith('<module>') or k.startswith('&lt;module&gt;')}

        print(f"  📊 関数レベル特徴量: {len(function_features)}個")
        print(f"  📊 モジュールレベル特徴量: {len(module_features)}個")

        # connected_components: 論理積（1つでも0があれば0、全て1以上なら1）
        all_connected_components = [features.get('connected_components', 0) for features in all_features.values()]
        total_connected = 1 if all(cc > 0 for cc in all_connected_components) else 0

        # ループと条件文: 関数レベルのみから計算（重複除去）
        function_loops = sum(features.get('loop_statements', 0) for features in function_features.values())
        function_conditions = sum(features.get('conditional_statements', 0) for features in function_features.values())

        # 構造的特徴: 全体から計算（関数+モジュール）
        total_cycles = sum(features.get('cycles', 0) for features in all_features.values())
        total_paths = sum(features.get('paths', 0) for features in all_features.values())
        total_complexity = sum(features.get('cyclomatic_complexity', 0) for features in all_features.values())

        print(f"  total_connected_components: {total_connected}")
        print(f"  function_loop_statements: {function_loops} (関数レベルのみ、重複除去)")
        print(f"  function_conditional_statements: {function_conditions} (関数レベルのみ、重複除去)")
        print(f"  total_cycles: {total_cycles}")
        print(f"  total_paths: {total_paths}")
        print(f"  total_cyclomatic_complexity: {total_complexity}")

        # クラスタリング用ベクトル表示（関数レベル特徴量使用）
        clustering_vector = [total_connected, function_loops, function_conditions, total_cycles, total_paths, total_complexity]
        print(f"  📊 クラスタリング用ベクトル: {clustering_vector}")

    print(f"\n個別CFG詳細:")
    for cfg_name, features in all_features.items():
        print(f"\n{cfg_name}:")
        print(f"  connected_components: {features.get('connected_components', 0)}")
        print(f"  loop_statements: {features.get('loop_statements', 0)}")
        print(f"  conditional_statements: {features.get('conditional_statements', 0)}")
        print(f"  cycles: {features.get('cycles', 0)}")
        print(f"  paths: {features.get('paths', 0)}")
        print(f"  cyclomatic_complexity: {features.get('cyclomatic_complexity', 0)}")

def analyze_accurate_cfg(source_file):
    """CFG解析"""
    print(f"解析中: {source_file}")
    all_features = {}

    # ソースコード読み込み
    source_code = ""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        print(f"読み込みエラー: {e}")

    # 関数レベル解析
    try:
        functions = parse_source(source_file)
        for func_name, func_obj in functions.items():
            metadata = analyze_function_metadata(func_obj)
            cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
            if cfg and len(cfg.nodes()) > 0:
                features = extract_accurate_features(cfg, func_name, source_code, source_file)
                features.update(metadata)
                all_features[func_name] = features
    except Exception as e:
        print(f"関数解析エラー: {e}")

    # モジュールレベル解析
    try:
        cfgs = fast_cfgs_from_source(source_file)
        for cfg_name, cfg in cfgs.items():
            if (cfg_name.startswith('<operator>') or cfg_name.startswith('&lt;operator&gt;')):
                continue
            if cfg_name in all_features:
                continue
            if len(cfg.nodes()) > 0:
                features = extract_accurate_features(cfg, cfg_name, source_code, source_file)
                all_features[cfg_name] = features
    except Exception as e:
        print(f"モジュール解析エラー: {e}")

    display_accurate_summary(all_features)
    return all_features

def main():
    test_files = ["whiletest.py"]

    for test_file in test_files:
        try:
            analyze_accurate_cfg(test_file)
        except FileNotFoundError:
            print(f"ファイルが見つかりません: {test_file}")
        except Exception as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    main()
