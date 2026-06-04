import uvicorn
import webbrowser
from utils.globals import API_BIND_TO_ALL_IPS, API_PORT

HOST = "127.0.0.1"
if API_BIND_TO_ALL_IPS:
    HOST = "0.0.0.0"

if __name__ == "__main__":
    webbrowser.open_new(f"http://127.0.0.1:{API_PORT}")
    uvicorn.run("server.api:app", host=HOST, port=API_PORT, reload=False)
