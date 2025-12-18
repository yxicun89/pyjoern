# PyJoern静的解析プロジェクト

## 概要

このプロジェクトは、PyJoernを使用したPythonコードの静的解析と機械学習によるコード分類を行うためのツールとドキュメントです。制御フロー（CFG）・データフロー（DFG）特徴量の抽出、K-meansクラスタリング、視覚化など、包括的な静的解析機能を提供します。

## ファイル構成

```
pyjoern/
├── analyze/
│   ├── kmeans_final_clean.py           # K-meansクラスタリング実装（ハンガリアンアルゴリズム対応）
│   ├── ext_cfg_dfg_feature.py          # CFG+データフロー特徴量抽出
│   ├── control-flow/                    # CFG解析モジュール
│   ├── data-flow/                       # データフロー解析モジュール
│   └── feature_cache_*.json             # 特徴量キャッシュファイル
├── visualize/
│   └── visualize_module_and_functions.py # PyJoernグラフ視覚化ツール
├── atcoder/                             # 分析対象コードサンプル
│   └── submissions_typical90_*/         # AtCoderサンプル
├── comprehensive_analysis.py            # 包括的な分析スクリプト
├── generate_quality_report.py          # HTML品質レポート生成
└── README.md                            # このファイル
```

## セットアップ

### 1. 仮想環境の作成と有効化

```bash
# Windows PowerShell
python -m venv pyjoern
.\pyjoern\Scripts\Activate.ps1

# Linux/Mac
python -m venv pyjoern
source pyjoern/bin/activate
```

### 2. 必要なパッケージのインストール

```bash
# 基本パッケージ
pip install pyjoern networkx matplotlib

# 機械学習・クラスタリング用
pip install scikit-learn scipy pandas seaborn numpy

# 次元削減手法（オプション）
pip install umap-learn  # UMAP
```

## 使用方法

### 1. CFG・データフロー特徴量の抽出

```bash
cd analyze
python ext_cfg_dfg_feature.py
```

**対象ディレクトリを変更する場合：**
```python
# ext_cfg_dfg_feature.py の main() 内
target_directory = "../atcoder/submissions_typical90_d"
```

**特徴量の内容（11次元ベクトル）：**
- **CFG特徴量（6次元）**: connected_components, loop_statements, conditional_statements, cycles, paths, cyclomatic_complexity
- **データフロー特徴量（5次元）**: total_reads, total_writes, max_reads, max_writes, var_count

### 2. K-meansクラスタリングの実行

```bash
cd analyze
python -c "from kmeans_final_clean import main; main('general', 'real_code_features', target_directory='../atcoder/submissions_typical90_d', k_clusters=5)"
```

**主要機能：**
- データの標準化（平均0、分散1）
- ハンガリアンアルゴリズムによる最適クラスタ-パターンマッピング
- 適合率・再現率・F1スコアの計算
- PCA/t-SNE/UMAPによる可視化

### 3. PyJoernグラフの視覚化

```bash
cd visualize
python visualize_module_and_functions.py
```

**コード内でファイル指定：**
```python
analyze_and_visualize_file("../path/to/your/code.py")
```

**出力：**
- CFG (Control Flow Graph)
- AST (Abstract Syntax Tree)
- DDG (Data Dependence Graph)

### 出力例

#### 特徴量抽出
```
📂 統合特徴量抽出開始: 100ファイル
✅ セントロイド追加: 5個
💾 特徴量ベクトル保存: 'feature_cache_typical90_d.json'
```

#### クラスタリング結果
```
📊 REAL_CODE_FEATURES クラスタリング結果
総クラスター数: 5 | 総サンプル数: 100

🏷️ Cluster 0 (20 ファイル) → 🎯 pattern1:
   適合率: 0.9500 | 再現率: 0.9048 | F1: 0.9268

全体評価:
   マクロ平均 F1: 0.8542
   重み付き平均 F1: 0.8723
   正確度: 87.00%
```

## 主な機能

### 1. 統合特徴量抽出（CFG + データフロー）

CFGとデータフロー特徴量を統合した11次元ベクトルを抽出：

