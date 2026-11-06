import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import get_session, init_database
from database.repository import DocumentRepository
from auth.roles import ROLE_PATTERN, clear_role_cache


def cmd_list(args):
    session = get_session()
    try:
        repo = DocumentRepository(session)
        roles = repo.list_roles()
        if not roles:
            print("No roles configured.")
            return

        print(f"{'ROLE':<20} {'ACTIVE':<8} {'ALL DOCS':<10} {'GRANTS':<40} {'DESCRIPTION'}")
        print("-" * 90)
        for role in roles:
            grants_str = ", ".join(
                f"{g.document_identifier}" + (f" (v{g.documentation_version})" if g.documentation_version else "")
                for g in role.document_access
            ) or "(none)"
            print(
                f"{role.name:<20} {str(role.is_active):<8} {str(role.can_access_all):<10} {grants_str:<40} {role.description or ''}"
            )
    finally:
        session.close()


def cmd_create_role(args):
    name = args.name.strip().lower()
    if not ROLE_PATTERN.fullmatch(name):
        print(f"Error: Invalid role name '{name}'. Must match ^[a-z0-9_-]{{1,50}}$")
        sys.exit(1)

    session = get_session()
    try:
        repo = DocumentRepository(session)
        existing = repo.get_role(name)
        if existing:
            print(f"Role '{name}' already exists.")
            return

        role = repo.create_role(
            name=name,
            description=args.description,
            can_access_all=bool(args.all),
            is_active=True,
        )
        clear_role_cache()
        print(f"Role '{role.name}' created successfully (can_access_all={role.can_access_all}).")
    finally:
        session.close()


def cmd_delete_role(args):
    name = args.name.strip().lower()
    session = get_session()
    try:
        repo = DocumentRepository(session)
        deleted = repo.delete_role(name)
        clear_role_cache()
        if deleted:
            print(f"Role '{name}' deleted.")
        else:
            print(f"Role '{name}' does not exist.")
    finally:
        session.close()


def cmd_deactivate_role(args):
    name = args.name.strip().lower()
    session = get_session()
    try:
        repo = DocumentRepository(session)
        deactivated = repo.deactivate_role(name)
        clear_role_cache()
        if deactivated:
            print(f"Role '{name}' deactivated.")
        else:
            print(f"Role '{name}' does not exist.")
    finally:
        session.close()


def cmd_set_all(args):
    name = args.name.strip().lower()
    mode = args.mode.strip().lower()
    if mode not in {"on", "off"}:
        print("Error: mode must be 'on' or 'off'")
        sys.exit(1)

    can_access_all = (mode == "on")
    session = get_session()
    try:
        repo = DocumentRepository(session)
        updated = repo.set_role_access_all(name, can_access_all)
        clear_role_cache()
        if updated:
            print(f"Role '{name}' can_access_all set to {can_access_all}.")
        else:
            print(f"Role '{name}' does not exist.")
    finally:
        session.close()


def cmd_grant(args):
    role_name = args.role.strip().lower()
    doc_raw = args.document.strip().lower()
    doc_stem = doc_raw[:-3] if doc_raw.endswith(".md") else doc_raw
    version = str(args.version).strip() if args.version is not None else None

    session = get_session()
    try:
        repo = DocumentRepository(session)
        role = repo.get_role(role_name)
        if not role:
            print(f"Error: Role '{role_name}' does not exist.")
            sys.exit(1)

        available_docs = repo.list_all_document_identifiers()
        if doc_stem not in available_docs:
            print(f"Error: Document '{doc_raw}' not found in ingested documents.")
            print(f"Available documents: {', '.join(available_docs) if available_docs else '(none ingested)'}")
            sys.exit(1)

        repo.grant_document_access(
            role_name=role_name,
            document_identifier=doc_stem,
            documentation_version=version,
        )
        clear_role_cache()
        ver_info = f" (version {version})" if version else " (all versions)"
        print(f"Granted access to '{doc_stem}'{ver_info} for role '{role_name}'.")
    finally:
        session.close()


