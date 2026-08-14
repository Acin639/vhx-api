import json
import re
from html import unescape
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "http://www.xvideos2.com"

TIMEOUT = 20


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Mobile Safari/537.36"
    ),

    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    )
})


# ============================================================
# GET HTML
# ============================================================

def get_html(url):

    response = session.get(
        url,
        timeout=TIMEOUT,
        allow_redirects=True
    )

    response.raise_for_status()

    return response.text


# ============================================================
# MAKE URL ABSOLUTE
# ============================================================

def absolute_url(
    value,
    page_url=BASE_URL
):

    if not value:
        return None

    value = str(value).strip()

    if not value:
        return None

    return urljoin(
        page_url,
        value
    )


# ============================================================
# EXTRACT JSON
# ============================================================

def extract_json(text):

    if not text:
        return None


    text = text.strip()


    # --------------------------------------------------------
    # Normal JSON
    # --------------------------------------------------------

    try:

        return json.loads(
            text
        )

    except Exception:

        pass


    # --------------------------------------------------------
    # Remove @ characters
    # --------------------------------------------------------

    cleaned = text.replace(
        "@",
        ""
    )


    try:

        return json.loads(
            cleaned
        )

    except Exception:

        pass


    # --------------------------------------------------------
    # JSON embedded in JavaScript
    # --------------------------------------------------------

    match = re.search(
        r"(\{.*\})",
        cleaned,
        re.DOTALL
    )


    if match:

        try:

            return json.loads(
                match.group(1)
            )

        except Exception:

            pass


    return None


# ============================================================
# FIND VIDEO METADATA
# ============================================================

def find_video_metadata(soup):

    scripts = soup.find_all(
        "script"
    )


    # --------------------------------------------------------
    # JSON-LD
    # --------------------------------------------------------

    for script in scripts:

        script_type = (
            script.get("type")
            or ""
        ).lower()


        if "ld+json" not in script_type:

            continue


        text = (
            script.string
            or script.get_text()
        )


        data = extract_json(
            text
        )


        if isinstance(
            data,
            dict
        ):

            return data


        if isinstance(
            data,
            list
        ):

            for item in data:

                if isinstance(
                    item,
                    dict
                ):

                    return item


    # --------------------------------------------------------
    # Ordinary scripts
    # --------------------------------------------------------

    for script in scripts:

        text = (
            script.string
            or script.get_text()
        )


        if not text:

            continue


        indicators = [

            "interactionStatistic",

            '"name"',

            '"description"',

            '"contentUrl"'

        ]


        if not any(
            x in text
            for x in indicators
        ):

            continue


        data = extract_json(
            text
        )


        if isinstance(
            data,
            dict
        ):

            return data


        if isinstance(
            data,
            list
        ):

            for item in data:

                if isinstance(
                    item,
                    dict
                ):

                    return item


    return {}


# ============================================================
# EXTRACT QUALITY URLS
# ============================================================

def extract_quality_urls(
    soup,
    video_url
):

    result = {

        "default_quality_url": None,

        "low_quality": None,

        "hd_quality": None,

        "uhd_quality": None

    }


    # --------------------------------------------------------
    # ORIGINAL HTML5 STRUCTURE
    # --------------------------------------------------------

    container = soup.select_one(
        "#html5video #html5video_base"
    )


    if container:

        links = container.select(
            "a[href]"
        )


        quality_names = [

            "default_quality_url",

            "low_quality",

            "hd_quality",

            "uhd_quality"

        ]


        for index, link in enumerate(
            links
        ):

            if index >= 4:

                break


            href = link.get(
                "href"
            )


            if not href:

                continue


            result[
                quality_names[index]
            ] = absolute_url(
                href,
                video_url
            )


    # --------------------------------------------------------
    # HLS / UHD
    # --------------------------------------------------------

    for script in soup.find_all(
        "script"
    ):

        text = (
            script.string
            or script.get_text()
        )


        if not text:

            continue


        if "setVideoHLS" not in text:

            continue


        patterns = [

            r"setVideoHLS\s*\(\s*['\"]([^'\"]+)",

            r"setVideoHLS\s*\(\s*[\"']([^\"']+)[\"']"

        ]


        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )


            if match:

                result[
                    "uhd_quality"
                ] = absolute_url(
                    match.group(1),
                    video_url
                )

                break


        if result[
            "uhd_quality"
        ]:

            break


    # --------------------------------------------------------
    # FALLBACK VIDEO LINKS
    # --------------------------------------------------------

    if not result[
        "default_quality_url"
    ]:

        for link in soup.select(
            "a[href]"
        ):

            href = link.get(
                "href"
            )


            if not href:

                continue


            lower = href.lower()


            if any(
                extension in lower
                for extension in [
                    ".mp4",
                    ".m3u8",
                    ".webm"
                ]
            ):

                result[
                    "default_quality_url"
                ] = absolute_url(
                    href,
                    video_url
                )

                break


    return result


