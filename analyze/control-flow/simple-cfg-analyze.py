from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx

def extract_cfg_features(cfg, func_name):
    """CFGから必要な特徴量のみを抽出する"""
    features = {}
    
    # 1. Connected Components
    try:
        weakly_connected = list(nx.weakly_connected_components(cfg))
        features['connected_components'] = len(weakly_connected)
    except Exception as e:
        features['connected_components'] = 0
    
    # 2. Loop Statements
    loop_count = 0
    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt).lower()
                if ('for' in stmt_str or 'while' in stmt_str) and 'Compare:' not in stmt_str:
                    loop_count += 1
    features['loop_statements'] = loop_count
    
    # 3. Conditional Statements
    conditional_count = 0
    for node in cfg.nodes():
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                if 'Compare:' in stmt_str or ('if' in stmt_str.lower() and 'Compare:' not in stmt_str):
                    conditional_count += 1
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
        print(f"  loop_statements: {features.get('loop_statements', 0)}")
        print(f"  conditional_statements: {features.get('conditional_statements', 0)}")
        print(f"  cycles: {features.get('cycles', 0)}")
        print(f"  paths: {features.get('paths', 0)}")
        print(f"  cyclomatic_complexity: {features.get('cyclomatic_complexity', 0)}")

def analyze_file_cfg(source_file):
    """ソースファイルのCFGから特徴量を抽出"""
    print(f"ファイル '{source_file}' のCFG解析")
    
    all_features = {}

    # parse_sourceで解析
    try:
        functions = parse_source(source_file)
        for func_name, func_obj in functions.items():
            cfg = func_obj.cfg if hasattr(func_obj, 'cfg') else None
            if cfg and len(cfg.nodes()) > 0:
                features = extract_cfg_features(cfg, func_name)
                all_features[func_name] = features
    except Exception as e:
        print(f"parse_source エラー: {e}")

    # fast_cfgs_from_sourceで解析
    try:
        cfgs = fast_cfgs_from_source(source_file)
        for cfg_name, cfg in cfgs.items():
            if (len(cfg.nodes()) > 0 and 
                not cfg_name.startswith('<operator>') and
                not cfg_name.startswith('&lt;operator&gt;') and
                cfg_name not in all_features):
                
                features = extract_cfg_features(cfg, cfg_name)
                all_features[cfg_name] = features
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