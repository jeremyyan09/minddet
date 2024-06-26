"""eval utils"""
import io as sysio

import numpy as np
from numba import njit


# @numba_jit(nopython=True)
def div_up(m, n):
    """div_up"""
    return m // n + (m % n > 0)


# @numba_jit
def get_thresholds(scores, num_gt, num_sample_pts=41):
    """get thresholds"""
    scores.sort()
    scores = scores[::-1]
    current_recall = 0
    thresholds = []
    for i, score in enumerate(scores):
        l_recall = (i + 1) / num_gt
        if i < (len(scores) - 1):
            r_recall = (i + 2) / num_gt
        else:
            r_recall = l_recall
        if ((r_recall - current_recall) < (current_recall - l_recall)) and (
            i < (len(scores) - 1)
        ):
            continue
        thresholds.append(score)
        current_recall += 1 / (num_sample_pts - 1.0)
    return thresholds


def _clean_gt_data(anno, current_cls_name, difficulty):
    """clean gt data"""
    min_height = [40, 25, 25]
    max_occlusion = [0, 1, 2]
    max_truncation = [0.15, 0.3, 0.5]
    num = len(anno["name"])
    num_valid = 0
    dc_bboxes, ignored = [], []

    for i in range(num):
        bbox = anno["bbox"][i]
        name = anno["name"][i].lower()
        height = abs(bbox[3] - bbox[1])
        if name == current_cls_name:
            valid_class = 1
        elif (current_cls_name == "pedestrian" and name == "person_sitting") or (
            current_cls_name == "car" and name == "van"
        ):
            valid_class = 0
        else:
            valid_class = -1
        ignore = False
        if (
            (anno["occluded"][i] > max_occlusion[difficulty])
            or (anno["truncated"][i] > max_truncation[difficulty])
            or (height <= min_height[difficulty])
        ):
            ignore = True
        if valid_class == 1 and not ignore:
            ignored.append(0)
            num_valid += 1
        elif valid_class == 0 or (ignore and (valid_class == 1)):
            ignored.append(1)
        else:
            ignored.append(-1)
        if anno["name"][i] == "DontCare":
            dc_bboxes.append(bbox)
    return num_valid, ignored, dc_bboxes


def _clean_dt_data(anno, current_cls_name, difficulty):
    """clean dt data"""
    min_height = [40, 25, 25]
    num = len(anno["name"])
    ignored = []
    for i in range(num):
        if anno["name"][i].lower() == current_cls_name:
            valid_class = 1
        else:
            valid_class = -1
        height = abs(anno["bbox"][i, 3] - anno["bbox"][i, 1])
        if height < min_height[difficulty]:
            ignored.append(1)
        elif valid_class == 1:
            ignored.append(0)
        else:
            ignored.append(-1)
    return ignored


def clean_data(gt_anno, dt_anno, current_class, difficulty):
    """clean data"""
    class_names = [
        "car",
        "pedestrian",
        "cyclist",
        "van",
        "person_sitting",
        "car",
        "tractor",
        "trailer",
    ]
    current_cls_name = class_names[current_class].lower()

    num_valid_gt, ignored_gt, dc_bboxes = _clean_gt_data(
        gt_anno, current_cls_name, difficulty
    )
    ignored_dt = _clean_dt_data(dt_anno, current_cls_name, difficulty)
    return num_valid_gt, ignored_gt, ignored_dt, dc_bboxes


