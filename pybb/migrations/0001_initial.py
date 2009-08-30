
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
        ))
        db.send_create_signal('pybb', ['Forum'])
        
        # Adding model 'Profile'
        db.create_table('pybb_profile', (
            ('id', orm['pybb.Profile:id']),
            ('user', orm['pybb.Profile:user']),
            ('site', orm['pybb.Profile:site']),
            ('jabber', orm['pybb.Profile:jabber']),
            ('icq', orm['pybb.Profile:icq']),
            ('msn', orm['pybb.Profile:msn']),
            ('aim', orm['pybb.Profile:aim']),
            ('yahoo', orm['pybb.Profile:yahoo']),
            ('location', orm['pybb.Profile:location']),
            ('signature', orm['pybb.Profile:signature']),
            ('time_zone', orm['pybb.Profile:time_zone']),
            ('language', orm['pybb.Profile:language']),
            ('avatar', orm['pybb.Profile:avatar']),
            ('show_signatures', orm['pybb.Profile:show_signatures']),
            ('markup', orm['pybb.Profile:markup']),
        ))
        db.send_create_signal('pybb', ['Profile'])
        
        # Adding model 'PrivateMessage'
        db.create_table('pybb_privatemessage', (
            ('id', orm['pybb.PrivateMessage:id']),
            ('thread', orm['pybb.PrivateMessage:thread']),
            ('src_user', orm['pybb.PrivateMessage:src_user']),
            ('dst_user', orm['pybb.PrivateMessage:dst_user']),
            ('created', orm['pybb.PrivateMessage:created']),
            ('markup', orm['pybb.PrivateMessage:markup']),
            ('subject', orm['pybb.PrivateMessage:subject']),
            ('body', orm['pybb.PrivateMessage:body']),
            ('body_html', orm['pybb.PrivateMessage:body_html']),
            ('body_text', orm['pybb.PrivateMessage:body_text']),
        ))
        db.send_create_signal('pybb', ['PrivateMessage'])
        
        # Adding model 'MessageBox'
        db.create_table('pybb_messagebox', (
            ('id', orm['pybb.MessageBox:id']),
            ('message', orm['pybb.MessageBox:message']),
            ('user', orm['pybb.MessageBox:user']),
            ('box', orm['pybb.MessageBox:box']),
            ('head', orm['pybb.MessageBox:head']),
            ('read', orm['pybb.MessageBox:read']),
            ('thread_read', orm['pybb.MessageBox:thread_read']),
            ('message_count', orm['pybb.MessageBox:message_count']),
        ))
        db.send_create_signal('pybb', ['MessageBox'])
        
        # Adding model 'Read'
        db.create_table('pybb_read', (
            ('id', orm['pybb.Read:id']),
            ('user', orm['pybb.Read:user']),
            ('topic', orm['pybb.Read:topic']),
            ('time', orm['pybb.Read:time']),
        ))
        db.send_create_signal('pybb', ['Read'])
        
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
        
        # Creating unique_together for [user, topic] on Read.
        db.create_unique('pybb_read', ['user_id', 'topic_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Post'
        db.delete_table('pybb_post')
        
        # Deleting model 'Attachment'
        db.delete_table('pybb_attachment')
        
        # Deleting model 'Category'
        db.delete_table('pybb_category')
        
        # Deleting model 'Forum'
        db.delete_table('pybb_forum')
        
        # Deleting model 'Profile'
        db.delete_table('pybb_profile')
        
        # Deleting model 'PrivateMessage'
        db.delete_table('pybb_privatemessage')
        
        # Deleting model 'MessageBox'
        db.delete_table('pybb_messagebox')
        
        # Deleting model 'Read'
        db.delete_table('pybb_read')
        
        # Deleting model 'Topic'
        db.delete_table('pybb_topic')
        
        # Dropping ManyToManyField 'Topic.subscribers'
        db.delete_table('pybb_topic_subscribers')
        
        # Dropping ManyToManyField 'Forum.moderators'
        db.delete_table('pybb_forum_moderators')
        
        # Deleting unique_together for [user, topic] on Read.
        db.delete_unique('pybb_read', ['user_id', 'topic_id'])
        
    
    
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
            'hash': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '40', 'db_index': 'True', 'blank': 'True'}),
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
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        'pybb.messagebox': {
            'box': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'head': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pybb.PrivateMessage']"}),
            'message_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'thread_read': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
            'user_ip': ('django.db.models.fields.IPAddressField', [], {'default': "''", 'max_length': '15', 'blank': 'True'})
        },
        'pybb.privatemessage': {
            'body': ('django.db.models.fields.TextField', [], {}),
            'body_html': ('django.db.models.fields.TextField', [], {}),
            'body_text': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'dst_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pm_recipient'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.CharField', [], {'default': "'bbcode'", 'max_length': '15'}),
            'src_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pm_author'", 'to': "orm['auth.User']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pybb.PrivateMessage']", 'null': 'True', 'blank': 'True'}),
            'user_box': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']"})
        },
        'pybb.profile': {
            'aim': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80', 'blank': 'True'}),
            'avatar': ('ExtendedImageField', ["_('Avatar')"], {'default': "''", 'width': 'pybb_settings.AVATAR_WIDTH', 'height': 'pybb_settings.AVATAR_HEIGHT', 'blank': 'True'}),
            'icq': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '12', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jabber': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30', 'blank': 'True'}),
            'markup': ('django.db.models.fields.CharField', [], {'default': "'bbcode'", 'max_length': '15'}),
            'msn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80', 'blank': 'True'}),
            'show_signatures': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'time_zone': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'user': ('AutoOneToOneField', ["orm['auth.User']"], {'related_name': "'pybb_profile'"}),
            'yahoo': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80', 'blank': 'True'})
        },
        'pybb.read': {
            'Meta': {'unique_together': "(['user', 'topic'],)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pybb.Topic']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'views': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'})
        }
    }
    
    complete_apps = ['pybb']
