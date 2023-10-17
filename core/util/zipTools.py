import os
import zipfile


from .common import create_dir


def extract_zip_plugin(curr_dir, resource_path):
    create_dir(resource_path)
    pack = zipfile.ZipFile(curr_dir)
    for pack_file in support_gbk(pack).namelist():
        if pack_file.endswith('.py'):
            continue
        if os.path.exists(os.path.join(resource_path, pack_file)):
            continue
        pack.extract(pack_file, resource_path)


def support_gbk(zip_file: zipfile.ZipFile):
    name_to_info = zip_file.NameToInfo
    for name, info in name_to_info.copy().items():
        real_name = name.encode('cp437').decode('gbk')
        if real_name != name:
            info.filename = real_name
            del name_to_info[name]
            name_to_info[real_name] = info
    return zip_file
