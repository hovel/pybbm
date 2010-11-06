from datetime import datetime

def update_read_tracking(topic, user):
    tracking = user.readtracking

    # if last_read > last_read - don't check topics
    if tracking.last_read and tracking.last_read > (topic.last_post.updated or
                                                    topic.last_post.created):
        return

    if isinstance(tracking.topics, dict):
        # clear topics if len > 5Kb and set last_read to current time
        if len(tracking.topics) > 5120:
            tracking.topics = None
            tracking.last_read = datetime.now()
            tracking.save()
        # update topics if new post exists or cache entry is empty
        if topic.last_post.pk > tracking.topics.get(str(topic.pk), 0):
            tracking.topics[str(topic.pk)] = topic.last_post.pk
            tracking.save()
    else:
        # initialize topic tracking dict
        tracking.topics = {topic.pk: topic.last_post.pk}
        tracking.save()
