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
from django.apps import apps

from taiga.base.utils.slug import slugify_uniquely
from taiga.auth.services import make_auth_response_data
from taiga.auth.signals import user_registered as user_registered_signal

from . import connector


def _slugify(username: str):
    """Deployment-specific username-to-unique-id slugification.

    Taiga requires a way to map LDAP attributes to local database
    unique identifiers. Depending on your setup, the sets of allowed
    characters for either may overlap only partially, or one may be
    a subset of another.

    Your LDAP may allow, for example, both users `User` and `user` to
    exist. Django's `slugify()` would map both to `user`. Taiga's
    `slugify_uniquely()` would map either to `user` if `user` doesn't
    yet exist in the database, and to `user-<something>` if it does -
    possibly uniquely on each login attempt.

    Edit this if your LDAP installation allows characters that Taiga
    slugs do not allow, or if substitutions need to be performed prior
    to slugification.

    NOTE that modifying code like this is ugly at best. Then again, so
    is making assumptions on what a username can be.

    NOTE also that adding or removing constraints on an already-populated
    database may result in unexpected failures.
    """
    # EXAMPLES PROVIDED BELOW MAY NOT WORK AS YOU EXPECT
    # example: replace common symbols found in e-mail addresses
    #username = username.replace('.', '-')
    #username = username.replace('+', '-')
    #username = username.replace('@', '-')
    # example: force lower-case
    #username = username.lower()

    return username


def ldap_login_func(request):
    """TODO: desc"""
    # although the form field is called 'username', it can be an e-mail
    # (or any other attribute)
    login_input = request.DATA.get('username', None)
    pass_input = request.DATA.get('password', None)

    # TODO: sanitize before passing to LDAP server?
    username, email, full_name = connector.login(login = login_input,
                                                 password = pass_input)

    user = register_or_update(username = username,
                               email = email,
                               full_name = full_name)

    data = make_auth_response_data(user)
    return data


@tx.atomic
def register_or_update(username: str, email: str, full_name: str):
    """
    Register new or update existing user in Django DB from LDAP data.

    Can raise `exc.IntegrityError` exceptions in case of conflict found.

    :returns: User
    """
    user_model = apps.get_model("users", "User")
    username = _slugify(username)

    try:
        # has user logged in before?
        user = user_model.objects.get(username = username)
    except user_model.DoesNotExist:
        # create a new user
        username_unique = slugify_uniquely(username,
                                           user_model,
                                           slugfield = "username")
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
