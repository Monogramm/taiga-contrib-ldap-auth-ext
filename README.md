# Taiga contrib ldap auth

Extended [Taiga.io](https://taiga.io/) plugin for LDAP authentication.

This is a fork of [ensky/taiga-contrib-ldap-auth](https://github.com/ensky/taiga-contrib-ldap-auth) which also retrieves the various contributions and other forks into one.


## Installation

Install the PIP package `taiga-contrib-ldap-auth-ext` in your
`taiga-back` python virtualenv:

```bash
  pip install taiga-contrib-ldap-auth-ext
```

If needed, change `pip` to `pip3` to use the Python 3 version.


## Configuration

### taiga-back

Add the following to `settings/local.py`:

```python
INSTALLED_APPS += ["taiga_contrib_ldap_auth_ext"]

LDAP_SERVER = 'ldap://ldap.example.com'
LDAP_PORT = 389

# Flag to enable LDAP with STARTTLS before bind
LDAP_START_TLS = False

# Support of alternative LDAP ciphersuites
#from ldap3 import Tls
#import ssl

#LDAP_TLS_CERTS = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1, ciphers='RSA+3DES')

# Full DN of the service account use to connect to LDAP server and search for login user's account entry
# If LDAP_BIND_DN is not specified, or is blank, then an anonymous bind is attempated
LDAP_BIND_DN = 'CN=SVC Account,OU=Service Accounts,OU=Servers,DC=example,DC=com'
LDAP_BIND_PASSWORD = '<REPLACE_ME>'

# Starting point within LDAP structure to search for login user
LDAP_SEARCH_BASE = 'OU=DevTeam,DC=example,DC=net'

# Additional search criteria to the filter (will be ANDed)
#LDAP_SEARCH_FILTER_ADDITIONAL = '(mail=*)'

# Names of attributes to get username, e-mail and full name values from
# These fields need to have a value in LDAP 
LDAP_USERNAME_ATTRIBUTE = 'uid'
LDAP_EMAIL_ATTRIBUTE = 'mail'
LDAP_FULL_NAME_ATTRIBUTE = 'displayName'

# Fallback on normal authentication method if this LDAP auth fails. Uncomment to enable.
# LDAP_FALLBACK = "normal"

# Function to map LDAP username to local DB user unique identifier.
# Upon successful LDAP bind, will override returned username attribute
# value. May result in unexpected failures if changed after the database
# has been populated.
# 
def _ldap_slugify(uid: str) -> str:
    # example: force lower-case
    #uid = uid.lower()
    return uid
    
# To enable the function above, uncomment the line below to store the function in the variable
#LDAP_MAP_USERNAME_TO_UID = _ldap_slugify

# Similarly, you can apply filters to the email and name by defining functions and specifying them here in the same way
#LDAP_MAP_EMAIL = _ldap_map_email
#LDAP_MAP_NAME = _ldap_map_name


```

A dedicated domain service account user (specified by `LDAP_BIND_DN`)
performs a search on LDAP for an account that has a
`LDAP_USERNAME_ATTRIBUTE` or `LDAP_EMAIL_ATTRIBUTE` matching the
user-provided login.

If the search is successful, then the returned entry and the
user-provided password are used to attempt a bind to LDAP. If the bind is
successful, then we can say that the user is authorised to log in to
Taiga.

If the `LDAP_BIND_DN` configuration setting is not specified or is
blank, then an anonymous bind is attempted to search for the login
user's LDAP account entry.

**RECOMMENDATION**: for security reasons, if you are using a service
account for performing the LDAP search, it should be configured to only
allow reading/searching the LDAP structure. No other LDAP (or wider
network) permissions should be granted for this user because you need
to specify the service account password in the configuration file. A
suitably strong password should be chosen, eg. VmLYBbvJaf2kAqcrt5HjHdG6


**Notes:**
* if you are using the Taiga's built-in `USER_EMAIL_ALLOWED_DOMAINS` config option, all LDAP email addresses will still be filtered through this list. Ensure that if `USER_EMAIL_ALLOWED_DOMAINS` != `None`, that your corporate LDAP email domain is also listed there. This is due to the fact that LDAP users are automatically "registered" behind the scenes on their first login.
* if you plan to only allow your LDAP users to access Taiga, set the `PUBLIC_REGISTER_ENABLED` config option to `False`. This will prevent any external user to register while still automatically register LDAP users on their first login.

### taiga-front

Change the `loginFormType` setting to `"ldap"` in `dist/conf.json`:

```json
    ...
    "loginFormType": "ldap",
    ...
```
