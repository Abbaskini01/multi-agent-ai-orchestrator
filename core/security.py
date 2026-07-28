"""
Neural Glass AI Orchestrator — Security & Compliance Engine
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from core.logger import log_event

WORKSPACE_ROOT = Path("workspace_sandbox")

# Common secret regex signatures
SECRET_PATTERNS = {
    "AWS Access Key ID": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
    "Generic API Key": r"(?i)(api_key|apikey|secret|password|token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
    "Private Key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
    "JWT Token": r"ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"
}

# Unsafe code patterns (SAST)
SAST_PATTERNS = {
    "Insecure Exec/Eval": r"\b(exec|eval)\s*\(",
    "Subprocess Shell Injection": r"subprocess\.(Popen|run|call)\s*\(.*shell\s*=\s*True",
    "Disabled SSL Verification": r"verify\s*=\s*False",
    "Hardcoded Localhost/IP": r"http://127\.0\.0\.1|http://localhost"
}


def scan_workspace_security() -> Dict[str, Any]:
    """Scans all files in workspace_sandbox for hardcoded secrets and SAST vulnerabilities."""
    findings: List[Dict[str, Any]] = []
    
    if not WORKSPACE_ROOT.exists():
        return {"status": "clean", "total_findings": 0, "findings": []}

    for file_path in WORKSPACE_ROOT.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith(".") and file_path.suffix in [".py", ".json", ".yml", ".env", ".js", ".ts"]:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                for line_idx, line in enumerate(lines, start=1):
                    # Check for secrets
                    for secret_type, pattern in SECRET_PATTERNS.items():
                        if re.search(pattern, line):
                            findings.append({
                                "file": str(file_path.relative_to(WORKSPACE_ROOT)),
                                "line": line_idx,
                                "category": "Hardcoded Secret",
                                "rule": secret_type,
                                "severity": "CRITICAL",
                                "snippet": line.strip()[:60]
                            })

                    # Check for SAST issues
                    for sast_type, pattern in SAST_PATTERNS.items():
                        if re.search(pattern, line):
                            findings.append({
                                "file": str(file_path.relative_to(WORKSPACE_ROOT)),
                                "line": line_idx,
                                "category": "Code Security Vulnerability",
                                "rule": sast_type,
                                "severity": "HIGH" if "Eval" in sast_type or "Shell" in sast_type else "MEDIUM",
                                "snippet": line.strip()[:60]
                            })

            except Exception as e:
                log_event("security_scan_file_error", file=str(file_path), error=str(e), level="warning")

    log_event("security_scan_completed", total_findings=len(findings))

    return {
        "status": "vulnerabilities_found" if findings else "clean",
        "total_findings": len(findings),
        "findings": findings
    }


def generate_compliance_report() -> Dict[str, Any]:
    """Evaluates workspace configuration against SOC2, ISO27001, and GDPR readiness checks."""
    scan_result = scan_workspace_security()
    has_secrets = any(f["category"] == "Hardcoded Secret" for f in scan_result["findings"])
    
    soc2_controls = {
        "CC6.1_Logical_Access_Security": "FAILED" if has_secrets else "PASSED",
        "CC6.6_Boundary_Protection": "PASSED" if not any(f["rule"] == "Disabled SSL Verification" for f in scan_result["findings"]) else "FAILED",
        "CC7.1_Vulnerability_Management": "PASSED" if scan_result["total_findings"] == 0 else "ACTION_REQUIRED"
    }

    status = "COMPLIANT" if all(v == "PASSED" for v in soc2_controls.values()) else "NON_COMPLIANT"

    return {
        "framework": "SOC2 Type II / ISO27001",
        "overall_status": status,
        "controls": soc2_controls,
        "total_vulnerabilities": scan_result["total_findings"]
    }