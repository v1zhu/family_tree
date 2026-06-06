import argparse
import sys

from .engine import FamilyTree


def main():
    parser = argparse.ArgumentParser(
        prog="family-tree",
        description="Family tree relationship manager",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="Start the web UI server")

    add_p = sub.add_parser("add-person", help="Add a person")
    add_p.add_argument("--name", default="", help="Person's name")
    add_p.add_argument("--age", type=int, help="Person's age")
    add_p.add_argument("--gender", default="", help="Person's gender")
    add_p.add_argument("--bio", default="", help="Short biography")

    list_p = sub.add_parser("list", help="List all people")

    info_p = sub.add_parser("info", help="Show person details")
    info_p.add_argument("id", type=int, help="Person ID")

    delete_p = sub.add_parser("delete-person", help="Delete a person")
    delete_p.add_argument("id", type=int, help="Person ID to delete")

    update_p = sub.add_parser("update-person", help="Update person details")
    update_p.add_argument("id", type=int, help="Person ID")
    update_p.add_argument("--name", help="New name")
    update_p.add_argument("--age", type=int, help="New age")
    update_p.add_argument("--gender", help="New gender")
    update_p.add_argument("--bio", help="New biography")

    rel_p = sub.add_parser("add-relation", help="Add a relationship")
    rel_p.add_argument("id1", type=int, help="Person ID")
    rel_p.add_argument("id2", type=int, help="Target person ID")
    rel_p.add_argument(
        "type", choices=["parent", "sibling", "spouse"], help="Relationship type"
    )

    del_rel_p = sub.add_parser(
        "delete-relation", help="Delete a relationship"
    )
    del_rel_p.add_argument("id1", type=int, help="Person ID")
    del_rel_p.add_argument("id2", type=int, help="Target person ID")
    del_rel_p.add_argument(
        "type", choices=["parent", "sibling", "spouse"], help="Relationship type"
    )

    anc_p = sub.add_parser("ancestors", help="Show all ancestors of a person")
    anc_p.add_argument("id", type=int, help="Person ID")

    desc_p = sub.add_parser("descendants", help="Show all descendants of a person")
    desc_p.add_argument("id", type=int, help="Person ID")

    relation_p = sub.add_parser(
        "relation", help="Find relationship between two people"
    )
    relation_p.add_argument("id1", type=int, help="First person ID")
    relation_p.add_argument("id2", type=int, help="Second person ID")

    graph_p = sub.add_parser("graph", help="Export graph data as JSON")
    graph_p.add_argument("--pretty", action="store_true", help="Pretty print")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tree = FamilyTree.load()

    if args.command == "serve":
        from .server import serve

        serve(tree)
    elif args.command == "add-person":
        pid = tree.add_person(
            name=args.name, age=args.age, gender=args.gender, bio=args.bio
        )
        tree.save()
        print(f"Added person #{pid}")
    elif args.command == "list":
        if not tree.people:
            print("No people in the tree.")
            return
        for pid in sorted(tree.people):
            p = tree.people[pid]
            name = p.get("name", "") or "Unnamed"
            age = p.get("age")
            age_str = f", {age}" if age else ""
            print(f"  #{pid}: {name}{age_str}")
    elif args.command == "info":
        p = tree.get_person(args.id)
        if not p:
            print(f"Person #{args.id} not found.")
            return
        print(f"  ID: #{p['id']}")
        print(f"  Name: {p.get('name', '') or 'Unnamed'}")
        print(f"  Age: {p.get('age', '') or 'N/A'}")
        print(f"  Gender: {p.get('gender', '') or 'N/A'}")
        print(f"  Bio: {p.get('bio', '') or 'N/A'}")
        spouses = tree.get_spouses(args.id)
        if spouses:
            spouse_names = [
                tree.people[pid].get("name", f"#{pid}") for pid in spouses
            ]
            print(f"  Spouses: {', '.join(spouse_names)}")
        parents = tree.get_parents(args.id)
        if parents:
            parent_names = [
                tree.people[pid].get("name", f"#{pid}") for pid in parents
            ]
            print(f"  Parents: {', '.join(parent_names)}")
        children = tree.get_children(args.id)
        if children:
            child_names = [
                tree.people[pid].get("name", f"#{pid}") for pid in children
            ]
            print(f"  Children: {', '.join(child_names)}")
        siblings = tree.get_siblings(args.id)
        if siblings:
            sibling_names = [
                tree.people[pid].get("name", f"#{pid}") for pid in siblings
            ]
            print(f"  Siblings: {', '.join(sibling_names)}")
    elif args.command == "delete-person":
        tree.delete_person(args.id)
        tree.save()
        print(f"Deleted person #{args.id}")
    elif args.command == "update-person":
        kwargs = {}
        for key in ("name", "age", "gender", "bio"):
            val = getattr(args, key, None)
            if val is not None:
                kwargs[key] = val
        tree.update_person(args.id, **kwargs)
        tree.save()
        print(f"Updated person #{args.id}")
    elif args.command == "add-relation":
        try:
            tree.add_relationship(args.id1, args.id2, args.type)
            tree.save()
            print(
                f"Added {args.type} relationship: #{args.id1} -> #{args.id2}"
            )
        except ValueError as e:
            print(f"Error: {e}")
    elif args.command == "delete-relation":
        try:
            tree.delete_relationship(args.id1, args.id2, args.type)
            tree.save()
            print(
                f"Deleted {args.type} relationship: #{args.id1} -> #{args.id2}"
            )
        except ValueError as e:
            print(f"Error: {e}")
    elif args.command == "relation":
        try:
            result = tree.get_relationship(args.id1, args.id2)
            print(result)
        except ValueError as e:
            print(f"Error: {e}")
    elif args.command == "ancestors":
        p = tree.get_person(args.id)
        if not p:
            print(f"Person #{args.id} not found.")
            return
        name = p.get("name", "") or f"#{args.id}"
        ancest = tree.get_ancestors(args.id)
        if not ancest:
            print(f"{name} has no known ancestors.")
            return
        print(f"Ancestors of {name}:")
        for dist, pid in ancest:
            an = tree.people[pid].get("name", f"#{pid}")
            label = {1: "parent", 2: "grandparent"}.get(dist, f"great-{'great-' * (dist - 3)}grandparent" if dist > 2 else f"{dist} gen up")
            print(f"  #{pid}: {an} ({label}, {dist} generation{'s' if dist > 1 else ''} away)")
    elif args.command == "descendants":
        p = tree.get_person(args.id)
        if not p:
            print(f"Person #{args.id} not found.")
            return
        name = p.get("name", "") or f"#{args.id}"
        desc = tree.get_descendants(args.id)
        if not desc:
            print(f"{name} has no known descendants.")
            return
        print(f"Descendants of {name}:")
        for dist, pid in desc:
            dn = tree.people[pid].get("name", f"#{pid}")
            label = {1: "child", 2: "grandchild"}.get(dist, f"great-{'great-' * (dist - 3)}grandchild" if dist > 2 else f"{dist} gen down")
            print(f"  #{pid}: {dn} ({label}, {dist} generation{'s' if dist > 1 else ''} away)")
    elif args.command == "graph":
        import json as json_module

        nodes = []
        edges = []
        for pid, p in tree.people.items():
            nodes.append(
                {
                    "id": pid,
                    "label": p.get("name", f"#{pid}"),
                    "age": p.get("age"),
                    "gender": p.get("gender"),
                    "bio": p.get("bio"),
                }
            )
            for rel in p.get("relationships", []):
                edges.append(
                    {
                        "from": pid,
                        "to": rel["target_id"],
                        "label": rel["type"],
                    }
                )
        graph = {"nodes": nodes, "edges": edges}
        indent = 2 if args.pretty else None
        print(json_module.dumps(graph, indent=indent))


if __name__ == "__main__":
    main()
