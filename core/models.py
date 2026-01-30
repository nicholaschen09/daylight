from django.db import models


# =============================================================================
# SAMPLE DJANGO MODELS - For reference only, not part of the assessment solution. Feel free to delete
#
# related_name usage:
#   category.items.all()       # Get all items in a category (reverse FK)
#   tag.items.all()            # Get all items with a tag (reverse M2M)
#
# CRUD Operations:
#   # Create
#   category = Category.objects.create(name="Electronics")
#   item = Item.objects.create(name="Laptop", category=category)
#   item.tags.add(tag1, tag2)
#
#   # Read
#   Item.objects.all()
#   Item.objects.get(id=1)
#   Item.objects.filter(is_active=True)
#   Item.objects.filter(category__name="Electronics")
#
#   # Update
#   item.name = "New Name"
#   item.save()
#   Item.objects.filter(is_active=False).update(is_active=True)
#
#   # Delete
#   item.delete()
#   Item.objects.filter(is_active=False).delete()
#   item.tags.remove(tag1)
#   item.tags.clear()
# =============================================================================
#


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Item(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # ForeignKey relationship
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items",
    )

    # ManyToMany relationship
    tags = models.ManyToManyField(Tag, related_name="items", blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "category"],
                name="unique_item_per_category",
            ),
        ]

    def __str__(self):
        return self.name


# =============================================================================
# SAMPLE DJANGO MODELS - For reference only, not part of the assessment solution. Feel free to delete
# =============================================================================
