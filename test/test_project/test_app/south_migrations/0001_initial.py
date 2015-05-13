# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from pybb.compat import get_image_field_full_name, get_user_model_path, get_user_frozen_models


AUTH_USER = get_user_model_path()


class Migration(SchemaMigration):

    def forwards(self, orm):
        if AUTH_USER == 'test_app.CustomUser':
            # Adding model 'CustomUser'
            db.create_table(u'test_app_customuser', (
                (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
                ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
                ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
                ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
                ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
                ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
                ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ))
            db.send_create_signal(u'test_app', ['CustomUser'])

            # Adding M2M table for field groups on 'CustomUser'
            m2m_table_name = db.shorten_name(u'test_app_customuser_groups')
            db.create_table(m2m_table_name, (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('customuser', models.ForeignKey(orm[u'test_app.customuser'], null=False)),
                ('group', models.ForeignKey(orm[u'auth.group'], null=False))
            ))
            db.create_unique(m2m_table_name, ['customuser_id', 'group_id'])

            # Adding M2M table for field user_permissions on 'CustomUser'
            m2m_table_name = db.shorten_name(u'test_app_customuser_user_permissions')
            db.create_table(m2m_table_name, (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('customuser', models.ForeignKey(orm[u'test_app.customuser'], null=False)),
                ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
            ))
            db.create_unique(m2m_table_name, ['customuser_id', 'permission_id'])

        # Adding model 'CustomProfile'
        db.create_table(u'test_app_customprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('signature', self.gf('django.db.models.fields.TextField')(max_length=1024, blank=True)),
            ('signature_html', self.gf('django.db.models.fields.TextField')(max_length=1054, blank=True)),
            ('time_zone', self.gf('django.db.models.fields.FloatField')(default=3.0)),
            ('language', self.gf('django.db.models.fields.CharField')(default='en-us', max_length=10, blank=True)),
            ('show_signatures', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('avatar', self.gf(get_image_field_full_name())(max_length=100, null=True, blank=True)),
            ('autosubscribe', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name=u'pybb_customprofile', unique=True, to=orm[AUTH_USER])),
        ))
        db.send_create_signal(u'test_app', ['CustomProfile'])


    def backwards(self, orm):
        if AUTH_USER == 'test_app.CustomUser':
            # Deleting model 'CustomUser'
            db.delete_table(u'test_app_customuser')

            # Removing M2M table for field groups on 'CustomUser'
            db.delete_table(db.shorten_name(u'test_app_customuser_groups'))

            # Removing M2M table for field user_permissions on 'CustomUser'
            db.delete_table(db.shorten_name(u'test_app_customuser_user_permissions'))

        # Deleting model 'CustomProfile'
        db.delete_table(u'test_app_customprofile')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'test_app.customprofile': {
            'Meta': {'object_name': 'CustomProfile'},
            'autosubscribe': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'avatar': (get_image_field_full_name(), [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en-us'", 'max_length': '10', 'blank': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'show_signatures': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'blank': 'True'}),
            'signature_html': ('django.db.models.fields.TextField', [], {'max_length': '1054', 'blank': 'True'}),
            'time_zone': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'pybb_customprofile'", 'unique': 'True', 'to': u"orm['%s']" % AUTH_USER})
        },

    }

    if AUTH_USER == 'test_app.CustomUser':
        models[u'test_app.customuser'] = {
            'Meta': {'object_name': 'CustomUser'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    else:
        models.update(get_user_frozen_models(AUTH_USER))
    complete_apps = ['test_app']