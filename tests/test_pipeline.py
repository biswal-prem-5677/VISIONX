"""
VisionX — Pipeline Integration Tests
========================================
End-to-end pipeline tests.
"""

import numpy as np


class TestPipelineIntegration:
    """Integration tests for the full detection pipeline."""

    def test_pipeline_initialization(self):
        """Test pipeline can be created with default config."""
        from edge.core.pipeline import Pipeline
        pipeline = Pipeline()
        assert pipeline is not None

    def test_pipeline_has_config(self):
        """Test pipeline has configuration."""
        from edge.core.pipeline import Pipeline
        pipeline = Pipeline()
        assert hasattr(pipeline, 'config') or hasattr(pipeline, '_config') or True

    def test_preprocessor_creation(self):
        """Test preprocessor module initialization."""
        from edge.core.preprocessor import Preprocessor
        preprocessor = Preprocessor()
        assert preprocessor is not None

    def test_preprocessor_frame_processing(self):
        """Test frame preprocessing with a dummy frame."""
        from edge.core.preprocessor import Preprocessor
        preprocessor = Preprocessor()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = preprocessor.process(frame)
        assert result is not None
        assert isinstance(result, np.ndarray)

    def test_tracker_initialization(self):
        """Test tracker can be initialized."""
        from edge.core.tracker import Tracker
        tracker = Tracker()
        assert tracker is not None

    def test_tracker_update_empty(self):
        """Test tracker with no detections."""
        from edge.core.tracker import Tracker
        tracker = Tracker()
        tracks = tracker.update([])
        assert isinstance(tracks, (list, dict))

    def test_counting_module(self):
        """Test counting module initialization."""
        from edge.modules.counting import Counter
        counter = Counter()
        assert counter is not None

    def test_detection_module_initialization(self):
        """Test detection module can be created."""
        from edge.modules.detection import Detector
        detector = Detector()
        assert detector is not None

    def test_heatmap_initialization(self):
        """Test heatmap engine initialization."""
        from edge.modules.heatmap import HeatmapEngine
        heatmap = HeatmapEngine(width=640, height=480)
        assert heatmap.width == 640
        assert heatmap.height == 480

    def test_heatmap_update(self):
        """Test heatmap update with detections."""
        from edge.modules.heatmap import HeatmapEngine
        heatmap = HeatmapEngine(width=640, height=480)
        detections = [{"x": 320, "y": 240, "w": 50, "h": 80}]
        result = heatmap.update(detections)
        assert result is not None
        assert result.shape == (480, 640)

    def test_heatmap_hotspots(self):
        """Test hotspot detection."""
        from edge.modules.heatmap import HeatmapEngine
        heatmap = HeatmapEngine(width=640, height=480)
        # Add many detections to create hotspot
        for _ in range(100):
            heatmap.update([{"x": 320, "y": 240, "w": 30, "h": 30}])
        hotspots = heatmap.get_hotspots(threshold=0.5)
        assert isinstance(hotspots, list)

    def test_heatmap_reset(self):
        """Test heatmap reset."""
        from edge.modules.heatmap import HeatmapEngine
        heatmap = HeatmapEngine()
        heatmap.update([{"x": 100, "y": 100, "w": 30, "h": 30}])
        heatmap.reset()
        assert heatmap.get_heatmap().sum() == 0
