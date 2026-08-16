"""Minimal agent-style run that seals a real .epi for the site demo."""
from pathlib import Path
from epi_recorder import record

out = Path("website/assets/demo/demo_refund_site.epi")
with record(str(out), workflow_name="site_demo_refund") as session:
    session.log("agent.plan", goal="Refund order ORD-9001 if eligible")
    session.log("tool.lookup", tool="orders.get", order_id="ORD-9001", amount_usd=89.0)
    session.log("policy.check", rule="refunds_under_100_auto", result="ALLOW")
    session.log("agent.decision", decision="APPROVE_REFUND", amount_usd=89.0, order_id="ORD-9001")
print("WROTE", out, "bytes", out.stat().st_size if out.exists() else 0)
