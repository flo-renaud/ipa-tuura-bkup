import logging
import os
import tempfile
import gssapi
import uuid


from ipalib.krb_utils import get_credentials_if_valid
from ipalib import api
from ipalib.errors import EmptyModlist
from ipalib.facts import is_ipa_client_configured
from ipalib.install.kinit import kinit_keytab, kinit_password
from ipapython import admintool, ipaldap


logger = logging.getLogger(__name__)


class IPANotFoundException(Exception):
    """
    Exception returned when an IPA user or group is not found.
    """
    pass


class _IPA(admintool.AdminTool):
    _instance = None

    def __init__(self):
        """Initialize IPA API.
           Set IPA API execution client context
           Create a connection to LDAP and bind to it
        """
        # This must be removed after IPA/LDAP scimv2 auth is implemented
        self._ipaadmin_principal = "admin"
        self._ipaadmin_password = "Secret123"

        if not is_ipa_client_configured():
            logger.error("IPA client is not configured on this system.")
            raise admintool.ScriptError()

        self._conn = None
        self._backend = None
        self._context = "client"
        self._ccache_dir = None
        self._ccache_name = None
        self._ipa_connect()
        self._ldap_connect()

    def _ipa_connect(self):
        """Init IPA API
        """
        base_config = dict(
            context=self._context, in_server=False, debug=False
        )
        try:
            if not self._valid_creds():
                self._temp_kinit()
        except Exception as e:
            logger.error(f'Failed to find default ccache {e}')

        try:
            api.bootstrap(**base_config)
            if not api.isdone("finalize"):
                api.finalize()
        except Exception as e:
            logger.info(f'bootstrap already done {e}')

        self._backend = api.Backend.rpcclient
        if not self._backend.isconnected():
            self._backend.connect(ccache=os.environ.get('KRB5CCNAME', None))

    def _valid_creds(self):
        # try GSSAPI first
        logger.info('valid creds')
        if "KRB5CCNAME" in os.environ:
            ccache = os.environ["KRB5CCNAME"]
            logger.info(f'ipa: init KRB5CCNAME set to {ccache}')

            try:
                cred = gssapi.Credentials(usage='initiate',
                                          store={'ccache': ccache})
            except gssapi.raw.misc.GSSError as e:
                logger.error(f'Failed to find default ccache {e}')
            else:
                logger.info(f'Using principal {cred.name}')
                return True

        elif "KRB5_CLIENT_KTNAME" in os.environ:
            logger.info('ktname')
            keytab = os.environ.get('KRB5_CLIENT_KTNAME', None)
            logger.info(f'KRB5_CLIENT_KTNAME set to {keytab}')
            ccache_name = "MEMORY:%s" % str(uuid.uuid4())
            os.environ["KRB5CCNAME"] = ccache_name

            try:
                logger.info('kinit keytab')
                cred = kinit_keytab(
                    self._ipaadmin_principal, keytab, ccache_name
                    )
            except gssapi.raw.misc.GSSError as e:
                logger.error(f'Kerberos authentication failed {e}')
            else:
                logger.info(f'Using principal {cred.name}')
                return True

        logger.info('get credentials if valid')
        creds = get_credentials_if_valid()
        if creds and \
           creds.lifetime > 0 and \
           "%s@" % self._ipaadmin_principal in \
           creds.name.display_as(creds.name.name_type):
            return True
        return False

    def _temp_kinit(self):
        """Kinit with password using a temporary ccache.
        """
        self._ccache_dir = tempfile.mkdtemp(prefix='krbcc')
        self._ccache_name = os.path.join(self._ccache_dir, 'ccache')

        try:
            kinit_password(self._ipaadmin_principal,
                           self._ipaadmin_password,
                           self._ccache_name)
        except RuntimeError as e:
            raise RuntimeError("Kerberos authentication failed: {}".format(e))
        os.environ["KRB5CCNAME"] = self._ccache_name

    def _ldap_connect(self):
        """Create a connection to LDAP and bind to it.
        """
        try:
            # LDAPI
            self._conn = ipaldap.LDAPClient.from_realm(api.env.realm)
            self._conn.external_bind()
        except Exception:
            try:
                # LDAP + GSSAPI
                self._conn = ipaldap.LDAPClient.from_hostname_secure(
                    api.env.server
                )
                self._conn.gssapi_bind()
            except Exception as e:
                logger.error(f'Unable to bind to LDAP server {e}')

    def ipa_user_add(self, scim_user):
        """
        Add a new user

        :param scim_user: user object conforming to the SCIM User Schema
        """

        self._ipa_connect()
        result = api.Command['user_add'](
            uid=scim_user.obj.username,
            givenname=scim_user.obj.first_name,
            sn=scim_user.obj.last_name,
            mail=scim_user.obj.email
            )
        logger.info(f'ipa user_add result {result}')

    def ipa_user_del(self, scim_user):
        """
        Delete ipa user

        :param scim_user: user object conforming to the SCIM User Schema
        :raises IPANotFoundException: if no user matching the username exists
        """
        self._ipa_connect()
        try:
            result = api.Command['user_del'](
                uid=scim_user.obj.username
                )
        except Exception as e:
            raise IPANotFoundException(
                "User {} not found".format(scim_user.obj.username)
                )
        logger.info(f'ipa: user_del result {result}')

    def ipa_user_mod(self, scim_user):
        """
        Modify ipa user

        :param scim_user: user object conforming to the SCIM User Schema
        :raises IPANotFoundException: if no user matching the username exists
        """
        self._ipa_connect()
        try:
            result = api.Command['user_mod'](
                scim_user.obj.username,
                givenname=scim_user.obj.first_name,
                sn=scim_user.obj.last_name,
                mail=scim_user.obj.email
                )
        except EmptyModlist as e:
            logger.debug("No modification for user {}".format(
                scim_user.obj.username))
            return
        except Exception as e:
            raise IPANotFoundException(
                "User {} not found".format(scim_user.obj.username)
                )
        logger.info(f'ipa: user_mod result {result}')


def IPA():
    if _IPA._instance is None:
        _IPA._instance = _IPA()
    return _IPA._instance
