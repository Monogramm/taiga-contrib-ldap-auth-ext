# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db import transaction as tx
from django.conf import settings
from django.apps import apps

from taiga.base.connectors.exceptions import ConnectorBaseException, BaseException
from taiga.base.utils.slug import slugify_uniquely
from taiga.auth.services import make_auth_response_data
from taiga.auth.signals import user_registered as user_registered_signal
from taiga.auth.services import get_auth_plugins

from . import connector

FALLBACK = getattr(settings, "LDAP_FALLBACK", "")

SLUGIFY = getattr(settings, 'LDAP_MAP_USERNAME_TO_UID', '')
EMAIL_MAP = getattr(settings, 'LDAP_MAP_EMAIL', '')
NAME_MAP = getattr(settings, 'LDAP_MAP_NAME', '')


def ldap_login_func(request):
    """TODO: desc"""
    # although the form field is called 'username', it can be an e-mail
    # (or any other attribute)
    login_input = request.DATA.get('username', None)
    password_input = request.DATA.get('password', None)

    try:
        # TODO: make sure these fields are sanitized before passing to LDAP server!
        username, email, full_name = connector.login(login = login_input, password = password_input)
    except connector.LDAPUserLoginError as ldap_error:
        # If no fallback authentication is specified, raise the original LDAP error
        if not FALLBACK:
            raise

        # Try normal authentication
        try:
            return get_auth_plugins()["normal"]["login_func"](request)
        except BaseException as normal_error:
            # Merge error messages of 'normal' and 'ldap' auth.
            raise ConnectorBaseException({
                "error_message": {
                    "ldap": ldap_error.detail["error_message"],
                    "normal": normal_error.detail
                }
            })
    else:
        # LDAP Auth successful
        user = register_or_update(username = username, email = email, full_name = full_name)
        data = make_auth_response_data(user)
        return data


@tx.atomic
def register_or_update(username: str, email: str, full_name: str):
    """
    Register new or update existing user in Django DB from LDAP data.

    Can raise `exc.IntegrityError` exceptions in case of conflict found.

    :returns: User
    """
    user_model = apps.get_model('users', 'User')

    username_unique = username
    if SLUGIFY:
        username_unique = SLUGIFY(username)        
        
    if EMAIL_MAP:
        email = EMAIL_MAP(email)

        
    if NAME_MAP:
        full_name = NAME_MAP(full_name)

    try:
        # has user logged in before?
        user = user_model.objects.get(username = username_unique)
    except user_model.DoesNotExist:
        # create a new user
        user = user_model.objects.create(username = username_unique,
                                         email = email,
                                         full_name = full_name)
        user_registered_signal.send(sender = user.__class__, user = user)
    else:
        # update DB entry if LDAP field values differ
        if user.email != email or user.full_name != full_name:
            user_object = user_model.objects.filter(pk = user.pk)
            user_object.update(email = email, full_name = full_name)
            user.refresh_from_db()

    return user
