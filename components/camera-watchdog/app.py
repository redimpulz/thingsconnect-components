"""RTSP カメラを定期的に覗いて、死活と画質の異常を判定する常駐エージェント。

環境変数:
  CAMERAS      "名前=rtsp://..." を ';' で連結（必須）
  INTERVAL_SEC 巡回間隔（既定 60）
  PORT         最新状態を返す HTTP ポート（既定 8080）
"""

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

W, H = 64, 36  # 判定用に落とす解像度。小さいほど CPU を使わない
PIXELS = W * H

DARK_MAX = 25.0  # これ未満は暗すぎ（レンズ遮蔽・消灯）
BRIGHT_MIN = 230.0  # これ超えは白飛び（逆光・照明直撃）
FROZEN_MAX = 0.2  # 前回との差がこれ未満なら映像が止まっている

started = time.time()
latest: dict[str, dict] = {}
checks = 0
lock = threading.Lock()


def grab(url: str) -> tuple[bytes | None, str | None]:
    """RTSP から 1 フレームだけ取り、グレースケールの生データとして返す。"""
    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-rtsp_transport', 'tcp',
        '-timeout', '10000000',  # ソケットのタイムアウト（マイクロ秒）
        '-i', url,
        '-frames:v', '1',
        '-vf', f'scale={W}:{H}',
        '-pix_fmt', 'gray',
        '-f', 'rawvideo', '-',
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=45)
    except subprocess.TimeoutExpired:
        return None, 'ffmpeg がタイムアウトしました'
    if p.returncode != 0 or len(p.stdout) < PIXELS:
        # メモリ上限を超えるとログを残さず強制終了されるので、終了コードで見分ける
        if p.returncode == 137:
            return None, 'ffmpeg が強制終了しました（メモリ上限の可能性）'
        err = p.stderr.decode('utf-8', 'replace').strip().splitlines()
        return None, (err[-1][:200] if err else 'フレームを取得できませんでした')
    return p.stdout[:PIXELS], None


def analyse(cur: bytes, prev: bytes | None) -> tuple[float, float | None, str]:
    brightness = sum(cur) / PIXELS
    diff = None
    if prev is not None and len(prev) == PIXELS:
        diff = sum(abs(a - b) for a, b in zip(cur, prev)) / PIXELS

    if brightness < DARK_MAX:
        status = 'dark'
    elif brightness > BRIGHT_MIN:
        status = 'bright'
    elif diff is not None and diff < FROZEN_MAX:
        status = 'frozen'
    else:
        status = 'ok'
    return brightness, diff, status


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):  # noqa: N802
        if self.path.rstrip('/') not in ('', '/status'):
            self.send_error(404)
            return
        with lock:
            body = json.dumps(
                {'uptimeSec': int(time.time() - started), 'checks': checks, 'cameras': latest},
                ensure_ascii=False,
                indent=2,
            ).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def serve(port: int) -> None:
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()


def parse_cameras(raw: str) -> list[tuple[str, str]]:
    out = []
    for entry in raw.split(';'):
        name, sep, url = entry.strip().partition('=')
        if not sep:
            raise ValueError(f'CAMERAS の書式が不正です: {entry}')
        out.append((name.strip(), url.strip()))
    return out


def main() -> None:
    raw = os.environ.get('CAMERAS', '').strip()
    if not raw:
        print('CAMERAS が未設定です', file=sys.stderr)
        sys.exit(1)
    cameras = parse_cameras(raw)
    interval = int(os.environ.get('INTERVAL_SEC', '60'))
    port = int(os.environ.get('PORT', '8080'))

    threading.Thread(target=serve, args=(port,), daemon=True).start()
    print(f'[watchdog] 起動: cameras={[n for n, _ in cameras]} interval={interval}s', flush=True)

    prev: dict[str, bytes] = {}
    global checks
    # 自分で終了せず回り続ける。終了したときの扱いは保証されていない
    while True:
        cycle_started = time.time()
        for name, url in cameras:
            frame, err = grab(url)
            ts = time.strftime('%Y-%m-%dT%H:%M:%S%z')
            if frame is None:
                record = {'ts': ts, 'status': 'unreachable', 'brightness': None, 'diff': None, 'error': err}
            else:
                brightness, diff, status = analyse(frame, prev.get(name))
                prev[name] = frame
                record = {
                    'ts': ts,
                    'status': status,
                    'brightness': round(brightness, 1),
                    'diff': None if diff is None else round(diff, 2),
                    'error': None,
                }
            with lock:
                latest[name] = record
                checks += 1
            # 標準出力はそのままエッジPC のログに残る
            print(json.dumps({'camera': name, **record}, ensure_ascii=False), flush=True)

        time.sleep(max(1.0, interval - (time.time() - cycle_started)))


if __name__ == '__main__':
    main()
