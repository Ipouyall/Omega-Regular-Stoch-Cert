import json
import yaml


def unify_all_uploaded(files):
    values = [(file.name, file.getvalue().decode("utf-8")) for file in files]
    unified = {}
    for name, value in values:
        if name.endswith(".json"):
            unified.update(json.loads(value))
        elif name.endswith(".yaml") or name.endswith(".yml"):
            unified.update(yaml.safe_load(value))
    return unified


def upload_file(ui_stat_place_holder, ui_uploader_place_holder):
    file_list = ui_uploader_place_holder.file_uploader(
        "Upload sample file(s)",
        type=["json", "yaml", "yml"],
        accept_multiple_files=True,
    )
    if file_list:
        ui_stat_place_holder.success("File uploaded successfully!" if len(file_list) == 1 else "Files uploaded successfully!")
        return unify_all_uploaded(file_list)
    return None
