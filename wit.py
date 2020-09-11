# upload 177
import datetime
import distutils.core
from filecmp import dircmp
import os
import random
import shutil
import sys

from graphviz import Digraph


def init():
    try:
        os.mkdir('.wit')
    except FileExistsError as err:
        print(f"{err}")
    finally:
        with open(os.path.join('.wit', 'activated.txt'), 'w+') as activated_file:
            activated_file.write('master')
        path_list = ['images', 'staging_area']
        for new_dir in path_list:
            path_dir = os.path.join('.wit', new_dir)
            try:
                os.mkdir(path_dir)
            except FileExistsError as err:
                print(f"{err}")


def add(path):
    src = os.path.abspath(path)
    witlocation = find_wit(path)
    witlocation = witlocation[::-1]
    witdirectory = os.getcwd()
    dst = os.path.join(witdirectory, '.wit', 'staging_area')
    if os.path.isdir(src):
        for item in witlocation:
            dst = os.path.join(dst, item)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
    elif os.path.isfile(src):
        for item in witlocation[:-1]:
            dst = os.path.join(dst, item)
        shutil.copy(src, dst)


def find_wit(path):
    which_dir_list = [path]
    parentpath = os.path.basename(os.getcwd())
    while parentpath != '':
        if '.wit' in os.listdir(os.getcwd()):
            return which_dir_list
        else:
            which_dir_list.append(parentpath)
            parentpath = os.path.basename(os.getcwd())
            os.chdir("..")
    raise ValueError("No wit")


def commit(MESSAGE):
    wit_path = is_wit_in_here()
    if wit_path:
        parent_folder_name = 'None'
        folder_name = create_folder(wit_path)
        with open(os.path.join(wit_path, '.wit', 'activated.txt'), 'r') as activated_file:
            branch_active = activated_file.read()
        if branch_active == '':
            reference_text = f'HEAD={folder_name}\nmaster={folder_name}\n'
        else:
            if os.path.isfile(os.path.join(wit_path, '.wit', 'references.txt')):
                with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
                    references_lines = references_file.readlines()
                for index_line in range(len(references_lines)):
                    if branch_active == references_lines[index_line][: len(branch_active)]:
                        if references_lines[0][5:-1] == references_lines[index_line][len(branch_active) + 1: -1]:
                            references_lines[index_line] = f'{branch_active}={folder_name}\n'
                parent_folder_name = references_lines[0][5:-1]
                references_lines[0] = f'HEAD={folder_name}\n'
                reference_text = ''.join(references_lines)
            else:
                reference_text = f'HEAD={folder_name}\nmaster={folder_name}\n'
            with open(os.path.join(wit_path, '.wit', 'references.txt'), 'w+') as references_file:
                references_file.writelines(reference_text)
            file_name = folder_name + '.txt'
            date = datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y %Z')
            text = f"parent={parent_folder_name}\ndate={date}\nmessage=" + MESSAGE
        with open(os.path.join(wit_path, '.wit', 'images', file_name), 'w') as log_file:
            log_file.write(text)
    else:
        print("There is no .wit folder in here. You should run the 'init' command first")


def create_folder(wit_path):
    folder_name = ''.join(random.choice('1234567890abcdef') for _ in range(40))
    src = os.path.join(wit_path, '.wit', 'staging_area')
    dst = os.path.join(wit_path, '.wit', 'images', folder_name)
    shutil.copytree(src, dst, symlinks=True)
    return folder_name


def is_wit_in_here():
    # With help from 'Example 1' in https://www.programcreek.com/python/example/448/os.pardir
    # by awslabs
    current_path = os.getcwd()
    is_wit_root = False
    if os.path.exists(os.path.join(current_path, ".wit")):
        is_wit_root = True
    while not is_wit_root:
        parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
        if parent_path == current_path:
            raise ValueError("There is no '.wit' folder in here. You should run the 'init' command first or change the cwd")
        current_path = parent_path
        if os.path.exists(os.path.join(current_path, ".wit")):
            is_wit_root = True
    return current_path


def status():
    wit_path = is_wit_in_here()
    if wit_path:
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
            present_commit_id = references_file.readline()[5:-1]
        dcmp = dircmp(os.path.join(wit_path, ".wit", "images", present_commit_id), os.path.join(wit_path, ".wit", 'staging_area')) 
        status_dict = status_files(dcmp)
        dcmp = dircmp(wit_path, os.path.join(wit_path, ".wit", 'staging_area'), ignore=['.wit']) 
        status_dict = status_files(dcmp)
        print(f"""
        Present commit_id: {present_commit_id}
        Changes to be committed: {status_dict['Changes to be committed']}
        Changes not staged for commit: {status_dict['Changes not staged for commit']}
        Untracked files: {status_dict['Untracked files']}
        """)
        return status_dict


def status_files(dcmp):
    changes_not_staged_for_commit = list(dcmp.diff_files)
    untracked_files = list(dcmp.left_only)
    Changes_to_be_committed = list(dcmp.right_only)
    for sub_dcmp in dcmp.subdirs.values():
        status_files(sub_dcmp)
    status_dict = {'Changes not staged for commit': changes_not_staged_for_commit, 'Untracked files': untracked_files, 'Changes to be committed': Changes_to_be_committed}
    return status_dict


