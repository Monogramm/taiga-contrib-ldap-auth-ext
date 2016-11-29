# Taiga contrib ldap auth

Taiga.io plugin for LDAP authentication.


## Installation

Install the PIP package `taiga-contrib-ldap-auth` in your
`taiga-back` python virtualenv:

```bash
  pip install taiga-contrib-ldap-auth
```

If needed, change `pip` to `pip3` to use the Python 3 version.


## Configuration

### Taiga Back

Add the following to `settings/local.py`:

```python
  INSTALLED_APPS += ["taiga_contrib_ldap_auth"]

  LDAP_SERVER = 'ldap://ldap.example.com'
  LDAP_PORT = 389

  # Full DN of the service account use to connect to LDAP server and search for login user's account entry
  # If LDAP_BIND_DN is not specified, or is blank, then an anonymous bind is attempated
  LDAP_BIND_DN = 'CN=SVC Account,OU=Service Accounts,OU=Servers,DC=example,DC=com'
  LDAP_BIND_PASSWORD = 'replace_me'   # eg.

  # Starting point within LDAP structure to search for login user
  LDAP_SEARCH_BASE = 'OU=DevTeam,DC=example,DC=net'

  # LDAP attribute used for searching (user-provided login value will have to match this attribute's value)
  LDAP_SEARCH_ATTRIBUTE = 'uid'
  # Append this to user-provided login value given above before performing search operation
  LDAP_SEARCH_ATTRIBUTE_SUFFIX = None # '@example.com'
  # Additional search criteria to the filter (will be ANDed)
  #LDAP_SEARCH_FILTER = 'mail=*'

  # Names of attributes to get email and full name values from
  LDAP_EMAIL_ATTRIBUTE = 'mail'
  LDAP_FULL_NAME_ATTRIBUTE = 'displayName'
```

A dedicated domain service account user (specified by `LDAP_BIND_DN`)
performs a search on LDAP for
an account that has a `LDAP_SEARCH_ATTRIBUTE` matching the
user-provided login.

If the search is
successful, then the returned entry and the user-provided password
to attempt a bind to LDAP. If the bind is
successful, then we can say that the user is authorised to log in to
Taiga.

Optionally `LDAP_SEARCH_ATTRIBUTE_SUFFIX` can be set to append a string
to the login field.

If the `LDAP_BIND_DN` configuration setting is not specified or is
blank, then an anonymous bind is attempted to search for the login
user's LDAP account entry.


RECOMMENDATION: Note that if you are using a service account for
performing the LDAP search for the user that is logging on to Taiga,
for security reasons, the service account user should be configured to
only allow reading/searching the LDAP structure. No other LDAP (or wider
network) permissions should be granted for this user because you need
to specify the service account password in this file. A suitably strong
password should be chosen, eg. VmLYBbvJaf2kAqcrt5HjHdG6


### Taiga Front

Change the `loginFormType` setting to `"ldap"` in `dist/js/conf.json`:

```json
...
    "loginFormType": "ldap",
...
```
