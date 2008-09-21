from django.contrib.syndication.feeds import Feed
from django.utils.feedgenerator import Atom1Feed

from pybb.models import Post

class LastPosts(Feed):
    feed_type = Atom1Feed
    title = 'Latest posts on forum'
    description = 'Latest posts on forum'
    link = 'adsf'
    title_template = 'pybb/feeds/posts_title.html'
    description_template = 'pybb/feeds/posts_description.html'

    def items(self):
        return Post.objects.order_by('-created')[:15]
