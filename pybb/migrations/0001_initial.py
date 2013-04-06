# encoding: utf-8
try:
    from django.contrib.auth import get_user_model
except ImportError:  # django < 1.5
    from django.contrib.auth.models import User
else:
    User = get_user_model()

from south.db import db
from django.db import models
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    
    def forwards(self, orm):

        # Adding model 'Post'
        db.create_table('pybb_post', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('body_html', self.gf('django.db.models.fields.TextField')()),
            ('body_text', self.gf('django.db.models.fields.TextField')()),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['pybb.Topic'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'posts', to=orm["%s.%s" % (User._meta.app_label, User._meta.object_name)])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('user_ip', self.gf('django.db.models.fields.IPAddressField')(default=u'0.0.0.0', max_length=15, blank=True)),
            ('markup', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal('pybb', ['Post'])

        # Adding model 'Category'
        db.create_table('pybb_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('position', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal('pybb', ['Category'])

        # Adding model 'Forum'
        db.create_table('pybb_forum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'forums', to=orm['pybb.Category'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('position', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('topic_count', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal('pybb', ['Forum'])

        # Adding model 'Profile'
        db.create_table('pybb_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('signature', self.gf('django.db.models.fields.TextField')(max_length=1024, blank=True)),
            ('signature_html', self.gf('django.db.models.fields.TextField')(max_length=1054, blank=True)),
            ('time_zone', self.gf('django.db.models.fields.FloatField')(default=3.0)),
            ('language', self.gf('django.db.models.fields.CharField')(default=u'en-us', max_length=10, blank=True)),
            ('show_signatures', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('avatar', self.gf('sorl.thumbnail.fields.ImageField')(max_length=100, null=True, blank=True)),
            ('user', self.gf('annoying.fields.AutoOneToOneField')(related_name=u'pybb_profile', unique=True, to=orm["%s.%s" % (User._meta.app_label, User._meta.object_name)])),
            ('markup', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('ban_status', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('ban_till', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('pybb', ['Profile'])

        # Adding model 'Attachment'
        db.create_table('pybb_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'attachments', to=orm['pybb.Post'])),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
            ('hash', self.gf('django.db.models.fields.CharField')(blank=True, default='', max_length=40, db_index=True)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('pybb', ['Attachment'])
        
        # Adding model 'ReadTracking'
        db.create_table('pybb_readtracking', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm["%s.%s" % (User._meta.app_label, User._meta.object_name)])),
            ('topics', self.gf('django.db.models.fields.TextField')(null=True)),
            ('last_read', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('pybb', ['ReadTracking'])

        # Adding model 'Topic'
        db.create_table('pybb_topic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('forum', self.gf('django.db.models.fields.related.ForeignKey')(related_name='topics', to=orm['pybb.Forum'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm["%s.%s" % (User._meta.app_label, User._meta.object_name)])),
            ('views', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('sticky', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal('pybb', ['Topic'])
        
        # Adding M2M table for field subscribers on 'Topic'
        db.create_table('pybb_topic_subscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('topic', models.ForeignKey(orm['pybb.topic'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('pybb_topic_subscribers', ['topic_id', 'user_id'])

        # Adding M2M table for field moderators on 'Forum'
        db.create_table('pybb_forum_moderators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('forum', models.ForeignKey(orm['pybb.forum'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('pybb_forum_moderators', ['forum_id', 'user_id'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Post'
        db.delete_table('pybb_post')
        
        # Deleting model 'Category'
        db.delete_table('pybb_category')
        
        # Deleting model 'Forum'
        db.delete_table('pybb_forum')
        
        # Deleting model 'Profile'
        db.delete_table('pybb_profile')
        
        # Deleting model 'Attachment'
        db.delete_table('pybb_attachment')
        
        # Deleting model 'ReadTracking'
        db.delete_table('pybb_readtracking')
        
        # Deleting model 'Topic'
        db.delete_table('pybb_topic')
        
        # Dropping ManyToManyField 'Topic.subscribers'
        db.delete_table('pybb_topic_subscribers')
        
        # Dropping ManyToManyField 'Forum.moderators'
        db.delete_table('pybb_forum_moderators')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pybb.attachment': {
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'hash': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['pybb.Post']"}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        },
        'pybb.category': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'pybb.forum': {
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'forums'", 'to': "orm['pybb.Category']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['%s.%s']"% (User._meta.app_label, User._meta.object_name), 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'topic_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'pybb.post': {
            'body': ('django.db.models.fields.TextField', [], {}),
            'body_html': ('django.db.models.fields.TextField', [], {}),
            'body_text': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.CharField', [], {'default': "'bbcode'", 'max_length': '15'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['pybb.Topic']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['%s.%s']"% (User._meta.app_label, User._meta.object_name)}),
            'user_ip': ('django.db.models.fields.IPAddressField', [], {'default': "'0.0.0.0'", 'max_length': '15', 'blank': 'True'})
        },
        'pybb.profile': {
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'ban_status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'ban_till': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'markup': ('django.db.models.fields.CharField', [], {'default': "'bbcode'", 'max_length': '15'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'show_signatures': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'blank': 'True'}),
            'signature_html': ('django.db.models.fields.TextField', [], {'max_length': '1054', 'blank': 'True'}),
            'time_zone': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['%s.%s']"% (User._meta.app_label, User._meta.object_name), 'related_name': "'pybb_profile'", 'unique': 'True'})
        },
        'pybb.readtracking': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_read': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'topics': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'to': "orm['%s.%s']"% (User._meta.app_label, User._meta.object_name)})
        },
        'pybb.topic': {
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics'", 'to': "orm['pybb.Forum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['%s.%s']"% (User._meta.app_label, User._meta.object_name), 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s.%s']"% (User._meta.app_label, User._meta.object_name)}),
            'views': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'})
        }
    }
    
    complete_apps = ['pybb']
