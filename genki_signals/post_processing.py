from __future__ import annotations

import itertools
from collections import OrderedDict, namedtuple
from typing import Callable, List, Tuple

import numpy as np
import torch
from more_itertools import pairwise
from torch import Tensor


def propagate_threshold(
    preds: list | Tensor | np.ndarray, low: float, high: float
) -> List[List[int]]:
    """Given a 1D array, find consecutive groups of values where all the values in each group are above `low` and at
    least one is above `high`, hysteresis thresholding

    Args:
        preds: 1D iterable of values with predictions to group together
        high: Higher threshold
        low: Lower threshold

    Returns:
        List of all the groups found

    Examples:
        >>> propagate_threshold([0.1, 0.97, 0.65, 0.99, 0.91], low=0.5, high=0.9)
        [[1, 2, 3, 4]]
        >>> propagate_threshold([0.55, 0.92, 0.4, 0.67, 0.7, 0.09, 0.91], low=0.5, high=0.9)
        [[0, 1], [6]]
    """
    if low > high:
        raise ValueError(f"Expected `low={low} to be smaller than `high={high}`")
    if isinstance(preds, (np.ndarray, Tensor)):
        if preds.ndim != 1:
            raise ValueError(f"Expected a 1-dim tensor, got `ndim={preds.ndim}`")

    groups, group, has_high = [], [], False
    for i, x in enumerate(preds):
        if x > high:
            group.append(i)
            has_high = True
        elif x > low:
            group.append(i)
        else:
            if has_high:
                # We only keep the groups that have at least one value above the `high` threshold
                groups.append(group)
            group, has_high = [], False
    else:
        if has_high:
            groups.append(group)

    return groups


def propagate_threshold_array(
    preds: Tensor | np.ndarray, low: float, high: float, eps: float = 0.001
) -> Tensor | np.ndarray:
    """For each row in a 2D array, find consecutive groups of values where all the values in each group are above `low`
    and at least one is above `high` and set all the `low` values in each group to `high + eps`, i.e. hysteresis
    thresholding per row

    The reason for setting values to `high + eps` is that it's intended to be used downstream in an argmax operation

    This algorithm is inspired by the hysterises part of the canny edge detector

    Failure mode:
        - There is no tie-break mechanism, so if for some reason 2 values in the same column are set to `high + eps`
          there is no way of selecting the "better" one. If this is becomes a problem, we could implement a tie-break
          with e.g. 3-point mean/median.

    Args:
        preds: A 2D array of values to groups together and threshold
        high: Higher threshold
        low: Lower threshold
        eps: Selected for torch.float32

    Returns:
        A copy of the original input with certain values set to `high + eps`

    Examples:
        >>> _preds = Tensor(
        ...    [[0.1, 0.95, 0.56, 0.7, 0.92],
        ...     [0.1, 0.05, 0.01, 0.06, 0.03],
        ...     [0.8, 0.0, 0.43, 0.24, 0.05]]
        ... )
        >>> propagate_threshold_array(_preds, low=0.5, high=0.9, eps=0.001)
        tensor([[0.1000, 0.9500, 0.9010, 0.9010, 0.9200],
                [0.1000, 0.0500, 0.0100, 0.0600, 0.0300],
                [0.8000, 0.0000, 0.4300, 0.2400, 0.0500]])
    """
    if isinstance(preds, Tensor):
        output = preds.clone()
    elif isinstance(preds, np.ndarray):
        output = preds.copy()
    else:
        raise ValueError
    for i, row in enumerate(preds):
        idxs_groups = propagate_threshold(row, low, high)
        for idxs in idxs_groups:
            # We update the output array s.t. all values the are above the low threshold (but not the high) are set to
            # `high + eps` for a downstream argmax operation
            idxs = np.array(idxs)
            replacements = output[i, idxs]
            is_low = replacements < high  # equivalent to `low < replacements < high`
            replacements[is_low] = high + eps
            output[i, idxs] = replacements

    return output


