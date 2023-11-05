
import torch
import numpy as np
import cv2


def annotator_wrapper(tensor_images, preprocessor_lambda):
    out_list = []

    for image in tensor_images:
        H, W, C = image.shape
        np_image = np.asarray(image * 255., dtype=np.uint8)

        np_result = preprocessor_lambda(np_image)

        np_result = cv2.resize(np_result, (W, H), interpolation=cv2.INTER_AREA)
        out_list.append(torch.from_numpy(np_result.astype(np.float32) / 255.0))

    return torch.stack(out_list, dim=0)


def HWC3(x):
    assert x.dtype == np.uint8

    if x.ndim == 2:
        x = x[:, :, None]
    assert x.ndim == 3

    H, W, C = x.shape
    assert C == 1 or C == 3 or C == 4

    if C == 3:
        return x

    if C == 1:
        return np.concatenate([x, x, x], axis=2)

    if C == 4:
        color = x[:, :, 0:3].astype(np.float32)
        alpha = x[:, :, 3:4].astype(np.float32) / 255.0
        y = color * alpha + 255.0 * (1.0 - alpha)
        y = y.clip(0, 255).astype(np.uint8)
        return y


def nms(x, t, s):
    x = cv2.GaussianBlur(x.astype(np.float32), (0, 0), s)

    f1 = np.array([[0, 0, 0], [1, 1, 1], [0, 0, 0]], dtype=np.uint8)
    f2 = np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0]], dtype=np.uint8)
    f3 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.uint8)
    f4 = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], dtype=np.uint8)

    y = np.zeros_like(x)

    for f in [f1, f2, f3, f4]:
        np.putmask(y, cv2.dilate(x, kernel=f) == x, x)

    z = np.zeros_like(y, dtype=np.uint8)
    z[y > t] = 255
    return z


def safe_step(x, step=2):
    y = x.astype(np.float32) * float(step + 1)
    y = y.astype(np.int32).astype(np.float32) / float(step)
    return y


def resize_image(input_image, resolution):
    H, W, C = input_image.shape

    H = float(H)
    W = float(W)
    k = float(resolution) / min(H, W)

    H *= k
    W *= k

    H = int(np.round(H / 64.0)) * 64
    W = int(np.round(W / 64.0)) * 64

    return cv2.resize(input_image, (W, H), interpolation=cv2.INTER_LANCZOS4 if k > 1 else cv2.INTER_AREA)
