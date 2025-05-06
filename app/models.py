from sqlalchemy import Column, Integer, String, Boolean, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

class Sex(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    sex = Column(Enum(Sex))
    nationality = Column(String)
    organization_name = Column(String)
    job_title = Column(String)
    birthdate = Column(Date)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True) 