# @numba_jit(nopython=True)
def image_box_overlap(boxes, query_boxes, criterion=-1):
    """image box overlap"""
    """
        Calculates the overlap of multiple boxes on the image with multiple query boxes

        Args:
            boxes (numpy.ndarray): An array of shape (n, 4), where n is the number of boxes and the 4th
            element is the width and height.
            query_boxes (numpy.ndarray): An array of shape (k, 4), where k is the number of query boxes and
            the 4th element is the width and height.
            criterion (int, optional): Overlap degree calculation method. - 1 for IoU, 0 for area,
            1 for minimum bounding rectangle. The default value is -1.

        Returns:
            numpy.ndarray: An array of shape (n, k), where n is the number of boxes and k is the number of query boxes.
            Each element represents the degree of overlap of boxes[n] with query_boxes[k].
    """
    n_boxes = boxes.shape[0]
    k_qboxes = query_boxes.shape[0]
    overlaps = np.zeros((n_boxes, k_qboxes), dtype=boxes.dtype)
    for k in range(k_qboxes):
        qbox_area = (query_boxes[k, 2] - query_boxes[k, 0]) * (
            query_boxes[k, 3] - query_boxes[k, 1]
        )
        for n in range(n_boxes):
            iw = min(boxes[n, 2], query_boxes[k, 2]) - max(
                boxes[n, 0], query_boxes[k, 0]
            )
            if iw > 0:
                ih = min(boxes[n, 3], query_boxes[k, 3]) - max(
                    boxes[n, 1], query_boxes[k, 1]
                )
                if ih > 0:
                    if criterion == -1:
                        ua = (
                            (boxes[n, 2] - boxes[n, 0]) * (boxes[n, 3] - boxes[n, 1])
                            + qbox_area
                            - iw * ih
                        )
                    elif criterion == 0:
                        ua = (boxes[n, 2] - boxes[n, 0]) * (boxes[n, 3] - boxes[n, 1])
                    elif criterion == 1:
                        ua = qbox_area
                    else:
                        ua = 1.0
                    overlaps[n, k] = iw * ih / ua
    return overlaps


@njit
def image_box_overlap_numba(boxes, query_boxes, criterion=-1):
    n_boxes = boxes.shape[0]
    k_qboxes = query_boxes.shape[0]
    overlaps = np.zeros((n_boxes, k_qboxes), dtype=boxes.dtype)

    qbox_area = query_boxes[:, 2] - query_boxes[:, 0]
    query_boxes_area = qbox_area.sum(axis=1)[:, np.newaxis]

    for n in range(n_boxes):
        box_area = (boxes[n, 2] - boxes[n, 0]) * (boxes[n, 3] - boxes[n, 1])
        box_left = boxes[n, 0]
        box_right = boxes[n, 2]
        box_top = boxes[n, 1]
        box_bottom = boxes[n, 3]

        for k in range(k_qboxes):
            iw = np.maximum(
                0,
                np.minimum(box_right, query_boxes[k, 2])
                - np.maximum(box_left, query_boxes[k, 0]),
            )
            if iw > 0:
                ih = np.maximum(
                    0,
                    np.minimum(box_bottom, query_boxes[k, 3])
                    - np.maximum(box_top, query_boxes[k, 1]),
                )
                if ih > 0:
                    if criterion == -1:
                        ua = box_area + query_boxes_area[k] - iw * ih
                    elif criterion == 0:
                        ua = box_area
                    elif criterion == 1:
                        ua = query_boxes_area[k]
                    else:
                        ua = 1.0
                    overlaps[n, k] += iw * ih / ua
    return overlaps


