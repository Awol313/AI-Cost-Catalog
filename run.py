import uvicorn

if __name__ == "__main__":
    # Port 8001 so this can run alongside the Brand Visibility Tracker on 8000.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)
