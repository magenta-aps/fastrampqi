#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from typing import Any
from typing import Dict
from typing import Type

from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from ramodels.lora import Facet
from ramodels.lora import ITSystem
from ramodels.lora import Klasse
from ramodels.lora import Organisation
from ramodels.lora._shared import LoraBase

from .base import ModelClientBase


class ModelClient(ModelClientBase[LoraBase]):
    """LoRa ModelClient.

    Example usage::

        async with ModelClient(
            base_url="http://mox:8080",
            client_id="AzureDiamond",
            client_secret="hunter2",
            auth_server=parse_obj_as(AnyHttpUrl,"https://keycloak.example.org/auth"),
            auth_realm="mordor",
        ) as client:
            r = await client.upload(objects)
    """

    upload_http_method = "PUT"
    path_map: Dict[Type[LoraBase], str] = {
        Facet: "/klassifikation/facet",
        ITSystem: "/organisation/itsystem",
        Klasse: "/klassifikation/klasse",
        Organisation: "/organisation/organisation",
    }
    async_httpx_client_class = AsyncClient

    def get_object_url(self, obj: LoraBase, *args: Any, **kwargs: Any) -> str:
        return "{}/{}".format(self.path_map[type(obj)], obj.uuid)

    def get_object_json(self, obj: LoraBase, *args: Any, **kwargs: Any) -> Any:
        # TODO: Pending https://github.com/samuelcolvin/pydantic/pull/2231. For now,
        #  UUID is included in the model, and has to be excluded when converted to JSON.
        return jsonable_encoder(
            obj=obj, by_alias=True, exclude={"uuid"}, exclude_none=True
        )
