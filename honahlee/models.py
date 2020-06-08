from tortoise.models import Model
from tortoise import fields


class Namespace(Model):
    name = fields.CharField(max_length=255, null=False, blank=False, unique=True)


class Host(Model):
    ip = fields.CharField(max_length=39)
    name = fields.TextField(null=True)


class ProtocolName(Model):
    name = fields.CharField(max_length=100, null=False, blank=False, unique=True)


class ServerName(Model):
    name = fields.CharField(max_length=100, null=False, blank=False, unique=True)


class EntityType(Model):
    name = fields.CharField(max_length=100, null=False, blank=False, unique=True)
    python_class = fields.CharField(max_length=255, null=False)


class Entity(Model):
    uuid = fields.UUIDField(null=False, unique=True)
    entity_type = fields.ForeignKeyField('honahlee.EntityType')
    date_created = fields.DatetimeField(null=False)


class NameComponent(Model):
    entity = fields.OneToOneField('honahlee.Entity', related_name='name_component', pk=True, on_delete=fields.CASCADE)
    name = fields.CharField(max_length=255, null=False, blank=False)


class AccountComponent(Model):
    entity = fields.OneToOneField('honahlee.Entity', related_name='account_component', pk=True,
                                  on_delete=fields.CASCADE)
    password = fields.TextField(null=True)
    email = fields.CharField(max_length=320)
    date_lockout = fields.DatetimeField(null=True)
    date_banned_until = fields.DatetimeField(null=True)
    date_last_login = fields.DatetimeField(null=True)
    date_last_logout = fields.DatetimeField(null=True)
    total_playtime = fields.TimeDeltaField(null=False)
    enabled = fields.BooleanField(default=True, null=False)
    admin_level = fields.SmallIntField(null=False)


class LoginRecord(Model):
    entity = fields.ForeignKeyField('honahlee.Entity', related_name='login_records', on_delete=fields.CASCADE)
    protocol = fields.ForeignKeyField('honahlee.ProtocolName')
    server = fields.ForeignKeyField('honahlee.ServerName')
    host = fields.ForeignKeyField('honahlee.Host')
    success = fields.BooleanField(null=False)
    date_created = fields.DatetimeField(null=False)


class IdentityComponent(Model):
    entity = fields.OneToOneField('honahlee.Entity', related_name='identity_component', on_delete=fields.CASCADE,
                                  pk=True)
    namespace = fields.ForeignKeyField('honahlee.Namespace', related_name='identities', on_delete=fields.RESTRICT)


class GameComponent(Model):
    entity = fields.OneToOneField('honahlee.Entity', related_name='game_component', on_delete=fields.CASCADE,
                                  pk=True)
    owner = fields.ForeignKeyField('honahlee.Entity', related_name='games')
    game_key = fields.CharField(max_length=255, null=False)

    class Meta:
        unique_together = (('owner', 'game_key'),)


class ACLPermission(Model):
    name = fields.CharField(max_length=50, null=False, unique=True, blank=False)


class ACLEntry(Model):
    # This Generic Foreign Key is the object being 'accessed'.
    resource = fields.ForeignKeyField('honahlee.Entity', related_name='acl_entries', on_delete=fields.CASCADE)
    identity = fields.ForeignKeyField('honahlee.Entity', related_name='acl_references', on_delete=fields.CASCADE)
    mode = fields.CharField(max_length=30, null=False, blank=True, default='')
    deny = fields.BooleanField(null=False, default=False)
    permissions = fields.ManyToManyField('honahlee.ACLPermission', related_name='entries')

    class Meta:
        unique_together = (('resource', 'identity', 'mode', 'deny'),)
        index_together = (('resource', 'deny'),)
