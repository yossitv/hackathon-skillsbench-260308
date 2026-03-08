# /// script
# dependencies = ["anthropic", "daytona-sdk"]
# ///
"""
Safety Check — Verify skill safety via static analysis (Claude) + dynamic sandbox (Daytona)

Two-phase approach:
  Phase 1: Static analysis with Claude API (dangerous patterns in SKILL.md + scripts/)
  Phase 2: Dynamic execution in Daytona sandbox (network blocked, observe behavior)

Usage:
    uv run safety_check.py <staging-skill-path>

Returns a safety report dict with:
  - dangerous_patterns: list of concerning code patterns found
  - network_attempts: list of blocked network connections detected
  - files_changed: list of files created/modified during execution
  - sandbox_stdout/stderr: raw output from sandbox execution
  - recommendation: "safe" | "review" | "dangerous"
"""

import argparse
import json
import os
import sys
from pathlib import Path

FACTORY_ROOT = Path(__file__).resolve().parent.parent


def read_skill_contents(skill_path: Path) -> dict[str, str]:
    """Read all text files in a skill directory."""
    contents = {}
    for f in skill_path.rglob("*"):
        if f.is_file() and f.suffix in (".md", ".py", ".sh", ".js", ".ts", ".yaml", ".yml", ".toml", ".json"):
            try:
                contents[str(f.relative_to(skill_path))] = f.read_text()
            except UnicodeDecodeError:
                contents[str(f.relative_to(skill_path))] = "<binary file>"
    return contents


# ── Phase 1: Static Analysis with Claude ────────────────────────────────

def static_analysis(skill_path: Path) -> dict:
    """Use Claude API to analyze skill contents for dangerous patterns."""
    import anthropic

    contents = read_skill_contents(skill_path)
    if not contents:
        return {"dangerous_patterns": [], "recommendation": "safe", "details": "Empty skill."}

    files_text = ""
    for name, content in contents.items():
        files_text += f"\n--- {name} ---\n{content}\n"

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""Analyze this agent skill for security risks. Return JSON only.

Skill contents:
{files_text}

Check for:
1. Shell injection (eval, exec, subprocess with user input)
2. File system attacks (rm -rf, writing outside workspace)
3. Network exfiltration (curl/wget to unknown URLs, sending data out)
4. Credential theft (reading .env, ~/.ssh, /etc/passwd)
5. Supply chain risks (pip install from untrusted sources, curl | bash)
6. Obfuscated code (base64 encoded commands, hex strings)

