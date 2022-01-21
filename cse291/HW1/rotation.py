import math
from pprint import pprint

import open3d as o3d

import numpy as np
import numpy.linalg as LA
from scipy import misc
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

# Note Matplotlib is only suitable for simple 3D visualization.
# For later problems, you should not use Matplotlib to do the plotting
from icecream import ic

np.set_printoptions(suppress=True)

sqrt2 = math.sqrt(2)

p = np.array([1 / sqrt2, 1 / sqrt2, 0, 0])
q = np.array([1 / sqrt2, 0, 1 / sqrt2, 0])


def angle_normalize(x):
    return ((x + np.pi) % (2 * np.pi)) - np.pi


def skew2vec(x_hat: np.ndarray) -> np.ndarray:
    """
    hat map so3 to vector
    :param x_hat:
    :return (3,) vector
    """
    assert x_hat.shape == (3, 3), "x_hat must be a 3x3 matrix"
    x1, x2, x3 = x_hat[2, 1], x_hat[0, 2], x_hat[1, 0]
    return np.array([x1, x2, x3])


def vec2skew(x: np.ndarray) -> np.ndarray:
    """
    vector to hat map so3
     [[0, -x3, x2],
      [x3, 0, -x1],
      [-x2, x1, 0]]
    :param x: vector
    :type x: numpy array vector
    :return: skew symmetric matrix
    """
    assert x.size == 3, "x must be a vector with 3 elements"
    x_hat = np.zeros((3, 3), dtype=np.float64)
    x_hat[0, 1] = -x[2]
    x_hat[0, 2] = x[1]
    x_hat[1, 0] = x[2]
    x_hat[1, 2] = -x[0]
    x_hat[2, 0] = -x[1]
    x_hat[2, 1] = x[0]

    return x_hat


def get_qs_qv_from_Quat(quat: np.ndarray):
    """Extract qs and qv from quaternion"""
    assert quat.size == 4, "q must be a quaternion with 4 elements"
    qs = quat[0]
    qv = quat[1:]
    return qs, qv


def get_rotation_matrix_from_Quat(quat: np.ndarray):
    assert quat.size == 4, "q must be a quaternion with 4 elements"
    assert abs(LA.norm(quat) - 1) < 1e-6, "q must be a unit quaternion"
    I = np.eye(3)
    qs, qv = get_qs_qv_from_Quat(quat)
    qv = qv.reshape(3, 1)

    qv_skew = vec2skew(qv)
    a = qs * I + qv_skew
    b = qs * I - qv_skew

    Eq = np.hstack([-qv, a])
    Gq = np.hstack([-qv, b])
    return Eq @ Gq.T


def get_exponential_coordinate_from_Quat(quat: np.ndarray):
    """
    return:
        omega_hat: unit vector of rotation axis
        theta: angle of rotation
    """
    qs, qv = get_qs_qv_from_Quat(quat)

    # A more numerically stable expression of the rotation angle
    # theta = 2 * np.arccos(qs)
    theta = 2 * np.arctan2(LA.norm(qv), qs)

    if theta == 0:
        return theta, np.zeros_like(qv)
    omega_hat = qv / np.sin(theta / 2)
    assert abs(LA.norm(omega_hat) - 1) < 1e-6, "||w|| != 1"

    return omega_hat, theta


def get_rotation_matrix_from_axis_angle(omega_hat: np.ndarray, theta: float):
    """
    get rotation matrix from exp map
    R ∈ SO(3) := Rot(w,theta)
        = \exp^{[\hat{w}] \theta}
        = I + [w]sin(\theta) + [w]^2 (1-cos(\theta))
    :param omega_hat: unit vector of rotation axis
    :param theta: angle of rotation
    return: rotation matrix
    """
    assert LA.norm(omega_hat) == 1, "omega_hat must be a unit vector"

    omega_hat_skew = vec2skew(omega_hat)

    # Rodrigues Formula
    rot = (
        np.eye(3)
        + omega_hat_skew * np.sin(theta)
        + LA.fractional_matrix_power(omega_hat_skew, 2) * (1 - np.cos(theta))
    )

    test = o3d.geometry.get_rotation_matrix_from_axis_angle(omega_hat * theta)
    assert np.allclose(rot, LA.expm(omega_hat_skew * theta)), "exp map is not correct"
    assert np.allclose(rot, test), "rotation matrix is not correct"
    return rot


def Q1():
    # (1) ==============================================
    r = (q + p) / 2
    norm_r = LA.norm(r)
    print(f"norm of r: {norm_r}")

    # unit quaternion
    unit_r = r / norm_r
    assert abs(LA.norm(unit_r) - 1) < 1e-6, "r is not a unit quaternion"

    rot = o3d.geometry.get_rotation_matrix_from_quaternion(unit_r)

    M_r = get_rotation_matrix_from_Quat(unit_r)
    assert np.allclose(M_r, rot), "rotation matrix is not correct"
    print(f"M(r): ")
    pprint(M_r)

    omega_hat_r, theta_r = get_exponential_coordinate_from_Quat(unit_r)
    print(f"theta: {theta_r: .4f} in radians / {np.rad2deg(theta_r)} in degrees")
    print(f"omega_hat_r: {omega_hat_r}")


