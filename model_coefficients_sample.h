// train_model.py により自動生成。手編集しないこと。
#pragma once

struct ModelCoefficients {
    float intercept;
    float coeffs[1]; // surface_temp_mean
};

// R^2 = 0.7778
static const ModelCoefficients MODEL_BEEF_CROQUETTE_TABLEMARK = {18.980333f, {0.971468f}};

// R^2 = 0.8582
static const ModelCoefficients MODEL_HAMBURGER_NICHIREI_MINI = {10.783143f, {1.032503f}};
