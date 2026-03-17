from typing import override
import random
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker

from library.models import Book, Author, Contribution, Publication, Borrowing, Reader

fake = Faker()


class Command(BaseCommand):
    help = "Generate fake data for all models (including User)."

    @override
    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of records per model (minimum).",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="asd",
            help="Password for user (default: 'asd').",
        )

    @override
    def handle(self, *args, **options):
        count = options["count"]
        password = options["password"]
        self.stdout.write(f"Generating at least {count} records per model...")
        self.stdout.write(f"User password: {options['password']}")

        # 1. Users
        users = []
        for _ in range(count):
            user = get_user_model().objects.create_user(  # pyright: ignore[reportAttributeAccessIssue]
                username=fake.unique.user_name(),
                email=fake.unique.email(),
                password=password
            )
            users.append(user)
        self.stdout.write(f"Created {len(users)} users.")

        # 2. Authors
        authors = []
        for _ in range(count):
            author = Author.objects.create(
                fullname=fake.name(),
                birth_on=fake.date_of_birth(minimum_age=20, maximum_age=90),
                birth_place=fake.city()
            )
            authors.append(author)
        self.stdout.write(f"Created {len(authors)} authors.")

        # 3. Books
        books = []
        for _ in range(count):
            book = Book.objects.create(
                title=fake.sentence(nb_words=4),
                created_on=fake.date_this_century(),
                genre=fake.word(),
                summary=fake.text(max_nb_chars=200),
                description=fake.text(max_nb_chars=500) if random.random() > 0.3 else None,
                license=fake.text(max_nb_chars=50) if random.random() > 0.5 else None
            )
            books.append(book)
        self.stdout.write(f"Created {len(books)} books.")

        # 4. Publications
        publications = []
        for _ in range(count):
            book = random.choice(books)
            publication = Publication.objects.create(
                book=book,
                isbn=fake.isbn13(separator="-"),
                publisher=fake.company(),
                published_on=fake.date_this_century(),
                publication_format=random.choice([fmt[0] for fmt in Publication.PublicationFormat.choices]),
                note=fake.text(max_nb_chars=200) if random.random() > 0.3 else None,
                state=random.choice([st[0] for st in Publication.PublicationState.choices])
            )
            publications.append(publication)
        self.stdout.write(f"Created {len(publications)} publications.")

        # 5. Readers
        readers = []
        for user in users:
            reader = Reader.objects.create(
                user=user,
                fullname=fake.name(),
                reader_card_number=fake.unique.bothify(text="RC-#######")
            )
            readers.append(reader)
        self.stdout.write(f"Created {len(readers)} readers.")

        # 6. Contributions
        contributions = []
        for _ in range(count):
            contribution = Contribution.objects.create(
                book=random.choice(books),
                author=random.choice(authors),
                contribution_type=random.choice([ct[0] for ct in Contribution.ContributionType.choices]),
                note=fake.text(max_nb_chars=200) if random.random() > 0.5 else None
            )
            contributions.append(contribution)
        self.stdout.write(f"Created {len(contributions)} contributions.")

        # 7. Borrowings
        borrowings = []
        for _ in range(count):
            publication = random.choice(publications)
            reader = random.choice(readers)
            borrowed_on = fake.date_this_year()
            returned_on = borrowed_on + timedelta(days=random.randint(1, 30)) if random.random() > 0.3 else None
            borrowing = Borrowing.objects.create(
                publication=publication,
                reader=reader,
                borrowed_on=borrowed_on,
                returned_on=returned_on
            )
            borrowings.append(borrowing)
        self.stdout.write(f"Created {len(borrowings)} borrowings.")

        self.stdout.write(self.style.SUCCESS("Fake data generation complete!"))
