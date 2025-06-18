from http import HTTPStatus

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from fastapi_zero.schemas import Message

app = FastAPI(title='API')


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Olá mundo!'}


@app.get('/html', response_class=HTMLResponse)
async def home():
    return """
    <html>
      <head><title>FastApi do Zero</title></head>
      <body>
        <h1>Olá, Mundo!</h1>
        <p>Este é um HTML direto no FastAPI.</p>
      </body>
    </html>
    """
