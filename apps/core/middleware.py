from django.conf import settings


class CachePublicMiddleware:
    """Autorise le CDN à garder les pages publiques 60 secondes au maximum.

    Une page servie depuis le cache du CDN ne réveille ni la fonction ni la base.
    Jamais appliqué à l'administration, à la page de contact (marquée `never_cache`),
    ni à une réponse qui pose un cookie ou à un visiteur connecté.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.prefixe_admin = "/" + settings.ADMIN_URL

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.method in ("GET", "HEAD")
            and response.status_code == 200
            and not request.path.startswith(self.prefixe_admin)
            and not response.has_header("Cache-Control")
            and not response.cookies
            and settings.SESSION_COOKIE_NAME not in request.COOKIES
        ):
            duree = settings.DUREE_CACHE_PAGES
            response["Cache-Control"] = f"public, max-age=0, s-maxage={duree}"
        return response
