from django.db.models import Sum
from ..models import Cart, CartItem





def merge_guest_cart_to_user_cart(request, user):
    """
    When user logs in:
    1. find guest cart by session_id
    2. merge into authenticated cart
    3. delete guest cart
    """

    session_id = request.session.session_key
    if not session_id:
        return  # No guest cart → nothing to merge

    try:
        guest_cart = Cart.objects.prefetch_related("items").get(session_id=session_id)
    except Cart.DoesNotExist:
        return  # No guest cart available

    # Authenticated user's cart
    user_cart, _ = Cart.objects.get_or_create(user=user)

    for item in guest_cart.items.all():

        # Check if same product+variant exists in user cart
        existing = CartItem.objects.filter(
            cart=user_cart,
            product=item.product,
            variant=item.variant
        ).first()

        if existing:
            # merge quantity
            new_qty = existing.quantity + item.quantity

            stock = item.variant.stock if item.variant else item.product.stock
            if new_qty > stock:
                new_qty = stock  

            existing.quantity = new_qty
            existing.subtotal = existing.price * new_qty
            existing.save()
        else:
            # move item to authenticated cart
            item.cart = user_cart
            item.save()

    # After merging → delete guest cart
    guest_cart.delete()

    # update total
    user_cart.total_amount = user_cart.items.aggregate(total=Sum("subtotal"))["total"] or 0
    user_cart.save()


# -------------------------------------------
def get_or_create_cart(request):
    """
    Return authenticated cart OR session-based guest cart
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    # unauthenticated → session cart
    session_id = request.session.session_key
    if not session_id:
        request.session.create()
        session_id = request.session.session_key

    cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart

