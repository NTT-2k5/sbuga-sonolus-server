from fastapi import APIRouter

from core import SonolusRequest
from helpers.data_compilers import (
    compile_engines_list,
    compile_backgrounds_list,
    compile_effects_list,
    compile_particles_list,
    get_skins_for_locale,
)
from helpers.models.sonolus.item_section import (
    SkinItemSection,
    BackgroundItemSection,
    EffectItemSection,
    ParticleItemSection,
    EngineItemSection,
)
from helpers.sonolus_typings import ItemType
from helpers.models.sonolus.response import ServerItemInfo

router = APIRouter()


@router.get("", response_model=ServerItemInfo)
async def main(request: SonolusRequest, item_type: ItemType):
    source = request.app.base_url
    localization = request.state.localization
    sections = []

    match item_type:
        case "engines":
            items = [
                item.to_engine_item()
                for item in await request.app.run_blocking(
                    compile_engines_list, source, localization
                )
            ]
            if items:
                sections.append(EngineItemSection(title="#ENGINE", items=items))
        case "skins":
            items = [
                item.to_skin_item()
                for item in await request.app.run_blocking(
                    get_skins_for_locale, source, localization
                )
            ]
            if items:
                sections.append(SkinItemSection(title="#SKIN", items=items))
        case "backgrounds":
            items = await request.app.run_blocking(compile_backgrounds_list, source)
            if items:
                sections.append(BackgroundItemSection(title="#BACKGROUND", items=items))
        case "effects":
            items = await request.app.run_blocking(compile_effects_list, source)
            if items:
                sections.append(EffectItemSection(title="#EFFECT", items=items))
        case "particles":
            items = await request.app.run_blocking(compile_particles_list, source)
            if items:
                sections.append(ParticleItemSection(title="#PARTICLE", items=items))

    return ServerItemInfo(sections=sections, banner=None)
