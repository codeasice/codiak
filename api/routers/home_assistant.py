from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.services import home_assistant_service

router = APIRouter()


@router.get("/sensors")
def get_sensors(entity_filter: str = "", device_class: str = ""):
    try:
        return home_assistant_service.get_sensors(entity_filter, device_class)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Home Assistant error: {e}")


@router.get("/entities")
def get_entities():
    try:
        return home_assistant_service.get_grouped_entities()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Home Assistant error: {e}")


class ServiceCall(BaseModel):
    entity_id: str


@router.post("/services/{domain}/{service}")
def call_service(domain: str, service: str, body: ServiceCall):
    try:
        return home_assistant_service.call_service(domain, service, body.entity_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Home Assistant error: {e}")