def Q2():
    omega_hat_p, theta_p = get_exponential_coordinate_from_Quat(p)
    omega_hat_q, theta_q = get_exponential_coordinate_from_Quat(q)

    print(f"theta_p: {theta_p: .4f} in radians / {np.rad2deg(theta_p)} in degrees")
    print(f"omega_hat_p: {omega_hat_p}")
    print(f"theta_q: {theta_q: .4f} in radians / {np.rad2deg(theta_q)} in degrees")
    print(f"omega_hat_q: {omega_hat_q}")


def Q3_a():
    omega_hat_p, theta_p = get_exponential_coordinate_from_Quat(p)
    omega_hat_q, theta_q = get_exponential_coordinate_from_Quat(q)

    R_p = get_rotation_matrix_from_axis_angle(omega_hat_p, theta_p)
    R_q = get_rotation_matrix_from_axis_angle(omega_hat_q, theta_q)
    ic(R_p, R_q)


def Q3_b():
    _, p_qv = get_qs_qv_from_Quat(p)
    _, q_qv = get_qs_qv_from_Quat(q)

    p_skew = vec2skew(p_qv)
    q_skew = vec2skew(q_qv)

    a = LA.expm(p_skew)
    b = LA.expm(q_skew)

    c = a @ b
    d = LA.expm(p_skew + q_skew)
    ic(c, d)

    print(f"exp([w1] + [w2]) = exp([w1]) exp([w2]): {np.allclose(c, d)}")


def Q4_a():
    p_prime = -p
    q_prime = -q

    """
    Two unit quaternions correspond to the same rotation
    R(q) = R(-q)
    """

    omega_hat_p, theta_p = get_exponential_coordinate_from_Quat(p)
    omega_hat_q, theta_q = get_exponential_coordinate_from_Quat(q)
    omega_hat_p_prime, theta_p_prime = get_exponential_coordinate_from_Quat(p_prime)
    omega_hat_q_prime, theta_q_prime = get_exponential_coordinate_from_Quat(q_prime)

    print(f"theta_p: {theta_p: .4f} in radians / {np.rad2deg(theta_p)} in degrees")
    print(f"omega_hat_p: {omega_hat_p}")
    print(
        f"theta_p': {theta_p_prime: .4f} in radians / {np.rad2deg(theta_p_prime)} in degrees"
    )
    print(f"omega_hat_p': {omega_hat_p_prime}")

    print(
        f"equal rotation: {np.allclose(get_rotation_matrix_from_Quat(p), get_rotation_matrix_from_Quat(p_prime))}"
    )

    print("-" * 50)
    print(f"theta_q: {theta_q: .4f} in radians / {np.rad2deg(theta_q)} in degrees")
    print(f"omega_hat_q: {omega_hat_q}")
    print(
        f"theta_q': {theta_q_prime: .4f} in radians / {np.rad2deg(theta_q_prime)} in degrees"
    )
    print(f"omega_hat_q': {omega_hat_q_prime}")
    print(
        f"equal rotation: {np.allclose(get_rotation_matrix_from_Quat(q), get_rotation_matrix_from_Quat(q_prime))}"
    )


def show_points(points):
    fig = plt.figure()
    ax = fig.gca(projection="3d")
    ax.set_xlim3d([-2, 2])
    ax.set_ylim3d([-2, 2])
    ax.set_zlim3d([0, 4])
    ax.scatter(points[0], points[2], points[1])


def compare_points(points1, points2):
    fig = plt.figure()
    ax = plt.axes(projection="3d")
    ax.set_xlim3d([-2, 2])
    ax.set_ylim3d([-2, 2])
    ax.set_zlim3d([0, 4])
    ax.scatter(points1[0], points1[2], points1[1])
    ax.scatter(points2[0], points2[2], points2[1])


def newtonsMethod(f, x0, tol=1.48e-08, max_iter=100):
    x = x0
    for itr in range(max_iter):
        df = misc.derivative(f, x, dx=1e-6)
        ic(df.shape)
        x1 = x - f(x) / df
        if abs(x1 - x) < tol:
            print(f"the root was found to be at {x1} after {itr} iterations")
            return x1
        x = x1
    print("Maximum number of iterations exceeded")
    return x


def hw0_solve(A, b, eps=1):
    """
    To find x
    x = h(\lambda))
    """
    I = np.eye(A.shape[1])
    h = lambda l: LA.inv(A.T @ A + 2 * l * I) @ A.T @ b
    f = lambda l: h(l).T @ h(l) - eps

    l0 = 0
    l = newtonsMethod(f, l0, eps, max_iter=100)

    return h(l)


if __name__ == "__main__":
    npz = np.load("data/HW1_P1.npz")
    X = npz["X"]
    Y = npz["Y"]
    ic(X.shape, Y.shape)
    compare_points(X, Y)  # noisy teapotsand

    # # implemntation of Q3
    # R1 = np.eye(3)
    # # solve this problem here, and store your final results in R1
    # for _ in range(1):
    #     hw0_solve(R1@X, Y, eps=1)
    # # Testing code, you should see the points of the 2 teapots roughly overlap
    # compare_points(R1@X, Y)
    # # plt.show()
    # print(R1.T@R1)
