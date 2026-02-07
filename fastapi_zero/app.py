from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fastapi_zero.api.routes.cart import router as cart_router
from fastapi_zero.api.routes.scrape import router as scrape_router
from fastapi_zero.api.routes.users import router as users_router
from fastapi_zero.schemas import Message

app = FastAPI(title='API')

app.mount(
    '/static', StaticFiles(directory='fastapi_zero/static'), name='static'
)
templates = Jinja2Templates(directory='fastapi_zero/templates')

app.include_router(users_router)
app.include_router(scrape_router)
app.include_router(cart_router)


@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    return FileResponse('fastapi_zero/static/favicon.svg', media_type='image/svg+xml')


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Olá mundo!'}


@app.get('/ui', response_class=HTMLResponse)
def ui_home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})
