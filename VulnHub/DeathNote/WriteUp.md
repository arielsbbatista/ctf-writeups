# DeathNote CTF Writeup

**Challenge:** DeathNote  
**Platform:** VulnHub  
**Difficulty:** Medium  
**Category:** Web / Linux Privilege Escalation  
**Date Completed:** 2026-06-22  
**Status:** ✅ Rooted  

---

## Objective

Gain root access to a Linux machine running WordPress. The challenge involves discovering credentials through web enumeration, using them for SSH access, database manipulation, and privilege escalation through sudo misconfiguration.

---

## Recon

Initial network scan revealed two open ports:

```bash
nmap -sC -sV -p22,80 --script http-enum 192.168.1.60
```

**Results:**
- Port 22: OpenSSH 7.9p1 (Debian)
- Port 80: Apache httpd 2.4.38 (Debian)
- Directories found: `/wordpress/`, `/robots.txt`, `/manual/`

**Key Findings:**
- robots.txt contained hint about `/important.jpg` and mention of user **ryuk**
- important.jpg held message from Soichiro Yagami with login hint: username in `user.txt`, password unknown

---

## Enumeration

### WordPress Enumeration
Nikto scan identified directory indexing at `/wordpress/wp-content/uploads/`.

Navigated to: `http://deathnote.vuln/wordpress/wp-content/uploads/2021/07/`

**Files discovered:**
- `notes.txt` (449 bytes)
- `user.txt` (91 bytes)

**Content of notes.txt:** List of potential passwords  
**Content of user.txt:** Username for login

### WordPress Hints
Challenge hint at `/wordpress/index.php/hint/0/` referenced:
- Find notes.txt on server (discovered)
- L's favorite line: `iamjustic3` (potential password clue)

---

## Exploitation

### Phase 1: SSH Bruteforce
Used Hydra with discovered username and password list:

```bash
hydra -L user.txt -P notes.txt ssh://192.168.1.60 -t 64
```

**Result:** Valid credentials found
- Username: `l`
- Password: `d34th4m3` (obfuscated)

SSH access gained.

### Phase 2: Privilege Escalation to Kira
Located WordPress configuration at `/var/www/deathnote.vuln/wordpress/wp-config.php`:
- Database user: `l`
- Database password: same as SSH password

Accessed MySQL and extracted WordPress user data:
- User: `kira`
- Hash: `$P$BLAm2r4YofLSOywvLguipu8Av1Tuwq.` (phpass format)

Unable to crack hash efficiently. Updated password directly in database:

```sql
UPDATE wp_users SET user_pass='7a61721ed4832664aa3ce8e2234dcdb4'
```

New password: `k1r4` (obfuscated)

Logged into WordPress as admin.

### Phase 3: System Access as Kira
Explored `/opt/L/kira-case/` directory:

Found encoded file: `case.wav`

Decoded using CyberChef (HEX → Base64):
```
k1r43v1l (obfuscated)
```

Switched user:
```bash
su kira
```

### Phase 4: Privilege Escalation to Root
Checked sudo privileges:

```bash
sudo -l
```

**Result:** User kira has full sudo access: `(ALL : ALL) ALL`

Escalated to root:

```bash
sudo su
```

Root access achieved.

---

## Post Exploitation

### File Exploration
- Discovered `/var/MISA.txt` with message: "it is toooo late for misa"
- Found `/home/kira/kira.txt` containing base64-encoded message about protecting directories

### Password Cracking (Optional)
Root hash from `/etc/shadow` cracked:
- Root password: `l0l` (obfuscated)

---

## Flags

**User Flag:** `l_d34th4m3_k1r4_k1r43v1l`  
**Root Flag:** `r00t_p4ssw0rd_l0l`

---

## Tools Used

### nmap
- **Purpose:** Network reconnaissance and service enumeration
- **Command:** `nmap -sC -sV -p22,80 --script http-enum 192.168.1.60`
- **Finding:** Identified HTTP and SSH services, WordPress installation

### Nikto
- **Purpose:** Web server vulnerability scanner and directory enumeration
- **Finding:** Located directory indexing vulnerability exposing upload folders

### curl
- **Purpose:** Manual HTTP requests and content retrieval
- **Finding:** Extracted content from important.jpg and enumerated web directories

### Hydra
- **Purpose:** SSH credential bruteforce
- **Command:** `hydra -L user.txt -P notes.txt ssh://192.168.1.60 -t 64`
- **Finding:** Discovered valid SSH credentials

### MySQL Client
- **Purpose:** Database access and WordPress user manipulation
- **Finding:** Extracted user hashes, updated password directly in database

### CyberChef
- **Purpose:** Decoding and encoding operations (HEX → Base64)
- **Finding:** Decoded case.wav file to extract password

### john
- **Purpose:** Password hash cracking
- **Command:** `john --wordlist=rockyou.txt hash_shadow --format=sha512crypt`
- **Finding:** Cracked root password

---

## Methodology

**Phase 1: Reconnaissance (5 min)**
1. Network scan with nmap
2. Identify services and open ports
3. Analyze web content and hints

**Phase 2: Web Enumeration (10 min)**
1. Run Nikto for directory discovery
2. Explore WordPress installation
3. Find and download credential files

**Phase 3: Initial Access (5 min)**
1. Bruteforce SSH with Hydra
2. Establish shell access

**Phase 4: Privilege Escalation (15 min)**
1. Access WordPress database
2. Extract and modify user credentials
3. Gain access as privileged user
4. Exploit sudo misconfiguration for root

---

## Lessons Learned

- **Credential Reuse:** Same password used for SSH and database access—always check configuration files
- **Default Protections:** WordPress user hashes can be updated directly if database access is available
- **Hint Analysis:** CTF hints often contain important information (look for encoded messages)
- **Sudo Misconfiguration:** Always check `sudo -l`; unrestricted sudo access = immediate privilege escalation
- **File Enumeration:** Directory indexing vulnerabilities expose sensitive files easily
- **Encoding Recognition:** Learn to identify common encoding schemes (HEX, Base64) for quick decoding

---

## References

- OWASP A01: Broken Access Control (WordPress access)
- OWASP A07: Identification and Authentication Failures
- CWE-256: Plaintext Storage of Password
- CWE-269: Improper Access Control (General)
- [Hydra Documentation](https://github.com/vanhauser-thc/thc-hydra)
- [CyberChef](https://gchq.github.io/CyberChef/)
- WordPress Security: Database access implications
