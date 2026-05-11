# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class MovieInfo(TypedDict):
    movie_id: str
    title: str
    release_year: int
    production_data: str

class AwardInfo(TypedDict):
    award_id: str
    name: str
    organization: str

class AwardNominationInfo(TypedDict):
    nomination_id: str
    movie_id: str
    award_id: str
    category: str
    year: int
    outcome: str  # Should be 'won', 'nominated', or 'lost'

class ActorInfo(TypedDict):
    actor_id: str
    name: str
    birthday: str

class MovieCastInfo(TypedDict):
    movie_id: str
    actor_id: str
    role_name: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Movies: {movie_id: MovieInfo}
        self.movies: Dict[str, MovieInfo] = {}
        # Awards: {award_id: AwardInfo}
        self.awards: Dict[str, AwardInfo] = {}
        # Award Nominations: {nomination_id: AwardNominationInfo}
        self.award_nominations: Dict[str, AwardNominationInfo] = {}
        # Actors: {actor_id: ActorInfo}
        self.actors: Dict[str, ActorInfo] = {}
        # Movie cast: {movie_id: List[MovieCastInfo]}
        self.movie_casts: Dict[str, List[MovieCastInfo]] = {}

        # Constraints:
        # - Each AwardNomination must reference existing movie_id and award_id
        # - AwardNomination outcome values are constrained to valid statuses (e.g., 'won', 'nominated', 'lost')
        # - movie_id must be unique for each movie
        # - Award categories must be consistent with their parent Award organization

    def get_movie_by_id(self, movie_id: str) -> dict:
        """
        Retrieve movie metadata for the given movie_id.

        Args:
            movie_id (str): Unique movie identifier.

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "data": MovieInfo
                    }
                Failure (movie_id not found):
                    {
                        "success": False,
                        "error": "Movie not found"
                    }

        Constraints:
            - movie_id must be present in the database.
            - movie_id is unique for each movie.
        """
        if movie_id in self.movies:
            return {"success": True, "data": self.movies[movie_id]}
        else:
            return {"success": False, "error": "Movie not found"}

    def list_movies(self) -> dict:
        """
        Get a list of all movies in the database.

        Returns:
            dict: {
                "success": True,
                "data": List[MovieInfo]    # List containing all movies, may be empty.
            }

        There are no input parameters or specific constraints for this operation.
        """
        movies_list = list(self.movies.values())
        return {
            "success": True,
            "data": movies_list
        }

    def get_award_by_id(self, award_id: str) -> dict:
        """
        Retrieve an award's details given the unique award_id.

        Args:
            award_id (str): Unique identifier of the award.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": AwardInfo  # Award's details
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Award not found"
                    }

        Constraints:
            - award_id must exist in the system.
        """
        if award_id in self.awards:
            return { "success": True, "data": self.awards[award_id] }
        else:
            return { "success": False, "error": "Award not found" }

    def list_awards(self) -> dict:
        """
        Return all awards registered in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[AwardInfo],  # List of all award records; may be empty if none exist
            }

        Constraints:
            - None (listing; no argument and no structural error state)
        """
        awards_list = list(self.awards.values())
        return { "success": True, "data": awards_list }

    def get_nominations_by_movie_id(self, movie_id: str) -> dict:
        """
        List all award nominations associated with a given movie_id.

        Args:
            movie_id (str): The unique ID of the movie whose nominations are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[AwardNominationInfo],
            }
            or
            {
                "success": False,
                "error": str,  # reason for failure (e.g., movie does not exist)
            }

        Constraints:
            - movie_id must exist in the system.
            - All award nominations returned are associated with this movie_id.
        """
        if movie_id not in self.movies:
            return { "success": False, "error": "Movie with the given movie_id does not exist." }

        result = [
            nomination
            for nomination in self.award_nominations.values()
            if nomination["movie_id"] == movie_id
        ]
        return { "success": True, "data": result }

    def get_nominations_by_award_id(self, award_id: str) -> dict:
        """
        List all award nominations for a specific award_id.

        Args:
            award_id (str): The ID of the award whose nominations should be listed.

        Returns:
            dict:
                On success:
                    {"success": True, "data": List[AwardNominationInfo]}  # May be empty.
                On failure:
                    {"success": False, "error": str}  # Award does not exist.

        Constraints:
            - award_id must exist in the awards dictionary.
            - If no nominations are found for this award_id, returns an empty list.
        """
        if award_id not in self.awards:
            return {"success": False, "error": f"Award with id '{award_id}' does not exist."}

        nominations = [
            nomination_info
            for nomination_info in self.award_nominations.values()
            if nomination_info["award_id"] == award_id
        ]

        return {"success": True, "data": nominations}

    def get_nomination_by_id(self, nomination_id: str) -> dict:
        """
        Retrieve detailed information for a specific AwardNomination by its unique nomination_id.

        Args:
            nomination_id (str): The unique identifier for the award nomination.

        Returns:
            dict:
              - On success: {"success": True, "data": AwardNominationInfo}
              - On failure: {"success": False, "error": "Nomination not found."}
        """
        nomination = self.award_nominations.get(nomination_id)
        if nomination is None:
            return {"success": False, "error": "Nomination not found."}
        return {"success": True, "data": nomination}

    def get_actor_by_id(self, actor_id: str) -> dict:
        """
        Retrieve actor record by `actor_id`.

        Args:
            actor_id (str): The unique identifier for the actor.

        Returns:
            dict: 
                - On success: {"success": True, "data": ActorInfo }
                - On error: {"success": False, "error": "Actor not found"}

        Constraints:
            - actor_id must exist in the database.
        """
        actor = self.actors.get(actor_id)
        if actor is None:
            return { "success": False, "error": "Actor not found" }
        return { "success": True, "data": actor }

    def list_actors(self) -> dict:
        """
        Get the complete list of actors in the movie database.

        Returns:
            dict: {
                "success": True,
                "data": List[ActorInfo]  # All actors (may be empty if none exist)
            }
        """
        return {
            "success": True,
            "data": list(self.actors.values())
        }

    def get_cast_by_movie_id(self, movie_id: str) -> dict:
        """
        Retrieve the cast list (actors and roles) for a specific movie.

        Args:
            movie_id (str): The unique identifier for the movie.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": [
                        {
                            "actor_id": str,
                            "name": str,
                            "birthday": str,
                            "role_name": str
                        },
                        ...
                    ]
                }
                On failure (movie not found):
                {
                    "success": False,
                    "error": "Movie not found"
                }

        Constraints:
            - movie_id must refer to an existing Movie.
            - Only actors present in the Actor registry are listed.
            - Returns an empty list if the movie has no cast.

        """
        # Check movie existence
        if movie_id not in self.movies:
            return { "success": False, "error": "Movie not found" }

        cast_list = self.movie_casts.get(movie_id, [])
        result = []
        for cast in cast_list:
            actor_id = cast["actor_id"]
            role_name = cast["role_name"]
            actor_info = self.actors.get(actor_id)
            if not actor_info:
                continue  # skip if actor not found
            result.append({
                "actor_id": actor_id,
                "name": actor_info["name"],
                "birthday": actor_info["birthday"],
                "role_name": role_name
            })

        return { "success": True, "data": result }

    def get_movies_by_actor_id(self, actor_id: str) -> dict:
        """
        List all movies in which a given actor appears.

        Args:
            actor_id (str): The unique identifier of the actor.

        Returns:
            dict: {
                "success": True,
                "data": List[MovieInfo]  # All MovieInfo entries where this actor appears.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., actor not found)
            }

        Constraints:
            - actor_id must exist in self.actors.
        """
        if actor_id not in self.actors:
            return { "success": False, "error": "Actor not found" }

        result_movie_ids = set()
        for movie_id, cast_list in self.movie_casts.items():
            if any(cast["actor_id"] == actor_id for cast in cast_list):
                if movie_id in self.movies:
                    result_movie_ids.add(movie_id)
        movies = [self.movies[movie_id] for movie_id in sorted(result_movie_ids)]

        return { "success": True, "data": movies }

    def summarize_awards_for_movie(self, movie_id: str) -> dict:
        """
        Aggregate and format all awards/nominations for a movie as a summary.
        Groups nominations by outcome, award organization, category, and year.

        Args:
            movie_id (str): Unique identifier of the movie.

        Returns:
            dict: {
                "success": True,
                "data": dict  # Summary structure: grouped by organization, with categories, outcomes etc.
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The movie_id must exist in the database.
            - If the movie has no nominations, data will be an empty dict.
        """
        if movie_id not in self.movies:
            return {"success": False, "error": "Movie does not exist"}

        # Gather nominations for this movie
        nominations = [
            n for n in self.award_nominations.values()
            if n["movie_id"] == movie_id
        ]

        # Summary structure:
        # {
        #   organization: {
        #     award_name: [
        #        {
        #           'category': str,
        #           'year': int,
        #           'outcome': str
        #        },
        #        ...
        #     ],
        #     ...
        #   },
        #   ...
        # }
        summary = {}
        for nom in nominations:
            award_id = nom["award_id"]
            award_info = self.awards.get(award_id)
            if not award_info:
                continue  # Defensive: Should not happen if constraints are enforced

            org = award_info["organization"]
            award_name = award_info["name"]
            category = nom["category"]
            year = nom["year"]
            outcome = nom["outcome"]

            # Drill down to organization > award_name
            if org not in summary:
                summary[org] = {}
            if award_name not in summary[org]:
                summary[org][award_name] = []
            summary[org][award_name].append({
                "category": category,
                "year": year,
                "outcome": outcome
            })

        return {"success": True, "data": summary}

    def add_movie(self, movie_id: str, title: str, release_year: int, production_data: str) -> dict:
        """
        Add a new movie record to the database.

        Args:
            movie_id (str): Unique identifier for the movie.
            title (str): Title of the movie.
            release_year (int): Year the movie was released.
            production_data (str): Production details of the movie.

        Returns:
            dict: 
                On success: 
                    { "success": True, "message": "Movie added successfully." }
                On failure (duplicate movie_id): 
                    { "success": False, "error": "Movie ID already exists." }

        Constraints:
            - movie_id must be unique for each movie.
        """
        if movie_id in self.movies:
            return { "success": False, "error": "Movie ID already exists." }

        self.movies[movie_id] = {
            "movie_id": movie_id,
            "title": title,
            "release_year": release_year,
            "production_data": production_data
        }
        return { "success": True, "message": "Movie added successfully." }

    def update_movie(
        self,
        movie_id: str,
        title: str = None,
        release_year: int = None,
        production_data: str = None
    ) -> dict:
        """
        Modify metadata of an existing movie.

        Args:
            movie_id (str): Unique identifier of the movie to update.
            title (str, optional): New title for the movie.
            release_year (int, optional): New release year.
            production_data (str, optional): New production data.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Movie updated successfully."}
                On failure:
                    {"success": False, "error": <reason>}
        Constraints:
            - movie_id must already exist.
            - Only title, release_year, production_data are updatable.
            - Type checks for updatable fields must pass if those fields are provided (not None).
        """
        movie = self.movies.get(movie_id)
        if not movie:
            return {"success": False, "error": "Movie ID does not exist."}

        updated = False

        if title is not None:
            if not isinstance(title, str):
                return {"success": False, "error": "Title must be a string."}
            movie["title"] = title
            updated = True

        if release_year is not None:
            if not isinstance(release_year, int):
                return {"success": False, "error": "Release year must be an integer."}
            movie["release_year"] = release_year
            updated = True

        if production_data is not None:
            if not isinstance(production_data, str):
                return {"success": False, "error": "Production data must be a string."}
            movie["production_data"] = production_data
            updated = True

        # Even if nothing was updated, this operation is a success (noop)
        return {"success": True, "message": "Movie updated successfully."}

    def delete_movie(self, movie_id: str) -> dict:
        """
        Remove a movie record (by `movie_id`) as well as all related award nominations and cast records.

        Args:
            movie_id (str): The ID of the movie to delete.

        Returns:
            dict:
                - {"success": True, "message": str} on success.
                - {"success": False, "error": str} if the movie does not exist.

        Constraints:
            - The movie must exist in the database.
            - All award nominations referencing the movie must be deleted.
            - All cast records for the movie must be deleted.
        """
        if movie_id not in self.movies:
            return {"success": False, "error": "Movie does not exist"}

        # Delete the MovieInfo entry
        del self.movies[movie_id]

        # Delete all related AwardNominationInfo entries
        to_delete_nominations = [nom_id for nom_id, nom_info in self.award_nominations.items()
                                 if nom_info["movie_id"] == movie_id]
        for nom_id in to_delete_nominations:
            del self.award_nominations[nom_id]

        # Delete all related MovieCastInfo entries
        if movie_id in self.movie_casts:
            del self.movie_casts[movie_id]

        return {
            "success": True,
            "message": f"Movie '{movie_id}' and all related nominations and cast records have been deleted"
        }

    def add_award(self, award_id: str, name: str, organization: str) -> dict:
        """
        Add a new award to the award registry.

        Args:
            award_id (str): Unique identifier for the award.
            name (str): The name of the award (e.g., "Best Picture").
            organization (str): The organization granting the award (e.g., "Academy Awards").

        Returns:
            dict: {
                "success": True,
                "message": "Award added successfully"
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - award_id must be unique (must not already exist in self.awards).
            - award_id, name, organization must be non-empty strings.
        """
        if not award_id or not name or not organization:
            return { "success": False, "error": "award_id, name, and organization must be non-empty strings" }
        if award_id in self.awards:
            return { "success": False, "error": "Award with this award_id already exists" }
        new_award: AwardInfo = {
            "award_id": award_id,
            "name": name,
            "organization": organization
        }
        self.awards[award_id] = new_award
        return { "success": True, "message": "Award added successfully" }

    def update_award(self, award_id: str, name: str = None, organization: str = None) -> dict:
        """
        Modify details of an existing award. Only 'name' and/or 'organization' fields can be updated.

        Args:
            award_id (str): The unique ID of the award to update.
            name (str, optional): The new name of the award. Leave as None to not update.
            organization (str, optional): The new organization for the award. Leave as None to not update.

        Returns:
            dict:
              - On success: { "success": True, "message": "Award updated successfully." }
              - On failure: { "success": False, "error": <reason> }

        Constraints:
            - award_id must exist in the system.
            - At least one of 'name' or 'organization' must be provided to update.
        """
        if award_id not in self.awards:
            return { "success": False, "error": "Award not found." }
        if name is None and organization is None:
            return { "success": False, "error": "No update fields specified." }

        award = self.awards[award_id]
        if name is not None:
            award["name"] = name
        if organization is not None:
            award["organization"] = organization
        self.awards[award_id] = award

        return { "success": True, "message": "Award updated successfully." }

    def add_award_nomination(
        self,
        nomination_id: str,
        movie_id: str,
        award_id: str,
        category: str,
        year: int,
        outcome: str
    ) -> dict:
        """
        Add a new AwardNomination entry, ensuring movie_id and award_id exist,
        outcome is valid, and nomination_id is unique.

        Args:
            nomination_id (str): Unique ID for the nomination
            movie_id (str): Refers to an existing Movie
            award_id (str): Refers to an existing Award
            category (str): Award category (no strict validation here)
            year (int): Year of the nomination
            outcome (str): 'won', 'nominated', or 'lost'

        Returns:
            dict: Success or failure with details/message.
            {
              "success": True, "message": "Award nomination added."
            }
            or
            {
              "success": False, "error": <reason>
            }

        Constraints:
            - nomination_id must be unique
            - movie_id/award_id must exist
            - outcome in {"won", "nominated", "lost"}
        """
        if nomination_id in self.award_nominations:
            return {"success": False, "error": "Nomination ID already exists."}
        if movie_id not in self.movies:
            return {"success": False, "error": "movie_id does not exist."}
        if award_id not in self.awards:
            return {"success": False, "error": "award_id does not exist."}
        if outcome not in {"won", "nominated", "lost"}:
            return {"success": False, "error": "Invalid outcome value. Must be 'won', 'nominated', or 'lost'."}

        nomination: AwardNominationInfo = {
            "nomination_id": nomination_id,
            "movie_id": movie_id,
            "award_id": award_id,
            "category": category,
            "year": year,
            "outcome": outcome
        }
        self.award_nominations[nomination_id] = nomination
        return {"success": True, "message": "Award nomination added."}

    def update_award_nomination(
        self, 
        nomination_id: str,
        outcome: str = None,
        year: int = None,
        category: str = None
    ) -> dict:
        """
        Change the outcome, year, or category of an AwardNomination (subject to constraints).

        Args:
            nomination_id (str): The unique identifier for the AwardNomination to update.
            outcome (str, optional): New outcome status; must be one of 'won', 'nominated', or 'lost' if specified.
            year (int, optional): New nomination year (must be integer).
            category (str, optional): New nomination category.

        Returns:
            dict: {
                "success": True,
                "message": "Award nomination updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Description of the failure.
            }

        Constraints:
          - nomination_id must exist
          - If provided, outcome must be one of {'won', 'nominated', 'lost'}
          - If provided, year must be an integer
          - If provided, category ideally should only be one permitted by the award's organization
        """
        # Check nomination exists
        if nomination_id not in self.award_nominations:
            return { "success": False, "error": "AwardNomination does not exist" }

        valid_outcomes = {'won', 'nominated', 'lost'}
        updated = False

        nomination = self.award_nominations[nomination_id]

        # Update outcome if given and valid
        if outcome is not None:
            if outcome not in valid_outcomes:
                return { "success": False, "error": "Invalid outcome, must be 'won', 'nominated', or 'lost'" }
            if nomination["outcome"] != outcome:
                nomination["outcome"] = outcome
                updated = True

        # Update year if given
        if year is not None:
            if not isinstance(year, int):
                return { "success": False, "error": "Year must be an integer" }
            if nomination["year"] != year:
                nomination["year"] = year
                updated = True

        # Update category if given
        if category is not None:
            # Category consistency with organization is not verifiable without a mapping, so only change if different.
            if nomination["category"] != category:
                nomination["category"] = category
                updated = True

        if updated:
            self.award_nominations[nomination_id] = nomination
            return { "success": True, "message": "Award nomination updated successfully" }
        else:
            return { "success": True, "message": "No changes made to award nomination" }

    def delete_award_nomination(self, nomination_id: str) -> dict:
        """
        Remove an AwardNomination from the database, given its nomination_id.

        Args:
            nomination_id (str): The unique ID of the nomination to be deleted.

        Returns:
            dict: 
                If successful:
                    {"success": True, "message": "Award nomination <nomination_id> has been deleted."}
                If not found:
                    {"success": False, "error": "Nomination ID does not exist."}

        Constraints:
            - Nomination ID must exist in self.award_nominations.
        """
        if nomination_id not in self.award_nominations:
            return {"success": False, "error": "Nomination ID does not exist."}
    
        del self.award_nominations[nomination_id]
        return {"success": True, "message": f"Award nomination {nomination_id} has been deleted."}

    def add_actor(self, actor_id: str, name: str, birthday: str) -> dict:
        """
        Add a new actor to the actor registry.

        Args:
            actor_id (str): Unique identifier for the actor.
            name (str): The actor's full name.
            birthday (str): The actor's birthday (expected format: 'YYYY-MM-DD').

        Returns:
            dict: {
                "success": True,
                "message": "Actor <actor_id> added."
            }
            or
            {
                "success": False,
                "error": "Actor with id <actor_id> already exists."
            }

        Constraints:
            - actor_id must be unique in the system.
        """
        if actor_id in self.actors:
            return {
                "success": False,
                "error": f"Actor with id {actor_id} already exists."
            }
        actor_info: ActorInfo = {
            "actor_id": actor_id,
            "name": name,
            "birthday": birthday
        }
        self.actors[actor_id] = actor_info
        return {
            "success": True,
            "message": f"Actor {actor_id} added."
        }

    def update_actor(self, actor_id: str, name: str = None, birthday: str = None) -> dict:
        """
        Edit an existing actor's info.

        Args:
            actor_id (str): The unique identifier of the actor to update.
            name (str, optional): Updated name for the actor.
            birthday (str, optional): Updated birthday for the actor.

        Returns:
            dict: {
                "success": True,
                "message": "Actor <actor_id> updated successfully"
            } or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - actor_id must exist in the system.
            - At least one updatable field (name or birthday) must be provided.
        """
        # Check actor exists
        if actor_id not in self.actors:
            return {"success": False, "error": "Actor does not exist"}

        if name is None and birthday is None:
            return {"success": False, "error": "No update fields provided"}

        if name is not None:
            self.actors[actor_id]["name"] = name
        if birthday is not None:
            self.actors[actor_id]["birthday"] = birthday

        return {"success": True, "message": f"Actor {actor_id} updated successfully"}

    def add_movie_cast(self, movie_id: str, actor_id: str, role_name: str) -> dict:
        """
        Add a new association between a movie and an actor (i.e., add cast member with specified role).
    
        Args:
            movie_id (str): Unique identifier of the movie.
            actor_id (str): Unique identifier of the actor.
            role_name (str): Name of the role played by the actor in the movie.

        Returns:
            dict: {
                "success": True,
                "message": "Actor <actor_id> added as '<role_name>' to movie <movie_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The movie_id must correspond to an existing movie.
            - The actor_id must correspond to an existing actor.
            - The same (movie_id, actor_id, role_name) combination should not already exist in the movie's cast.
        """
        if movie_id not in self.movies:
            return {"success": False, "error": "Movie does not exist."}
        if actor_id not in self.actors:
            return {"success": False, "error": "Actor does not exist."}
    
        cast_list = self.movie_casts.setdefault(movie_id, [])
        for cast in cast_list:
            if cast["actor_id"] == actor_id and cast["role_name"] == role_name:
                return {"success": False, "error": "This actor with the same role is already associated with the movie."}

        replaced = False
        updated_cast_list = []
        for cast in cast_list:
            if cast["actor_id"] == actor_id:
                replaced = True
                continue
            updated_cast_list.append(cast)

        new_cast = {
            "movie_id": movie_id,
            "actor_id": actor_id,
            "role_name": role_name
        }
        updated_cast_list.append(new_cast)
        self.movie_casts[movie_id] = updated_cast_list

        if replaced:
            return {
                "success": True,
                "message": f"Actor {actor_id} role updated to '{role_name}' in movie {movie_id}."
            }

        return {
            "success": True,
            "message": f"Actor {actor_id} added as '{role_name}' to movie {movie_id}."
        }

    def remove_movie_cast(self, movie_id: str, actor_id: str) -> dict:
        """
        Remove an actor from a movie's cast list.

        Args:
            movie_id (str): Unique identifier for the movie.
            actor_id (str): Unique identifier for the actor to be removed.

        Returns:
            dict: 
                If removal is successful:
                    {
                        "success": True,
                        "message": "Actor removed from movie cast."
                    }
                If a problem occurs:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
        - The movie_id must exist.
        - The actor_id must appear in the cast list for the given movie.
        - If actor_id does not exist in the cast, an error is returned.
        """

        if movie_id not in self.movies:
            return { "success": False, "error": "Movie does not exist." }
        if movie_id not in self.movie_casts or not self.movie_casts[movie_id]:
            return { "success": False, "error": "No cast assigned to this movie." }

        original_cast = self.movie_casts[movie_id]
        updated_cast = [entry for entry in original_cast if entry["actor_id"] != actor_id]

        if len(updated_cast) == len(original_cast):
            return { "success": False, "error": "Actor not found in cast for the movie." }

        # Update the cast list
        if updated_cast:
            self.movie_casts[movie_id] = updated_cast
        else:
            # No more cast, remove the entry
            del self.movie_casts[movie_id]

        return { "success": True, "message": "Actor removed from movie cast." }


