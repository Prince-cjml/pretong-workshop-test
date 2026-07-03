#pragma once

#ifdef __cplusplus
extern "C" {
#endif

int fastops_api_version();

int standardize_features(
    const float* input,
    float* output,
    int rows,
    int cols,
    float epsilon
);

#ifdef __cplusplus
}
#endif