def cmd_revoke(args):
    role_name = args.role.strip().lower()
    doc_raw = args.document.strip().lower()
    doc_stem = doc_raw[:-3] if doc_raw.endswith(".md") else doc_raw
    version = str(args.version).strip() if args.version is not None else None

    session = get_session()
    try:
        repo = DocumentRepository(session)
        revoked = repo.revoke_document_access(
            role_name=role_name,
            document_identifier=doc_stem,
            documentation_version=version,
        )
        clear_role_cache()
        ver_info = f" (version {version})" if version else " (all versions)"
        if revoked:
            print(f"Revoked access to '{doc_stem}'{ver_info} from role '{role_name}'.")
        else:
            print(f"No matching grant found for role '{role_name}' and document '{doc_stem}'.")
    finally:
        session.close()


def cmd_seed_examples(args):
    init_database()
    session = get_session()
    try:
        repo = DocumentRepository(session)

        # 1. Admin role (can_access_all = True)
        admin = repo.get_role("admin")
        if admin is None:
            admin = repo.create_role(
                name="admin",
                description="Administrator with full documentation access",
                can_access_all=True,
                is_active=True,
            )
            print("Created role 'admin' with can_access_all=True.")
        else:
            admin.can_access_all = True
            admin.is_active = True
            session.commit()
            print("Updated role 'admin' (can_access_all=True, is_active=True).")

        # 2. Receptionist role (can_access_all = False, grants to billing-guide & corporate-billing-guide)
        receptionist = repo.get_role("receptionist")
        if receptionist is None:
            receptionist = repo.create_role(
                name="receptionist",
                description="Receptionist with billing documentation access",
                can_access_all=False,
                is_active=True,
            )
            print("Created role 'receptionist'.")
        else:
            receptionist.can_access_all = False
            receptionist.is_active = True
            session.commit()
            print("Updated role 'receptionist' (can_access_all=False, is_active=True).")

        repo.grant_document_access(
            role_name="receptionist",
            document_identifier="billing-guide",
            documentation_version=None,
        )
        repo.grant_document_access(
            role_name="receptionist",
            document_identifier="corporate-billing-guide",
            documentation_version=None,
        )
        clear_role_cache()
        print("Granted 'billing-guide' and 'corporate-billing-guide' (all versions) to 'receptionist'.")
        print("Seed examples completed successfully.")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Manage RAG roles and document access permissions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="List all roles and their document access grants")

    # create-role
    create_p = subparsers.add_parser("create-role", help="Create a new role")
    create_p.add_argument("name", help="Role name (lowercase alphanumeric)")
    create_p.add_argument("--all", action="store_true", help="Grant access to all documents")
    create_p.add_argument("--description", default=None, help="Role description")

    # delete-role
    del_p = subparsers.add_parser("delete-role", help="Delete a role")
    del_p.add_argument("name", help="Role name")

    # deactivate-role
    deact_p = subparsers.add_parser("deactivate-role", help="Deactivate a role")
    deact_p.add_argument("name", help="Role name")

    # set-all
    setall_p = subparsers.add_parser("set-all", help="Toggle can_access_all for a role")
    setall_p.add_argument("role", help="Role name")
    setall_p.add_argument("mode", choices=["on", "off"], help="on or off")

    # grant
    grant_p = subparsers.add_parser("grant", help="Grant document access to a role")
    grant_p.add_argument("role", help="Role name")
    grant_p.add_argument("document", help="Document identifier (file stem or name)")
    grant_p.add_argument("--version", default=None, help="Documentation version (omit for all versions)")

    # revoke
    revoke_p = subparsers.add_parser("revoke", help="Revoke document access from a role")
    revoke_p.add_argument("role", help="Role name")
    revoke_p.add_argument("document", help="Document identifier")
    revoke_p.add_argument("--version", default=None, help="Documentation version")

    # seed-examples
    subparsers.add_parser("seed-examples", help="Seed default example roles (admin and receptionist)")

    args = parser.parse_args()

    commands = {
        "list": cmd_list,
        "create-role": cmd_create_role,
        "delete-role": cmd_delete_role,
        "deactivate-role": cmd_deactivate_role,
        "set-all": cmd_set_all,
        "grant": cmd_grant,
        "revoke": cmd_revoke,
        "seed-examples": cmd_seed_examples,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