# @numba_jit(nopython=True)
def compute_statistics_jit(
    overlaps,
    gt_datas,
    dt_datas,
    ignored_gt,
    ignored_det,
    dc_bboxes,
    metric,
    min_overlap,
    thresh=0.0,
    compute_fp=False,
    compute_aos=False,
):
    """compute statistics jit"""
    det_size = dt_datas.shape[0]
    gt_size = gt_datas.shape[0]
    dt_scores = dt_datas[:, -1]
    dt_alphas = dt_datas[:, 4]
    gt_alphas = gt_datas[:, 4]
    dt_bboxes = dt_datas[:, :4]

    assigned_detection = [False] * det_size
    ignored_threshold = [False] * det_size
    if compute_fp:
        for i in range(det_size):
            if dt_scores[i] < thresh:
                ignored_threshold[i] = True
    # Using a large negative number to filter the cases with no detections
    # for counting False Positives
    no_detection = -10000000
    tp, fp, fn, similarity = 0, 0, 0, 0
    thresholds = np.zeros((gt_size,))
    thresh_idx = 0
    delta = np.zeros((gt_size,))
    delta_idx = 0
    for i in range(gt_size):
        if ignored_gt[i] == -1:
            continue
        det_idx = -1
        valid_detection = no_detection
        max_overlap = 0
        assigned_ignored_det = False

        for j in range(det_size):
            if ignored_det[j] == -1 or assigned_detection[j] or ignored_threshold[j]:
                continue
            overlap = overlaps[j, i]
            dt_score = dt_scores[j]
            if not compute_fp and overlap > min_overlap and dt_score > valid_detection:
                det_idx = j
                valid_detection = dt_score
            elif (
                compute_fp
                and overlap > min_overlap
                and (overlap > max_overlap or assigned_ignored_det)
                and ignored_det[j] == 0
            ):
                max_overlap = overlap
                det_idx = j
                valid_detection = 1
                assigned_ignored_det = False
            elif (
                compute_fp
                and overlap > min_overlap
                and (valid_detection == no_detection)
                and ignored_det[j] == 1
            ):
                det_idx = j
                valid_detection = 1
                assigned_ignored_det = True

        if valid_detection == no_detection and ignored_gt[i] == 0:
            fn += 1
        elif valid_detection != no_detection and (
            ignored_gt[i] == 1 or ignored_det[det_idx] == 1
        ):
            assigned_detection[det_idx] = True
        elif valid_detection != no_detection:
            # only a tp add a threshold.
            tp += 1
            thresholds[thresh_idx] = dt_scores[det_idx]
            thresh_idx += 1
            if compute_aos:
                delta[delta_idx] = gt_alphas[i] - dt_alphas[det_idx]
                delta_idx += 1

            assigned_detection[det_idx] = True
    if compute_fp:
        for i in range(det_size):
            if not (
                assigned_detection[i]
                or ignored_det[i] == -1
                or ignored_det[i] == 1
                or ignored_threshold[i]
            ):
                fp += 1
        nstuff = 0
        if metric == 0:
            overlaps_dt_dc = image_box_overlap(dt_bboxes, dc_bboxes, 0)
            for i in range(dc_bboxes.shape[0]):
                for j in range(det_size):
                    if (
                        assigned_detection[j]
                        or ignored_det[j] == -1
                        or ignored_det[j] == 1
                        or ignored_threshold[j]
                    ):
                        continue
                    if overlaps_dt_dc[j, i] > min_overlap:
                        assigned_detection[j] = True
                        nstuff += 1
        fp -= nstuff
        if compute_aos:
            tmp = np.zeros((fp + delta_idx,))
            for i in range(delta_idx):
                tmp[i + fp] = (1.0 + np.cos(delta[i])) / 2.0
            if tp > 0 or fp > 0:
                similarity = np.sum(tmp)
            else:
                similarity = -1
    return tp, fp, fn, similarity, thresholds[:thresh_idx]


def get_split_parts(num, num_part):
    """get split parts"""
    same_part = num // num_part
    remain_num = num % num_part
    if remain_num == 0:
        return [same_part] * num_part
    return [same_part] * num_part + [remain_num]


# @numba_jit(nopython=True)
def fused_compute_statistics(
    overlaps,
    pr,
    gt_nums,
    dt_nums,
    dc_nums,
    gt_datas,
    dt_datas,
    dontcares,
    ignored_gts,
    ignored_dets,
    metric,
    min_overlap,
    thresholds,
    compute_aos=False,
):
    """fused compute statistics"""
    gt_num = 0
    dt_num = 0
    dc_num = 0
    for i in range(gt_nums.shape[0]):
        for t, thresh in enumerate(thresholds):
            overlap = overlaps[
                dt_num : dt_num + dt_nums[i], gt_num : gt_num + gt_nums[i]
            ]

            gt_data = gt_datas[gt_num : gt_num + gt_nums[i]]
            dt_data = dt_datas[dt_num : dt_num + dt_nums[i]]
            ignored_gt = ignored_gts[gt_num : gt_num + gt_nums[i]]
            ignored_det = ignored_dets[dt_num : dt_num + dt_nums[i]]
            dontcare = dontcares[dc_num : dc_num + dc_nums[i]]
            tp, fp, fn, similarity, _ = compute_statistics_jit(
                overlap,
                gt_data,
                dt_data,
                ignored_gt,
                ignored_det,
                dontcare,
                metric,
                min_overlap=min_overlap,
                thresh=thresh,
                compute_fp=True,
                compute_aos=compute_aos,
            )
            pr[t, 0] += tp
            pr[t, 1] += fp
            pr[t, 2] += fn
            if similarity != -1:
                pr[t, 3] += similarity
        gt_num += gt_nums[i]
        dt_num += dt_nums[i]
        dc_num += dc_nums[i]


