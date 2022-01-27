from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_scim.models import AbstractSCIMGroupMixin, AbstractSCIMUserMixin


class CustomUserManager(UserManager):
    def create_user(self, scim_username, email, password=None):
        """
        Create and save a User with the scim_username and password.
        """
        if not scim_username:
            raise ValueError(_('The scim_username must be set'))
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(scim_username=scim_username,
                          email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, scim_username, email, password=None):
        """
        Create and save a SuperUser with the given email and password.
        """
        user = self.create_user(scim_username, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractSCIMUserMixin, AbstractBaseUser):
    # Why override this? Can't we just use what the AbstractSCIMUser mixin
    # gives us? The USERNAME_FIELD needs to be "unique" and for flexibility, 
    # AbstractSCIMUser.scim_username is not unique by default.
    scim_username = models.CharField(
        _('SCIM Username'),
        max_length=254,
        null=True,
        blank=True,
        default=None,
        unique=True,
        help_text=_("A service provider's unique identifier for the user"),
    )

    first_name = models.CharField(
        _('First Name'),
        max_length=100,
    )

    last_name = models.CharField(
        _('Last Name'),
        max_length=100,
    )

    email = models.EmailField(
        _('Email'),
    )
    
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )


    scim_groups = models.ManyToManyField(
        'scimv2bridge.Group'
    )
    
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'scim_username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name

    def get_short_name(self):
        return self.first_name + (' ' + self.last_name[0] if self.last_name else '')
    
    @property
    def username(self):
        return self.scim_username

class Group(AbstractSCIMGroupMixin):
    pass



