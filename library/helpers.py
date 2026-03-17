from typing import Any

from django.db.models import Model


def bulk_sync(
        objects: list[dict[str, Any]],
        parent_field: str,
        parent_instance: Model,
        model_to_sync: type[Model],
        fields_to_resolve: dict[str, type[Model]],
        fields_to_update: list[str]
):
    to_delete_ids: list[int] = list(
        model_to_sync.objects.filter(**{parent_field: parent_instance}).values_list("id", flat=True)
    )
    to_create: list[Model] = []
    to_update: list[Model] = []
    for object_to_sync in objects:
        if object_id := object_to_sync.get("id"):
            if object_id in to_delete_ids:
                to_delete_ids.remove(object_id)

        object_to_sync[parent_field] = parent_instance
        for field_name, field_model in fields_to_resolve.items():
            object_to_sync[field_name] = field_model.objects.get(pk=object_to_sync[field_name])

        instance = model_to_sync()
        for field_name, value in object_to_sync.items():
            setattr(instance, field_name, value)

        if object_id:
            to_update.append(instance)
        else:
            to_create.append(instance)

    model_to_sync.objects.filter(id__in=to_delete_ids).delete()
    model_to_sync.objects.bulk_update(to_update, fields_to_update)
    model_to_sync.objects.bulk_create(to_create)
