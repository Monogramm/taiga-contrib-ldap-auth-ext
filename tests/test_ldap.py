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

from taiga_contrib_ldap_auth_ext import connector
from unittest.mock import patch, Mock

import pytest
import sys

sys.path.append("../taiga-back/")


def test_ldap_login_success():
    BASE_EMAIL = "@example.com"
    with patch("taiga_contrib_ldap_auth_ext.connector.Server") as m_server, \
            patch("taiga_contrib_ldap_auth_ext.connector.Connection") as m_connection, \
            patch("taiga_contrib_ldap_auth_ext.connector.BASE_EMAIL", new=BASE_EMAIL):
        m_server.return_value = Mock()
        m_connection.return_value = Mock()

        login = "**userName**"
        password = "**password**"
        (username, email, full_name) = connector.login(login, password)
        assert username == login
        assert email == login + BASE_EMAIL
        assert full_name == login


def test_ldap_login_fail():
    with pytest.raises(connector.LDAPError) as e:
        login = "**userName**"
        password = "**password**"
        connector.login(login, password)

    assert e.value.status_code == 400
    assert "error_message" in e.value.detail
