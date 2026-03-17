from typing import Optional, Any, Annotated
from pydantic import field_validator
from datetime import date

from ninja import NinjaAPI, Router, Query, Schema, ModelSchema, Field, Path, Header
from ninja.errors import HttpError
from ninja.pagination import paginate

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from .helpers import bulk_sync
from .models import Author, Book, Publication, Contribution, Borrowing, Reader

borrowing_router = Router()
publication_router = Router()
book_router = Router()
author_router = Router()


api = NinjaAPI(version="1.0.0", title="Library Administration")
api.add_router("borrowings/", borrowing_router, tags=["Borrowings"])
api.add_router("publications/", publication_router, tags=["Publications"])
api.add_router("books/", book_router, tags=["Books"])
api.add_router("authors/", author_router, tags=["Authors"])


class ResponseSuccessSchema(Schema):
    success: bool


class ResponseIdSchema(Schema):
    id: int


class AuthorCreate(ModelSchema):
    model_config = {"extra": "forbid"}
    class Meta:
        model = Author
        fields = "__all__"
        exclude = ("id",)


class AuthorGet(ModelSchema):
    class Meta:
        model = Author
        fields = "__all__"


class AuthorUpdate(ModelSchema):
    model_config = {"extra": "forbid"}
    class Meta:
        model = Author
        fields_optional = "__all__"
        exclude = ("id",)


class AuthorList(Schema):
    id: int
    fullname: str


class AuthorFilter(Schema):
    fullname__icontains: str | None = Field(None, alias="fullname")
    contribution__book__title__icontains: str | None = Field(None, alias="book_name")


@author_router.post("create/", response=ResponseIdSchema)
def author_create(request, author: AuthorCreate):
    new_author: Author = Author.objects.create(**author.dict())
    return ResponseIdSchema(id=new_author.pk)


@author_router.patch("{author_id}/update/", response=ResponseSuccessSchema)
def author_update(request, author_id: int, payload: AuthorUpdate):
    author: Author = get_object_or_404(Author, pk=author_id)
    for field_name, value in payload.dict(exclude_unset=True).items():
        setattr(author, field_name, value)

    author.save()

    return ResponseSuccessSchema(success=True)


@author_router.get("", response=list[AuthorList])
@paginate()
def author_list(request, query: Query[AuthorFilter]):
    authors = Author.objects.filter(**query.dict(exclude_none=True)).distinct()
    result = []
    for author in authors:
        result.append(AuthorList(id=author.pk, fullname=author.fullname))
    return result


@author_router.get("{author_id}/", response=AuthorGet)
def author_get(request, author_id: int):
    author: Author = get_object_or_404(Author, pk=author_id)
    return author


class ContributionCreate(ModelSchema):
    model_config = {"extra": "forbid"}

    @field_validator("author", mode="before", check_fields=False)
    @classmethod
    def author_exists(cls, value: int):
        if not Author.objects.filter(pk=value).exists():
            raise ValueError(f"Author with id {value} does not exist")
        return value
    class Meta:
        model = Contribution
        fields = "__all__"
        exclude = ("id", "book")


class ContributionGet(ModelSchema):
    class Meta:
        model = Contribution
        fields = "__all__"
        exclude = ("book",)


class ContributionSync(ModelSchema):
    model_config = {"extra": "forbid"}

    @field_validator("author", mode="before", check_fields=False)
    @classmethod
    def author_exists(cls, value: int):
        if not Author.objects.filter(pk=value).exists():
            raise ValueError(f"Author with id {value} does not exist")
        return value

    class Meta:
        model = Contribution
        fields = "__all__"
        fields_optional = ("id",)
        exclude = ("book",)


class ContributionList(Schema):
    contribution_type: str
    author: AuthorList


class BookCreate(ModelSchema):
    model_config = {"extra": "forbid"}
    contributions: list[ContributionCreate]
    class Meta:
        model = Book
        fields = "__all__"
        exclude = ("id",)


