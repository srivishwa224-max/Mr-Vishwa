import concurrent.futures
import io
import json
import tempfile
import unittest
from pathlib import Path

from wsgi import Application


class ReleaseConcurrencyTests(unittest.TestCase):
    def test_concurrent_authenticated_reads_are_isolated_and_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            application = Application(Path(tmp) / "referdue.sqlite", "https://referdue.example")

            def request(path, body=None, cookie=""):
                raw = json.dumps(body).encode() if body is not None else b""
                environ = {
                    "REQUEST_METHOD": "POST" if body is not None else "GET",
                    "PATH_INFO": path,
                    "wsgi.url_scheme": "https",
                    "HTTP_HOST": "referdue.example",
                    "HTTP_ORIGIN": "https://referdue.example",
                    "HTTP_COOKIE": cookie,
                    "CONTENT_LENGTH": str(len(raw)),
                    "CONTENT_TYPE": "application/json",
                    "wsgi.input": io.BytesIO(raw),
                    "REMOTE_ADDR": "127.0.0.1",
                }
                response = {}

                def start_response(status, headers):
                    response.update(status=status, headers=dict(headers))

                response["body"] = b"".join(application(environ, start_response))
                return response

            registered = request(
                "/api/register",
                {"email": "load-test@example.com", "password": "synthetic-long-password"},
            )
            cookie = registered["headers"]["Set-Cookie"]
            account_mail = application.app().db.execute(
                "SELECT body FROM account_mail WHERE status='pending'"
            ).fetchone()[0]
            token = account_mail.split("#verify=")[1].split()[0]
            self.assertTrue(request("/api/verify-account", {"token": token})["status"].startswith("200"))
            created = request("/api/workspaces", {"name": "Concurrent sample"}, cookie)
            self.assertTrue(created["status"].startswith("200"))
            workspace_id = json.loads(created["body"])["id"]

            def read_workspace(_):
                response = request("/api/workspaces", cookie=cookie)
                return response["status"], json.loads(response["body"])

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(read_workspace, range(32)))

            self.assertTrue(all(status.startswith("200") for status, _ in results))
            for _, payload in results:
                self.assertEqual([[workspace_id, "Concurrent sample", "owner"]], payload["items"])

            if hasattr(application.local, "app"):
                application.local.app.store.close()


if __name__ == "__main__":
    unittest.main()
