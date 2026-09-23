from pydantic import BaseModel,HttpUrl
from datetime import datetime

class UrlPayload(BaseModel):
    url: HttpUrl
    expires_at: datetime | None = None


