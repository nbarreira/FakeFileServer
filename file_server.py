from collections.abc import AsyncGenerator
import math
from time import sleep
from random import randbytes
import csv
import logging
import uuid

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse, PlainTextResponse
from pydantic_settings import BaseSettings
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format=f"%(levelname)-8s: %(message)s",
)
logger = logging.getLogger(__name__)


# File's filenames and sizes are stored in a dictionary as pairs key-value
files = dict()

# Stores the environment variables read at the server startup


class Settings(BaseSettings):
    fake_file_server_file: str = "./files.csv"

# Reads the file passed as an environment variable
# and generates the fake filesystem.
# This file should be a csv where each row stores the filename
# and the size  in bytes of a fake file.
# If the path does not exist the fake filesystem is empty.
# Rows with formatting issues are ignored.


def init_fake_file_system(filename: str):
    try:
        f = open(filename, "r")
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            try:
                files[row[0]] = int(row[1])
            except IndexError:
                logger.warning(f"Incorrect format at row {i+1}: {row}")
            except ValueError:
                logger.warning(f"Incorrect file size at row {i+1}: {row[1]}")
        f.close()
    except FileNotFoundError:
        logger.warning(f"File server empty: No such file {filename}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Loading fake server from file {settings.fake_file_server_file}")
    init_fake_file_system(settings.fake_file_server_file)
    logger.info(f"Fake file server loaded. Number of files: {len(files)}")
    yield
    print("unloaded on shutdown")

description = """
FakeFileServer API fakes an online file server

## Files
You will able to **get a file as a stream**. It only requires the filename. In order to **resume**
a previous download, the request must contain the *Range* header as follows:
```
Range: bytes=<start>-
```
where `<start>` is the byte from  which the download will resume. 
"""

settings = Settings()
app = FastAPI(
    title="FakeFileServer",
    description=description,
    version="0.0.1",
    lifespan=lifespan)



# Allow CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simulates reading a file in chunks by returning chunks of random bytes
# Note that the filename is not needed
async def simulate_read_file(request: Request, request_id: str, size: int, start: int, chunk_size: int = 1024 * 64) -> AsyncGenerator[bytes, None, None]:
    remaining = size - start
    client_disconnected = False
    logger.info(
        f"[{request_id}] Sending fake file: bytes = {size} | chunks = {math.floor(remaining/chunk_size) + int(remaining/chunk_size > 0)}")

    for i in range(math.floor(remaining/chunk_size)):
        logger.info(f"[{request_id}] Sending chunk {i}")

        sleep(0.05) # Uncomment this line to slow down the download

        # Checks if the client has paused/cancelled the download
        if await request.is_disconnected():
            logger.info(
                f"[{request_id}] Client disconnected: interrupting download")
            client_disconnected = True
            break

        # Returns a chunk of random bytes
        yield randbytes(chunk_size)

    last_chunk_size = remaining % chunk_size
    if not client_disconnected and last_chunk_size > 0:
        # Returns the remai ning bytes to complete the requested size
        logger.info(
            f"[{request_id}] Sending chunk {math.floor(remaining/chunk_size)}")
        yield randbytes(last_chunk_size)


@app.get("/file/stream",
         responses={
             200: {
                 "content": {"application/octet-stream": {}},
                 "description": "Return a file as a stream of bytes.",
             },
             206: {
                 "description": "Return part of a file as a stream of bytes.",
             },
             404: {
                 "description": "The file was not found.",
             }
         },
         )
async def stream_file(filename: str, request: Request) -> Response:
    if filename in files:
        # Checks if a partial read is requested (range header is present)
        range_header = request.headers.get("range")
        if range_header is not None:
            try:
                start = int(range_header[range_header.find(
                    "=")+1:range_header.find("-")].strip())
            except ValueError:
                start = 0  # If the format is incorrect, the streaming starts at the beginning of the file
        else:
            start = 0

        size = files[filename]

        # Default response headers
        response_headers = {
            "Content-Length": f"{size - start}",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Accept-Ranges": "bytes"
        }

        # Additional response header when part of the file was requested
        if start > 0:
            response_headers["Content-Range"] = f"bytes {start}-{size}/{size}"

        request_id = uuid.uuid4()  # For debbuging purpouses
        return StreamingResponse(
            simulate_read_file(request, request_id, size, start),
            media_type="application/octet-stream",
            status_code=200 if start == 0 else 206,
            headers=response_headers
        )
    else:
        return PlainTextResponse("File not found", status_code=404)
