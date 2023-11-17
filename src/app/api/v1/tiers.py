from typing import Annotated

from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import fastapi

from app.schemas.tier import (
    TierRead,
    TierCreate,
    TierCreateInternal,
    TierUpdate
)
from app.api.dependencies import get_current_superuser
from app.core.database import async_get_db
from app.crud.crud_tier import crud_tiers
from app.api.paginated import PaginatedListResponse, paginated_response, compute_offset

router = fastapi.APIRouter(tags=["tiers"])

@router.post("/tier", dependencies=[Depends(get_current_superuser)], status_code=201)
async def write_tier(
    request: Request, 
    tier: TierCreate, 
    db: Annotated[AsyncSession, Depends(async_get_db)]
):  
    tier_internal_dict = tier.model_dump()
    db_tier = await crud_tiers.exists(db=db, name=tier_internal_dict["name"])
    if db_tier:
        raise HTTPException(status_code=400, detail="Tier Name not available")
    
    tier_internal = TierCreateInternal(**tier_internal_dict)
    return await crud_tiers.create(db=db, object=tier_internal)


@router.get("/tiers", response_model=PaginatedListResponse[TierRead])
async def read_tiers(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    items_per_page: int = 10
):
    tiers_data = await crud_tiers.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        schema_to_select=TierRead
    )

    return paginated_response(
        crud_data=tiers_data, 
        page=page, 
        items_per_page=items_per_page
    )


@router.get("/tier/{name}", response_model=TierRead)
async def read_tier(
    request: Request,
    name: str, 
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    db_tier = await crud_tiers.get(db=db, schema_to_select=TierRead, name=name)
    if db_tier is None:
        raise HTTPException(status_code=404, detail="Tier not found")

    return db_tier


@router.patch("/tier/{name}", dependencies=[Depends(get_current_superuser)])
async def patch_tier(
    request: Request, 
    values: TierUpdate,
    name: str,
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    db_tier = await crud_tiers.get(db=db, schema_to_select=TierRead, name=name)
    if db_tier is None:
        raise HTTPException(status_code=404, detail="Tier not found")
    
    await crud_tiers.update(db=db, object=values, name=name)
    return {"message": "Tier updated"}


@router.delete("/tier/{name}", dependencies=[Depends(get_current_superuser)])
async def erase_tier(
    request: Request,
    name: str, 
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    db_tier = await crud_tiers.get(db=db, schema_to_select=TierRead, name=name)
    if db_tier is None:
        raise HTTPException(status_code=404, detail="Tier not found")
    
    await crud_tiers.delete(db=db, db_row=db_tier, name=name)
    return {"message": "Tier deleted"}
