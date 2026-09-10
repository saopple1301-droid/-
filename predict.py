"""
train_model.py が書き出した係数(model_coefficients.json)を使って、
新しく測った値から中心温度を推定する。

使い方:
    python3 predict.py --category beef_croquette_tablemark \\
        --value watt=500 --value elapsed_time_s=60 --value ambient_temp=23.4 \\
        --value initial_temp=-13.0 --value surface_temp_mean=80.0

--preference を指定すると、「猫舌さん向け」「熱々派」など好みに応じた
目安温度と比べて、まだ加熱が必要かどうか・あと何秒くらいかを表示する
(train_model.pyが計算したelapsed_time_s 1秒あたりの温度上昇率から
逆算する簡易的な見積もり):
    python3 predict.py --category beef_croquette_tablemark \\
        --value surface_temp_mean=48.2 --preference atsuatsu

好みの目安温度を自分で指定したい場合は --target-temp を使う:
    python3 predict.py --category beef_croquette_tablemark \\
        --value surface_temp_mean=48.2 --target-temp 85
"""

import argparse
import json

# 好み別の目安中心温度(℃)。対象食品はすでに加熱調理済みの冷凍食品を
# 温め直すだけなので、これは食中毒対策の安全温度ではなく、あくまで
# 「好みの熱さ」の目安。
PREFERENCE_TEMPS = {
    "neko_jita": {"label": "猫舌さん向け(ぬるめ)", "temp": 60.0},
    "normal": {"label": "ふつう", "temp": 75.0},
    "atsuatsu": {"label": "熱々派", "temp": 90.0},
}


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
    parser.add_argument(
        "--preference",
        choices=list(PREFERENCE_TEMPS.keys()),
        default=None,
        help=(
            "好みに応じた目安温度で判定する: "
            + ", ".join(f"{k}({v['label']})" for k, v in PREFERENCE_TEMPS.items())
        ),
    )
    args = parser.parse_args()

    target_temp = args.target_temp
    target_label = None
    if args.preference is not None:
        pref = PREFERENCE_TEMPS[args.preference]
        target_label = pref["label"]
        if target_temp is None:
            target_temp = pref["temp"]

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

    if target_temp is not None:
        label = f"{target_label}の目安" if target_label else "目標温度"
        rate = model.get("heating_rate_c_per_s")
        if rate is None:
            print(
                "→ 加熱速度のデータが無いため、あと何秒必要かは計算できません"
                "(model_coefficients.json を train_model.py で作り直してください)"
            )
        elif center_temp >= target_temp:
            print(f"→ {label}({target_temp:.0f}℃)にはもう十分温まっていると推定されます")
        elif rate <= 0:
            print("→ 加熱速度が0以下のため、追加加熱時間を計算できません")
        else:
            remaining_s = (target_temp - center_temp) / rate
            print(
                f"→ {label}({target_temp:.0f}℃)まで、あと約{remaining_s:.0f}秒の"
                f"加熱が必要と推定されます(簡易的な見積もりです)"
            )


if __name__ == "__main__":
    main()
