from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["nom", "email", "sujet", "date", "lu"]
    list_editable = ["lu"]
    list_filter = ["lu"]
    search_fields = ["nom", "email", "sujet", "contenu"]
    readonly_fields = ["nom", "email", "sujet", "contenu", "date"]
    fields = ["nom", "email", "sujet", "contenu", "date", "lu"]
    actions = ["marquer_lu", "marquer_non_lu"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Marquer comme lu")
    def marquer_lu(self, request, queryset):
        queryset.update(lu=True)

    @admin.action(description="Marquer comme non lu")
    def marquer_non_lu(self, request, queryset):
        queryset.update(lu=False)
