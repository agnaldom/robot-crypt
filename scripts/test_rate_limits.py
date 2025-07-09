#!/usr/bin/env python3
"""
Rate limiting test and monitoring utility for Robot-Crypt API.

This script helps test the rate limiting implementation and monitor
API usage patterns.
"""

import asyncio
import aiohttp
import time
import json
import argparse
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics


class RateLimitTester:
    """Test rate limiting behavior of API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.results = []
        
    async def test_endpoint(self, endpoint: str, num_requests: int = 50, concurrent: int = 5, delay: float = 0.1):
        """
        Test rate limiting on a specific endpoint.
        
        Args:
            endpoint: API endpoint to test (e.g., '/portfolio/wallet/total-value')
            num_requests: Total number of requests to send
            concurrent: Number of concurrent requests
            delay: Delay between batches (seconds)
        """
        print(f"\n🧪 Testing endpoint: {endpoint}")
        print(f"📊 Sending {num_requests} requests with {concurrent} concurrent requests")
        print(f"⏱️  Delay between batches: {delay}s")
        print("-" * 60)
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        results = []
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for batch in range(0, num_requests, concurrent):
                batch_size = min(concurrent, num_requests - batch)
                batch_start = time.time()
                
                # Create concurrent requests
                tasks = []
                for i in range(batch_size):
                    task = self._make_request(session, endpoint, headers, batch + i + 1)
                    tasks.append(task)
                
                # Execute concurrent requests
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        results.append({
                            'request_id': batch + i + 1,
                            'status_code': 'ERROR',
                            'response_time': 0,
                            'error': str(result),
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        results.append(result)
                
                batch_time = time.time() - batch_start
                successful = sum(1 for r in batch_results if not isinstance(r, Exception) and r.get('status_code') == 200)
                rate_limited = sum(1 for r in batch_results if not isinstance(r, Exception) and r.get('status_code') == 429)
                
                print(f"Batch {batch//concurrent + 1:2d}: {successful:2d} success, {rate_limited:2d} rate limited, {batch_time:.2f}s")
                
                # Delay between batches
                if delay > 0 and batch + concurrent < num_requests:
                    await asyncio.sleep(delay)
        
        total_time = time.time() - start_time
        self._analyze_results(results, total_time)
        return results
    
    async def _make_request(self, session: aiohttp.ClientSession, endpoint: str, headers: dict, request_id: int):
        """Make a single HTTP request."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with session.get(url, headers=headers) as response:
                response_time = time.time() - start_time
                
                # Try to get rate limit headers
                rate_limit_headers = {}
                for header in response.headers:
                    if header.lower().startswith('x-ratelimit'):
                        rate_limit_headers[header] = response.headers[header]
                
                content = None
                try:
                    content = await response.json()
                except:
                    content = await response.text()
                
                return {
                    'request_id': request_id,
                    'status_code': response.status,
                    'response_time': response_time,
                    'rate_limit_headers': rate_limit_headers,
                    'content_length': len(str(content)),
                    'timestamp': datetime.now().isoformat(),
                    'content': content if response.status == 429 else None  # Only store 429 responses
                }
        except Exception as e:
            return {
                'request_id': request_id,
                'status_code': 'ERROR',
                'response_time': time.time() - start_time,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_results(self, results: List[Dict], total_time: float):
        """Analyze and display test results."""
        print("\n📈 ANALYSIS RESULTS")
        print("=" * 60)
        
        # Basic statistics
        total_requests = len(results)
        successful = [r for r in results if r.get('status_code') == 200]
        rate_limited = [r for r in results if r.get('status_code') == 429]
        errors = [r for r in results if r.get('status_code') == 'ERROR']
        other_errors = [r for r in results if isinstance(r.get('status_code'), int) and r.get('status_code') not in [200, 429]]
        
        print(f"Total requests:     {total_requests}")
        print(f"Successful (200):   {len(successful):3d} ({len(successful)/total_requests*100:.1f}%)")
        print(f"Rate limited (429): {len(rate_limited):3d} ({len(rate_limited)/total_requests*100:.1f}%)")
        print(f"Network errors:     {len(errors):3d} ({len(errors)/total_requests*100:.1f}%)")
        print(f"Other errors:       {len(other_errors):3d} ({len(other_errors)/total_requests*100:.1f}%)")
        print(f"Total time:         {total_time:.2f} seconds")
        print(f"Requests per second: {total_requests/total_time:.2f}")
        
        # Response time analysis
        if successful:
            response_times = [r['response_time'] for r in successful]
            print(f"\n⏱️  RESPONSE TIME ANALYSIS (successful requests)")
            print(f"Average: {statistics.mean(response_times):.3f}s")
            print(f"Median:  {statistics.median(response_times):.3f}s")
            print(f"Min:     {min(response_times):.3f}s")
            print(f"Max:     {max(response_times):.3f}s")
        
        # Rate limit analysis
        if rate_limited:
            print(f"\n🚦 RATE LIMIT ANALYSIS")
            
            # Show sample rate limit response
            sample_429 = rate_limited[0]
            if sample_429.get('content'):
                print("Sample 429 response:")
                print(json.dumps(sample_429['content'], indent=2)[:500] + "..." if len(str(sample_429['content'])) > 500 else json.dumps(sample_429['content'], indent=2))
            
            # Show rate limit headers progression
            print(f"\nRate limit headers from first few 429 responses:")
            for i, r in enumerate(rate_limited[:3]):
                if r.get('rate_limit_headers'):
                    print(f"Response {i+1}: {r['rate_limit_headers']}")
        
        # Timeline analysis
        print(f"\n📊 TIMELINE ANALYSIS")
        
        # Group by 10-second windows
        window_size = 10  # seconds
        timeline = {}
        
        for result in results:
            try:
                timestamp = datetime.fromisoformat(result['timestamp'])
                window = int(timestamp.timestamp() // window_size) * window_size
                
                if window not in timeline:
                    timeline[window] = {'success': 0, 'rate_limited': 0, 'errors': 0}
                
                if result.get('status_code') == 200:
                    timeline[window]['success'] += 1
                elif result.get('status_code') == 429:
                    timeline[window]['rate_limited'] += 1
                else:
                    timeline[window]['errors'] += 1
            except:
                continue
        
        print(f"{'Time Window':<20} {'Success':<8} {'Rate Limited':<13} {'Errors':<7}")
        print("-" * 50)
        for window in sorted(timeline.keys()):
            window_time = datetime.fromtimestamp(window).strftime("%H:%M:%S")
            data = timeline[window]
            print(f"{window_time:<20} {data['success']:<8} {data['rate_limited']:<13} {data['errors']:<7}")
    
    async def monitor_endpoint(self, endpoint: str, duration: int = 300, interval: float = 1.0):
        """
        Monitor an endpoint for rate limiting behavior over time.
        
        Args:
            endpoint: API endpoint to monitor
            duration: Monitoring duration in seconds
            interval: Request interval in seconds
        """
        print(f"\n📡 Monitoring endpoint: {endpoint}")
        print(f"⏱️  Duration: {duration} seconds")
        print(f"🔄 Request interval: {interval} seconds")
        print("-" * 60)
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        start_time = time.time()
        results = []
        
        async with aiohttp.ClientSession() as session:
            request_count = 0
            while time.time() - start_time < duration:
                request_count += 1
                result = await self._make_request(session, endpoint, headers, request_count)
                results.append(result)
                
                # Display real-time status
                status = result.get('status_code')
                response_time = result.get('response_time', 0)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                if status == 200:
                    print(f"[{timestamp}] ✅ {status} - {response_time:.3f}s")
                elif status == 429:
                    rate_headers = result.get('rate_limit_headers', {})
                    remaining = rate_headers.get('X-RateLimit-Remaining', 'N/A')
                    reset = rate_headers.get('X-RateLimit-Reset', 'N/A')
                    print(f"[{timestamp}] 🚦 {status} - Remaining: {remaining}, Reset: {reset}")
                else:
                    print(f"[{timestamp}] ❌ {status} - {result.get('error', 'Unknown error')}")
                
                # Wait for next request
                await asyncio.sleep(interval)
        
        total_time = time.time() - start_time
        self._analyze_results(results, total_time)
        return results


async def main():
    parser = argparse.ArgumentParser(description="Test Robot-Crypt API rate limiting")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--token", help="Authentication token")
    parser.add_argument("--endpoint", default="/portfolio/wallet/total-value", help="Endpoint to test")
    parser.add_argument("--mode", choices=["test", "monitor"], default="test", help="Test mode")
    parser.add_argument("--requests", type=int, default=50, help="Number of requests for test mode")
    parser.add_argument("--concurrent", type=int, default=5, help="Concurrent requests")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration (seconds)")
    parser.add_argument("--interval", type=float, default=1.0, help="Request interval (seconds)")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between batches (seconds)")
    
    args = parser.parse_args()
    
    print("🤖 Robot-Crypt API Rate Limit Tester")
    print("=" * 60)
    print(f"Target URL: {args.url}")
    print(f"Endpoint: {args.endpoint}")
    print(f"Mode: {args.mode}")
    
    tester = RateLimitTester(args.url, args.token)
    
    if args.mode == "test":
        await tester.test_endpoint(
            args.endpoint,
            num_requests=args.requests,
            concurrent=args.concurrent,
            delay=args.delay
        )
    elif args.mode == "monitor":
        await tester.monitor_endpoint(
            args.endpoint,
            duration=args.duration,
            interval=args.interval
        )


if __name__ == "__main__":
    asyncio.run(main())
