# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class ArticleInfo(TypedDict):
    article_id: str
    title: str
    content: str
    summary: str
    publication_date: str
    status: str
    author_id: str
    category_id: str
    source_id: str
    media_link: str

class AuthorInfo(TypedDict):
    author_id: str
    name: str
    bio: str
    contact_info: str
    sta: str  # As per source; possibly "status" or similar.

class CategoryInfo(TypedDict):
    category_id: str
    name: str
    description: str

class SourceInfo(TypedDict):
    source_id: str
    name: str
    url: str
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        News website content management system environment.
        """

        # Articles: {article_id: ArticleInfo}
        self.articles: Dict[str, ArticleInfo] = {}

        # Authors: {author_id: AuthorInfo}
        self.authors: Dict[str, AuthorInfo] = {}

        # Categories: {category_id: CategoryInfo}
        self.categories: Dict[str, CategoryInfo] = {}

        # Sources: {source_id: SourceInfo}
        self.sources: Dict[str, SourceInfo] = {}

        # Constraints:
        # - Each article must be linked to a valid source and author.
        # - Articles may be unpublished, scheduled for publication, or live;
        #   only published articles are visible to end-users.
        # - Article IDs are unique within the system.
        # - Categories and sources must be created before associating articles with them.

    def get_article_by_id(self, article_id: str) -> dict:
        """
        Retrieve the full details (all ArticleInfo fields) of a specific article using its unique article_id.

        Args:
            article_id (str): The unique identifier of the article to retrieve.

        Returns:
            dict:
                - If found: {"success": True, "data": ArticleInfo}
                - If not found: {"success": False, "error": "Article not found"}

        Constraints:
            - The article_id must exist in the CMS's records.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article not found" }
    
        return { "success": True, "data": self.articles[article_id] }

    def list_articles_by_source(self, source_id: str = None, source_name: str = None) -> dict:
        """
        Retrieve all articles associated with a given source, specified by either source_id or source_name.

        Args:
            source_id (str, optional): The unique identifier of the source.
            source_name (str, optional): The unique name of the source.

        Returns:
            dict:
                success (bool): Whether the operation succeeded.
                data (list[ArticleInfo]): Articles linked to the source (may be empty).
                error (str, optional): Error message, if any.

        Constraints:
            - At least one of source_id or source_name must be provided.
            - Source must exist.
        """
        resolved_source_id = None

        # Resolve source_id
        if source_id:
            if source_id not in self.sources:
                return {"success": False, "error": "Source with given source_id does not exist"}
            resolved_source_id = source_id
        elif source_name:
            # Search for source by name
            for src in self.sources.values():
                if src["name"] == source_name:
                    resolved_source_id = src["source_id"]
                    break
            if not resolved_source_id:
                return {"success": False, "error": "Source with given name does not exist"}
        else:
            return {"success": False, "error": "Must provide source_id or source_name"}

        # Gather all articles with matching source_id
        articles = [
            article for article in self.articles.values()
            if article["source_id"] == resolved_source_id
        ]

        return {"success": True, "data": articles}

    def get_articles_by_ids_from_source(self, article_ids: list[str], source_id: str) -> dict:
        """
        Retrieve article info for the specified article_ids, **only** if each article belongs to the given source.

        Args:
            article_ids (List[str]): List of article IDs to retrieve.
            source_id (str): Source ID to filter articles by.

        Returns:
            dict:
                - On success: {
                    'success': True,
                    'data': List[ArticleInfo]  # Each member matches both ID and source
                  }
                - On failure: {
                    'success': False,
                    'error': str  # e.g. source does not exist
                  }

        Constraints:
            - The provided source_id must exist.
            - Any article_ids not found or not matching that source are skipped.
        """
        if source_id not in self.sources:
            return { "success": False, "error": "Source does not exist" }

        result = []
        for article_id in article_ids:
            article = self.articles.get(article_id)
            if article and article['source_id'] == source_id:
                result.append(article)

        return { "success": True, "data": result }

    def get_source_by_name(self, name: str) -> dict:
        """
        Retrieve full source details (SourceInfo) given the source's name.

        Args:
            name (str): The name of the source to look up.

        Returns:
            dict: 
                If found: {"success": True, "data": SourceInfo}
                If not found: {"success": False, "error": "Source not found"}

        Constraints:
            - The provided name must match a source's name exactly.
        """
        for source in self.sources.values():
            if source["name"] == name:
                return {"success": True, "data": source}
        return {"success": False, "error": "Source not found"}

    def get_author_by_id(self, author_id: str) -> dict:
        """
        Retrieve full details of an author by their author_id.

        Args:
            author_id (str): The unique identifier of the author.

        Returns:
            dict: {
                "success": True,
                "data": AuthorInfo   # Author's complete information.
            }
            or
            {
                "success": False,
                "error": str         # Error message if author_id does not exist.
            }

        Constraints:
            - author_id must exist in the system.
        """
        if author_id not in self.authors:
            return {"success": False, "error": "Author not found"}
        return {"success": True, "data": self.authors[author_id]}

    def get_category_by_id(self, category_id: str) -> dict:
        """
        Retrieve full details about a category given its category_id.

        Args:
            category_id (str): The ID of the category to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": CategoryInfo,  # If category found
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. 'Category not found'
            }

        Constraints:
            - category_id must exist in self.categories.
        """
        category = self.categories.get(category_id)
        if category is None:
            return { "success": False, "error": "Category not found" }
        return { "success": True, "data": category }

    def list_articles_by_status(self, status: str) -> dict:
        """
        Retrieve all articles filtered by a given publication status.

        Args:
            status (str): The publication status to filter by. Must be one of:
                          'published', 'unpublished', or 'scheduled'.

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo]  # List of articles with the exact status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message (e.g., invalid status)
            }

        Constraints:
            - Status must be 'published', 'unpublished', or 'scheduled'.
        """
        allowed_statuses = {"published", "unpublished", "scheduled"}
        if status not in allowed_statuses:
            return { "success": False, "error": "Invalid article status" }

        result = [article for article in self.articles.values() if article["status"] == status]
        return { "success": True, "data": result }

    def list_articles_by_author(self, author_id: str) -> dict:
        """
        Retrieve all articles written by the specified author.

        Args:
            author_id (str): ID of the author whose articles to list.

        Returns:
            dict:
                success (bool): True if author exists (query ran), False if invalid author.
                data (List[ArticleInfo]): List of article info for matching articles (empty if none), present only if success.
                error (str): Error message if failed.
    
        Constraints:
            - The given author_id must exist in the system.
        """
        if author_id not in self.authors:
            return {
                "success": False,
                "error": "Author does not exist"
            }
        articles = [
            article_info
            for article_info in self.articles.values()
            if article_info["author_id"] == author_id
        ]
        return {
            "success": True,
            "data": articles
        }

    def list_all_sources(self) -> dict:
        """
        Retrieve all available content sources in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[SourceInfo]  # List of all sources, possibly empty.
            }
        Constraints:
            - No input arguments. Always succeeds.
            - Returns empty list if there are no sources in the system.
        """
        sources_list = list(self.sources.values())
        return { "success": True, "data": sources_list }

    def list_all_categories(self) -> dict:
        """
        Retrieve all categories currently defined in the system.

        Returns:
            dict:
                - success (bool): True if retrieval was successful.
                - data (List[CategoryInfo]): List of all category info structs (may be empty).

        Constraints:
            - No constraints apply; all categories in the state are returned.
            - If there are no categories, returns an empty list.
        """
        return {
            "success": True,
            "data": list(self.categories.values())
        }

    def create_article(
        self,
        article_id: str,
        title: str,
        content: str,
        summary: str,
        publication_date: str,
        status: str,
        author_id: str,
        category_id: str,
        source_id: str,
        media_link: str
    ) -> dict:
        """
        Add a new article to the CMS system, checking for all required associations.

        Args:
            article_id (str): Unique identifier for the article.
            title (str): Title of the article.
            content (str): Full content/body of the article.
            summary (str): Short summary/abstract.
            publication_date (str): Date/time of publication (expected date string).
            status (str): Current status (e.g., 'published', 'draft').
            author_id (str): ID of the author (must exist).
            category_id (str): ID of the category (must exist).
            source_id (str): ID of the source (must exist).
            media_link (str): URL or path to associated media.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Article '<article_id>' created successfully." }
              - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Article ID must be unique.
            - author_id, category_id, and source_id must exist in their respective tables.
            - All fields are required and must not be empty.
        """
        # Check required fields
        fields = {
            "article_id": article_id, "title": title, "content": content,
            "summary": summary, "publication_date": publication_date,
            "status": status, "author_id": author_id, "category_id": category_id,
            "source_id": source_id, "media_link": media_link
        }
        for key, val in fields.items():
            if val is None or (isinstance(val, str) and val.strip() == ""):
                return { "success": False, "error": f"Missing or empty field: {key}" }

        # Check for unique article ID
        if article_id in self.articles:
            return { "success": False, "error": "Article ID already exists." }

        # Check existence of author
        if author_id not in self.authors:
            return { "success": False, "error": "Author not found." }

        # Check existence of category
        if category_id not in self.categories:
            return { "success": False, "error": "Category not found." }

        # Check existence of source
        if source_id not in self.sources:
            return { "success": False, "error": "Source not found." }

        # All checks passed; create the article
        self.articles[article_id] = {
            "article_id": article_id,
            "title": title,
            "content": content,
            "summary": summary,
            "publication_date": publication_date,
            "status": status,
            "author_id": author_id,
            "category_id": category_id,
            "source_id": source_id,
            "media_link": media_link
        }

        return { "success": True, "message": f"Article '{article_id}' created successfully." }

    def update_article(
        self,
        article_id: str,
        title: str = None,
        content: str = None,
        summary: str = None,
        publication_date: str = None,
        status: str = None,
        author_id: str = None,
        category_id: str = None,
        source_id: str = None,
        media_link: str = None,
    ) -> dict:
        """
        Update an existing article’s content, metadata, or associations.

        Args:
            article_id (str): The ID of the article to update.
            title (str, optional): New title for the article.
            content (str, optional): New content for the article.
            summary (str, optional): New summary for the article.
            publication_date (str, optional): New publication date.
            status (str, optional): New status.
            author_id (str, optional): ID of the new author (must exist).
            category_id (str, optional): ID of the new category (must exist).
            source_id (str, optional): ID of the new source (must exist).
            media_link (str, optional): New media link.

        Returns:
            dict: {
                "success": True,
                "message": "Article updated successfully"
            } or {
                "success": False,
                "error": str
            }

        Constraints:
            - Article must exist.
            - If updating author/source/category, new reference must exist.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article not found" }

        article = self.articles[article_id]

        # Check associations if updating
        if author_id is not None:
            if author_id not in self.authors:
                return { "success": False, "error": "Author does not exist" }
            article["author_id"] = author_id
        if category_id is not None:
            if category_id not in self.categories:
                return { "success": False, "error": "Category does not exist" }
            article["category_id"] = category_id
        if source_id is not None:
            if source_id not in self.sources:
                return { "success": False, "error": "Source does not exist" }
            article["source_id"] = source_id

        # Update any other fields if given
        if title is not None:
            article["title"] = title
        if content is not None:
            article["content"] = content
        if summary is not None:
            article["summary"] = summary
        if publication_date is not None:
            article["publication_date"] = publication_date
        if status is not None:
            article["status"] = status
        if media_link is not None:
            article["media_link"] = media_link

        self.articles[article_id] = article
        return { "success": True, "message": "Article updated successfully" }

    def delete_article(self, article_id: str) -> dict:
        """
        Remove an article from the system by its article_id.

        Args:
            article_id (str): Unique identifier of the article to remove.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message
            }
            OR
            {
                "success": False,
                "error": str  # Error message if article_id does not exist
            }

        Constraints:
            - The article must exist in the system.
            - Removal is permanent; no cascading or additional constraints required.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article not found" }
    
        del self.articles[article_id]
        return { "success": True, "message": f"Article {article_id} deleted" }

    def change_article_status(self, article_id: str, new_status: str) -> dict:
        """
        Changes the publication status of an article (e.g., publish, schedule, unpublish).

        Args:
            article_id (str): The unique ID of the article whose status is to be changed.
            new_status (str): The new status value ('published', 'scheduled', 'unpublished').

        Returns:
            dict: 
                If successful:
                    { "success": True, "message": "Article status updated to <new_status>" }
                If error:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Article must exist.
            - new_status must be one of ['published', 'scheduled', 'unpublished'].
        """
        allowed_statuses = ['published', 'scheduled', 'unpublished']
        if article_id not in self.articles:
            return { "success": False, "error": "Article does not exist" }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status: {new_status}" }

        # Change status
        self.articles[article_id]['status'] = new_status
        return { "success": True, "message": f"Article status updated to {new_status}" }

    def create_source(self, source_id: str, name: str, url: str, description: str) -> dict:
        """
        Add a new content source to the system.

        Args:
            source_id (str): Unique identifier for the source.
            name (str): Name of the source.
            url (str): Website or content source URL.
            description (str): Description of the source.

        Returns:
            dict: {
                "success": True,
                "message": "Source <source_id> created successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - source_id must be unique.
            - All fields are required and must not be empty.
        """
        # Basic validation
        if not (source_id and name and url and description):
            return {
                "success": False,
                "error": "All fields (source_id, name, url, description) are required and must not be empty."
            }
        if source_id in self.sources:
            return {
                "success": False,
                "error": f"Source with ID '{source_id}' already exists."
            }
        self.sources[source_id] = {
            "source_id": source_id,
            "name": name,
            "url": url,
            "description": description
        }
        return {
            "success": True,
            "message": f"Source '{source_id}' created successfully."
        }

    def update_source(self, source_id: str, name: str = None, url: str = None, description: str = None) -> dict:
        """
        Edit (update) metadata for an existing source.

        Args:
            source_id (str): The identifier of the source to update.
            name (str, optional): New name for the source.
            url (str, optional): New URL for the source.
            description (str, optional): New description for the source.

        Returns:
            dict: {
                "success": True,
                "message": "Source updated successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The source_id must exist in the system.
            - Only the provided fields are updated.
            - If none of the fields are provided, no changes are made, but the operation is still treated as successful.
        """
        if source_id not in self.sources:
            return { "success": False, "error": "Source does not exist" }
    
        source = self.sources[source_id]
        updated = False
        if name is not None:
            source["name"] = name
            updated = True
        if url is not None:
            source["url"] = url
            updated = True
        if description is not None:
            source["description"] = description
            updated = True

        # No changes is not an error; treat as success regardless.
        return { "success": True, "message": "Source updated successfully" }

    def delete_source(self, source_id: str) -> dict:
        """
        Remove a content source from the system.

        Args:
            source_id (str): The unique identifier of the source to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Source <source_id> deleted"
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - The source must exist.
            - Cannot delete if any article is currently associated with this source.
        """
        if source_id not in self.sources:
            return { "success": False, "error": "Source does not exist" }

        # Check if any article references this source
        for article in self.articles.values():
            if article["source_id"] == source_id:
                return {
                    "success": False,
                    "error": f"Cannot delete source: Article {article['article_id']} is linked to this source"
                }

        # Passed checks; safe to delete
        del self.sources[source_id]
        return {
            "success": True,
            "message": f"Source {source_id} deleted"
        }

    def create_category(self, category_id: str, name: str, description: str) -> dict:
        """
        Add a new category to the system.

        Args:
            category_id (str): Unique identifier for the category.
            name (str): The human-readable category name.
            description (str): Description of the category.

        Returns:
            dict: On success:
                      { "success": True, "message": "Category created successfully." }
                  On failure (e.g., ID exists):
                      { "success": False, "error": "<reason>" }

        Constraints:
            - category_id must be unique in self.categories.
        """
        if not category_id or not isinstance(category_id, str):
            return { "success": False, "error": "Invalid or missing category_id." }
        if category_id in self.categories:
            return { "success": False, "error": "Category ID already exists." }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid or missing category name." }
        if not isinstance(description, str):
            return { "success": False, "error": "Invalid category description." }

        self.categories[category_id] = {
            "category_id": category_id,
            "name": name,
            "description": description
        }

        return { "success": True, "message": "Category created successfully." }

    def update_category(
        self,
        category_id: str,
        name: str = None,
        description: str = None
    ) -> dict:
        """
        Update a category's name and/or description.

        Args:
            category_id (str): The ID of the category to update.
            name (str, optional): The new name for the category (if updating).
            description (str, optional): The new description for the category (if updating).

        Returns:
            dict: {
                "success": True,
                "message": "Category updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - category_id must exist in self.categories.
            - At least one of name or description should be provided to actually update the category,
              but if both are None, treated as a no-op (success, nothing changed).
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist." }

        # Fetch the category info
        category = self.categories[category_id]

        fields_updated = []

        if name is not None:
            category["name"] = name
            fields_updated.append("name")
        if description is not None:
            category["description"] = description
            fields_updated.append("description")

        # No-op is allowed (no fields updated), but still success.
        return {
            "success": True,
            "message": (
                "Category updated successfully."
                if fields_updated else
                "No fields changed for category."
            )
        }

    def delete_category(self, category_id: str) -> dict:
        """
        Remove a category from the system if there are no articles referencing it.

        Args:
            category_id (str): The ID of the category to remove.

        Returns:
            dict: 
                - {"success": True, "message": "Category deleted"} if deletion succeeds.
                - {"success": False, "error": "..."} if:
                    - The category does not exist
                    - The category is still referenced by one or more articles

        Constraints:
            - The category must exist.
            - The category cannot be deleted if any article references it (referential integrity).
        """
        # Check if category exists
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist"}

        # Check if any articles refer to this category
        for article in self.articles.values():
            if article.get("category_id") == category_id:
                return {
                    "success": False,
                    "error": "Cannot delete: One or more articles are associated with this category"
                }
    
        # Safe to delete
        del self.categories[category_id]
        return {"success": True, "message": "Category deleted"}

    def create_author(self, author_id: str, name: str, bio: str, contact_info: str, sta: str) -> dict:
        """
        Add a new author to the system.

        Args:
            author_id (str): The unique identifier for the author.
            name (str): The author's name.
            bio (str): The author's biography.
            contact_info (str): Contact information for the author.
            sta (str): Author status or similar.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Author <author_id> created." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Author IDs must be unique.
            - All fields are required (no missing/empty fields).
        """
        # Check if author_id already exists
        if author_id in self.authors:
            return { "success": False, "error": f"Author with id '{author_id}' already exists." }
    
        # Basic field presence checks (could be more strict, here just check not empty)
        if not all([author_id, name, bio, contact_info, sta]):
            return { "success": False, "error": "All fields (author_id, name, bio, contact_info, sta) are required." }
    
        # Add author
        self.authors[author_id] = {
            "author_id": author_id,
            "name": name,
            "bio": bio,
            "contact_info": contact_info,
            "sta": sta
        }
        return { "success": True, "message": f"Author '{author_id}' created." }

    def update_author(
        self,
        author_id: str,
        name: str = None,
        bio: str = None,
        contact_info: str = None,
        sta: str = None
    ) -> dict:
        """
        Edit an author's details.

        Args:
            author_id (str): The ID of the author to update.
            name (str, optional): New author name.
            bio (str, optional): New bio for the author.
            contact_info (str, optional): New contact information.
            sta (str, optional): New status (or similar; as per schema).

        Returns:
            dict:
                - On success: {'success': True, 'message': 'Author updated successfully'}
                - On failure: {'success': False, 'error': 'reason'}

        Constraints:
            - The author must exist.
            - At least one updatable field must be provided.
        """
        # Check author existence
        if author_id not in self.authors:
            return {"success": False, "error": "Author does not exist."}

        # Build updates
        updates = {}
        if name is not None:
            updates["name"] = name
        if bio is not None:
            updates["bio"] = bio
        if contact_info is not None:
            updates["contact_info"] = contact_info
        if sta is not None:
            updates["sta"] = sta

        if not updates:
            return {"success": False, "error": "No update fields provided."}

        # Apply updates
        self.authors[author_id].update(updates)
        return {"success": True, "message": "Author updated successfully"}

    def delete_author(self, author_id: str) -> dict:
        """
        Remove an author from the system.

        Args:
            author_id (str): The ID of the author to remove.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Author <author_id> deleted." }
              - On failure (author not found): { "success": False, "error": "Author not found." }
              - On failure (author still referenced): { "success": False, "error": "Cannot delete author: author is still assigned to one or more articles." }

        Constraints:
            - Author cannot be deleted if referenced by any article.
            - author_id must exist in the system.
        """
        if author_id not in self.authors:
            return { "success": False, "error": "Author not found." }

        for article in self.articles.values():
            if article['author_id'] == author_id:
                return {
                    "success": False,
                    "error": "Cannot delete author: author is still assigned to one or more articles."
                }

        del self.authors[author_id]
        return { "success": True, "message": f"Author {author_id} deleted." }


class NewsWebsiteCMS(BaseEnv):
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

    def get_article_by_id(self, **kwargs):
        return self._call_inner_tool('get_article_by_id', kwargs)

    def list_articles_by_source(self, **kwargs):
        return self._call_inner_tool('list_articles_by_source', kwargs)

    def get_articles_by_ids_from_source(self, **kwargs):
        return self._call_inner_tool('get_articles_by_ids_from_source', kwargs)

    def get_source_by_name(self, **kwargs):
        return self._call_inner_tool('get_source_by_name', kwargs)

    def get_author_by_id(self, **kwargs):
        return self._call_inner_tool('get_author_by_id', kwargs)

    def get_category_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_by_id', kwargs)

    def list_articles_by_status(self, **kwargs):
        return self._call_inner_tool('list_articles_by_status', kwargs)

    def list_articles_by_author(self, **kwargs):
        return self._call_inner_tool('list_articles_by_author', kwargs)

    def list_all_sources(self, **kwargs):
        return self._call_inner_tool('list_all_sources', kwargs)

    def list_all_categories(self, **kwargs):
        return self._call_inner_tool('list_all_categories', kwargs)

    def create_article(self, **kwargs):
        return self._call_inner_tool('create_article', kwargs)

    def update_article(self, **kwargs):
        return self._call_inner_tool('update_article', kwargs)

    def delete_article(self, **kwargs):
        return self._call_inner_tool('delete_article', kwargs)

    def change_article_status(self, **kwargs):
        return self._call_inner_tool('change_article_status', kwargs)

    def create_source(self, **kwargs):
        return self._call_inner_tool('create_source', kwargs)

    def update_source(self, **kwargs):
        return self._call_inner_tool('update_source', kwargs)

    def delete_source(self, **kwargs):
        return self._call_inner_tool('delete_source', kwargs)

    def create_category(self, **kwargs):
        return self._call_inner_tool('create_category', kwargs)

    def update_category(self, **kwargs):
        return self._call_inner_tool('update_category', kwargs)

    def delete_category(self, **kwargs):
        return self._call_inner_tool('delete_category', kwargs)

    def create_author(self, **kwargs):
        return self._call_inner_tool('create_author', kwargs)

    def update_author(self, **kwargs):
        return self._call_inner_tool('update_author', kwargs)

    def delete_author(self, **kwargs):
        return self._call_inner_tool('delete_author', kwargs)

