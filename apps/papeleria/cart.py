from decimal import Decimal

from apps.papeleria.models.articulos import Articulo

SESSION_CART_KEY = "papeleria_cart"


class PapeleriaCart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(SESSION_CART_KEY)
        if not cart:
            cart = self.session[SESSION_CART_KEY] = {}
        self.cart = cart

    def add(self, articulo_id: int, cantidad: int = 1):
        articulo_id = str(articulo_id)
        if articulo_id not in self.cart:
            self.cart[articulo_id] = {"cantidad": 0}
        self.cart[articulo_id]["cantidad"] += cantidad
        self.save()

    def update(self, articulo_id: int, cantidad: int):
        articulo_id = str(articulo_id)
        if cantidad <= 0:
            self.remove(articulo_id)
        else:
            if articulo_id in self.cart:
                self.cart[articulo_id]["cantidad"] = cantidad
                self.save()

    def remove(self, articulo_id: int):
        articulo_id = str(articulo_id)
        if articulo_id in self.cart:
            del self.cart[articulo_id]
            self.save()

    def clear(self):
        del self.session[SESSION_CART_KEY]
        self.save()

    def save(self):
        self.session.modified = True

    def get_items(self):
        """Retorna los ítems con el objeto Articulo real y subtotales"""
        articulo_ids = self.cart.keys()
        articulos = Articulo.objects.filter(id__in=articulo_ids)

        items = []
        total = Decimal("0.00")

        for articulo in articulos:
            item_data = self.cart[str(articulo.id)]
            cantidad = item_data["cantidad"]
            subtotal = articulo.importe * cantidad
            total += subtotal

            items.append({
                "articulo": articulo.to_dict(),
                "cantidad": cantidad,
                "subtotal": float(subtotal),
            })

        return items, float(total)
