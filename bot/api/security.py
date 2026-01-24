"""
API Security Module
===================
Rate limiting and IP blocking for API protection:
- Request rate limiting (per IP, per token)
- IP blacklisting/whitelisting
- Brute force protection
- Request logging and monitoring
"""

import asyncio
import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Tuple, Callable
from collections import defaultdict
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
import ipaddress

logger = logging.getLogger('Offcialx.APISecurity')

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, requests_per_minute: int = 60,
                 requests_per_hour: int = 1000,
                 burst_size: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size

        # Request tracking: key -> list of timestamps
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)

        # Token buckets for burst control
        self.buckets: Dict[str, Dict] = {}

        # Cleanup task
        self._cleanup_task = None

    def _get_bucket(self, key: str) -> Dict:
        """Get or create a token bucket for a key"""
        now = time.time()

        if key not in self.buckets:
            self.buckets[key] = {
                'tokens': self.burst_size,
                'last_update': now
            }

        bucket = self.buckets[key]

        # Refill tokens based on time passed
        time_passed = now - bucket['last_update']
        tokens_to_add = time_passed * (self.requests_per_minute / 60)
        bucket['tokens'] = min(self.burst_size, bucket['tokens'] + tokens_to_add)
        bucket['last_update'] = now

        return bucket

    def is_allowed(self, key: str) -> Tuple[bool, Dict]:
        """Check if a request is allowed"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)

        # Clean old entries
        self.minute_requests[key] = [
            t for t in self.minute_requests[key] if t > minute_ago
        ]
        self.hour_requests[key] = [
            t for t in self.hour_requests[key] if t > hour_ago
        ]

        minute_count = len(self.minute_requests[key])
        hour_count = len(self.hour_requests[key])

        # Check limits
        if minute_count >= self.requests_per_minute:
            retry_after = 60 - (now - self.minute_requests[key][0]).seconds
            return False, {
                'error': 'rate_limit_exceeded',
                'limit': 'minute',
                'retry_after': max(1, retry_after),
                'requests_made': minute_count,
                'requests_allowed': self.requests_per_minute
            }

        if hour_count >= self.requests_per_hour:
            retry_after = 3600 - (now - self.hour_requests[key][0]).seconds
            return False, {
                'error': 'rate_limit_exceeded',
                'limit': 'hour',
                'retry_after': max(1, retry_after),
                'requests_made': hour_count,
                'requests_allowed': self.requests_per_hour
            }

        # Check burst bucket
        bucket = self._get_bucket(key)
        if bucket['tokens'] < 1:
            return False, {
                'error': 'burst_limit_exceeded',
                'retry_after': 1,
                'message': 'Too many rapid requests'
            }

        # Allow request
        bucket['tokens'] -= 1
        self.minute_requests[key].append(now)
        self.hour_requests[key].append(now)

        return True, {
            'remaining_minute': self.requests_per_minute - minute_count - 1,
            'remaining_hour': self.requests_per_hour - hour_count - 1
        }

    def cleanup(self):
        """Clean up old entries"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        for key in list(self.minute_requests.keys()):
            self.minute_requests[key] = [
                t for t in self.minute_requests[key] if t > hour_ago
            ]
            if not self.minute_requests[key]:
                del self.minute_requests[key]

        for key in list(self.hour_requests.keys()):
            self.hour_requests[key] = [
                t for t in self.hour_requests[key] if t > hour_ago
            ]
            if not self.hour_requests[key]:
                del self.hour_requests[key]

