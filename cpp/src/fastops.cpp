#include "fastops.h"

#include <Eigen/Dense>
#include <algorithm>
#include <cmath>

extern "C" int fastops_api_version() {
    return 1;
}

extern "C" int standardize_feature(
    const float* input,
    float* output,
    int rows,
    int cols,
    float epsilon
) {
    if (input == nullptr || output == nullptr) {
        return 1;
    }
    if (
        rows <= 0 ||
        cols <= 0 ||
        epsilon <= 0.0F
    ) {
        return 2;
    }

    using Matrix =
        Eigen::Matrix<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>;

    Eigen::Map<const Matrix> x(input, rows, cols);
    Eigen::Map<Matrix> y(output, rows, cols);

    for (int col = 0; col < cols; ++col) {
        const auto values = x.col(col);
        const float mean = values.mean();
        const float variance = (values.array() - mean).square().mean();
        const float stddev = std::max(std::sqrt(variance), epsilon);
        y.col(col) = (values.array() - mean) / stddev;
    }

    return 0;
}
