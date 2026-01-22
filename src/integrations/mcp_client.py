"""MCP client for Dice job search integration with retry logic and error handling."""

import asyncio
import time
from typing import Any, Dict, List, Optional
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class DiceMCPClient:
    """Wrapped MCP client for Dice.com job search with robust error handling."""

    def __init__(self, server_url: str = "https://mcp.dice.com/mcp"):
        """
        Initialize Dice MCP client.

        Args:
            server_url: URL of the Dice MCP server (default: https://mcp.dice.com/mcp)
        """
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s

    async def connect(self):
        """Establish connection to the Dice MCP server."""
        # Note: For HTTP/SSE transport, we'll use httpx directly
        # The MCP Python SDK primarily supports stdio transport
        # For remote HTTP servers, we need to make direct HTTP calls
        pass

    async def search_jobs(
        self,
        keyword: str,
        location: Optional[str] = None,
        radius: Optional[float] = None,
        radius_unit: Optional[str] = "miles",
        jobs_per_page: Optional[int] = 25,
        page_number: Optional[int] = 1,
        posted_date: Optional[str] = None,
        workplace_types: Optional[List[str]] = None,
        employment_types: Optional[List[str]] = None,
        employer_types: Optional[List[str]] = None,
        willing_to_sponsor: Optional[bool] = None,
        easy_apply: Optional[bool] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search for jobs using the Dice MCP server.

        Args:
            keyword: Job title or keywords to search for (required)
            location: Geographic location (e.g., "San Francisco, CA")
            radius: Search radius from location (minimum: 1.0)
            radius_unit: Unit for radius: "mi", "km", "miles", or "kilometers"
            jobs_per_page: Number of results per page (range: 1-100)
            page_number: Page number for pagination (default: 1)
            posted_date: Filter by recency: "ONE" (1 day), "THREE" (3 days), "SEVEN" (7 days)
            workplace_types: List of ["Remote", "On-Site", "Hybrid"]
            employment_types: List of ["FULLTIME", "CONTRACTS", "PARTTIME", "THIRD_PARTY"]
            employer_types: List of ["Direct Hire", "Recruiter", "Other"]
            willing_to_sponsor: Filter for employers willing to sponsor work authorization
            easy_apply: Filter for jobs with simplified application process
            fields: Specific fields to include in response (returns all by default)

        Returns:
            Dict containing job search results with data, meta, and _links

        Raises:
            ValueError: If required parameters are missing or invalid
            httpx.HTTPError: If HTTP request fails after retries
        """
        if not keyword:
            raise ValueError("keyword parameter is required")

        # Validate numeric parameters
        if radius is not None and radius < 1.0:
            raise ValueError("radius must be >= 1.0")
        if jobs_per_page is not None and not (1 <= jobs_per_page <= 100):
            raise ValueError("jobs_per_page must be between 1 and 100")
        if page_number is not None and page_number < 1:
            raise ValueError("page_number must be >= 1")

        # Validate enum parameters
        valid_workplace_types = {"Remote", "On-Site", "Hybrid"}
        valid_employment_types = {"FULLTIME", "CONTRACTS", "PARTTIME", "THIRD_PARTY"}
        valid_posted_dates = {"ONE", "THREE", "SEVEN"}
        valid_radius_units = {"mi", "km", "miles", "kilometers"}

        if workplace_types:
            invalid = set(workplace_types) - valid_workplace_types
            if invalid:
                raise ValueError(
                    f"Invalid workplace_types: {invalid}. Must be {valid_workplace_types}"
                )

        if employment_types:
            invalid = set(employment_types) - valid_employment_types
            if invalid:
                raise ValueError(
                    f"Invalid employment_types: {invalid}. Must be {valid_employment_types}"
                )

        if posted_date and posted_date not in valid_posted_dates:
            raise ValueError(
                f"Invalid posted_date: {posted_date}. Must be one of {valid_posted_dates}"
            )

        if radius_unit and radius_unit not in valid_radius_units:
            raise ValueError(
                f"Invalid radius_unit: {radius_unit}. Must be one of {valid_radius_units}"
            )

        # Build request payload
        payload = {
            "keyword": keyword,
            "jobs_per_page": jobs_per_page,
            "page_number": page_number,
        }

        # Add optional parameters
        if location:
            payload["location"] = location
        if radius is not None:
            payload["radius"] = radius
        if radius_unit:
            payload["radius_unit"] = radius_unit
        if posted_date:
            payload["posted_date"] = posted_date
        if workplace_types:
            payload["workplace_types"] = workplace_types
        if employment_types:
            payload["employment_types"] = employment_types
        if employer_types:
            payload["employer_types"] = employer_types
        if willing_to_sponsor is not None:
            payload["willing_to_sponsor"] = willing_to_sponsor
        if easy_apply is not None:
            payload["easy_apply"] = easy_apply
        if fields:
            payload["fields"] = fields

        # Execute with retry logic
        return await self._execute_with_retry(payload)

    async def _execute_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute MCP tool call with exponential backoff retry logic.

        Args:
            payload: Request payload for search_jobs

        Returns:
            Job search results

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Use proper MCP protocol with streamable HTTP client
                async with streamablehttp_client(self.server_url) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        # Initialize the MCP connection
                        await session.initialize()

                        # Call the search_jobs tool via MCP protocol
                        result = await session.call_tool("search_jobs", payload)

                        # Extract content from MCP response
                        # MCP returns CallToolResult with content array
                        if result.content:
                            import json

                            # The first content item should contain the JSON response
                            content = result.content[0]
                            if hasattr(content, "text"):
                                return json.loads(content.text)
                            elif hasattr(content, "data"):
                                # Handle if it's returned as binary data
                                import base64

                                data = base64.b64decode(content.data)
                                return json.loads(data.decode("utf-8"))

                        # If no content, return empty result
                        return {"data": [], "meta": {}}

            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()

                # Check if it's a rate limit error
                if "429" in error_msg or "rate limit" in error_msg:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delays[attempt]
                        await asyncio.sleep(delay)
                        continue

                # Check if it's a server error
                if "500" in error_msg or "502" in error_msg or "503" in error_msg:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delays[attempt]
                        await asyncio.sleep(delay)
                        continue

                # For other errors, retry once more if we have attempts left
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    await asyncio.sleep(delay)
                    continue

                # Last attempt failed, raise the exception
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise RuntimeError("All retries exhausted without specific error")

    async def close(self):
        """Close the MCP client connection."""
        if self.session:
            await self.session.close()
            self.session = None


# Synchronous wrapper for easier use in non-async contexts
class DiceMCPClientSync:
    """Synchronous wrapper around DiceMCPClient."""

    def __init__(self, server_url: str = "https://mcp.dice.com/mcp"):
        self.client = DiceMCPClient(server_url)

    def search_jobs(self, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for search_jobs."""
        return asyncio.run(self.client.search_jobs(**kwargs))

    def close(self):
        """Close the client connection."""
        asyncio.run(self.client.close())
