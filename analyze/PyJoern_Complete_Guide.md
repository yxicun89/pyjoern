# PyJoern完全ガイド

Pythonコード静的解析のための包括的ドキュメント

## 目次

1. [はじめに](#はじめに)
2. [環境設定](#環境設定)
3. [基本的な使用方法](#基本的な使用方法)
4. [制御フローグラフ解析](#制御フローグラフ解析)
5. [条件分岐とループの検出](#条件分岐とループの検出)
6. [変数の読み書き分析](#変数の読み書き分析)
7. [循環複雑度の計算](#循環複雑度の計算)
8. [パス分析](#パス分析)
9. [実践的な使用例](#実践的な使用例)
10. [トラブルシューティング](#トラブルシューティング)
11. [ベストプラクティス](#ベストプラクティス)
12. [クイックリファレンス](#クイックリファレンス)

## はじめに

PyJoernは、Pythonコードの静的解析を行うための強力なツールです。Joern（静的解析プラットフォーム）のPython用バインディングとして、コードプロパティグラフ（CPG）を生成し、詳細な解析を可能にします。

### 主な機能

- **制御フローグラフ（CFG）**: プログラムの実行経路を可視化
- **抽象構文木（AST）**: コードの構造を解析
- **データ依存グラフ（DDG）**: 変数間の依存関係を特定
- **循環複雑度**: コードの複雑さを定量化
- **変数分析**: 読み書きパターンを解析
- **パス分析**: 実行可能な経路を特定

## 環境設定

### インストール手順

```bash
# 仮想環境の作成
python -m venv pyjoern

# 仮想環境の有効化
## Windows
pyjoern\Scripts\activate
## Linux/Mac
source pyjoern/bin/activate

# PyJoernとその依存関係のインストール
pip install pyjoern networkx matplotlib
```

### 動作確認

```python
from pyjoern import parse_source
import networkx as nx

# 基本的な動作テスト
functions = parse_source("test.py")
print(f"検出された関数: {list(functions.keys())}")
```

## 基本的な使用方法

### PyJoernの主要API

```python
from pyjoern import parse_source, fast_cfgs_from_source

# 完全なパース解析（推奨）
functions = parse_source("example.py")

# 高速CFG生成（大きなファイル用）
cfgs = fast_cfgs_from_source("example.py")

# 関数情報の取得
for func_name, func_obj in functions.items():
    print(f"関数名: {func_name}")
    print(f"開始行: {func_obj.start_line}")
    print(f"終了行: {func_obj.end_line}")

    # CFGの確認
    if func_obj.cfg:
        print(f"CFGノード数: {len(func_obj.cfg.nodes)}")
        print(f"CFGエッジ数: {len(func_obj.cfg.edges)}")
```

### サンプルコード

以降の例で使用するサンプルコード：

```python
# whiletest.py
def example(x):
    if x > 0:
        for i in range(x):
            print(i)
    else:
        while x < 0:
            x += 1
    return x

if __name__ == "__main__":
    print(example(5))
```

## 制御フローグラフ解析

### CFGノードの種類

PyJoernでは以下のノード種類を扱います：

| ノード種類 | 説明 | 例 |
|------------|------|-----|
| `Compare` | 比較演算（条件分岐） | `x > 0`, `x < 0` |
| `Call` | 関数呼び出し | `print(i)`, `range(x)` |
| `Assignment` | 代入操作 | `i = value` |
| `Return` | 関数の戻り値 | `return x` |
| `Nop` | 特殊操作 | `FUNCTION_START`, `FUNCTION_END` |
| `UnsupportedStmt` | サポート外ステートメント | `x += 1` |

### CFG分析の実装

```python
def analyze_cfg_structure(cfg):
    """CFGの構造分析"""

    # エントリーポイントとエグジットポイント
    entry_nodes = [n for n in cfg.nodes if n.is_entrypoint]
    exit_nodes = [n for n in cfg.nodes if n.is_exitpoint]

    print(f"エントリーポイント: {len(entry_nodes)}個")
    print(f"エグジットポイント: {len(exit_nodes)}個")

    # 各ノードの詳細
    for i, node in enumerate(cfg.nodes):
        print(f"\nノード {i+1} (Block:{node.addr}):")
        print(f"  エントリー: {node.is_entrypoint}")
        print(f"  エグジット: {node.is_exitpoint}")

        # ステートメントの詳細
        if hasattr(node, 'statements') and node.statements:
            for j, stmt in enumerate(node.statements):
                stmt_type = type(stmt).__name__
                print(f"    [{stmt_type}] {stmt}")
```

## 条件分岐とループの検出

### 条件分岐の検出

```python
def detect_conditional_statements(cfg):
    """条件分岐の検出"""
    conditionals = []

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_type = type(stmt).__name__

                # Compare文（条件分岐）の検出
                if stmt_type == 'Compare':
                    conditionals.append({
                        'statement': str(stmt),
                        'node': node.addr,
                        'type': 'comparison'
                    })

    return conditionals
```

### ループの検出

```python
def detect_loop_statements(cfg):
    """ループの検出"""
    loops = []

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_type = type(stmt).__name__
                stmt_str = str(stmt)

                # for文（range呼び出し）
                if stmt_type == 'Call' and 'range(' in stmt_str:
                    loops.append({
                        'type': 'for_loop',
                        'statement': stmt_str,
                        'node': node.addr
                    })

                # while文（iterator例外）
                elif 'iteratorNonEmptyOrException' in stmt_str:
                    loops.append({
                        'type': 'while_loop',
                        'statement': stmt_str,
                        'node': node.addr
                    })

    return loops
```

## 変数の読み書き分析

### 基本的な変数分析

```python
import re
from collections import defaultdict

def analyze_variable_usage(cfg):
    """変数の読み書き分析"""
    variables = defaultdict(lambda: {'reads': 0, 'writes': 0})

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                # 通常の代入（書き込み）
                if stmt_type == 'Assignment':
                    match = re.match(r'(\w+)\s*=', stmt_str)
                    if match:
                        var_name = match.group(1)
                        variables[var_name]['writes'] += 1

                # 複合代入演算子（+= 等）
                elif (stmt_type == 'UnsupportedStmt' and
                      'assignmentPlus' in stmt_str):
                    match = re.search(r"'([a-zA-Z_]\w*)\s*\+=", stmt_str)
                    if match:
                        var_name = match.group(1)
                        variables[var_name]['reads'] += 1   # 読み取り
                        variables[var_name]['writes'] += 1  # 書き込み

                # 比較での変数使用（読み取り）
                elif stmt_type == 'Compare':
                    for var_name in re.findall(r'\b([a-zA-Z_]\w*)\b', stmt_str):
                        if var_name not in ['Compare', 'tmp0', 'tmp1']:
                            variables[var_name]['reads'] += 1

                # 関数呼び出しでの変数使用（読み取り）
                elif stmt_type == 'Call':
                    for var_name in re.findall(r'\b([a-zA-Z_]\w*)\b', stmt_str):
                        if var_name not in ['range', 'print', 'Call']:
                            variables[var_name]['reads'] += 1

    return dict(variables)
```

### 複合代入演算子の処理

**重要**: `+=`、`-=`などの複合代入演算子は、PyJoernでは`UnsupportedStmt`として扱われ、読み書き両方の操作を行います。

```python
def detect_compound_assignments(cfg):
    """複合代入演算子の詳細検出"""
    compound_ops = []

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                if stmt_type == 'UnsupportedStmt':
                    # 各種複合代入演算子の検出
                    operators = {
                        'assignmentPlus': '+=',
                        'assignmentMinus': '-=',
                        'assignmentMult': '*=',
                        'assignmentDiv': '/='
                    }

                    for op_type, op_symbol in operators.items():
                        if op_type in stmt_str:
                            pattern = f"'([a-zA-Z_]\\w*)\\s*\\{op_symbol.replace('=', '=')}'"
                            match = re.search(pattern, stmt_str)
                            if match:
                                compound_ops.append({
                                    'variable': match.group(1),
                                    'operator': op_symbol,
                                    'node': node.addr
                                })

    return compound_ops
```

## 循環複雑度の計算

### McCabe循環複雑度の正確な計算

循環複雑度の正確な計算式：

```
M = E - N + 2P
```

- M: McCabe循環複雑度
- E: グラフのエッジ数
- N: グラフのノード数
- P: 連結成分の個数

```python
def calculate_mccabe_complexity(cfg):
    """正確なMcCabe循環複雑度の計算"""

    # グラフの基本情報
    E = len(cfg.edges)  # エッジ数
    N = len(cfg.nodes)  # ノード数

    # 連結成分数の計算
    try:
        undirected_cfg = cfg.to_undirected()
        P = nx.number_connected_components(undirected_cfg)
    except:
        P = 1  # エラーの場合は1とする

    # McCabe複雑度: M = E - N + 2P
    mccabe_complexity = E - N + 2 * P

    # 簡易計算（参考値）
    conditional_count = len(detect_conditional_statements(cfg))
    loop_count = len(detect_loop_statements(cfg))
    simple_complexity = conditional_count + loop_count + 1

    return {
        'mccabe_complexity': mccabe_complexity,
        'simple_complexity': simple_complexity,
        'edges': E,
        'nodes': N,
        'components': P,
        'formula': f"M = {E} - {N} + 2×{P} = {mccabe_complexity}"
    }
```

### 複雑度の解釈

| 複雑度 | 評価 | 推奨アクション |
|--------|------|---------------|
| 1-10 | 低い（良好） | そのまま維持 |
| 11-20 | 中程度（注意） | レビュー検討 |
| 21-50 | 高い | リファクタリング推奨 |
| 51以上 | 非常に高い | 緊急対応必要 |

## パス分析

### 静的パス分析

```python
def analyze_execution_paths(cfg):
    """実行パスの分析"""

    # エントリーポイントとエグジットポイント
    entry_nodes = [n for n in cfg.nodes if n.is_entrypoint]
    exit_nodes = [n for n in cfg.nodes if n.is_exitpoint]

    if not entry_nodes or not exit_nodes:
        return {'total_paths': 0, 'path_details': []}

    total_paths = 0
    all_paths = []

    # すべての単純パスを計算
    for entry in entry_nodes:
        for exit in exit_nodes:
            try:
                simple_paths = list(nx.all_simple_paths(cfg, entry, exit))
                total_paths += len(simple_paths)
                all_paths.extend(simple_paths)
            except nx.NetworkXNoPath:
                pass

    return {
        'total_paths': total_paths,
        'path_details': all_paths[:5],  # 最初の5つを表示
        'path_descriptions': [
            " -> ".join([f"Block:{n.addr}" for n in path])
            for path in all_paths[:5]
        ]
    }
```

### 実行可能パス数の推定

```python
def estimate_executable_paths(cfg):
    """実行可能パス数の推定"""

    conditional_count = len(detect_conditional_statements(cfg))
    loop_count = len(detect_loop_statements(cfg))

    # 基本推定: 2^(条件分岐数)
    estimated_paths = 2 ** conditional_count

    # ループの影響を考慮
    if loop_count > 0:
        estimated_paths *= 3  # 0回、1回、複数回実行

    return {
        'estimated_paths': estimated_paths,
        'conditional_branches': conditional_count,
        'loops': loop_count,
        'calculation': f"2^{conditional_count} × 3^{loop_count} = {estimated_paths}"
    }
```

## 実践的な使用例

### 包括的分析スクリプト

```python
def comprehensive_analysis(file_path):
    """包括的な静的解析"""

    functions = parse_source(file_path)
    results = {}

    for func_name, func_obj in functions.items():
        if func_obj.cfg and isinstance(func_obj.cfg, nx.DiGraph):

            # 各種分析の実行
            metrics = {
                'basic_info': {
                    'start_line': func_obj.start_line,
                    'end_line': func_obj.end_line,
                    'total_lines': func_obj.end_line - func_obj.start_line + 1
                },
                'cfg_info': {
                    'nodes': len(func_obj.cfg.nodes),
                    'edges': len(func_obj.cfg.edges)
                },
                'conditionals': detect_conditional_statements(func_obj.cfg),
                'loops': detect_loop_statements(func_obj.cfg),
                'variables': analyze_variable_usage(func_obj.cfg),
                'complexity': calculate_mccabe_complexity(func_obj.cfg),
                'paths': analyze_execution_paths(func_obj.cfg)
            }

            results[func_name] = metrics

    return results
```

### 結果の表示

```python
def display_analysis_results(results):
    """分析結果の表示"""

    for func_name, metrics in results.items():
        print(f"\n{'='*60}")
        print(f"関数: {func_name}")
        print(f"{'='*60}")

        # 基本情報
        basic = metrics['basic_info']
        print(f"行数: {basic['start_line']}-{basic['end_line']} ({basic['total_lines']}行)")

        # CFG情報
        cfg = metrics['cfg_info']
        print(f"CFG: {cfg['nodes']}ノード, {cfg['edges']}エッジ")

        # 制御構造
        print(f"条件分岐: {len(metrics['conditionals'])}個")
        print(f"ループ: {len(metrics['loops'])}個")

        # 複雑度
        complexity = metrics['complexity']
        print(f"McCabe複雑度: {complexity['mccabe_complexity']} ({complexity['formula']})")

        # 変数分析
        variables = metrics['variables']
        total_reads = sum(v['reads'] for v in variables.values())
        total_writes = sum(v['writes'] for v in variables.values())
        print(f"変数: {len(variables)}個, 読み取り: {total_reads}, 書き込み: {total_writes}")

        # パス情報
        paths = metrics['paths']
        print(f"実行パス: {paths['total_paths']}個")
```

### コード品質評価

```python
def evaluate_code_quality(results):
    """コード品質の評価"""

    quality_scores = []

    for func_name, metrics in results.items():
        complexity = metrics['complexity']['mccabe_complexity']
        paths = metrics['paths']['total_paths']
        variables = len(metrics['variables'])

        # 複雑度スコア（0-100）
        if complexity <= 5:
            complexity_score = 100
        elif complexity <= 10:
            complexity_score = 80
        elif complexity <= 20:
            complexity_score = 60
        else:
            complexity_score = 30

        # パススコア（0-100）
        if paths <= 3:
            path_score = 100
        elif paths <= 5:
            path_score = 80
        else:
            path_score = 60

        # 変数スコア（0-100）
        if variables <= 5:
            variable_score = 100
        elif variables <= 10:
            variable_score = 80
        else:
            variable_score = 60

        # 総合スコア
        total_score = (complexity_score + path_score + variable_score) / 3

        quality_scores.append({
            'function': func_name,
            'complexity_score': complexity_score,
            'path_score': path_score,
            'variable_score': variable_score,
            'total_score': total_score
        })

    return quality_scores
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. NetworkXのインポートエラー

```bash
# エラー: ModuleNotFoundError: No module named 'networkx'
pip install networkx
```

#### 2. PyJoernの解析エラー

```python
# エラーハンドリングの実装
try:
    functions = parse_source(file_path)
except Exception as e:
    print(f"解析エラー: {e}")
    # フォールバック処理
    functions = {}
```

#### 3. 複合代入演算子が検出されない

複合代入演算子（`+=`、`-=`など）は`UnsupportedStmt`として扱われるため、正規表現での特別な検出が必要です。

```python
# 正しい検出方法
if stmt_type == 'UnsupportedStmt' and 'assignmentPlus' in stmt_str:
    match = re.search(r"'([a-zA-Z_]\w*)\s*\+=", stmt_str)
    if match:
        var_name = match.group(1)
        # 読み書き両方として処理
```

#### 4. 大きなファイルでの性能問題

```python
# 高速CFG生成を使用
cfgs = fast_cfgs_from_source(file_path)

# または分析対象を限定
def analyze_specific_functions(file_path, target_functions):
    functions = parse_source(file_path)
    return {name: func for name, func in functions.items()
            if name in target_functions}
```

## ベストプラクティス

### 1. 効率的な分析のための推奨事項

- **段階的な分析**: 基本メトリクスから始めて詳細分析へ
- **エラーハンドリング**: PyJoernの解析失敗を考慮
- **結果の検証**: 複数の方法で同じメトリクスを計算
- **適切な文書化**: 分析結果の意味を明確に記録

### 2. 分析精度向上のテクニック

- **複合代入演算子の適切な処理**
- **一時変数の除外** (`tmp0`, `tmp1`など)
- **ライブラリ関数の識別** (`print`, `range`など)
- **ネストした制御構造の正確な検出**

### 3. 保守性の向上

```python
# 設定の外部化
EXCLUDED_VARIABLES = ['tmp0', 'tmp1', 'Compare']
LIBRARY_FUNCTIONS = ['print', 'range', 'len', 'str']

# 再利用可能な関数
def is_library_function(name):
    return name in LIBRARY_FUNCTIONS

def is_temp_variable(name):
    return name in EXCLUDED_VARIABLES or name.startswith('tmp')
```

## クイックリファレンス

### 基本的なAPIの使用

```python
# 必須インポート
from pyjoern import parse_source, fast_cfgs_from_source
import networkx as nx
from collections import defaultdict
import re

# 基本的な解析
functions = parse_source("file.py")
for name, func in functions.items():
    cfg = func.cfg
    ast = func.ast
```

### よく使用するメトリクス

```python
# 基本メトリクス
nodes = len(cfg.nodes)
edges = len(cfg.edges)
complexity = edges - nodes + 2 * 1  # P=1 for single component

# 制御構造の数
conditionals = len([n for n in cfg.nodes
                   if any(type(s).__name__ == 'Compare'
                         for s in n.statements)])

loops = len([n for n in cfg.nodes
            if any('range(' in str(s)
                  for s in n.statements)])
```

### 変数分析のクイック実装

```python
def quick_variable_analysis(cfg):
    vars = defaultdict(lambda: {'r': 0, 'w': 0})

    for node in cfg.nodes:
        for stmt in node.statements:
            s, t = str(stmt), type(stmt).__name__

            if t == 'Assignment':
                if m := re.match(r'(\w+)\s*=', s):
                    vars[m.group(1)]['w'] += 1
            elif t == 'Compare':
                for v in re.findall(r'\b([a-zA-Z_]\w*)\b', s):
                    if v not in ['Compare']:
                        vars[v]['r'] += 1

    return dict(vars)
```

### デバッグ用の表示関数

```python
def debug_cfg(cfg):
    """CFGのデバッグ表示"""
    for i, node in enumerate(cfg.nodes):
        print(f"Node {i}: Block:{node.addr}")
        for j, stmt in enumerate(node.statements):
            print(f"  {j}: [{type(stmt).__name__}] {stmt}")
```

---

## まとめ

PyJoernを使った効果的な静的解析には以下のポイントが重要です：

### 基本的な分析技法
1. **正確な循環複雑度**: M = E - N + 2P の式を使用
2. **while文の処理**: 条件分岐として適切にカウント
3. **複合代入演算子**: `+=`等は読み書き両方として処理
4. **静的パス分析**: 構造的な経路数を計算
5. **エラーハンドリング**: 解析失敗に対する適切な対応

### 高度な活用方法
6. **関数間依存関係**: 呼び出し関係を分析して設計品質を評価
7. **データフロー分析**: 変数のライフサイクルを追跡
8. **メトリクス集計**: 複数の指標を統合して総合評価
9. **品質ゲート**: CI/CDでの自動品質チェック
10. **レポート生成**: 結果を可視化して共有

### 実践的なベストプラクティス
- 段階的な分析: 基本メトリクスから始めて詳細分析へ
- 継続的監視: CI/CDパイプラインでの自動チェック
- 閾値設定: プロジェクトに応じた品質基準の設定
- 結果の可視化: HTMLレポートやダッシュボードの活用

これらの知見を活用することで、PyJoernを使った高品質な静的解析が可能になります。特に、継続的インテグレーションと組み合わせることで、コード品質の持続的な改善が実現できます。

---

**作成日**: 2025年1月
**バージョン**: 1.0
**対象**: PyJoern 4.x系

## 高度な分析技法

### 関数間の依存関係分析

PyJoernでは、関数間の呼び出し関係も分析できます：

```python
def analyze_function_dependencies(functions):
    """関数間の依存関係を分析"""
    dependencies = defaultdict(set)

    for func_name, func_obj in functions.items():
        if func_obj.cfg:
            for node in func_obj.cfg.nodes:
                if hasattr(node, 'statements') and node.statements:
                    for stmt in node.statements:
                        if type(stmt).__name__ == 'Call':
                            stmt_str = str(stmt)
                            # 他の関数への呼び出しを検出
                            for other_func in functions.keys():
                                if other_func != func_name and other_func in stmt_str:
                                    dependencies[func_name].add(other_func)

    return dict(dependencies)
```

### データフロー分析

変数のライフサイクルを追跡：

```python
def analyze_variable_lifecycle(cfg):
    """変数のライフサイクル分析"""
    lifecycle = defaultdict(list)

    for node in cfg.nodes:
        if hasattr(node, 'statements') and node.statements:
            for stmt in node.statements:
                stmt_str = str(stmt)
                stmt_type = type(stmt).__name__

                # 変数の定義
                if stmt_type == 'Assignment':
                    match = re.match(r'(\w+)\s*=', stmt_str)
                    if match:
                        var_name = match.group(1)
                        lifecycle[var_name].append({
                            'action': 'definition',
                            'node': node.addr,
                            'statement': stmt_str
                        })

                # 変数の使用
                elif stmt_type == 'Compare':
                    for var_name in re.findall(r'\b([a-zA-Z_]\w*)\b', stmt_str):
                        if var_name not in ['Compare', 'tmp0', 'tmp1']:
                            lifecycle[var_name].append({
                                'action': 'usage',
                                'node': node.addr,
                                'statement': stmt_str
                            })

    return dict(lifecycle)
```

### コードメトリクス集計

複数のメトリクスを統合して評価：

```python
def calculate_comprehensive_metrics(file_path):
    """総合的なコードメトリクス計算"""
    functions = parse_source(file_path)

    overall_metrics = {
        'total_functions': len(functions),
        'total_complexity': 0,
        'average_complexity': 0,
        'max_complexity': 0,
        'total_paths': 0,
        'total_variables': 0,
        'function_details': {}
    }

    for func_name, func_obj in functions.items():
        if func_obj.cfg:
            complexity = calculate_mccabe_complexity(func_obj.cfg)
            paths = analyze_paths(func_obj.cfg)
            variables = analyze_variables(func_obj.cfg)

            func_complexity = complexity['mccabe_complexity']
            func_paths = paths['total_paths']
            func_variables = len(variables)

            overall_metrics['total_complexity'] += func_complexity
            overall_metrics['total_paths'] += func_paths
            overall_metrics['total_variables'] += func_variables
            overall_metrics['max_complexity'] = max(
                overall_metrics['max_complexity'], func_complexity
            )

            overall_metrics['function_details'][func_name] = {
                'complexity': func_complexity,
                'paths': func_paths,
                'variables': func_variables
            }

    # 平均値の計算
    if overall_metrics['total_functions'] > 0:
        overall_metrics['average_complexity'] = (
            overall_metrics['total_complexity'] / overall_metrics['total_functions']
        )

    return overall_metrics
```

## 継続的インテグレーション（CI）での活用

### 品質ゲートの実装

```python
def quality_gate_check(file_path, thresholds=None):
    """CI用の品質ゲートチェック"""

    if thresholds is None:
        thresholds = {
            'max_complexity': 10,
            'max_paths': 5,
            'max_variables': 15
        }

    results = comprehensive_analysis(file_path)
    failures = []

    for func_name, metrics in results.items():
        complexity = metrics['cyclomatic_complexity']['mccabe_complexity']
        paths = metrics['paths']['total_paths']
        variables = len(metrics['variables'])

        if complexity > thresholds['max_complexity']:
            failures.append({
                'function': func_name,
                'metric': 'complexity',
                'value': complexity,
                'threshold': thresholds['max_complexity']
            })

        if paths > thresholds['max_paths']:
            failures.append({
                'function': func_name,
                'metric': 'paths',
                'value': paths,
                'threshold': thresholds['max_paths']
            })

        if variables > thresholds['max_variables']:
            failures.append({
                'function': func_name,
                'metric': 'variables',
                'value': variables,
                'threshold': thresholds['max_variables']
            })

    return {
        'passed': len(failures) == 0,
        'failures': failures
    }
```

### レポート生成

```python
def generate_html_report(file_path, output_file="quality_report.html"):
    """HTML品質レポートの生成"""

    metrics = calculate_comprehensive_metrics(file_path)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>コード品質レポート</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .high-complexity {{ background-color: #ffcccc; }}
            .medium-complexity {{ background-color: #ffffcc; }}
            .low-complexity {{ background-color: #ccffcc; }}
        </style>
    </head>
    <body>
        <h1>コード品質レポート</h1>
        <h2>概要</h2>
        <p>総関数数: {metrics['total_functions']}</p>
        <p>平均複雑度: {metrics['average_complexity']:.2f}</p>
        <p>最大複雑度: {metrics['max_complexity']}</p>

        <h2>関数別詳細</h2>
        <table>
            <tr>
                <th>関数名</th>
                <th>複雑度</th>
                <th>実行パス数</th>
                <th>変数数</th>
                <th>評価</th>
            </tr>
    """

    for func_name, details in metrics['function_details'].items():
        complexity = details['complexity']

        if complexity <= 10:
            css_class = "low-complexity"
            evaluation = "良好"
        elif complexity <= 20:
            css_class = "medium-complexity"
            evaluation = "注意"
        else:
            css_class = "high-complexity"
            evaluation = "改善必要"

        html_content += f"""
            <tr class="{css_class}">
                <td>{func_name}</td>
                <td>{complexity}</td>
                <td>{details['paths']}</td>
                <td>{details['variables']}</td>
                <td>{evaluation}</td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_file
```

### GitHub Actions連携

```yaml
# .github/workflows/code-quality.yml
name: Code Quality Check

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  quality-check:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install pyjoern networkx

    - name: Run quality check
      run: |
        python quality_check.py

    - name: Upload report
      uses: actions/upload-artifact@v2
      with:
        name: quality-report
        path: quality_report.html
```
