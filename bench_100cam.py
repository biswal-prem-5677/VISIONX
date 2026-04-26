"""
VisionX — 100-Camera Load Simulation
========================================
Simulates 100 cameras sending detection data simultaneously.
Measures throughput, latency, and bottlenecks at every pipeline stage.
"""

import time
import threading
import statistics
import sys
import os
import loguru

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.models import Detection, BoundingBox, FrameResult  # noqa: E402
from decision.engine import DecisionEngine  # noqa: E402
from decision.rules import Rule, RuleCondition, RuleField, RuleOperator, RuleSeverity  # noqa: E402
from decision.governance import GovernanceValidator  # noqa: E402
from events.event_engine import EventEngine  # noqa: E402


# ============================================
# CONFIG
# ============================================
NUM_CAMERAS = 100
FRAMES_PER_CAMERA = 50       # 50 frames per camera
DETECTIONS_PER_FRAME = 5     # 5 objects per frame
TOTAL_FRAMES = NUM_CAMERAS * FRAMES_PER_CAMERA  # 5000 frames total

print("=" * 70)
print("VisionX 100-Camera Load Simulation")
print("=" * 70)
print(f"Cameras:       {NUM_CAMERAS}")
print(f"Frames/cam:    {FRAMES_PER_CAMERA}")
print(f"Objects/frame: {DETECTIONS_PER_FRAME}")
print(f"Total frames:  {TOTAL_FRAMES}")
print(f"Total events:  ~{TOTAL_FRAMES} (worst case)")
print("=" * 70)


# ============================================
# 1. DETECTION THROUGHPUT
# ============================================
print("\n[1/5] Detection Throughput (FrameResult creation)...")

def create_mock_detections(n: int, camera_id: int, frame_id: int) -> list[Detection]:
    """Simulate detector output."""
    classes = ["person", "car", "no_helmet", "bicycle", "truck"]
    return [
        Detection(
            class_id=i % len(classes),
            class_name=classes[i % len(classes)],
            confidence=0.7 + (i % 3) * 0.1,
            bbox=BoundingBox(x1=100.0 + i * 50, y1=100.0, x2=200.0 + i * 50, y2=300.0),
            track_id=camera_id * 100 + i,
        )
        for i in range(n)
    ]

frame_times = []
frames_created = []

start_total = time.perf_counter()
for cam_id in range(NUM_CAMERAS):
    for frame_num in range(FRAMES_PER_CAMERA):
        t0 = time.perf_counter()
        dets = create_mock_detections(DETECTIONS_PER_FRAME, cam_id, frame_num)
        fr = FrameResult(
            frame_id=cam_id * FRAMES_PER_CAMERA + frame_num,
            detections=dets,
            fps=30.0,
            processing_time_ms=12.0,
            source_id=f"camera_{cam_id}",
            metadata={"counts": {"total_objects": len(dets), "person": 2, "car": 1}},
        )
        frames_created.append(fr)
        frame_times.append((time.perf_counter() - t0) * 1000)

detection_total = time.perf_counter() - start_total

print(f"  Total frames created: {len(frames_created)}")
print(f"  Total time:           {detection_total*1000:.1f}ms")
print(f"  Avg per frame:        {statistics.mean(frame_times):.3f}ms")
print(f"  P95 per frame:        {sorted(frame_times)[int(len(frame_times)*0.95)]:.3f}ms")
print(f"  P99 per frame:        {sorted(frame_times)[int(len(frame_times)*0.99)]:.3f}ms")
print(f"  Throughput:           {len(frames_created)/detection_total:.0f} frames/sec")


# ============================================
# 2. DECISION ENGINE THROUGHPUT
# ============================================
print("\n[2/5] Decision Engine (rule evaluation)...")

engine = DecisionEngine()

# Add 10 rules (realistic mix)
rules = [
    Rule(id="crowd", name="Crowd Alert", conditions=[
        RuleCondition(field=RuleField.PERSON_COUNT, operator=RuleOperator.GT, value=10)
    ], actions=["log_event"], severity=RuleSeverity.WARNING, cooldown_seconds=0, priority=3),
    Rule(id="no_helmet", name="No Helmet", conditions=[
        RuleCondition(field=RuleField.DETECTION_CLASS, operator=RuleOperator.CONTAINS, value="no_helmet")
    ], actions=["log_event", "send_email"], severity=RuleSeverity.WARNING, cooldown_seconds=0, priority=2),
    Rule(id="intrusion", name="Zone Intrusion", conditions=[
        RuleCondition(field=RuleField.ZONE_COUNT, operator=RuleOperator.GT, value=0, zone_filter="restricted")
    ], actions=["send_email", "trigger_webhook"], severity=RuleSeverity.EMERGENCY, cooldown_seconds=0, priority=1),
    Rule(id="object_count", name="High Object Count", conditions=[
        RuleCondition(field=RuleField.OBJECT_COUNT, operator=RuleOperator.GT, value=20)
    ], actions=["log_event"], severity=RuleSeverity.INFO, cooldown_seconds=0, priority=5),
    Rule(id="low_conf", name="Low Confidence Alert", conditions=[
        RuleCondition(field=RuleField.CONFIDENCE, operator=RuleOperator.LT, value=0.5)
    ], actions=["log_event"], severity=RuleSeverity.INFO, cooldown_seconds=0, priority=8),
]
for r in rules:
    engine.add_rule(r)

