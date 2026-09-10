"""
物体認識テンプレート(食品カテゴリごとの既知情報)。

ここに登録した diameter_cm や weight_g は、カメラ画像から食品を
判別・カウントする際の参照値として使う想定。
中心温度の回帰モデル自体の入力特徴量ではない(現状は1食品カテゴリのみで
直径が一定のため、回帰の説明変数にはならない)。
"""

FOOD_TEMPLATES = {
    "beef_croquette_tablemark": {
        "display_name": "サクうまっ！牛肉コロッケ",
        "diameter_cm": 5.0,
        "weight_g_per_piece": 27,
        "pieces_per_pack": 5,
        "pack_weight_g": 135,
    },
    "hamburger": {
        "display_name": "ハンバーグ",
        "diameter_cm": None,
        "weight_g_per_piece": None,
        "pieces_per_pack": None,
        "pack_weight_g": None,
    },
}


def get_template(food_category: str) -> dict:
    if food_category not in FOOD_TEMPLATES:
        raise KeyError(f"未登録の食品カテゴリです: {food_category}")
    return FOOD_TEMPLATES[food_category]
