"""Authomize connector for Bamboo HR"""
from connectors import Base

CONNECTOR_ID = "bamboo-hr"


class Connector(Base):
    """Authomize connector for Bamboo HR"""

    def __init__(self):
        super().__init__(CONNECTOR_ID)
