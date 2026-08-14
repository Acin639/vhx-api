from flask import Flask, request, jsonify
from vhx import gethome, search


app = Flask(__name__)


# ============================================================
# HOME API
# ============================================================

@app.route("/api/home", methods=["GET"])
def home_api():

    try:

        # ?limit=10
        limit = request.args.get(
            "limit",
            default=10,
            type=int
        )


        # Prevent invalid values
        if limit < 1:

            return jsonify({
                "success": False,
                "error": "limit must be greater than 0"
            }), 400


        videos = gethome(
            limit
        )


        return jsonify({

            "success": True,

            "count": len(videos),

            "videos": videos

        })


    except Exception:

        return jsonify({

            "success": False,

            "error": "Unable to get homepage videos"

        }), 500


# ============================================================
# SEARCH API
# ============================================================

@app.route("/api/search", methods=["GET"])
def search_api():

    try:

        # ----------------------------------------------------
        # Search keyword
        # ----------------------------------------------------

        keyword = request.args.get(
            "q",
            ""
        ).strip()


        if not keyword:

            return jsonify({

                "success": False,

                "error":
                    "Search query is required. "
                    "Use ?q=your-search"

            }), 400


        # ----------------------------------------------------
        # Starting page
        # ----------------------------------------------------

        page = request.args.get(
            "page",
            default=1,
            type=int
        )


        if page < 1:

            return jsonify({

                "success": False,

                "error":
                    "page must be greater than 0"

            }), 400


        # ----------------------------------------------------
        # Number of pages
        # ----------------------------------------------------

        pages_value = request.args.get(
            "pages",
            default="1"
        )


        if pages_value.lower() == "all":

            pages = None

        else:

            try:

                pages = int(
                    pages_value
                )

            except ValueError:

                return jsonify({

                    "success": False,

                    "error":
                        "pages must be a number "
                        "or 'all'"

                }), 400


            if pages < 1:

                return jsonify({

                    "success": False,

                    "error":
                        "pages must be greater than 0"

                }), 400


        # ----------------------------------------------------
        # Result limit
        # ----------------------------------------------------

        limit_value = request.args.get(
            "limit",
            default="10"
        )


        if limit_value.lower() == "all":

            limit = None

        else:

            try:

                limit = int(
                    limit_value
                )

            except ValueError:

                return jsonify({

                    "success": False,

                    "error":
                        "limit must be a number "
                        "or 'all'"

                }), 400


            if limit < 1:

                return jsonify({

                    "success": False,

                    "error":
                        "limit must be greater than 0"

                }), 400


        # ----------------------------------------------------
        # Run scraper
        # ----------------------------------------------------

        videos = search(

            keyword,

            page=page,

            pages=pages,

            limit=limit

        )


        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "query": keyword,

            "page": page,

            "pages": (
                "all"
                if pages is None
                else pages
            ),

            "limit": (
                "all"
                if limit is None
                else limit
            ),

            "count": len(videos),

            "videos": videos

        })


    except Exception:

        return jsonify({

            "success": False,

            "error":
                "Unable to perform search"

        }), 500


# ============================================================
# API INFORMATION
# ============================================================

@app.route("/", methods=["GET"])
def index():

    return jsonify({

        "name": "VHX Video API",

        "status": "online",

        "endpoints": {

            "home":
                "/api/home?limit=10",

            "search":
                "/api/search?q=hello&page=1&pages=3&limit=20"

        }

    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({

        "success": True,

        "status": "online"

    })


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )