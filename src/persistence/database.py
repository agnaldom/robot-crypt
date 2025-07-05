"""
Abstract database interface.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union

from core.logging_setup import logger

T = TypeVar('T')


class DatabaseException(Exception):
    """Exception raised for database errors."""
    pass


class Database(ABC, Generic[T]):
    """
    Abstract database interface.
    Defines the contract for database implementations.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the database.
        
        Raises:
            DatabaseException: If connection fails.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to the database.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connection to database is active.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        pass

    @abstractmethod
    def create(self, collection: str, data: Union[Dict[str, Any], T]) -> str:
        """
        Create a new document/record.
        
        Args:
            collection (str): Collection/table name.
            data (Union[Dict[str, Any], T]): Data to insert.
        
        Returns:
            str: ID of the created document/record.
        
        Raises:
            DatabaseException: If creation fails.
        """
        pass

    @abstractmethod
    def read(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a document/record by ID.
        
        Args:
            collection (str): Collection/table name.
            document_id (str): Document/record ID.
        
        Returns:
            Optional[Dict[str, Any]]: Document/record data, or None if not found.
        
        Raises:
            DatabaseException: If read fails.
        """
        pass

    @abstractmethod
    def update(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a document/record.
        
        Args:
            collection (str): Collection/table name.
            document_id (str): Document/record ID.
            data (Dict[str, Any]): Data to update.
        
        Returns:
            bool: True if update was successful, False otherwise.
        
        Raises:
            DatabaseException: If update fails.
        """
        pass

    @abstractmethod
    def delete(self, collection: str, document_id: str) -> bool:
        """
        Delete a document/record.
        
        Args:
            collection (str): Collection/table name.
            document_id (str): Document/record ID.
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        
        Raises:
            DatabaseException: If deletion fails.
        """
        pass

    @abstractmethod
    def query(self, collection: str, query: Dict[str, Any], sort: Optional[Dict[str, Any]] = None, 
              limit: Optional[int] = None, skip: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query documents/records.
        
        Args:
            collection (str): Collection/table name.
            query (Dict[str, Any]): Query criteria.
            sort (Optional[Dict[str, Any]], optional): Sort criteria. Defaults to None.
            limit (Optional[int], optional): Maximum number of results. Defaults to None.
            skip (Optional[int], optional): Number of results to skip. Defaults to None.
        
        Returns:
            List[Dict[str, Any]]: Query results.
        
        Raises:
            DatabaseException: If query fails.
        """
        pass

    @abstractmethod
    def create_collection(self, collection: str) -> bool:
        """
        Create a new collection/table.
        
        Args:
            collection (str): Collection/table name.
        
        Returns:
            bool: True if creation was successful, False otherwise.
        
        Raises:
            DatabaseException: If creation fails.
        """
        pass

    @abstractmethod
    def delete_collection(self, collection: str) -> bool:
        """
        Delete a collection/table.
        
        Args:
            collection (str): Collection/table name.
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        
        Raises:
            DatabaseException: If deletion fails.
        """
        pass

    @abstractmethod
    def collection_exists(self, collection: str) -> bool:
        """
        Check if a collection/table exists.
        
        Args:
            collection (str): Collection/table name.
        
        Returns:
            bool: True if collection exists, False otherwise.
        """
        pass
