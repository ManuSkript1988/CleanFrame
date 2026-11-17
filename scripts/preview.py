"""Serve the actual TV UI and the retained design gallery on this Mac."""
import argparse
import io
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from font_assets import font_overlay

ROOT = Path(__file__).resolve().parents[1]


class PreviewServer(ThreadingHTTPServer):
    request_queue_size = 128
    mock_tv = False


MOCK_SCRIPT = ROOT / 'scripts/preview/tv-mock.js'
# Inserted before device.js only with --mock-tv. app/index.html itself is never changed.
MOCK_TAGS = b'<script src="/preview-mock/tv-mock.js"></script>\n<script>CleanFrameTVMock.preview();</script>\n'


class Preview(SimpleHTTPRequestHandler):
    def send_bytes(self, content, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        return io.BytesIO(content)

    def send_head(self):
        route = unquote(urlsplit(self.path).path)
        if self.server.mock_tv and route == '/preview-mock/tv-mock.js':
            return self.send_bytes(MOCK_SCRIPT.read_bytes(), 'text/javascript; charset=utf-8')
        if self.server.mock_tv and route in ['/home', '/home/', '/home/index.html']:
            page = (ROOT / 'app/index.html').read_bytes()
            marker = b'<script src="device.js"></script>'
            if marker not in page:
                self.send_error(500, 'device.js script tag not found')
                return None
            return self.send_bytes(page.replace(marker, MOCK_TAGS + marker, 1), 'text/html; charset=utf-8')
        if route in ['/home/assets/font-catalog.js', '/home/assets/private-fonts.css'] or route.startswith('/home/assets/private-fonts/'):
            source = font_overlay(include_private=self.server.include_private_fonts).get(route[len('/home/'):])
            if source is None:
                self.send_error(404, 'File not found')
                return None
            content = source.read_bytes() if isinstance(source, Path) else source
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(route))
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            return io.BytesIO(content)
        return super().send_head()

    def translate_path(self, path):
        route = urlsplit(path).path
        # Serve only the packaged UI and offline material-builder inputs.
        if route == '/' or route == '/home':
            return str(ROOT / 'app/index.html')
        if route.startswith('/home/'):
            self.directory = str(ROOT / 'app')
            return super().translate_path(route[5:])
        if route.startswith('/build/'):
            self.directory = str(ROOT / 'scripts/materials')
            return super().translate_path(route[6:])
        self.directory = str(ROOT / 'app')
        return super().translate_path(route)

    def do_GET(self):
        if urlsplit(self.path).path == '/':
            self.send_response(302)
            self.send_header('Location', '/home/')
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4795)
    parser.add_argument('--public-fonts', action='store_true', help='Use only the fonts distributed with the source')
    parser.add_argument('--mock-tv', action='store_true', help='Simulate HDMI inputs and app launches in this preview only; no TV is contacted')
    args = parser.parse_args()
    server = PreviewServer(('127.0.0.1', args.port), Preview)
    server.include_private_fonts = not args.public_fonts
    server.mock_tv = args.mock_tv
    print('CleanFrame preview: http://127.0.0.1:' + str(server.server_port) + '/home/' + (' (TV simulation; not a TV test)' if args.mock_tv else ''), flush=True)
    server.serve_forever()
