from fastapi import APIRouter, Query
from fastapi import HTTPException, status

from core import SonolusRequest
from helpers.data_compilers import (
    compile_engines_list,
    compile_backgrounds_list,
    compile_effects_list,
    compile_particles_list,
    get_skins_for_locale,
)
from helpers.paginate import list_to_pages
from helpers.sonolus_typings import ItemType
from helpers.models.sonolus.response import ServerItemList

router = APIRouter()


@router.get("", response_model=ServerItemList)
async def main(
    request: SonolusRequest,
    item_type: ItemType,
    page: int = Query(0, ge=0),
):
    locale = request.state.loc
    source = request.app.base_url
    localization = request.state.localization

    match item_type:
        case "engines":
            data = [
                item.to_engine_item()
                for item in await request.app.run_blocking(
                    compile_engines_list, source, localization
                )
            ]
        case "skins":
            data = [
                item.to_skin_item()
                for item in await request.app.run_blocking(
                    get_skins_for_locale, source, localization
                )
            ]
        case "backgrounds":
            data = await request.app.run_blocking(compile_backgrounds_list, source)
        case "effects":
            data = await request.app.run_blocking(compile_effects_list, source)
        case "particles":
            data = await request.app.run_blocking(compile_particles_list, source)
        case _:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=locale.items_not_found(item_type),
            )

    pages = list_to_pages(data, request.app.get_items_per_page(item_type))
    if len(pages) == 0:
        return ServerItemList(pageCount=0, items=[])

    if page >= len(pages):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.not_found,
        )

    return ServerItemList(pageCount=len(pages), items=pages[page])
