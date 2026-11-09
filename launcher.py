import sys
import os
import time
import socket
import threading
import webbrowser

import uvicorn

from app import app


HOST = "127.0.0.1"
PORT = 8010

URL = f"http://{HOST}:{PORT}"


def wait_for_server():

    for _ in range(60):

        try:

            with socket.create_connection(
                (HOST, PORT),
                timeout=0.5
            ):

                webbrowser.open(
                    URL
                )

                return

        except OSError:

            time.sleep(
                0.25
            )


def main():

    print()
    print("=" * 50)
    print("DataForge AI")
    print("=" * 50)
    print()
    print(f"Starting DataForge at {URL}")
    print()
    print(
        "Keep this window open while "
        "using DataForge."
    )
    print()

    browser_thread = threading.Thread(
        target=wait_for_server,
        daemon=True
    )

    browser_thread.start()

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":

    main()