class IPBlocker:
    """IP blocking and whitelisting system"""

    def __init__(self):
        # Blocked IPs/ranges
        self.blocked_ips: Set[str] = set()
        self.blocked_ranges: list = []

        # Whitelisted IPs/ranges (bypass rate limiting)
        self.whitelisted_ips: Set[str] = set()
        self.whitelisted_ranges: list = []

        # Temporary blocks (for brute force)
        self.temp_blocks: Dict[str, datetime] = {}

        # Failed attempt tracking
        self.failed_attempts: Dict[str, list] = defaultdict(list)
        self.max_failed_attempts = 5
        self.block_duration = 3600  # 1 hour

        # Request tracking for suspicious activity
        self.request_patterns: Dict[str, list] = defaultdict(list)

        # Load blocked IPs from environment
        self._load_from_env()

    def _load_from_env(self):
        """Load blocked/whitelisted IPs from environment"""
        blocked = os.getenv('BLOCKED_IPS', '')
        if blocked:
            for ip in blocked.split(','):
                ip = ip.strip()
                if ip:
                    self.block_ip(ip)

        whitelisted = os.getenv('WHITELISTED_IPS', '')
        if whitelisted:
            for ip in whitelisted.split(','):
                ip = ip.strip()
                if ip:
                    self.whitelist_ip(ip)

    def _is_ip_in_range(self, ip: str, ranges: list) -> bool:
        """Check if IP is in any of the ranges"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for network in ranges:
                if ip_obj in network:
                    return True
        except:
            pass
        return False

    def is_blocked(self, ip: str) -> Tuple[bool, Optional[str]]:
        """Check if an IP is blocked"""
        # Check permanent blocks
        if ip in self.blocked_ips:
            return True, "IP is permanently blocked"

        if self._is_ip_in_range(ip, self.blocked_ranges):
            return True, "IP range is blocked"

        # Check temporary blocks
        if ip in self.temp_blocks:
            if datetime.utcnow() < self.temp_blocks[ip]:
                remaining = (self.temp_blocks[ip] - datetime.utcnow()).seconds
                return True, f"IP temporarily blocked. Retry in {remaining}s"
            else:
                del self.temp_blocks[ip]

        return False, None

    def is_whitelisted(self, ip: str) -> bool:
        """Check if an IP is whitelisted"""
        if ip in self.whitelisted_ips:
            return True
        return self._is_ip_in_range(ip, self.whitelisted_ranges)

    def block_ip(self, ip_or_range: str, permanent: bool = True):
        """Block an IP or range"""
        try:
            if '/' in ip_or_range:
                network = ipaddress.ip_network(ip_or_range, strict=False)
                self.blocked_ranges.append(network)
            else:
                self.blocked_ips.add(ip_or_range)

            logger.warning(f'Blocked IP/range: {ip_or_range}')
        except Exception as e:
            logger.error(f'Failed to block IP {ip_or_range}: {e}')

    def unblock_ip(self, ip_or_range: str):
        """Unblock an IP or range"""
        self.blocked_ips.discard(ip_or_range)

        try:
            if '/' in ip_or_range:
                network = ipaddress.ip_network(ip_or_range, strict=False)
                self.blocked_ranges = [r for r in self.blocked_ranges if r != network]
        except:
            pass

        if ip_or_range in self.temp_blocks:
            del self.temp_blocks[ip_or_range]

        logger.info(f'Unblocked IP/range: {ip_or_range}')

    def whitelist_ip(self, ip_or_range: str):
        """Whitelist an IP or range"""
        try:
            if '/' in ip_or_range:
                network = ipaddress.ip_network(ip_or_range, strict=False)
                self.whitelisted_ranges.append(network)
            else:
                self.whitelisted_ips.add(ip_or_range)

            logger.info(f'Whitelisted IP/range: {ip_or_range}')
        except Exception as e:
            logger.error(f'Failed to whitelist IP {ip_or_range}: {e}')

    def record_failed_attempt(self, ip: str, reason: str = None):
        """Record a failed authentication attempt"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.block_duration)

        # Clean old attempts
        self.failed_attempts[ip] = [
            t for t in self.failed_attempts[ip] if t > cutoff
        ]

        # Add new attempt
        self.failed_attempts[ip].append(now)

        # Check if should be blocked
        if len(self.failed_attempts[ip]) >= self.max_failed_attempts:
            self.temp_blocks[ip] = now + timedelta(seconds=self.block_duration)
            logger.warning(f'IP {ip} temporarily blocked for {self.max_failed_attempts} failed attempts')
            return True

        return False

    def record_suspicious_activity(self, ip: str, activity_type: str):
        """Record suspicious activity for pattern detection"""
        now = datetime.utcnow()

        self.request_patterns[ip].append({
            'time': now,
            'type': activity_type
        })

        # Keep only last hour
        cutoff = now - timedelta(hours=1)
        self.request_patterns[ip] = [
            p for p in self.request_patterns[ip] if p['time'] > cutoff
        ]

        # Check for suspicious patterns
        if len(self.request_patterns[ip]) > 100:
            # Too many requests in short time
            self.temp_blocks[ip] = now + timedelta(seconds=300)
            logger.warning(f'IP {ip} blocked for suspicious activity pattern')

    def get_stats(self) -> Dict:
        """Get blocking statistics"""
        return {
            'blocked_ips': len(self.blocked_ips),
            'blocked_ranges': len(self.blocked_ranges),
            'whitelisted_ips': len(self.whitelisted_ips),
            'temp_blocked_ips': len(self.temp_blocks),
            'ips_with_failed_attempts': len(self.failed_attempts)
        }

