# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/routes/__init__.py
# Description: API routes package for organizing endpoint modules
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from myragdb.api.routes.directories import router as directories_router

__all__ = ['directories_router']