class BookGet(ModelSchema):
    contributions: list[ContributionGet] = Field(default_factory=list, alias="contribution_set.all")
    class Meta:
        model = Book
        fields = "__all__"


class BookUpdate(ModelSchema):
    model_config = {"extra": "forbid"}
    contributions: Optional[list[ContributionSync]] = None
    class Meta:
        model = Book
        fields_optional = "__all__"
        exclude = ("id",)


class BookList(Schema):
    id: int
    title: str
    contributions: list[ContributionList] = Field(default_factory=list, alias="contribution_set.all")


class BookFilter(Schema):
    title__icontains: str | None = Field(None, alias="title")
    genre__icontains: str | None = Field(None, alias="genre")
    contribution__author__fullname__icontains: str | None = Field(None, alias="author_fullname")


@book_router.post("create/", response=ResponseIdSchema)
@transaction.atomic
def book_create(request, book: BookCreate):
    book_to_create: dict[str, Any] = book.dict()

    contributions = book_to_create.pop("contributions")

    new_book: Book = Book.objects.create(**book_to_create)

    for contribution in contributions:
        contribution["author"] = Author.objects.get(id=contribution["author"])
        Contribution.objects.create(book=new_book, **contribution)

    return ResponseIdSchema(id=new_book.pk)


@book_router.patch("{book_id}/update/", response=ResponseSuccessSchema)
@transaction.atomic
def book_update(request, book_id: int, payload: BookUpdate):
    book: Book = get_object_or_404(Book, pk=book_id)

    book_to_update: dict[str, Any] = payload.dict(exclude_unset=True)
    contributions = book_to_update.pop("contributions", [])

    bulk_sync(
        contributions,
        "book",
        book,
        Contribution,
        {"author": Author},
        ["author", "contribution_type", "note"]
    )

    for field_name, value in book_to_update.items():
        setattr(book, field_name, value)
    book.save()

    return ResponseSuccessSchema(success=True)


@book_router.get("", response=list[BookList])
@paginate
def book_list(request, query: Query[BookFilter]):
    books: QuerySet[Book] = Book.objects.filter(**query.dict(exclude_none=True)).distinct()
    return books


@book_router.get("{book_id}/", response=BookGet)
def book_get(request, book_id: int):
    book: Book = get_object_or_404(Book, pk=book_id)
    return book


class PublicationCreate(ModelSchema):
    model_config = {"extra": "ignore"}
    @field_validator("book", mode="before", check_fields=False)
    @classmethod
    def book_exists(cls, value: int):
        if not Book.objects.filter(pk=value).exists():
            raise ValueError(f"Book with id {value} does not exist")
        return value
    class Meta:
        model = Publication
        fields = "__all__"
        exclude = ("id", "state")


class PublicationUpdate(ModelSchema):
    model_config = {"extra": "ignore"}
    @field_validator("book", mode="before", check_fields=False)
    @classmethod
    def book_exists(cls, value: int):
        if not Book.objects.filter(pk=value).exists():
            raise ValueError(f"Book with id {value} does not exist")
        return value
    class Meta:
        model = Publication
        fields_optional = "__all__"
        exclude = ("id", "state")


class PublicationGet(ModelSchema):
    book: BookGet = Field(..., alias="book")
    class Meta:
        model = Publication
        fields = "__all__"


class PublicationTransition(Schema):
    publication_id: int
    state: Publication.PublicationState


class PublicationFilter(Schema):
    isbn__icontains: str | None = Field(None, alias="isbn")
    book__name__icontains: str | None = Field(None, alias="book_name")
    book__contribution__author__fullname__icontains: str | None = Field(None, alias="author_fullname")
    state: Publication.PublicationState | None = None


class PublicationList(Schema):
    id: int
    isbn: str
    book: BookList


@publication_router.post("create/", response=ResponseIdSchema)
def publication_create(request, publication: PublicationCreate):
    publication_to_create: dict[str, Any] = publication.dict()
    publication_to_create["book"] = Book.objects.get(pk=publication_to_create["book"])

    new_publication: Publication = Publication.objects.create(**publication_to_create)

    return ResponseIdSchema(id=new_publication.pk)


