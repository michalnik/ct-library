import pytest


@pytest.mark.django_db
def test_borrow_publication(test_data):
    from ninja.testing import TestClient
    from library.rest import publication_router
    from library.models import Borrowing, Publication, Reader

    available_publication = Publication.objects.filter(
        state=Publication.PublicationState.AVAILABLE
    ).first()
    assert available_publication

    reader = Reader.objects.filter(user__is_active=True).first()
    assert reader

    readers_borrowings = Borrowing.objects.filter(
        publication=available_publication,
        reader=reader,
        returned_on__isnull=True
    )
    current_count = readers_borrowings.count()

    client = TestClient(publication_router)
    response = client.post(
        f"{available_publication.pk}/borrow/",
        headers={"x-user-id": reader.user.pk},
    )
    assert response.status_code == 200
    assert response.data["success"] == True

    available_publication.refresh_from_db()
    assert available_publication.state == Publication.PublicationState.BORROWED

    assert readers_borrowings.exists()
    assert readers_borrowings.count() == current_count + 1

    response = client.patch(
        f"{available_publication.pk}/return/",
        headers={"x-user-id": reader.user.pk},
    )
    assert response.status_code == 200
    assert response.data["success"] == True

    available_publication.refresh_from_db()
    assert available_publication.state == Publication.PublicationState.RETURNED

    assert not readers_borrowings.exists()


@pytest.mark.django_db
def test_mark_available(test_data):
    from ninja.testing import TestClient
    from library.rest import publication_router
    from library.models import Borrowing, Publication, Reader

    returned_publication = Publication.objects.filter(state=Publication.PublicationState.RETURNED).first()
    assert returned_publication

    client = TestClient(publication_router)
    response = client.patch(f"{returned_publication.id}/to/{Publication.PublicationState.AVAILABLE}/")

    assert response.status_code == 200

    returned_publication.refresh_from_db()
    assert returned_publication.state == Publication.PublicationState.AVAILABLE