def process_predictions(
    pred: Tensor, confidence_low: float, confidence: float | None
) -> Tensor:
    if confidence is None:
        return pred
    pred_proc = propagate_threshold_array(
        torch.squeeze(pred, dim=0), low=confidence_low, high=confidence
    )
    pred_proc[0, :] = confidence
    return pred_proc


Group = namedtuple("Group", "key, length, loc")


def idx_pairs_from_start_mask(start_mask: np.ndarray) -> list:
    """Generates index pairs from a start mask, where 1 indicates a start of a new sequence (and 0 the continuation)

    Examples:
        >>> idx_pairs_from_start_mask(np.array([1, 0, 0, 1, 0]))
        [(0, 3), (3, 5)]
    """
    if len(start_mask) == 0:
        return []
    assert set(np.unique(start_mask)).issubset(
        {0, 1}
    ), "Expected the start mask to be only 0 or 1"
    assert (
        start_mask[0] == 1
    ), f"Expected the first element to be the start of a mask, got {start_mask[0]}"
    idx = np.where(start_mask)[0]
    idx = np.r_[idx, len(start_mask)]
    idx_pairs = list(pairwise(idx))
    return idx_pairs


def _extract_groups_np(x: np.ndarray, skip_zero: bool = False) -> List[Group]:
    """Separate vectorized version for speed"""
    if x.size == 0:
        return []
    start_mask = np.r_[1, np.diff(x) != 0]
    idx_pairs = idx_pairs_from_start_mask(start_mask)
    groups = [
        Group(key=int(x[p_min].item()), length=p_max - p_min, loc=p_min)
        for p_min, p_max in idx_pairs
    ]
    groups = [g for g in groups if not (skip_zero and g.key == 0)]
    return groups


def _extract_groups(p: list, skip_zero=False) -> List[Group]:
    """Extract consecutive groups of values in 1D arrays"""
    idx = 0
    groups = []
    for key, group in itertools.groupby(p):
        group_len = len(list(group))
        if skip_zero and key == 0:
            idx += group_len
            continue
        groups.append(Group(key=int(key), length=group_len, loc=idx))
        idx += group_len

    return groups


def extract_groups(
    x: List | torch.Tensor | np.ndarray, skip_zero: bool = False
) -> List[Group]:
    """Extract consecutive groups of values in 1D arrays

    Examples:
        >>> extract_groups(np.array([1, 1, 1, 3, 0]))
        [Group(key=1, length=3, loc=0), Group(key=3, length=1, loc=3), Group(key=0, length=1, loc=4)]
        >>> extract_groups(torch.Tensor([1]))
        [Group(key=1, length=1, loc=0)]
        >>> extract_groups([0,1], skip_zero=True)
        [Group(key=1, length=1, loc=1)]
        >>> extract_groups([1,0], skip_zero=True)
        [Group(key=1, length=1, loc=0)]
    """
    if isinstance(x, torch.Tensor):
        x = x.cpu().numpy()

    if isinstance(x, np.ndarray):
        groups = _extract_groups_np(x, skip_zero)
    else:
        groups = _extract_groups(x, skip_zero)

    return groups


def find_smallest_dist(dist_mat: np.ndarray) -> List[Tuple[int, int]]:
    """Return the indices of the array values sorted in ascending order

    Args:
        dist_mat: Distance matrix

    Returns:
        List of tuples with the indices into the distance matrix sorted ascending by size

    Examples:
        >>> x = np.array([[1.0, 2.0],
        ...               [0.2, 10.0],
        ...               [3.0, 90.0],
        ...               [1.0, 0.0]])
        >>> find_smallest_dist(x)
        [(3, 1), (1, 0), (0, 0), (3, 0), (0, 1), (2, 0), (1, 1), (2, 1)]
    """
    idx_flat_sort = np.argsort(dist_mat, axis=None)
    rows, cols = np.unravel_index(idx_flat_sort, dist_mat.shape)

    return list(zip(rows, cols))


def group_dist(group0: Group, group1: Group) -> float:
    return abs(group0.length - group1.length) + abs(group0.loc - group1.loc)


