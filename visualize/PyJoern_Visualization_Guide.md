# PyJoern 視覚化プログラム解説

## 概要

`visualize_graphs_fixed.py` は、Pythonソースコードを静的解析してCFG（制御フローグラフ）、AST（抽象構文木）、DDG（データ依存グラフ）を視覚化するプログラムです。PyJoernライブラリを使用して、複雑なプログラムの制御フローを直感的に理解できる強力な静的解析・視覚化ツールを提供します。

## プログラム全体構成

### メイン機能

```python
def analyze_and_visualize_file(source_file, output_dir="graph_images")
```

このプログラムは以下の3つの主要機能を提供します：

1. **parse_source解析**: 詳細な静的解析でCFG、AST、DDGを生成
2. **fast_cfg解析**: 高速CFG解析で関数レベルのCFGのみを生成
3. **グラフ比較**: 3つのグラフを横並びで比較表示

## 視覚化の核心機能

### 1. ノードラベル作成 (`create_node_labels`)

```python
def create_node_labels(graph, graph_type="CFG"):
```

#### CFGノードの特徴

- **Block番号**: `Block {node.addr}` でブロックを識別
- **ステートメント分析**: 汎用的なパターン検出
  - `LOOP_ITERATION`: ループの反復チェック
  - `CONDITION`: 条件比較（`Compare:`で検出）
  - `FUNCTION_CALL`: 関数呼び出し（`Call:`で検出）
  - `ASSIGNMENT`: 代入文（`Assignment:`で検出）
  - `FUNCTION_START/END`: 関数の開始/終了

#### 特別処理

```python
# FUNCTION_START + 条件判定の組み合わせノード
if has_function_start and has_condition:
    base_label = "[START] FUNCTION ENTRY\n" + "="*16
```

### 2. エッジの色分けとスタイル (`get_edge_colors_and_styles`)

```python
def get_edge_colors_and_styles(graph, graph_type="CFG"):
```

#### エッジタイプの識別

- 🔴 **ループバックエッジ**: `#FF6B6B`（赤色、破線）
  - `source.addr > target.addr` でループを検出
  - 関数終了ノードからのエッジは除外
- 🔵 **条件分岐エッジ**: `#4169E1`（青色、実線）
  - `Compare:`文の存在で判定
- ⚫ **通常エッジ**: `#333333`（ダークグレー、実線）

### 3. ノードの色分け (`get_node_colors`)

```python
def get_node_colors(graph, graph_type="CFG"):
```

#### CFGノードの色コード

| 色 | HEXコード | 意味 | 説明 |
|---|---|---|---|
| 🔴 | `#FF6B6B` | **警告** | FUNCTION_START + 条件判定の組み合わせ |
| 🟢 | `#90EE90` | **エントリーポイント** | 関数開始 |
| 🩷 | `#FFB6C1` | **エグジットポイント** | 関数終了 |
| 🟡 | `#FFD700` | **マージノード** | 制御フローの合流点 |
| 🔵 | `#87CEFA` | **条件判定ノード** | if/while文 |
| 🟢 | `#98FB98` | **関数呼び出し** | Call文 |
| 🔵 | `#87CEEB` | **通常ノード** | その他のステートメント |

## グラフ描画機能

### 4. 単一グラフ視覚化 (`visualize_graph`)

```python
def visualize_graph(graph, title, graph_type="CFG", save_path=None):
```

#### レイアウト選択

- **小規模グラフ** (≤10ノード): Spring layout
- **CFG**: Graphviz dot layout（階層的）
- **AST/DDG**: Spring layout

#### 描画順序

1. エッジ描画（カーブ付き）
2. ノード描画（色分け）
3. ラベル描画
4. エッジラベル描画（"Loop"など）
5. 凡例追加

### 5. 比較グラフ (`compare_graphs_side_by_side`)

```python
def compare_graphs_side_by_side(cfg, ast, ddg, func_name, save_dir=None):
```

CFG、AST、DDGを横並びで比較表示し、各グラフの特徴を一目で確認可能。

## 高度な描画機能

### 6. カーブ付きエッジ描画 (`draw_edges_with_curves`)

```python
def draw_edges_with_curves(graph, pos, edge_colors, edge_styles):
```

- **重複エッジ対応**: 同じノード間の複数エッジを異なるカーブで描画
- **カーブ角度**: 0.1、0.3の異なる弧度で視覚的に区別

### 7. エッジラベル (`get_edge_labels`)

- **"Loop"ラベル**: 実際のループバックエッジのみ
- **関数終了除外**: FUNCTION_ENDノードからのエッジは除外
- **True/False除去**: CFGでは条件分岐ラベルは色分けのみ

## 汎用性の工夫

### パターンベース検出

特定の変数名（`x > 0`、`i % 2`など）にハードコーディングせず、汎用的なパターンで検出：

```python
# 条件比較の判定（汎用的）
elif 'Compare:' in stmt_str:
    primary_stmt_type = "CONDITION"

# ループ構造の判定
if 'iteratorNonEmptyOrException' in stmt_str:
    primary_stmt_type = "LOOP_ITERATION"
```

### HTMLエンティティ対応

```python
# フィルタリング条件
if (not name.startswith('<operator>') and
    not name.startswith('&lt;operator&gt;') and  # HTMLエンコード対応
    not name == '<module>' and
    not name == '&lt;module&gt;'):
```

## 実行フロー

1. **ソースファイル読み込み**
2. **parse_source解析** → CFG、AST、DDG生成
3. **個別グラフ視覚化** → PNG保存
4. **比較グラフ生成** → 3つのグラフを横並び表示
5. **fast_cfg解析** → 関数レベルCFGのみ抽出・視覚化

## 視覚的特徴

- **色分けによる識別**: エントリー/エグジット/条件/ループを色で区別
- **矢印スタイル**: 制御フローの方向を明確に表示
- **ラベル情報**: ブロック番号、ステートメント要約、行番号
- **凡例付き**: 各色とエッジタイプの意味を説明

## 使用例

```python
# whiletest.pyを解析
analyze_and_visualize_file("whiletest.py")
```

このプログラムは、複雑なプログラムの制御フローを直感的に理解できる強力な静的解析・視覚化ツールです。

## 技術的詳細

### 依存ライブラリ

- `pyjoern`: 静的解析エンジン
- `networkx`: グラフ操作
- `matplotlib`: 視覚化
- `numpy`: 数値計算

### 出力形式

- **個別グラフ**: PNG形式で保存
- **比較グラフ**: 3つのグラフを横並びで表示・保存
- **デバッグ情報**: コンソール出力で解析状況を確認

### カスタマイズ可能要素

- **色設定**: ノード・エッジの色を変更可能
- **レイアウト**: グラフレイアウトアルゴリズムを選択可能
- **ラベル内容**: ノードラベルの表示内容を調整可能
- **保存形式**: 画像形式・解像度を変更可能
