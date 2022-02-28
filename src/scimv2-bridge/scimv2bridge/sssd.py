import dbus

DBUS_SSSD_NAME = 'org.freedesktop.sssd.infopipe'
DBUS_PROPERTY_IF = 'org.freedesktop.DBus.Properties'
DBUS_SSSD_USERS_PATH = '/org/freedesktop/sssd/infopipe/Users'
DBUS_SSSD_USERS_IF = 'org.freedesktop.sssd.infopipe.Users'
DBUS_SSSD_USER_IF = 'org.freedesktop.sssd.infopipe.Users.User'

class SSSDNotFoundException(Exception):
    pass

class _SSSD:
    sssd_to_model = {
        'givenname': 'first_name',
        'sn': 'last_name',
        'mail': 'email'}

    _instance = None

    def __init__(self):
        try:
            self._bus = dbus.SystemBus()
            self._users_obj = self._bus.get_object(
                DBUS_SSSD_NAME, DBUS_SSSD_USERS_PATH)
            self._users_iface = dbus.Interface(
                self._users_obj, DBUS_SSSD_USERS_IF)
        except dbus.DBusException as e:
            # TBD: add some logging
            raise e

    def _get_user_from_path(self, user_path):
        """
        Returns a dict representation of the user

        user_path is the DBus path to the user object
        """
        user_obj= self._bus.get_object(DBUS_SSSD_NAME, user_path)
        user_iface = dbus.Interface(user_obj, DBUS_PROPERTY_IF)
        name = user_iface.Get(DBUS_SSSD_USER_IF, "name")
        userdict = {'scim_username': str(name)}
        userdict['scim_id'] = int(user_iface.Get(DBUS_SSSD_USER_IF, "uidNumber"))
        extra_attrs = user_iface.Get(DBUS_SSSD_USER_IF, "extraAttributes")
        for (sssd_attr, scim_attr) in self.sssd_to_model.items():
            val = extra_attrs.get(sssd_attr)
            if val:
                userdict[scim_attr] = str(val[0])
        return userdict

    def find_user_by_name(self, username):
        """
        Returns a dict representation of the user
        """
        try:
            user_path = self._users_iface.FindByName(username)
        except dbus.exceptions.DBusException:
            raise SSSDNotFoundException()

        return self._get_user_from_path(user_path)

    def find_user_by_id(self, id):
        """
        Returns a dict representation of the user
        """
        try:
            user_path = self._users_iface.FindByID(id)
        except dbus.exceptions.DBusException:
            raise SSSDNotFoundException()

        return self._get_user_from_path(user_path)


def SSSD():
    if _SSSD._instance is None:
        _SSSD._instance = _SSSD()
    return _SSSD._instance
