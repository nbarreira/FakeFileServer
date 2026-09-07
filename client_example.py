import requests

if __name__ == "__main__":

    print("TEST 1 -- DOWNLOAD A FILE THAT DOES NOT EXIST")
    response = requests.get("http://localhost:8000/file/stream?filename=xx", 
                            stream=True)
    print(f"[File not found] Response ok = {response.ok}")
    print(f"[File not found] Response status code = {response.status_code}")
    print(f"[File not found] Response text = {response.text}")

    print("TEST 2 -- DOWNLOAD CORRECTLY A FILE")
    response = requests.get("http://localhost:8000/file/stream?filename=glib-2.82.4.tar.xz", 
                            stream=True)
    print(f"[Download file] Response ok = {response.ok}")
    print(f"[Download file] Response status code = {response.status_code}")
    print(f"[Download file] Response headers = {response.headers}")
    print("[Download file] Saving file to disk")
    with open('tmp.tar.xz', 'wb') as f:
        for i, chunk in enumerate(response.iter_content(chunk_size=1024*64)):
            print(f"[Download file] Received chunk {i}")
            f.write(chunk)
        f.close()

    print("TEST 3 -- INTERRUPTING A DOWNLOAD")
    response = requests.get("http://localhost:8000/file/stream?filename=gdk-pixbuf-2.42.12.tar.xz", 
                            stream=True)
    print(f"[Interrupt download] Response ok = {response.ok}")
    print(f"[Interrupt download] Response status code = {response.status_code}")
    print(f"[Interrupt download] Response headers = {response.headers}")
    print("[Interrupt download] Saving file to disk")
    with open('tmp2.tar.xz', 'wb') as f:
        for i, chunk in enumerate(response.iter_content(chunk_size=1024*64)):
            print(f"[Interrupt download] Received chunk {i}")
            f.write(chunk)
            break
        f.close()


    print("TEST 4 -- RESUMING A DOWNLOAD")
    headers = {
             "Range": f"bytes={1024*64}-"
    }
    response = requests.get("http://localhost:8000/file/stream?filename=gdk-pixbuf-2.42.12.tar.xz", 
                             stream=True,
                             headers=headers)
    print(f"[Resume download] Response ok = {response.ok}")
    print(f"[Resume download] Response status code = {response.status_code}")
    print(f"[Resume download] Response headers = {response.headers}")
    print("[Resume download] Saving file to disk")
    with open('tmp2.tar.xz', 'ab') as f:
        for i, chunk in enumerate(response.iter_content(chunk_size=1024*64)):
            print(f"[Resume download] Received chunk {i}")
            f.write(chunk)
        f.close()
    
