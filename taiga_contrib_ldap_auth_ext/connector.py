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

from ldap3 import Server, Connection, AUTO_BIND_NO_TLS, AUTO_BIND_TLS_BEFORE_BIND, ANONYMOUS, SIMPLE, SYNC, SUBTREE, NONE

from django.conf import settings
from taiga.base.connectors.exceptions import ConnectorBaseException


class LDAPError(ConnectorBaseException):
    pass


class LDAPConnectionError(LDAPError):
    pass


class LDAPUserLoginError(LDAPError):
    pass


# TODO https://github.com/Monogramm/taiga-contrib-ldap-auth-ext/issues/16
SERVER = getattr(settings, "LDAP_SERVER", "localhost")
PORT = getattr(settings, "LDAP_PORT", "389")

SEARCH_BASE = getattr(settings, "LDAP_SEARCH_BASE", "")
SEARCH_FILTER_ADDITIONAL = getattr(
    settings, "LDAP_SEARCH_FILTER_ADDITIONAL", "")
BIND_DN = getattr(settings, "LDAP_BIND_DN", "")
BIND_PASSWORD = getattr(settings, "LDAP_BIND_PASSWORD", "")

USERNAME_ATTRIBUTE = getattr(settings, "LDAP_USERNAME_ATTRIBUTE", "uid")
EMAIL_ATTRIBUTE = getattr(settings, "LDAP_EMAIL_ATTRIBUTE", "mail")
FULL_NAME_ATTRIBUTE = getattr(settings, "LDAP_FULL_NAME_ATTRIBUTE", "displayName")

TLS_CERTS = getattr(settings, "LDAP_TLS_CERTS", "")
START_TLS = getattr(settings, "LDAP_START_TLS", False)

ADMIN_GROUP_CLASS = getattr(settings, "LDAP_ADMIN_GROUP_CLASS", "posixGroup")
ADMIN_GROUP_MEMBER_ATTRIBUTE = getattr(settings, "LDAP_ADMIN_GROUP_MEMBER_ATTRIBUTE",
                                       "memberUid")


def _get_server() -> Server:
    """ Creates a server instance based on the available data.

    :return: a server instance
    """
    tls = None
    if TLS_CERTS:
        tls = TLS_CERTS

    # connect to the LDAP server
    use_ssl = SERVER.lower().startswith("ldaps://")

    try:
        server = Server(SERVER, port=PORT, get_info=NONE,
                        use_ssl=use_ssl, tls=tls)
    except Exception as e:
        error = f"Error connecting to LDAP server: {e}"
        raise LDAPConnectionError({"error_message": error})

    return server


def _connect(username: str = '', password: str = '') -> Connection:
    """ Creates a connection to the server.
    If a user and a password a provided, they are used for establishing a connection.
    If they are not provided and BIND_DN and BIND_PASSWORD are available,
    they are used instead.
    Otherwise an anonymous login is attempted.

    :param username: the username to be used for the connection (default: '')
    :param password: the password to be used for the connection (default: '')
    :return: a connection to the server
    """
    server = _get_server()

    # if the user and password are provided explicitly, use them
    if username and password:
        service_user = username
        service_pass = password
        service_auth = SIMPLE
    # authenticate as service if credentials provided, anonymously otherwise
    elif BIND_DN and BIND_PASSWORD:
        service_user = BIND_DN
        service_pass = BIND_PASSWORD
        service_auth = SIMPLE
    else:
        service_user = None
        service_pass = None
        service_auth = ANONYMOUS

    auto_bind = AUTO_BIND_NO_TLS
    if START_TLS:
        auto_bind = AUTO_BIND_TLS_BEFORE_BIND

    try:
        c = Connection(server, auto_bind=auto_bind, client_strategy=SYNC,
                       check_names=True, user=service_user,
                       password=service_pass, authentication=service_auth)
    except Exception as e:
        error = f"Error connecting to LDAP server: {e}"
        raise LDAPConnectionError({"error_message": error})

    return c


def login(username: str, password: str) -> tuple:
    """
    Connect to LDAP server, perform a search and attempt a bind.

    Can raise `exc.LDAPConnectionError` exceptions if the
    connection to LDAP fails.

    Can raise `exc.LDAPUserLoginError` exceptions if the
    login to LDAP fails.

    :returns: tuple (username, email, full_name)

    """
    c = _connect()

    # search for user-provided login
    search_filter = f'(|({USERNAME_ATTRIBUTE}={username})' \
                    f'({EMAIL_ATTRIBUTE}={username}))'
    if SEARCH_FILTER_ADDITIONAL:
        search_filter = f'(&{search_filter}{SEARCH_FILTER_ADDITIONAL})'
    try:
        c.search(search_base=SEARCH_BASE,
                 search_filter=search_filter,
                 search_scope=SUBTREE,
                 attributes=[USERNAME_ATTRIBUTE, EMAIL_ATTRIBUTE, FULL_NAME_ATTRIBUTE],
                 paged_size=5)
    except Exception as e:
        error = f"LDAP login incorrect: {e}"
        raise LDAPUserLoginError({"error_message": error})

    # we are only interested in user objects in the response
    c.response = [r for r in c.response if 'raw_attributes' in r and 'dn' in r]
    # stop if no search results
    if not c.response:
        raise LDAPUserLoginError({"error_message": "LDAP login not found"})
    # handle multiple matches
    elif len(c.response) > 1:
        raise LDAPUserLoginError(
            {"error_message": "LDAP login could not be determined."})

    # handle missing mandatory attributes
    attributes = c.response[0].get('attributes')
    if not (attributes.get(USERNAME_ATTRIBUTE) and
            attributes.get(EMAIL_ATTRIBUTE) and
            attributes.get(FULL_NAME_ATTRIBUTE)):
        raise LDAPUserLoginError({"error_message": "LDAP login is invalid."})

    # attempt LDAP bind
    username = attributes.get(USERNAME_ATTRIBUTE)[0]
    email = attributes.get(EMAIL_ATTRIBUTE)[0]
    full_name = attributes.get(FULL_NAME_ATTRIBUTE)[0]
    try:
        dn = c.response[0].get('dn')
        _connect(username=dn, password=password)
    except Exception as e:
        error = "LDAP bind failed: %s" % e
        raise LDAPUserLoginError({"error_message": error})

    # LDAP binding successful, but some values might have changed, or
    # this is the user's first login, so return them
    return (username, email, full_name)


def is_user_in_group(username: str, group: str) -> bool:
    """ Check if given username is member of a group.

    :param username: the username to be checked
    :param group: the group to be checked
    :return: if the username is member of the group
    """
    c = _connect()

    c.search(search_base=group,
             search_filter=f'(&(objectClass={ADMIN_GROUP_CLASS})'
                           f'({ADMIN_GROUP_MEMBER_ATTRIBUTE}={username}))',
             search_scope=SUBTREE,
             attributes=[f'{ADMIN_GROUP_MEMBER_ATTRIBUTE}'])

    return len(c.response) > 0
