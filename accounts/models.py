from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, email, password):
        if not username:
            raise ValueError('please enter username')
        if not email:
            raise ValueError('please enter email')

        user = self.model(username=username, email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_admin = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)

    password_1 = models.CharField(max_length=30)
    password_2 = models.CharField(max_length=30)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=60, blank=True, null=True)
    birthdate = models.DateTimeField(blank=True, null=True)

    role = models.CharField(
        max_length=50,
        choices=[
            ('doctor', 'doctor'),
            ('expert', 'expert'),
            ('student', 'student'),
            ('researcher', 'researcher'),
            ('others', 'others')
        ],
        default='student',
        blank=True,
        null=True
    )

    field_of_study = models.CharField(max_length=50,
                                      choices=[
                                          ('Pathology', 'pathology'),
                                          ('Histopathology', 'histopathology'),
                                          ('Oncology', 'Oncology'),
                                          ('Hematology', 'Hematology'),
                                          ('Neurology', 'Neurology'),
                                          ('Pulmonology', 'Pulmonology'),
                                          ('Medicine researches', 'Medicine researches'),
                                          ('Genetic', 'Genetic'),
                                          ('Computer science', 'AI'),
                                          ('others', 'others')
                                      ],
                                      default='pathology',
                                      blank=True,
                                      null=True)

    academy = models.CharField(max_length=50,
                               help_text='school, college, hospital, ...',
                               blank=True,
                               null=True)

    def __str__(self):
        return f'{self.user.username} profile:'

