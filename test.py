import torch
from scipy.spatial.transform import Rotation


def quaternion_to_rotation_matrix(q):
    q = q / torch.norm(q, dim=1, keepdim=True)  # 归一化四元数

    qw, qx, qy, qz = q.unbind(dim=1)
    rotation_matrix = torch.stack([
        torch.stack([1 - 2*qy**2 - 2*qz**2, 2*qx*qy - 2*qz*qw, 2*qx*qz + 2*qy*qw], dim=1),
        torch.stack([2*qx*qy + 2*qz*qw, 1 - 2*qx**2 - 2*qz**2, 2*qy*qz - 2*qx*qw], dim=1),
        torch.stack([2*qx*qz - 2*qy*qw, 2*qy*qz + 2*qx*qw, 1 - 2*qx**2 - 2*qy**2], dim=1)
    ], dim=1)
    return rotation_matrix


def rotation_matrix_to_quaternion(R):
    qw = 0.5 * torch.sqrt(1 + R[:, 0, 0] + R[:, 1, 1] + R[:, 2, 2])
    qx = (R[:, 2, 1] - R[:, 1, 2]) / (4 * qw)
    qy = (R[:, 0, 2] - R[:, 2, 0]) / (4 * qw)
    qz = (R[:, 1, 0] - R[:, 0, 1]) / (4 * qw)
    return torch.stack([qw, qx, qy, qz], dim=1)


quaternion = torch.tensor([Rotation.from_euler('ZYX', [45, 0, 0], degrees=True).as_quat(),
                           Rotation.from_euler('ZYX', [-45, 0, 0], degrees=True).as_quat()])  # 实部为 0.7071，虚部为 [0, 0.7071, 0]
print(quaternion)
matrix = quaternion_to_rotation_matrix(quaternion)
print(matrix)
quaternion = rotation_matrix_to_quaternion(matrix)
print(quaternion)
