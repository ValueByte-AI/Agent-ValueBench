# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional, List, Dict
import datetime



class BookInfo(TypedDict):
    book_id: str
    title: str
    author: str
    genre: str
    file_format: str
    file_location: str
    uploaded_by: str
    upload_date: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    email: str
    account_status: str

class CategoryInfo(TypedDict):
    category_id: str
    category_name: str
    description: str

class BookCategoryAssociationInfo(TypedDict):
    book_id: str
    category_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for digital book management.
        """

        # Books: {book_id: BookInfo}
        self.books: Dict[str, BookInfo] = {}  # Book entity
        
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}  # User entity
        
        # Categories: {category_id: CategoryInfo}
        self.categories: Dict[str, CategoryInfo] = {}  # Category entity
        
        # Book/Category associations: List of BookCategoryAssociationInfo
        self.book_category_associations: List[BookCategoryAssociationInfo] = []  # BookCategoryAssociation entity

        # Constraints:
        # - Each book must have a unique identifier (book_id).
        # - File uploads must conform to supported formats (e.g., PDF, EPUB, etc.).
        # - Users can only organize or manage books they have uploaded or are permitted to access.
        # - Book metadata (title, author, format, etc.) must be complete for upload acceptance.

    def _normalized_supported_file_formats(self):
        formats = getattr(self, "supported_file_formats", None)
        if formats is None:
            return None
        if isinstance(formats, str):
            raw_text = formats.strip()
            if not raw_text:
                return None
            parsed_formats = None
            try:
                decoded = json.loads(raw_text)
                if isinstance(decoded, list):
                    parsed_formats = decoded
            except Exception:
                parsed_formats = None
            if parsed_formats is None:
                parsed_formats = [part.strip() for part in raw_text.split(",") if part.strip()]
            formats = parsed_formats
        if not isinstance(formats, (list, tuple, set)):
            return None
        normalized = []
        for fmt in formats:
            if not isinstance(fmt, str) or not fmt.strip():
                return None
            normalized.append(fmt.strip())
        return normalized

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user_id.

        Args:
            user_id (str): The unique identifier for the user to look up.

        Returns:
            dict:
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": str }
        Constraints:
            - user_id must exist in the platform's user records.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": f"User with id '{user_id}' does not exist." }
        return { "success": True, "data": user }

    def list_all_users(self) -> dict:
        """
        Retrieve all registered users on the platform.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of UserInfo dicts for all users (may be empty if no users)
            }
        """
        return {
            "success": True,
            "data": list(self.users.values())
        }

    def get_books_by_user(self, user_id: str) -> dict:
        """
        Retrieve all books uploaded by a particular user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success:
                    { "success": True, "data": List[BookInfo] }
                    (List may be empty if the user exists but has uploaded no books.)
                On failure:
                    { "success": False, "error": str }

        Constraints:
            - The specified user must exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        result = [
            book_info for book_info in self.books.values()
            if book_info["uploaded_by"] == user_id
        ]
        return { "success": True, "data": result }

    def get_book_by_id(self, book_id: str) -> dict:
        """
        Retrieve full information (BookInfo) for the book with the specified unique book_id.

        Args:
            book_id (str): The unique identifier of the book.

        Returns:
            dict: {
                "success": True,
                "data": BookInfo,   # BookInfo dict for the found book
            }
            or
            {
                "success": False,
                "error": str,  # Description of error (e.g., "Book not found")
            }

        Constraints:
            - The book_id must exist in the books dictionary for success.
        """
        if book_id not in self.books:
            return { "success": False, "error": "Book not found" }

        return { "success": True, "data": self.books[book_id] }


    def search_books_by_metadata(
        self, 
        title: Optional[str] = None, 
        author: Optional[str] = None, 
        genre: Optional[str] = None, 
        file_format: Optional[str] = None
    ) -> dict:
        """
        Search for books by matching (case-insensitive substring for title, author, genre; 
        case-insensitive exact for file_format) on provided non-None parameters.

        Args:
            title (Optional[str]): Substring of title to search for (case-insensitive).
            author (Optional[str]): Substring of author name to search for (case-insensitive).
            genre (Optional[str]): Substring of genre to search for (case-insensitive).
            file_format (Optional[str]): File format to search for (case-insensitive, exact).

        Returns:
            dict: 
                - If successful, {
                    "success": True,
                    "data": List[BookInfo]  # Matching books (may be empty)
                  }
        """
        def matches(book: Dict, key: str, value: Optional[str], exact: bool = False) -> bool:
            if value is None:
                return True
            if exact:
                return book[key].lower() == value.lower()
            return value.lower() in book[key].lower()
    
        result = [
            book for book in self.books.values()
            if matches(book, "title", title)
            and matches(book, "author", author)
            and matches(book, "genre", genre)
            and matches(book, "file_format", file_format, exact=True)
        ]
        return {"success": True, "data": result}

    def list_all_books(self) -> dict:
        """
        Retrieve all books stored on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BookInfo], # List of all BookInfo records (empty if no books)
            }

        Constraints:
            - None (just returns all books present).
            - If no books available, returns an empty list.
        """
        all_books = list(self.books.values())
        return {"success": True, "data": all_books}

    def is_book_id_unique(self, book_id: str) -> dict:
        """
        Check whether the given book_id is not already used in the system.

        Args:
            book_id (str): The candidate book identifier to check.

        Returns:
            dict: 
                - { "success": True, "data": True } if book_id is unique (not used)
                - { "success": True, "data": False } if book_id is already used
                - { "success": False, "error": "Invalid book_id" } if input is invalid

        Constraints:
            - Book_id must not be empty or None.
        """
        if not book_id or not isinstance(book_id, str):
            return { "success": False, "error": "Invalid book_id" }
        is_unique = book_id not in self.books
        return { "success": True, "data": is_unique }

    def get_supported_file_formats(self) -> dict:
        """
        Retrieve the list of supported file formats for book uploads.
    
        Returns:
            dict:
                success (bool): True if successful, False if key missing.
                data (List[str]): List of allowed file format strings (e.g. ["PDF", "EPUB"]).
                error (str, optional): Description of the error if unsuccessful.
    
        Constraints:
            - No input parameters.
            - Returns current state of allowed formats, or error if unset.
        """
        normalized_formats = self._normalized_supported_file_formats()
        if normalized_formats is None:
            return {
                "success": False,
                "error": "Supported file formats not configured."
            }
    
        return {
            "success": True,
            "data": list(normalized_formats)
        }

    def list_categories(self) -> dict:
        """
        Retrieve the list of all categories available on the platform.

        Returns:
            dict: 
                {
                    "success": True, 
                    "data": List[CategoryInfo]  # List of category info dictionaries. May be empty.
                }
        Constraints:
            - No input arguments required.
            - Operation always succeeds (returns empty list if no categories present).
        """
        return {
            "success": True,
            "data": list(self.categories.values())
        }

    def get_category_by_id(self, category_id: str) -> dict:
        """
        Retrieve information about a category given its category_id.

        Args:
            category_id (str): The unique identifier of the category.

        Returns:
            dict: {
                "success": True,
                "data": CategoryInfo  # Category information
            }
            or
            {
                "success": False,
                "error": str  # Error message if category is not found
            }

        Constraints:
            - The category_id must exist in the platform.
        """
        category = self.categories.get(category_id)
        if category is None:
            return { "success": False, "error": "Category not found" }
        return { "success": True, "data": category }

    def get_categories_for_book(self, book_id: str) -> dict:
        """
        List all categories (with full metadata) to which a specific book is assigned.
    
        Args:
            book_id (str): Unique identifier of the book to query.
        
        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo],  # List of CategoryInfo dicts (empty if book in no categories)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., book does not exist
            }
        
        Constraints:
            - The book must exist in the platform records.
        """
        if book_id not in self.books:
            return { "success": False, "error": "Book does not exist" }
    
        # Find all category_ids for this book
        cat_ids = [
            assoc["category_id"]
            for assoc in self.book_category_associations
            if assoc["book_id"] == book_id
        ]
        # Get full category info for these IDs (exclude missing categories for robustness)
        categories = [
            self.categories[cat_id] for cat_id in cat_ids
            if cat_id in self.categories
        ]
        return { "success": True, "data": categories }

    def list_books_in_category(self, category_id: str) -> dict:
        """
        List all books (with metadata) under a specific category.

        Args:
            category_id (str): The unique identifier of the category to query.

        Returns:
            dict: {
                "success": True,
                "data": List[BookInfo],  # List of BookInfo dicts for all books in this category (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Category does not exist"
            }

        Constraints:
            - The specified category_id must exist in the platform.
            - No user/ownership filtering is applied.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }

        # Get book_ids for this category
        book_ids = [
            assoc["book_id"]
            for assoc in self.book_category_associations
            if assoc["category_id"] == category_id
        ]

        # Get BookInfo for all matching books (may be empty)
        books_in_category = [
            self.books[book_id] for book_id in book_ids if book_id in self.books
        ]

        return { "success": True, "data": books_in_category }

    def get_book_category_associations(self) -> dict:
        """
        Retrieve all book-category association entries in the system.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[BookCategoryAssociationInfo]  # possibly empty if no associations
                }
    
        Constraints:
            - None. Returns all associations present in the environment.
            - Always succeeds (returns empty list if none exist).
        """
        return {
            "success": True,
            "data": list(self.book_category_associations)
        }

    def upload_new_book(self, book_info: BookInfo) -> dict:
        """
        Upload a new electronic book to the platform.
    
        Validates:
            - book_id uniqueness
            - Complete book metadata (title, author, genre, file_format, file_location, uploaded_by)
            - File format in supported formats
            - uploaded_by is a valid user

        Args:
            book_info (BookInfo): Dictionary with keys:
                - book_id, title, author, genre, file_format, file_location, uploaded_by, upload_date (optional)
    
        Returns:
            dict: 
                - On success: { "success": True, "message": "Book uploaded successfully." }
                - On error: { "success": False, "error": "<reason>" }
        """

        required_fields = ['book_id', 'title', 'author', 'genre', 'file_format', 'file_location', 'uploaded_by']
        # Ensure all required metadata fields are present and non-blank
        for field in required_fields:
            if field not in book_info or not str(book_info[field]).strip():
                return { "success": False, "error": f"Missing or empty required field: {field}" }
    
        book_id = book_info['book_id']
        file_format = book_info['file_format'].lower()
        uploaded_by = book_info['uploaded_by']

        # Check for unique book_id
        if book_id in self.books:
            return { "success": False, "error": "Book ID already exists. Book IDs must be unique." }
    
        supported_formats = self._normalized_supported_file_formats()
        if supported_formats is None:
            if not hasattr(self, 'supported_file_formats'):
                self.supported_file_formats = ["PDF", "EPUB"]
                supported_formats = ["PDF", "EPUB"]
            else:
                return {
                    "success": False,
                    "error": "Supported file formats not configured correctly."
                }

        # Check file format support
        if file_format not in {fmt.lower() for fmt in supported_formats}:
            return {
                "success": False,
                "error": f"Unsupported file format: {file_format}. Supported formats: {', '.join(supported_formats)}"
            }
    
        # Check user exists
        if uploaded_by not in self.users:
            return { "success": False, "error": f"User '{uploaded_by}' does not exist." }

        # Set or validate upload_date
        book_meta = dict(book_info)
        if 'upload_date' not in book_meta or not str(book_meta['upload_date']).strip():
            book_meta['upload_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        self.books[book_id] = book_meta

        return { "success": True, "message": "Book uploaded successfully." }

    def edit_book_metadata(self, user_id: str, book_id: str, updated_fields: dict) -> dict:
        """
        Update book metadata fields (title, author, genre, file_format, etc.) for a book the user is permitted to manage.

        Args:
            user_id (str): The ID of the user requesting the update.
            book_id (str): The ID of the book to update.
            updated_fields (dict): Metadata fields to update; keys can be title, author, genre, file_format.

        Returns:
            dict: {
                "success": True,
                "message": "Book metadata updated successfully"
            }
            or
            {
                "success": False,
                "error": "Description of the failure reason"
            }

        Constraints:
            - Only the user who uploaded the book can edit its metadata.
            - Book must exist.
            - User must exist.
            - file_format (if changed) must be in supported formats.
            - Required fields (title, author, genre, file_format) must be present and non-empty after update.
            - book_id and uploaded_by cannot be changed.
        """
        # Ensure user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Ensure book exists
        if book_id not in self.books:
            return {"success": False, "error": "Book does not exist"}

        book = self.books[book_id]

        # Permission: only uploader can edit
        if book["uploaded_by"] != user_id:
            return {"success": False, "error": "User is not permitted to edit this book"}

        # Fields allowed to update
        allowed_fields = {"title", "author", "genre", "file_format"}

        # Don't allow change to book_id, uploaded_by, etc.
        for field in updated_fields:
            if field not in allowed_fields:
                return {"success": False, "error": f"Field '{field}' cannot be updated"}

        # Check file_format if changed
        if "file_format" in updated_fields:
            new_format = updated_fields["file_format"]
            supported_formats = self._normalized_supported_file_formats()
            if supported_formats is None:
                supported_formats = ["PDF", "EPUB", "MOBI"]
            if new_format.upper() not in (fmt.upper() for fmt in supported_formats):
                return {"success": False, "error": f"Unsupported file format '{new_format}'"}

        # Ensure required metadata (after update) is present and not empty
        required_fields = ["title", "author", "genre", "file_format"]
        for key in required_fields:
            val = updated_fields.get(key, book.get(key, ""))
            if not isinstance(val, str) or not val.strip():
                return {"success": False, "error": f"Required field '{key}' cannot be empty"}

        # Perform the update
        for field, value in updated_fields.items():
            book[field] = value

        # Save
        self.books[book_id] = book

        return {"success": True, "message": "Book metadata updated successfully"}

    def delete_book(self, book_id: str, requesting_user_id: str) -> dict:
        """
        Remove a book from the platform, if and only if the requesting user is allowed to do so.

        Args:
            book_id (str): The identifier for the book to delete.
            requesting_user_id (str): The user ID requesting deletion.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Book deleted successfully." }
                On failure:
                    { "success": False, "error": <reason> }
    
        Constraints:
            - Only the uploader (uploaded_by == requesting_user_id) may delete the book.
            - Book and user must exist.
            - All category associations for this book are also removed.
        """
        # Check user existence
        if requesting_user_id not in self.users:
            return { "success": False, "error": "Requesting user does not exist." }
    
        # Check book existence
        if book_id not in self.books:
            return { "success": False, "error": "Book does not exist." }
    
        book_info = self.books[book_id]
        # Permission check: uploader only
        if book_info["uploaded_by"] != requesting_user_id:
            return { "success": False, "error": "Permission denied: only the uploader may delete this book." }
    
        # Remove the book
        del self.books[book_id]
    
        # Remove all BookCategoryAssociation records for this book
        self.book_category_associations = [
            assoc for assoc in self.book_category_associations
            if assoc["book_id"] != book_id
        ]
    
        return { "success": True, "message": "Book deleted successfully." }

    def assign_book_to_category(self, book_id: str, category_id: str) -> dict:
        """
        Assign a book to a specific category.

        Args:
            book_id (str): The ID of the book to assign.
            category_id (str): The ID of the category to assign the book to.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Book assigned to category successfully." }
                On failure (e.g., invalid book, category, or duplicate assignment):
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Both book_id and category_id must exist in the platform.
            - The association must not already exist.
        """
        if book_id not in self.books:
            return { "success": False, "error": "Book ID does not exist." }
        if category_id not in self.categories:
            return { "success": False, "error": "Category ID does not exist." }
        for assoc in self.book_category_associations:
            if assoc["book_id"] == book_id and assoc["category_id"] == category_id:
                return { "success": False, "error": "Book is already assigned to this category." }
        self.book_category_associations.append({
            "book_id": book_id,
            "category_id": category_id
        })
        return { "success": True, "message": "Book assigned to category successfully." }

    def remove_book_from_category(self, book_id: str, category_id: str) -> dict:
        """
        Removes the association between a book and a category.

        Args:
            book_id (str): The unique identifier of the book.
            category_id (str): The unique identifier of the category.

        Returns:
            dict: {
                "success": True,
                "message": "Book removed from category."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Both book_id and category_id must exist.
            - The specified book must be currently associated with the given category_id.
        """
        if book_id not in self.books:
            return {"success": False, "error": "Book ID does not exist."}
    
        if category_id not in self.categories:
            return {"success": False, "error": "Category ID does not exist."}
    
        assoc_index = None
        for idx, assoc in enumerate(self.book_category_associations):
            if assoc["book_id"] == book_id and assoc["category_id"] == category_id:
                assoc_index = idx
                break

        if assoc_index is None:
            return {"success": False, "error": "The specified association does not exist."}

        # Remove the association
        del self.book_category_associations[assoc_index]

        return {"success": True, "message": "Book removed from category."}

    def create_category(self, category_id: str, category_name: str, description: str) -> dict:
        """
        Add a new category to the platform.

        Args:
            category_id (str): Unique identifier for the new category.
            category_name (str): Name for the category.
            description (str): Description of the category.

        Returns:
            dict: {
                "success": True,
                "message": "Category '<category_name>' created."
            }
            OR
            {
                "success": False,
                "error": "Category ID already exists."
            }

        Constraints:
            - category_id must be unique in the platform.
        """
        if category_id in self.categories:
            return { "success": False, "error": "Category ID already exists." }
        # Optional: check for empty name, but not strictly required
        self.categories[category_id] = {
            "category_id": category_id,
            "category_name": category_name,
            "description": description
        }
        return { "success": True, "message": f"Category '{category_name}' created." }

    def update_file_location(self, book_id: str, new_file_location: str) -> dict:
        """
        Change the file location or storage reference for an uploaded book.

        Args:
            book_id (str): The unique identifier of the book whose file location should be updated.
            new_file_location (str): The new storage path or reference.

        Returns:
            dict: {
                "success": True,
                "message": "File location updated for book <book_id>."
            }
            or
            {
                "success": False,
                "error": "Book not found."
            }

        Constraints:
            - Book with given book_id must exist.
        """
        if book_id not in self.books:
            return {"success": False, "error": "Book not found."}
    
        self.books[book_id]['file_location'] = new_file_location
        return {
            "success": True,
            "message": f"File location updated for book {book_id}."
        }

    def set_supported_file_formats(self, formats: list) -> dict:
        """
        Update the platform's list of supported file formats (admin action).

        Args:
            formats (list): List of string file formats to support (e.g. ["PDF", "EPUB"]).

        Returns:
            dict:
                - On success: {'success': True, 'message': 'Supported file formats updated.'}
                - On failure: {'success': False, 'error': <reason>}

        Constraints:
            - All items in formats must be non-empty strings.
            - The list must not be empty, and must not contain duplicates.
        """
        if not isinstance(formats, list):
            return {"success": False, "error": "Input must be a list of format strings."}
        if not formats:
            return {"success": False, "error": "List of supported formats cannot be empty."}
        # Check for valid, non-empty, unique strings
        sanitized = []
        seen = set()
        for f in formats:
            if not isinstance(f, str) or not f.strip():
                return {"success": False, "error": "All formats must be non-empty strings."}
            ff = f.strip().upper()
            if ff in seen:
                return {"success": False, "error": f"Duplicate file format: {ff}"}
            seen.add(ff)
            sanitized.append(ff)
        self.supported_file_formats = sanitized
        return {"success": True, "message": f"Supported file formats updated: {sanitized}"}


class DigitalBookManagementPlatform(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_books_by_user(self, **kwargs):
        return self._call_inner_tool('get_books_by_user', kwargs)

    def get_book_by_id(self, **kwargs):
        return self._call_inner_tool('get_book_by_id', kwargs)

    def search_books_by_metadata(self, **kwargs):
        return self._call_inner_tool('search_books_by_metadata', kwargs)

    def list_all_books(self, **kwargs):
        return self._call_inner_tool('list_all_books', kwargs)

    def is_book_id_unique(self, **kwargs):
        return self._call_inner_tool('is_book_id_unique', kwargs)

    def get_supported_file_formats(self, **kwargs):
        return self._call_inner_tool('get_supported_file_formats', kwargs)

    def list_categories(self, **kwargs):
        return self._call_inner_tool('list_categories', kwargs)

    def get_category_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_by_id', kwargs)

    def get_categories_for_book(self, **kwargs):
        return self._call_inner_tool('get_categories_for_book', kwargs)

    def list_books_in_category(self, **kwargs):
        return self._call_inner_tool('list_books_in_category', kwargs)

    def get_book_category_associations(self, **kwargs):
        return self._call_inner_tool('get_book_category_associations', kwargs)

    def upload_new_book(self, **kwargs):
        return self._call_inner_tool('upload_new_book', kwargs)

    def edit_book_metadata(self, **kwargs):
        return self._call_inner_tool('edit_book_metadata', kwargs)

    def delete_book(self, **kwargs):
        return self._call_inner_tool('delete_book', kwargs)

    def assign_book_to_category(self, **kwargs):
        return self._call_inner_tool('assign_book_to_category', kwargs)

    def remove_book_from_category(self, **kwargs):
        return self._call_inner_tool('remove_book_from_category', kwargs)

    def create_category(self, **kwargs):
        return self._call_inner_tool('create_category', kwargs)

    def update_file_location(self, **kwargs):
        return self._call_inner_tool('update_file_location', kwargs)

    def set_supported_file_formats(self, **kwargs):
        return self._call_inner_tool('set_supported_file_formats', kwargs)
