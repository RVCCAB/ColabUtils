import os
import shutil
import hashlib
import time

LOGS_FOLDER = '/content/RVCCAB/logs'
WEIGHTS_FOLDER = '/content/RVCCAB/weights'
GOOGLE_DRIVE_PATH = '/content/drive/MyDrive/RVC_Backup'

def import_google_drive_backup():
    print("Google Drive yedeği yükleniyor...")
    GOOGLE_DRIVE_PATH = '/content/drive/MyDrive/RVC_Backup' # change this to your Google Drive path
    LOGS_FOLDER = '/content/RVCCAB/logs'
    WEIGHTS_FOLDER = '/content/RVCCAB/weights'
    weights_exist = False
    for root, dirs, files in os.walk(GOOGLE_DRIVE_PATH):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.isfile(filepath) and not filepath.startswith(os.path.join(GOOGLE_DRIVE_PATH, 'weights')):
                backup_filepath = os.path.join(LOGS_FOLDER, os.path.relpath(filepath, GOOGLE_DRIVE_PATH))
                backup_folderpath = os.path.dirname(backup_filepath)
                if not os.path.exists(backup_folderpath):
                    os.makedirs(backup_folderpath)
                    print(f'Yedekleme klasörü oluşturuldu: {backup_folderpath}', flush=True)
                shutil.copy2(filepath, backup_filepath) # copy file with metadata
                print(f'Google Drive yedeğinden içeri aktarıldı: {filename}')
            elif filepath.startswith(os.path.join(GOOGLE_DRIVE_PATH, 'weights')) and filename.endswith('.pth'):
                weights_exist = True
                weights_filepath = os.path.join(WEIGHTS_FOLDER, os.path.relpath(filepath, os.path.join(GOOGLE_DRIVE_PATH, 'weights')))
                weights_folderpath = os.path.dirname(weights_filepath)
                if not os.path.exists(weights_folderpath):
                    os.makedirs(weights_folderpath)
                    print(f'Weights klasörü oluşturuldu: {weights_folderpath}', flush=True)
                shutil.copy2(filepath, weights_filepath) # copy file with metadata
                print(f'Weights klasöründen içeri aktarıldı: {filename}')
    if weights_exist:
        print("Google Drive'da bulunan Weights klasöründen içeri aktarıldı.")
    else:
        print("Google Drive'da weights yedeği bulamadık.")
    print("Google Drive içeri aktarması tamamlandı.")

def get_md5_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def copy_weights_folder_to_drive():
    destination_folder = os.path.join(GOOGLE_DRIVE_PATH, 'weights')
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    num_copied = 0
    for filename in os.listdir(WEIGHTS_FOLDER):
        if filename.endswith('.pth'):
            source_file = os.path.join(WEIGHTS_FOLDER, filename)
            destination_file = os.path.join(destination_folder, filename)
            if not os.path.exists(destination_file):
                shutil.copy2(source_file, destination_file)
                num_copied += 1
                print(f"{filename} adlı dosya Google Drive'a kopyalandı.")

    if num_copied == 0:
        print("Kopyalanması gereken yeni bir model yok.")
    else:
        print(f"{num_copied} adet dosya Google Drive'a yedeklendi.")

def backup_files():
    print("\n Yedekleme döngüsü başlatılıyor...")
    last_backup_timestamps_path = os.path.join(LOGS_FOLDER, 'last_backup_timestamps.txt')
    fully_updated = False 
    try:
        with open(last_backup_timestamps_path, 'r') as f:
            last_backup_timestamps = dict(line.strip().split(':') for line in f)
    except:
        last_backup_timestamps = {}
    while True:
        updated = False # flag to check if any files were updated
        for root, dirs, files in os.walk(LOGS_FOLDER):
            for filename in files:
                if filename != 'last_backup_timestamps.txt':
                    filepath = os.path.join(root, filename)
                    if os.path.isfile(filepath):
                        backup_filepath = os.path.join(GOOGLE_DRIVE_PATH, os.path.relpath(filepath, LOGS_FOLDER))
                        backup_folderpath = os.path.dirname(backup_filepath)
                        if not os.path.exists(backup_folderpath):
                            os.makedirs(backup_folderpath)
                            print(f'Created backup folder: {backup_folderpath}', flush=True)
                        # check if file has changed since last backup
                        last_backup_timestamp = last_backup_timestamps.get(filepath)
                        current_timestamp = os.path.getmtime(filepath)
                        if last_backup_timestamp is None or float(last_backup_timestamp) < current_timestamp:
                            shutil.copy2(filepath, backup_filepath) # copy file with metadata
                            last_backup_timestamps[filepath] = str(current_timestamp) # update last backup timestamp
                            if last_backup_timestamp is None:
                                print(f'Dosya yedeklendi: {filename}')
                            else:
                                print(f'Yedeklenen dosya güncellendi: {filename}')
                            updated = True
                            fully_updated = False  # if a file is updated, all files are not up to date
        # check if any files were deleted in Colab and delete them from the backup drive
        for filepath in list(last_backup_timestamps.keys()):
            if not os.path.exists(filepath):
                backup_filepath = os.path.join(GOOGLE_DRIVE_PATH, os.path.relpath(filepath, LOGS_FOLDER))
                if os.path.exists(backup_filepath):
                    os.remove(backup_filepath)
                    print(f'Dosya silindi: {filepath}')
                del last_backup_timestamps[filepath]
                updated = True
                fully_updated = False  # if a file is deleted, all files are not up to date
        if not updated and not fully_updated:
            print("Tüm dosyalar güncel.")
            fully_updated = True  # if all files are up to date, set the boolean to True
            copy_weights_folder_to_drive()
            sleep_time = 15
        else:
            sleep_time = 0.1
        with open(last_backup_timestamps_path, 'w') as f:
            for filepath, timestamp in last_backup_timestamps.items():
                f.write(f'{filepath}:{timestamp}\n')
        time.sleep(sleep_time) # wait for 15 seconds before checking again, or 1s if not fully up to date to speed up backups