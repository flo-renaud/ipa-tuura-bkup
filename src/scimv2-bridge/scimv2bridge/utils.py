from django.db import NotSupportedError
from django_scim.filters import UserFilterQuery, GroupFilterQuery
from itertools import chain
from scimv2bridge.models import User
from scimv2bridge.sssd import SSSD, SSSDNotFoundException

class SCIMUserFilterQuery(UserFilterQuery):
    attr_map = {
        # attr, sub attr, uri
        ('userName', None, None): 'scim_username',
        ('name', 'familyName', None): 'last_name',
        ('familyName', None, None): 'last_name',
        ('name', 'givenName', None): 'first_name',
        ('givenName', None, None): 'first_name',
        ('active', None, None): 'is_active',
    }

    @classmethod
    def search(cls, filter_query, request=None):
        localresult = super(SCIMUserFilterQuery, cls).search(filter_query, request)
        if len(localresult) > 0:
            return localresult

        # The only supported search filters are equality filters
        items = filter_query.split(" ")
        if len(items) != 3:
            raise NotSupportedError('Support only exact search by username')

        (attr, op, value) = (items[0], items[1], items[2].strip('"'))
        if attr.lower() != "username":
            raise NotSupportedError('Support only search by username')
        if op.lower() != 'eq':
            raise NotSupportedError('Support only exact search')

        try:
            sssd_if = SSSD()
            user_dict = sssd_if.find_user_by_name(value)
        except SSSDNotFoundException:
            return localresult

        myuser = User()
        for (attr, value) in user_dict.items():
            setattr(myuser, attr, value)
        myuser.id = myuser.scim_id

        mylist = [myuser]
        return mylist


class SCIMGroupFilterQuery(GroupFilterQuery):
    attr_map = {
        ('displayName', None, None): 'scim_display_name'
    }
