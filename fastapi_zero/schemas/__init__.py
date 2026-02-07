from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from .cart import AddToCartRequest, CartItemPublic, CartResponse


class Message(BaseModel):
    message: str


class UserSchema(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    username: str
    email: EmailStr
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    users: list[UserPublic]


class ScrapeUrlsRequest(BaseModel):
    urls: list[HttpUrl]
    category: str | None = None
    max_concurrency: int = Field(default=20, ge=1, le=200)


class ScrapedItemPublic(BaseModel):
    url: HttpUrl
    title: str | None
    price: float | None
    currency: str | None


class ProductBestPrice(BaseModel):
    product_id: int
    name: str
    category: str | None
    lowest_price: float
    currency: str | None
    source_url: HttpUrl


class ScrapeResult(BaseModel):
    total_scraped: int
    total_saved: int
    products: list[ProductBestPrice]
    raw_items: list[ScrapedItemPublic]


class CrawlRequest(BaseModel):
    base_url: HttpUrl
    max_urls: int = Field(default=1000, ge=1, le=20000)
    max_concurrency: int = Field(default=10, ge=1, le=200)
    include_patterns: list[str] | None = None
    exclude_patterns: list[str] | None = None
    use_sitemap: bool = True
    follow_links: bool = False
    max_depth: int = Field(default=1, ge=0, le=5)


class CrawlResponse(BaseModel):
    total_urls: int
    urls: list[HttpUrl]


class SearchCrawlRequest(BaseModel):
    search_url: HttpUrl
    query: str | None = None
    max_pages: int = Field(default=5, ge=1, le=50)
    max_urls: int = Field(default=500, ge=1, le=20000)
    max_concurrency: int = Field(default=5, ge=1, le=50)
    include_patterns: list[str] | None = None
    exclude_patterns: list[str] | None = None


class SearchCrawlResponse(BaseModel):
    total_urls: int
    urls: list[HttpUrl]


__all__ = [
    'Message',
    'UserSchema',
    'UserPublic',
    'UserList',
    'ScrapeUrlsRequest',
    'ScrapedItemPublic',
    'ProductBestPrice',
    'ScrapeResult',
    'CrawlRequest',
    'CrawlResponse',
    'SearchCrawlRequest',
    'SearchCrawlResponse',
    'AddToCartRequest',
    'CartItemPublic',
    'CartResponse',
]
