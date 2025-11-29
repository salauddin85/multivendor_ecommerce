
# from decimal import Decimal
# from django.db import transaction
# from django.utils.crypto import get_random_string
# from apps.orders.models import Order, OrderItem, ShippingAddress
# from apps.products.models import Product, ProductVariant
# from apps.stores.models import Store
# from apps.authentication.models import CustomUser


# def _generate_order_number():
#     return f"ORD-{get_random_string(10).upper()}"


# @transaction.atomic
# def create_order_from_cart(user, cart_items, shipping_address, payment_method=None, customer_note=''):
#     """Create order(s) for a multi-vendor cart.
#     cart_items: list of dict {product, variant, quantity, store}
#     returns: parent_order (if multiple stores, parent with sub_orders), created_orders list
#     """
#     # Group items by store
#     store_groups = {}
#     for item in cart_items:
#         store_id = item['store'].id if isinstance(item['store'], Store) else item['store']
#         store_groups.setdefault(store_id, []).append(item)

#     created_orders = []
#     parent_order = None

#     for idx, (store_id, items) in enumerate(store_groups.items()):
#         store = Store.objects.get(id=store_id)
#         subtotal = Decimal('0.00')
#         for it in items:
#             price = Decimal(str(it.get('price', '0.00')))
#             qty = int(it.get('quantity', 1))
#             subtotal += price * qty

#         # basic shipping calculation (placeholder)
#         shipping_fee = Decimal('50.00') if subtotal < Decimal('1000.00') else Decimal('0.00')
#         tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
#         discount = Decimal('0.00')
#         total_amount = subtotal + shipping_fee + tax - discount

#         order = Order.objects.create(
#             order_number=_generate_order_number(),
#             user=user,
#             store=store,
#             parent=None,  
#             subtotal=subtotal,
#             shipping_fee=shipping_fee,
#             tax=tax,
#             discount=discount,
#             total_amount=total_amount,
#             payment_method=payment_method or '',
#             shipping_address=shipping_address,
#             customer_note=customer_note or '',
#         )

#         for it in items:
#             product = Product.objects.get(id=it['product'].id if hasattr(it['product'],'id') else it['product'])
#             variant = None
#             if it.get('variant'):
#                 variant = ProductVariant.objects.get(id=it['variant'].id if hasattr(it['variant'],'id') else it['variant'])
#             qty = int(it.get('quantity', 1))
#             price = Decimal(str(it.get('price', product.base_price)))
#             subtotal_item = price * qty
#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 variant=variant,
#                 store=store,
#                 product_name=product.title,
#                 variant_name=variant.variant_name if variant else '',
#                 quantity=qty,
#                 price=price,
#                 discount=Decimal('0.00'),
#                 subtotal=subtotal_item,
#             )
#             # reduce stock (simple decrement) - optional: check & raise if insufficient
#             if variant:
#                 variant.stock = max(0, variant.stock - qty)
#                 variant.save()
#             else:
#                 product.stock = max(0, product.stock - qty)
#                 product.save()

#         created_orders.append(order)

#     if len(created_orders) > 1:
#         parent_order = Order.objects.create(
#             order_number=_generate_order_number(),
#             user=user,
#             store=created_orders[0].store,  # parent store can be null or platform store
#             parent=None,
#             subtotal=sum([o.subtotal for o in created_orders]),
#             shipping_fee=sum([o.shipping_fee for o in created_orders]),
#             tax=sum([o.tax for o in created_orders]),
#             discount=sum([o.discount for o in created_orders]),
#             total_amount=sum([o.total_amount for o in created_orders]),
#         )
#         # attach child orders
#         for o in created_orders:
#             o.parent = parent_order
#             o.save()

#     # Return a simple payload
#     return parent_order or created_orders[0], created_orders

