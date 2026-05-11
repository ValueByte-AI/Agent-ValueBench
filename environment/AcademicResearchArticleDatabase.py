# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ArticleInfo(TypedDict):
    article_id: str
    title: str
    abstract: str
    publication_date: str
    journal: str
    doi: str
    keywords: List[str]       # List of keyword_id
    author_id: List[str]      # List of author_id

class AuthorInfo(TypedDict):
    author_id: str
    name: str
    affiliation: str

class KeywordInfo(TypedDict):
    keyword_id: str
    keyword_tex: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Academic research article database environment.
        """
        # Articles: {article_id: ArticleInfo}
        self.articles: Dict[str, ArticleInfo] = {}

        # Authors: {author_id: AuthorInfo}
        self.authors: Dict[str, AuthorInfo] = {}

        # Keywords: {keyword_id: KeywordInfo}
        self.keywords: Dict[str, KeywordInfo] = {}

        # Constraints:
        # - Each article must be associated with a valid DOI.
        # - An article can have one or more authors and keywords.
        # - The combination of title, DOI, and author(s) should uniquely identify an article.
        # - All article metadata (title, abstract, keywords, etc.) must be searchable.
        # - The system must accurately maintain total article count for summary queries.

    def search_articles_by_keyword(self, keyword: str) -> dict:
        """
        Retrieve a list of articles associated with a given keyword (by keyword text or keyword_id).

        Args:
            keyword (str): The keyword to search for (may be a keyword_id or the keyword text).

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The keyword must exist, either as a keyword_id or as keyword_tex (case-sensitive).
            - If no articles are found, returns an empty list.
        """
        # Try if keyword is used as keyword_id
        if keyword in self.keywords:
            keyword_id = keyword
        else:
            # Try to find by text
            keyword_id = None
            for k_id, kw_info in self.keywords.items():
                if kw_info['keyword_tex'] == keyword:
                    keyword_id = k_id
                    break
            if keyword_id is None:
                return {"success": False, "error": "Keyword not found"}

        # Find all articles associated with this keyword_id
        result = [
            article_info
            for article_info in self.articles.values()
            if keyword_id in article_info.get('keywords', [])
        ]

        return {"success": True, "data": result}

    def get_article_by_doi(self, doi: str) -> dict:
        """
        Retrieve the complete metadata for an article identified by its DOI.

        Args:
            doi (str): The Digital Object Identifier of the article.

        Returns:
            dict: 
              - On success:
                  {
                      "success": True,
                      "data": ArticleInfo  # metadata for the article with the given DOI
                  }
              - On failure:
                  {
                      "success": False,
                      "error": "No article found for DOI <doi>"
                  }

        Constraints:
            - DOI must exist and map to an article in the database.
        """
        for article in self.articles.values():
            if article["doi"] == doi:
                return {"success": True, "data": article}
        return {"success": False, "error": f"No article found for DOI {doi}"}

    def get_article_by_id(self, article_id: str) -> dict:
        """
        Retrieve the complete metadata for an article given its article_id.

        Args:
            article_id (str): The unique identifier of the article.

        Returns:
            dict: {
                "success": True,
                "data": ArticleInfo  # The metadata for the article
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "Article not found"
            }

        Constraints:
            - The article_id must exist in the articles database.
        """
        article = self.articles.get(article_id)
        if article is None:
            return { "success": False, "error": "Article not found" }
        return { "success": True, "data": article }

    def get_articles_by_author(self, author_id: str = None, name: str = None) -> dict:
        """
        Retrieve all articles authored by a specific author, searched by author_id or by name.
        If both author_id and name are provided, author_id takes precedence.

        Args:
            author_id (str, optional): The unique ID of the author.
            name (str, optional): The (full) name of the author.

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo],  # May be empty if author has no articles
            }
            or
            {
                "success": False,
                "error": str  # Error message if author not found or invalid params
            }

        Constraints:
            - author_id, if provided, must exist in authors.
            - If searching by name and multiple authors match, aggregates articles for all.
            - At least one of author_id or name must be provided.
        """
        if author_id:
            # Lookup by author_id
            if author_id not in self.authors:
                return {"success": False, "error": "Author not found"}
            matching_ids = [author_id]
        elif name:
            # Lookup by name (can result in multiple matches)
            matching_ids = [aid for aid, info in self.authors.items() if info["name"] == name]
            if not matching_ids:
                return {"success": False, "error": "Author not found"}
        else:
            return {"success": False, "error": "Either author_id or name must be provided"}

        # Find all articles listing any of the matching author ids
        articles = [
            article
            for article in self.articles.values()
            if any(aid in article["author_id"] for aid in matching_ids)
        ]

        return {"success": True, "data": articles}

    def search_articles_by_title(self, title_query: str) -> dict:
        """
        Retrieve a list of articles whose titles match or contain the specified string
        (case-insensitive substring search).

        Args:
            title_query (str): Title substring or full string to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo],  # May be empty if no matches.
            }
            or
            {
                "success": False,
                "error": str  # E.g., if query is empty
            }

        Constraints:
            - Search is case-insensitive.
            - Title query must not be empty or all whitespace.
        """
        if not isinstance(title_query, str) or not title_query.strip():
            return { "success": False, "error": "Title query must not be empty" }

        query = title_query.strip().lower()
        result = [
            article_info for article_info in self.articles.values()
            if query in article_info['title'].lower()
        ]
        return { "success": True, "data": result }

    def list_keywords(self) -> dict:
        """
        Retrieve a list of all keywords and their associated ids.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[KeywordInfo]  # List of all keywords as dictionaries with keyword_id and keyword_tex.
            }
            If there are no keywords, returns an empty list in data.
        """
        return {
            "success": True,
            "data": list(self.keywords.values())
        }

    def get_keyword_by_text(self, keyword_tex: str) -> dict:
        """
        Retrieve the keyword_id for a given keyword's text.

        Args:
            keyword_tex (str): The exact text value of the keyword.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": keyword_id (str)
                }
                or
                {
                    "success": False,
                    "error": "Keyword not found"
                }

        Constraints:
            - Exact (case-sensitive) match is required for keyword text.
        """
        for keyword in self.keywords.values():
            if keyword["keyword_tex"] == keyword_tex:
                return { "success": True, "data": keyword["keyword_id"] }
        return { "success": False, "error": "Keyword not found" }

    def get_article_count(self) -> dict:
        """
        Obtain the total number of articles in the database.

        Returns:
            dict: {
                "success": True,
                "data": int  # Total article count
            }

        Constraints:
            - The system must accurately maintain total article count for summary queries.

        Notes:
            - Always succeeds. No input parameters required.
        """
        count = len(self.articles)
        return {"success": True, "data": count}

    def get_author_by_id(self, author_id: str) -> dict:
        """
        Retrieve the details (metadata) of an author given their author_id.

        Args:
            author_id (str): The unique identifier of the author.

        Returns:
            dict: {
                "success": True,
                "data": AuthorInfo  # Author info dictionary
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. author not found
            }

        Constraints:
            - The author_id must exist in the database.
        """
        author = self.authors.get(author_id)
        if author is not None:
            return {"success": True, "data": author}
        else:
            return {"success": False, "error": "Author not found"}

    def get_authors_of_article(self, article_id: str) -> dict:
        """
        List all authors (full details) for a specific article.

        Args:
            article_id (str): The unique ID of the article.

        Returns:
            dict: {
                "success": True,
                "data": List[AuthorInfo],  # All matching authors (empty if no authors)
            }
            or
            {
                "success": False,
                "error": str  # Description (e.g., "Article not found")
            }

        Constraints:
            - Article must exist.
            - Only returns author details for authors found in the authors table.
        """
        article = self.articles.get(article_id)
        if not article:
            return { "success": False, "error": "Article not found" }

        author_infos = [
            self.authors[aid]
            for aid in article.get("author_id", [])
            if aid in self.authors
        ]

        return { "success": True, "data": author_infos }

    def get_keywords_of_article(self, article_id: str) -> dict:
        """
        List all keyword details (KeywordInfo) associated with the specified article.

        Args:
            article_id (str): The unique identifier of the target article.

        Returns:
            dict: {
                "success": True,
                "data": List[KeywordInfo]  # List of keyword details (may be empty if none),
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. article does not exist
            }

        Constraints:
            - Article with article_id must exist.
            - Returns only keywords that actually exist in the keywords dictionary.
        """
        if article_id not in self.articles:
            return {"success": False, "error": "Article does not exist"}

        keyword_ids = self.articles[article_id].get("keywords", [])
        keyword_infos = [
            self.keywords[kw_id]
            for kw_id in keyword_ids
            if kw_id in self.keywords
        ]

        return {"success": True, "data": keyword_infos}

    def add_article(
        self, 
        article_id: str, 
        title: str, 
        abstract: str, 
        publication_date: str, 
        journal: str, 
        doi: str, 
        keywords: List[str], 
        author_id: List[str]
    ) -> dict:
        """
        Add a new article record to the database. 
    
        Args:
            article_id (str): Unique internal identifier for the article.
            title (str): Title of the article.
            abstract (str): Abstract/summary of the article.
            publication_date (str): Publication date (format assumed valid).
            journal (str): Journal or conference name.
            doi (str): Digital Object Identifier (must be non-empty).
            keywords (List[str]): List of keyword_id's.
            author_id (List[str]): List of author_id's.

        Returns:
            dict: Success with message, or failure with explanation.

        Constraints:
            - DOI must be supplied and not empty/None.
            - At least one valid author_id and one valid keyword must be provided.
            - No duplicate allowed (title, doi, and authors combination must be unique).
            - All supplied keywords and authors must already exist.
            - article_id must be unique in the database.
        """
        # Validate DOI
        if not doi or not isinstance(doi, str) or doi.strip() == "":
            return {"success": False, "error": "Valid DOI is required."}
    
        # Validate at least one author and one keyword
        if not author_id or len(author_id) == 0:
            return {"success": False, "error": "At least one author_id must be provided."}
        if not keywords or len(keywords) == 0:
            return {"success": False, "error": "At least one keyword must be provided."}

        # Check article_id uniqueness
        if article_id in self.articles:
            return {"success": False, "error": "article_id already exists."}

        # Check all authors exist
        for aid in author_id:
            if aid not in self.authors:
                return {"success": False, "error": f"Author with author_id '{aid}' does not exist."}
    
        # Check all keywords exist
        for kwid in keywords:
            if kwid not in self.keywords:
                return {"success": False, "error": f"Keyword with keyword_id '{kwid}' does not exist."}

        # Check for uniqueness: (title, doi, author(s)) combination
        for art in self.articles.values():
            if art['title'] == title and art['doi'] == doi and set(art['author_id']) == set(author_id):
                return {"success": False, "error": "An article with the same title, DOI, and authors already exists."}

        new_article = {
            "article_id": article_id,
            "title": title,
            "abstract": abstract,
            "publication_date": publication_date,
            "journal": journal,
            "doi": doi,
            "keywords": list(keywords),
            "author_id": list(author_id)
        }
        self.articles[article_id] = new_article
        return {"success": True, "message": "Article added successfully."}

    def update_article_metadata(
        self,
        article_id: str,
        title: str = None,
        abstract: str = None,
        publication_date: str = None,
        journal: str = None,
        doi: str = None,
        keywords: list = None,      # list of keyword_id
        author_id: list = None      # list of author_id
    ) -> dict:
        """
        Edit the metadata of an existing article.

        Args:
            article_id (str): The ID of the article to update (required).
            title (str, optional): New title.
            abstract (str, optional): New abstract.
            publication_date (str, optional): New publication date.
            journal (str, optional): New journal.
            doi (str, optional): New DOI.
            keywords (list of str, optional): New list of keyword_ids.
            author_id (list of str, optional): New list of author_ids.

        Returns:
            dict: {
                "success": True,
                "message": "Article metadata updated"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Article must exist.
            - If updating DOI, must be non-empty.
            - If updating authors or keywords, all IDs must be valid.
            - After update, (title, doi, author_id) combination must be unique among all articles.
            - Article must have at least one author and one keyword after update.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article not found" }
    
        article = self.articles[article_id].copy()  # Use a copied dict to test updates safely

        # Update only fields provided
        if title is not None:
            article["title"] = title
        if abstract is not None:
            article["abstract"] = abstract
        if publication_date is not None:
            article["publication_date"] = publication_date
        if journal is not None:
            article["journal"] = journal
        if doi is not None:
            if not doi.strip():
                return { "success": False, "error": "DOI must not be empty." }
            article["doi"] = doi
        if keywords is not None:
            if not isinstance(keywords, list) or not keywords:
                return { "success": False, "error": "At least one keyword must be provided." }
            for kw_id in keywords:
                if kw_id not in self.keywords:
                    return { "success": False, "error": f"Keyword ID '{kw_id}' does not exist." }
            article["keywords"] = keywords
        if author_id is not None:
            if not isinstance(author_id, list) or not author_id:
                return { "success": False, "error": "At least one author must be provided." }
            for aid in author_id:
                if aid not in self.authors:
                    return { "success": False, "error": f"Author ID '{aid}' does not exist." }
            article["author_id"] = author_id

        # Ensure at least one author and one keyword
        if not article.get("author_id") or not article.get("keywords"):
            return { "success": False, "error": "Article must have at least one author and one keyword." }
    
        # Enforce uniqueness: (title, doi, author_id) combo must be unique
        updated_tuple = (article["title"], article["doi"], tuple(sorted(article["author_id"])))
        for a_id, a in self.articles.items():
            if a_id == article_id:
                continue
            other_tuple = (a["title"], a["doi"], tuple(sorted(a["author_id"])))
            if updated_tuple == other_tuple:
                return { "success": False, "error": "An article with the same title, DOI, and authors already exists." }

        # Write changes back to main dict
        self.articles[article_id] = article
        return { "success": True, "message": "Article metadata updated" }

    def delete_article(self, article_id: str) -> dict:
        """
        Remove an article record from the database.

        Args:
            article_id (str): The unique ID of the article to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Article deleted successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The article must exist (article_id must be in the articles dictionary).
            - Only the article is removed; authors and keywords are not affected.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article not found." }

        del self.articles[article_id]
        return { "success": True, "message": "Article deleted successfully." }

    def add_author(self, author_id: str, name: str, affiliation: str) -> dict:
        """
        Adds a new author record to the database.

        Args:
            author_id (str): Unique identifier for the author.
            name (str): Full name of the author.
            affiliation (str): Institutional/organizational affiliation.

        Returns:
            dict: {
                "success": True,
                "message": "Author added successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - author_id must not already exist.
            - All input fields must be non-empty strings.
        """
        # Check for uniqueness of author_id
        if not author_id or not isinstance(author_id, str):
            return {"success": False, "error": "Invalid or empty author_id"}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or empty name"}
        if not affiliation or not isinstance(affiliation, str):
            return {"success": False, "error": "Invalid or empty affiliation"}
        if author_id in self.authors:
            return {"success": False, "error": "Author ID already exists"}

        author_info: AuthorInfo = {
            "author_id": author_id,
            "name": name,
            "affiliation": affiliation,
        }
        self.authors[author_id] = author_info
        return {"success": True, "message": "Author added successfully"}

    def update_author(self, author_id: str, name: str = None, affiliation: str = None) -> dict:
        """
        Edit an existing author's information (name and/or affiliation).

        Args:
            author_id (str): Unique identifier of the author to update.
            name (str, optional): New name for the author.
            affiliation (str, optional): New affiliation for the author.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Author information updated." }
                - On failure: { "success": False, "error": "Reason for failure." }

        Constraints:
            - The author with author_id must exist in the database.
            - At least one of 'name' or 'affiliation' should be supplied for update (if none, will no-op successfully).

        Note:
            - Fields left as None will not be updated.
        """
        if author_id not in self.authors:
            return {"success": False, "error": "Author not found."}

        # Update only provided fields
        if name is not None:
            self.authors[author_id]['name'] = name
        if affiliation is not None:
            self.authors[author_id]['affiliation'] = affiliation

        return {"success": True, "message": "Author information updated."}

    def add_keyword(self, keyword_id: str, keyword_tex: str) -> dict:
        """
        Insert a new keyword for indexing articles.

        Args:
            keyword_id (str): Unique identifier for the keyword.
            keyword_tex (str): The textual representation of the keyword.

        Returns:
            dict: 
                { 
                    "success": True, 
                    "message": "Keyword added successfully" 
                }
            or
                { 
                    "success": False, 
                    "error": "reason for failure" 
                }
    
        Constraints:
            - keyword_id must be unique (not already present in self.keywords).
            - keyword_tex should not be empty.
        """
        if not isinstance(keyword_id, str) or not keyword_id.strip():
            return { "success": False, "error": "Keyword ID must be a non-empty string" }
        if not isinstance(keyword_tex, str) or not keyword_tex.strip():
            return { "success": False, "error": "Keyword text must be a non-empty string" }
        if keyword_id in self.keywords:
            return { "success": False, "error": "Keyword ID already exists" }
    
        keyword_info = {
            "keyword_id": keyword_id,
            "keyword_tex": keyword_tex
        }
        self.keywords[keyword_id] = keyword_info
        return { "success": True, "message": "Keyword added successfully" }

    def update_keyword(self, keyword_id: str, new_keyword_tex: str) -> dict:
        """
        Edit an existing keyword's text.

        Args:
            keyword_id (str): The ID of the keyword to be updated.
            new_keyword_tex (str): The new text value for the keyword.

        Returns:
            dict:
                On success: {"success": True, "message": "Keyword text updated successfully."}
                On failure: {"success": False, "error": "Keyword not found."}

        Constraints:
            - The keyword_id must exist in the database.
            - No restriction on uniqueness or non-emptiness of new_keyword_tex.
        """
        if keyword_id not in self.keywords:
            return {"success": False, "error": "Keyword not found."}
    
        self.keywords[keyword_id]["keyword_tex"] = new_keyword_tex
        return {"success": True, "message": "Keyword text updated successfully."}


class AcademicResearchArticleDatabase(BaseEnv):
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

    def search_articles_by_keyword(self, **kwargs):
        return self._call_inner_tool('search_articles_by_keyword', kwargs)

    def get_article_by_doi(self, **kwargs):
        return self._call_inner_tool('get_article_by_doi', kwargs)

    def get_article_by_id(self, **kwargs):
        return self._call_inner_tool('get_article_by_id', kwargs)

    def get_articles_by_author(self, **kwargs):
        return self._call_inner_tool('get_articles_by_author', kwargs)

    def search_articles_by_title(self, **kwargs):
        return self._call_inner_tool('search_articles_by_title', kwargs)

    def list_keywords(self, **kwargs):
        return self._call_inner_tool('list_keywords', kwargs)

    def get_keyword_by_text(self, **kwargs):
        return self._call_inner_tool('get_keyword_by_text', kwargs)

    def get_article_count(self, **kwargs):
        return self._call_inner_tool('get_article_count', kwargs)

    def get_author_by_id(self, **kwargs):
        return self._call_inner_tool('get_author_by_id', kwargs)

    def get_authors_of_article(self, **kwargs):
        return self._call_inner_tool('get_authors_of_article', kwargs)

    def get_keywords_of_article(self, **kwargs):
        return self._call_inner_tool('get_keywords_of_article', kwargs)

    def add_article(self, **kwargs):
        return self._call_inner_tool('add_article', kwargs)

    def update_article_metadata(self, **kwargs):
        return self._call_inner_tool('update_article_metadata', kwargs)

    def delete_article(self, **kwargs):
        return self._call_inner_tool('delete_article', kwargs)

    def add_author(self, **kwargs):
        return self._call_inner_tool('add_author', kwargs)

    def update_author(self, **kwargs):
        return self._call_inner_tool('update_author', kwargs)

    def add_keyword(self, **kwargs):
        return self._call_inner_tool('add_keyword', kwargs)

    def update_keyword(self, **kwargs):
        return self._call_inner_tool('update_keyword', kwargs)