@publication_router.patch("{publication_id}/update/")
def publication_update(request, publication_id: int, payload: PublicationUpdate):
    publication: Publication = get_object_or_404(Publication, pk=publication_id)

    publication_to_update = payload.dict(exclude_unset=True)
    if book_id := publication_to_update.get("book"):
        publication_to_update["book"] = Book.objects.get(pk=book_id)

    for field_name, value in publication_to_update.items():
        setattr(publication, field_name, value)

    publication.save()

    return ResponseSuccessSchema(success=True)


@publication_router.get("{publication_id}/", response=PublicationGet)
def publication_get(request, publication_id: int):
    return get_object_or_404(Publication, pk=publication_id)


@publication_router.patch("{publication_id}/to/{state}/", response=ResponseSuccessSchema)
def publication_to_state(request, params: Path[PublicationTransition]):
    if params.state != Publication.PublicationState.AVAILABLE:
        raise HttpError(
            400,
            f"Transition to state '{Publication.PublicationState(params.state).label}' is not implemented!"
        )

    publication: Publication = get_object_or_404(
        Publication,
        pk=params.publication_id,
        state=Publication.PublicationState.RETURNED
    )
    publication.state = params.state
    publication.save()

    return ResponseSuccessSchema(success=True)


@publication_router.get("", response=list[PublicationList])
@paginate
def publication_list(request, query: Query[PublicationFilter]):
    publications: QuerySet[Publication] = Publication.objects.filter(**query.dict(exclude_none=True)).distinct()
    return publications


UserId = Annotated[int, Header(..., description="User ID", alias="x-user-id")]  # pyright: ignore[reportCallIssue]


@publication_router.post("{publication_id}/borrow/", response=ResponseSuccessSchema)
@transaction.atomic
def borrow_create(request, publication_id: int, user_id: UserId):
    publication = get_object_or_404(Publication, pk=publication_id, state=Publication.PublicationState.AVAILABLE)
    publication.state = Publication.PublicationState.BORROWED
    publication.save()

    if not (reader := Reader.objects.filter(user_id=user_id).first()):
        raise HttpError(400, "Reader not found.")

    Borrowing.objects.create(publication=publication, reader=reader, borrowed_on=timezone.now().date())

    return ResponseSuccessSchema(success=True)


@publication_router.patch("{publication_id}/return/", response=ResponseSuccessSchema)
@transaction.atomic
def borrow_return(request, publication_id: int, user_id: UserId):
    publication = get_object_or_404(Publication, pk=publication_id, state=Publication.PublicationState.BORROWED)
    publication.state = Publication.PublicationState.RETURNED
    publication.save()

    if not (reader := Reader.objects.filter(user_id=user_id).first()):
        raise HttpError(400, "Reader not found.")

    Borrowing.objects.filter(publication=publication, reader=reader, returned_on__isnull=True).update(returned_on=timezone.now().date())

    return ResponseSuccessSchema(success=True)


class UserList(Schema):
    id: int
    username: str
    email: str


class ReaderList(Schema):
    user: UserList
    fullname: str
    reader_card_number: str


class BorrowingList(Schema):
    publication: PublicationList
    reader: ReaderList
    borrowed_on: date
    returned_on: date | None = None


class BorrowingFilter(Schema):
    reader__user_id: int | None = Field(None, alias="user_id")
    reader__fullname__icontains: str | None = Field(None, alias="reader_fullname")
    reader__reader_card_number: str | None = Field(None, alias="reader_card_number")
    publication__state: Publication.PublicationState | None = Field(None, alias="publication_state")


@borrowing_router.get("", response=list[BorrowingList])
@paginate
def borrowing_list(request, query: Query[BorrowingFilter]):
    borrowings: QuerySet[Borrowing] = Borrowing.objects.filter(**query.dict(exclude_none=True)).distinct()
    return borrowings