def checkout(commit_id):
    wit_path = is_wit_in_here()
    if wit_path:
        new_activated = ''
        status_dict = status()
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
            branch_commit_id = references_file.readlines()
        for branch_name in branch_commit_id:
            if commit_id == branch_name[: len(commit_id)]:
                new_activated = commit_id
                commit_id = branch_name[len(commit_id) + 1: -1]
        with open(os.path.join(wit_path, '.wit', 'activated.txt'), 'w+') as activated_file:
            activated_file.write(new_activated)
        if len(status_dict['Changes to be committed']) < 1 or len(status_dict['Changes not staged for commit']) < 1:
            src = os.path.join(wit_path, '.wit', 'images', commit_id)
            dst = wit_path
            distutils.dir_util.copy_tree(src, dst, preserve_mode=0)
        else:
            return "Checkout did not run"
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
            lines = references_file.readlines()
        lines[0] = f'HEAD={commit_id}\n'
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'w+') as references_file:
            references_file.writelines(lines)
        src = os.path.join(wit_path, '.wit', 'images', commit_id)
        dst = os.path.join(wit_path, '.wit', 'staging_area')
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)


def graph():
    wit_path = is_wit_in_here()
    if wit_path:
        our_graph = Digraph('G', filename='something', format='png', strict=True)
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
            lines = references_file.readlines()
        # making a list of all commit id in references
        parents_list = []
        for i in range(len(lines)):
            parents_list.append(lines[i].split('=')[1][: -1])
        for i in parents_list:
            parent_line = i + '.txt'
            while parent_line[: 4] != 'None':
                with open(os.path.join(wit_path, '.wit', 'images', parent_line), 'r') as images_file:
                    lines = images_file.readlines()
                new_parent_line = lines[0].split('=')[1][: 40]
                if new_parent_line[: 4] != 'None':
                    new_parent_line += '.txt'
                    our_graph.edge(parent_line[0:40], new_parent_line[0:40])
                    if ',' in lines[0]:
                        second_parent = lines[0].split('=')[1][41: -1]
                        our_graph.edge(parent_line[0:40], second_parent)
                parent_line = new_parent_line
        our_graph.view()


def branch(NAME):
    wit_path = is_wit_in_here()
    if wit_path:
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
            lines = references_file.readlines()
        commit_id = lines[0][5:-1]
        lines[-1] = f'{lines[-1]}{NAME}={commit_id}\n'
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'w+') as references_file:
            references_file.writelines(lines)


def merge(BRANCH_NAME):
    wit_path = is_wit_in_here()
    if wit_path:
        head_list = []
        branch_list = []
        # making a list with all HEAD perants
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
            head_lines = references_file.readlines()
        head_commit_id = head_lines[0][5:-1] + '.txt'
        head_list.append(head_commit_id[0:40])
        while head_commit_id != 'None':
            with open(os.path.join(wit_path, '.wit', 'images', head_commit_id), 'r') as images_file:
                head_lines = images_file.readlines()
            new_parent_line = head_lines[0][7:-1]
            if new_parent_line != 'None':
                new_parent_line += '.txt'
                head_list.append(new_parent_line[0:40])
            head_commit_id = new_parent_line
        # making a list with all BRANCH_NAME perants
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
            branch_lines = references_file.readlines()
        for branch_name in branch_lines:
            if BRANCH_NAME == branch_name[: len(BRANCH_NAME)]:
                branch_commitid = branch_name[len(BRANCH_NAME) + 1: -1]
                head_commit_id = branch_commitid + '.txt'
        branch_list.append(head_commit_id[0:40])
        while head_commit_id != 'None':
            with open(os.path.join(wit_path, '.wit', 'images', head_commit_id), 'r') as images_file:
                head_lines = images_file.readlines()
            new_parent_line = head_lines[0][7:-1]
            if new_parent_line != 'None':
                new_parent_line += '.txt'
                branch_list.append(new_parent_line[0:40])
            head_commit_id = new_parent_line
        # finding common parent
        common_parent = [com_par for com_par in head_list if com_par in branch_list][0]
        # finding the files that have been changed in BRANCH_NAME since common_parent
        print(f"common_parent: {common_parent}")
        print(f"branch_commitid: {branch_commitid}")
        dcmp = dircmp(os.path.join(wit_path, ".wit", "images", common_parent), os.path.join(wit_path, ".wit", 'images', branch_commitid))
        differe_files, new_files = find_differences(dcmp)
        # copy the different files to staging area
        for branch_item in differe_files:
            add(branch_item)
        for branch_item in new_files:
            add(branch_item)
        # add in commit - two parents
        commit(f'Merge branch: {BRANCH_NAME}')
#        commit('one')
        with open(os.path.join(wit_path, '.wit', 'references.txt'), 'r') as references_file:
            head_lines = references_file.readlines()
        head_commit_id = head_lines[0][5:-1] + '.txt'
        with open(os.path.join(wit_path, '.wit', 'images', head_commit_id), 'r') as images_file:
            head_lines = images_file.readlines()
        new_parent_line = head_lines[0][:-1] + ',' + branch_commitid + '\n'
        head_lines[0] = new_parent_line
        with open(os.path.join(wit_path, '.wit', 'images', head_commit_id), 'w') as log_file:
            log_file.writelines(head_lines)


def find_differences(dcmp):
    differ_files = list(dcmp.diff_files)
    new_files = list(dcmp.right_only)
    for sub_dcmp in dcmp.subdirs.values():
        find_differences(sub_dcmp)
    return differ_files, new_files


if __name__ == "__main__":
    path = None
    if len(sys.argv) == 3:
        if sys.argv[1] == 'add':
            add(sys.argv[2])
        elif sys.argv[1] == 'commit':
            commit(sys.argv[2])
        elif sys.argv[1] == 'checkout':
            checkout(sys.argv[2])
        elif sys.argv[1] == 'branch':
            branch(sys.argv[2])
        elif sys.argv[1] == 'merge':
            merge(sys.argv[2])
    elif len(sys.argv) == 2:
        if sys.argv[1] == 'init':
            init()
        elif sys.argv[1] == 'status':
            status()
        elif sys.argv[1] == 'graph':
            graph()
    else:
        print("Wrong command, please try again")