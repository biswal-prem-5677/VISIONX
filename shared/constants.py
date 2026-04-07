"""
VisionX — System-Wide Constants
================================
Central configuration values used across edge, cloud, and platform layers.
"""

# ============================================
# Application Identity
# ============================================
APP_NAME = "VisionX"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Distributed AI Vision Platform — Detect. Understand. Decide. Act."

# ============================================
# Performance Modes
# ============================================
class PerformanceMode:
    LITE = "lite"           # Mobile, Raspberry Pi
    BALANCED = "balanced"   # Laptop, Desktop
    MAX = "max"             # Cloud GPU, Jetson AGX

PERFORMANCE_CONFIGS = {
    PerformanceMode.LITE: {
        "input_size": 320,
        "skip_frames": 2,
        "precision": "INT8",
        "batch_size": 1,
        "max_fps": 15,
    },
    PerformanceMode.BALANCED: {
        "input_size": 640,
        "skip_frames": 0,
        "precision": "FP16",
        "batch_size": 1,
        "max_fps": 30,
    },
    PerformanceMode.MAX: {
        "input_size": 1280,
        "skip_frames": 0,
        "precision": "FP32",
        "batch_size": 4,
        "max_fps": 60,
    },
}

# ============================================
# Detection Defaults
# ============================================
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
DEFAULT_NMS_THRESHOLD = 0.45
DEFAULT_MODEL = "yolov8n.pt"

# COCO class names (80 classes)
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep",
    "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
    "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
    "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
    "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush",
]

# ============================================
# Tracking Defaults
# ============================================
TRACKER_MAX_AGE = 30          # Frames before track is deleted
TRACKER_MIN_HITS = 3          # Minimum detections before track is confirmed
TRACKER_IOU_THRESHOLD = 0.3   # Minimum IoU for matching

# ============================================
# Camera Source Types
# ============================================
class CameraSource:
    WEBCAM = "webcam"
    RTSP = "rtsp"
    IP_CAMERA = "ip_camera"
    VIDEO_FILE = "video_file"
    IMAGE_FILE = "image_file"

# ============================================
# Event Types
# ============================================
class EventType:
    ALERT = "alert"
    NOTIFICATION = "notification"
    AUTOMATION = "automation"
    API_CALL = "api_call"
    HARDWARE = "hardware"

# ============================================
# Event Severity Levels
# ============================================
class Severity:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# ============================================
# User Roles
# ============================================
class UserRole:
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    API_ONLY = "api_only"

# ============================================
# Subscription Plans
# ============================================
class Plan:
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

PLAN_LIMITS = {
    Plan.FREE: {
        "max_cameras": 1,
        "max_events_per_day": 100,
        "api_rate_limit_per_hour": 100,
        "features": ["detection", "counting"],
    },
    Plan.PRO: {
        "max_cameras": 5,
        "max_events_per_day": 10000,
        "api_rate_limit_per_hour": 1000,
        "features": ["detection", "counting", "tracking", "ocr", "analytics"],
    },
    Plan.ENTERPRISE: {
        "max_cameras": -1,  # unlimited
        "max_events_per_day": -1,
        "api_rate_limit_per_hour": -1,
        "features": [
            "detection", "counting", "tracking", "ocr", "face",
            "pose", "segmentation", "analytics", "api", "automation",
        ],
    },
}

# ============================================
# Notification Channels
# ============================================
class NotificationChannel:
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"

# ============================================
# Visualization Colors (BGR for OpenCV)
# ============================================
COLORS = {
    "person": (255, 128, 0),
    "car": (0, 255, 128),
    "truck": (0, 128, 255),
    "bicycle": (255, 255, 0),
    "motorcycle": (255, 0, 255),
    "default": (0, 255, 0),
}

# ============================================
# System Limits
# ============================================
MAX_FRAME_QUEUE_SIZE = 30
MAX_RESULT_QUEUE_SIZE = 30
HEARTBEAT_INTERVAL_SECONDS = 10
STATE_SNAPSHOT_INTERVAL_SECONDS = 5
CRASH_REPORT_MAX_BREADCRUMBS = 50
OFFLINE_BUFFER_MAX_EVENTS = 10000
