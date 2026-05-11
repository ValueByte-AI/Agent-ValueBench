# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid
from datetime import datetime



# State Space Entity Typings

class UserInfo(TypedDict):
    _id: str               # User ID
    name: str
    email: str
    account_sta: str       # Account status

class BookInfo(TypedDict):
    book_id: str
    title: str
    author: str
    isbn: str
    publisher: str
    publication_year: int
    cover_image_url: str
    description: str

class BookshelfInfo(TypedDict):
    shelf_id: str
    user_id: str
    shelf_name: str
    shelf_type: str

class UserBookInfo(TypedDict):
    _id: str
    book_id: str
    shelf_id: str
    date_added: str
    reading_status: str
    note: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for a digital personal bookshelf system.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Books: {book_id: BookInfo}
        self.books: Dict[str, BookInfo] = {}

        # Bookshelves: {shelf_id: BookshelfInfo}
        self.bookshelves: Dict[str, BookshelfInfo] = {}

        # UserBooks: {_id: UserBookInfo}
        self.userbooks: Dict[str, UserBookInfo] = {}

        # --- Constraints ---
        # - Each book must have a unique ISBN (if available).
        # - Users can only modify bookshelves they own.
        # - A book can be associated with multiple shelves for a single user.
        # - Books must be assigned to at least one bookshelf upon addition to the user's collection.
        # - Only valid ISBNs retrieve book metadata automatically.

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve all user infos whose name exactly matches the given name.
    
        Args:
            name (str): The name of the user to search for. (Exact/case-sensitive match)
        
        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[UserInfo],  # List of matching user info dicts (may be empty if no match)
                }
                or
                {
                    "success": False,
                    "error": str  # No user found with the given name
                }
        """
        matches = [user for user in self.users.values() if user["name"] == name]
        if not matches:
            return { "success": False, "error": "No user found with the given name" }
        return { "success": True, "data": matches }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve a user's information by their unique user ID.

        Args:
            user_id (str): The unique user ID (_id) to query.

        Returns:
            dict: 
              - On success: { "success": True, "data": UserInfo }
              - On failure (user not found): { "success": False, "error": "User not found" }
    
        Constraints:
            - No modification of state.
            - No permission checks needed for this simple query.
        """
        if user_id in self.users:
            return { "success": True, "data": self.users[user_id] }
        else:
            return { "success": False, "error": "User not found" }

    def list_user_bookshelves(self, user_id: str) -> dict:
        """
        List all bookshelves belonging to a specified user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[BookshelfInfo]   # List of bookshelf info (can be empty if user has no shelves)
                    }
                On error:
                    {
                        "success": False,
                        "error": str   # Reason, e.g. user does not exist
                    }

        Constraints:
            - The specified user must exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        bookshelves = [
            shelf for shelf in self.bookshelves.values()
            if shelf["user_id"] == user_id
        ]
        return {"success": True, "data": bookshelves}

    def get_bookshelf_by_name(self, user_id: str, shelf_name: str) -> dict:
        """
        Retrieve a bookshelf belonging to a given user by its name.

        Args:
            user_id (str): The user ID (must match BookshelfInfo.user_id).
            shelf_name (str): The target bookshelf's name.

        Returns:
            dict: {
                "success": True,
                "data": BookshelfInfo
            }
            or
            {
                "success": False,
                "error": "Bookshelf not found for user"
            }

        Constraints:
            - Users can only access (retrieve) bookshelves they own.
            - Shelf names are only unique within a user's ownership scope.
        """
        for shelf in self.bookshelves.values():
            if shelf["user_id"] == user_id and shelf["shelf_name"] == shelf_name:
                return {"success": True, "data": shelf}

        return {"success": False, "error": "Bookshelf not found for user"}

    def get_bookshelf_by_id(self, shelf_id: str) -> dict:
        """
        Retrieve bookshelf information by shelf ID.

        Args:
            shelf_id (str): The unique identifier for the bookshelf.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": BookshelfInfo  # info for the matched bookshelf
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Bookshelf does not exist"
                    }
        Constraints:
            - No permissions or ownership checks for this query.
        """
        bookshelf = self.bookshelves.get(shelf_id)
        if bookshelf is None:
            return { "success": False, "error": "Bookshelf does not exist" }
        return { "success": True, "data": bookshelf }

    def list_books_by_isbn(self, isbn: str) -> dict:
        """
        List all books in the system matching the provided ISBN.

        Args:
            isbn (str): The ISBN to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[BookInfo]  # All books that have this ISBN (may be empty, should usually be 0 or 1)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. invalid input)
            }

        Constraints:
            - No enforcement of uniqueness; merely returns all matches.
            - If ISBN is an empty string or None, returns error.
        """
        if not isinstance(isbn, str) or not isbn.strip():
            return { "success": False, "error": "A non-empty ISBN string must be provided." }

        result = [book for book in self.books.values() if book.get("isbn") == isbn]
        return { "success": True, "data": result }

    def get_book_by_id(self, book_id: str) -> dict:
        """
        Retrieve full metadata for a book specified by its book_id.

        Args:
            book_id (str): Unique identifier for the book in the system.

        Returns:
            dict:
                - If found: {"success": True, "data": BookInfo}
                - If not found: {"success": False, "error": "Book not found"}

        Constraints:
            - book_id must exist in the system.
        """
        if book_id not in self.books:
            return { "success": False, "error": "Book not found" }
        return { "success": True, "data": self.books[book_id] }

    def get_book_by_isbn(self, isbn: str) -> dict:
        """
        Retrieve book metadata by ISBN.

        Args:
            isbn (str): The ISBN code to search for.

        Returns:
            dict:
                - On success: {"success": True, "data": BookInfo}
                - If not found: {"success": False, "error": "Book with the given ISBN not found"}

        Constraints:
            - Each book must have a unique ISBN (if available).
            - ISBN must be matched exactly (case-sensitive).
        """
        if not isbn or not isinstance(isbn, str):
            return {"success": False, "error": "Invalid ISBN parameter"}

        for book in self.books.values():
            if book.get("isbn") == isbn:
                return {"success": True, "data": book}

        return {"success": False, "error": "Book with the given ISBN not found"}

    def validate_isbn(self, isbn: str) -> dict:
        """
        Check whether a given ISBN is valid (ISBN-10 or ISBN-13).

        Args:
            isbn (str): The ISBN string to check.

        Returns:
            dict: {
                "success": True,
                "data": { "is_valid": bool }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Valid ISBN-10: 10 characters, last can be X/x, uses ISBN-10 checksum.
            - Valid ISBN-13: 13 digits, uses ISBN-13 checksum.
        """
        def clean_isbn(isbn_str: str) -> str:
            # Remove hyphens and spaces, uppercase for 'X'
            return isbn_str.replace('-', '').replace(' ', '').upper()

        if not isinstance(isbn, str):
            return { "success": False, "error": "ISBN must be a string" }

        isbn_clean = clean_isbn(isbn)
        n = len(isbn_clean)

        def is_valid_isbn10(isbn10: str) -> bool:
            if len(isbn10) != 10:
                return False
            if not isbn10[:9].isdigit():
                return False
            # Last char can be digit or 'X'
            if not (isbn10[9].isdigit() or isbn10[9] == 'X'):
                return False
            total = 0
            for i in range(9):
                total += (i + 1) * int(isbn10[i])
            if isbn10[9] == 'X':
                total += 10 * 10
            else:
                total += 10 * int(isbn10[9])
            return total % 11 == 0

        def is_valid_isbn13(isbn13: str) -> bool:
            if len(isbn13) != 13 or not isbn13.isdigit():
                return False
            total = 0
            for i in range(12):
                digit = int(isbn13[i])
                if i % 2 == 0:
                    total += digit
                else:
                    total += 3 * digit
            checksum = (10 - (total % 10)) % 10
            return int(isbn13[12]) == checksum

        result = False
        if n == 10:
            result = is_valid_isbn10(isbn_clean)
        elif n == 13:
            result = is_valid_isbn13(isbn_clean)

        return { "success": True, "data": { "is_valid": result } }

    def get_userbook_entry(self, user_id: str, book_id: str, shelf_id: str) -> dict:
        """
        Check if a UserBook record (book-to-shelf association) exists for the given user, book, and shelf.

        Args:
            user_id (str): The user who owns the shelf.
            book_id (str): The book to check association for.
            shelf_id (str): The shelf to check association for.

        Returns:
            dict: {
                "success": True,
                "data": UserBookInfo  # Details if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - All IDs (user_id, book_id, shelf_id) must exist.
            - The shelf must belong to the specified user.
        """
        if user_id not in self.users:
            return {"success": False, "error": "user_id does not exist"}
        if book_id not in self.books:
            return {"success": False, "error": "book_id does not exist"}
        if shelf_id not in self.bookshelves:
            return {"success": False, "error": "shelf_id does not exist"}
        shelf = self.bookshelves[shelf_id]
        if shelf["user_id"] != user_id:
            return {"success": False, "error": "Shelf does not belong to this user"}

        for userbook in self.userbooks.values():
            if userbook["book_id"] == book_id and userbook["shelf_id"] == shelf_id:
                return {"success": True, "data": userbook}

        return {"success": False, "error": "No such UserBook entry exists for this book and shelf"}

    def list_userbook_entries_by_shelf(self, shelf_id: str) -> dict:
        """
        List all UserBook entries assigned to the specified shelf.

        Args:
            shelf_id (str): The identifier for the bookshelf.

        Returns:
            dict: {
                "success": True,
                "data": List[UserBookInfo],  # List of UserBookInfo entries for the shelf (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Description of why the operation failed
            }

        Constraints:
            - Fails if the specified shelf does not exist.
        """
        if shelf_id not in self.bookshelves:
            return {"success": False, "error": "Bookshelf does not exist"}

        result = [
            userbook for userbook in self.userbooks.values()
            if userbook["shelf_id"] == shelf_id
        ]

        return {"success": True, "data": result}

    def list_userbook_entries_for_book(self, user_id: str, book_id: str) -> dict:
        """
        List all shelf associations (UserBook entries) for a given user and book.

        Args:
            user_id (str): The user's ID.
            book_id (str): The book's ID.

        Returns:
            dict:
                - success: True, data: List[UserBookInfo] (all matching entries placed by the user for this book)
                - success: False, error: Info message (user or book does not exist)

        Constraints:
            - user_id must exist in self.users
            - book_id must exist in self.books
            - Only associations involving shelves owned by the user and matching book_id are listed
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if book_id not in self.books:
            return { "success": False, "error": "Book does not exist" }

        # First, get all shelf_ids owned by the user
        user_shelf_ids = {
            shelf_id for shelf_id, shelf in self.bookshelves.items()
            if shelf["user_id"] == user_id
        }

        # Filter userbook entries that match book_id and shelf_id is one of the user's shelves
        result = [
            userbook for userbook in self.userbooks.values()
            if userbook["book_id"] == book_id and userbook["shelf_id"] in user_shelf_ids
        ]

        return { "success": True, "data": result }

    def add_book_by_isbn(self, isbn: str) -> dict:
        """
        Create a new Book entry and populate its metadata via ISBN (if valid and unique).

        Args:
            isbn (str): ISBN of the new book.

        Returns:
            dict: 
                { "success": True, "message": "Book added successfully", "book": BookInfo }
                OR
                { "success": False, "error": str }  # On invalid or duplicate ISBN, or metadata fetch error.

        Constraints:
            - ISBN must be valid (syntactic validation).
            - ISBN must be unique (not already in self.books).
            - Metadata is filled from ISBN; if not retrievable, operation fails.
        """

        # Helper validator: Checks ISBN-10/13 validity
        def _is_valid_isbn(isbn_str: str) -> bool:
            digits = isbn_str.replace("-", "").replace(" ", "")
            if len(digits) == 10 and digits[:-1].isdigit():
                s = sum((i + 1) * int(x) for i, x in enumerate(digits[:-1]))
                check = digits[-1]
                if check == 'X': check_val = 10
                else: check_val = int(check) if check.isdigit() else -1
                return (s + check_val * 10) % 11 == 0
            if len(digits) == 13 and digits.isdigit():
                s = sum((1 if i % 2 == 0 else 3) * int(x) for i, x in enumerate(digits[:-1]))
                checksum = (10 - (s % 10)) % 10
                return checksum == int(digits[-1])
            return False

        # Helper mock: Fetch book metadata by ISBN (would in reality query an API)
        def _fetch_metadata_by_isbn(isbn: str) -> dict:
            # Dummy metadata for example purposes
            dummy_db = {
                "9780140449136": {
                    "title": "Meditations",
                    "author": "Marcus Aurelius",
                    "publisher": "Penguin Classics",
                    "publication_year": 2006,
                    "cover_image_url": "https://...",
                    "description": "A series of personal writings by Marcus Aurelius."
                }
            }
            return dummy_db.get(isbn, None)

        if not _is_valid_isbn(isbn):
            return {"success": False, "error": "Invalid ISBN"}

        # ISBN must be unique
        for book in self.books.values():
            if book['isbn'] == isbn:
                return {"success": False, "error": "Book with this ISBN already exists"}

        metadata = _fetch_metadata_by_isbn(isbn)
        if not metadata:
            return {"success": False, "error": "Could not retrieve metadata for this ISBN"}

        book_id = str(uuid.uuid4())

        book_info: BookInfo = {
            "book_id": book_id,
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "isbn": isbn,
            "publisher": metadata.get("publisher", ""),
            "publication_year": metadata.get("publication_year", 0),
            "cover_image_url": metadata.get("cover_image_url", ""),
            "description": metadata.get("description", ""),
        }

        self.books[book_id] = book_info

        return {
            "success": True,
            "message": "Book added successfully",
            "book": book_info
        }

    def add_new_book(
        self,
        book_id: str,
        title: str,
        author: str,
        isbn: str,
        publisher: str,
        publication_year: int,
        cover_image_url: str,
        description: str
    ) -> dict:
        """
        Add a new Book entry with given metadata if ISBN is unique (if provided) and book_id is unique.

        Args:
            book_id (str): Unique book identifier.
            title (str): Book title.
            author (str): Book author.
            isbn (str): Book ISBN (may be empty, but if provided must be unique).
            publisher (str): Book publisher.
            publication_year (int): Year of publication.
            cover_image_url (str): URL for book cover image.
            description (str): Book description.

        Returns:
            dict: Success or error dictionary:
                - On success: { "success": True, "message": "Book added successfully." }
                - On error: { "success": False, "error": <reason> }

        Constraints:
            - ISBN must be unique if provided (not empty).
            - book_id must be unique.
        """
        # Check for required uniqueness of book_id
        if book_id in self.books:
            return { "success": False, "error": "Book ID already exists." }

        # Check that ISBN is unique if provided (not empty string)
        if isbn:
            for b in self.books.values():
                if b.get("isbn", "").strip() and b["isbn"].strip() == isbn.strip():
                    return { "success": False, "error": "ISBN already exists for another book." }

        # Compose the book info
        book_info: BookInfo = {
            "book_id": book_id,
            "title": title,
            "author": author,
            "isbn": isbn,
            "publisher": publisher,
            "publication_year": publication_year,
            "cover_image_url": cover_image_url,
            "description": description
        }

        self.books[book_id] = book_info

        return { "success": True, "message": "Book added successfully." }

    def create_bookshelf(self, user_id: str, shelf_name: str, shelf_type: str) -> dict:
        """
        Create a new bookshelf for a user.

        Args:
            user_id (str): The ID of the user who will own the shelf.
            shelf_name (str): The name of the shelf (must be unique for this user).
            shelf_type (str): The type/category of the shelf.

        Returns:
            dict: {
                "success": True,
                "message": "Bookshelf created with id <shelf_id>"
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - user_id must exist in the system.
            - shelf_name must be unique for the user.
        """
        # Validate user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if not shelf_name or not shelf_type:
            return { "success": False, "error": "shelf_name and shelf_type must be provided" }
        # Check if shelf name already exists for this user
        for shelf in self.bookshelves.values():
            if shelf["user_id"] == user_id and shelf["shelf_name"].lower() == shelf_name.lower():
                return { "success": False, "error": "Shelf name already exists for this user" }
        # Create a unique shelf_id (simple auto-increment or uuid)
        shelf_id = "shelf_" + str(uuid.uuid4())
        self.bookshelves[shelf_id] = {
            "shelf_id": shelf_id,
            "user_id": user_id,
            "shelf_name": shelf_name,
            "shelf_type": shelf_type
        }
        return { "success": True, "message": f"Bookshelf created with id {shelf_id}" }

    def add_book_to_shelf(self, user_id: str, book_id: str, shelf_id: str, reading_status: str = "", note: str = "") -> dict:
        """
        Associates the specified book with the specified user shelf by creating a UserBook entry.

        Args:
            user_id (str): The user's ID.
            book_id (str): The book's ID.
            shelf_id (str): The bookshelf's ID, must belong to the user.
            reading_status (str, optional): Reading status of the book (e.g., 'To Read', 'Reading', 'Finished').
            note (str, optional): Any note the user wants to add for this book/shelf association.

        Returns:
            dict: {
                "success": True,
                "message": "Book added to shelf."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - Users can only modify bookshelves they own.
            - Each (user, book, shelf) association can exist only once.
            - Book must exist; shelf must exist and belong to the user.
        """
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check book existence
        if book_id not in self.books:
            return {"success": False, "error": "Book does not exist."}

        # Check bookshelf existence and ownership
        shelf = self.bookshelves.get(shelf_id)
        if not shelf:
            return {"success": False, "error": "Shelf does not exist."}
        if shelf["user_id"] != user_id:
            return {"success": False, "error": "Shelf does not belong to the user."}

        # Prevent duplicate UserBook entry
        for ub in self.userbooks.values():
            if ub["book_id"] == book_id and ub["shelf_id"] == shelf_id:
                return {"success": False, "error": "Book is already on this shelf for the user."}

        # Generate a unique UserBook ID
        userbook_id = f"{user_id}:{book_id}:{shelf_id}"

        # Get current date string (ISO 8601)
        date_added = datetime.now().isoformat()

        self.userbooks[userbook_id] = {
            "_id": userbook_id,
            "book_id": book_id,
            "shelf_id": shelf_id,
            "date_added": date_added,
            "reading_status": reading_status,
            "note": note
        }

        return {"success": True, "message": "Book added to shelf."}

    def update_userbook_reading_status(self, userbook_id: str, new_reading_status: str) -> dict:
        """
        Update the reading status of a UserBook association (e.g., “to-read”, “reading”, “completed”).

        Args:
            userbook_id (str): The ID of the UserBook association to update.
            new_reading_status (str): The new reading status to set.

        Returns:
            dict: {
                "success": True,
                "message": "Reading status updated for UserBook <userbook_id>"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The UserBook entry must exist.
            - Accepts any string as reading status (unless stricter validation is required).
        """
        if userbook_id not in self.userbooks:
            return { "success": False, "error": "UserBook entry does not exist" }

        self.userbooks[userbook_id]["reading_status"] = new_reading_status
        return {
            "success": True,
            "message": f"Reading status updated for UserBook {userbook_id}"
        }

    def update_userbook_note(self, userbook_id: str, note: str) -> dict:
        """
        Update or add a note to a UserBook association.

        Args:
            userbook_id (str): The unique identifier of the UserBook entry to update.
            note (str): The content of the note to set for the UserBook association.

        Returns:
            dict: {
                "success": True,
                "message": "Note updated for UserBook <userbook_id>."
            }
            OR
            {
                "success": False,
                "error": "UserBook entry not found."
            }

        Constraints:
            - The specified UserBook entry must exist in the system.
            - No additional constraints on note content or length, unless enforced elsewhere.
        """
        if userbook_id not in self.userbooks:
            return {"success": False, "error": "UserBook entry not found."}

        self.userbooks[userbook_id]["note"] = note
        return {"success": True, "message": f"Note updated for UserBook {userbook_id}."}

    def move_book_between_shelves(self, userbook_id: str, from_shelf_id: str, to_shelf_id: str, user_id: str) -> dict:
        """
        Remove a UserBook association from one shelf and add it to another.

        Args:
            userbook_id (str): The ID of the UserBook association to move.
            from_shelf_id (str): The shelf the book is currently on.
            to_shelf_id (str): The shelf to move the association to.
            user_id (str): The user performing the operation (must own both shelves).

        Returns:
            dict: {
                "success": True,
                "message": "Moved book association from shelf <from_shelf_id> to <to_shelf_id>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only the shelf owner can move books between their shelves.
            - Both shelf ids must belong to the same user.
            - Cannot move to the same shelf.
        """
        # Check UserBook exists
        userbook = self.userbooks.get(userbook_id)
        if not userbook:
            return {"success": False, "error": "UserBook entry not found"}

        # Check shelves exist
        from_shelf = self.bookshelves.get(from_shelf_id)
        to_shelf = self.bookshelves.get(to_shelf_id)
        if not from_shelf:
            return {"success": False, "error": "Source shelf (from_shelf_id) does not exist"}
        if not to_shelf:
            return {"success": False, "error": "Destination shelf (to_shelf_id) does not exist"}

        # Check both shelves belong to the same user and user is the owner
        if from_shelf['user_id'] != user_id or to_shelf['user_id'] != user_id:
            return {"success": False, "error": "Permission denied: One or both shelves are not owned by the user"}

        # Check UserBook is on the from_shelf
        if userbook['shelf_id'] != from_shelf_id:
            return {"success": False, "error": "UserBook's current shelf does not match the given from_shelf_id"}

        # Prevent moving to the same shelf
        if from_shelf_id == to_shelf_id:
            return {"success": False, "error": "Source and destination shelves must be different"}

        # Move: update the shelf_id
        userbook['shelf_id'] = to_shelf_id

        return {
            "success": True,
            "message": f"Moved book association from shelf {from_shelf_id} to {to_shelf_id}"
        }

    def remove_book_from_shelf(self, userbook_id: str) -> dict:
        """
        Remove a UserBook association (removing a book from a shelf), only if the book 
        would still remain on at least one shelf for the same user.

        Args:
            userbook_id (str): The identifier of the UserBook association to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Book removed from shelf successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The entry must exist.
            - After removal, the same (user, book) pair must still exist in at least one other shelf (for that user).
            - Book must always be associated with at least one shelf for the user.
        """
        # 1. Ensure the UserBook entry exists
        if userbook_id not in self.userbooks:
            return {"success": False, "error": "UserBook entry does not exist."}
        userbook = self.userbooks[userbook_id]
        shelf_id = userbook["shelf_id"]
        book_id = userbook["book_id"]

        # 2. Get user_id from the shelf
        if shelf_id not in self.bookshelves:
            return {"success": False, "error": "Associated bookshelf does not exist."}
        shelf_info = self.bookshelves[shelf_id]
        user_id = shelf_info["user_id"]

        # 3. Count number of UserBook entries for this user and book across any shelf (excluding the current one)
        other_userbook_links = [
            ub for ub in self.userbooks.values()
            if (
                ub["_id"] != userbook_id
                and ub["book_id"] == book_id
                and ub["shelf_id"] in self.bookshelves
                and self.bookshelves[ub["shelf_id"]]["user_id"] == user_id
            )
        ]
        if not other_userbook_links:
            # Would leave the book with no shelf for this user
            return {"success": False, "error": "Book must remain on at least one shelf for this user."}

        # 4. Remove the UserBook entry
        del self.userbooks[userbook_id]

        return {"success": True, "message": "Book removed from shelf successfully."}

    def delete_bookshelf(self, shelf_id: str, user_id: str) -> dict:
        """
        Delete a user's bookshelf. This is only permitted if the requesting user owns the shelf.
        If any book for the user would be left with no shelf assignment as a result, the operation fails.

        Args:
            shelf_id (str): The ID of the bookshelf to delete.
            user_id (str): The ID of the user requesting the deletion.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Bookshelf deleted." }
              - On failure: { "success": False, "error": <reason> }
        Constraints:
            - User can only delete their own bookshelves.
            - No book for the user may be left with zero shelf assignments after deletion.

        """
        shelf = self.bookshelves.get(shelf_id)
        if not shelf:
            return {"success": False, "error": "Bookshelf does not exist."}
        if shelf["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: user does not own this bookshelf."}

        # Find all UserBook entries for this shelf
        userbook_ids_to_delete = [ub_id for ub_id, ub in self.userbooks.items() if ub["shelf_id"] == shelf_id]

        # For each UserBook about to be deleted, check if the corresponding user-book relation
        # will have at least one other shelf
        for ub_id in userbook_ids_to_delete:
            ub_entry = self.userbooks[ub_id]
            book_id = ub_entry["book_id"]
            # Find all other UserBook entries for the same user and book, but different shelf
            other_assignments = [
                other_ub for other_ub in self.userbooks.values()
                if other_ub["book_id"] == book_id
                and other_ub["shelf_id"] != shelf_id
                and self.bookshelves.get(other_ub["shelf_id"], {}).get("user_id") == user_id
            ]
            if not other_assignments:
                book = self.books.get(book_id)
                book_title = book["title"] if book else book_id
                return {
                    "success": False,
                    "error": (
                        f"Cannot delete shelf: Book '{book_title}' would have no assigned shelf. "
                        "Reassign it to another shelf before deleting."
                    )
                }

        # Passed checks — can safely delete the shelf and referenced UserBook entries
        for ub_id in userbook_ids_to_delete:
            del self.userbooks[ub_id]
        del self.bookshelves[shelf_id]

        return {
            "success": True,
            "message": "Bookshelf deleted."
        }

    def remove_book_completely_from_user(self, user_id: str, book_id: str) -> dict:
        """
        Remove all UserBook associations for a book belonging to a user, completely removing the book from their collection.

        Args:
            user_id (str): The user's unique ID.
            book_id (str): The book's unique ID.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Book removed completely from user collection." }
                On error:
                    { "success": False, "error": "Error message" }

        Constraints:
            - The operation is only legal if, after execution, the book is not on any shelf for this user (enforced by removing all userbook relations for user/book).
            - The user and book must exist.
            - Book must already be in at least one shelf for the user.
        """
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        # Check book existence
        if book_id not in self.books:
            return { "success": False, "error": "Book does not exist." }

        # Collect all relevant UserBook ids
        userbook_ids_to_remove = [
            ub_id for ub_id, userbook in self.userbooks.items()
            if userbook["book_id"] == book_id
            and self.bookshelves.get(userbook["shelf_id"], {}).get("user_id") == user_id
        ]

        if not userbook_ids_to_remove:
            return { "success": False, "error": "Book is not in user's collection." }

        for ub_id in userbook_ids_to_remove:
            del self.userbooks[ub_id]

        # Final safety check
        still_exists = any(
            userbook["book_id"] == book_id
            and self.bookshelves.get(userbook["shelf_id"], {}).get("user_id") == user_id
            for userbook in self.userbooks.values()
        )
        if still_exists:
            return { "success": False, "error": "Failed to remove all associations for this book from this user." }

        return { "success": True, "message": "Book removed completely from user collection." }


class DigitalBookshelfSystem(BaseEnv):
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_user_bookshelves(self, **kwargs):
        return self._call_inner_tool('list_user_bookshelves', kwargs)

    def get_bookshelf_by_name(self, **kwargs):
        return self._call_inner_tool('get_bookshelf_by_name', kwargs)

    def get_bookshelf_by_id(self, **kwargs):
        return self._call_inner_tool('get_bookshelf_by_id', kwargs)

    def list_books_by_isbn(self, **kwargs):
        return self._call_inner_tool('list_books_by_isbn', kwargs)

    def get_book_by_id(self, **kwargs):
        return self._call_inner_tool('get_book_by_id', kwargs)

    def get_book_by_isbn(self, **kwargs):
        return self._call_inner_tool('get_book_by_isbn', kwargs)

    def validate_isbn(self, **kwargs):
        return self._call_inner_tool('validate_isbn', kwargs)

    def get_userbook_entry(self, **kwargs):
        return self._call_inner_tool('get_userbook_entry', kwargs)

    def list_userbook_entries_by_shelf(self, **kwargs):
        return self._call_inner_tool('list_userbook_entries_by_shelf', kwargs)

    def list_userbook_entries_for_book(self, **kwargs):
        return self._call_inner_tool('list_userbook_entries_for_book', kwargs)

    def add_book_by_isbn(self, **kwargs):
        return self._call_inner_tool('add_book_by_isbn', kwargs)

    def add_new_book(self, **kwargs):
        return self._call_inner_tool('add_new_book', kwargs)

    def create_bookshelf(self, **kwargs):
        return self._call_inner_tool('create_bookshelf', kwargs)

    def add_book_to_shelf(self, **kwargs):
        return self._call_inner_tool('add_book_to_shelf', kwargs)

    def update_userbook_reading_status(self, **kwargs):
        return self._call_inner_tool('update_userbook_reading_status', kwargs)

    def update_userbook_note(self, **kwargs):
        return self._call_inner_tool('update_userbook_note', kwargs)

    def move_book_between_shelves(self, **kwargs):
        return self._call_inner_tool('move_book_between_shelves', kwargs)

    def remove_book_from_shelf(self, **kwargs):
        return self._call_inner_tool('remove_book_from_shelf', kwargs)

    def delete_bookshelf(self, **kwargs):
        return self._call_inner_tool('delete_bookshelf', kwargs)

    def remove_book_completely_from_user(self, **kwargs):
        return self._call_inner_tool('remove_book_completely_from_user', kwargs)

