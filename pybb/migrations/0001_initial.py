
from south.db import db
from django.db import models
from pybb.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Post'
        db.create_table('pybb_post', (
            ('id', orm['pybb.Post:id']),
            ('topic', orm['pybb.Post:topic']),
            ('user', orm['pybb.Post:user']),
            ('created', orm['pybb.Post:created']),
            ('updated', orm['pybb.Post:updated']),
            ('markup', orm['pybb.Post:markup']),
            ('body', orm['pybb.Post:body']),
            ('body_html', orm['pybb.Post:body_html']),
            ('body_text', orm['pybb.Post:body_text']),
            ('user_ip', orm['pybb.Post:user_ip']),
        ))
        db.send_create_signal('pybb', ['Post'])
        
        # Adding model 'Category'
        db.create_table('pybb_category', (
            ('id', orm['pybb.Category:id']),
            ('name', orm['pybb.Category:name']),
            ('position', orm['pybb.Category:position']),
        ))
        db.send_create_signal('pybb', ['Category'])
        
        # Adding model 'Forum'
        db.create_table('pybb_forum', (
            ('id', orm['pybb.Forum:id']),
            ('category', orm['pybb.Forum:category']),
            ('name', orm['pybb.Forum:name']),
            ('position', orm['pybb.Forum:position']),
            ('description', orm['pybb.Forum:description']),
            ('updated', orm['pybb.Forum:updated']),
            ('post_count', orm['pybb.Forum:post_count']),
            ('topic_count', orm['pybb.Forum:topic_count']),
        ))
        db.send_create_signal('pybb', ['Forum'])
        
        # Adding model 'Profile'
        db.create_table('pybb_profile', (
            ('id', orm['pybb.Profile:id']),
            ('user', orm['pybb.Profile:user']),
            ('signature', orm['pybb.Profile:signature']),
            ('signature_html', orm['pybb.Profile:signature_html']),
            ('time_zone', orm['pybb.Profile:time_zone']),
            ('language', orm['pybb.Profile:language']),
            ('avatar', orm['pybb.Profile:avatar']),
            ('show_signatures', orm['pybb.Profile:show_signatures']),
            ('markup', orm['pybb.Profile:markup']),
            ('ban_status', orm['pybb.Profile:ban_status']),
            ('ban_till', orm['pybb.Profile:ban_till']),
            ('post_count', orm['pybb.Profile:post_count']),
        ))
        db.send_create_signal('pybb', ['Profile'])
        
        # Adding model 'Attachment'
        db.create_table('pybb_attachment', (
            ('id', orm['pybb.Attachment:id']),
            ('post', orm['pybb.Attachment:post']),
            ('size', orm['pybb.Attachment:size']),
            ('content_type', orm['pybb.Attachment:content_type']),
            ('path', orm['pybb.Attachment:path']),
            ('name', orm['pybb.Attachment:name']),
            ('hash', orm['pybb.Attachment:hash']),
        ))
        db.send_create_signal('pybb', ['Attachment'])
        
        # Adding model 'ReadTracking'
        db.create_table('pybb_readtracking', (
            ('id', orm['pybb.ReadTracking:id']),
            ('user', orm['pybb.ReadTracking:user']),
            ('topics', orm['pybb.ReadTracking:topics']),
            ('last_read', orm['pybb.ReadTracking:last_read']),
        ))
        db.send_create_signal('pybb', ['ReadTracking'])
        
        # Adding model 'Topic'
        db.create_table('pybb_topic', (
            ('id', orm['pybb.Topic:id']),
            ('forum', orm['pybb.Topic:forum']),
            ('name', orm['pybb.Topic:name']),
            ('created', orm['pybb.Topic:created']),
            ('updated', orm['pybb.Topic:updated']),
            ('user', orm['pybb.Topic:user']),
            ('views', orm['pybb.Topic:views']),
            ('sticky', orm['pybb.Topic:sticky']),
            ('closed', orm['pybb.Topic:closed']),
            ('post_count', orm['pybb.Topic:post_count']),
        ))
        db.send_create_signal('pybb', ['Topic'])
        
        # Adding ManyToManyField 'Topic.subscribers'
        db.create_table('pybb_topic_subscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('topic', models.ForeignKey(orm.Topic, null=False)),
            ('user', models.ForeignKey(orm['auth.User'], null=False))
        ))
        
        # Adding ManyToManyField 'Forum.moderators'
        db.create_table('pybb_forum_moderators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('forum', models.ForeignKey(orm.Forum, null=False)),
            ('user', models.ForeignKey(orm['auth.User'], null=False))
        ))
        
    
    
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
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['auth.User']"}),
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
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'related_name': "'pybb_profile'", 'unique': 'True'})
        },
        'pybb.readtracking': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_read': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'topics': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'to': "orm['auth.User']"})
        },
        'pybb.topic': {
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics'", 'to': "orm['pybb.Forum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'views': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'})
        }
    }
    
    complete_apps = ['pybb']
