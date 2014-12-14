Javascript functionality
========================

Pybb does not depend on any javascript code. But javascript can provide more rich user experience
when interacting with forum.

For enabling javascript features your installation should meet some requirements:

  * include in your templates link to `pybbjs.js` file, for example with ``{% static 'pybb/js/pybbjs.js' %}`` tag
  * to enable deleting posts via ajax, add to your delete link inline onclick handler
    with calling pybb_delete_post(url, post_id, confirm_text)
  * to enable quoting selected text in post, add in each post link with `quote-selected-link` class
  * to enable quoting full message via ajax, add in each post link with `quote-link` class and href
    attribute pointed to view that return text to quote
  * to enable insert in post body user's nickname by clicking with shift pressed, just wrap each post
    with tag with `post-row` class and place inside it nickname wrapped by tag with `post-username` class

All of this features enabled in standard templates shipped with pybbm app.