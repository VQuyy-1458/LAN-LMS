"""Run on each client machine against the public web origin; never logs credentials."""
import argparse
import getpass
import json
from urllib.parse import urlsplit

import httpx
from websockets.sync.client import connect
from websockets.exceptions import WebSocketException


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True, help='Example: http://192.168.1.10:8080 (no /api suffix)')
    parser.add_argument('--username', help='Optional interactive auth/CSRF/WebSocket/logout check')
    args = parser.parse_args()
    origin = args.base_url.rstrip('/')
    url = urlsplit(origin)
    if url.scheme not in ('http', 'https') or not url.hostname or url.path or url.query or url.fragment or url.username:
        parser.error('base-url must be a web origin without a path or credentials')
    results = []
    with httpx.Client(base_url=origin, timeout=10, follow_redirects=False) as client:
        def check(label, path, status):
            response = client.get(path)
            if response.status_code != status:
                raise RuntimeError(f'{label}: expected HTTP {status}, received {response.status_code}')
            results.append({'check': label, 'passed': True})
            return response
        check('health', '/api/health', 200)
        check('migrated database', '/api/ready', 200)
        check('unauthenticated request blocked', '/api/auth/me', 401)
        if args.username:
            password = getpass.getpass('Password (not stored): ')
            response = client.post('/api/auth/login', headers={'Origin': origin}, json={'username': args.username, 'password': password})
            password = None
            if response.status_code != 200:
                raise RuntimeError(f'Login failed: HTTP {response.status_code}')
            try:
                user = check('session cookie', '/api/auth/me', 200).json()
                token_response = check('CSRF token', '/api/auth/csrf', 200)
                assert token_response.json()['csrf_token']
                if not user['must_change_password']:
                    cookie = '; '.join(f'{c.name}={c.value}' for c in client.cookies.jar)
                    ws_url = ('wss' if url.scheme == 'https' else 'ws') + '://' + url.netloc + '/ws'
                    with connect(ws_url, origin=origin, additional_headers={'Cookie': cookie}, open_timeout=10) as ws:
                        message = json.loads(ws.recv(timeout=25))
                        if message.get('type') != 'heartbeat':
                            raise RuntimeError('Expected WebSocket heartbeat')
                        ws.send(json.dumps({'type': 'heartbeat.ack', 'id': message['id']}))
                    results.append({'check': 'authenticated WebSocket heartbeat', 'passed': True})
                else:
                    results.append({'check': 'authenticated WebSocket', 'passed': False, 'note': 'Change initial password in frontend first'})
            finally:
                token = client.get('/api/auth/csrf')
                if token.status_code == 200:
                    response = client.post('/api/auth/logout', headers={'Origin': origin, 'X-CSRF-Token': token.json()['csrf_token']})
                    if response.status_code != 204:
                        raise RuntimeError(f'Logout failed: HTTP {response.status_code}')
                    check('logout revoked session', '/api/auth/me', 401)
    print(json.dumps({'origin': origin, 'checks': results}, ensure_ascii=False, indent=2))
    return 0 if all(item['passed'] for item in results) else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (httpx.HTTPError, WebSocketException, RuntimeError, OSError, TimeoutError, ValueError, KeyError) as exc:
        # Avoid printing exception payloads that may include cookies or credentials.
        print(f'LAN check failed ({type(exc).__name__}). Check origin, proxy, migrations and server availability.')
        raise SystemExit(1)
