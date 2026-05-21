from uuid import UUID

from .base_model import BaseModel


class TestingCreateOrg(BaseModel):
    org_create: "TestingCreateOrgOrgCreate"


class TestingCreateOrgOrgCreate(BaseModel):
    uuid: UUID


TestingCreateOrg.update_forward_refs()
TestingCreateOrgOrgCreate.update_forward_refs()