Return ONLY valid JSON:
{{
  "dangerous_patterns": ["description of each pattern found"],
  "network_urls": ["any URLs/domains the scripts contact"],
  "recommendation": "safe" | "review" | "dangerous",
  "summary": "one-line summary"
}}"""
        }]
    )

    text = message.content[0].text
    # Extract JSON from response
    try:
        # Handle markdown code blocks
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "dangerous_patterns": [],
            "recommendation": "review",
            "summary": f"Could not parse analysis: {text[:200]}"
        }


# ── Phase 2: Dynamic Sandbox Execution with Daytona ────────────────────

def _install_iptables(sandbox) -> bool:
    """Install iptables in sandbox, working around broken repos."""
    # Check if already available
    check = sandbox.process.exec("which iptables 2>/dev/null || true")
    if check.result.strip():
        return True

    # Remove problematic third-party repos that block apt-get
    sandbox.process.exec(
        "sudo rm -f /etc/apt/sources.list.d/yarn.list "
        "/etc/apt/sources.list.d/nodesource.list 2>/dev/null || true"
    )
    # Install iptables
    result = sandbox.process.exec(
        "sudo apt-get update -qq 2>/dev/null && "
        "sudo apt-get install -y -qq iptables 2>/dev/null"
    )
    # Verify
    verify = sandbox.process.exec("which iptables 2>/dev/null || true")
    return bool(verify.result.strip())


def _block_network(sandbox) -> str:
    """Block outbound network. Returns method used or empty string on failure."""
    # Try iptables first — must allow ESTABLISHED so sandbox control plane survives
    if _install_iptables(sandbox):
        try:
            # Order matters: allow rules first, then set default DROP
            # 1. Allow loopback
            sandbox.process.exec("sudo iptables -A OUTPUT -o lo -j ACCEPT")
            # 2. Allow already-established connections (control plane)
            sandbox.process.exec(
                "sudo iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT"
            )
            # 3. Drop all NEW outbound connections
            sandbox.process.exec(
                "sudo iptables -A OUTPUT -m state --state NEW -j DROP"
            )
            return "iptables"
        except Exception:
            pass

    # Fallback: DNS-level blocking (break name resolution for new connections)
    try:
        sandbox.process.exec(
            "sudo cp /etc/resolv.conf /etc/resolv.conf.bak && "
            "sudo bash -c 'echo nameserver 127.0.0.1 > /etc/resolv.conf'"
        )
        return "dns-block"
    except Exception:
        pass

    return ""


def _detect_network_attempts(sandbox, method: str) -> list[str]:
    """Detect blocked outbound connections after script execution."""
    attempts = []

    if method == "iptables":
        # Check iptables counters for dropped packets
        stats = sandbox.process.exec("sudo iptables -L OUTPUT -v -n 2>/dev/null || true")
        if stats.result.strip():
            for line in stats.result.strip().splitlines():
                if "DROP" in line and "pkts" not in line:
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] != "0":
                        attempts.append(f"Dropped {parts[0]} packets: {line.strip()}")

        # Also check kernel log
        dmesg = sandbox.process.exec(
            "dmesg 2>/dev/null | grep -i 'dropped\\|reject\\|blocked' | tail -20 || true"
        )
        if dmesg.result.strip():
            attempts.extend(dmesg.result.strip().splitlines())

    # Universal: try a test connection to verify blocking works
    test = sandbox.process.exec(
        "timeout 3 curl -s -o /dev/null -w '%{http_code}' https://httpbin.org/get 2>&1 || echo 'BLOCKED'"
    )
    if "BLOCKED" in test.result or test.result.strip() == "000":
        attempts.append("VERIFIED: outbound HTTPS blocked")
    elif test.result.strip():
        attempts.append(f"WARNING: outbound may not be blocked (curl returned: {test.result.strip()[:100]})")

    return attempts


def dynamic_analysis(skill_path: Path) -> dict:
    """Run scripts in Daytona sandbox with network blocked."""
    api_key = os.environ.get("DAYTONA_API_KEY")
    if not api_key:
        return {
            "skipped": True,
            "reason": "DAYTONA_API_KEY not set. Skipping dynamic analysis."
        }

    try:
        from daytona_sdk import Daytona, DaytonaConfig
    except ImportError:
        return {
            "skipped": True,
            "reason": "daytona-sdk not installed. Skipping dynamic analysis."
        }

    config = DaytonaConfig(api_key=api_key)
    base_url = os.environ.get("DAYTONA_BASE_URL")
    if base_url:
        config.api_url = base_url

    daytona = Daytona(config)
    sandbox = None
    report = {
        "network_attempts": [],
        "files_changed": [],
        "sandbox_stdout": "",
        "sandbox_stderr": "",
        "network_method": "",
    }

    try:
        sandbox = daytona.create()
        print(f"    Sandbox created: {sandbox.id}")

        # Upload skill files
        for f in skill_path.rglob("*"):
            if f.is_file():
                rel = f.relative_to(skill_path)
                sandbox.fs.upload_file(
                    f.read_bytes(),
                    f"/home/daytona/skill/{rel}"
                )
        print(f"    Skill files uploaded")

        # Record initial state
        sandbox.process.exec("find /home/daytona/skill -type f | sort > /tmp/before.txt")

        # Block outbound network
        method = _block_network(sandbox)
        report["network_method"] = method
        print(f"    Network blocked via: {method}")

        # Find and execute scripts
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            for script in sorted(scripts_dir.iterdir()):
                if not script.is_file():
                    continue

                remote_path = f"/home/daytona/skill/scripts/{script.name}"
                if script.suffix == ".py":
                    cmd = f"timeout 30 python {remote_path} --help 2>&1 || timeout 30 python {remote_path} 2>&1"
                elif script.suffix == ".sh":
                    cmd = f"timeout 30 bash {remote_path} --help 2>&1 || timeout 30 bash {remote_path} 2>&1"
                else:
                    continue

                print(f"    Executing: {script.name}")
                result = sandbox.process.exec(cmd)
                report["sandbox_stdout"] += f"\n--- {script.name} ---\n{result.result}\n"

        # Detect network attempts
        report["network_attempts"] = _detect_network_attempts(sandbox, method)

        # Check file changes
        sandbox.process.exec("find /home/daytona/skill -type f | sort > /tmp/after.txt")
        diff = sandbox.process.exec("diff /tmp/before.txt /tmp/after.txt || true")
        if diff.result.strip():
            report["files_changed"] = diff.result.strip().splitlines()

    except Exception as e:
        report["error"] = str(e)
        import traceback
        report["traceback"] = traceback.format_exc()
    finally:
        if sandbox:
            try:
                daytona.delete(sandbox)
                print(f"    Sandbox deleted")
            except Exception:
                pass

    return report


# ── Combined Report ─────────────────────────────────────────────────────

def run_safety_check(skill_path: Path) -> dict:
    """Run both static and dynamic analysis, return combined report."""
    print("  Phase 1: Static analysis (Claude API)...")
    static = static_analysis(skill_path)

    print("  Phase 2: Dynamic analysis (Daytona sandbox)...")
    dynamic = dynamic_analysis(skill_path)

    report = {
        "dangerous_patterns": static.get("dangerous_patterns", []),
        "network_urls": static.get("network_urls", []),
        "network_attempts": dynamic.get("network_attempts", []),
        "files_changed": dynamic.get("files_changed", []),
        "recommendation": static.get("recommendation", "review"),
        "summary": static.get("summary", ""),
        "dynamic_skipped": dynamic.get("skipped", False),
        "dynamic_reason": dynamic.get("reason", ""),
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Safety check a staged skill")
    parser.add_argument("skill_path", help="Path to skill in staging/")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not skill_path.exists():
        print(f"  Error: {skill_path} not found")
        sys.exit(1)

    report = run_safety_check(skill_path)

    print(f"\n  {'─' * 50}")
    print(f"  Safety Report: {skill_path.name}")
    print(f"  {'─' * 50}")
    print(f"  Recommendation: {report['recommendation']}")
    print(f"  Summary: {report['summary']}")

    if report["dangerous_patterns"]:
        print(f"\n  Dangerous patterns:")
        for p in report["dangerous_patterns"]:
            print(f"    - {p}")

    if report["network_urls"]:
        print(f"\n  Network URLs found:")
        for u in report["network_urls"]:
            print(f"    - {u}")

    if report["dynamic_skipped"]:
        print(f"\n  Dynamic analysis: skipped ({report['dynamic_reason']})")

    if report["network_attempts"]:
        print(f"\n  Blocked network attempts:")
        for n in report["network_attempts"]:
            print(f"    - {n}")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
