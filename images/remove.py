import os
directory_path = '/home/cena/apps/Upwork/Resume/images'
for filename in os.listdir(directory_path):
    if filename.lower().endswith('.jpeg') or filename.lower().endswith('.png') or filename.lower().endswith('.webp'):
        os.remove(f'{directory_path}/{filename}')
