# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ArticleInfo(TypedDict):
    article_id: str
    title: str
    body: str
    section_id: str
    author_id: str
    publication_date: str
    keywords: List[str]
    status: str  # e.g., 'draft', 'published'

class SectionInfo(TypedDict):
    section_id: str
    name: str
    description: str

class AuthorInfo(TypedDict):
    author_id: str
    name: str
    bio: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Articles: {article_id: ArticleInfo}
        self.articles: Dict[str, ArticleInfo] = {}
        # Sections: {section_id: SectionInfo}
        self.sections: Dict[str, SectionInfo] = {}
        # Authors: {author_id: AuthorInfo}
        self.authors: Dict[str, AuthorInfo] = {}

        # Constraints:
        # - Only articles with status "published" are shown to readers.
        # - Each article must have exactly one section and one author.
        # - Publication date must be set for published articles.
        # - Keywords should be searchable to facilitate content discovery.

    def get_section_by_name(self, name: str) -> dict:
        """
        Retrieve section information and section_id by the name.

        Args:
            name (str): The section name to search for (case-sensitive).

        Returns:
            dict: 
                { "success": True, "data": SectionInfo }
                OR
                { "success": False, "error": "Section not found" }
        """
        for section in self.sections.values():
            if section["name"] == name:
                return { "success": True, "data": section }
        return { "success": False, "error": "Section not found" }

    def get_section_by_id(self, section_id: str) -> dict:
        """
        Retrieve section information given its section_id.

        Args:
            section_id (str): The unique identifier of the section.

        Returns:
            dict: {
                "success": True,
                "data": SectionInfo,  # Information about the section
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "Section not found"
            }
        """
        section = self.sections.get(section_id)
        if section is None:
            return { "success": False, "error": "Section not found" }
        return { "success": True, "data": section }

    def list_all_sections(self) -> dict:
        """
        List all available news sections/categories in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[SectionInfo],  # List of all sections (may be empty if none created)
            }
        """
        all_sections = list(self.sections.values())
        return { "success": True, "data": all_sections }

    def get_author_by_id(self, author_id: str) -> dict:
        """
        Retrieve author information given the author_id.

        Args:
            author_id (str): The unique identifier of the author.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "data": AuthorInfo  # Dictionary of author attributes
                }
                Failure: {
                    "success": False,
                    "error": str  # Reason for failure (e.g. author not found)
                }
        """
        author = self.authors.get(author_id)
        if author is None:
            return { "success": False, "error": "Author not found" }
        return { "success": True, "data": author }

    def list_all_authors(self) -> dict:
        """
        List all journalists/authors in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[AuthorInfo]  # List of all authors (may be empty if none present)
            }
        """
        return {
            "success": True,
            "data": list(self.authors.values())
        }

    def list_articles_by_section(self, section_id: str, status: str = None) -> dict:
        """
        List articles that belong to a given section_id, 
        optionally filtering by article status (e.g., 'published', 'draft').

        Args:
            section_id (str): ID of the section to query.
            status (str, optional): Filter articles by this status ('published', 'draft', etc.)
    
        Returns:
            dict:
                - success (bool)
                - data: list of ArticleInfo (if success)
                - error (str) if failed

        Constraints:
            - section_id must exist in sections.
        """
        if section_id not in self.sections:
            return { "success": False, "error": "Section does not exist" }
    
        articles = [
            article for article in self.articles.values()
            if article["section_id"] == section_id and (status is None or article["status"] == status)
        ]
        return { "success": True, "data": articles }

    def list_articles_by_status(self, status: str) -> dict:
        """
        List all articles currently in the specified status across the entire backlog.

        Args:
            status (str): Article status to filter by, e.g. "draft" or "published".

        Returns:
            dict:
                - success (bool)
                - data: list of ArticleInfo (if success)
                - error (str) if failed

        Constraints:
            - status must be a non-empty string.
        """
        if not isinstance(status, str) or not status.strip():
            return {"success": False, "error": "Invalid status input"}

        normalized_status = status.strip()
        articles = [
            article for article in self.articles.values()
            if article["status"] == normalized_status
        ]
        return {"success": True, "data": articles}

    def list_published_articles_by_section(self, section_id: str) -> dict:
        """
        List all articles with status 'published' in the specified section, 
        sorted by publication_date (most recent first).

        Args:
            section_id (str): The id of the news section.

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo]  # May be empty if no articles found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
        
        Constraints:
            - Section must exist.
            - Only return articles with status 'published' and matching section_id.
            - All returned articles have publication_date set.
        """
        if section_id not in self.sections:
            return {"success": False, "error": "Section does not exist"}

        articles = [
            article for article in self.articles.values()
            if article["status"] == "published"
            and article["section_id"] == section_id
            and article.get("publication_date")  # ensure date is set
        ]

        # Sorting: most recent first. Assumes publication_date is ISO8601 string.
        articles_sorted = sorted(
            articles,
            key=lambda x: x["publication_date"],
            reverse=True
        )

        return {"success": True, "data": articles_sorted}

    def search_articles_by_keyword(self, keyword: str, status: str = None) -> dict:
        """
        Retrieve articles that contain the given keyword. Optionally filter by article status.

        Args:
            keyword (str): Keyword to search for (case-insensitive exact match in the keywords list).
            status (str, optional): If provided, only include articles with this status.

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo]  # All matching articles
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If status is provided, filter articles by that status.
        """
        if not isinstance(keyword, str) or not keyword.strip():
            return {"success": False, "error": "Invalid keyword input"}

        keyword_lower = keyword.strip().lower()
        result = []
        for article in self.articles.values():
            keywords_list = article.get("keywords", [])
            # Search is case-insensitive
            if any(k.lower() == keyword_lower for k in keywords_list):
                if status is None or article.get("status") == status:
                    result.append(article)
        return {"success": True, "data": result}

    def get_article_by_id(self, article_id: str) -> dict:
        """
        Fetch the full details of an article given its article_id.

        Args:
            article_id (str): The unique identifier for the article.

        Returns:
            dict: 
                On success: { "success": True, "data": ArticleInfo }
                On failure: { "success": False, "error": "Article not found" }
        Constraints:
            - The article must exist in the NewsContentManagementSystem.
        """
        article = self.articles.get(article_id)
        if article is None:
            return { "success": False, "error": "Article not found" }
        return { "success": True, "data": article }

    def list_latest_published_articles(self, section_id: str = None) -> dict:
        """
        Fetch the latest (most recently published) articles across all sections or within a specific section.

        Args:
            section_id (str, optional): If provided, filters articles by this section ID.
                                       If None, searches across all sections.

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo],  # Sorted by publication_date desc, may be empty
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only articles with status 'published' are returned.
            - For section-specific queries, the section_id must exist.
            - Results are sorted by 'publication_date' descending (latest first).
        """
        # Section check if filter applied
        if section_id is not None and section_id not in self.sections:
            return {"success": False, "error": "Section does not exist"}

        # Gather all published articles (optionally filtered by section)
        published_articles = []
        for article in self.articles.values():
            if article["status"] == "published":
                if section_id is None or article["section_id"] == section_id:
                    # Must have publication_date set per the rules
                    if article["publication_date"]:
                        published_articles.append(article)

        # Sort by publication_date descending, assuming ISO or sortable string format
        published_articles.sort(key=lambda a: a["publication_date"], reverse=True)

        return {"success": True, "data": published_articles}

    def get_articles_by_author(self, author_id: str, status: str = None) -> dict:
        """
        List articles written by a specific author, optionally filtered by status.

        Args:
            author_id (str): Author's unique ID.
            status (str, optional): Article status to filter by, e.g. "published" or "draft".
                If None, all articles by the author are returned.

        Returns:
            dict:
                - On success:
                    {
                      "success": True,
                      "data": List[ArticleInfo]  # May be empty if author has no articles
                    }
                - On error:
                    {
                      "success": False,
                      "error": str  # Reason, e.g. author not found
                    }

        Constraints:
            - author_id must exist in the authors.
            - If status is given, only select articles by that status.
        """
        if author_id not in self.authors:
            return { "success": False, "error": "Author not found" }

        matching_articles = [
            article for article in self.articles.values()
            if article['author_id'] == author_id and (status is None or article['status'] == status)
        ]

        return { "success": True, "data": matching_articles }

    def add_article(
        self,
        article_id: str,
        title: str,
        body: str,
        section_id: str,
        author_id: str,
        keywords: list = None
    ) -> dict:
        """
        Create a new article in 'draft' status.

        Args:
            article_id (str): Unique article identifier.
            title (str): Article title.
            body (str): Article body text.
            section_id (str): Section to which the article belongs.
            author_id (str): Author of the article.
            keywords (list, optional): List of keyword strings.

        Returns:
            dict: {
                "success": True,
                "message": "Article created with ID <article_id> in draft status."
            }
            or
            {
                "success": False,
                "error": <error_reason>
            }

        Constraints:
            - article_id must be unique.
            - section_id must exist in the system.
            - author_id must exist in the system.
            - status is always 'draft' upon creation.
            - publication_date is empty for draft.
            - keywords defaults to empty list if not provided.
        """
        if article_id in self.articles:
            return { "success": False, "error": "Article ID already exists." }
        if section_id not in self.sections:
            return { "success": False, "error": "Section not found." }
        if author_id not in self.authors:
            return { "success": False, "error": "Author not found." }
        if keywords is None:
            keywords = []

        article_info = {
            "article_id": article_id,
            "title": title,
            "body": body,
            "section_id": section_id,
            "author_id": author_id,
            "publication_date": "",
            "keywords": keywords,
            "status": "draft"
        }
        self.articles[article_id] = article_info

        return {
            "success": True,
            "message": f"Article created with ID {article_id} in draft status."
        }

    def edit_article(
        self,
        article_id: str,
        title: str = None,
        body: str = None,
        keywords: list = None,
        section_id: str = None,
        author_id: str = None,
        publication_date: str = None,
        status: str = None
    ) -> dict:
        """
        Update attributes (title, body, keywords, section_id, author_id, publication_date, status)
        of an existing article. Any subset of updatable fields can be provided.

        Args:
            article_id (str): ID of the article to update.
            title (str, optional): New title.
            body (str, optional): New body text.
            keywords (list, optional): New list of keywords.
            section_id (str, optional): New section ID (must exist).
            author_id (str, optional): New author ID (must exist).
            publication_date (str, optional): New publication date (string format).
            status (str, optional): New status ('draft', 'published', etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Article updated successfully"
            }
            or {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Article must exist.
            - If updating section_id, the section must exist.
            - If updating author_id, the author must exist.
            - If status is set to "published", publication_date must be set (either previously or via this update).
            - Keywords, if provided, must be a list of str.
            - At least one updatable field must be specified.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article not found" }
    
        updatable_fields = ['title', 'body', 'keywords', 'section_id', 'author_id', 'publication_date', 'status']
        given_fields = {k: v for k, v in [
            ('title', title), ('body', body), ('keywords', keywords), 
            ('section_id', section_id), ('author_id', author_id),
            ('publication_date', publication_date), ('status', status)
        ] if v is not None }

        if not given_fields:
            return { "success": False, "error": "No fields provided to update" }
    
        article = self.articles[article_id]

        # Field-wise constraint checks
        if 'section_id' in given_fields:
            if section_id not in self.sections:
                return { "success": False, "error": "Section does not exist" }
        if 'author_id' in given_fields:
            if author_id not in self.authors:
                return { "success": False, "error": "Author does not exist" }
        if 'keywords' in given_fields:
            if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
                return { "success": False, "error": "Keywords must be a list of strings" }
        if 'status' in given_fields:
            if status == "published":
                # Check: publication_date either already set or provided
                pub_date_new = publication_date if 'publication_date' in given_fields else article.get('publication_date', None)
                if not pub_date_new or pub_date_new.strip() == "":
                    return { "success": False, "error": "Publication date required for published articles" }

        # All constraints passed, update fields
        for field, value in given_fields.items():
            article[field] = value

        # Extra check: If after update, status is 'published', ensure publication_date is set
        new_status = article.get('status', None)
        pub_date = article.get('publication_date', None)
        if new_status == "published" and (not pub_date or pub_date.strip() == ""):
            return { "success": False, "error": "Publication date required for published articles" }

        self.articles[article_id] = article
        return { "success": True, "message": "Article updated successfully" }

    def set_article_status(self, article_id: str, status: str) -> dict:
        """
        Change the publication status of an article.
    
        Args:
            article_id (str): ID of the article to update.
            status (str): New status ('draft' or 'published').

        Returns:
            dict:
                On success: { "success": True, "message": str }
                On failure: { "success": False, "error": str }

        Constraints:
            - Article must exist.
            - Status must be 'draft' or 'published'.
            - If status is set to 'published':
                - publication_date must be set (non-empty).
                - section_id and author_id must be set (non-empty).
        """
        if article_id not in self.articles:
            return {"success": False, "error": f"Article with id '{article_id}' does not exist"}

        valid_statuses = ["draft", "published"]
        if status not in valid_statuses:
            return {"success": False, "error": f"Invalid status '{status}'. Must be one of {valid_statuses}"}

        article = self.articles[article_id]
        # Validate fields if publishing
        if status == "published":
            if not article.get("publication_date"):
                return {"success": False, "error": "Cannot publish: publication_date is not set."}
            if not article.get("section_id"):
                return {"success": False, "error": "Cannot publish: section is not set."}
            if not article.get("author_id"):
                return {"success": False, "error": "Cannot publish: author is not set."}

        article["status"] = status
        self.articles[article_id] = article
        return {
            "success": True,
            "message": f"Status of article '{article_id}' set to '{status}'."
        }

    def set_article_publication_date(self, article_id: str, publication_date: str) -> dict:
        """
        Assign or update the publication_date for an article.

        Args:
            article_id (str): The ID of the article to update.
            publication_date (str): The new publication date to assign (string format).

        Returns:
            dict:
                - On success: { "success": True, "message": "Publication date updated for article <article_id>" }
                - On failure: { "success": False, "error": "Article not found" }

        Constraints:
            - The article must exist.
            - Operation allowed for both draft and published articles.
        """
        article = self.articles.get(article_id)
        if not article:
            return { "success": False, "error": "Article not found" }
        article["publication_date"] = publication_date
        return { "success": True, "message": f"Publication date updated for article {article_id}" }

    def assign_section_to_article(self, article_id: str, section_id: str) -> dict:
        """
        Set or change the section_id for a given article.

        Args:
            article_id (str): The ID of the article to update.
            section_id (str): The ID of the section to assign to the article.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Section assigned to article successfully." }
                On error:
                    { "success": False, "error": "Description of the error" }

        Constraints:
            - article_id must exist in the system.
            - section_id must exist in the system.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article does not exist." }

        if section_id not in self.sections:
            return { "success": False, "error": "Section does not exist." }

        self.articles[article_id]['section_id'] = section_id
        return { "success": True, "message": "Section assigned to article successfully." }

    def assign_author_to_article(self, article_id: str, author_id: str) -> dict:
        """
        Set or update the author of an article.

        Args:
            article_id (str): The ID of the article to update.
            author_id (str): The ID of the author to assign.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Author assigned to article." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Article must exist.
            - Author must exist.
            - Ensures each article is associated with exactly one author.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article does not exist" }
        if author_id not in self.authors:
            return { "success": False, "error": "Author does not exist" }
    
        self.articles[article_id]["author_id"] = author_id
        return { "success": True, "message": "Author assigned to article." }

    def add_section(self, section_id: str, name: str, description: str) -> dict:
        """
        Add a new section (category) to the system.

        Args:
            section_id (str): Unique section identifier.
            name (str): Name of the section.
            description (str): Description of the section.

        Returns:
            dict: {
                "success": True,
                "message": "Section added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - section_id must be unique across all sections.
        """
        if not section_id or not isinstance(section_id, str):
            return {"success": False, "error": "Invalid or missing section_id."}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or missing name."}
        if not description or not isinstance(description, str):
            return {"success": False, "error": "Invalid or missing description."}
        if section_id in self.sections:
            return {"success": False, "error": "Section with this section_id already exists."}
        self.sections[section_id] = {
            "section_id": section_id,
            "name": name,
            "description": description
        }
        return {"success": True, "message": "Section added successfully."}

    def add_author(self, author_id: str, name: str, bio: str) -> dict:
        """
        Add a new author/journalist to the system.

        Args:
            author_id (str): Unique identifier for the author.
            name (str): Name of the author.
            bio (str): Short biography of the author.

        Returns:
            dict: {
                "success": True,
                "message": "Author <author_id> added successfully."
            }
            or
            {
                "success": False,
                "error": <reason for failure>
            }

        Constraints:
            - The author_id must not already exist in the system.
        """
        if not author_id or not name or not bio:
            return {"success": False, "error": "author_id, name, and bio must be provided and non-empty."}
        if author_id in self.authors:
            return {"success": False, "error": f"Author ID '{author_id}' already exists."}
    
        self.authors[author_id] = {
            "author_id": author_id,
            "name": name,
            "bio": bio
        }
        return {"success": True, "message": f"Author '{author_id}' added successfully."}

    def add_keyword_to_article(self, article_id: str, keyword: str) -> dict:
        """
        Add a non-duplicate, non-empty keyword to the specified article's keyword list.

        Args:
            article_id (str): ID of the article to modify.
            keyword (str): Keyword to add.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Keyword added to article."}
                On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - Article must exist.
            - Keyword must be a non-empty string.
            - Keyword must not already be in the article's keywords list.
        """
        # Check article existence
        if article_id not in self.articles:
            return {"success": False, "error": "Article not found."}
    
        # Validate keyword
        if not isinstance(keyword, str) or not keyword.strip():
            return {"success": False, "error": "Keyword must be a non-empty string."}

        keyword = keyword.strip()
        article = self.articles[article_id]
        if keyword in article["keywords"]:
            return {"success": False, "error": "Keyword already present in article."}

        article["keywords"].append(keyword)
        return {"success": True, "message": "Keyword added to article."}

    def remove_keyword_from_article(self, article_id: str, keyword: str) -> dict:
        """
        Remove a keyword from an article's keywords list.

        Args:
            article_id (str): The ID of the article.
            keyword (str): The keyword to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Keyword removed from article."
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - The article must exist.
            - The keyword must exist in the article's keyword list.
        """
        article = self.articles.get(article_id)
        if not article:
            return { "success": False, "error": "Article not found." }

        keywords = article.get("keywords", [])
        if keyword not in keywords:
            return { "success": False, "error": "Keyword not found in article." }

        keywords.remove(keyword)
        article["keywords"] = keywords
        self.articles[article_id] = article

        return { "success": True, "message": "Keyword removed from article." }

    def delete_article(self, article_id: str) -> dict:
        """
        Permanently remove an article from the system by its article ID.

        Args:
            article_id (str): The unique identifier of the article to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Article <article_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Article with ID <article_id> does not exist."
            }

        Constraints:
            - Article must exist to be deleted.
            - Sections and Authors are not affected by article deletion.
        """
        if article_id not in self.articles:
            return {
                "success": False,
                "error": f"Article with ID {article_id} does not exist."
            }
        del self.articles[article_id]
        return {
            "success": True,
            "message": f"Article {article_id} deleted."
        }


class NewsContentManagementSystem(BaseEnv):
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

    def get_section_by_name(self, **kwargs):
        return self._call_inner_tool('get_section_by_name', kwargs)

    def get_section_by_id(self, **kwargs):
        return self._call_inner_tool('get_section_by_id', kwargs)

    def list_all_sections(self, **kwargs):
        return self._call_inner_tool('list_all_sections', kwargs)

    def get_author_by_id(self, **kwargs):
        return self._call_inner_tool('get_author_by_id', kwargs)

    def list_all_authors(self, **kwargs):
        return self._call_inner_tool('list_all_authors', kwargs)

    def list_articles_by_section(self, **kwargs):
        return self._call_inner_tool('list_articles_by_section', kwargs)

    def list_articles_by_status(self, **kwargs):
        return self._call_inner_tool('list_articles_by_status', kwargs)

    def list_published_articles_by_section(self, **kwargs):
        return self._call_inner_tool('list_published_articles_by_section', kwargs)

    def search_articles_by_keyword(self, **kwargs):
        return self._call_inner_tool('search_articles_by_keyword', kwargs)

    def get_article_by_id(self, **kwargs):
        return self._call_inner_tool('get_article_by_id', kwargs)

    def list_latest_published_articles(self, **kwargs):
        return self._call_inner_tool('list_latest_published_articles', kwargs)

    def get_articles_by_author(self, **kwargs):
        return self._call_inner_tool('get_articles_by_author', kwargs)

    def add_article(self, **kwargs):
        return self._call_inner_tool('add_article', kwargs)

    def edit_article(self, **kwargs):
        return self._call_inner_tool('edit_article', kwargs)

    def set_article_status(self, **kwargs):
        return self._call_inner_tool('set_article_status', kwargs)

    def set_article_publication_date(self, **kwargs):
        return self._call_inner_tool('set_article_publication_date', kwargs)

    def assign_section_to_article(self, **kwargs):
        return self._call_inner_tool('assign_section_to_article', kwargs)

    def assign_author_to_article(self, **kwargs):
        return self._call_inner_tool('assign_author_to_article', kwargs)

    def add_section(self, **kwargs):
        return self._call_inner_tool('add_section', kwargs)

    def add_author(self, **kwargs):
        return self._call_inner_tool('add_author', kwargs)

    def add_keyword_to_article(self, **kwargs):
        return self._call_inner_tool('add_keyword_to_article', kwargs)

    def remove_keyword_from_article(self, **kwargs):
        return self._call_inner_tool('remove_keyword_from_article', kwargs)

    def delete_article(self, **kwargs):
        return self._call_inner_tool('delete_article', kwargs)
