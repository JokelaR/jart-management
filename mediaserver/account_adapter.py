from allauth.account.adapter import DefaultAccountAdapter # pyright: ignore[reportMissingTypeStubs]
from django.http import HttpRequest

class NoLocalUsersAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return False