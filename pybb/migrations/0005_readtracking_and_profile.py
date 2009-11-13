
from south.db import db
from django.db import models
from pybb.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'ReadTracking'
        db.create_table('pybb_readtracking', (
            ('id', orm['pybb.readtracking:id']),
            ('user', orm['pybb.readtracking:user']),
            ('topics', orm['pybb.readtracking:topics']),
            ('last_read', orm['pybb.readtracking:last_read']),
        ))
        db.send_create_signal('pybb', ['ReadTracking'])
        
        # Deleting field 'Profile.msn'
        db.delete_column('pybb_profile', 'msn')
        
        # Deleting field 'Profile.aim'
        db.delete_column('pybb_profile', 'aim')
        
        # Deleting field 'Profile.jabber'
        db.delete_column('pybb_profile', 'jabber')
        
        # Deleting field 'Profile.location'
        db.delete_column('pybb_profile', 'location')
        
        # Deleting field 'Profile.yahoo'
        db.delete_column('pybb_profile', 'yahoo')
        
        # Deleting field 'Profile.site'
        db.delete_column('pybb_profile', 'site')
        
        # Deleting field 'Profile.icq'
        db.delete_column('pybb_profile', 'icq')
        
        # Deleting model 'read'
        db.delete_table('pybb_read')
        
        # Changing field 'Profile.language'
        # (to signature: django.db.models.fields.CharField(max_length=10, blank=True))
        db.alter_column('pybb_profile', 'language', orm['pybb.profile:language'])
        
        # Changing field 'Profile.signature_html'
        # (to signature: django.db.models.fields.TextField(max_length=1054, blank=True))
        db.alter_column('pybb_profile', 'signature_html', orm['pybb.profile:signature_html'])
        
        # Changing field 'Profile.signature'
        # (to signature: django.db.models.fields.TextField(max_length=1024, blank=True))
        db.alter_column('pybb_profile', 'signature', orm['pybb.profile:signature'])
        
        # Changing field 'Profile.avatar'
        # (to signature: django.db.models.fields.files.ImageField(max_length=100, blank=True))
        db.alter_column('pybb_profile', 'avatar', orm['pybb.profile:avatar'])
        
        # Changing field 'Forum.description'
        # (to signature: django.db.models.fields.TextField(blank=True))
        db.alter_column('pybb_forum', 'description', orm['pybb.forum:description'])
        
        # Changing field 'Attachment.hash'
        # (to signature: django.db.models.fields.CharField(db_index=True, max_length=40, blank=True))
        db.alter_column('pybb_attachment', 'hash', orm['pybb.attachment:hash'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'ReadTracking'
        db.delete_table('pybb_readtracking')
        
        # Adding field 'Profile.msn'
        db.add_column('pybb_profile', 'msn', orm['pybb.profile:msn'])
        
        # Adding field 'Profile.aim'
        db.add_column('pybb_profile', 'aim', orm['pybb.profile:aim'])
        
        # Adding field 'Profile.jabber'
        db.add_column('pybb_profile', 'jabber', orm['pybb.profile:jabber'])
        
        # Adding field 'Profile.location'
        db.add_column('pybb_profile', 'location', orm['pybb.profile:location'])
        
        # Adding field 'Profile.yahoo'
        db.add_column('pybb_profile', 'yahoo', orm['pybb.profile:yahoo'])
        
        # Adding field 'Profile.site'
        db.add_column('pybb_profile', 'site', orm['pybb.profile:site'])
        
        # Adding field 'Profile.icq'
        db.add_column('pybb_profile', 'icq', orm['pybb.profile:icq'])
        
        # Adding model 'read'
        db.create_table('pybb_read', (
            ('topic', orm['pybb.profile:topic']),
            ('user', orm['pybb.profile:user']),
            ('id', orm['pybb.profile:id']),
            ('time', orm['pybb.profile:time']),
        ))
        db.send_create_signal('pybb', ['read'])
        
        # Changing field 'Profile.language'
        # (to signature: django.db.models.fields.CharField(default='', max_length=10, blank=True))
        db.alter_column('pybb_profile', 'language', orm['pybb.profile:language'])
        
        # Changing field 'Profile.signature_html'
        # (to signature: django.db.models.fields.TextField(default='', max_length=1054, blank=True))
        db.alter_column('pybb_profile', 'signature_html', orm['pybb.profile:signature_html'])
        
        # Changing field 'Profile.signature'
        # (to signature: django.db.models.fields.TextField(default='', max_length=1024, blank=True))
        db.alter_column('pybb_profile', 'signature', orm['pybb.profile:signature'])
        
        # Changing field 'Profile.avatar'
        # (to signature: ThumbnailField(_('Avatar'), default='', blank=True, size=(settings.PYBB_AVATAR_WIDTH, settings.PYBB_AVATAR_HEIGHT)))
        db.alter_column('pybb_profile', 'avatar', orm['pybb.profile:avatar'])
        
        # Changing field 'Forum.description'
        # (to signature: django.db.models.fields.TextField(default='', blank=True))
        db.alter_column('pybb_forum', 'description', orm['pybb.forum:description'])
        
        # Changing field 'Attachment.hash'
        # (to signature: django.db.models.fields.CharField(default='', max_length=40, blank=True, db_index=True))
        db.alter_column('pybb_attachment', 'hash', orm['pybb.attachment:hash'])
        
    
    
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
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
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
            'show_signatures': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'blank': 'True'}),
            'signature_html': ('django.db.models.fields.TextField', [], {'max_length': '1054', 'blank': 'True'}),
            'time_zone': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'user': ('AutoOneToOneField', ["orm['auth.User']"], {'related_name': "'pybb_profile'"})
        },
        'pybb.readtracking': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_read': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'topics': ('JSONField', [], {'null': 'True'}),
            'user': ('AutoOneToOneField', ["orm['auth.User']"], {})
        },
        'pybb.topic': {
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pybb.Forum']"}),
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
