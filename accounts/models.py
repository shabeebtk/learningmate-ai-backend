from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from cloudinary.models import CloudinaryField

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        return self.create_user(email, password, **extra_fields)
    
    

class MyUsers(AbstractUser):
    username = models.CharField(max_length=100, unique=True, null=False, blank=False)
    email = models.EmailField(max_length=100, unique=True)
    is_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()
    
    groups = models.ManyToManyField(
        Group,
        related_name='myuser_set',  # Changed related_name to avoid clash
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='myuser_permissions',  # Changed related_name to avoid clash
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    @property
    def profile_name(self):
        """Return the name from profile if exists, else fallback to username"""
        return getattr(self.profile, 'name', self.username)

    def __str__(self):
        return self.email
    

def profile_img_upload_to(instance, filename):
    return f'users/profile/{instance.user.id}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(MyUsers, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    profile_img = CloudinaryField('image', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    
