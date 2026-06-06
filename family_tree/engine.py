import json
import os

DATA_DIR = os.path.expanduser("~/.family_tree")
DATA_FILE = os.path.join(DATA_DIR, "data.json")


class FamilyTree:
    def __init__(self, data=None):
        if data:
            self.people = {int(k): v for k, v in data.get("people", {}).items()}
            self.next_id = data.get("next_id", 1)
        else:
            self.people = {}
            self.next_id = 1

    def to_dict(self):
        return {
            "people": {str(k): v for k, v in self.people.items()},
            "next_id": self.next_id,
        }

    def save(self, path=None):
        path = path or DATA_FILE
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load(path=None):
        path = path or DATA_FILE
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            return FamilyTree(data)
        return FamilyTree()

    def add_person(self, name="", age=None, gender="", bio=""):
        pid = self.next_id
        self.next_id += 1
        self.people[pid] = {
            "id": pid,
            "name": name,
            "age": age,
            "gender": gender,
            "bio": bio,
            "relationships": [],
        }
        return pid

    def delete_person(self, pid):
        if pid not in self.people:
            raise ValueError(f"Person #{pid} not found")
        del self.people[pid]
        for p in self.people.values():
            p["relationships"] = [
                r for r in p["relationships"] if r["target_id"] != pid
            ]

    def get_person(self, pid):
        return self.people.get(pid)

    def update_person(self, pid, **kwargs):
        if pid not in self.people:
            raise ValueError(f"Person #{pid} not found")
        for key in ("name", "age", "gender", "bio"):
            if key in kwargs:
                self.people[pid][key] = kwargs[key]

    def add_relationship(self, pid, target_id, rel_type):
        if pid not in self.people:
            raise ValueError(f"Person #{pid} not found")
        if target_id not in self.people:
            raise ValueError(f"Person #{target_id} not found")
        if rel_type not in ("parent", "sibling", "spouse"):
            raise ValueError("Relationship type must be 'parent', 'sibling', or 'spouse'")

        rel = {"type": rel_type, "target_id": target_id}
        existing = self.people[pid]["relationships"]
        if rel not in existing:
            existing.append(rel)

        if rel_type == "parent":
            child_rel = {"type": "child", "target_id": pid}
            if child_rel not in self.people[target_id]["relationships"]:
                self.people[target_id]["relationships"].append(child_rel)
        elif rel_type == "spouse":
            spouse_rel = {"type": "spouse", "target_id": pid}
            if spouse_rel not in self.people[target_id]["relationships"]:
                self.people[target_id]["relationships"].append(spouse_rel)

    def delete_relationship(self, pid, target_id, rel_type):
        if pid not in self.people:
            raise ValueError(f"Person #{pid} not found")
        self.people[pid]["relationships"] = [
            r
            for r in self.people[pid]["relationships"]
            if not (r["type"] == rel_type and r["target_id"] == target_id)
        ]
        if rel_type == "parent":
            self.people[target_id]["relationships"] = [
                r
                for r in self.people[target_id]["relationships"]
                if not (r["type"] == "child" and r["target_id"] == pid)
            ]
        elif rel_type == "spouse":
            self.people[target_id]["relationships"] = [
                r
                for r in self.people[target_id]["relationships"]
                if not (r["type"] == "spouse" and r["target_id"] == pid)
            ]

    def _ancestors(self, pid, max_depth=100):
        result = {pid: 0}
        queue = [(pid, 0)]
        visited = {pid}
        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for rel in self.people[current].get("relationships", []):
                if rel["type"] == "parent":
                    parent_id = rel["target_id"]
                    if parent_id not in visited:
                        visited.add(parent_id)
                        nd = depth + 1
                        result[parent_id] = nd
                        queue.append((parent_id, nd))
        return result

    def _descendants(self, pid, max_depth=100):
        result = {pid: 0}
        queue = [(pid, 0)]
        visited = {pid}
        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for rel in self.people[current].get("relationships", []):
                if rel["type"] == "child":
                    child_id = rel["target_id"]
                    if child_id not in visited:
                        visited.add(child_id)
                        nd = depth + 1
                        result[child_id] = nd
                        queue.append((child_id, nd))
        return result

    def get_all_relationships(self, pid):
        if pid not in self.people:
            return []
        return self.people[pid].get("relationships", [])

    def get_siblings(self, pid):
        if pid not in self.people:
            return []
        parents = [
            r["target_id"]
            for r in self.people[pid].get("relationships", [])
            if r["type"] == "parent"
        ]
        siblings = set()
        for parent_id in parents:
            for other_pid, person in self.people.items():
                if other_pid == pid:
                    continue
                if any(
                    r["type"] == "parent" and r["target_id"] == parent_id
                    for r in person.get("relationships", [])
                ):
                    siblings.add(other_pid)
        return sorted(siblings)

    def get_children(self, pid):
        return sorted(
            other_pid
            for other_pid, person in self.people.items()
            if any(
                r["type"] == "parent" and r["target_id"] == pid
                for r in person.get("relationships", [])
            )
        )

    def get_parents(self, pid):
        if pid not in self.people:
            return []
        return sorted(
            r["target_id"]
            for r in self.people[pid].get("relationships", [])
            if r["type"] == "parent"
        )

    def get_spouses(self, pid):
        if pid not in self.people:
            return []
        return sorted(
            r["target_id"]
            for r in self.people[pid].get("relationships", [])
            if r["type"] == "spouse"
        )

    def get_ancestors(self, pid, max_depth=100):
        raw = self._ancestors(pid, max_depth)
        result = sorted(
            ((dist, pid2) for pid2, dist in raw.items() if pid2 != pid),
            key=lambda x: (x[0], x[1]),
        )
        return result

    def get_descendants(self, pid, max_depth=100):
        raw = self._descendants(pid, max_depth)
        result = sorted(
            ((dist, pid2) for pid2, dist in raw.items() if pid2 != pid),
            key=lambda x: (x[0], x[1]),
        )
        return result

    def get_relationship(self, pid1, pid2):
        if pid1 not in self.people or pid2 not in self.people:
            raise ValueError("Person not found")
        if pid1 == pid2:
            return "same person"

        n1 = self.people[pid1].get("name", f"#{pid1}")
        n2 = self.people[pid2].get("name", f"#{pid2}")

        if self._is_spouse(pid1, pid2):
            return f"{n1} and {n2} are spouses"

        result = self._find_blood_relationship(pid1, pid2)
        if result:
            return result

        result = self._find_inlaw_relationship(pid1, pid2)
        if result:
            return result

        return "no relationship found"

    def _is_spouse(self, pid1, pid2):
        for rel in self.people[pid1].get("relationships", []):
            if rel["type"] == "spouse" and rel["target_id"] == pid2:
                return True
        return False

    def _find_blood_relationship(self, pid1, pid2):
        anc1 = self._ancestors(pid1)
        anc2 = self._ancestors(pid2)

        common = set(anc1.keys()) & set(anc2.keys())
        if common:
            best = min(common, key=lambda x: anc1[x] + anc2[x])
            return _describe_relationship(pid1, pid2, self.people, anc1[best], anc2[best], best)

        desc1 = self._descendants(pid1)
        if pid2 in desc1:
            return _describe_relationship(pid1, pid2, self.people, 0, desc1[pid2], pid1)

        desc2 = self._descendants(pid2)
        if pid1 in desc2:
            return _describe_relationship(pid1, pid2, self.people, desc2[pid1], 0, pid2)

        return None

    def _find_inlaw_relationship(self, pid1, pid2):
        for spouse_id in self.get_spouses(pid1):
            result = self._describe_inlaw(pid1, spouse_id, pid2)
            if result:
                return result
        for spouse_id in self.get_spouses(pid2):
            result = self._describe_inlaw(pid2, spouse_id, pid1)
            if result:
                return result
        return None

    def _describe_inlaw(self, linked_pid, spouse_pid, other_pid):
        n_linked = self.people[linked_pid].get("name", f"#{linked_pid}")
        n_spouse = self.people[spouse_pid].get("name", f"#{spouse_pid}")
        n_other = self.people[other_pid].get("name", f"#{other_pid}")

        anc = self._ancestors(spouse_pid)
        desc = self._descendants(spouse_pid)

        if other_pid in anc:
            dist = anc[other_pid]
            label = {1: "parent", 2: "grandparent"}.get(dist, f"great-{'great-' * (dist - 3)}grandparent" if dist > 2 else "ancestor")
            return f"{n_other} is the {label}-in-law of {n_linked} (spouse of {n_spouse})"

        if other_pid in desc:
            dist = desc[other_pid]
            label = {1: "parent", 2: "grandparent"}.get(dist, f"great-{'great-' * (dist - 3)}grandparent" if dist > 2 else "ancestor")
            return f"{n_linked} (spouse of {n_spouse}) is the step-{label} of {n_other}"

        blood_rel = self._find_blood_relationship(spouse_pid, other_pid)
        if blood_rel:
            return f"{n_linked} (spouse of {n_spouse}) is related by marriage to {n_other}"
        return None


