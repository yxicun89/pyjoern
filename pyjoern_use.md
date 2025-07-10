```markdown
# PyJoern基本ガイド

Pythonコード静的解析ツール PyJoern の基本的な使い方

## 目次

1. [はじめに](#はじめに)
2. [環境設定](#環境設定)
3. [基本的なAPI](#基本的なapi)
4. [parse_source vs fast_cfgs_from_source](#parse_source-vs-fast_cfgs_from_source)
5. [取得できるデータ](#取得できるデータ)
6. [基本的な使用例](#基本的な使用例)
7. [よくある質問](#よくある質問)

## はじめに

PyJoernは、Pythonコードの静的解析を行うためのツールです。コードの構造を解析し、制御フローグラフ（CFG）や抽象構文木（AST）を生成します。

### 主な機能
- 制御フローグラフ（CFG）の生成
- 抽象構文木（AST）の生成
- 関数の基本情報取得
- コードの構造解析

## 環境設定

### インストール

```bash
# 仮想環境の作成
python -m venv pyjoern

# 仮想環境の有効化（Windows）
pyjoern\Scripts\activate

# 仮想環境の有効化（Linux/Mac）
source pyjoern/bin/activate

# PyJoernのインストール
pip install pyjoern networkx
```

## 基本的なAPI

PyJoernには主に2つのグラフ作成方法があります：

### 1. parse_source() - 完全な解析
```python
from pyjoern import parse_source

functions = parse_source("example.py")
```

### 2. fast_cfgs_from_source() - 高速CFG生成
```python
from pyjoern import fast_cfgs_from_source

cfgs = fast_cfgs_from_source("example.py")
```

## parse_source vs fast_cfgs_from_source

| 項目 | parse_source | fast_cfgs_from_source |
|------|-------------|----------------------|
| **速度** | 遅い | 高速 |
| **詳細度** | 高い（CFG + AST + DDG） | 中程度（CFGのみ） |
| **メモリ使用量** | 多い | 少ない |
| **用途** | 詳細分析 | 大量ファイル処理 |

### parse_source() の特徴

```python
functions = parse_source("example.py")
for func_name, func_obj in functions.items():
    print(f"関数名: {func_name}")
    print(f"CFG: {func_obj.cfg}")      # 制御フローグラフ
    print(f"AST: {func_obj.ast}")      # 抽象構文木
    print(f"開始行: {func_obj.start_line}")
    print(f"終了行: {func_obj.end_line}")
```

**取得できる情報：**
- 関数の詳細情報（開始行、終了行）
- 高品質なCFG
- 完全なAST
- ノードの詳細な属性

### fast_cfgs_from_source() の特徴

```python
cfgs = fast_cfgs_from_source("example.py")
for cfg_name, cfg in cfgs.items():
    print(f"CFG名: {cfg_name}")
    print(f"ノード数: {len(cfg.nodes)}")
    print(f"エッジ数: {len(cfg.edges)}")
```

**取得できる情報：**
- CFGのみ（ASTなし）
- 基本的なノード情報
- 高速な処理

## 取得できるデータ

### 関数オブジェクト（parse_source）

```python
functions = parse_source("example.py")
func_obj = functions["example"]

# 基本情報
print(func_obj.start_line)  # 関数の開始行
print(func_obj.end_line)    # 関数の終了行

# グラフ情報
cfg = func_obj.cfg          # 制御フローグラフ
ast = func_obj.ast          # 抽象構文木
```

### CFGノードの構造

```python
for node in cfg.nodes:
    print(f"ノード型: {type(node)}")
    print(f"アドレス: {node.addr}")
    print(f"インデックス: {node.idx}")

    # ノードの属性
    print(f"エントリーポイント: {node.is_entrypoint}")
    print(f"エグジットポイント: {node.is_exitpoint}")
    print(f"マージノード: {node.is_merged_node}")

    # ステートメント（実行文）
    if hasattr(node, 'statements'):
        for stmt in node.statements:
            print(f"ステートメント型: {type(stmt).__name__}")
            print(f"ステートメント内容: {stmt}")
```

### ステートメントの種類

| ステートメント型 | 説明 | 例 |
|-----------------|------|-----|
| `Compare` | 比較演算 | `x > 0`, `x < 0` |
| `Call` | 関数呼び出し | `print(i)`, `range(x)` |
| `Assignment` | 代入 | `i = value` |
| `Return` | return文 | `return x` |
| `Nop` | 特殊操作 | `FUNCTION_START`, `FUNCTION_END` |
| `UnsupportedStmt` | サポート外 | `x += 1`, `CONTROL_STRUCTURE` |

## 基本的な使用例

### サンプルコード

```python
# example.py
def example(x):
    if x > 0:
        for i in range(x):
            print(i)
    else:
        while x < 0:
            x += 1
    return x
```

### 基本的な解析スクリプト

```python
from pyjoern import parse_source
import networkx as nx

def basic_analysis(file_path):
    """基本的な解析"""

    # ファイルを解析
    functions = parse_source(file_path)

    for func_name, func_obj in functions.items():
        print(f"\n=== 関数: {func_name} ===")
        print(f"開始行: {func_obj.start_line}")
        print(f"終了行: {func_obj.end_line}")

        # CFGの基本情報
        if func_obj.cfg:
            cfg = func_obj.cfg
            print(f"CFGノード数: {len(cfg.nodes)}")
            print(f"CFGエッジ数: {len(cfg.edges)}")

            # 各ノードの詳細
            print("\nCFGノード詳細:")
            for i, node in enumerate(cfg.nodes):
                print(f"  ノード{i+1}: Block:{node.addr}")
                print(f"    エントリー: {node.is_entrypoint}")
                print(f"    エグジット: {node.is_exitpoint}")

                # ステートメント
                if hasattr(node, 'statements') and node.statements:
                    for j, stmt in enumerate(node.statements):
                        print(f"      文{j+1}: [{type(stmt).__name__}] {stmt}")

