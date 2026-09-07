# FakeFileServer
A fake file server that returns streams of bytes as fake files

## Installation

1. Download the repository
2. Install the dependencies

```bash
pip install -r requirements.txt
```

## Run server

- Debug mode

```
FAKE_FILE_SERVER_FILE=<CSV_FILE> fastapi dev file_server.py
```

- Production mode

```
FAKE_FILE_SERVER_FILE=<CSV_FILE> fastapi run file_server.py
```

where `<CSV_FILE>` is the path to a CSV file that contains a list of fake files and their sizes. 
The format of this file is for each row:
```
filename,filesize
```
where `filesize` represents the size of the file in bytes.

If the environment variable `FAKE_FILE_SERVER_FILE` is not set, the server tries to load `files.csv`. If the csv file is not found, an empty file server is created.
