file_path = "scenario_pass"


def append_to_file(string_to_append):
    with open(file_path, "a+") as file:
        file.write(string_to_append)


if __name__ == "__main__":
    append_to_file("aa")