class MovieDatabaseManagementSystem(BaseEnv):
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

    def get_movie_by_id(self, **kwargs):
        return self._call_inner_tool('get_movie_by_id', kwargs)

    def list_movies(self, **kwargs):
        return self._call_inner_tool('list_movies', kwargs)

    def get_award_by_id(self, **kwargs):
        return self._call_inner_tool('get_award_by_id', kwargs)

    def list_awards(self, **kwargs):
        return self._call_inner_tool('list_awards', kwargs)

    def get_nominations_by_movie_id(self, **kwargs):
        return self._call_inner_tool('get_nominations_by_movie_id', kwargs)

    def get_nominations_by_award_id(self, **kwargs):
        return self._call_inner_tool('get_nominations_by_award_id', kwargs)

    def get_nomination_by_id(self, **kwargs):
        return self._call_inner_tool('get_nomination_by_id', kwargs)

    def get_actor_by_id(self, **kwargs):
        return self._call_inner_tool('get_actor_by_id', kwargs)

    def list_actors(self, **kwargs):
        return self._call_inner_tool('list_actors', kwargs)

    def get_cast_by_movie_id(self, **kwargs):
        return self._call_inner_tool('get_cast_by_movie_id', kwargs)

    def get_movies_by_actor_id(self, **kwargs):
        return self._call_inner_tool('get_movies_by_actor_id', kwargs)

    def summarize_awards_for_movie(self, **kwargs):
        return self._call_inner_tool('summarize_awards_for_movie', kwargs)

    def add_movie(self, **kwargs):
        return self._call_inner_tool('add_movie', kwargs)

    def update_movie(self, **kwargs):
        return self._call_inner_tool('update_movie', kwargs)

    def delete_movie(self, **kwargs):
        return self._call_inner_tool('delete_movie', kwargs)

    def add_award(self, **kwargs):
        return self._call_inner_tool('add_award', kwargs)

    def update_award(self, **kwargs):
        return self._call_inner_tool('update_award', kwargs)

    def add_award_nomination(self, **kwargs):
        return self._call_inner_tool('add_award_nomination', kwargs)

    def update_award_nomination(self, **kwargs):
        return self._call_inner_tool('update_award_nomination', kwargs)

    def delete_award_nomination(self, **kwargs):
        return self._call_inner_tool('delete_award_nomination', kwargs)

    def add_actor(self, **kwargs):
        return self._call_inner_tool('add_actor', kwargs)

    def update_actor(self, **kwargs):
        return self._call_inner_tool('update_actor', kwargs)

    def add_movie_cast(self, **kwargs):
        return self._call_inner_tool('add_movie_cast', kwargs)

    def remove_movie_cast(self, **kwargs):
        return self._call_inner_tool('remove_movie_cast', kwargs)
