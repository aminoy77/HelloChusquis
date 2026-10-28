"""Chunked request bodies must respect the 1 MiB cap (audit #13)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from core.http_limits import MAX_REQUEST_BODY_BYTES, RequestBodyLimitMiddleware


app = FastAPI()
app.add_middleware(RequestBodyLimitMiddleware)


@app.post("/echo")
async def echo(request: Request):
    body = await request.body()
    return {"size": len(body)}


client = TestClient(app)


class TestChunkedBodyLimit(unittest.TestCase):
    def test_small_chunked_body_passes(self):
        def gen():
            yield b"hello world"

        r = client.post("/echo", content=gen())  # no content-length -> chunked
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["size"], 11)

    def test_oversized_chunked_body_rejected(self):
        def gen():
            yield b"x" * (MAX_REQUEST_BODY_BYTES + 1)

        r = client.post("/echo", content=gen())
        self.assertEqual(r.status_code, 413)

    def test_content_length_path_still_enforced(self):
        r = client.post("/echo", content=b"x" * (MAX_REQUEST_BODY_BYTES + 1))
        self.assertEqual(r.status_code, 413)


if __name__ == "__main__":
    unittest.main()
