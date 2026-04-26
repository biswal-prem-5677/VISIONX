"""
VisionX — Detection Unit Tests
=================================
Tests for the YOLO detection module using mock/sample data.
"""


from shared.models import BoundingBox, Detection


class TestBoundingBox:
    """Tests for the BoundingBox model."""

    def test_properties(self):
        bbox = BoundingBox(x1=10, y1=20, x2=110, y2=120)
        assert bbox.width == 100
        assert bbox.height == 100
        assert bbox.center == (60.0, 70.0)
        assert bbox.area == 10000

    def test_zero_size(self):
        bbox = BoundingBox(x1=50, y1=50, x2=50, y2=50)
        assert bbox.width == 0
        assert bbox.height == 0
        assert bbox.area == 0


class TestDetection:
    """Tests for the Detection model."""

    def test_creation(self):
        det = Detection(
            class_id=0,
            class_name="person",
            confidence=0.85,
            bbox=BoundingBox(x1=10, y1=20, x2=50, y2=80),
        )
        assert det.class_name == "person"
        assert det.confidence == 0.85
        assert det.track_id is None

    def test_with_track_id(self):
        det = Detection(
            class_id=0,
            class_name="person",
            confidence=0.9,
            bbox=BoundingBox(x1=0, y1=0, x2=100, y2=100),
            track_id=5,
        )
        assert det.track_id == 5

    def test_metadata(self):
        det = Detection(
            class_id=2,
            class_name="car",
            confidence=0.75,
            bbox=BoundingBox(x1=0, y1=0, x2=50, y2=50),
            metadata={"speed": 45.2},
        )
        assert det.metadata["speed"] == 45.2


class TestDetectorStructure:
    """Tests for Detector class structure (without loading a model)."""

    def test_import(self):
        from edge.modules.detection import Detector
        assert Detector is not None

    def test_init_defaults(self):
        from edge.modules.detection import Detector
        det = Detector()
        assert det.model_path == "yolov8n.pt"
        assert det.confidence == 0.5
        assert det.is_loaded is False

    def test_update_confidence(self):
        from edge.modules.detection import Detector
        det = Detector()
        det.update_confidence(0.8)
        assert det.confidence == 0.8

    def test_update_confidence_clamp(self):
        from edge.modules.detection import Detector
        det = Detector()
        det.update_confidence(1.5)
        assert det.confidence == 1.0
        det.update_confidence(-0.5)
        assert det.confidence == 0.0

    def test_update_target_classes(self):
        from edge.modules.detection import Detector
        det = Detector()
        det.update_target_classes(["person", "car"])
        assert det.target_classes == ["person", "car"]

    def test_stats(self):
        from edge.modules.detection import Detector
        det = Detector()
        stats = det.get_stats()
        assert stats["model"] == "yolov8n.pt"
        assert stats["is_loaded"] is False
        assert stats["total_inferences"] == 0
        assert stats["avg_inference_ms"] == 0.0
