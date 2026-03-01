from pydantic import BaseModel


class ConnectionStatus(BaseModel):
    service: str
    status: str
    last_collected_at: str | None = None


class ConnectionsResponse(BaseModel):
    connections: list[ConnectionStatus]
