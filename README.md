# PyJoern静的解析プロジェクト

## 概要

このプロジェクトは、PyJoernを使用したPythonコードの静的解析を行うためのツールとドキュメントです。コード品質の測定、循環複雑度の計算、変数分析、パス分析など、包括的な静的解析機能を提供します。

## ファイル構成

```
pyjoern/
├── whiletest.py                    # 分析対象のサンプルコード
├── comprehensive_analysis.py       # 包括的な分析スクリプト
├── generate_quality_report.py     # HTML品質レポート生成スクリプト
├── PyJoern_Complete_Guide.tex     # LaTeX版の完全ガイド
├── PyJoern_Complete_Guide.md      # Markdown版の完全ガイド
└── README.md                      # このファイル
```

## セットアップ

### 1. 仮想環境の作成と有効化

```bash
# Windows
python -m venv pyjoern
pyjoern\Scripts\activate

# Linux/Mac
python -m venv pyjoern
source pyjoern/bin/activate
```

### 2. 必要なパッケージのインストール

```bash
pip install pyjoern networkx matplotlib
```

## 使用方法

### 基本的な分析

```bash
# 包括的な分析の実行
python comprehensive_analysis.py

# 品質レポートの生成
python generate_quality_report.py whiletest.py
```

### 分析項目

- **循環複雑度**: McCabe複雑度（M = E - N + 2P）
- **実行パス数**: 静的解析による実行可能パス数
- **変数分析**: 読み取り・書き込み回数の分析
- **制御構造**: 条件分岐とループの検出
- **コード品質**: 総合的な品質評価

### 出力例

```
=== 関数: main ===
Connected Components     : 1
Loop Statements          : 2
Conditional Statements   : 3
Cycles                   : 0
Paths                    : 2
Cyclomatic Complexity    : 4
Variable Count           : 3
Total Reads              : 8
Total Writes             : 5
```

## 主な機能

### 1. 循環複雑度計算

正確なMcCabe複雑度を計算します：

```python
def calculate_mccabe_complexity(cfg):
    E = len(cfg.edges)    # エッジ数
    N = len(cfg.nodes)    # ノード数
    P = nx.number_connected_components(cfg.to_undirected())  # 連結成分数

    mccabe_complexity = E - N + 2 * P
    return mccabe_complexity
```

### 2. 変数の読み書き分析

複合代入演算子（`+=`、`-=`など）も正確に検出します：

```python
# x += 1 は読み取りと書き込みの両方としてカウント
variables['x']['reads'] += 1
variables['x']['writes'] += 1
```

### 3. パス分析

静的解析による実行可能パス数を計算します：

```python
def analyze_paths(cfg):
    entry_nodes = [n for n in cfg.nodes if n.is_entrypoint]
    exit_nodes = [n for n in cfg.nodes if n.is_exitpoint]

    total_paths = 0
    for entry in entry_nodes:
        for exit in exit_nodes:
            paths = list(nx.all_simple_paths(cfg, entry, exit))
            total_paths += len(paths)

    return total_paths
```

### 4. HTMLレポート生成

視覚的な品質レポートを生成します：

```bash
python generate_quality_report.py whiletest.py
# -> whiletest_quality_report.html が生成される
```

## 品質基準

### 複雑度の評価

- **1-10**: 良好（保守しやすい）
- **11-20**: 注意（改善を検討）
- **21以上**: 改善必要（リファクタリング推奨）

### 変数使用の指針

- 読み取り回数 > 書き込み回数：適切な変数使用
- 書き込み回数 > 読み取り回数：未使用変数の可能性

## 継続的インテグレーション

### GitHub Actions設定例

```yaml
name: Code Quality Check
on: [push, pull_request]

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
      run: pip install pyjoern networkx
    - name: Run quality check
      run: python comprehensive_analysis.py
```

## トラブルシューティング

### よくある問題

1. **NetworkXのインポートエラー**
   ```bash
   pip install networkx
   ```

2. **PyJoernの解析エラー**
   - ファイルパスを確認
   - 仮想環境が有効になっているか確認

3. **複合代入演算子が検出されない**
   - `UnsupportedStmt`として処理されるため、正規表現で検出

### パフォーマンス向上

- 大きなファイルには`fast_cfgs_from_source()`を使用
- 分析する関数を限定
- メモリ使用量を監視

## 参考資料

- [PyJoern公式](https://github.com/fabsx00/pyjoern)
- [Joernプロジェクト](https://joern.io/)
- [McCabe複雑度論文](https://www.literateprogramming.com/mccabe.pdf)

## ライセンス

本プロジェクトは、教育および研究目的での使用を想定しています。

---

**作成日**: 2025年1月
**更新日**: 2025年1月
**作成者**: 静的解析研究チーム