# Global instances
rate_limiter = RateLimiter()
ip_blocker = IPBlocker()

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI"""

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check IP block
        is_blocked, reason = ip_blocker.is_blocked(client_ip)
        if is_blocked:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={'error': 'forbidden', 'message': reason}
            )

        # Skip rate limiting for whitelisted IPs
        if not ip_blocker.is_whitelisted(client_ip):
            # Apply rate limiting
            rate_key = self._get_rate_key(request, client_ip)
            allowed, info = rate_limiter.is_allowed(rate_key)

            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=info,
                    headers={
                        'Retry-After': str(info.get('retry_after', 60)),
                        'X-RateLimit-Limit': str(rate_limiter.requests_per_minute),
                        'X-RateLimit-Remaining': '0'
                    }
                )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add security headers
        response.headers['X-Process-Time'] = str(process_time)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Log slow requests
        if process_time > 5:
            logger.warning(f'Slow request: {request.url.path} took {process_time:.2f}s from {client_ip}')

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check forwarded headers (for proxies)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        return request.client.host if request.client else '0.0.0.0'

    def _get_rate_key(self, request: Request, client_ip: str) -> str:
        """Generate rate limiting key"""
        # Use API key if present, otherwise use IP
        api_key = request.headers.get('X-API-Key', '')

        if api_key:
            return f"token:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

        return f"ip:{client_ip}"

def require_auth(func: Callable):
    """Decorator to require authentication and track failed attempts"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        client_ip = request.client.host if request.client else '0.0.0.0'

        # Check for API key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            ip_blocker.record_failed_attempt(client_ip, 'missing_api_key')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='API key required'
            )

        # Validate API key (implement your validation logic)
        valid_key = os.getenv('API_SECRET_KEY', '')
        if api_key != valid_key:
            blocked = ip_blocker.record_failed_attempt(client_ip, 'invalid_api_key')
            if blocked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Too many failed attempts. IP blocked temporarily.'
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid API key'
            )

        return await func(request, *args, **kwargs)

    return wrapper

# Rate limit decorator for specific endpoints
def rate_limit(requests_per_minute: int = 30):
    """Decorator for endpoint-specific rate limiting"""
    endpoint_limiter = RateLimiter(requests_per_minute=requests_per_minute)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else '0.0.0.0'
            endpoint = request.url.path
            key = f"{client_ip}:{endpoint}"

            allowed, info = endpoint_limiter.is_allowed(key)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=info
                )

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator

# Admin endpoints for managing blocks
async def get_security_stats() -> Dict:
    """Get security statistics"""
    return {
        'rate_limiter': {
            'active_keys': len(rate_limiter.minute_requests)
        },
        'ip_blocker': ip_blocker.get_stats()
    }

async def block_ip_endpoint(ip: str, permanent: bool = True):
    """Block an IP via API"""
    ip_blocker.block_ip(ip, permanent)
    return {'success': True, 'message': f'IP {ip} blocked'}

async def unblock_ip_endpoint(ip: str):
    """Unblock an IP via API"""
    ip_blocker.unblock_ip(ip)
    return {'success': True, 'message': f'IP {ip} unblocked'}
