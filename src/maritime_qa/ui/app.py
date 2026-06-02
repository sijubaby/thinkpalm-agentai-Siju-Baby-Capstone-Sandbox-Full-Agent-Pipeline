"""Entry point: starts the built-in web UI (re-exports server)."""

from maritime_qa.ui.server import start_server

main = start_server

if __name__ == "__main__":
    start_server()