# Suppress loguru for benchmarks
loguru.logger.disable("decision")
loguru.logger.disable("events")
loguru.logger.disable("decision.governance")

decision_times = []
total_triggered = 0

start_decision = time.perf_counter()
for fr in frames_created:
    t0 = time.perf_counter()
    results = engine.evaluate(fr)
    decision_times.append((time.perf_counter() - t0) * 1000)
    total_triggered += len(results)

decision_total = time.perf_counter() - start_decision

print(f"  Rules evaluated:      {len(rules)} rules × {len(frames_created)} frames = {len(rules) * len(frames_created)} evaluations")
print(f"  Total triggered:      {total_triggered}")
print(f"  Total time:           {decision_total*1000:.1f}ms")
print(f"  Avg per frame:        {statistics.mean(decision_times):.3f}ms")
print(f"  P95 per frame:        {sorted(decision_times)[int(len(decision_times)*0.95)]:.3f}ms")
print(f"  P99 per frame:        {sorted(decision_times)[int(len(decision_times)*0.99)]:.3f}ms")
print(f"  Throughput:           {len(frames_created)/decision_total:.0f} evaluations/sec")


# ============================================
# 3. GOVERNANCE THROUGHPUT
# ============================================
print("\n[3/5] Governance Validator...")

governance = GovernanceValidator()

# Re-evaluate to get rule results
engine2 = DecisionEngine()
for r in rules:
    engine2.add_rule(r)
engine2._last_triggered.clear()

# Collect sample results
sample_results = []
for fr in frames_created[:100]:
    res = engine2.evaluate(fr)
    if res:
        sample_results.extend(res)
    engine2._last_triggered.clear()

gov_times = []
total_approved = 0
total_blocked = 0

start_gov = time.perf_counter()
for i in range(0, len(sample_results), 5):
    batch = sample_results[i:i+5]
    t0 = time.perf_counter()
    approved = governance.validate(batch, context={"zone": "", "max_confidence": 0.85})
    gov_times.append((time.perf_counter() - t0) * 1000)
    total_approved += len(approved)
    total_blocked += len(batch) - len(approved)

gov_total = time.perf_counter() - start_gov

print(f"  Rules checked:        {len(sample_results)}")
print(f"  Approved:             {total_approved}")
print(f"  Blocked/Modified:     {total_blocked}")
print(f"  Total time:           {gov_total*1000:.1f}ms")
if gov_times:
    print(f"  Avg per batch(5):     {statistics.mean(gov_times):.3f}ms")
    print(f"  P95 per batch:        {sorted(gov_times)[int(len(gov_times)*0.95)]:.3f}ms")
print(f"  Throughput:           {len(sample_results)/max(gov_total,0.001):.0f} validations/sec")


# ============================================
# 4. EVENT ENGINE THROUGHPUT
# ============================================
print("\n[4/5] Event Engine (dispatch with ThreadPool)...")

event_engine = EventEngine()

# Re-run with fresh engine to get results
engine3 = DecisionEngine()
for r in rules:
    engine3.add_rule(r)

event_times = []
total_events = 0

start_events = time.perf_counter()
for fr in frames_created:
    engine3._last_triggered.clear()
    results = engine3.evaluate(fr)
    if results:
        t0 = time.perf_counter()
        events = event_engine.process_rule_results(results, frame_context={"frame_id": fr.frame_id})
        event_times.append((time.perf_counter() - t0) * 1000)
        total_events += len(events)

event_total = time.perf_counter() - start_events

print(f"  Events created:       {total_events}")
print(f"  Actions dispatched:   ~{total_events * 2} (avg 2 actions/event)")
print(f"  Thread pool workers:  {event_engine._executor._max_workers}")
print(f"  Total time:           {event_total*1000:.1f}ms")
if event_times:
    print(f"  Avg per frame:        {statistics.mean(event_times):.3f}ms")
    print(f"  P95 per frame:        {sorted(event_times)[int(len(event_times)*0.95)]:.3f}ms")
    print(f"  P99 per frame:        {sorted(event_times)[int(len(event_times)*0.99)]:.3f}ms")
print(f"  Throughput:           {total_events/max(event_total,0.001):.0f} events/sec")


# ============================================
# 5. FULL PIPELINE E2E (simulated concurrent cameras)
# ============================================
print("\n[5/5] Full Pipeline E2E (100 concurrent camera threads)...")

e2e_engine = DecisionEngine()
for r in rules:
    e2e_engine.add_rule(r)
e2e_gov = GovernanceValidator()
e2e_event = EventEngine()

