// train_model.py により自動生成。手編集しないこと。
//
// center_temp = intercept + coeffs[0]*特徴量[0] + coeffs[1]*特徴量[1] + ...
// 出力(center_temp)の単位: degC
// 特徴量(coeffsの添字と対応、この順序で値を渡すこと):
    //   [0] surface_temp_mean (単位: degC)
#pragma once

struct ModelCoefficients {
    float intercept;
    float coeffs[1];
};

// food_category = "hamburger_nichirei_mini" / R^2 = 0.8805
static const ModelCoefficients MODEL_HAMBURGER_NICHIREI_MINI = {11.472747f, {1.024638f}};
