from pydantic import BaseModel, ConfigDict


class ORMReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
