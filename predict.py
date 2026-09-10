"""
train_model.py が書き出した係数(model_coefficients.json)を使って、
新しく測った値から中心温度を推定する。

使い方:
    python3 predict.py --category beef_croquette_tablemark \\
        --value watt=500 --value elapsed_time_s=60 --value ambient_temp=23.4 \\
        --value initial_temp=-13.0 --value surface_temp_mean=80.0
"""

import argparse
import json


def parse_value_args(pairs):
    values = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"--value は name=value の形式で指定してください: {pair}")
        name, raw_value = pair.split("=", 1)
        values[name] = float(raw_value)
    return values


def predict(model, values):
    missing = [f for f in model["features"] if f not in values]
    if missing:
        raise ValueError(f"次の特徴量の値が指定されていません: {missing}")

    result = model["intercept"]
    for name, coef in zip(model["features"], model["coeffs"]):
        result += coef * values[name]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-json", default="model_coefficients.json")
    parser.add_argument("--category", required=True, help="food_category (例: beef_croquette_tablemark)")
    parser.add_argument(
        "--value",
        action="append",
        required=True,
        help="name=value の形式で特徴量の値を指定(複数回指定可)",
    )
    args = parser.parse_args()

    with open(args.model_json, encoding="utf-8") as f:
        models = json.load(f)

    if args.category not in models:
        raise SystemExit(
            f"カテゴリ '{args.category}' のモデルが見つかりません。"
            f"利用可能なカテゴリ: {list(models.keys())}"
        )

    model = models[args.category]
    values = parse_value_args(args.value)
    center_temp = predict(model, values)

    print(f"推定中心温度: {center_temp:.1f} ℃  (このモデルの学習時R^2={model['r2']:.4f})")


if __name__ == "__main__":
    main()
