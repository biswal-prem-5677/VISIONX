"""
VisionX — Tracking Unit Tests
================================
Tests for the tracker and tracking module using synthetic detections.
"""


from edge.core.tracker import Tracker, _iou
from edge.modules.tracking import TrackingModule
from shared.models import BoundingBox, Detection


def _make_detection(x1, y1, x2, y2, cls="person", conf=0.9) -> Detection:
    """Helper to create a detection."""
    return Detection(
        class_id=0,
        class_name=cls,
        confidence=conf,
        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
    )


class TestIoU:
    """Tests for the IoU computation."""

    def test_perfect_overlap(self):
        box = BoundingBox(x1=0, y1=0, x2=100, y2=100)
        assert _iou(box, box) == 1.0

    def test_no_overlap(self):
        a = BoundingBox(x1=0, y1=0, x2=50, y2=50)
        b = BoundingBox(x1=100, y1=100, x2=200, y2=200)
        assert _iou(a, b) == 0.0

    def test_partial_overlap(self):
        a = BoundingBox(x1=0, y1=0, x2=100, y2=100)
        b = BoundingBox(x1=50, y1=50, x2=150, y2=150)
        iou = _iou(a, b)
        # Intersection: 50x50 = 2500, Union: 10000+10000-2500 = 17500
        assert abs(iou - 2500 / 17500) < 0.001

    def test_contained(self):
        a = BoundingBox(x1=0, y1=0, x2=100, y2=100)
        b = BoundingBox(x1=25, y1=25, x2=75, y2=75)
        iou = _iou(a, b)
        # Intersection: 50x50 = 2500, Union: 10000+2500-2500 = 10000
        assert abs(iou - 0.25) < 0.001


class TestTracker:
    """Tests for the core Tracker."""

    def test_new_track_created(self):
        tracker = Tracker()
        dets = [_make_detection(10, 10, 50, 50)]
        results = tracker.update(dets)
        assert len(results) == 1
        assert results[0].track_id is not None

    def test_track_persists(self):
        tracker = Tracker(min_hits=1)
        dets1 = [_make_detection(10, 10, 50, 50)]
        r1 = tracker.update(dets1)
        tid = r1[0].track_id

        # Same position next frame
        dets2 = [_make_detection(12, 12, 52, 52)]
        r2 = tracker.update(dets2)

        assert r2[0].track_id == tid

    def test_multiple_tracks(self):
        tracker = Tracker()
        dets = [
            _make_detection(10, 10, 50, 50),
            _make_detection(200, 200, 250, 250),
        ]
        results = tracker.update(dets)
        assert len(results) == 2
        ids = {r.track_id for r in results}
        assert len(ids) == 2  # Different IDs

    def test_track_deleted_after_max_age(self):
        tracker = Tracker(max_age=2, min_hits=1)
        # Frame 1: create track
        tracker.update([_make_detection(10, 10, 50, 50)])
        # Frames 2-4: no detections
        tracker.update([])
        tracker.update([])
        tracker.update([])

        tracks = tracker.get_active_tracks()
        assert len(tracks) == 0

    def test_get_track_count(self):
        tracker = Tracker(min_hits=1)
        dets = [
            _make_detection(10, 10, 50, 50, cls="person"),
            _make_detection(200, 200, 250, 250, cls="car"),
        ]
        # Need multiple frames for confirmation
        tracker.update(dets)
        tracker.update(dets)

        assert tracker.get_track_count() >= 2
        assert tracker.get_track_count("person") >= 1

    def test_reset(self):
        tracker = Tracker()
        tracker.update([_make_detection(10, 10, 50, 50)])
        tracker.reset()

        assert tracker.get_track_count() == 0
        stats = tracker.get_stats()
        assert stats["active_tracks"] == 0

    def test_stats(self):
        tracker = Tracker()
        tracker.update([_make_detection(10, 10, 50, 50)])
        stats = tracker.get_stats()
        assert "active_tracks" in stats
        assert "total_created" in stats
        assert "frame_count" in stats
        assert stats["frame_count"] == 1


class TestTrackingModule:
    """Tests for the higher-level TrackingModule."""

    def test_direction_estimation(self):
        tm = TrackingModule(min_hits=1)

        # Frame 1: object at (30, 30)
        dets1 = [_make_detection(10, 10, 50, 50)]
        r1 = tm.update(dets1)
        tid = r1[0].track_id

        # Frame 2: object moved right to (60, 30)
        dets2 = [_make_detection(40, 10, 80, 50)]
        tm.update(dets2)

        direction = tm.get_direction(tid)
        assert direction in ("right", "stationary", "unknown")

    def test_track_count(self):
        tm = TrackingModule(min_hits=1)
        dets = [_make_detection(10, 10, 50, 50)]
        tm.update(dets)
        tm.update(dets)
        assert tm.get_track_count() >= 1

    def test_reset(self):
        tm = TrackingModule()
        tm.update([_make_detection(10, 10, 50, 50)])
        tm.reset()
        assert tm.get_track_count() == 0

    def test_stats(self):
        tm = TrackingModule()
        tm.update([_make_detection(10, 10, 50, 50)])
        stats = tm.get_stats()
        assert "active_tracks" in stats
        assert "directions" in stats
