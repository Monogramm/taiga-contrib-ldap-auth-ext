# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2015 Ensky Lin <enskylin@gmail.com>
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

from ldap3 import Server, Connection, SIMPLE, ANONYMOUS, SYNC, SIMPLE, SYNC, ASYNC, SUBTREE, NONE

from django.conf import settings
from taiga.base.connectors.exceptions import ConnectorBaseException


class LDAPLoginError(ConnectorBaseException):
    pass


SERVER = getattr(settings, "LDAP_SERVER", "")
PORT = getattr(settings, "LDAP_PORT", "")

SEARCH_BASE = getattr(settings, "LDAP_SEARCH_BASE", "")
SEARCH_ATTRIBUTE = getattr(settings, "LDAP_SEARCH_ATTRIBUTE", "")
SEARCH_ATTRIBUTE_SUFFIX = getattr(settings, "LDAP_SEARCH_ATTRIBUTE_SUFFIX", "")
SEARCH_FILTER = getattr(settings, "LDAP_SEARCH_FILTER", "")
BIND_DN = getattr(settings, "LDAP_BIND_DN", "")
BIND_PASSWORD = getattr(settings, "LDAP_BIND_PASSWORD", "")

EMAIL_ATTRIBUTE = getattr(settings, "LDAP_EMAIL_ATTRIBUTE", "")
FULL_NAME_ATTRIBUTE = getattr(settings, "LDAP_FULL_NAME_ATTRIBUTE", "")

def login(login: str, password: str) -> tuple:
    """
    Connect to LDAP server, perform a search and attempt a bind.

    Can raise `exc.LDAPLoginError` exceptions if any of the
    operations failed.

    :returns: tuple (user_email, full_name)

    """

    try:
        if SERVER.lower().startswith("ldaps://"):
            use_ssl = True
        else:
            use_ssl = False
        server = Server(SERVER, port = PORT, get_info = NONE, use_ssl = use_ssl)

        if BIND_DN is not None and BIND_DN != '':
            user = BIND_DN
            password = BIND_PASSWORD
            authentication = SIMPLE
        else:
            user = None
            password = None
            authentication = ANONYMOUS
        c = Connection(server, auto_bind = True, client_strategy = SYNC, check_names = True,
                       user = user, password = password, authentication = authentication)

    except Exception as e:
        error = "Error connecting to LDAP server: %s" % e
        raise LDAPLoginError({"error_message": error})

    try:
        if(SEARCH_ATTRIBUTE_SUFFIX is not None and SEARCH_ATTRIBUTE_SUFFIX != ''):
            search_filter = '(%s=%s)' % (SEARCH_ATTRIBUTE, login + SEARCH_ATTRIBUTE_SUFFIX)
        else:
            search_filter = '(%s=%s)' % (SEARCH_ATTRIBUTE, login)

        if SEARCH_FILTER:
            search_filter = '(&%s(%s))' % (search_filter, SEARCH_FILTER)

        c.search(search_base = SEARCH_BASE,
                 search_filter = search_filter,
                 search_scope = SUBTREE,
                 attributes = [EMAIL_ATTRIBUTE,FULL_NAME_ATTRIBUTE],
                 paged_size = 5)

        if len(c.response) > 0:
            dn = c.response[0].get('dn')
            user_email = c.response[0].get('raw_attributes').get(EMAIL_ATTRIBUTE)[0].decode('utf-8')
            full_name = c.response[0].get('raw_attributes').get(FULL_NAME_ATTRIBUTE)[0].decode('utf-8')

            user_conn = Connection(server, auto_bind = True, client_strategy = SYNC, user = dn, password = password, authentication = SIMPLE, check_names = True)

            return (user_email, full_name)

        raise LDAPLoginError({"error_message": "Login or password incorrect"})

    except Exception as e:
        error = "LDAP account or password incorrect: %s" % e
        raise LDAPLoginError({"error_message": error})
