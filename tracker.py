"""Lightweight centroid tracker: assigns persistent IDs to detections across frames.

This is what makes Loitering Detection and per-object dwell time possible —
without stable IDs you can't measure how long someone has been in a zone.
"""
import time
from collections import OrderedDict
import numpy as np


class CentroidTracker:
    def __init__(self, max_disappeared=30, max_distance=80):
        self.next_id = 0
        self.objects = OrderedDict()       # id -> centroid (x, y)
        self.disappeared = OrderedDict()   # id -> consecutive frames missing
        self.first_seen = {}               # id -> timestamp first tracked
        self.last_seen = {}                # id -> timestamp last matched
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid):
        oid = self.next_id
        self.objects[oid] = centroid
        self.disappeared[oid] = 0
        now = time.time()
        self.first_seen[oid] = now
        self.last_seen[oid] = now
        self.next_id += 1
        return oid

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]
        del self.first_seen[object_id]
        del self.last_seen[object_id]

    def update(self, centroids):
        if len(centroids) == 0:
            for oid in list(self.disappeared.keys()):
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self.deregister(oid)
            return self.objects

        if len(self.objects) == 0:
            for c in centroids:
                self.register(c)
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            D = np.linalg.norm(
                np.array(object_centroids)[:, None] - np.array(centroids)[None, :],
                axis=2,
            )

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows, used_cols = set(), set()
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > self.max_distance:
                    continue
                oid = object_ids[row]
                self.objects[oid] = centroids[col]
                self.disappeared[oid] = 0
                self.last_seen[oid] = time.time()
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(D.shape[0])) - used_rows
            unused_cols = set(range(D.shape[1])) - used_cols

            for row in unused_rows:
                oid = object_ids[row]
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self.deregister(oid)

            for col in unused_cols:
                self.register(centroids[col])

        return self.objects

    def duration(self, object_id):
        """Seconds this object has been continuously tracked."""
        if object_id not in self.first_seen:
            return 0
        return self.last_seen[object_id] - self.first_seen[object_id]
