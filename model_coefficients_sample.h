// train_model.py により自動生成。手編集しないこと。
#pragma once

struct ModelCoefficients {
    float intercept;
    float coeffs[5]; // watt, elapsed_time_s, ambient_temp, initial_temp, surface_temp_mean
};

// R^2 = 0.8144
static const ModelCoefficients MODEL_BEEF_CROQUETTE_TABLEMARK = {-395.000000f, {0.041337f, 0.648168f, 14.984375f, -2.684896f, 0.543725f}};

// R^2 = 0.7895
static const ModelCoefficients MODEL_HAMBURGER = {-16.431460f, {0.045246f, 1.267151f, -0.075063f, -2.550408f, -0.063380f}};
