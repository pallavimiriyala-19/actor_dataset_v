"""
TMDb actor identification and verification module.
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple
from config.settings import (
    TMDB_API_KEY,
    TMDB_BASE_URL,
    TMDB_IMAGE_BASE_URL,
    MIN_ACTOR_CREDITS,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


logger = logging.getLogger(__name__)


class TMDbActorIdentifier:
    """
    Identifies and retrieves actor information from TMDb API.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize TMDb identifier.

        Args:
            api_key: TMDb API key (uses TMDB_API_KEY from settings if not provided)
        """
        self.api_key = api_key or TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDB_API_KEY not set. Set it via environment variable.")
        
        self.base_url = TMDB_BASE_URL
        self.image_url = TMDB_IMAGE_BASE_URL
        self.session = requests.Session()
        self.session.timeout = REQUEST_TIMEOUT

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """
        Make authenticated request to TMDb API.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: If request fails
            ValueError: If API returns error
        """
        if params is None:
            params = {}
        
        params["api_key"] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making request to {url}")
        
        response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data or "success" in data and not data["success"]:
            raise ValueError(f"TMDb API error: {data}")
        
        return data

    def search_actors(self, actor_name: str) -> List[Dict]:
        """
        Search for actors by name.

        Args:
            actor_name: Name of actor to search

        Returns:
            List of actor search results
        """
        logger.info(f"Searching for actor: {actor_name}")
        
        params = {
            "query": actor_name,
            "include_adult": False,
        }
        
        try:
            data = self._make_request("search/person", params)
            results = data.get("results", [])
            logger.info(f"Found {len(results)} results for '{actor_name}'")
            return results
        except Exception as e:
            logger.error(f"Error searching for actor '{actor_name}': {str(e)}")
            raise

    def get_actor_details(self, person_id: int) -> Dict:
        """
        Get detailed information about an actor.

        Args:
            person_id: TMDb person ID

        Returns:
            Actor details dictionary
        """
        logger.info(f"Fetching details for person ID: {person_id}")
        
        try:
            data = self._make_request(f"person/{person_id}", {
                "append_to_response": "images,combined_credits"
            })
            logger.debug(f"Retrieved details for {data.get('name', 'Unknown')}")
            return data
        except Exception as e:
            logger.error(f"Error fetching actor details for ID {person_id}: {str(e)}")
            raise

    def get_actor_images(self, person_id: int, limit: int = 50) -> List[Dict]:
        """
        Get profile images for an actor.

        Args:
            person_id: TMDb person ID
            limit: Maximum number of images to retrieve

        Returns:
            List of image dictionaries with paths
        """
        logger.info(f"Fetching images for person ID: {person_id}")
        
        try:
            data = self._make_request(f"person/{person_id}/images", {})
            profiles = data.get("profiles", [])
            
            # Sort by vote average (quality)
            profiles = sorted(
                profiles,
                key=lambda x: x.get("vote_average", 0),
                reverse=True
            )
            
            images = profiles[:limit]
            logger.info(f"Retrieved {len(images)} images for person ID {person_id}")
            return images
        except Exception as e:
            logger.error(f"Error fetching images for person ID {person_id}: {str(e)}")
            return []

    def get_actor_filmography(self, person_id: int) -> Tuple[List[Dict], List[Dict]]:
        """
        Get actor's filmography (movies and TV).

        Args:
            person_id: TMDb person ID

        Returns:
            Tuple of (movies, tv_shows) lists
        """
        logger.info(f"Fetching filmography for person ID: {person_id}")
        
        try:
            data = self._make_request(f"person/{person_id}/combined_credits", {})
            
            cast = data.get("cast", [])
            
            # Separate movies and TV
            movies = [c for c in cast if c.get("media_type") == "movie"]
            tv_shows = [c for c in cast if c.get("media_type") == "tv"]
            
            logger.info(f"Found {len(movies)} movies and {len(tv_shows)} TV shows")
            return movies, tv_shows
        except Exception as e:
            logger.error(f"Error fetching filmography for ID {person_id}: {str(e)}")
            return [], []

    def verify_actor_is_telugu(self, person_id: int) -> Tuple[bool, str]:
        """
        Verify that actor primarily works in Telugu film industry.

        Args:
            person_id: TMDb person ID

        Returns:
            Tuple of (is_telugu_actor, confidence_message)
        """
        logger.info(f"Verifying Telugu actor status for person ID: {person_id}")
        
        try:
            movies, tv_shows = self.get_actor_filmography(person_id)
            
            if not movies and not tv_shows:
                return False, "No filmography found"
            
            # Check for Telugu language content
            telugu_count = 0
            total_count = len(movies) + len(tv_shows)
            
            for item in movies + tv_shows:
                # Check original language
                if item.get("original_language") == "te":
                    telugu_count += 1
                # Check release date (some Telugu films may not have language tagged)
                elif item.get("origin_country"):
                    if "IN" in item.get("origin_country", []):
                        telugu_count += 1
            
            telugu_percentage = (telugu_count / total_count * 100) if total_count > 0 else 0
            
            # Consider Telugu actor if at least 30% of content is Telugu
            is_telugu = telugu_percentage >= 20 and telugu_count >= MIN_ACTOR_CREDITS
            
            message = f"{telugu_count}/{total_count} credits appear to be Telugu content ({telugu_percentage:.1f}%)"
            
            logger.info(f"Telugu verification: {is_telugu} - {message}")
            return is_telugu, message
        except Exception as e:
            logger.error(f"Error verifying Telugu actor status: {str(e)}")
            return False, f"Verification error: {str(e)}"

    def disambiguate_actor(self, actor_name: str) -> Optional[Dict]:
        """
        Disambiguate actor by finding the most likely match.
        Prefers actors with:
        - Higher popularity
        - More profile images
        - More credits
        - Telugu film industry presence

        Args:
            actor_name: Actor name to disambiguate

        Returns:
            Best matching actor details or None if no good match found
        """
        logger.info(f"Disambiguating actor: {actor_name}")
        
        try:
            results = self.search_actors(actor_name)
            
            if not results:
                logger.warning(f"No results found for '{actor_name}'")
                return None
            
            # Score each result
            scored_results = []
            for result in results:
                score = 0
                person_id = result.get("id")
                
                # Prefer exact name match
                if result.get("name", "").lower() == actor_name.lower():
                    score += 100
                
                # Prefer higher popularity
                popularity = result.get("popularity", 0)
                score += min(popularity, 100)
                
                # Prefer actors with profile images
                if result.get("profile_path"):
                    score += 50
                
                # Check if actor has significant credits
                if person_id:
                    try:
                        movies, tv_shows = self.get_actor_filmography(person_id)
                        credit_count = len(movies) + len(tv_shows)
                        score += min(credit_count, 50)
                        
                        # Bonus for Telugu confirmation
                        is_telugu, _ = self.verify_actor_is_telugu(person_id)
                        if is_telugu:
                            score += 200
                    except Exception as e:
                        logger.warning(f"Could not verify credits for {result.get('name')}: {str(e)}")
                
                scored_results.append((score, result))
            
            # Sort by score (descending)
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            best_result = scored_results[0][1] if scored_results else None
            
            if best_result:
                logger.info(f"Best match for '{actor_name}': {best_result.get('name')} (ID: {best_result.get('id')})")
            
            return best_result
        except Exception as e:
            logger.error(f"Error disambiguating actor '{actor_name}': {str(e)}")
            return None

    def get_complete_actor_profile(self, actor_name: str) -> Optional[Dict]:
        """
        Get complete actor profile with all necessary information.

        Args:
            actor_name: Actor name

        Returns:
            Complete actor profile or None
        """
        logger.info(f"Building complete profile for: {actor_name}")
        
        try:
            # Find best matching actor
            actor_info = self.disambiguate_actor(actor_name)
            
            if not actor_info:
                logger.error(f"Could not find actor: {actor_name}")
                return None
            
            person_id = actor_info["id"]
            
            # Get detailed information
            details = self.get_actor_details(person_id)
            
            # Get images from profile
            images = self.get_actor_images(person_id)
            
            # Get filmography
            movies, tv_shows = self.get_actor_filmography(person_id)
            
            # Verify Telugu status
            is_telugu, telugu_msg = self.verify_actor_is_telugu(person_id)
            
            profile = {
                "tmdb_id": person_id,
                "name": details.get("name"),
                "profile_image": details.get("profile_path"),
                "biography": details.get("biography"),
                "popularity": details.get("popularity"),
                "known_for_department": details.get("known_for_department"),
                "images": images,
                "movies": movies,
                "tv_shows": tv_shows,
                "is_telugu_actor": is_telugu,
                "telugu_verification": telugu_msg,
                "total_credits": len(movies) + len(tv_shows),
            }
            
            logger.info(f"Complete profile for {details.get('name')}: {len(images)} images, {len(movies)} movies, {len(tv_shows)} TV shows")
            
            return profile
        except Exception as e:
            logger.error(f"Error building complete profile for '{actor_name}': {str(e)}")
            return None

    def get_image_url(self, image_path: str, size: str = "original") -> str:
        """
        Construct full image URL from TMDb image path.

        Args:
            image_path: Image path from TMDb
            size: Image size (original, w500, w342, etc.)

        Returns:
            Full image URL
        """
        return f"{self.image_url}/{size}{image_path}"
