
import json
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from app.database import users_collection, projects_collection


EXPECTED_PROJECTS = {
    ("my first test project", "https://example.com"),
    ("test 2 ", "https://www.encyclopedia.com"),
    ("web", "https://www.wikipedia.com"),
    ("Northstar Demo store", "http://localhost:3001"),
}


def main():
    print("\n=== TEST AI PROJECT OWNERSHIP MIGRATION ===\n")

    users = list(
        users_collection.find(
            {},
            {"name": 1, "email": 1},
        )
    )

    if not users:
        raise RuntimeError("No registered accounts found.")

    print("Registered accounts:\n")

    for index, user in enumerate(users, start=1):
        print(
            f"{index}. {user.get('name', 'Unknown')} "
            f"({user.get('email', 'No email')})"
        )

    choice = input(
        "\nSelect the number of your current Test AI account: "
    ).strip()

    if not choice.isdigit():
        raise RuntimeError("Please enter a valid account number.")

    selected_index = int(choice) - 1

    if selected_index < 0 or selected_index >= len(users):
        raise RuntimeError("Account selection is out of range.")

    selected_user = users[selected_index]
    owner_id = str(selected_user["_id"])

    unowned_projects = list(
        projects_collection.find({
            "owner_id": {"$exists": False}
        })
    )

    if len(unowned_projects) != 4:
        raise RuntimeError(
            "Expected exactly four unowned projects, "
            f"but found {len(unowned_projects)}. "
            "No changes were made."
        )

    actual_projects = {
        (
            project.get("name"),
            project.get("target_url"),
        )
        for project in unowned_projects
    }

    if actual_projects != EXPECTED_PROJECTS:
        print("\nUnowned project records differ from the expected list.")
        print("No changes were made.")
        return

    print("\nProjects to migrate:\n")

    for project in unowned_projects:
        print(
            f"- {project['name']} "
            f"(ID: {project['_id']})"
        )

    print(
        "\nSelected account:",
        selected_user.get("email"),
    )

    confirmation = input(
        "\nType ASSIGN to confirm these four projects belong "
        "to this account: "
    ).strip()

    if confirmation != "ASSIGN":
        print("Migration cancelled. No changes made.")
        return

    backup_dir = Path(__file__).resolve().parent / "migration_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup_path = backup_dir / f"projects_before_owner_{timestamp}.json"

    backup_records = [
        {
            **{
                key: value
                for key, value in project.items()
                if key != "_id"
            },
            "_id": str(project["_id"]),
        }
        for project in unowned_projects
    ]

    with backup_path.open("x", encoding="utf-8") as file:
        json.dump(
            backup_records,
            file,
            indent=2,
            default=str,
        )

    print(f"\nBackup created: {backup_path}")

    migrated = 0

    for project in unowned_projects:
        result = projects_collection.update_one(
            {
                "_id": ObjectId(project["_id"]),
                "owner_id": {"$exists": False},
            },
            {
                "$set": {
                    "owner_id": owner_id,
                }
            },
        )

        migrated += result.modified_count

    print(f"\nProjects updated: {migrated}")

    verified = projects_collection.count_documents({
        "_id": {
            "$in": [project["_id"] for project in unowned_projects]
        },
        "owner_id": owner_id,
    })

    print(f"Projects verified under selected account: {verified}")

    if migrated == 4 and verified == 4:
        print("\nSUCCESS: All four projects assigned.")
    else:
        print(
            "\nWARNING: Migration was incomplete. "
            "Keep the backup and review the database."
        )


if __name__ == "__main__":
    main()