def _get_parted_overlaps(gt_annos, dt_annos, split_parts, metric):
    """get overlaps parted"""
    parted_overlaps = []
    example_idx = 0
    for num_part in split_parts:
        gt_annos_part = gt_annos[example_idx : example_idx + num_part]
        dt_annos_part = dt_annos[example_idx : example_idx + num_part]
        if metric == 0:
            gt_boxes = np.concatenate([a["bbox"] for a in gt_annos_part], 0)
            dt_boxes = np.concatenate([a["bbox"] for a in dt_annos_part], 0)
            overlap_part = image_box_overlap(gt_boxes, dt_boxes)
        else:
            raise ValueError("unknown metric")
        parted_overlaps.append(overlap_part)
        example_idx += num_part

    return parted_overlaps


def calculate_iou_partly(gt_annos, dt_annos, metric, num_parts=50):
    """fast iou algorithm. this function can be used independently to
    do result analysis. Must be used in CAMERA coordinate system.
    Args:
        gt_annos: dict, must from get_label_annos() in kitti_common.py
        dt_annos: dict, must from get_label_annos() in kitti_common.py
        metric: eval type. 0: bbox, 1: bev, 2: 3d
        num_parts: int. a parameter for fast calculate algorithm
    """
    assert len(gt_annos) == len(dt_annos)
    total_dt_num = np.stack([len(a["name"]) for a in dt_annos], 0)
    total_gt_num = np.stack([len(a["name"]) for a in gt_annos], 0)
    num_examples = len(gt_annos)
    split_parts = get_split_parts(num_examples, num_parts)

    parted_overlaps = _get_parted_overlaps(gt_annos, dt_annos, split_parts, metric)
    overlaps = []
    example_idx = 0
    for j, num_part in enumerate(split_parts):
        gt_num_idx, dt_num_idx = 0, 0
        for i in range(num_part):
            gt_box_num = total_gt_num[example_idx + i]
            dt_box_num = total_dt_num[example_idx + i]
            overlaps.append(
                parted_overlaps[j][
                    gt_num_idx : gt_num_idx + gt_box_num,
                    dt_num_idx : dt_num_idx + dt_box_num,
                ]
            )
            gt_num_idx += gt_box_num
            dt_num_idx += dt_box_num
        example_idx += num_part

    return overlaps, parted_overlaps, total_gt_num, total_dt_num


def _prepare_data(gt_annos, dt_annos, current_class, difficulty):
    """prepare data"""
    gt_datas_list = []
    dt_datas_list = []
    total_dc_num = []
    ignored_gts, ignored_dets, dontcares = [], [], []
    total_num_valid_gt = 0
    for i in range(len(gt_annos)):
        rets = clean_data(gt_annos[i], dt_annos[i], current_class, difficulty)
        num_valid_gt, ignored_gt, ignored_det, dc_bboxes = rets
        ignored_gts.append(np.array(ignored_gt, dtype=np.int64))
        ignored_dets.append(np.array(ignored_det, dtype=np.int64))
        if np.array(dc_bboxes).shape[0] == 0:
            dc_bboxes = np.zeros((0, 4)).astype(np.float64)
        else:
            dc_bboxes = np.stack(dc_bboxes, 0).astype(np.float64)
        total_dc_num.append(dc_bboxes.shape[0])
        dontcares.append(dc_bboxes)
        total_num_valid_gt += num_valid_gt
        gt_datas = np.concatenate(
            [gt_annos[i]["bbox"], gt_annos[i]["alpha"][..., np.newaxis]], 1
        )
        dt_datas = np.concatenate(
            [
                dt_annos[i]["bbox"],
                dt_annos[i]["alpha"][..., np.newaxis],
                dt_annos[i]["score"][..., np.newaxis],
            ],
            1,
        )
        gt_datas_list.append(gt_datas)
        dt_datas_list.append(dt_datas)
    total_dc_num = np.stack(total_dc_num, axis=0)
    return (
        gt_datas_list,
        dt_datas_list,
        ignored_gts,
        ignored_dets,
        dontcares,
        total_dc_num,
        total_num_valid_gt,
    )