def group_dist_heuristic(
    group_old: Group,
    group_new: Group,
    match_lower_or_eq_idx: bool = False,
    enforce_key: bool = False,
) -> float:
    """Find distance between groups

    Examples:
        >>> group_dist_heuristic(Group(key=0, length=5, loc=2), Group(key=1, length=8, loc=1))
        4
        >>> group_dist_heuristic(Group(1, 5, 2), Group(1, 8, 3), match_lower_or_eq_idx=True)
        inf
        >>> group_dist_heuristic(Group(0, 5, 2), Group(1, 8, 1), enforce_key=True)
        inf
    """
    if match_lower_or_eq_idx and (group_new.loc - group_old.loc) > 0:
        return np.inf
    if enforce_key and group_old.key != group_new.key:
        return np.inf
    dist = group_dist(group_old, group_new)
    return dist


def calc_dist_mat(
    groups_registered: List[Group],
    groups_found: List[Group],
    dist_func: Callable[[Group, Group], float],
) -> np.ndarray:
    dist_mat = np.zeros((len(groups_registered), len(groups_found)))
    for i, g_reg in enumerate(groups_registered):
        for j, g_found in enumerate(groups_found):
            dist_mat[i, j] = dist_func(g_reg, g_found)
    return dist_mat


class GroupTracker:
    """
    https://www.pyimagesearch.com/2018/07/23/simple-object-tracking-with-opencv/
    """

    def __init__(
        self,
        dist_func: Callable[[Group, Group], float],
        max_disappeared: int = 2,
        min_group_size: int = 0,
        min_trigger_idx: int = 0,
        background_key: int | None = 0,
    ):
        self._max_disappeared = max_disappeared
        self._min_group_size = min_group_size
        self._min_trigger_idx = min_trigger_idx
        self._dist_func = dist_func
        self._background_key = background_key

        self._next_obj_id = 0
        self._obj_id_cycle_size = 1000
        self.obj_id_to_group = OrderedDict()
        self._disappeared = OrderedDict()
        self.new_objects = []

    def register(self, group: Group) -> None:
        """Register a new object"""
        self.obj_id_to_group[self._next_obj_id] = group
        self._disappeared[self._next_obj_id] = 0
        self._next_obj_id += 1
        self._next_obj_id %= self._obj_id_cycle_size
        self.new_objects.append(group)

    def deregister(self, object_id: int) -> None:
        """De-register an object that has disappeared"""
        del self.obj_id_to_group[object_id]
        del self._disappeared[object_id]

    def deregister_disappeared(self) -> None:
        """Find all object that have disappeared and de-register them"""
        objects_to_deregister = [
            obj_id
            for obj_id, n in self._disappeared.items()
            if n > self._max_disappeared
        ]
        for obj_id in objects_to_deregister:
            self.deregister(obj_id)

    def _filter_on_update_start(self, groups: List[Group]) -> List[Group]:
        """Only track groups of a certain size -> Filter small groups

        Heuristic to prevent from triggering on noise or only small parts of the movement
        """
        groups = [g for g in groups if g.length >= self._min_group_size]
        groups = [g for g in groups if g.key != self._background_key]
        return groups

    def _filter_on_update_end(self, groups: List[Group]) -> List[Group]:
        """Only trigger on new events that appear in the "right" half of each window

        Heuristic to ensure spurious events that 'appear' (usually noise or longer events split into 2 groups) to far
        away from the newest timestamp are not
        """
        return [g for g in groups if g.loc >= self._min_trigger_idx]

    def update(self, groups_found: List[Group]) -> Tuple[OrderedDict, List[Group]]:
        groups_found = self._filter_on_update_start(groups_found)

        self.new_objects = []
        if len(groups_found) == 0:
            # If we found no new objects, update the already tracked objects
            for object_id in self._disappeared:
                self._disappeared[object_id] += 1
        elif len(self.obj_id_to_group) == 0:
            # Register all if we have no tracked objects
            for g in groups_found:
                self.register(g)
        else:
            # We have objects tracked and we found new objects. Calculate which ones to match
            object_ids, groups_registered = tuple(zip(*self.obj_id_to_group.items()))
            # Rows -> Already tracked, Cols -> New objects
            dist_mat = calc_dist_mat(groups_registered, groups_found, self._dist_func)
            rows_seen, cols_seen = set(), set()
            for row, col in find_smallest_dist(dist_mat):
                if row in rows_seen or col in cols_seen or dist_mat[row, col] == np.inf:
                    continue
                obj_id = object_ids[row]
                self.obj_id_to_group[obj_id] = groups_found[col]
                self._disappeared[obj_id] = 0
                rows_seen.add(row)
                cols_seen.add(col)

            num_rows, num_cols = dist_mat.shape
            rows_not_seen = set(range(num_rows)).difference(rows_seen)
            cols_not_seen = set(range(num_cols)).difference(cols_seen)

            for row in rows_not_seen:
                obj_id = object_ids[row]
                self._disappeared[obj_id] += 1

            for col in cols_not_seen:
                self.register(groups_found[col])

        self.deregister_disappeared()

        self.new_objects = self._filter_on_update_end(self.new_objects)
        return self.obj_id_to_group, self.new_objects


