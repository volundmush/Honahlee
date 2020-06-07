from tortoise.models import Model
from tortoise import fields


class Account(Model):
    uuid = fields.UUIDField(null=False, unique=True)
    name = fields.CharField(max_length=255)
    name_ci = fields.CharField(max_length=255, unique=True)
    password = fields.TextField(null=True)
    email = fields.CharField(max_length=320)
    email_ci = fields.CharField(max_length=320, unique=True)
    date_created = fields.DatetimeField(null=False)
    date_lockout = fields.DatetimeField(null=True)
    date_banned_until = fields.DatetimeField(null=True)
    date_last_login = fields.DatetimeField(null=True)
    date_last_logout = fields.DatetimeField(null=True)
    total_playtime = fields.BigIntField(null=False, default=0)
    enabled = fields.BooleanField(default=True, null=False)
    admin_level = fields.TimeDeltaField(default=0, null=False)


class Game(Model):
    owner = fields.ForeignKeyField('honahlee.Account', related_name='games')
    name = fields.CharField(max_length=255)
    name_ci = fields.CharField(max_length=255, unique=True)

    class Meta:
        unique_together = (('owner', 'name_ci'),)
