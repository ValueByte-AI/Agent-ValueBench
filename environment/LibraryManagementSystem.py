# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional



class BookInfo(TypedDict):
    book_id: str
    title: str
    author: str
    publisher: str
    year: int
    genre: str
    status: str  # 'available' or 'on_loan'
    location: str

class PatronInfo(TypedDict):
    patron_id: str
    name: str
    contact_details: str
    account_status: str

class LoanRecordInfo(TypedDict):
    loan_id: str
    book_id: str
    patron_id: str
    checkout_date: str  # ISO date string
    due_date: str       # ISO date string
    return_date: Optional[str]  # ISO date string or None
    status: str         # e.g., 'active', 'returned', 'overdue'

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Library Management System stateful environment.
        Attributes reflect entities:
        - books: all books/resources in the collection
        - patrons: all library users
        - loan_records: records of book loans
        """

        # Books: {book_id: BookInfo}
        self.books: Dict[str, BookInfo] = {}

        # Patrons: {patron_id: PatronInfo}
        self.patrons: Dict[str, PatronInfo] = {}

        # Loan records: {loan_id: LoanRecordInfo}
        self.loan_records: Dict[str, LoanRecordInfo] = {}

        # Constraints:
        # - Books cannot be removed if they are currently on loan (status ≠ available).
        # - Each book must have a unique book_id.
        # - LoanRecords must refer to valid book_id and patron_id.
        # - Only books present in the collection can be deleted.
        # - Removal of a book must also update or invalidate related LoanRecords if present.

    def get_book_by_id(self, book_id: str) -> dict:
        """
        Retrieve detailed information for a specific book using its book_id.

        Args:
            book_id (str): Unique identifier for the book.

        Returns:
            dict: 
                { "success": True, "data": BookInfo }
                OR
                { "success": False, "error": "Book not found" }
        Constraints:
            - The book_id must exist in the collection.
        """
        if book_id not in self.books:
            return { "success": False, "error": "Book not found" }
        return { "success": True, "data": self.books[book_id] }

    def list_books(self) -> dict:
        """
        Retrieve a list of all books in the collection.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BookInfo]  # List of all books in the library (empty if none)
            }
        """
        all_books = list(self.books.values())
        return { "success": True, "data": all_books }

    def get_book_status(self, book_id: str) -> dict:
        """
        Retrieve the current status ('available' or 'on_loan') of a book by its ID.

        Args:
            book_id (str): The unique identifier for the book.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": {
                        "book_id": str,
                        "status": str  # 'available' or 'on_loan'
                    }
                }
                - On failure: {
                    "success": False,
                    "error": "Book not found"
                }

        Constraints:
            - The book_id must exist in the system.
        """
        book = self.books.get(book_id)
        if not book:
            return {"success": False, "error": "Book not found"}
        return {"success": True, "data": {"book_id": book_id, "status": book["status"]}}

    def list_books_by_status(self, status: str) -> dict:
        """
        List all books filtered by their status.

        Args:
            status (str): The status to filter books by. Must be either 'available' or 'on_loan'.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": List[BookInfo]  # List of books with the given status
                  }
                - On error (invalid status): {
                      "success": False,
                      "error": "Invalid status: must be 'available' or 'on_loan'."
                  }

        Constraints:
            - Only supports status 'available' or 'on_loan'.
            - No side effects; information query only.
        """
        valid_statuses = {"available", "on_loan"}
        if status not in valid_statuses:
            return {
                "success": False,
                "error": "Invalid status: must be 'available' or 'on_loan'."
            }

        matching_books = [
            book_info for book_info in self.books.values() if book_info["status"] == status
        ]
        return {
            "success": True,
            "data": matching_books
        }

    def get_loan_records_for_book(self, book_id: str) -> dict:
        """
        Retrieve all loan records (LoanRecordInfo) associated with the given book_id.

        Args:
            book_id (str): The unique identifier for the book.

        Returns:
            dict: {
                "success": True,
                "data": List[LoanRecordInfo],  # List may be empty if no records
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g. book does not exist
            }

        Constraints:
            - Only books present in the collection can be queried.
        """
        if book_id not in self.books:
            return {"success": False, "error": "Book does not exist"}

        records = [
            record for record in self.loan_records.values()
            if record["book_id"] == book_id
        ]
        return {"success": True, "data": records}

    def get_patron_by_id(self, patron_id: str) -> dict:
        """
        Retrieve detailed information for a specific patron using patron_id.

        Args:
            patron_id (str): The unique identifier of the patron.

        Returns:
            dict: {
                "success": True,
                "data": PatronInfo  # Patron metadata if patron exists
            }
            or
            {
                "success": False,
                "error": str  # Error message if patron does not exist
            }

        Constraints:
            - patron_id must exist in the system for success.
        """
        patron_info = self.patrons.get(patron_id)
        if patron_info is None:
            return { "success": False, "error": "Patron not found" }
        return { "success": True, "data": patron_info }

    def get_loan_record_by_id(self, loan_id: str) -> dict:
        """
        Retrieve details for a specific loan record using the provided loan_id.

        Args:
            loan_id (str): Identifier of the loan record.

        Returns:
            dict:
                On success: { "success": True, "data": LoanRecordInfo }
                On failure: { "success": False, "error": "Loan record not found" }
        """
        loan_record = self.loan_records.get(loan_id)
        if not loan_record:
            return { "success": False, "error": "Loan record not found" }
        return { "success": True, "data": loan_record }

    def list_active_loans_for_book(self, book_id: str) -> dict:
        """
        List all active loan records for a given book.
    
        Args:
            book_id (str): The unique identifier of the book to query.
    
        Returns:
            dict: 
              On success:
                {
                  "success": True,
                  "data": List[LoanRecordInfo]  # Active ('active' or 'overdue') loans for this book
                }
              On error:
                {
                  "success": False,
                  "error": "Book does not exist"
                }
        Constraints:
            - book_id must exist in the collection; otherwise, operation fails.
            - "Active" means loan record status is 'active' or 'overdue'.
        """
        if book_id not in self.books:
            return { "success": False, "error": "Book does not exist" }

        result = [
            loan_info for loan_info in self.loan_records.values()
            if loan_info["book_id"] == book_id and loan_info["status"] in ("active", "overdue")
        ]
        return { "success": True, "data": result }

    def list_all_loan_records(self) -> dict:
        """
        Retrieve all loan records currently in the library system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LoanRecordInfo]  # List of all loan records (may be empty)
            }
        """
        all_loan_records = list(self.loan_records.values())
        return {"success": True, "data": all_loan_records}

    def remove_book(self, book_id: str) -> dict:
        """
        Permanently delete a book from the library collection after validating all constraints.

        Args:
            book_id (str): The unique identifier of the book to be removed.

        Returns:
            dict: On success:
                      { "success": True, "message": "Book <book_id> removed and related loan records invalidated" }
                  On failure:
                      { "success": False, "error": <str> }

        Constraints:
            - The book must exist.
            - The book must have status 'available' (not on loan).
            - All related loan records (if any) must be invalidated (their 'status' set to 'invalidated').
        """
        # Check if book exists
        book = self.books.get(book_id)
        if not book:
            return {"success": False, "error": "Book not found"}
    
        # Check if book is available (not on loan)
        if book["status"] != "available":
            return {"success": False, "error": "Book cannot be removed because it is currently on loan"}

        # Remove the book from collection
        del self.books[book_id]

        # Invalidate related loan records
        related_records = 0
        for record in self.loan_records.values():
            if record["book_id"] == book_id and record["status"] != "invalidated":
                record["status"] = "invalidated"
                related_records += 1

        return {
            "success": True,
            "message": f"Book {book_id} removed and {related_records} related loan records invalidated"
        }

    def update_loan_record_status(self, book_id: str, new_status: str) -> dict:
        """
        Update the status field of all loan records associated with the given book_id.

        Args:
            book_id (str): The unique identifier of the book whose loan records will be updated.
            new_status (str): The new status to set for each loan record (e.g., 'invalidated', 'cancelled').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Updated status of N loan records for book_id X to 'Y'"
                    }
                    (or, if no records)
                    {
                        "success": True,
                        "message": "No loan records found for book_id X."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Book with id X does not exist."
                    }

        Constraints:
            - Book with book_id must exist.
            - Only the status field in LoanRecordInfo is updated.
        """
        if book_id not in self.books:
            return {
                "success": False,
                "error": f"Book with id {book_id} does not exist."
            }

        updated_count = 0
        for record in self.loan_records.values():
            if record["book_id"] == book_id:
                record["status"] = new_status
                updated_count += 1

        if updated_count == 0:
            return {
                "success": True,
                "message": f"No loan records found for book_id {book_id}."
            }
        else:
            return {
                "success": True,
                "message": f"Updated status of {updated_count} loan records for book_id {book_id} to '{new_status}'."
            }

    def invalidate_loan_records_for_book(self, book_id: str) -> dict:
        """
        Mark all loan records for the specified book as invalid or update their state accordingly.

        Args:
            book_id (str): The unique identifier of the book whose loan records should be invalidated.

        Returns:
            dict: {
                "success": True,
                "message": "All loan records for book <book_id> have been invalidated or updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The book_id must exist in the system.
            - Only loan records with book_id matching the input should be affected.
        """
        if book_id not in self.books:
            return {"success": False, "error": f"Book with id '{book_id}' does not exist."}

        affected = 0
        for loan_record in self.loan_records.values():
            if loan_record["book_id"] == book_id:
                loan_record["status"] = "invalidated"
                affected += 1

        return {
            "success": True,
            "message": f"All loan records for book '{book_id}' have been invalidated or updated."
        }

    def add_book(
        self,
        book_id: str,
        title: str,
        author: str,
        publisher: str,
        year: int,
        genre: str,
        status: str,
        location: str
    ) -> dict:
        """
        Add a new book to the collection with all required attributes, ensuring a unique book_id.

        Args:
            book_id (str): Unique identifier for the book.
            title (str): Title of the book.
            author (str): Author of the book.
            publisher (str): Publisher of the book.
            year (int): Year of publication.
            genre (str): Genre/category of the book.
            status (str): 'available' or 'on_loan'.
            location (str): Physical or logical location in the library.

        Returns:
            dict: 
            - On success: { "success": True, "message": "Book <book_id> added." }
            - On error:   { "success": False, "error": "Reason for failure." }

        Constraints:
            - book_id must be unique.
            - All fields must be provided.
        """
        # Validate uniqueness of book_id
        if book_id in self.books:
            return { "success": False, "error": f"Book with book_id '{book_id}' already exists." }
    
        # Basic value checks (fall back to general error for missing field/type issues)
        if not all([book_id, title, author, publisher, isinstance(year, int), genre, status, location]):
            return { "success": False, "error": "One or more required fields are missing or of incorrect type." }
    
        if status not in ["available", "on_loan"]:
            return { "success": False, "error": "Status must be either 'available' or 'on_loan'." }

        # Create and store new book
        self.books[book_id] = {
            "book_id": book_id,
            "title": title,
            "author": author,
            "publisher": publisher,
            "year": year,
            "genre": genre,
            "status": status,
            "location": location
        }

        return { "success": True, "message": f"Book '{book_id}' added." }

    def update_book_info(self, book_id: str, updates: dict) -> dict:
        """
        Modify metadata or status for an existing book.

        Args:
            book_id (str): The unique identifier of the book to update.
            updates (dict): Dictionary of field names (str) and new values to update.
                            Allowed fields: 'title', 'author', 'publisher', 'year',
                            'genre', 'status', 'location'.

        Returns:
            dict: {
                "success": True,
                "message": "Book info updated for book_id: <book_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Book must exist (book_id in self.books).
            - book_id cannot be changed via this operation.
            - Only mutable fields can be updated.
        """
        if book_id not in self.books:
            return {"success": False, "error": "Book with this book_id does not exist"}

        allowed_fields = {"title", "author", "publisher", "year", "genre", "status", "location"}
        if not updates:
            return {"success": False, "error": "No fields provided for update"}

        if "book_id" in updates:
            return {"success": False, "error": "Updating book_id is not allowed"}

        # Only update valid fields
        updated = False
        for field, value in updates.items():
            if field in allowed_fields:
                self.books[book_id][field] = value
                updated = True
            else:
                # If any field is invalid, reject the whole update
                return {"success": False, "error": f"Invalid field '{field}' for update"}

        if not updated:
            return {"success": False, "error": "No valid fields provided for update"}

        return {"success": True, "message": f"Book info updated for book_id: {book_id}"}

    def add_loan_record(
        self,
        loan_id: str,
        book_id: str,
        patron_id: str,
        checkout_date: str,
        due_date: str,
        return_date: 'Optional[str]',
        status: str
    ) -> dict:
        """
        Add a new loan record after validating the referenced book and patron exist.

        Args:
            loan_id (str): Unique loan record identifier.
            book_id (str): ID of the book being loaned.
            patron_id (str): ID of the patron borrowing the book.
            checkout_date (str): The checkout date (ISO string).
            due_date (str): Book due date (ISO string).
            return_date (Optional[str]): Return date (ISO string) or None.
            status (str): Loan status ('active', 'returned', 'overdue', etc.).

        Returns:
            dict: 
                On success: { "success": True, "message": "Loan record added successfully." }
                On error: { "success": False, "error": <reason> }

        Constraints:
            - loan_id must be unique among loan_records.
            - book_id must exist in books.
            - patron_id must exist in patrons.
            - LoanRecords must refer to valid book_id and patron_id.
        """

        # Check for uniqueness of loan_id
        if loan_id in self.loan_records:
            return {"success": False, "error": "Loan record with this loan_id already exists."}
    
        # Validate book_id exists
        if book_id not in self.books:
            return {"success": False, "error": "Book with provided book_id does not exist."}
    
        # Validate patron_id exists
        if patron_id not in self.patrons:
            return {"success": False, "error": "Patron with provided patron_id does not exist."}

        # (OPTIONAL, not in constraints: check book is available for loan)
        # if self.books[book_id]["status"] != "available":
        #     return {"success": False, "error": "Book is not available for loan."}

        # Add the LoanRecord
        new_loan: LoanRecordInfo = {
            "loan_id": loan_id,
            "book_id": book_id,
            "patron_id": patron_id,
            "checkout_date": checkout_date,
            "due_date": due_date,
            "return_date": return_date,
            "status": status
        }
        self.loan_records[loan_id] = new_loan

        return {"success": True, "message": "Loan record added successfully."}

    def remove_loan_record(self, loan_id: str) -> dict:
        """
        Delete or archive a loan record from the system.

        Args:
            loan_id (str): The unique identifier of the loan record to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Loan record removed."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The loan record must exist in the system.
            - No restrictions based on status: any loan record (active, returned, or overdue) may be removed.
        """
        if loan_id not in self.loan_records:
            return { "success": False, "error": "Loan record does not exist." }

        del self.loan_records[loan_id]
        return { "success": True, "message": "Loan record removed." }

    def update_patron_info(
        self,
        patron_id: str,
        name: str = None,
        contact_details: str = None,
        account_status: str = None
    ) -> dict:
        """
        Modify information or account status for a library patron.

        Args:
            patron_id (str): The unique ID for the patron to update.
            name (str, optional): The new name for the patron.
            contact_details (str, optional): Updated contact information.
            account_status (str, optional): New account status (e.g., 'active', 'suspended').

        Returns:
            dict: {
                "success": True,
                "message": "Patron information updated successfully."
            }
            or
            {
                "success": False,
                "error": "Patron not found."
            }

        Constraints:
            - Patron must exist.
            - Only the specified fields are updated.
        """
        if patron_id not in self.patrons:
            return { "success": False, "error": "Patron not found." }

        updated = False

        if name is not None:
            self.patrons[patron_id]["name"] = name
            updated = True
        if contact_details is not None:
            self.patrons[patron_id]["contact_details"] = contact_details
            updated = True
        if account_status is not None:
            self.patrons[patron_id]["account_status"] = account_status
            updated = True

        # It's OK to be a no-op if nothing is updated, but still return success
        return { "success": True, "message": "Patron information updated successfully." }

    def add_patron(self, patron_id: str, name: str, contact_details: str, account_status: str) -> dict:
        """
        Add a new patron to the library system.

        Args:
            patron_id (str): Unique identifier for the patron.
            name (str): Patron's full name.
            contact_details (str): Patron's contact info (e.g., phone/email).
            account_status (str): Initial status of the patron account (e.g., 'active').

        Returns:
            dict: {
                "success": True,
                "message": "Patron <id> added."
            }
            or
            {
                "success": False,
                "error": "Patron ID already exists."
            }

        Constraints:
            - patron_id must be unique (not already in the system).
        """
        if patron_id in self.patrons:
            return { "success": False, "error": "Patron ID already exists." }

        self.patrons[patron_id] = {
            "patron_id": patron_id,
            "name": name,
            "contact_details": contact_details,
            "account_status": account_status
        }
        return { "success": True, "message": f"Patron {patron_id} added." }

    def remove_patron(self, patron_id: str) -> dict:
        """
        Remove a patron from the library system. All existing loan records with this patron 
        will be marked as 'invalidated' in their status field.

        Args:
            patron_id (str): Unique identifier of the patron to remove.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Patron removed." }
              - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Patron must exist in self.patrons to be removed.
            - All associated loan records will have their status set to "invalidated".
        """
        if patron_id not in self.patrons:
            return { "success": False, "error": "Patron does not exist" }

        # Remove patron
        del self.patrons[patron_id]

        # Invalidate all associated loan records
        for lr in self.loan_records.values():
            if lr["patron_id"] == patron_id:
                lr["status"] = "invalidated"

        return { "success": True, "message": "Patron removed." }


class LibraryManagementSystem(BaseEnv):
    def __init__(self, *, parameters=None):
        super().__init__()
        self.parameters = copy.deepcopy(parameters or {})
        self._mirrored_state_keys = set()
        self._inner = self._build_inner_env()
        self._apply_init_config(self._inner, self.parameters if isinstance(self.parameters, dict) else {})
        self._sync_from_inner()

    @staticmethod
    def _build_inner_env():
        try:
            return _GeneratedEnvImpl({})
        except Exception:
            return _GeneratedEnvImpl()

    @staticmethod
    def _apply_init_config(env, init_config):
        if not isinstance(init_config, dict):
            return
        for key, value in init_config.items():
            setattr(env, key, copy.deepcopy(value))

    def _sync_from_inner(self):
        reserved = {
            "parameters",
            "_inner",
            "_mirrored_state_keys",
            "tool_list",
            "env_description",
            "initial_parameter_schema",
            "default_initial_parameters",
            "tool_descs",
        }
        current = set()
        for key, value in vars(self._inner).items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if key in reserved:
                continue
            setattr(self, key, copy.deepcopy(value))
            current.add(key)
        stale = getattr(self, "_mirrored_state_keys", set()) - current
        for key in stale:
            if hasattr(self, key):
                delattr(self, key)
        self._mirrored_state_keys = current

    def _call_inner_tool(self, tool_name: str, kwargs: Dict[str, Any]):
        func = getattr(self._inner, tool_name)
        result = func(**copy.deepcopy(kwargs or {}))
        self._sync_from_inner()
        return result

    def get_book_by_id(self, **kwargs):
        return self._call_inner_tool('get_book_by_id', kwargs)

    def list_books(self, **kwargs):
        return self._call_inner_tool('list_books', kwargs)

    def get_book_status(self, **kwargs):
        return self._call_inner_tool('get_book_status', kwargs)

    def list_books_by_status(self, **kwargs):
        return self._call_inner_tool('list_books_by_status', kwargs)

    def get_loan_records_for_book(self, **kwargs):
        return self._call_inner_tool('get_loan_records_for_book', kwargs)

    def get_patron_by_id(self, **kwargs):
        return self._call_inner_tool('get_patron_by_id', kwargs)

    def get_loan_record_by_id(self, **kwargs):
        return self._call_inner_tool('get_loan_record_by_id', kwargs)

    def list_active_loans_for_book(self, **kwargs):
        return self._call_inner_tool('list_active_loans_for_book', kwargs)

    def list_all_loan_records(self, **kwargs):
        return self._call_inner_tool('list_all_loan_records', kwargs)

    def remove_book(self, **kwargs):
        return self._call_inner_tool('remove_book', kwargs)

    def update_loan_record_status(self, **kwargs):
        return self._call_inner_tool('update_loan_record_status', kwargs)

    def invalidate_loan_records_for_book(self, **kwargs):
        return self._call_inner_tool('invalidate_loan_records_for_book', kwargs)

    def add_book(self, **kwargs):
        return self._call_inner_tool('add_book', kwargs)

    def update_book_info(self, **kwargs):
        return self._call_inner_tool('update_book_info', kwargs)

    def add_loan_record(self, **kwargs):
        return self._call_inner_tool('add_loan_record', kwargs)

    def remove_loan_record(self, **kwargs):
        return self._call_inner_tool('remove_loan_record', kwargs)

    def update_patron_info(self, **kwargs):
        return self._call_inner_tool('update_patron_info', kwargs)

    def add_patron(self, **kwargs):
        return self._call_inner_tool('add_patron', kwargs)

    def remove_patron(self, **kwargs):
        return self._call_inner_tool('remove_patron', kwargs)

