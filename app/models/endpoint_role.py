# app/models/endpoint_role.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class EndpointRole(Base):
    __tablename__ = "endpoint_roles"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_name = Column(String, index=True)  
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role")

    def __repr__(self):
        return f"<EndpointRole(endpoint_name='{self.endpoint_name}', role_id={self.role_id})>"
