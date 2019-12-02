# This is a helper class for vector math. You can extend it or delete if you want.
from typing import List, Tuple

from util.vec import Vec3


class Segment:

    def __init__(self, start: Vec3, end: Vec3):
        self.start = start
        self.end = end
        self.to_end = end - start

    def nearest_point(self, position: Vec3, constrain: bool = True) -> Tuple[Vec3, float]:
        """
        Returns the point along the line defined by the segment which is nearest to the given position.
        It may be outside the bounds of the segment. Also returns the ratio or 'progress' from the
        start to the end. 0 is at the start, 1 is at the end, and anything outside that range means
        the nearest point is outside the bounds of the segment.
        """
        start_to_position = position - self.start
        plane_normal = self.to_end.normalized()
        on_plane = start_to_position.project_to_plane(plane_normal)
        point_on_segment = position - on_plane
        ratio = plane_normal.dot(point_on_segment) / self.to_end.length()
        if constrain:
            if ratio < 0:
                point_on_segment = self.start
            if ratio > 1:
                point_on_segment = self.end
        return point_on_segment, ratio


def get_path_progression(point: Vec3, path: List[Vec3]) -> Tuple[float, float]:
    min_distance = None
    closest_seg = None
    point_on_closest_seg = None
    distance_accum = 0
    progression_before_min = 0
    for i in range(0, len(path) - 1):
        seg = Segment(path[i], path[i+1])
        point_on_seg, ratio = seg.nearest_point(point)
        distance = point_on_seg.dist(point)
        if min_distance is None or distance < min_distance:
            min_distance = distance
            closest_seg = seg
            point_on_closest_seg = point_on_seg
            progression_before_min = distance_accum
        distance_accum += seg.to_end.length()

    progression = progression_before_min + (point_on_closest_seg - closest_seg.start).length()
    return progression, min_distance
