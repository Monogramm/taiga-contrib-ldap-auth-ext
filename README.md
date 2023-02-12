![PyPI - License](https://img.shields.io/pypi/l/taiga-contrib-ldap-auth-ext.svg?style=flat-square)

# Taiga contrib ldap auth ext²

Extended [Taiga.io](https://taiga.io/) plugin for LDAP authentication.

This is a fork of [Monogramm/taiga-contrib-ldap-auth-ext](https://github.com/Monogramm/taiga-contrib-ldap-auth-ext), which, in turn, is a fork of [ensky/taiga-contrib-ldap-auth](https://github.com/ensky/taiga-contrib-ldap-auth).

Compared to Monogramm/taiga-contrib-ldap-auth-ext, this repo has the following changes:

* Add step-by-step Docker setup guide to README
* Adjust sample configuration in README

You can always also [compare the changes in-depth on GitHub](https://github.com/Monogramm/taiga-contrib-ldap-auth-ext/compare/master...TuringTux:taiga-contrib-ldap-auth-ext:master).

## :whale: Installation & Configuration with Docker

If you installed a dockerized Taiga using the 30 Minute Setup approach, you should be able to install this plugin using this guide.

The following will assume that you have a clone of the [kaleidos-ventures/taiga-docker](https://github.com/kaleidos-ventures/taiga-docker) repository on the computer you want to host Taiga on.

### taiga-back

1. Edit the `taiga-back` section in the `docker-compose.yml`: Replace `image: taigaio/taiga-back:latest` with `build: ./custom-back`
2. Create a folder `custom-back` next to the `docker-compose.yml` file
3. In this folder, create a file `config.append.py`. The contents of the file are collapsed below.
4.  In this folder, also create a `Dockerfile`. The contents of the file are collapsed below.

If you were to start Taiga now, it would not pull the `taiga-back` directly from Docker Hub but instead build the image from the specified `Dockerfile`. This is exactly what we want, however, do not start Taiga yet – there is still work to be done in `taiga-front`.

#### `custom-back/config.append.py`

<details>
<summary>Click here to expand</summary>

```python
INSTALLED_APPS += ["taiga_contrib_ldap_auth_ext"]

LDAP_SERVER = "ldaps://ldap.example.com"
LDAP_PORT = 636

LDAP_BIND_DN = "CN=SVC Account,OU=Service Accounts,OU=Servers,DC=example,DC=com"
LDAP_BIND_PASSWORD = "verysecurepassword"

LDAP_SEARCH_BASE = 'OU=DevTeam,DC=example,DC=net'

LDAP_USERNAME_ATTRIBUTE = "uid"
LDAP_EMAIL_ATTRIBUTE = "mail"
LDAP_FULL_NAME_ATTRIBUTE = "givenName"

LDAP_SAVE_LOGIN_PASSWORD = False

LDAP_MAP_USERNAME_TO_UID = None
```

Change the following fields matching your setup:

**`LDAP_SERVER` and `LDAP_PORT`:** You will definitely have to change the server URL. If possible, try to keep the `ldaps://` to use a secure connection. The port can likely stay as is, unless...

* ... you run the LDAP server on a different (non-standard) port.
* ... you want to use unencrypted, insecure LDAP: In this case, change `ldaps://` to `ldap://` and the port to 389.
* ... you want to use STARTTLS. In this case, you have to make the same changes as for unencrypted, insecure LDAP and set `LDAP_START_TLS = True`, making the section look like this:
    ```python
    LDAP_SERVER = "ldap://ldap.example.com"
    LDAP_PORT = 389
    LDAP_START_TLS = True
    ```
    What happens is that an unencrypted connection is established first, but then upgraded to a secure connection. To the best of my knowledge, this should also be safe – however, I like the `ldaps://` variant more.

**`LDAP_BIND_DN`, `LDAP_BIND_PASSWORD`**: You will need to change them. 

The bind user is a dedicated service account. The plugin will connect to the LDAP server using this service account and search for an LDAP entry that has a `LDAP_USERNAME_ATTRIBUTE` or `LDAP_EMAIL_ATTRIBUTE` matching the user-provided login.

If the search is successful, the found LDAP entry and the user-provided password are used to attempt a bind to LDAP. If the bind is successful, then we can say that the user is authorised to log in to Taiga.

If `LDAP_BIND_DN` is not specified or blank, an anonymous bind is attempted.

It is recommended to limit the service account and only allow it to read and search the LDAP structure (no write or other LDAP access). The credentials should also not be used for any other account on the network. This minimizes the damage in cases of a successful LDAP injection or if you ever accidentially give someone access to the configuration file (e.g. by committing it into version control or having misconfigured permissions). Use a suitably strong, ideally randomly generated password.

**`LDAP_SEARCH_BASE`**: The subtree where the users are located.

**`LDAP_USERNAME_ATTRIBUTE`, `LDAP_EMAIL_ATTRIBUTE`, `LDAP_FULL_NAME_ATTRIBUTE`**: These are the LDAP attributes used to get the username, email and full name shown in the Taiga application. They need to have a value in LDAP. Depending on your LDAP setup, you might need to change them.

**`LDAP_SAVE_LOGIN_PASSWORD`**: Set this to `True` or remove the line if you want to store the passwords in the local database as well.

**`LDAP_MAP_USERNAME_TO_UID`**: This line fixes a bug. If omitted, the plugin will likely crash and no authentication is possible.

<!-- TODO: Explain this -->

There are several more configurable options. See the original Monogramm plugin repository for more details.
</details>

#### `custom-back/Dockerfile`

<details>
<summary>Click here to expand</summary>

```Dockerfile
FROM taigaio/taiga-back:latest

# Insert custom configuration into the taiga configuration file
COPY config.append.py /taiga-back/settings
RUN cat /taiga-back/settings/config.append.py >> /taiga-back/settings/config.py && rm /taiga-back/settings/config.append.py

# Install git, because we need it to install the taiga-ldap-contrib-auth-ext package
RUN apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install git+https://github.com/TuringTux/taiga-contrib-ldap-auth-ext-2.git

RUN apt-get purge -y git \
    && apt-get autoremove -y
```

The statements in the Dockerfile have the following effect:

1. `FROM ...` bases the image we build on the official `taigaio/taiga-back` image.
2. `COPY ...` and `RUN ...` copy the `config.append.py` file into the container, append it to `/taiga-back/settings/config.py` and then delete it again.
3. `RUN apt-get ...` fetches the apt package lists, installs Git and removes the lists again (to save some space)
4. `RUN pip install ...` installs this plugin directly from Git (this is why we had to install Git)
5. `RUN apt-get purge ...` removes Git again (and all its dependencies) because we only needed it to install the plugin.
</details>

### taiga-front

1. Edit the `taiga-front` section in the `docker-compose.yml`. Insert the following below `networks`:

    ```yml
    volumes:
    - ./custom-front/conf.override.json:/usr/share/nginx/html/conf.json
    ```

    There should already be a commented block hinting that you can do this (just with a different path). You can delete this block, or, alternatively, place the file at the path given there and just remove the `# `.

2. Create a folder `custom-front` next to the `docker-compose.yml` file
3. In this folder, create a file `conf.override.json`. The contents of the file are collapsed below.

#### `custom-front/conf.override.json`

This file will replace the `conf.json` file. As the `conf.json` is normally automatically generated at runtime from the configuration in your `docker-compose.yml`, this is a bit trickier. Basically, the process boils down to this:

1. Somehow get a valid `conf.json`
2. Create a modified version by adding the following entry somewhere in the JSON: 
    ```json
    "loginFormType": "ldap",
    ```

The question is: How do you get a valid `conf.json`?

* The [relevant section of the Taiga 30 min setup guide](https://community.taiga.io/t/taiga-30min-setup/170#map-a-confjson-file-23) recommends to use an example `config.json` which you then have to adjust.
* Alternatively, you could also start the container first without any adjustments, and then copy the file out like this:
    ```bash
    docker cp taiga_taiga-front_1:/usr/share/nginx/html/conf.json conf.json
    ```
    You then have a valid, production-ready `conf.json` you can just extend by the entry mentioned above. I'd recommend this method.

## :bulb: Further notes

* If you are using the Taiga's built-in `USER_EMAIL_ALLOWED_DOMAINS` config option, all LDAP email addresses will still be filtered through this list. Ensure that if `USER_EMAIL_ALLOWED_DOMAINS` != `None`, that your corporate LDAP email domain is also listed there. This is due to the fact that LDAP users are automatically "registered" behind the scenes on their first login.
* Instead of appending to the `config.py` file in `taiga-back`, you can also insert the configuration into `common.py`. In our tests, both ways worked.
