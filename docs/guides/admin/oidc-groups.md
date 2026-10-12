# OIDC group/role based access control

Timesketch can use group or role claims from an OpenID Connect (OIDC) identity
provider to restrict who can log in, to create and fill Timesketch groups and
to grant admin privileges.

This builds on the general OIDC login setup (`GOOGLE_OIDC_ENABLED`,
`GOOGLE_OIDC_CLIENT_ID`, ...). See `data/timesketch.conf` for all options.

!!! warning "Google OIDC is not supported"
    Google's own OIDC provider does not include a groups claim in its ID
    tokens. These features therefore only work with other OIDC providers
    configured via `GOOGLE_OIDC_AUTH_URL` and `GOOGLE_OIDC_DISCOVERY_URL`
    (e.g. Keycloak, Okta, Microsoft Entra ID), despite the `GOOGLE_` prefix of
    the option names.

## Configuration

| Option | Description |
| --- | --- |
| `GOOGLE_OIDC_GROUPS_CLAIM` | Name of the token claim holding groups/roles (e.g. `groups`, `roles`). `None` disables all features on this page. |
| `GOOGLE_OIDC_SCOPES` | Scopes requested from the provider. Add the scope your provider needs to emit the claim. |
| `GOOGLE_OIDC_GROUPS_SEPARATOR` | Split a string claim into several groups using this separator. |
| `GOOGLE_OIDC_GROUPS_REGEX` | Extract the group name from each raw value. The first capture group is used if present, otherwise the whole match. Values that do not match are ignored. |
| `GOOGLE_OIDC_ALLOWED_GROUPS` | Groups allowed to log in. |
| `GOOGLE_OIDC_ADMIN_GROUP` | Members of this group are made Timesketch admins. |
| `GOOGLE_OIDC_GROUPS_SYNC_ENABLED` | Create Timesketch groups and add the user to them at login. |
| `GOOGLE_OIDC_GROUPS_REMOVE_STALE` | Also remove memberships (and admin) that are no longer in the token. |

Example for an LDAP style claim:

```python
GOOGLE_OIDC_GROUPS_CLAIM = "groups"
GOOGLE_OIDC_GROUPS_REGEX = r"CN=([^,]+)"
GOOGLE_OIDC_ALLOWED_GROUPS = ["Analysts", "Admins"]
GOOGLE_OIDC_ADMIN_GROUP = "Admins"
GOOGLE_OIDC_GROUPS_SYNC_ENABLED = True
```

## Behaviour and caveats

### Access control

* `GOOGLE_OIDC_ALLOWED_USERS` and `GOOGLE_OIDC_ALLOWED_GROUPS` add up: a user
  may log in if they are listed in `GOOGLE_OIDC_ALLOWED_USERS` **or** are a
  member of an allowed group. This allows group based access plus individual
  exceptions (external consultants, service or break-glass accounts). If only
  one list is set, only that list applies. If both are empty, every
  authenticated user is allowed.
* When `GOOGLE_OIDC_ALLOWED_GROUPS` is set, only groups from that list are
  synced to Timesketch.
* Denied logins are logged with the user, whether the claim was present and
  group counts, but not the group names.

### Synchronization happens at login only

Groups and admin status are updated on each OIDC login. Existing sessions stay
valid and a user who left the identity provider keeps their Timesketch
memberships. Those memberships grant nothing because the user can no longer log
in. "Stale" cleanup therefore means *at the next login*, not immediately.

The user is only logged in after the sync succeeded. If the sync fails, the
login fails with an error and no session is created.

### Admin group

Admin status is only granted or revoked when `GOOGLE_OIDC_ADMIN_GROUP` is set.
Without it, admins created with `tsctl make-admin` are never touched, even with
`GOOGLE_OIDC_GROUPS_REMOVE_STALE = True`.

### The identity provider becomes the source of truth

With `GOOGLE_OIDC_GROUPS_REMOVE_STALE = True`, users are removed from **every**
Timesketch group that is not in their token, including groups managed locally
with `tsctl create-group` / `tsctl add-group-member`. Enabling it on an
existing instance can remove sketch access that was granted through those
groups.

Do not combine it with `tsctl sync-groups-from-json`: the two would overwrite
each other's memberships.

### Missing or incomplete claims

* If the configured claim is missing from a token, a warning is logged and the
  user is treated as having no groups. With `REMOVE_STALE` enabled this removes
  their synced groups, so check the provider's claim mapping and scopes.
* If the provider marks the claim as incomplete (the token has the claim listed
  in `_claim_names`, as Microsoft Entra ID does for users in too many groups,
  "group overage"), the login is rejected with an error instead of syncing a
  partial list. Configure the provider to emit group names or roles for the
  application, or reduce the number of groups assigned to the user.

### Group names

* Group names longer than 255 characters (the database limit) are skipped and a
  warning is logged. Use `GOOGLE_OIDC_GROUPS_REGEX` to shorten raw values such
  as full LDAP DNs.
* An existing Timesketch group with the same name is reused.
* An invalid `GOOGLE_OIDC_GROUPS_REGEX` is logged as a configuration error and
  logins fail with HTTP 500 until it is fixed.
