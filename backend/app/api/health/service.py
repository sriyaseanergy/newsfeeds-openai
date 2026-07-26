from app.api.health.schemas import HealthResponse


class HealthService:
    @staticmethod
    def get_health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            version="0.1.0",
        )
