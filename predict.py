"""
train_model.py が書き出した係数(model_coefficients.json)を使って、
新しく測った値から中心温度を推定する。

使い方:
    python3 predict.py --category beef_croquette_tablemark \\
        --value watt=500 --value elapsed_time_s=60 --value ambient_temp=23.4 \\
        --value initial_temp=-13.0 --value surface_temp_mean=80.0

--target-temp を指定すると、まだ目標温度に届いていない場合に
「あと何秒加熱すべきか」も合わせて表示する(train_model.pyが計算した
elapsed_time_s 1秒あたりの温度上昇率から逆算する簡易的な見積もり):
    python3 predict.py --category beef_croquette_tablemark \\
        --value surface_temp_mean=48.2 --target-temp 85
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
    parser.add_argument(
        "--target-temp",
        type=float,
        default=None,
        help="この温度(℃)に達するまであと何秒加熱すべきかも表示する",
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

    if args.target_temp is not None:
        rate = model.get("heating_rate_c_per_s")
        if rate is None:
            print(
                "→ 加熱速度のデータが無いため、あと何秒必要かは計算できません"
                "(model_coefficients.json を train_model.py で作り直してください)"
            )
        elif center_temp >= args.target_temp:
            print(f"→ すでに目標温度({args.target_temp:.1f}℃)に達していると推定されます")
        elif rate <= 0:
            print("→ 加熱速度が0以下のため、追加加熱時間を計算できません")
        else:
            remaining_s = (args.target_temp - center_temp) / rate
            print(
                f"→ 目標温度({args.target_temp:.1f}℃)まで、あと約{remaining_s:.0f}秒の"
                f"加熱が必要と推定されます(加熱速度 約{rate:.3f}℃/秒として計算。簡易的な見積もりです)"
            )


if __name__ == "__main__":
    main()
