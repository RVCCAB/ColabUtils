import os
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm.notebook import tqdm
from pathlib import Path
import requests

def run_script():
    def run_cmd(cmd):
        process = subprocess.run(cmd, shell=True, check=True, text=True)
        return process.stdout

    # Change the current directory to /content/
    os.chdir('/content/')
    print("/content klasörüne geçildi.")

    # Define the repo path
    repo_path = '/content/RVCCAB'

    def copy_all_files_in_directory(src_dir, dest_dir):
        # Iterate over all files in source directory
        for item in Path(src_dir).glob('*'):
            if item.is_file():
                # Copy each file to destination directory
                shutil.copy(item, dest_dir)
            else:
                # If it's a directory, make a new directory in the destination and copy the files recursively
                new_dest = Path(dest_dir) / item.name
                new_dest.mkdir(exist_ok=True)
                copy_all_files_in_directory(str(item), str(new_dest))

    def clone_and_copy_repo(repo_path):
        # New repository link
        new_repo_link = "https://github.com/RVCCAB/RVCCAB-RVC.git"
        # Temporary path to clone the repository
        temp_repo_path = "/content/temp_RVCCAB"
        # New folder name
        new_folder_name = "temp_RVCCAB"

        # Clone the latest code from the new repository to a temporary location
        run_cmd(f"git clone {new_repo_link} {temp_repo_path}")
        os.chdir(temp_repo_path)

        # Copy all files from the cloned repository to the existing path
        copy_all_files_in_directory(temp_repo_path, repo_path)
        print(f"Tüm dosyalar {new_folder_name} GitHub'dan taşındı.")

        # Change working directory back to /content/
        os.chdir('/content/')
        print("/content/")
        
        # Remove the temporary cloned repository
        shutil.rmtree(temp_repo_path)

    # Call the function
    clone_and_copy_repo(repo_path)

    # Download the credentials file for RVC archive sheet
    os.makedirs('/content/RVCCAB/stats/', exist_ok=True)
    run_cmd("wget -q https://cdn.discordapp.com/attachments/945486970883285045/1114717554481569802/peppy-generator-388800-07722f17a188.json -O /content/RVCCAB/stats/peppy-generator-388800-07722f17a188.json")

    # Forcefully delete any existing torchcrepe dependencies downloaded from an earlier run just in case
    shutil.rmtree('/content/RVCCAB/torchcrepe', ignore_errors=True)
    shutil.rmtree('/content/torchcrepe', ignore_errors=True)

    # Download the torchcrepe folder from the maxrmorrison/torchcrepe repository
    run_cmd("git clone https://github.com/maxrmorrison/torchcrepe.git")
    shutil.move('/content/torchcrepe/torchcrepe', '/content/RVCCAB/')
    shutil.rmtree('/content/torchcrepe', ignore_errors=True)  # Delete the torchcrepe repository folder

    # Change the current directory to /content/RVCCAB
    os.chdir('/content/RVCCAB')
    os.makedirs('pretrained', exist_ok=True)
    os.makedirs('uvr5_weights', exist_ok=True)

def download_file(url, filepath):
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(filepath, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

def download_pretrained_models():
    pretrained_models = {
        "pretrained": [
            "D40k.pth",
            "G40k.pth",
            "f0D40k.pth",
            "f0G40k.pth"
        ],
        "pretrained_v2": [
            "D40k.pth",
            "G40k.pth",
            "f0D40k.pth",
            "f0G40k.pth",
            "f0G48k.pth",
            "f0D48k.pth"
        ]
    }

    base_url = "https://RVCCABwebui.s3.eu-central-1.amazonaws.com/rvcwebui/"
    base_path = "/content/RVCCAB/"

    # Calculate total number of files to download
    total_files = sum(len(files) for files in pretrained_models.values()) + 1  # +1 for hubert_base.pt

    with tqdm(total=total_files, desc="Dosyalar indiriliyor...") as pbar:
        for folder, models in pretrained_models.items():
            folder_path = os.path.join(base_path, folder)
            os.makedirs(folder_path, exist_ok=True)
            for model in models:
                url = base_url + folder + "/" + model
                filepath = os.path.join(folder_path, model)
                download_file(url, filepath)
                pbar.update()

        # Download hubert_base.pt to the base path
        hubert_url = base_url + "hubert_base.pt"
        print(hubert_url)
        hubert_filepath = os.path.join(base_path, "hubert_base.pt")
        download_file(hubert_url, hubert_filepath)
        
        rmvpe_url = base_url + "rmvpe.pt"
        rmvpe_filepath = os.path.join(base_path, "rmvpe.pt")
        print(rmvpe_url)

        download_file(rmvpe_url, rmvpe_filepath)
        

        pbar.update()

def clone_repository(run_download):
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(run_script)
        if run_download:
            executor.submit(download_pretrained_models)