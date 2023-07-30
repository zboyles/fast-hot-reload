
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from fast_hot_reload import FastHotReload

change_me = "7.5"

app = FastAPI()

# add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# add a route to the app
@app.get("/")
async def root():
    # return basic html
    return HTMLResponse(
        content=f"""
        <html style='background-color:black;color:white;'>
            <head>
                <title>FastAPI Hot Reload</title>
            </head>
            <body>
                <h1>FastAPI Hot Reload</h1>
                <p>Welcome to the FastAPI Hot Reload demo!</p>
                <p>Change me: {change_me}</p>
            </body>
        </html>
        """
    )

FastHotReload(app=app, use_alternate_config=True)

