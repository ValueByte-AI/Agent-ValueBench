# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from typing import Optional



# Book entity fields
class BookInfo(TypedDict):
    book_id: str
    title: str
    language: str
    description: str
    subject_tags: List[str]
    publication_date: str
    download_count: int

# Author entity fields
class AuthorInfo(TypedDict):
    author_id: str
    name: str
    birth_year: int
    death_year: int

# BookAuthor entity fields (not used directly, see structure below)
# Each book_id is mapped to a list of author_ids

# Resource entity fields
class ResourceInfo(TypedDict):
    resource_id: str
    book_id: str
    format: str
    url: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        State for the Project Gutenberg digital library environment.
        """

        # books: {book_id: BookInfo}
        # Entity: Book (book_id, title, language, description, subject_tags, publication_date, download_count)
        self.books: Dict[str, BookInfo] = {}

        # authors: {author_id: AuthorInfo}
        # Entity: Author (author_id, name, birth_year, death_year)
        self.authors: Dict[str, AuthorInfo] = {}

        # book_authors: {book_id: [author_id, ...]}
        # Entity: BookAuthor (book_id, author_id)
        self.book_authors: Dict[str, List[str]] = {}

        # resources: {book_id: [ResourceInfo, ...]}
        # Entity: Resource (resource_id, book_id, format, url)
        self.resources: Dict[str, List[ResourceInfo]] = {}

        # Constraints reminder:
        # - All books must have at least one resource (downloadable format).
        # - Each book can have multiple associated authors.
        # - Download counts are incremented only when a download link is accessed.
        # - Book searches are performed over indexed metadata fields (title, subject_tags, description, etc.).

    def search_books_by_metadata(self, query_term: str) -> dict:
        """
        Search for books where the query term appears in any indexed metadata field
        (title, subject_tags, description), returning a list of matching book IDs.

        Args:
            query_term (str): The string to search for (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # book_ids of all matching books.
            }
            or in case of input error:
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The search is case-insensitive.
            - The query term is matched as a substring of the field (for lists like subject_tags, match to any tag).
            - If no matches, return an empty list.
            - Indexed metadata fields: title, subject_tags, description.
            - If query_term is empty or whitespace, returns empty list (success).
        """
        # input validation
        if not isinstance(query_term, str):
            return {"success": False, "error": "Query term must be a string"}
        q = query_term.strip().lower()
        if not q:
            # Empty query: semantic to return no results.
            return {"success": True, "data": []}

        matching_ids = []
        for book_id, book in self.books.items():
            # Check title
            in_title = q in book.get("title", "").lower()
            # Check description
            in_description = q in book.get("description", "").lower()
            # Check any subject_tags
            in_tags = any(q in tag.lower() for tag in book.get("subject_tags", []))
            if in_title or in_description or in_tags:
                matching_ids.append(book_id)
        return {"success": True, "data": matching_ids}

    def get_book_info(self, book_id: str) -> dict:
        """
        Retrieve metadata of a book given its book_id.

        Args:
            book_id (str): The unique identifier of the book.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": BookInfo  # Book metadata (title, language, description, etc.)
                }
                or
                {
                    "success": False,
                    "error": "Book not found"
                }

        Constraints:
            - book_id must exist in the library.
        """
        book = self.books.get(book_id)
        if book is None:
            return { "success": False, "error": "Book not found" }
        return { "success": True, "data": book }

    def get_books_info_batch(self, book_ids: list[str]) -> dict:
        """
        Retrieve metadata for multiple books given a list of book_ids.

        Args:
            book_ids (list[str]): A list of book_id strings.

        Returns:
            dict:
                success: True and data as list of BookInfo for found book_ids, preserving input order and skips missing.
                    { "success": True, "data": [BookInfo, ...] }
                OR
                success: False and error message if none found.
                    { "success": False, "error": "No valid book_ids found." }

        Constraints:
            - Returns BookInfo only for book_ids that exist in the library.
            - Preserves the input order and includes duplicates if present.
            - If no IDs found, returns error.
        """
        result = []
        for book_id in book_ids:
            if book_id in self.books:
                result.append(self.books[book_id])

        if not result and book_ids:
            return { "success": False, "error": "No valid book_ids found." }
        return { "success": True, "data": result }

    def get_book_authors(self, book_id: str) -> dict:
        """
        Given a book_id, retrieve the list of associated author IDs and their full information
        (author_id, name, birth_year, death_year).

        Args:
            book_id (str): The ID of the book.

        Returns:
            dict: {
                "success": True,
                "data": List[Dict[str, Any]],  # Each entry contains author_id, name, birth_year, death_year.
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Book must exist.
            - Authors should exist for all associated author_ids.
        """
        # Check if book exists
        if book_id not in self.books:
            return { "success": False, "error": "Book not found" }

        author_ids = self.book_authors.get(book_id, [])
        result = []

        for author_id in author_ids:
            author_info = self.authors.get(author_id)
            if author_info:
                result.append({
                    "author_id": author_info["author_id"],
                    "name": author_info["name"],
                    "birth_year": author_info["birth_year"],
                    "death_year": author_info["death_year"]
                })
            # If author_info is missing, skip it (should not happen if DB is consistent)

        return { "success": True, "data": result }

    def get_author_info(self, author_id: str) -> dict:
        """
        Retrieve the full metadata for an author by their author_id.

        Args:
            author_id (str): Unique identifier for the author.

        Returns:
            dict: 
                - If found: { "success": True, "data": AuthorInfo }
                - If not found: { "success": False, "error": "Author not found" }

        Constraints:
            - author_id must exist in the authors dictionary.
        """
        author = self.authors.get(author_id)
        if author is None:
            return { "success": False, "error": "Author not found" }
        return { "success": True, "data": author }

    def get_book_resources(self, book_id: str) -> dict:
        """
        Retrieve all downloadable resources for a given book.

        Args:
            book_id (str): The unique identifier for the book.

        Returns:
            dict: {
                "success": True,
                "data": List[ResourceInfo]  # All downloadable resources for the book
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. book not found or no resources
            }

        Constraints:
            - Book with book_id must exist.
            - Book must have at least one resource (by environment constraint).
        """
        if book_id not in self.books:
            return { "success": False, "error": "Book not found" }

        resources = self.resources.get(book_id)
        if not resources or len(resources) == 0:
            # Should not normally happen, but handle defensively.
            return { "success": False, "error": "No resources available for this book" }

        return { "success": True, "data": resources }

    def get_download_count(self, book_id: str) -> dict:
        """
        Retrieve the current download count for a given book.

        Args:
            book_id (str): The unique identifier of the book.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": int  # The download count for the specified book
                }
                On failure:
                {
                    "success": False,
                    "error": str  # "Book not found"
                }
        Constraints:
            - Book must exist in the library.
        """
        book = self.books.get(book_id)
        if not book:
            return { "success": False, "error": "Book not found" }
        return { "success": True, "data": book["download_count"] }

    def list_books_by_author(self, author_id: str) -> dict:
        """
        Retrieve all book_ids authored by the specified author.

        Args:
            author_id (str): The unique identifier of the author.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[str]  # list of book_ids authored by author_id (may be empty)
                    }
                On error:
                    {
                        "success": False,
                        "error": "Author does not exist"
                    }

        Constraints:
            - The author_id must exist in the library.
            - Only book_ids to which this author is linked will be returned.
        """
        if author_id not in self.authors:
            return { "success": False, "error": "Author does not exist" }

        result = []
        for book_id, author_ids in self.book_authors.items():
            if author_id in author_ids:
                result.append(book_id)

        return { "success": True, "data": result }

    def list_all_books(self) -> dict:
        """
        Retrieve the IDs and minimal information (book_id and title) for all books in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[{"book_id": str, "title": str}],  # minimal info per book
            }
            or
            {
                "success": True,
                "data": []  # if no books exist
            }

        Constraints:
            - None (simply lists all books, no filtering).
        """
        result = [
            {"book_id": book_info["book_id"], "title": book_info["title"]}
            for book_info in self.books.values()
        ]
        return {"success": True, "data": result}

    def list_all_authors(self) -> dict:
        """
        Retrieve full info for all authors in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[AuthorInfo]  # List of all authors' info (may be empty if no authors)
            }
        """
        authors_list = list(self.authors.values())
        return { "success": True, "data": authors_list }

    def increment_download_count(self, book_id: str, resource_id: str) -> dict:
        """
        Simulate access of a download resource, incrementing the associated book's download_count.

        Args:
            book_id (str): The unique identifier of the book whose resource is being accessed.
            resource_id (str): The unique identifier of the resource being downloaded.

        Returns:
            dict: 
                On Success:
                    {
                        "success": True,
                        "message": "Download count incremented for book <book_id>"
                    }
                On Failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - book_id must exist in the library.
            - resource_id must exist for the given book_id.
            - Download count is incremented only when a valid resource is accessed.
        """
        # Check for valid book_id
        if book_id not in self.books:
            return {"success": False, "error": "Book not found"}

        # Check that the book has at least one resource
        resources = self.resources.get(book_id, [])
        resource_found = any(res["resource_id"] == resource_id for res in resources)
        if not resource_found:
            return {"success": False, "error": "Resource not found for the specified book"}

        # Increment download count
        self.books[book_id]["download_count"] += 1

        return {
            "success": True,
            "message": f"Download count incremented for book {book_id}"
        }

    def add_book(
        self,
        book_id: str,
        title: str,
        language: str,
        description: str,
        subject_tags: list,
        publication_date: str,
        resources: list,
        download_count: int = 0
    ) -> dict:
        """
        Add a new book to the library with metadata and initial downloadable resource(s).

        Args:
            book_id (str): Unique identifier for the book.
            title (str): Book title.
            language (str): Language code or name.
            description (str): Description text.
            subject_tags (List[str]): List of subject keywords.
            publication_date (str): Book's original publication date.
            resources (List[ResourceInfo]): List of downloadable resources for the book. At least one required.
            download_count (int, optional): Initial download count. Defaults to 0.

        Returns:
            dict: 
                On success: { "success": True, "message": "Book <book_id> added successfully." }
                On failure: { "success": False, "error": <error_message> }

        Constraints:
            - book_id must be unique (not already in system).
            - At least one resource must be provided, and all must match this book_id.
        """
        # Check for duplicate book_id
        if book_id in self.books:
            return { "success": False, "error": "Book ID already exists." }

        # Check resources nonempty
        if not resources or len(resources) == 0:
            return { "success": False, "error": "At least one downloadable resource is required for a new book." }

        # Validate subject_tags
        if not isinstance(subject_tags, list) or not all(isinstance(tag, str) for tag in subject_tags):
            return { "success": False, "error": "subject_tags must be a list of strings." }

        # Validate resources: all resource book_id must match new book_id
        for resource in resources:
            if 'book_id' not in resource or resource['book_id'] != book_id:
                return { "success": False, "error": "All resources must have matching book_id for the book being added." }
    
        # Create new BookInfo
        new_book: BookInfo = {
            "book_id": book_id,
            "title": title,
            "language": language,
            "description": description,
            "subject_tags": subject_tags,
            "publication_date": publication_date,
            "download_count": download_count
        }
        self.books[book_id] = new_book

        # Add resources
        self.resources[book_id] = []
        for resource in resources:
            self.resources[book_id].append(resource.copy())

        # (Authors may be linked via another method.)

        return { "success": True, "message": f"Book {book_id} added successfully." }

    def update_book_metadata(
        self,
        book_id: str,
        title: str = None,
        language: str = None,
        description: str = None,
        subject_tags: list = None,
        publication_date: str = None
    ) -> dict:
        """
        Modify the metadata fields (title, language, description, subject_tags, publication_date) of an existing book.
    
        Args:
            book_id (str): the ID of the book to update.
            title (str, optional): new title.
            language (str, optional): new language.
            description (str, optional): new description.
            subject_tags (List[str], optional): new subject tags.
            publication_date (str, optional): new publication date.
        
        Returns:
            dict:
                On success: { "success": True, "message": "Book metadata updated successfully" }
                On failure: { "success": False, "error": <reason> }
            
        Constraints:
            - Book must exist.
            - Only allows update of title, language, description, subject_tags, publication_date.
            - At least one valid field to update must be provided.
            - Does not permit update of book_id or download_count.
            - Field types must be correct.
        """
        if book_id not in self.books:
            return { "success": False, "error": "Book does not exist" }

        updatable_fields = ["title", "language", "description", "subject_tags", "publication_date"]
        update_args = {
            "title": title,
            "language": language,
            "description": description,
            "subject_tags": subject_tags,
            "publication_date": publication_date
        }

        changed = False
        for key, value in update_args.items():
            if value is not None:
                # Type check
                if key == "subject_tags":
                    if not isinstance(value, list) or not all(isinstance(tag, str) for tag in value):
                        return { "success": False, "error": "subject_tags must be a list of strings" }
                elif key in ["title", "language", "description", "publication_date"]:
                    if not isinstance(value, str):
                        return { "success": False, "error": f"{key} must be a string" }
                # Perform update
                self.books[book_id][key] = value
                changed = True

        if not changed:
            return { "success": False, "error": "No valid metadata fields provided for update" }

        return { "success": True, "message": "Book metadata updated successfully" }

    def delete_book(self, book_id: str) -> dict:
        """
        Remove a book (by book_id) from the library, including:
        - The book's core metadata,
        - All associated author relationships,
        - All resources for this book.

        Args:
            book_id (str): The unique identifier for the book to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Book and its relationships/resources deleted."
            }
            OR
            {
                "success": False,
                "error": "Book not found"
            }

        Constraints:
            - If the book does not exist, no changes made, error returned.
            - All references to the book must be removed from all state spaces.
        """
        if book_id not in self.books:
            return {"success": False, "error": "Book not found"}

        # Remove the book info
        self.books.pop(book_id, None)
        # Remove book-author relationships
        self.book_authors.pop(book_id, None)
        # Remove resources for this book
        self.resources.pop(book_id, None)

        return {
            "success": True,
            "message": "Book and its relationships/resources deleted."
        }

    def add_author(self, author_id: str, name: str, birth_year: int, death_year: int) -> dict:
        """
        Add a new author entity to the library.

        Args:
            author_id (str): Unique identifier for the author. Must not already exist.
            name (str): The author's name.
            birth_year (int): The year the author was born.
            death_year (int): The year the author died.

        Returns:
            dict: {
                "success": True,
                "message": "Author <name> (ID: <author_id>) added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Author IDs must be unique within the system.
        """
        if author_id in self.authors:
            return { "success": False, "error": "Author ID already exists." }
    
        self.authors[author_id] = {
            "author_id": author_id,
            "name": name,
            "birth_year": birth_year,
            "death_year": death_year
        }
        return { "success": True, "message": f"Author {name} (ID: {author_id}) added successfully." }

    def link_author_to_book(self, book_id: str, author_id: str) -> dict:
        """
        Associate an additional author with an existing book.

        Args:
            book_id (str): The identifier for the book to link.
            author_id (str): The identifier for the author to associate.

        Returns:
            dict: 
                - {"success": True, "message": "Author linked to book successfully."}
                - {"success": False, "error": <reason str>}
    
        Constraints:
            - Both book and author must exist.
            - The association must not already be present (no duplicates).
        """
        if book_id not in self.books:
            return {"success": False, "error": "Book does not exist."}
        if author_id not in self.authors:
            return {"success": False, "error": "Author does not exist."}

        if book_id not in self.book_authors:
            self.book_authors[book_id] = []

        if author_id in self.book_authors[book_id]:
            return {"success": False, "error": "Author is already linked to this book."}

        self.book_authors[book_id].append(author_id)
        return {"success": True, "message": "Author linked to book successfully."}


    def add_resource_to_book(
        self, 
        book_id: str, 
        format: str, 
        url: str
    ) -> dict:
        """
        Add a new downloadable resource (by format and url) to an existing book.

        Args:
            book_id (str): ID of the book to which to add the resource.
            format (str): Resource format string (e.g., 'epub', 'html', 'pdf').
            url (str): Download URL for the resource.

        Returns:
            dict: Success or failure.
                - On success: { "success": True, "message": str }
                - On failure: { "success": False, "error": str }

        Constraints:
            - book_id must exist.
            - format and url must be non-empty.
            - Duplicate (format, url) for this book not allowed.
            - Resource_id will be a generated UUID.
        """
        if not book_id or book_id not in self.books:
            return {"success": False, "error": "Book does not exist."}
        if not format or not format.strip():
            return {"success": False, "error": "Resource format is required."}
        if not url or not url.strip():
            return {"success": False, "error": "Resource URL is required."}

        resources = self.resources.get(book_id, [])
        for res in resources:
            if res["format"] == format and res["url"] == url:
                return {"success": False, "error": "Resource with same format and URL already exists for this book."}

        # Generate a unique resource_id
        resource_id = str(uuid.uuid4())
        new_resource = {
            "resource_id": resource_id,
            "book_id": book_id,
            "format": format,
            "url": url
        }

        resources.append(new_resource)
        self.resources[book_id] = resources

        return {
            "success": True,
            "message": f"Resource added to book {book_id}."
        }

    def remove_resource_from_book(self, book_id: str, resource_id: str) -> dict:
        """
        Remove an existing downloadable resource (by resource_id) from a book.

        Args:
            book_id (str): The unique identifier of the book.
            resource_id (str): The identifier of the resource to remove.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Resource <resource_id> removed from book <book_id>." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - The book must exist.
            - The resource must exist for the specified book.
            - The book must have at least one resource after removal.
        """
        if book_id not in self.books:
            return {"success": False, "error": f"Book {book_id} does not exist."}

        if book_id not in self.resources or not self.resources[book_id]:
            return {"success": False, "error": f"No resources found for book {book_id}."}

        resource_list = self.resources[book_id]
        resource_found = False

        # Find and remove the resource
        for idx, res in enumerate(resource_list):
            if res["resource_id"] == resource_id:
                resource_found = True
                # Check if removal would leave zero resources (not allowed)
                if len(resource_list) == 1:
                    return {
                        "success": False,
                        "error": f"Cannot remove the last resource from book {book_id}."
                    }
                # Safe to remove
                del resource_list[idx]
                self.resources[book_id] = resource_list
                return {
                    "success": True,
                    "message": f"Resource {resource_id} removed from book {book_id}."
                }

        if not resource_found:
            return {
                "success": False,
                "error": f"Resource {resource_id} not found for book {book_id}."
            }

    def update_resource(
        self,
        resource_id: str,
        format: str = None,
        url: str = None
    ) -> dict:
        """
        Update the metadata (format, url) for a specific resource by resource_id.

        Args:
            resource_id (str): Unique identifier of the resource to update.
            format (str, optional): New format value for the resource.
            url (str, optional): New URL for the resource.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str  # Resource not found, or no update parameters provided.
            }

        Constraints:
            - The resource must exist in the library.
            - At least one of `format` or `url` must be provided to update.
        """
        if format is None and url is None:
            return {
                "success": False,
                "error": "No update parameters provided. Specify at least one of 'format' or 'url'."
            }
        # Search for resource in all books
        for book_id, res_list in self.resources.items():
            for res in res_list:
                if res["resource_id"] == resource_id:
                    updated_fields = []
                    if format is not None:
                        res["format"] = format
                        updated_fields.append("format")
                    if url is not None:
                        res["url"] = url
                        updated_fields.append("url")
                    if updated_fields:
                        return {
                            "success": True,
                            "message": f"Resource {resource_id} updated: {', '.join(updated_fields)}."
                        }
                    else:
                        return {
                            "success": True,
                            "message": "No fields were actually changed (provided values match existing values)."
                        }
        return {
            "success": False,
            "error": "Resource not found"
        }


class ProjectGutenbergLibrary(BaseEnv):
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

    def search_books_by_metadata(self, **kwargs):
        return self._call_inner_tool('search_books_by_metadata', kwargs)

    def get_book_info(self, **kwargs):
        return self._call_inner_tool('get_book_info', kwargs)

    def get_books_info_batch(self, **kwargs):
        return self._call_inner_tool('get_books_info_batch', kwargs)

    def get_book_authors(self, **kwargs):
        return self._call_inner_tool('get_book_authors', kwargs)

    def get_author_info(self, **kwargs):
        return self._call_inner_tool('get_author_info', kwargs)

    def get_book_resources(self, **kwargs):
        return self._call_inner_tool('get_book_resources', kwargs)

    def get_download_count(self, **kwargs):
        return self._call_inner_tool('get_download_count', kwargs)

    def list_books_by_author(self, **kwargs):
        return self._call_inner_tool('list_books_by_author', kwargs)

    def list_all_books(self, **kwargs):
        return self._call_inner_tool('list_all_books', kwargs)

    def list_all_authors(self, **kwargs):
        return self._call_inner_tool('list_all_authors', kwargs)

    def increment_download_count(self, **kwargs):
        return self._call_inner_tool('increment_download_count', kwargs)

    def add_book(self, **kwargs):
        return self._call_inner_tool('add_book', kwargs)

    def update_book_metadata(self, **kwargs):
        return self._call_inner_tool('update_book_metadata', kwargs)

    def delete_book(self, **kwargs):
        return self._call_inner_tool('delete_book', kwargs)

    def add_author(self, **kwargs):
        return self._call_inner_tool('add_author', kwargs)

    def link_author_to_book(self, **kwargs):
        return self._call_inner_tool('link_author_to_book', kwargs)

    def add_resource_to_book(self, **kwargs):
        return self._call_inner_tool('add_resource_to_book', kwargs)

    def remove_resource_from_book(self, **kwargs):
        return self._call_inner_tool('remove_resource_from_book', kwargs)

    def update_resource(self, **kwargs):
        return self._call_inner_tool('update_resource', kwargs)

