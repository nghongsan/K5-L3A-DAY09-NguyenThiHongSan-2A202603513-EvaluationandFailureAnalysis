"""Local three-architecture demo. Run from src: python3 -m lab8.demo.web."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

SRC = Path(__file__).resolve().parents[2]
UI = Path(__file__).with_name('ui')
SHAPES = ('workflow', 'single', 'orchestrator')
CASES = {
    'C-001': ('Hoàn phí giao trễ', 'Đơn giao trễ 4 ngày, phí ship 35.000đ, approval hợp lệ.'),
    'C-002': ('Ticket khác dữ liệu thật', 'Ticket nói trễ 5 ngày; order chỉ trễ 2 ngày. Phải từ chối.'),
    'C-003': ('Hàng hỏng đã xác minh', 'Tính bồi thường theo policy và số tiền đã thanh toán.'),
    'C-004': ('Thiếu mã đơn', 'Yêu cầu bổ sung thông tin; không tự đoán mã đơn từ ticket.'),
    'C-005': ('Đơn không thuộc khách', 'Chuyển xử lý, không tiết lộ dữ liệu của chủ đơn khác.'),
    'C-007': ('Approval không hợp lệ', 'Quote 35.000đ nhưng host từ chối ghi tiền.'),
    'C-008': ('Approval thấp hơn quote', 'Đề xuất 35.000đ; chỉ được hoàn 20.000đ.'),
    'C-010': ('Ticket chứa lệnh giả', 'Bỏ qua yêu cầu vượt chính sách, vẫn hoàn đúng 35.000đ.'),
    'C-013': ('Đã hoàn đủ trước đó', 'Host chặn khoản hoàn lặp theo cùng đơn hàng.'),
    'C-014': ('Chỉ hoàn phần chênh lệch', 'Quote 150.000đ, đã hoàn 30.000đ; lần này hoàn 120.000đ.'),
}


def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError('Yêu cầu phải là JSON object.')
    claim = payload.get('claim_id', 'C-001')
    mode = payload.get('mode', 'run')
    seed = payload.get('seed', 11)
    if not isinstance(claim, str) or not isinstance(mode, str) or claim not in CASES or mode not in ('run', 'retry', 'crash'):
        raise ValueError('Claim hoặc chế độ không được hỗ trợ.')
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 999999:
        raise ValueError('Seed phải là số nguyên từ 0 đến 999999.')
    if mode == 'crash' and claim != 'C-001':
        raise ValueError('Demo crash dùng C-001 để bảo đảm đi qua bước ghi refund.')
    return {'claim_id': claim, 'mode': mode, 'seed': seed}


def worker(shape, payload):
    """Each subprocess owns its working directory, database, and trace files."""
    import time
    from lab8.app import prepare_store, run_shape
    from lab8.db import connect, load_jsonl
    from lab8.durability import InjectedCrash
    from lab8.metrics import trial_pass

    if shape not in SHAPES:
        raise ValueError('Unknown shape')
    payload = validate(payload)
    claim, seed, mode = payload['claim_id'], payload['seed'], payload['mode']
    store = Path('demo.sqlite').resolve()
    prepare_store(store)
    expected = next(row['expected'] for row in load_jsonl(SRC / 'data/public_claims.jsonl')
                    if row['claim_id'] == claim)
    attempts = []
    points = ['after_effect_before_checkpoint', None] if mode == 'crash' else [None] * (2 if mode == 'retry' else 1)
    final = None
    passed = False
    reason = 'no_result'
    for index, point in enumerate(points, 1):
        started = time.time()
        try:
            result = run_shape(shape, claim, seed=seed, store_path=str(store), crash_at=point)
            conn = connect(store)
            try:
                passed, reason = trial_pass(result.as_dict(), expected, conn, started_at=started)
            finally:
                conn.close()
            final = result.as_dict()
            # Fail closed: never forward artifacts the lab scanner considers unsafe.
            if 'leak' in reason or 'secret' in reason or 'pii' in reason:
                raise ValueError('Unsafe trace rejected')
            trace = json.loads(Path(result.trace_path).read_text(encoding='utf-8'))
            attempts.append({'number': index, 'status': result.status, 'events': trace['events'],
                             'refund_count': len(result.refund_effects),
                             'refund_vnd': sum(e['amount_vnd'] for e in result.refund_effects)})
        except InjectedCrash:
            trace_path = Path('traces') / f'R-{shape}-{claim}-s{seed}.json'
            trace = json.loads(trace_path.read_text(encoding='utf-8')) if trace_path.exists() else {'events': []}
            attempts.append({'number': index, 'status': 'crashed', 'events': trace['events'],
                             'crash_at': point})
    if final is None:
        raise ValueError('No final result')
    # trace_path points into a disposable directory; the UI gets an event snapshot instead.
    final.pop('trace_path', None)
    return {'shape': shape, 'result': final, 'attempts': attempts,
            'passed': passed, 'check_reason': reason}


def compare(payload):
    payload = validate(payload)
    rows = []
    env = os.environ.copy()
    env['PYTHONPATH'] = str(SRC) + os.pathsep + env.get('PYTHONPATH', '')
    for shape in SHAPES:
        with tempfile.TemporaryDirectory(prefix=f'lab8-ui-{shape}-') as temp:
            process = subprocess.run([sys.executable, '-m', 'lab8.demo.web', '--worker', shape],
                                     input=json.dumps(payload), text=True, capture_output=True,
                                     cwd=temp, env=env, timeout=30)
            if process.returncode:
                raise RuntimeError(f'{shape}: không chạy được. Kiểm tra test Python trong repo.')
            rows.append(json.loads(process.stdout))
    return {'claim_id': payload['claim_id'], 'seed': payload['seed'], 'mode': payload['mode'],
            'rows': rows, 'note': 'MockLLM · chi phí mô phỏng · mỗi kiến trúc dùng SQLite riêng'}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # No request bodies, raw tickets, or traces in stdout.

    def send(self, status, body, content_type='application/json; charset=utf-8'):
        data = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, dict) else body
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/cases':
            return self.send(200, {'cases': [{'id': cid, 'title': title, 'description': description}
                                           for cid, (title, description) in CASES.items()]})
        files = {'/': ('index.html', 'text/html; charset=utf-8'),
                 '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                 '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if path not in files:
            return self.send(404, {'error': 'Không tìm thấy.'})
        name, mime = files[path]
        self.send(200, (UI / name).read_bytes(), mime)

    def do_POST(self):
        if self.path != '/api/compare':
            return self.send(404, {'error': 'Không tìm thấy.'})
        # Custom header prevents cross-site form submissions to the local demo.
        origin = self.headers.get('Origin')
        if self.headers.get('X-Demo-Request') != '1' or (origin and origin != f'http://{self.headers.get("Host")}'):
            return self.send(403, {'error': 'Yêu cầu phải đến từ giao diện demo local.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise ValueError('Kích thước yêu cầu không hợp lệ.')
            result = compare(json.loads(self.rfile.read(length)))
            self.send(200, result)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send(400, {'error': str(exc)})
        except (RuntimeError, subprocess.TimeoutExpired):
            self.send(500, {'error': 'Không chạy được demo. Hãy chạy pytest để kiểm tra backend.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8088)
    parser.add_argument('--worker', choices=SHAPES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker, json.load(sys.stdin)), ensure_ascii=False))
        return
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'LogiX Lab demo: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