```python
from ext_cfg_dfg_feature import extract_integrated_features_vector

# 単一ファイル
vector = extract_integrated_features_vector("sample.py")
# -> [1, 2, 3, 0, 4, 5, 10, 15, 8, 12, 4]
#    [CFG 6次元] + [データフロー 5次元]

# 複数ファイル一括処理
from ext_cfg_dfg_feature import batch_extract_integrated_features
results = batch_extract_integrated_features(file_list)
```

### 2. データの標準化（オンライン学習対応）

増分処理に対応した標準化（平均0、分散1）：

```python
from kmeans_final_clean import OnlineStandardScaler

scaler = OnlineStandardScaler(n_features=11)
X = scaler.fit_transform(data)  # 標準化

# 新しいデータの追加
scaler.partial_fit(new_data)  # 統計量を更新
X_new = scaler.transform(new_data)
```

### 3. ハンガリアンアルゴリズムによる最適マッピング

クラスタとカテゴリの最適な1対1割り当て：

```python
from kmeans_final_clean import hungarian_cluster_pattern_assignment

assignment_dict, confusion_matrix, _, _, score = \
    hungarian_cluster_pattern_assignment(cluster_labels, file_paths)

# -> {0: 'pattern1', 1: 'pattern2', ...}
```

### 4. 適合率・再現率・F値の計算

クラスタリング品質の定量評価：

```python
from kmeans_final_clean import calculate_precision_recall_f1

metrics_dict, overall_metrics = calculate_precision_recall_f1(
    assignment_dict, confusion_matrix, cluster_ids,
    pattern_names, cluster_labels, file_paths
)

print(f"F1スコア: {overall_metrics['weighted_f1']:.4f}")
print(f"正確度: {overall_metrics['accuracy']:.4f}")
```

### 5. キャッシュ機能による高速化

特徴量を自動キャッシュして差分更新：

```python
# 初回実行: 全ファイルを処理
batch_results = batch_extract_integrated_features(file_list)
save_feature_vectors(batch_results, groups, base_dir, "cache.json")

# 2回目以降: 変更ファイルのみ処理
file_changes = detect_file_changes(target_dir, "cache.json")
updated_data = update_cache_incrementally(target_dir, "cache.json", file_changes)
```

### 6. グラフ視覚化（階層的レイアウト）

コード実行順序に基づいたCFG/AST/DDGの視覚化：

```python
from visualize_module_and_functions import analyze_and_visualize_file

analyze_and_visualize_file("sample.py", output_dir="graph_images")
# -> CFG, AST, DDGの画像が生成される
```

## クラスタリング評価指標

### 適合率（Precision）

そのクラスタの中でどれだけ正解カテゴリを含めているかの割合（ノイズの少なさ）

```
適合率 = TP / (TP + FP)
```

- **TP**: クラスタ内で正しく分類されたファイル数
- **FP**: クラスタ内で誤って分類されたファイル数

### 再現率（Recall）

正解カテゴリのファイル数に対して正しく分類したファイル数の割合

```
再現率 = TP / (TP + FN)
```

- **FN**: 他のクラスタに分類されてしまった正解ファイル数

### F値（F1スコア）

適合率と再現率の調和平均（バランスの良さを評価）

```
F1 = 2 × (適合率 × 再現率) / (適合率 + 再現率)
```

### 評価基準

- **F1 ≥ 0.90**: 優秀（非常に良い分類）
- **0.80 ≤ F1 < 0.90**: 良好（実用的）
- **0.70 ≤ F1 < 0.80**: 要改善（調整推奨）
- **F1 < 0.70**: 不良（再設計必要）

## 実験ワークフロー

### 典型的な実験手順

1. **データ収集**: AtCoderなどからコードサンプルを取得
   ```bash
   mkdir -p atcoder/submissions_typical90_xx
   # サンプルコードを配置
   ```

2. **特徴量抽出**: CFG+データフロー特徴量を抽出
   ```bash
   cd analyze
   python ext_cfg_dfg_feature.py
   # -> feature_cache_*.json が生成される
   ```

3. **クラスタリング実行**: K-meansでコードを分類
   ```bash
   python -c "from kmeans_final_clean import main; main('general', 'real_code_features')"
   # -> clustering_results_YYYYMMDD_HHMMSS/ に結果保存
   ```

4. **結果分析**: F1スコア、混同行列を確認
   ```
   📊 全体評価:
      マクロ平均 F1: 0.8542
      正確度: 87.00%
   ```

