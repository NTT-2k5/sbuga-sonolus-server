from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from helpers.level_builder import get_converted_chart

router = APIRouter()


@router.get("")
async def main(chart_key: str):
    sep = chart_key.find("-")
    if sep < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="invalid chart key",
        )

    region = chart_key[:sep]
    chart_id = chart_key[sep + 1 :]

    try:
        converted, _ = await get_converted_chart(chart_id, region)
    except HTTPException:
        raise

    return Response(
        content=converted,
        media_type="application/octet-stream",
    )
