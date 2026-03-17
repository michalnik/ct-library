from django.db import models
from django.conf import settings


class Book(models.Model):
    title = models.CharField(max_length=255)
    created_on = models.DateField()
    genre = models.CharField(max_length=255)
    summary = models.TextField()
    description = models.TextField(null=True)
    license = models.TextField(null=True)


class Contribution(models.Model):
    class ContributionType(models.TextChoices):
        AUTHOR = "AUT", "Author"
        CO_AUTHOR = "COA", "Co-Author"
        TRANSLATOR = "TRL", "Translator"
        EDITOR = "EDT", "Editor"
        ILLUSTRATOR = "ILS", "Illustrator"

    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)
    contribution_type = models.CharField(
        default=ContributionType.AUTHOR,
        choices=ContributionType,
        max_length=255
    )
    note = models.TextField(null=True)


class Author(models.Model):
    fullname = models.CharField(max_length=255)
    birth_on = models.DateField()
    birth_place = models.CharField(max_length=255)


class Publication(models.Model):
    class PublicationFormat(models.TextChoices):
        PAPERBACK = "PBK", "Paperback"
        HARDCOVER = "HCV", "Hardcover"
        EBOOK = "EBK", "Ebook"
        AUDIOBOOK = "ABK", "Audiobook"

    class PublicationState(models.TextChoices):
        AVAILABLE = "AVL", "Available"
        BORROWED = "BOR", "Borrowed"
        RETURNED = "RTD", "Returned"
        LOST = "LST", "Lost"
        DAMAGED = "DMG", "Damaged"
        DISCARDED = "DCD", "Discarded"

    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    isbn = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    published_on = models.DateField()
    publication_format = models.CharField(
        default=PublicationFormat.PAPERBACK,
        choices=PublicationFormat,
        max_length=255
    )
    note = models.TextField(null=True)
    state = models.CharField(
        default=PublicationState.AVAILABLE,
        choices=PublicationState,
        max_length=255
    )


class Borrowing(models.Model):
    publication = models.ForeignKey("Publication", on_delete=models.CASCADE)
    reader = models.ForeignKey("Reader", on_delete=models.CASCADE)
    borrowed_on = models.DateField()
    returned_on = models.DateField(null=True)


class Reader(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=255)
    reader_card_number = models.CharField(max_length=255, unique=True)
