from django.contrib import admin
from .models import CertificateType, Item, SubItem, CategoryGroup, Category, FieldType, ExtraField, LegalRequirements, BusinessProfile ,VehicleSpecs,UploadFilesSubItem
from django import forms
from .widgets import MarkdownWidget
from django.utils.html import format_html

@admin.register(CertificateType)
class CertificateTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description']
    search_fields = ['name']
    
@admin.register(UploadFilesSubItem)
class UploadFilesSubItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'subitem', 'file', 'expiry_date','certificate_type')  
    search_fields = ['subitem__numberPlate', 'certificate_type__name']
    list_filter = ['certificate_type']
    # search_fields = ('file',)  
    # list_filter = ('expiry_date',) 
    
class UploadFilesSubItemInline(admin.TabularInline):
    model = UploadFilesSubItem
    extra = 1  
    fields = ('file', 'expiry_date')  
    verbose_name_plural = "Item Files"

@admin.register(SubItem)
class SubItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'value', 'numberPlate')  
    search_fields = ('value', 'numberPlate')  
    list_filter = ('item',)  
    inlines = [UploadFilesSubItemInline]
    
    
class SubItemInline(admin.TabularInline):
    model = SubItem
    extra = 1  
    fields = ('value', 'numberPlate')
    inlines = [UploadFilesSubItemInline]
    
    
@admin.register(FieldType)
class FieldTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_tag']
    list_filter = ['name']
    search_fields = ['name']


@admin.register(CategoryGroup)
class CategoryGroupAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'icon_tag']
    search_fields = ['name']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category_group', 'price_unit','author']
    list_filter = ['category_group']
    search_fields = ['name', 'category_group__name']
    filter_horizontal = ['field_types', 'associated_categories', 'legal_requirements']

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'contract_text':
            kwargs['widget'] = MarkdownWidget()
        return super().formfield_for_dbfield(db_field, **kwargs)

admin.site.register(Category, CategoryAdmin)


class ExtraFieldInline(admin.TabularInline):
    model = ExtraField
    extra = 1


class SubItemInline(admin.TabularInline):
    model = SubItem
    extra = 1

# admin.site.register(License)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'price', 'category', 'owner', 'status']
    list_filter = ['category__category_group', 'status']
    search_fields = ['name', 'category__name', 'owner', 'status', 'category__category_group__name']
    inlines = [SubItemInline]

    def has_add_permission(self, request):
        return False

    def get_inlines(self, request, obj=None):
        if obj:
            inlines = [ExtraFieldInline]
            if obj.category.sub_item_type:
                inlines.append(SubItemInline)
            return inlines
        return []

# this is the LegalRequirements Form
class LicenseForm(forms.ModelForm):
    available_fields = [field.name for field in BusinessProfile._meta.get_fields()]

    requirements = forms.MultipleChoiceField(
        choices=[(field, field) for field in available_fields],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = LegalRequirements
        fields = '__all__'

    def clean_requirements(self):
        selected_fields = self.cleaned_data.get('requirements')
        invalid_fields = [field for field in selected_fields if field not in self.available_fields]
        if invalid_fields:
            raise forms.ValidationError(f"Invalid field names selected: {', '.join(invalid_fields)}")
        return selected_fields

class LicenseAdmin(admin.ModelAdmin):
    form = LicenseForm
    list_display = ['name', 'description', 'requirements']

admin.site.register(LegalRequirements, LicenseAdmin)

@admin.register(VehicleSpecs)
class VehicleSpecsAdmin(admin.ModelAdmin):
    list_display = ['id', 'make', 'model', 'model_year', 'categories', 'colored_status']
    list_filter = ['make', 'model', 'model_year', 'status', 'categories__name']
    search_fields = ['make', 'model', 'model_year', 'categories__name']
    autocomplete_fields = ['categories']
    actions = ['approve_vehicle_specs', 'reject_vehicle_specs']

    @admin.action(description="Approve selected VehicleSpecs")
    def approve_vehicle_specs(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description="Reject selected VehicleSpecs")
    def reject_vehicle_specs(self, request, queryset):
        queryset.update(status='rejected')

    def colored_status(self, obj):
        colors = {'approved':'green','pending':'orange','rejected':'red'}
        return format_html(
            '<span style="color:{};">{}</span>',
            colors.get(obj.status,'black'),
            obj.get_status_display()
        )
    colored_status.short_description = "Status"

