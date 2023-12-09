from graphene import ResolveInfo


class DashboardLoaders:
    def __init__(self):
        pass


class WebsiteLoaders:
    def __init__(self):
        pass


class LoaderMiddleware:
    def resolve(self, next, root, info: ResolveInfo, **args):
        if info.context.path.startswith("/dashboard/"):
            info.context.loaders = DashboardLoaders()
        elif info.context.path.startswith("/storefront/"):
            info.context.loaders = WebsiteLoaders()

        return next(root, info, **args)