thread_times = []
thread_events = []
lock = threading.Lock()

def camera_worker(cam_id: int, num_frames: int):
    """Simulate one camera processing frames."""
    local_times = []
    local_events = 0

    for frame_num in range(num_frames):
        t0 = time.perf_counter()

        # Create detections
        dets = create_mock_detections(DETECTIONS_PER_FRAME, cam_id, frame_num)
        fr = FrameResult(
            frame_id=cam_id * num_frames + frame_num,
            detections=dets, fps=30.0, processing_time_ms=10.0,
            source_id=f"cam_{cam_id}",
            metadata={"counts": {"total_objects": len(dets)}},
        )

        # Decision
        e2e_engine._last_triggered.clear()
        results = e2e_engine.evaluate(fr)

        # Governance
        if results:
            results = e2e_gov.validate(results, context={"zone": "", "max_confidence": 0.85})

        # Events
        if results:
            events = e2e_event.process_rule_results(results)
            local_events += len(events)

        elapsed = (time.perf_counter() - t0) * 1000
        local_times.append(elapsed)

    with lock:
        thread_times.extend(local_times)
        thread_events.append(local_events)

# Launch 100 threads simultaneously
threads = []
e2e_start = time.perf_counter()

for cam_id in range(NUM_CAMERAS):
    t = threading.Thread(target=camera_worker, args=(cam_id, 10), daemon=True)
    threads.append(t)

# Start all at once
for t in threads:
    t.start()

# Wait for completion
for t in threads:
    t.join(timeout=30)

e2e_total = time.perf_counter() - e2e_start

total_e2e_frames = NUM_CAMERAS * 10
total_e2e_events = sum(thread_events)

print(f"  Cameras:              {NUM_CAMERAS} (concurrent threads)")
print(f"  Frames processed:     {total_e2e_frames}")
print(f"  Events generated:     {total_e2e_events}")
print(f"  Total wall time:      {e2e_total*1000:.1f}ms ({e2e_total:.2f}s)")
if thread_times:
    print(f"  Avg frame latency:    {statistics.mean(thread_times):.3f}ms")
    print(f"  P50 frame latency:    {sorted(thread_times)[int(len(thread_times)*0.50)]:.3f}ms")
    print(f"  P95 frame latency:    {sorted(thread_times)[int(len(thread_times)*0.95)]:.3f}ms")
    print(f"  P99 frame latency:    {sorted(thread_times)[int(len(thread_times)*0.99)]:.3f}ms")
    print(f"  Max frame latency:    {max(thread_times):.3f}ms")
print(f"  Throughput:           {total_e2e_frames/e2e_total:.0f} frames/sec")
print(f"  Events/sec:           {total_e2e_events/max(e2e_total, 0.001):.0f}")


# ============================================
# 6. BOTTLENECK ANALYSIS
# ============================================
print(f"\n{'=' * 70}")
print("BOTTLENECK ANALYSIS")
print(f"{'=' * 70}")

stages = {
    "Detection/FrameResult": (statistics.mean(frame_times), detection_total),
    "Decision Engine":       (statistics.mean(decision_times), decision_total),
    "Governance":            (statistics.mean(gov_times) if gov_times else 0, gov_total),
    "Event Engine":          (statistics.mean(event_times) if event_times else 0, event_total),
}

slowest = max(stages.items(), key=lambda x: x[1][0])

print(f"\n  {'Stage':<25} {'Avg/frame':>12} {'Total':>12} {'% of pipeline':>14}")
print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*14}")

total_avg = sum(v[0] for v in stages.values())
for name, (avg_ms, total_s) in stages.items():
    pct = (avg_ms / total_avg * 100) if total_avg > 0 else 0
    marker = " ← BOTTLENECK" if name == slowest[0] else ""
    print(f"  {name:<25} {avg_ms:>9.3f}ms {total_s*1000:>9.1f}ms {pct:>12.1f}%{marker}")

print(f"\n  Full pipeline per frame: {total_avg:.3f}ms")
print(f"  Max theoretical FPS:    {1000/total_avg:.0f} fps (single-threaded)")
print(f"  At 30fps per camera:    supports {int(1000/total_avg/33.3)} cameras (single-thread)")
print(f"  With 100 threads:       {total_e2e_frames/e2e_total:.0f} fps actual")

# UI impact estimate
ws_msgs_per_sec = total_e2e_frames / e2e_total
print(f"\n  WebSocket load:         {ws_msgs_per_sec:.0f} msgs/sec")
if ws_msgs_per_sec > 60:
    print(f"  ⚠️  UI RISK: >{ws_msgs_per_sec:.0f} msgs/sec may cause React re-render lag")
    print("  FIX: Throttle WebSocket → store updates to 10-15fps with requestAnimationFrame")
else:
    print("  ✅ UI safe: <60 msgs/sec")

print(f"\n{'=' * 70}")
print("SIMULATION COMPLETE")
print(f"{'=' * 70}")
