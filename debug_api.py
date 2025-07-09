#!/usr/bin/env python3
"""
Debug script to analyze API issues with rate limiting and authentication.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any


class APIDebugger:
    """Debug utility for API issues."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, endpoint: str, headers: Dict[str, str] = None, params: Dict[str, Any] = None):
        """Test a single endpoint and return detailed response info."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.get(url, headers=headers or {}, params=params or {}) as response:
                # Get response details
                response_data = {
                    "url": str(response.url),
                    "status": response.status,
                    "headers": dict(response.headers),
                    "content": None,
                    "error": None
                }
                
                try:
                    content = await response.text()
                    # Try to parse as JSON
                    try:
                        response_data["content"] = json.loads(content)
                    except:
                        response_data["content"] = content
                except Exception as e:
                    response_data["error"] = str(e)
                
                return response_data
                
        except Exception as e:
            return {
                "url": url,
                "status": "ERROR",
                "error": str(e),
                "headers": {},
                "content": None
            }
    
    async def test_rate_limiting(self):
        """Test rate limiting behavior."""
        print("🧪 Testing Rate Limiting...")
        print("-" * 50)
        
        # Test endpoints that are being rate limited
        endpoints = [
            "/portfolio/wallet/value-history?currency=USD&period=month",
            "/portfolio/metrics",
            "/trades?limit=10"
        ]
        
        for endpoint in endpoints:
            print(f"\nTesting: {endpoint}")
            
            # Make multiple requests quickly
            for i in range(5):
                result = await self.test_endpoint(endpoint)
                
                status = result["status"]
                if status == 429:
                    print(f"  Request {i+1}: {status} - Rate Limited")
                    rate_headers = {k: v for k, v in result["headers"].items() if k.lower().startswith('x-ratelimit')}
                    if rate_headers:
                        print(f"    Rate limit headers: {rate_headers}")
                elif status == 401:
                    print(f"  Request {i+1}: {status} - Unauthorized")
                elif status == 200:
                    print(f"  Request {i+1}: {status} - Success")
                else:
                    print(f"  Request {i+1}: {status} - {result.get('error', 'Unknown')}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            print()
    
    async def test_authentication(self):
        """Test authentication endpoints."""
        print("🔐 Testing Authentication...")
        print("-" * 50)
        
        # Test login endpoint
        login_result = await self.test_endpoint("/auth/login")
        print(f"Login endpoint: {login_result['status']}")
        
        # Test protected endpoints without auth
        protected_endpoints = [
            "/portfolio/metrics",
            "/trades",
            "/auth/me"
        ]
        
        for endpoint in protected_endpoints:
            result = await self.test_endpoint(endpoint)
            print(f"{endpoint}: {result['status']}")
            if result['status'] == 401:
                print(f"  → Correctly requires authentication")
        
        print()
    
    async def test_basic_endpoints(self):
        """Test basic endpoints that should work."""
        print("🏥 Testing Basic Endpoints...")
        print("-" * 50)
        
        basic_endpoints = [
            "/",
            "/health",
            "/config",
            "/docs"
        ]
        
        for endpoint in basic_endpoints:
            result = await self.test_endpoint(endpoint)
            print(f"{endpoint}: {result['status']}")
            
            if result['status'] == 200:
                print(f"  ✅ Working correctly")
            else:
                print(f"  ❌ Error: {result.get('error', 'Unknown')}")
        
        print()
    
    async def analyze_rate_limit_config(self):
        """Analyze rate limit configuration."""
        print("📊 Rate Limit Configuration Analysis...")
        print("-" * 50)
        
        # Test a rate-limited endpoint to get headers
        result = await self.test_endpoint("/portfolio/wallet/value-history?currency=USD&period=month")
        
        if result['status'] == 429:
            print("Current rate limit status: EXCEEDED")
            headers = result['headers']
            rate_headers = {k: v for k, v in headers.items() if k.lower().startswith('x-ratelimit')}
            
            print("Rate limit headers:")
            for header, value in rate_headers.items():
                print(f"  {header}: {value}")
                
            if 'content' in result and result['content']:
                print("\nRate limit response:")
                print(json.dumps(result['content'], indent=2))
        else:
            print(f"Current rate limit status: OK (Status: {result['status']})")
        
        print()
    
    async def run_full_diagnosis(self):
        """Run complete API diagnosis."""
        print("🤖 Robot-Crypt API Diagnosis")
        print("=" * 60)
        
        await self.test_basic_endpoints()
        await self.test_authentication()
        await self.analyze_rate_limit_config()
        await self.test_rate_limiting()
        
        print("=" * 60)
        print("✅ Diagnosis complete!")


async def main():
    """Main function."""
    async with APIDebugger() as debugger:
        await debugger.run_full_diagnosis()


if __name__ == "__main__":
    asyncio.run(main())
