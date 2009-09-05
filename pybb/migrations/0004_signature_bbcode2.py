
from south.db import db
from django.db import models
from pybb.models import *

class Migration:
    
    def forwards(self, orm):
        [profile.save() for profile in Profile.objects.all()]
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Profile.signature_html'
        #db.delete_column('pybb_profile', 'signature_html')
        pass
        
    
    
    #complete_apps = ['pybb']
