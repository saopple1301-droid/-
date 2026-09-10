# 電子レンジ対応 非接触中心温度推定センサー — モデル構築

## これは何を使っているか

`train_model.py` は **Pythonの標準ライブラリだけ**で動く重回帰(最小二乗法)スクリプトです。
numpyやscikit-learnのインストールは不要です(データ数が数十件と少なく、
単純な線形回帰で十分なため、あえて外部ライブラリに依存させていません)。

やっていることは中学〜高校レベルの数学で説明できます。

- 「中心温度 = a×加熱ワット数 + b×経過秒数 + c×室温 + d×初期温度 + e×表面温度平均 + 切片」
  という式の a, b, c, d, e と切片を、実測データに一番よく当てはまるように求める(最小二乗法)。
- 食品カテゴリ(牛肉コロッケ／ハンバーグ)ごとに別々の式を作る。

## 使い方

```bash
python3 train_model.py
```

`data/measured_data_trial1.csv` を読み込み、カテゴリごとの係数とR²(当てはまりの良さ、
1に近いほど良い)をターミナルに表示し、`model_coefficients_sample.h`(C++ヘッダ)を
自動生成します。ファームウェア(`center_temp_sensor.ino`)側はこのヘッダの係数を
読んで中心温度を計算する想定です。

特徴量を絞り込みたい場合(例: 引き継ぎ書にある表面温度のみのモデルを再現):

```bash
python3 train_model.py --features surface_temp_mean
```

これで引き継ぎ書記載の `center_temp = 18.98 + 0.971 × surface_temp_mean`(R²=0.778)と
同じ結果になることを確認済みです。

## 実際に中心温度を予測する(predict.py)

`train_model.py` は「係数を求める」だけで、それ単体では中心温度は計算できません。
求めた係数を使って実際に予測するには `predict.py` を使います。

```bash
# 1. 学習(係数を計算し、model_coefficients.json を書き出す)
python3 train_model.py

# 2. 予測(新しく測った値を入れると中心温度が返る)
python3 predict.py --category beef_croquette_tablemark \
    --value watt=500 --value elapsed_time_s=60 --value ambient_temp=23.4 \
    --value initial_temp=-13.0 --value surface_temp_mean=80.0
# => 推定中心温度: 93.6 ℃  (このモデルの学習時R^2=0.8144)
```

`--value` は `train_model.py` で使った特徴量と同じ名前を全て指定する必要があります
(過不足があるとエラーで教えてくれます)。ファームウェア側で直接計算したい場合は、
`model_coefficients_sample.h` の係数を同じ式(切片 + Σ係数×特徴量)に当てはめれば
C++でも同じ結果になります。

## 直径5cm(コロッケ)の扱いについて

「コロッケの直径は約5cm」という情報は `food_templates.py` の `FOOD_TEMPLATES` に
メタ情報として登録しました。現時点では牛肉コロッケという1食品カテゴリしかデータが
無く、直径も一定なので、**回帰モデルの説明変数(特徴量)としては使っていません**。
主にカメラ画像から食品の種類やサイズを判別する側(`food_templates.py`の物体認識ロジック)
で参照する値です。将来、直径の異なる食品を複数扱うようになったら、
「表面積/体積比」のような形でモデルの特徴量に組み込むことも検討できます。

## 今後の改善点(引き継ぎ書より)

- `weight_loss_rate`(重量変化率)を実測データに追加すると、本来想定していた
  5特徴量フルのモデルが作れる(現在は代わりに watt/elapsed_time_s/ambient_temp/
  initial_temp/surface_temp_mean の5特徴量を使用)。
- データ数(n=16, n=23)がまだ少ないため、追加データが増えるほど信頼性が上がる。
