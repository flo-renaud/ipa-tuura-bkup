from django_scim.filters import UserFilterQuery, GroupFilterQuery

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

class SCIMGroupFilterQuery(GroupFilterQuery):
    attr_map = {
        ('displayName', None, None): 'scim_display_name'
    }
