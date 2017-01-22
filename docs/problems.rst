Known problems
==============

Using with a database that doest not support microseconds
---------------------------------------------------------

If you are using a database which does not support microseconds (MySQL for eg.), a forum can be
wrongly marked read. It can happens if a user who read the only unread topic from a forum in
the same time an other user create / update an other topic on the same forum.