"""
実測CSV(measured_data_trial1.csv)から、食品カテゴリごとに
「中心温度 = 係数 * 特徴量 + ... + 切片」の重回帰モデルを最小二乗法で求める。

外部ライブラリ(numpy / scikit-learn等)は使わず、Python標準ライブラリだけで
動くようにしている。行列演算はガウスの消去法で正規方程式
(X^T X) beta = X^T y を解く方式。

既定では food_category が "beef_croquette_tablemark"(冷凍コロッケ)の行だけを使う。
ハンバーグなど他カテゴリも含めたい場合は --categories all を指定する。

使い方:
    python3 train_model.py
    python3 train_model.py --categories all
    python3 train_model.py --csv data/measured_data_trial1.csv --features watt elapsed_time_s ambient_temp initial_temp surface_temp_mean
"""

import argparse
import csv
import json
from collections import defaultdict

DEFAULT_FEATURES = [
    "watt",
    "elapsed_time_s",
    "ambient_temp",
    "initial_temp",
    "surface_temp_mean",
]
DEFAULT_CATEGORIES = ["beef_croquette_tablemark"]
TARGET = "center_temp"
CATEGORY_COL = "food_category"


def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(value):
    if value is None or value == "":
        return None
    return float(value)


def build_dataset(rows, features, categories=None):
    """カテゴリごとに (X, y) を組み立てる。欠損値がある行、対象外カテゴリの行はスキップする。"""
    by_category = defaultdict(lambda: {"X": [], "y": []})
    skipped = 0
    for row in rows:
        category = row[CATEGORY_COL]
        if categories is not None and category not in categories:
            skipped += 1
            continue
        target = to_float(row[TARGET])
        feature_values = [to_float(row[f]) for f in features]
        if target is None or any(v is None for v in feature_values):
            skipped += 1
            continue
        by_category[category]["X"].append([1.0] + feature_values)  # 先頭1.0は切片項
        by_category[category]["y"].append(target)
    return by_category, skipped


def matmul_at_a(x):
    """X^T X を計算する。"""
    n_cols = len(x[0])
    result = [[0.0] * n_cols for _ in range(n_cols)]
    for row in x:
        for i in range(n_cols):
            for j in range(n_cols):
                result[i][j] += row[i] * row[j]
    return result


def matmul_at_y(x, y):
    """X^T y を計算する。"""
    n_cols = len(x[0])
    result = [0.0] * n_cols
    for row, target in zip(x, y):
        for i in range(n_cols):
            result[i] += row[i] * target
    return result


def solve_linear_system(a, b):
    """ガウスの消去法(部分ピボット選択あり)で a @ beta = b を解く。"""
    n = len(a)
    augmented = [row[:] + [b[i]] for i, row in enumerate(a)]

    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(augmented[r][col]))
        if abs(augmented[pivot_row][col]) < 1e-12:
            raise ValueError(
                "特徴量間の相関が強すぎるか、データ数が不足しているため解けません。"
                "特徴量を減らすかデータを増やしてください。"
            )
        augmented[col], augmented[pivot_row] = augmented[pivot_row], augmented[col]

        pivot = augmented[col][col]
        augmented[col] = [v / pivot for v in augmented[col]]

        for r in range(n):
            if r == col:
                continue
            factor = augmented[r][col]
            augmented[r] = [
                v - factor * augmented[col][i] for i, v in enumerate(augmented[r])
            ]

    return [row[-1] for row in augmented]


def r_squared(x, y, beta):
    mean_y = sum(y) / len(y)
    ss_tot = sum((v - mean_y) ** 2 for v in y)
    ss_res = 0.0
    for row, actual in zip(x, y):
        predicted = sum(coef * v for coef, v in zip(beta, row))
        ss_res += (actual - predicted) ** 2
    if ss_tot == 0:
        return float("nan")
    return 1 - ss_res / ss_tot


def fit(x, y):
    ata = matmul_at_a(x)
    aty = matmul_at_y(x, y)
    beta = solve_linear_system(ata, aty)
    r2 = r_squared(x, y, beta)
    return beta, r2


def format_cpp_header(models, features):
    lines = [
        "// train_model.py により自動生成。手編集しないこと。",
        "#pragma once",
        "",
        "struct ModelCoefficients {",
        "    float intercept;",
        f"    float coeffs[{len(features)}]; // {', '.join(features)}",
        "};",
        "",
    ]
    for category, (beta, r2) in models.items():
        var_name = f"MODEL_{category.upper()}"
        intercept, *coeffs = beta
        lines.append(f"// R^2 = {r2:.4f}")
        lines.append(
            f"static const ModelCoefficients {var_name} = {{{intercept:.6f}f, "
            f"{{{', '.join(f'{c:.6f}f' for c in coeffs)}}}}};"
        )
        lines.append("")
    return "\n".join(lines)


def format_json(models, features):
    """predict.py が読み込む形式で係数を書き出す。"""
    return {
        category: {
            "features": features,
            "intercept": beta[0],
            "coeffs": beta[1:],
            "r2": r2,
        }
        for category, (beta, r2) in models.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="data/measured_data_trial1.csv")
    parser.add_argument("--features", nargs="+", default=DEFAULT_FEATURES)
    parser.add_argument(
        "--categories",
        nargs="+",
        default=DEFAULT_CATEGORIES,
        help="学習対象のfood_category(既定: 冷凍コロッケのみ)。全カテゴリを使う場合は --categories all を指定",
    )
    parser.add_argument("--out-header", default="model_coefficients_sample.h")
    parser.add_argument("--out-json", default="model_coefficients.json")
    args = parser.parse_args()

    categories = None if args.categories == ["all"] else args.categories
    rows = load_rows(args.csv)
    by_category, skipped = build_dataset(rows, args.features, categories)

    print(f"読み込んだ行数: {len(rows)} / 欠損値・対象外カテゴリでスキップした行数: {skipped}")
    print(f"対象カテゴリ: {'全カテゴリ' if categories is None else categories}")
    print(f"使用する特徴量: {args.features}")
    print()

    models = {}
    for category, data in by_category.items():
        x, y = data["X"], data["y"]
        if len(x) <= len(args.features):
            print(f"[{category}] データ数({len(x)}件)が特徴量数より少ないためスキップ")
            continue
        beta, r2 = fit(x, y)
        models[category] = (beta, r2)
        intercept, *coeffs = beta
        print(f"[{category}] n={len(x)}, R^2={r2:.4f}")
        print(f"  center_temp = {intercept:.4f}")
        for name, coef in zip(args.features, coeffs):
            print(f"      + ({coef:+.4f}) * {name}")
        print()

    if models:
        header = format_cpp_header(models, args.features)
        with open(args.out_header, "w", encoding="utf-8") as f:
            f.write(header)
        print(f"C++ヘッダを書き出しました: {args.out_header}")

        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(format_json(models, args.features), f, ensure_ascii=False, indent=2)
        print(f"予測用の係数ファイルを書き出しました: {args.out_json}")
        print(f"→ predict.py --category <カテゴリ名> --value 特徴量名=値 ... で予測できます")


if __name__ == "__main__":
    main()
