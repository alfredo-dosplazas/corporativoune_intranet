from dal import autocomplete


class EmpresaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        pass
