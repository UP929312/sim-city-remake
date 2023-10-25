new_names = []

with open("name_list.txt", "r") as file:
    people_names: list[str] = file.read().split("\n")
    # rint(len(people_names))
    for name_row in people_names:
        name = name_row.split()
        if len(name) <= 1:
            # rint("No surname", name)
            continue
        name = name[::-1]
        first, last = name[0].title(), name[-1]
        if len(name[-1]) == 1:
            # rint("One letter surname, skipping", name)
            continue
        if first[0] in ["*", "'", "©"]:
            continue
        if first[0] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ".lower():
            continue
        new_names.append(" ".join((first, last)))

# rint(len(new_names))

with open("cleaned_names.txt", "w") as file:
    file.write("\n".join(sorted(new_names)))
