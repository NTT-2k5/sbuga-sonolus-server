from fastapi import APIRouter

from core import SonolusRequest
from helpers.data_compilers import compile_banner
from helpers.models.sonolus.misc import ServerInfoItemButton
from helpers.models.sonolus.options import (
    ServerSelectOption,
    ServerOption_Value,
    ServerToggleOption,
)
from helpers.models.sonolus.response import ServerInfo, ServerConfiguration

router = APIRouter()


@router.get("", response_model=ServerInfo)
async def main(request: SonolusRequest):
    locale = request.state.loc

    banner_srl = await request.app.run_blocking(compile_banner)

    button_list = [
        ServerInfoItemButton(type="level"),
        ServerInfoItemButton(type="playlist"),
        ServerInfoItemButton(
            type="post",
            title="#COLLABORATION",
            icon="award",
            infoType="collaboration",
        ),
        ServerInfoItemButton(type="skin"),
        ServerInfoItemButton(type="effect"),
        ServerInfoItemButton(type="particle"),
        ServerInfoItemButton(type="background"),
        ServerInfoItemButton(type="configuration"),
    ]

    options = [
        ServerToggleOption(
            query="showspoilers",
            name=locale.show_spoiler_charts,
            description=locale.show_spoiler_charts_desc,
            required=False,
            default=False,
        ),
        ServerSelectOption(
            query="levelbg",
            name="#BACKGROUND",
            required=False,
            default="v3",
            values=[
                ServerOption_Value(name="v3", title="PJSK V3"),
                ServerOption_Value(name="v1", title="PJSK V1"),
                ServerOption_Value(name="black", title="Black"),
            ],
        ),
    ]

    desc = locale.server_description

    return ServerInfo(
        title=request.app.config["name"],
        description=desc,
        buttons=button_list,
        configuration=ServerConfiguration(options=options),
        banner=banner_srl if banner_srl else None,
    )
