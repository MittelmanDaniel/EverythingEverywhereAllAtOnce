"""Simple dev server that maps clean URLs to .html files."""
import http.server
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Strip query string for file lookup
        path = self.path.split("?")[0]
        # If no extension and not a file, try .html
        if "." not in os.path.basename(path):
            html_path = path.rstrip("/") + ".html"
            if os.path.isfile(html_path.lstrip("/")):
                self.path = html_path + ("?" + self.path.split("?")[1] if "?" in self.path else "")
        super().do_GET()

if __name__ == "__main__":
    port = 3000
    print(f"Serving on http://localhost:{port}")
    http.server.HTTPServer(("", port), CleanURLHandler).serve_forever()