def eval_class(
    gt_annos,
    dt_annos,
    current_classes,
    difficultys,
    metric,
    min_overlaps,
    compute_aos=False,
    num_parts=50,
):
    """Kitti eval. support 2d/bev/3d/aos eval. support 0.5:0.05:0.95 coco AP.
    Args:
        gt_annos: dict, must from get_label_annos() in kitti_common.py
        dt_annos: dict, must from get_label_annos() in kitti_common.py
        current_classes: int, 0: car, 1: pedestrian, 2: cyclist
        difficultys: int. eval difficulty, 0: easy, 1: normal, 2: hard
        metric: eval type. 0: bbox, 1: bev, 2: 3d
        min_overlaps: float, min overlap. official:
            [[0.7, 0.5, 0.5], [0.7, 0.5, 0.5], [0.7, 0.5, 0.5]]
            format: [metric, class]. choose one from matrix above.
        compute_aos: bool. compute aos or not
        num_parts: int. a parameter for fast calculate algorithm

    Returns:
        dict of recall, precision and aos
    """
    if len(gt_annos) != len(dt_annos):
        raise ValueError(
            f"Number of elements in ground-truth and detected annotations "
            f"lists must be equal, got {len(gt_annos)} and {len(dt_annos)}."
        )
    num_examples = len(gt_annos)
    split_parts = get_split_parts(num_examples, num_parts)

    rets = calculate_iou_partly(dt_annos, gt_annos, metric, num_parts)
    overlaps, parted_overlaps, total_dt_num, total_gt_num = rets
    n_sample_pts = 41
    num_minoverlap = len(min_overlaps)
    num_class = len(current_classes)
    num_difficulty = len(difficultys)
    precision = np.zeros([num_class, num_difficulty, num_minoverlap, n_sample_pts])
    for m, current_class in enumerate(current_classes):
        for n, difficulty in enumerate(difficultys):
            rets = _prepare_data(gt_annos, dt_annos, current_class, difficulty)
            (
                gt_datas_list,
                dt_datas_list,
                ignored_gts,
                ignored_dets,
                dontcares,
                total_dc_num,
                total_num_valid_gt,
            ) = rets
            for k, min_overlap in enumerate(min_overlaps[:, metric, m]):
                thresholdss = []
                for i in range(len(gt_annos)):
                    rets = compute_statistics_jit(
                        overlaps[i],
                        gt_datas_list[i],
                        dt_datas_list[i],
                        ignored_gts[i],
                        ignored_dets[i],
                        dontcares[i],
                        metric,
                        min_overlap=min_overlap,
                        thresh=0.0,
                        compute_fp=False,
                    )
                    _, _, _, _, thresholds = rets
                    thresholdss += thresholds.tolist()
                thresholdss = np.array(thresholdss)
                thresholds = get_thresholds(thresholdss, total_num_valid_gt)
                thresholds = np.array(thresholds)
                pr = np.zeros([len(thresholds), 4])
                idx = 0
                for j, num_part in enumerate(split_parts):
                    gt_datas_part = np.concatenate(
                        gt_datas_list[idx : idx + num_part], 0
                    )
                    dt_datas_part = np.concatenate(
                        dt_datas_list[idx : idx + num_part], 0
                    )
                    dc_datas_part = np.concatenate(dontcares[idx : idx + num_part], 0)
                    ignored_dets_part = np.concatenate(
                        ignored_dets[idx : idx + num_part], 0
                    )
                    ignored_gts_part = np.concatenate(
                        ignored_gts[idx : idx + num_part], 0
                    )
                    fused_compute_statistics(
                        parted_overlaps[j],
                        pr,
                        total_gt_num[idx : idx + num_part],
                        total_dt_num[idx : idx + num_part],
                        total_dc_num[idx : idx + num_part],
                        gt_datas_part,
                        dt_datas_part,
                        dc_datas_part,
                        ignored_gts_part,
                        ignored_dets_part,
                        metric,
                        min_overlap=min_overlap,
                        thresholds=thresholds,
                        compute_aos=compute_aos,
                    )
                    idx += num_part
                for i in range(len(thresholds)):
                    precision[m, n, k, i] = pr[i, 0] / (pr[i, 0] + pr[i, 1])
                for i in range(len(thresholds)):
                    precision[m, n, k, i] = np.max(precision[m, n, k, i:], axis=-1)
    ret_dict = {"precision": precision}
    return ret_dict


