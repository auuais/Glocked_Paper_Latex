#include <math.h>
#include <stdio.h>
#include "imu_madgwick.h"

static int finite_q(const Quaternion_t *q)
{
    return isfinite(q->q0) && isfinite(q->q1) && isfinite(q->q2) && isfinite(q->q3);
}

int main(void)
{
    MadgwickFilter_t filter;
    int stationary_finite, tilted_finite, no_accel_finite;
    Madgwick_Init(&filter, 125.0f, 0.12f);
    Madgwick_Update(&filter, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f);
    stationary_finite = finite_q(&filter.q);
    printf("identity_stationary: finite=%d q=(%.9g,%.9g,%.9g,%.9g)\n",
           stationary_finite, (double)filter.q.q0, (double)filter.q.q1,
           (double)filter.q.q2, (double)filter.q.q3);
    Madgwick_Init(&filter, 125.0f, 0.12f);
    Madgwick_Update(&filter, 0.0f, 0.0f, 0.0f, 0.01f, 0.0f, 1.0f);
    tilted_finite = finite_q(&filter.q);
    printf("small_tilt_control: finite=%d\n", tilted_finite);
    Madgwick_Init(&filter, 125.0f, 0.12f);
    Madgwick_Update(&filter, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f);
    no_accel_finite = finite_q(&filter.q);
    printf("zero_acceleration_control: finite=%d\n", no_accel_finite);
    puts("Scope: exact copied C host boundary reproduction; no physical IMU or timing test.");
    return (!stationary_finite && tilted_finite && no_accel_finite) ? 0 : 1;
}
