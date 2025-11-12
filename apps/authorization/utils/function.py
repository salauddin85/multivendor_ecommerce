from django.core.cache import cache

def clear_user_permissions_cache():
    
    try:
        cache.delete_pattern("*user_permissions_*")
        print("Deleted all user permission caches using delete_pattern()")
    except NotImplementedError:
        print("delete_pattern not supported for this cache backend")