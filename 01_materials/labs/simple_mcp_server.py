
#!/usr/bin/env python3
"""
simple_mcp_server.py

A minimal MCP server with three tools.
Run it from a terminal with:
    python simple_mcp_server.py

It will start listening on http://localhost:8000
and your notebook connects to http://localhost:8000/sse
"""

import hashlib
import json
import re
from mcp.server.fastmcp import FastMCP

# --- Create the server ---
mcp = FastMCP(name="Simple Security Server")


# --- Tool 1: Password strength checker ---
@mcp.tool()
def check_password_strength(password: str) -> str:
    """
    Checks the strength of a password.
    Returns a score from 0-100 and suggestions for improvement.
    Use this when the user asks to evaluate or rate a password.
    """
    score = 0
    tips = []

    if len(password) >= 16:
        score += 30
    elif len(password) >= 12:
        score += 20
    elif len(password) >= 8:
        score += 10
    else:
        tips.append("Use at least 8 characters")

    if re.search(r"[A-Z]", password): score += 15
    else: tips.append("Add uppercase letters")

    if re.search(r"[a-z]", password): score += 15
    else: tips.append("Add lowercase letters")

    if re.search(r"[0-9]", password): score += 15
    else: tips.append("Add numbers")

    if re.search(r"[!@#$%^&*()\-_=+]", password): score += 25
    else: tips.append("Add special characters like !@#$%")

    rating = "Very Weak" if score < 30 else "Weak" if score < 50 else "Moderate" if score < 70 else "Strong" if score < 85 else "Very Strong"

    return json.dumps({
        "score": score,
        "rating": rating,
        "tips": tips or ["No improvements needed!"]
    })


# --- Tool 2: Hash generator ---
@mcp.tool()
def generate_hash(text: str, algorithm: str = "sha256") -> str:
    """
    Generates a cryptographic hash of the input text.
    Supported algorithms: md5, sha1, sha256, sha512.
    Use when the user wants to hash a string or compare hash algorithms.
    """
    try:
        h = hashlib.new(algorithm.lower())
        h.update(text.encode())
        return json.dumps({"algorithm": algorithm.upper(), "hash": h.hexdigest()})
    except ValueError:
        return f"Unsupported algorithm: {algorithm}. Choose from: md5, sha1, sha256, sha512"


# --- Tool 3: OWASP Top 10 reference ---
@mcp.tool()
def get_owasp_top10() -> str:
    """
    Returns the OWASP Top 10 web application security risks (2021 edition).
    Use when the user asks about common web vulnerabilities or security best practices.
    """
    top10 = [
        {"rank": 1, "name": "Broken Access Control"},
        {"rank": 2, "name": "Cryptographic Failures"},
        {"rank": 3, "name": "Injection"},
        {"rank": 4, "name": "Insecure Design"},
        {"rank": 5, "name": "Security Misconfiguration"},
        {"rank": 6, "name": "Vulnerable and Outdated Components"},
        {"rank": 7, "name": "Identification and Authentication Failures"},
        {"rank": 8, "name": "Software and Data Integrity Failures"},
        {"rank": 9, "name": "Security Logging and Monitoring Failures"},
        {"rank": 10, "name": "Server-Side Request Forgery (SSRF)"},
    ]
    return json.dumps(top10)


# --- Start the server ---
if __name__ == "__main__":
    # SSE transport: runs an HTTP server on port 8000
    # Clients connect to http://localhost:8000/sse
    mcp.run(transport="sse")