def flatten_preds(preds: Tensor) -> Tensor:
    """Flatten predictions from (batch, num_classes, num_windows) to (batch * num_windows, num_classes)
    treating each window as an independent prediction

    Examples:
        >>> x = torch.FloatTensor(
        ...     [[[0.1, 0.2, 0.9, 0.8], [0.5, 0.8, 0.03, 0.01], [0.4, 0.0, 0.07, 0.19]],
        ...     [[1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]]
        ... )
        >>> x.shape
        torch.Size([2, 3, 4])
        >>> y = flatten_preds(x)
        >>> y.shape
        torch.Size([8, 3])
        >>> y
        tensor([[0.1000, 0.5000, 0.4000],
                [0.2000, 0.8000, 0.0000],
                [0.9000, 0.0300, 0.0700],
                [0.8000, 0.0100, 0.1900],
                [1.0000, 0.0000, 0.0000],
                [1.0000, 0.0000, 0.0000],
                [0.0000, 1.0000, 0.0000],
                [0.0000, 0.0000, 1.0000]])
    """
    preds_flat = preds.transpose(-2, -1)
    preds_flat = torch.flatten(preds_flat, start_dim=0, end_dim=1)
    return preds_flat


def flatten_labels(x: Tensor) -> Tensor:
    """Flatten labels from (batch, num_windows) to (batch * num_windows,)

    NOTE: Just a convenience to be able to easily compare to `_flatten_predictions`

    >>> flatten_labels(torch.LongTensor([[0, 1, 1, 0], [2, 2, 2, 2]]))
    tensor([0, 1, 1, 0, 2, 2, 2, 2])
    """
    return x.ravel()


def flatten_inputs(x: Tensor) -> Tensor:
    """Flatten raw (x) data from (batch, window_len, num_channels) to
    (batch * window_len, num_channels)."""
    return x.view(-1, x.size(-1))


def with_threshold(
    y: torch.Tensor, threshold: float | None, dim: int = 0
) -> torch.Tensor:
    """
    Examples:
        >>> x = torch.Tensor([[0.1, 0.2, 0.3],
        ...                   [0.4, 0.5, 0.6],
        ...                   [0.7, 0.8, 0.9],
        ...                   [0.91, 0.911, 0.912]])
        >>> with_threshold(x, 0.5)
        tensor([[0.5000, 0.2000, 0.3000],
                [0.5000, 0.5000, 0.6000],
                [0.5000, 0.8000, 0.9000],
                [0.5000, 0.9110, 0.9120]])
    """
    if threshold is None:
        return y

    y_thresh = y.clone()
    y_thresh[:, dim] = threshold
    return y_thresh


def prepare_predictions(
    pred: torch.Tensor, confidence: float, confidence_low: float
) -> List[Group]:
    pred_proc = process_predictions(pred, confidence_low, confidence)
    pred_argmax = torch.argmax(pred_proc, dim=-2)
    groups = extract_groups(pred_argmax)
    return groups
