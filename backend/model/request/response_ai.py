


from pydantic import BaseModel


class ResponseFromAI(BaseModel):
    table_name : str
    ids : list[str]
