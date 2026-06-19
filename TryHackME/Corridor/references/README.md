# References & Resources

## IDOR (Insecure Direct Object Reference)

### Official Resources
- **OWASP IDOR:** https://owasp.org/www-community/attacks/IDOR
- **CWE-639:** https://cwe.mitre.org/data/definitions/639.html
- **OWASP Top 10 2021 - A01:** https://owasp.org/Top10/

### Security Articles
- **PortSwigger Web Security:** https://portswigger.net/web-security/access-control/idor
- **HackTricks IDOR:** https://book.hacktricks.xyz/pentesting-web/idor

## Tools Used

### Reconnaissance
- **Nmap:** https://nmap.org/
- **nmap scripts:** https://nmap.org/nsedoc/

### Enumeration
- **ffuf:** https://github.com/ffuf/ffuf
- **Gobuster:** https://github.com/OJ/gobuster
- **OWASP ZAP:** https://www.zaproxy.org/

### Testing & Analysis
- **curl:** https://curl.se/
- **Burp Suite:** https://portswigger.net/burp
- **Postman:** https://www.postman.com/

## Hash Functions & MD5

### MD5 Limitations
- **Wikipedia MD5:** https://en.wikipedia.org/wiki/MD5
- **MD5 Collisions:** https://shattered.io/

### Online MD5 Tools
- **CyberChef:** https://gchq.github.io/CyberChef/ (encryption/decoding)
- **MD5Online:** https://www.md5online.org/

## Werkzeug & Python Security

### Werkzeug Documentation
- **Werkzeug:** https://werkzeug.palletsprojects.com/
- **Flask Security:** https://flask.palletsprojects.com/security/

### CVE Information
- **CVE-2024-42367:** Check CVE databases
- **NVD (National Vulnerability Database):** https://nvd.nist.gov/

## Access Control & Authorization

### Implementation Best Practices
- **OWASP Authorization:** https://owasp.org/www-community/attacks/Authorization
- **OWASP Authentication Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

### Testing Guides
- **OWASP Testing Guide:** https://owasp.org/www-project-web-security-testing-guide/

## CTF Platforms & Challenges

### TryHackMe
- **TryHackMe:** https://www.tryhackme.com/
- **Corridor Challenge:** https://www.tryhackme.com/

### Related Challenges
- IDOR-based challenges on HackTheBox
- Web security tracks on TryHackMe

## Learning Resources

### General Web Security
- **PortSwigger Web Academy:** https://portswigger.net/web-security
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **HackTricks:** https://book.hacktricks.xyz/

### Penetration Testing
- **OSCP Preparation:** https://www.offensive-security.com/
- **eLearnSecurity Resources:** https://www.ellearnity.com/

---

## Corridor-Specific References

### Challenge Details
- **Challenge:** Corridor (TryHackMe)
- **Vulnerability:** Insecure Direct Object Reference (IDOR)
- **Difficulty:** Easy-Medium
- **Exploitation Time:** ~20-30 minutes

### Key Concept
Boundary case testing (ID=0) is critical when exploiting sequential ID schemes. Always test:
- ID=0 (zero-based indexing)
- ID=-1 (negative indices)
- ID beyond visible max
- ID="admin" or special values

---

**Last Updated:** 2026-06-19  
**Status:** Complete & Verified