5. **可視化**: グラフ構造を確認
   ```bash
   cd visualize
   python visualize_module_and_functions.py
   ```

### 継続的インテグレーション

```yaml
name: Feature Extraction & Clustering
on: [push, pull_request]

jobs:
  analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install pyjoern networkx scikit-learn scipy numpy pandas
    - name: Extract features
      run: |
        cd analyze
        python ext_cfg_dfg_feature.py
    - name: Run clustering
      run: |
        cd analyze
        python -c "from kmeans_final_clean import main; main('general', 'real_code_features')"
```

## トラブルシューティング

### よくある問題

1. **scipyがインストールされていない（ハンガリアンアルゴリズムエラー）**
   ```bash
   pip install scipy
   ```

2. **キャッシュファイルが見つからない**
   ```bash
   # 特徴量を再抽出
   cd analyze
   python ext_cfg_dfg_feature.py
   ```

3. **メモリ不足エラー**
   - ファイル数を減らす
   - バッチサイズを調整
   ```python
   # 一度に処理するファイル数を制限
   batch_results = batch_extract_integrated_features(file_list[:100])
   ```

4. **標準化エラー（分散が0）**
   - 特徴量がすべて同じ値の場合に発生
   - `OnlineStandardScaler`は自動的に処理（std=1に設定）

5. **パターン認識が正しくない**
   ```python
   # extract_pattern_from_filepath() をデバッグ
   from ext_cfg_dfg_feature import extract_pattern_from_file_path
   print(extract_pattern_from_file_path("your_file.py"))
   ```

### パフォーマンス最適化

1. **キャッシュ機能の活用**
   ```python
   # 差分更新で高速化（変更ファイルのみ処理）
   file_changes = detect_file_changes(target_dir, cache_file)
   updated_data = update_cache_incrementally(target_dir, cache_file, file_changes)
   ```

2. **並列処理（将来実装予定）**
   ```python
   # 複数ファイルの特徴量抽出を並列化
   from concurrent.futures import ProcessPoolExecutor
   with ProcessPoolExecutor() as executor:
       results = list(executor.map(extract_integrated_features_vector, file_list))
   ```

3. **メモリ効率の改善**
   - 大規模データセットは分割処理
   - 不要なキャッシュファイルを削除

## ファイル別機能一覧

| ファイル | 主要機能 | 使用頻度 |
|---------|---------|---------|
| `analyze/kmeans_final_clean.py` | K-meansクラスタリング、ハンガリアンアルゴリズム、評価指標計算 | ⭐⭐⭐ |
| `analyze/ext_cfg_dfg_feature.py` | CFG+データフロー特徴量抽出、キャッシュ管理 | ⭐⭐⭐ |
| `visualize/visualize_module_and_functions.py` | CFG/AST/DDGの視覚化 | ⭐⭐ |
| `comprehensive_analysis.py` | レガシー分析スクリプト | ⭐ |

## データフロー

```
ソースコード (*.py)
    ↓
[ext_cfg_dfg_feature.py]
    ↓ 特徴量抽出
feature_cache_*.json (11次元ベクトル)
    ↓
[kmeans_final_clean.py]
    ↓ 標準化 → クラスタリング → ハンガリアンアルゴリズム
clustering_results_*/ (JSON + 可視化画像)
    ↓
評価指標 (適合率, 再現率, F1スコア)
```

## 参考資料

### ツール・ライブラリ
- [PyJoern公式](https://github.com/fabsx00/pyjoern)
- [Joernプロジェクト](https://joern.io/)
- [scikit-learn K-means](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html)
- [scipy Hungarian Algorithm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html)

### 理論・論文
- [McCabe複雑度論文](https://www.literateprogramming.com/mccabe.pdf)
- Hungarian Algorithm (Kuhn-Munkres algorithm)
- データフロー解析の基礎

## ライセンス

本プロジェクトは、教育および研究目的での使用を想定しています。

---

**作成日**: 2025年1月
**更新日**: 2025年12月18日
**作成者**: 静的解析研究チーム
**主要機能**: CFG/DFG特徴量抽出、K-meansクラスタリング、ハンガリアンアルゴリズム、評価指標計算
