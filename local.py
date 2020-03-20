# If you want to modify this file, I recommend check out docker-taiga-example
# https://github.com/benhutchins/docker-taiga-example
#
# Please modify this file as needed, see the local.py.example for details:
# https://github.com/taigaio/taiga-back/blob/master/settings/local.py.example
#
# Importing docker provides common settings, see:
# https://github.com/benhutchins/docker-taiga/blob/master/docker-settings.py
# https://github.com/taigaio/taiga-back/blob/master/settings/common.py

from .docker import *
from ldap3 import Tls
import ssl

#########################################
## LDAP
#########################################

if os.getenv('TAIGA_ENABLE_LDAP').lower() == 'true':
    # see https://github.com/Monogramm/taiga-contrib-ldap-auth-ext
    print("Taiga contrib LDAP Auth Ext enabled", file=sys.stderr)
    INSTALLED_APPS += ["taiga_contrib_ldap_auth_ext"]

    if os.getenv('TAIGA_LDAP_USE_TLS').lower() == 'true':
        # Flag to enable LDAP with STARTTLS before bind
        LDAP_START_TLS = True
        LDAP_TLS_CERTS = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1, ciphers='RSA+3DES')
    else:
        LDAP_START_TLS = False

    LDAP_SERVER = os.getenv('TAIGA_LDAP_SERVER')
    LDAP_PORT = int(os.getenv('TAIGA_LDAP_PORT'))

    # Full DN of the service account use to connect to LDAP server and search for login user's account entry
    # If LDAP_BIND_DN is not specified, or is blank, then an anonymous bind is attempated
    LDAP_BIND_DN = os.getenv('TAIGA_LDAP_BIND_DN')
    LDAP_BIND_PASSWORD = os.getenv('TAIGA_LDAP_BIND_PASSWORD')

    # Starting point within LDAP structure to search for login user
    # Something like 'ou=People,dc=company,dc=com'
    LDAP_SEARCH_BASE = os.getenv('TAIGA_LDAP_BASE_DN')

    # Additional search criteria to the filter (will be ANDed)
    #LDAP_SEARCH_FILTER_ADDITIONAL = '(mail=*)'

    # Names of attributes to get username, e-mail and full name values from
    # These fields need to have a value in LDAP
    LDAP_USERNAME_ATTRIBUTE = os.getenv('TAIGA_LDAP_USERNAME_ATTRIBUTE')
    LDAP_EMAIL_ATTRIBUTE = os.getenv('TAIGA_LDAP_EMAIL_ATTRIBUTE')
    LDAP_FULL_NAME_ATTRIBUTE = os.getenv('TAIGA_LDAP_FULL_NAME_ATTRIBUTE')

    # Option to not store the passwords in the local db
    if os.getenv('TAIGA_LDAP_SAVE_LOGIN_PASSWORD').lower() == 'false':
        LDAP_SAVE_LOGIN_PASSWORD = False

    # Fallback on normal authentication method if this LDAP auth fails. Uncomment to enable.
    LDAP_FALLBACK = os.getenv('TAIGA_LDAP_FALLBACK')

    # Function to map LDAP username to local DB user unique identifier.
    # Upon successful LDAP bind, will override returned username attribute
    # value. May result in unexpected failures if changed after the database
    # has been populated.
    def _ldap_slugify(uid: str) -> str:
        # example: force lower-case
        uid = uid.lower()
        return uid

    LDAP_MAP_USERNAME_TO_UID = _ldap_slugify

    ## For additional configuration options, look at:
    # https://github.com/taigaio/taiga-back/blob/master/settings/local.py.example