def _describe_relationship(pid1, pid2, people, d1, d2, common_ancestor):
    name1 = people[pid1].get("name", f"#{pid1}")
    name2 = people[pid2].get("name", f"#{pid2}")
    anc_name = people[common_ancestor].get("name", f"#{common_ancestor}")

    if d1 == 0 and d2 == 0:
        return f"{name1} and {name2} are the same person"

    if d1 == 0:
        # pid1 is the common ancestor, pid2 is descendant
        if d2 == 1:
            return f"{name2} is the child of {name1}"
        elif d2 == 2:
            return f"{name2} is the grandchild of {name1}"
        else:
            prefix = "great-" * (d2 - 2)
            return f"{name2} is the {prefix}grandchild of {name1}"

    if d2 == 0:
        # pid2 is the common ancestor, pid1 is descendant
        if d1 == 1:
            return f"{name1} is the child of {name2}"
        elif d1 == 2:
            return f"{name1} is the grandchild of {name2}"
        else:
            prefix = "great-" * (d1 - 2)
            return f"{name1} is the {prefix}grandchild of {name2}"

    d_min = min(d1, d2)
    d_max = max(d1, d2)
    removed = d_max - d_min

    if d_min == 1:
        if removed == 0:
            return f"{name1} and {name2} are siblings"
        if removed == 1:
            if d1 == 1:
                return f"{name1} is the aunt/uncle of {name2}"
            else:
                return f"{name1} is the niece/nephew of {name2}"
        else:
            prefix = "great-" * (removed - 1)
            if d1 == 1:
                return f"{name1} is the {prefix}aunt/uncle of {name2}"
            else:
                return f"{name1} is the {prefix}niece/nephew of {name2}"

    cousin_level = d_min - 1
    cousin_str = _ordinal(cousin_level) + " cousin" if cousin_level > 1 else "first cousin"

    removed_str = ""
    if removed >= 1:
        removed_str = {1: " once removed", 2: " twice removed"}.get(removed, f" {removed} times removed")

    return f"{name1} and {name2} are {cousin_str}{removed_str}"


def _ordinal(n):
    if n == 2:
        return "second"
    elif n == 3:
        return "third"
    elif n == 4:
        return "fourth"
    elif n == 5:
        return "fifth"
    return f"{n}th"