# 実行
if __name__ == "__main__":
    basic_analysis("example.py")
```

### 特定の情報を取得する例

```python
def get_basic_metrics(file_path):
    """基本メトリクスを取得"""

    functions = parse_source(file_path)

    for func_name, func_obj in functions.items():
        if func_obj.cfg:
            cfg = func_obj.cfg

            # 基本メトリクス
            nodes = len(cfg.nodes)
            edges = len(cfg.edges)

            # 制御構造をカウント
            compare_count = 0
            call_count = 0
            assignment_count = 0

            for node in cfg.nodes:
                if hasattr(node, 'statements'):
                    for stmt in node.statements:
                        stmt_type = type(stmt).__name__

                        if stmt_type == 'Compare':
                            compare_count += 1
                        elif stmt_type == 'Call':
                            call_count += 1
                        elif stmt_type == 'Assignment':
                            assignment_count += 1

            print(f"関数: {func_name}")
            print(f"  ノード数: {nodes}")
            print(f"  エッジ数: {edges}")
            print(f"  比較文: {compare_count}")
            print(f"  関数呼び出し: {call_count}")
            print(f"  代入文: {assignment_count}")
```

### 高速CFGでの解析例

```python
def fast_analysis(file_path):
    """高速CFG解析"""

    cfgs = fast_cfgs_from_source(file_path)

    for cfg_name, cfg in cfgs.items():
        print(f"\nCFG: {cfg_name}")
        print(f"ノード数: {len(cfg.nodes)}")
        print(f"エッジ数: {len(cfg.edges)}")

        # ノードの簡単な情報
        for i, node in enumerate(cfg.nodes):
            print(f"  ノード{i+1}: {repr(node)}")
```

## PyJoern vs Joern-CLI 詳細比較

### 基本比較表

| 項目 | PyJoern | Joern-CLI |
|------|---------|-----------|
| **言語** | Python | Scala/Java |
| **インターface** | ライブラリ | コマンドライン |
| **インストール** | pip install | バイナリダウンロード |
| **学習コスト** | 低い（Python慣れ） | 高い（専用言語） |
| **機能の完全性** | 部分的 | 完全 |
| **カスタマイズ性** | 高い | 高い |
| **大量処理** | 得意 | 得意 |
| **メモリ効率** | 中程度 | 高い |
| **処理速度** | 中程度 | 高速 |

### 機能比較詳細

| 機能 | PyJoern | Joern-CLI | 備考 |
|------|---------|-----------|------|
| **CFG生成** | ✓ | ✓ | 両方対応 |
| **AST生成** | ✓ | ✓ | 両方対応 |
| **DDG生成** | ✓ | ✓ | データ依存グラフ |
| **PDG生成** | × | ✓ | PyJoernでは未実装 |
| **CPG統合** | 部分的 | ✓ | Joern-CLIが完全 |
| **クエリ言語** | × | ✓ | Joern専用DSL |
| **バッチ処理** | ✓ | ✓ | 両方得意 |
| **可視化** | 手動 | 組み込み | |

## PyJoernの特徴と制限

### PyJoernで取得可能なグラフ

```python
from pyjoern import parse_source

functions = parse_source("example.py")
func_obj = functions["example"]

# 取得可能なグラフ
print(f"CFG: {hasattr(func_obj, 'cfg')}")    # ✓ 利用可能
print(f"AST: {hasattr(func_obj, 'ast')}")    # ✓ 利用可能
print(f"DDG: {hasattr(func_obj, 'ddg')}")    # ✓ 利用可能
print(f"PDG: {hasattr(func_obj, 'pdg')}")    # × 未実装
```

### PyJoernで省略されている機能

- **PDG（Program Dependence Graph）**: 制御依存とデータ依存の統合グラフ
- **完全なCPG**: Code Property Graphの統合ビュー
- **Joernクエリ言語**: 専用DSLによる高度クエリ
- **セマンティック解析**: より深いコード理解
- **組み込み可視化**: グラフの自動可視化機能

### PyJoernの利点

- **Python統合**: 機械学習パイプラインに組み込みやすい
- **簡単なインストール**: pip一発でインストール完了
- **カスタマイズ性**: Pythonコードで自由に拡張
- **NetworkX互換**: 豊富なグラフアルゴリズムを活用

## Joern-CLIの特徴

# CPGの生成と操作（Joern内部）
importCode("example.py")
cpg.method.name.l  // 全メソッド名を取得
cpg.call.name.l    // 全関数呼び出しを取得
```

### Joern-CLIの高度な機能

```scala
// クエリ言語での複雑な解析
cpg.method.name("example").controlStructure.l
cpg.identifier.name("x").reachableBy(cpg.assignment).l
cpg.call.name("print").argument.l

// 脆弱性パターンの検出
cpg.call.name("eval").argument.isLiteral(false).l
```
---

**参考文献**
- [PyJoern GitHub](https://github.com/octopus-platform/pyjoern)
- [Joern公式ドキュメント](https://joern.io/)
- [NetworkX Documentation](https://networkx.org/)
```
