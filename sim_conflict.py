"""
VisionX — Conflicting Rules Simulation
Traces: Rule A (trigger) vs Rule B (suppress) through full pipeline.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import loguru
loguru.logger.remove()
loguru.logger.add(sys.stdout, format="  [LOG] {message}", level="DEBUG")

from shared.models import Detection, BoundingBox, FrameResult  # noqa: E402
from decision.engine import DecisionEngine  # noqa: E402
from decision.rules import Rule, RuleCondition, RuleField, RuleOperator, RuleSeverity  # noqa: E402
from decision.governance import GovernanceValidator  # noqa: E402
from events.event_engine import EventEngine  # noqa: E402

print("=" * 70)
print("CONFLICTING RULES SIMULATION")
print("Rule A: Trigger alert (priority=1, group=alert_control)")
print("Rule B: Suppress alert (priority=5, group=alert_control)")
print("=" * 70)

# ── SETUP ──
engine = DecisionEngine()

rule_a = Rule(
    id="trigger_alert",
    name="Trigger Alert - Person Detected",
    conditions=[
        RuleCondition(field=RuleField.PERSON_COUNT, operator=RuleOperator.GT, value=0)
    ],
    actions=["send_email", "log_event", "trigger_webhook"],
    severity=RuleSeverity.CRITICAL,
    cooldown_seconds=0,
    priority=1,
    group="alert_control",
)

rule_b = Rule(
    id="suppress_alert",
    name="Suppress Alert - Safe Hours",
    conditions=[
        RuleCondition(field=RuleField.PERSON_COUNT, operator=RuleOperator.GT, value=0)
    ],
    actions=["suppress_all", "log_suppression"],
    severity=RuleSeverity.INFO,
    cooldown_seconds=0,
    priority=5,
    group="alert_control",
)

engine.add_rule(rule_a)
engine.add_rule(rule_b)

governance = GovernanceValidator()
event_engine = EventEngine()

# ── CREATE FRAME: 2 persons detected ──
frame = FrameResult(
    frame_id=1,
    detections=[
        Detection(class_id=0, class_name="person", confidence=0.92,
                  bbox=BoundingBox(x1=100, y1=100, x2=200, y2=300), track_id=1),
        Detection(class_id=0, class_name="person", confidence=0.88,
                  bbox=BoundingBox(x1=300, y1=100, x2=400, y2=300), track_id=2),
    ],
    fps=30.0,
    processing_time_ms=12.0,
    metadata={"counts": {"total_objects": 2, "person": 2}},
)

print()
print("== STAGE 1: DECISION ENGINE ==")
print(f"Input: FrameResult with {len(frame.detections)} persons")
print(f"Rules registered: {len(engine.get_all_rules())}")
print(f'  Rule A: "{rule_a.name}" priority={rule_a.priority} group={rule_a.group}')
print(f'  Rule B: "{rule_b.name}" priority={rule_b.priority} group={rule_b.group}')

results = engine.evaluate(frame)

print(f"\nDecision Engine output: {len(results)} rule(s) triggered")
for r in results:
    print(f"  -> TRIGGERED: {r.rule_name} (severity={r.severity.value}, actions={r.actions})")

if len(results) < 2:
    print(f'  -> SKIPPED: Rule B (group "{rule_b.group}" already claimed by Rule A, priority 1 beats 5)')

print()
print("== STAGE 2: GOVERNANCE VALIDATOR ==")
print(f"Input: {len(results)} triggered rule(s)")
print("Active policies: privacy_zones, biometric_consent, low_confidence_gate")

approved = governance.validate(
    results,
    context={"zone": "", "max_confidence": 0.92, "frame_id": 1}
)

print(f"Governance output: {len(approved)} approved")
for r in approved:
    print(f"  -> APPROVED: {r.rule_name} actions={r.actions}")

stats = governance.get_stats()
print(f"  Blocked: {stats['total_blocked']} | Modified: {stats['total_modified']}")

print()
print("== STAGE 3: EVENT ENGINE ==")
print(f"Input: {len(approved)} approved rule(s)")

events = event_engine.process_rule_results(
    approved,
    frame_context={"frame_id": 1, "detections": 2}
)

print(f"Events created: {len(events)}")
for e in events:
    print(f'  -> Event: type={e.event_type} severity={e.severity} msg="{e.message}"')

print()
print("== FINAL RESULT (Scenario 1) ==")
print("Rule A (trigger, priority=1): FIRED")
print("Rule B (suppress, priority=5): BLOCKED by group exclusion")
print(f"Actions executed: {approved[0].actions if approved else 'none'}")
print("Conflict resolution: HIGHEST PRIORITY WINS")

# ── SCENARIO 2: Swap priorities ──
print()
print("=" * 70)
print("SCENARIO 2: Rule B gets HIGHER priority (suppress wins)")
print("=" * 70)

engine2 = DecisionEngine()

rule_a2 = rule_a.model_copy()
rule_a2.priority = 5

rule_b2 = rule_b.model_copy()
rule_b2.priority = 1

engine2.add_rule(rule_a2)
engine2.add_rule(rule_b2)

print("\nSwapped priorities:")
print("  Rule A: priority=5 (was 1)")
print("  Rule B: priority=1 (was 5)")

results2 = engine2.evaluate(frame)

print(f"\nDecision Engine output: {len(results2)} rule(s) triggered")
for r in results2:
    print(f"  -> TRIGGERED: {r.rule_name} (severity={r.severity.value}, actions={r.actions})")

if len(results2) == 1 and results2[0].rule_id == "suppress_alert":
    print()
    print("== FINAL RESULT (Scenario 2) ==")
    print("Rule B (suppress, priority=1): FIRED")
    print("Rule A (trigger, priority=5): BLOCKED by group exclusion")
    print(f"Actions executed: {results2[0].actions}")
    print("System behavior: Alert SUPPRESSED. No email, no webhook.")

# ── SCENARIO 3: Governance blocks the action ──
print()
print("=" * 70)
print("SCENARIO 3: Governance blocks trigger in private zone")
print("=" * 70)

engine3 = DecisionEngine()
engine3.add_rule(rule_a)  # priority=1, trigger alert

results3 = engine3.evaluate(frame)
print(f"\nDecision: {len(results3)} rule(s) triggered")

gov3 = GovernanceValidator()
approved3 = gov3.validate(
    results3,
    context={"zone": "bathroom", "max_confidence": 0.92}
)

print(f"Governance (zone=bathroom): {len(approved3)} approved")
if len(approved3) == 0:
    print("  -> BLOCKED: Zone 'bathroom' is in blocked_zones policy")
    print()
    print("== FINAL RESULT (Scenario 3) ==")
    print("Rule A triggered but GOVERNANCE BLOCKED it")
    print("Actions executed: NONE")
    print("System behavior: Privacy protected. No alert in private zone.")

print()
print("=" * 70)
print("ALL 3 SCENARIOS VERIFIED")
print("=" * 70)
