from django.core.paginator import Paginator, Page


class SqlPage(Page):
    """
    Subclase de Page que calcula start_index y end_index
    basándose en la página solicitada sin hacer slicing sobre object_list.
    """
    def start_index(self):
        if self.paginator.count == 0:
            return 0
        return (self.number - 1) * self.paginator.per_page + 1

    def end_index(self):
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page


class SqlPaginator(Paginator):
    """
    Paginador personalizado para django-tables2 que utiliza el conteo total
    precalculado desde SQL y evita recortar nuevamente la lista obtenida por LIMIT/OFFSET.
    """
    def __init__(self, object_list, per_page, total_count=0, **kwargs):
        self._total_count = int(total_count)
        super().__init__(object_list, per_page, **kwargs)

    @property
    def count(self):
        return self._total_count

    def page(self, number):
        number = self.validate_number(number)
        return SqlPage(self.object_list, number, self)