def get_map(prec):
    """get map"""
    sums = 0
    for i in range(0, prec.shape[-1], 4):
        sums = sums + prec[..., i]
    return sums / 11 * 100


def do_eval(
    gt_annos,
    dt_annos,
    current_classes,
    min_overlaps,
    compute_aos=False,
    difficultys=(0, 1, 2),
):
    """do eval"""
    # min_overlaps: [num_minoverlap, metric, num_class]
    ret = eval_class(
        gt_annos, dt_annos, current_classes, difficultys, 0, min_overlaps, compute_aos
    )
    # ret: [num_class, num_diff, num_minoverlap, num_sample_points]
    map_bbox = get_map(ret["precision"])
    return map_bbox


def print_str(value, *arg, sstream=None):
    """print str"""
    if sstream is None:
        sstream = sysio.StringIO()
    sstream.truncate(0)
    sstream.seek(0)
    print(value, *arg, file=sstream)
    return sstream.getvalue()


def get_official_eval_result(
    gt_annos, dt_annos, current_classes, difficultys=(0, 1, 2), return_data=False
):
    """get official eval result"""
    min_overlaps = np.array(
        [
            [
                [0.7, 0.5, 0.5, 0.7, 0.5, 0.7, 0.7, 0.7],
                [0.7, 0.5, 0.5, 0.7, 0.5, 0.7, 0.7, 0.7],
                [0.7, 0.5, 0.5, 0.7, 0.5, 0.7, 0.7, 0.7],
            ]
        ]
    )
    class_to_name = {
        0: "Car",
        1: "Pedestrian",
        2: "Cyclist",
        3: "Van",
        4: "Person_sitting",
        5: "car",
        6: "tractor",
        7: "trailer",
    }
    name_to_class = {v: n for n, v in class_to_name.items()}
    if not isinstance(current_classes, (list, tuple)):
        current_classes = [current_classes]
    current_classes_int = []
    for curcls in current_classes:
        if isinstance(curcls, str):
            current_classes_int.append(name_to_class[curcls])
        else:
            current_classes_int.append(curcls)
    current_classes = current_classes_int
    min_overlaps = min_overlaps[:, :, current_classes]
    result = "        Easy   Mod    Hard\n"
    map_bbox = do_eval(
        gt_annos, dt_annos, current_classes, min_overlaps, False, difficultys
    )
    for j, curcls in enumerate(current_classes):
        # mAP threshold array: [num_minoverlap, metric, class]
        # mAP result: [num_class, num_diff, num_minoverlap]
        for i in range(min_overlaps.shape[0]):
            result += print_str(
                (
                    f"{class_to_name[curcls]} "
                    "AP@{:.2f}, {:.2f}, {:.2f}:".format(*min_overlaps[i, :, j])
                )
            )
            result += print_str(
                (
                    f"bbox AP: {map_bbox[j, 0, i]: .2f}, "
                    f"{map_bbox[j, 1, i]: .2f}, "
                    f"{map_bbox[j, 2, i]: .2f}"
                )
            )
    if return_data:
        return result, map_bbox
    return result