# ============================================================
# EXTRACT VIDEO CARDS
# ============================================================

def extract_video_cards(
    html,
    page_url
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    videos = []


    # --------------------------------------------------------
    # Main selector
    # --------------------------------------------------------

    blocks = soup.select(
        "#content "
        "div.mozaique.cust-nb-cols "
        "div.thumb-block"
    )


    # --------------------------------------------------------
    # Fallback selector
    # --------------------------------------------------------

    if not blocks:

        blocks = soup.select(
            "#content .thumb-block"
        )


    # --------------------------------------------------------
    # Last fallback
    # --------------------------------------------------------

    if not blocks:

        blocks = soup.select(
            ".thumb-block"
        )


    # --------------------------------------------------------
    # Process cards
    # --------------------------------------------------------

    for block in blocks:

        # ====================================================
        # VIDEO URL
        # ====================================================

        link = block.select_one(
            ".thumb-inside "
            ".thumb "
            "a[href]"
        )


        if not link:

            link = block.select_one(
                "a[href]"
            )


        if not link:

            continue


        video_url = absolute_url(
            link.get("href"),
            page_url
        )


        if not video_url:

            continue


        # ====================================================
        # THUMBNAIL
        # ====================================================

        thumbnail = None


        image = block.select_one(
            ".thumb-inside "
            ".thumb "
            "img"
        )


        if not image:

            image = block.select_one(
                "img"
            )


        if image:

            thumbnail_attributes = [

                "data-src",

                "data-original",

                "data-lazy-src",

                "data-thumb",

                "src"

            ]


            for attribute in (
                thumbnail_attributes
            ):

                value = image.get(
                    attribute
                )


                if value:

                    thumbnail = absolute_url(
                        value,
                        page_url
                    )

                    break


        # ====================================================
        # TITLE
        # ====================================================

        title = None


        title_element = block.select_one(
            ".thumb-under "
            "p "
            "a[title]"
        )


        if not title_element:

            title_element = block.select_one(
                ".thumb-under "
                "p "
                "a"
            )


        if not title_element:

            title_element = block.select_one(
                "a[title]"
            )


        if title_element:

            title = (
                title_element.get("title")
                or
                title_element.get_text(
                    " ",
                    strip=True
                )
            )


        # ====================================================
        # DURATION
        # ====================================================

        duration = None


        duration_element = block.select_one(
            "span.duration"
        )


        if duration_element:

            duration = duration_element.get_text(
                " ",
                strip=True
            )


        # ====================================================
        # ADD VIDEO
        # ====================================================

        videos.append({

            "video_url":
                video_url,

            "thumbnail":
                thumbnail,

            "title":
                title,

            "duration":
                duration

        })


    return videos


# ============================================================
# PROCESS ONE VIDEO
# ============================================================

def process_video(
    video
):

    video_url = video.get(
        "video_url"
    )


    if not video_url:

        return None


    try:

        # ----------------------------------------------------
        # Download video page
        # ----------------------------------------------------

        html = get_html(
            video_url
        )


        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        # ----------------------------------------------------
        # Get qualities
        # ----------------------------------------------------

        qualities = extract_quality_urls(
            soup,
            video_url
        )


        # ----------------------------------------------------
        # Get metadata
        # ----------------------------------------------------

        metadata = find_video_metadata(
            soup
        )


        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title = (

            metadata.get("name")

            or

            video.get("title")

        )


        if title:

            title = unescape(
                str(title)
            )


        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        duration = (

            metadata.get("duration")

            or

            video.get("duration")

        )


        # ----------------------------------------------------
        # Views
        # ----------------------------------------------------

        views = None


        interaction = metadata.get(
            "interactionStatistic"
        )


        if isinstance(
            interaction,
            dict
        ):

            views = interaction.get(
                "userInteractionCount"
            )


        elif isinstance(
            interaction,
            list
        ):

            for item in interaction:

                if not isinstance(
                    item,
                    dict
                ):

                    continue


                views = item.get(
                    "userInteractionCount"
                )


                if views is not None:

                    break


        # ----------------------------------------------------
        # Format views
        # ----------------------------------------------------

        if views is not None:

            try:

                views = int(
                    str(views)
                    .replace(
                        ",",
                        ""
                    )
                    .replace(
                        " Views",
                        ""
                    )
                    .strip()
                )


                views = (
                    f"{views:,} Views"
                )


            except Exception:

                views = str(
                    views
                )


        # ----------------------------------------------------
        # Final object
        # ----------------------------------------------------

        return {

            "thumbnail":
                video.get(
                    "thumbnail"
                ),

            "title":
                title,

            "views":
                views,

            "default_quality_url":
                qualities[
                    "default_quality_url"
                ],

            "low_quality":
                qualities[
                    "low_quality"
                ],

            "hd_quality":
                qualities[
                    "hd_quality"
                ],

            "uhd_quality":
                qualities[
                    "uhd_quality"
                ],

            "duration":
                duration

        }


    except Exception:

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # If anything goes wrong with this video,
        # simply skip it.
        # ----------------------------------------------------

        return None


# ============================================================
# GETHOME
# ============================================================

def gethome(
    limit=10
):

    """
    Get videos from homepage.

    Examples:

        gethome()
            -> 10 videos

        gethome(5)
            -> 5 videos

        gethome(50)
            -> 50 videos

        gethome(None)
            -> all homepage videos
    """


    homepage_url = (
        BASE_URL.rstrip("/")
        + "/"
    )


    try:

        html = get_html(
            homepage_url
        )

    except Exception:

        return []


    # --------------------------------------------------------
    # Extract homepage cards
    # --------------------------------------------------------

    cards = extract_video_cards(
        html,
        homepage_url
    )


    # --------------------------------------------------------
    # Apply limit
    # --------------------------------------------------------

    if limit is not None:

        cards = cards[
            :limit
        ]


    results = []


    # --------------------------------------------------------
    # Process videos
    # --------------------------------------------------------

    for card in cards:

        result = process_video(
            card
        )


        # Failed videos are skipped

        if result is None:

            continue


        results.append(
            result
        )


    return results


# ============================================================
# SEARCH
# ============================================================

def search(
    keyword,
    page=1,
    pages=1,
    limit=10
):

    """
    Search videos.

    Parameters:

        keyword:
            Search term.

        page:
            Starting page.

        pages:
            Number of pages to search.

            1
                First page only.

            3
                Three pages.

            None
                All available pages.

        limit:
            Maximum number of returned videos.

            10
                Maximum 10.

            50
                Maximum 50.

            None
                No limit.


    Examples:

        search("hello")

        search(
            "hello",
            limit=20
        )

        search(
            "hello",
            page=2
        )

        search(
            "hello",
            pages=5
        )

        search(
            "hello",
            pages=None,
            limit=100
        )

        search(
            "hello",
            pages=None,
            limit=None
        )
    """


    results = []

    seen = set()

    current_page = page

    pages_checked = 0


    while True:

        # ====================================================
        # PAGE LIMIT
        # ====================================================

        if (

            pages is not None

            and

            pages_checked >= pages

        ):

            break


        # ====================================================
        # RESULT LIMIT
        # ====================================================

        if (

            limit is not None

            and

            len(results) >= limit

        ):

            break


        # ====================================================
        # BUILD SEARCH URL
        # ====================================================

        params = {

            "k":
                keyword,

            "p":
                current_page - 1,

            "top":
                ""

        }


        search_url = (

            BASE_URL.rstrip("/")

            + "/?"

            + urlencode(params)

        )


        # ====================================================
        # GET PAGE
        # ====================================================

        try:

            html = get_html(
                search_url
            )

        except Exception:

            break


        # ====================================================
        # FIND VIDEOS
        # ====================================================

        cards = extract_video_cards(
            html,
            search_url
        )


        if not cards:

            break


        pages_checked += 1


        new_videos = 0


        # ====================================================
        # PROCESS VIDEOS
        # ====================================================

        for card in cards:

            # ------------------------------------------------
            # Stop at result limit
            # ------------------------------------------------

            if (

                limit is not None

                and

                len(results) >= limit

            ):

                break


            video_url = card.get(
                "video_url"
            )


            if not video_url:

                continue


            # ------------------------------------------------
            # Skip duplicates
            # ------------------------------------------------

            if video_url in seen:

                continue


            seen.add(
                video_url
            )


            # ------------------------------------------------
            # Process
            # ------------------------------------------------

            result = process_video(
                card
            )


            # ------------------------------------------------
            # Failed = skip
            # ------------------------------------------------

            if result is None:

                continue


            results.append(
                result
            )


            new_videos += 1


        # ====================================================
        # NO NEW RESULTS
        # ====================================================

        if new_videos == 0:

            break


        # ====================================================
        # NEXT PAGE
        # ====================================================

        current_page += 1


    return results