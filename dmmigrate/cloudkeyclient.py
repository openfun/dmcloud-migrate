import cloudkey


class Client(object):

    def __init__(self, dmcloud_user_id, dmcloud_api_key):
        self.client = cloudkey.CloudKey(dmcloud_user_id, dmcloud_api_key)
        self._organisation_id = None

    @property
    def organisation_id(self):
        if self._organisation_id is None:
            self._organisation_id = self.client.organisation.get()["id"]
        return self._organisation_id

    def iter_users(self):
        for user in iter_results(self.client.user.search, org_id=self.organisation_id, fields=["id", "username"]):
            yield User(user["id"], user["username"])

    def act_as_user(self, user):
        self.client.act_as_user(user.user_id)

    def iter_media(self):
        for media in iter_results(self.client.media.search, fields=["id", "meta.title"]):
            yield Media(media["id"], media["meta"]['title'])

    def get_assets(self, media):
        return self.client.media.get_assets(media_id=media.media_id)


class User(object):

    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name


class Media(object):

    def __init__(self, media_id, title):
        self.media_id = media_id
        self.title = title


def iter_results(function, *args, **kwargs):
    has_more = True
    page = 1
    kwargs['per_page'] = 100
    while has_more:
        kwargs["page"] = page
        results = function(*args, **kwargs)
        has_more = results['has_more']
        page += 1
        for result in results['list']:
            yield result
