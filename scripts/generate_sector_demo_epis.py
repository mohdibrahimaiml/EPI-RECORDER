#!/usr/bin/env python3
"""
Generate realistic sector demo .epi artifacts with a live LLM (Groq).

Requires:
  GROQ_API_KEY
  pip install langchain-groq langchain-core epi-recorder

Outputs (git-allowable under docs/assets/):
  docs/assets/demo-finance-loan-underwriter.epi
  docs/assets/demo-healthcare-clinical-triage.epi
  docs/assets/demo-insurance-claim-adjudication.epi
  docs/assets/demo-legal-contract-review.epi

Also copies into demo_workflows/ for local demos.

Usage:
  set GROQ_API_KEY=gsk_...
  python scripts/generate_sector_demo_epis.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import zipfile
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "assets"
DEMO_DIR = ROOT / "demo_workflows"


def _require_groq() -> str:
    key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not key:
        print("GROQ_API_KEY is not set.", file=sys.stderr)
        return ""
    return key


def _llm_invoke(api_key: str, system: str, user: str) -> str:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_groq import ChatGroq

    from epi_recorder.adapters.langchain import EpiCallbackHandler
    from epi_recorder.api import get_current_session

    session = get_current_session()
    handler = EpiCallbackHandler(session) if session else None
    llm = ChatGroq(
        model=os.environ.get("EPI_DEMO_GROQ_MODEL", "llama-3.1-8b-instant"),
        api_key=api_key,
        temperature=0.2,
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", system), ("human", "{input}")]
    )
    chain = prompt | llm | StrOutputParser()
    cfg = {"callbacks": [handler]} if handler else {}
    return chain.invoke({"input": user}, config=cfg)


def _tool(epi, name: str, tool_input, output, *, ok: bool = True, error: str | None = None):
    cid = str(uuid4())
    epi.log(
        "tool.call",
        {"tool": name, "input": tool_input, "call_id": cid},
    )
    if ok:
        epi.log(
            "tool.response",
            {"tool": name, "output": output, "ok": True, "call_id": cid},
        )
    else:
        epi.log(
            "tool.response",
            {
                "tool": name,
                "ok": False,
                "error": error or "tool failed",
                "call_id": cid,
            },
        )


def _leak_scan(path: Path) -> list[str]:
    from epi_core.container import EPIContainer
    import tempfile

    inner = Path(tempfile.mkdtemp()) / "inner.zip"
    EPIContainer.extract_inner_payload(path, inner)
    hits: list[str] = []
    with zipfile.ZipFile(inner) as zf:
        for name in zf.namelist():
            data = zf.read(name)
            if b"gsk_" in data or b"GROQ_API_KEY" in data:
                hits.append(name)
    return hits


def _seal_and_check(path: Path) -> None:
    hits = _leak_scan(path)
    if hits:
        raise RuntimeError(f"Secret material found in {path}: {hits}")
    print(f"  sealed {path.name}  size={path.stat().st_size}  CLEAN")


def finance_loan(api_key: str, out: Path) -> None:
    from epi_recorder import record

    with record(
        out,
        goal="Underwrite consumer loan application APP-78421",
        workflow_name="Finance · Loan Underwriter Agent",
        tags=["demo", "finance", "loan", "underwriting"],
        notes="Realistic demo: credit pull, income verify, policy rules, LLM decision.",
    ) as epi:
        epi.log(
            "agent.run.start",
            {
                "agent_name": "LoanUnderwriterAgent",
                "domain": "finance",
                "user_input": "Underwrite personal loan for Jordan Lee, $22,000 @ 36 months",
                "goal": "Approve or deny with defensible evidence trail",
                "risk_class": "credit_decision",
            },
        )
        _tool(
            epi,
            "crm.fetch_application",
            {"application_id": "APP-78421"},
            {
                "applicant": "Jordan Lee",
                "requested_amount_usd": 22000,
                "term_months": 36,
                "stated_income_usd": 78000,
                "employment": "W2 · software engineer · 2.4 years",
                "purpose": "debt consolidation",
            },
        )
        _tool(
            epi,
            "bureau.soft_pull_credit",
            {"applicant_id": "APP-78421", "bureau": "Equifax-soft"},
            {
                "fico": 714,
                "utilization": 0.31,
                "delinquencies_24m": 0,
                "inquiries_6m": 2,
                "open_trades": 7,
            },
        )
        _tool(
            epi,
            "payroll.verify_income",
            {"employer": "Northline Systems", "stated_income_usd": 78000},
            {"verified_income_usd": 76500, "method": "payroll_api", "confidence": 0.91},
        )
        _tool(
            epi,
            "policy.evaluate_credit_box",
            {
                "min_fico": 680,
                "max_dti": 0.42,
                "max_amount_usd": 35000,
            },
            {
                "in_box": True,
                "estimated_dti": 0.29,
                "flags": [],
            },
        )
        decision = _llm_invoke(
            api_key,
            "You are a cautious consumer-loan underwriter. Reply with APPROVE or DENY, "
            "a one-sentence reason, and a risk note. No PII beyond what is given. Be concise.",
            "Applicant Jordan Lee. Requested $22,000 / 36 mo debt consolidation. "
            "FICO 714, utilization 31%, DTI ~29%, verified income $76,500. "
            "In credit box. Decision?",
        )
        epi.log(
            "agent.decision",
            {
                "decision": "APPROVE" if "APPROVE" in decision.upper() else "DENY",
                "rationale": decision,
                "application_id": "APP-78421",
                "policy_version": "credit-box-2026.03",
            },
        )
        epi.log(
            "agent.run.end",
            {"status": "completed", "application_id": "APP-78421"},
        )
    _seal_and_check(out)


def healthcare_triage(api_key: str, out: Path) -> None:
    from epi_recorder import record

    with record(
        out,
        goal="Triage virtual-care intake for adult with chest discomfort",
        workflow_name="Healthcare · Clinical Triage Agent",
        tags=["demo", "healthcare", "triage", "clinical"],
        notes="Demo only — not medical advice. Escalation path logged as evidence.",
    ) as epi:
        epi.log(
            "agent.run.start",
            {
                "agent_name": "ClinicalTriageAgent",
                "domain": "healthcare",
                "user_input": "Adult patient reports intermittent chest pressure for 2 hours",
                "goal": "Route to ED / urgent care / nurse line with documented red flags",
                "disclaimer": "not_a_diagnosis",
            },
        )
        _tool(
            epi,
            "ehr.fetch_intake",
            {"encounter_id": "ENC-90312"},
            {
                "chief_complaint": "intermittent chest pressure × 2h",
                "age": 54,
                "sex": "M",
                "history": ["hypertension", "hyperlipidemia"],
                "meds": ["lisinopril", "atorvastatin"],
            },
        )
        _tool(
            epi,
            "symptom.red_flag_screen",
            {
                "symptoms": ["chest_pressure", "mild_dyspnea_on_exertion"],
                "duration_hours": 2,
            },
            {
                "red_flags": ["possible_acs_symptoms"],
                "severity": "high",
                "recommended_disposition": "ED_now",
            },
        )
        _tool(
            epi,
            "protocol.lookup",
            {"protocol_id": "chest-pain-adult-v4"},
            {
                "name": "Adult chest pain triage",
                "action_if_acs_risk": "Advise emergency care; do not delay for televisit",
            },
        )
        advice = _llm_invoke(
            api_key,
            "You are a clinical triage assistant (not a doctor). Given tools already "
            "flagged high ACS risk, recommend disposition. Be clear, urgent, and "
            "include 'not a diagnosis' disclaimer. 3-5 sentences max.",
            "54M with HTN/HLD, 2h intermittent chest pressure, mild DOE. "
            "Red-flag screen: possible ACS, severity high, disposition ED_now. "
            "What should the virtual-care agent tell the patient?",
        )
        epi.log(
            "agent.decision",
            {
                "disposition": "ED_now",
                "message_to_patient": advice,
                "protocol_id": "chest-pain-adult-v4",
                "human_escalation_required": True,
            },
        )
        epi.log(
            "agent.approval.request",
            {
                "action": "release_triage_message",
                "reason": "High-risk disposition requires nurse confirmation before send",
            },
        )
        epi.log(
            "agent.approval.response",
            {
                "action": "release_triage_message",
                "decision": "approved",
                "reviewer": "rn.patel@clinic.example",
            },
        )
        epi.log("agent.run.end", {"status": "completed", "encounter_id": "ENC-90312"})
    _seal_and_check(out)


def insurance_claim(api_key: str, out: Path) -> None:
    from epi_recorder import record

    with record(
        out,
        goal="Adjudicate water-damage claim CLM-48219",
        workflow_name="Insurance · Claim Adjudication Agent",
        tags=["demo", "insurance", "claims", "adjudication"],
        notes="Deterministic policy exclusion path with LLM narrative for adjuster.",
    ) as epi:
        epi.log(
            "agent.run.start",
            {
                "agent_name": "ClaimAdjudicationAgent",
                "domain": "insurance",
                "user_input": "Review claim CLM-48219 water damage kitchen",
                "goal": "Pay, deny, or request more info with policy-backed rationale",
            },
        )
        _tool(
            epi,
            "claims.load",
            {"claim_id": "CLM-48219"},
            {
                "policy_id": "HO-3-99210",
                "loss_type": "water",
                "reported_cause": "gradual_leak_under_sink",
                "claimed_amount_usd": 18400,
                "date_of_loss": "2026-03-02",
            },
        )
        _tool(
            epi,
            "policy.coverage_lookup",
            {"policy_id": "HO-3-99210", "peril": "water"},
            {
                "form": "HO-3",
                "sudden_and_accidental_water": True,
                "gradual_leak_exclusion": True,
                "mold_sublimit_usd": 5000,
            },
        )
        _tool(
            epi,
            "fnol.photos_analyze",
            {"claim_id": "CLM-48219", "photos": 6},
            {
                "findings": ["cabinet_staining", "soft_flooring", "no_burst_pipe_visible"],
                "likely_onset": "gradual",
            },
        )
        narrative = _llm_invoke(
            api_key,
            "You are an insurance claims assistant. Policy tools already indicate "
            "gradual leak exclusion applies. Draft a concise adjuster recommendation: "
            "DENY or PAY or RFI, with 2-4 sentences citing the exclusion. Professional tone.",
            "Claim CLM-48219 HO-3. Reported gradual leak under sink. "
            "Photos suggest gradual onset, no burst pipe. Claimed $18,400. "
            "Policy: gradual_leak_exclusion=true. Recommendation?",
        )
        epi.log(
            "agent.decision",
            {
                "recommendation": "DENY",
                "llm_narrative": narrative,
                "exclusion": "gradual_leak",
                "claim_id": "CLM-48219",
            },
        )
        epi.log(
            "agent.approval.request",
            {
                "action": "issue_denial_letter",
                "claim_id": "CLM-48219",
                "amount_usd": 18400,
            },
        )
        epi.log(
            "agent.approval.response",
            {
                "action": "issue_denial_letter",
                "decision": "approved",
                "reviewer": "claims.manager@carrier.example",
            },
        )
        epi.log("agent.run.end", {"status": "completed", "claim_id": "CLM-48219"})
    _seal_and_check(out)


def legal_contract(api_key: str, out: Path) -> None:
    from epi_recorder import record

    with record(
        out,
        goal="Review vendor MSA redlines for risk before signature",
        workflow_name="Legal · Contract Review Agent",
        tags=["demo", "legal", "contract", "msa"],
        notes="Demo contract review — not legal advice.",
    ) as epi:
        epi.log(
            "agent.run.start",
            {
                "agent_name": "ContractReviewAgent",
                "domain": "legal",
                "user_input": "Review MSA-2026-441 vendor redlines vs playbook",
                "goal": "Flag material risks and propose negotiation positions",
                "disclaimer": "not_legal_advice",
            },
        )
        _tool(
            epi,
            "dms.fetch_agreement",
            {"doc_id": "MSA-2026-441"},
            {
                "title": "Master Services Agreement — CloudOps Vendor",
                "counterparty": "Nimbus Ops LLC",
                "governing_law": "Delaware",
                "pages": 28,
            },
        )
        _tool(
            epi,
            "playbook.load",
            {"playbook_id": "saas-vendor-v7"},
            {
                "must_haves": [
                    "liability_cap >= 12mo fees",
                    "data_processing_addendum",
                    "termination_for_convenience_30d",
                ],
                "red_lines": [
                    "unlimited_indemnity_for_IP",
                    "customer_unlimited_liability",
                    "auto_renew_without_notice",
                ],
            },
        )
        _tool(
            epi,
            "clause.extract_risks",
            {"doc_id": "MSA-2026-441"},
            {
                "findings": [
                    {
                        "clause": "8.2 Limitation of Liability",
                        "issue": "cap set at 3 months fees",
                        "severity": "high",
                    },
                    {
                        "clause": "11 Auto-Renewal",
                        "issue": "renews annually without notice window",
                        "severity": "medium",
                    },
                    {
                        "clause": "14.1 Indemnity",
                        "issue": "customer IP indemnity is mutual unlimited",
                        "severity": "high",
                    },
                ]
            },
        )
        memo = _llm_invoke(
            api_key,
            "You are a commercial contracts assistant (not a lawyer). Summarize material "
            "risks vs playbook and give negotiation asks. Use short bullets. Include "
            "'not legal advice' once.",
            "MSA-2026-441 vs saas-vendor-v7. Findings: liability cap 3mo fees (playbook "
            "wants 12mo); auto-renew without notice; mutual unlimited IP indemnity. "
            "Draft counsel-ready memo bullets.",
        )
        epi.log(
            "agent.decision",
            {
                "recommendation": "negotiate_before_sign",
                "memo": memo,
                "blocking_issues": 2,
                "doc_id": "MSA-2026-441",
            },
        )
        epi.log(
            "agent.approval.request",
            {
                "action": "send_redline_package",
                "doc_id": "MSA-2026-441",
                "to_role": "general_counsel",
            },
        )
        epi.log(
            "agent.approval.response",
            {
                "action": "send_redline_package",
                "decision": "approved",
                "reviewer": "gc.desk@company.example",
            },
        )
        epi.log("agent.run.end", {"status": "completed", "doc_id": "MSA-2026-441"})
    _seal_and_check(out)


def main() -> int:
    api_key = _require_groq()
    if not api_key:
        return 2

    try:
        import langchain_groq  # noqa: F401
    except ImportError:
        print("Install: pip install langchain-groq langchain-core", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    jobs = [
        ("demo-finance-loan-underwriter.epi", finance_loan),
        ("demo-healthcare-clinical-triage.epi", healthcare_triage),
        ("demo-insurance-claim-adjudication.epi", insurance_claim),
        ("demo-legal-contract-review.epi", legal_contract),
    ]

    results: list[Path] = []
    for name, fn in jobs:
        target = OUT_DIR / name
        print(f"\n=== {name} ===")
        # record() may rewrite under epi-recordings/; force absolute under docs/assets
        abs_target = target.resolve()
        fn(api_key, abs_target)
        # If sealed elsewhere, copy
        alt = ROOT / "epi-recordings" / name
        if not abs_target.exists() and alt.exists():
            shutil.copy2(alt, abs_target)
        if abs_target.exists():
            shutil.copy2(abs_target, DEMO_DIR / name)
            results.append(abs_target)
        else:
            # Find newest matching under epi-recordings
            matches = list((ROOT / "epi-recordings").glob(f"*{name}"))
            if matches:
                shutil.copy2(matches[0], abs_target)
                shutil.copy2(matches[0], DEMO_DIR / name)
                results.append(abs_target)
            else:
                print(f"  WARN: missing output for {name}", file=sys.stderr)

    print("\n=== VERIFY ALL ===")
    from epi_core.container import EPIContainer

    for path in results:
        ok, mismatches = EPIContainer.verify_integrity(path)
        steps = EPIContainer.read_steps(path)
        kinds = {}
        for s in steps:
            k = s.get("kind") or "?"
            kinds[k] = kinds.get(k, 0) + 1
        print(f"{path.name}: integrity={ok} steps={len(steps)} kinds={kinds}")

    print("\nDone. Artifacts:")
    for p in results:
        print(" ", p)
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
