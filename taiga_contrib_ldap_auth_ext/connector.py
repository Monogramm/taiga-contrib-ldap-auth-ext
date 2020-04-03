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

from ldap3 import Server, Connection, AUTO_BIND_NO_TLS, AUTO_BIND_TLS_BEFORE_BIND, ANONYMOUS, SIMPLE, SYNC, SUBTREE, \
    NONE

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


def connect_to_ldap_server(ldap_value, connection, auto_bind, search_filter, password):
    if connection is None:
        return

    try:

        connection.search(search_base=SEARCH_BASE,
                              search_filter=search_filter,
                              search_scope=SUBTREE,
                              attributes=[USERNAME_ATTRIBUTE,
                                          EMAIL_ATTRIBUTE, FULL_NAME_ATTRIBUTE],
                              paged_size=5)
    except Exception as e:
        error_message = "LDAP login incorrect: %s" % e
        print(error_message, flush=True)
        raise LDAPUserLoginError({"error_message": error_message})
    # we are only interested in user objects in the response
    connection.response = [r for r in connection.response if 'raw_attributes' in r and 'dn' in r]
    # stop if no search results
    if not connection.response:
        raise LDAPUserLoginError({"error_message": "LDAP login not found"})

    # handle multiple matches
    if len(connection.response) > 1:
        raise LDAPUserLoginError(
            {"error_message": "LDAP login could not be determined."})

    # handle missing mandatory attributes
    raw_attributes = connection.response[0].get('raw_attributes')
    if raw_attributes.get(USERNAME_ATTRIBUTE) or raw_attributes.get(EMAIL_ATTRIBUTE) or raw_attributes.get(
            FULL_NAME_ATTRIBUTE):
        raise LDAPUserLoginError({"error_message": "LDAP login is invalid."})

    # attempt LDAP bind
    username = raw_attributes.get(USERNAME_ATTRIBUTE)[0].decode('utf-8')
    email = raw_attributes.get(EMAIL_ATTRIBUTE)[0].decode('utf-8')
    full_name = raw_attributes.get(FULL_NAME_ATTRIBUTE)[0].decode('utf-8')
    try:
        dn = str(bytes(connection.response[0].get('dn'), 'utf-8'), encoding='utf-8')
        print(dn, flush=True)
        print("before connection", flush=True)
        print(ldap_value, flush=True)
        Connection(ldap_value, auto_bind=auto_bind, client_strategy=SYNC,
                   check_names=True, authentication=SIMPLE,
                   user=dn, password=password)
        print("after connection", flush=True)
    except Exception as e:
        error = "LDAP bind failed: %s" % e
        raise LDAPUserLoginError({"error_message": error})

    # LDAP binding successful, but some values might have changed, or
    # this is the user's first login, so return them
    return username, email, full_name


def login(username: str, password: str) -> tuple:
    """
    Connect to LDAP server, perform a search and attempt a bind.
    Can raise `exc.LDAPConnectionError` exceptions if the
    connection to LDAP fails.
    Can raise `exc.LDAPUserLoginError` exceptions if the
    login to LDAP fails.
    :returns: tuple (username, email, full_name)
    """
    tls = None
    if TLS_CERTS:
        tls = TLS_CERTS

    # Dict with server key and connection value
    server_ldap_list = []
    # Connect to the LDAP servers
    servers_list = SERVER.split(',')
    for server_address in servers_list:
        if len(server_address) <= 10:
            continue
        if server_address.lower().startswith("ldaps://"):
            use_ssl = True
        else:
            use_ssl = False
        try:
            print(server_address, flush=True)
            server = Server(server_address, port=int(PORT), get_info=NONE,
                            use_ssl=use_ssl, tls=tls)
            server_ldap_list.append(server)
        except Exception as e:
            error = "Error connecting to LDAP server: %s" % e
            raise LDAPConnectionError({"error_message": error})

    # authenticate as service if credentials provided, anonymously otherwise
    if BIND_DN is not None and BIND_DN != '':
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

    # search for user-provided login
    search_filter = '(|(%s=%s)(%s=%s))' % (
        USERNAME_ATTRIBUTE, username, EMAIL_ATTRIBUTE, username)
    if SEARCH_FILTER_ADDITIONAL:
        search_filter = '(&%s%s)' % (search_filter, SEARCH_FILTER_ADDITIONAL)

    print(server_ldap_list, flush=True)
    for server in server_ldap_list:
        try:
            c = Connection(server, auto_bind=auto_bind, client_strategy=SYNC, check_names=True,
                           user=service_user, password=service_pass, authentication=service_auth)
            if c.result.description == 'success':
                data = connect_to_ldap_server(server, c, auto_bind, search_filter, password)
            else:
                print('Connection to LDAP server refused')
        except Exception as e:
            print("Error: {0}".format(e), flush=True)
            print("Failed to authenticate against LDAP {0}".format(server.name), flush=True)
            continue
        if data is not None:
            break
    raise LDAPUserLoginError({"error_message": "Unable to authenticate user to LDAP server"})