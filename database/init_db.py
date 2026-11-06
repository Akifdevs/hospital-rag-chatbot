from database.connection import init_database


def main():

    print(
        "Initializing RAG document database..."
    )

    init_database()

    print(
        "Database initialized successfully."
    )


if __name__ == "__main__":
    main()
