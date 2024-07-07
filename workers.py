from pathlib import Path
from config import MainConfig
from confz import BaseConfig, FileSource
from datetime import datetime, timedelta
import os
import torch
import numpy as np
from tqdm import tqdm
from utils import load_detector, load_classificator, open_mapping, extract_crops
from itertools import repeat
from PIL import Image
from PIL.ExifTags import TAGS
import pandas as pd

def get_exif(filename):
    image = Image.open(filename)
    image.verify()
    return image._getexif()


def get_labeled_exif(exif):
    labeled = {}
    for (key, val) in exif.items():
        if key in TAGS:
            labeled[TAGS[key]] = val

    return labeled


def get_datetime(labeled_exif):
    if "DateTimeOriginal" in labeled_exif:
        return labeled_exif["DateTimeOriginal"]
    elif "DateTime" in labeled_exif:
        return labeled_exif["DateTime"]
    else:
        return None


def model_worker(data_folder):
    # Load main config
    main_config = MainConfig(config_sources=FileSource(file="config.yml"))
    device = main_config.device

    # Separate main config
    detector_config = main_config.detector
    classificator_config = main_config.classificator

    # Load models
    detector = load_detector(detector_config).to(device)
    classificator = load_classificator(classificator_config).to(device)
    mapping = open_mapping(path_mapping=main_config.mapping)

    cameras = list()
    category = os.listdir(data_folder)

    try:
        category.remove('.DS_Store')
    except:
        pass

    category = [int(elt) for elt in category]
    category.sort()
    category = [str(elt) for elt in category]

    df = pd.DataFrame(columns=['folder_name', 'class', 'date_registration_start', 'date_registration_end', 'count'])


    for folder in category:
        print(folder)
        folderpath = os.path.join(data_folder, str(folder))
        filelist = os.listdir(folderpath)
        for i in range(len(filelist)):
            filelist[i] = os.path.join(folderpath, filelist[i])
        cameras.append([folder, filelist])

    for i, camera in tqdm(cameras):

        photos = classify(classificator, classificator_config, detector, detector_config, device, camera, mapping)
        _class = []
        date_registration = datetime(2019,12,31).min
        date_registration_end = date_registration
        max_count = 0
        animals_count = {}

        for photo in photos:
            filename = f'{data_folder}\\{str(i)}\\{photo[0]}'
            exif = get_exif(filename)
            labeled = get_labeled_exif(exif)
            photo_datetime = get_datetime(labeled)
            photo_datetime = datetime.strptime(photo_datetime, '%Y:%m:%d %H:%M:%S')
            # print(filename, photo_datetime)
            _, count, animals = photo[0], photo[1], photo[2]
            animals = list(filter(lambda animal: animal != 'Empty', animals))

            # print(count, animals)
            for animal in animals:
                if animal != 'Empty':
                    animals_count.setdefault(animal, 0)
                    animals_count[animal] += 1

            # print(max_count)
            if date_registration == datetime(2019,12,31).min:
                if count != 0:
                    date_registration = photo_datetime
                    date_registration_end = photo_datetime
                    max_count = count
                    # print(max_count)

            elif photo_datetime-date_registration_end < timedelta(minutes=30):
                if count != 0:
                    date_registration_end = photo_datetime
                    max_count = max(max_count,count)
                    # print(max_count)

            else:
                if max_count > 0:
                    df.loc[len(df.index)] = [i, max(animals_count, key=animals_count.get), date_registration,
                                             date_registration_end,
                                             max_count if max_count < 5 else 5]
                # print(i, max(animals_count, key=animals_count.get), date_registration, date_registration_end,
                #       max_count if max_count < 5 else 5)

                date_registration = photo_datetime
                date_registration_end = photo_datetime
                max_count = count
                animals_count = {}
                for animal in animals:
                    animals_count.setdefault(animal, 0)
                    animals_count[animal] += 1
                # print(max_count)
        if max_count>0:
            df.loc[len(df.index)] = [i, max(animals_count, key=animals_count.get), date_registration, date_registration_end,
                  max_count if max_count < 5 else 5]

            # print(i, max(animals_count, key=animals_count.get), date_registration, date_registration_end,
            #       max_count if max_count < 5 else 5)

        # print(len(camera))
    #df.to_csv('subs.csv')
    return df

def save_df(df, path):
    df.to_csv(os.path.join(path,'subs.csv'), index=False)

def classify(classificator, classificator_config, detector, detector_config, device, pathes_to_imgs, mapping):

    if len(pathes_to_imgs):

        list_predictions = []

        num_packages_det = np.ceil(len(pathes_to_imgs) / detector_config.batch_size).astype(np.int32)
        with torch.no_grad():
            for i in range(num_packages_det):
                # Inference detector
                batch_images_det = pathes_to_imgs[detector_config.batch_size * i:
                                                  detector_config.batch_size * (1 + i)]
                results_det = detector(batch_images_det,
                                       iou=detector_config.iou,
                                       conf=detector_config.conf,
                                       imgsz=detector_config.imgsz,
                                       verbose=False,
                                       device=device)

                if len(results_det) > 0:
                    # Extract crop by bboxes
                    dict_crops = extract_crops(results_det, config=classificator_config)

                    # Inference classificator
                    for img_name, batch_images_cls in dict_crops.items():
                        # if len(batch_images_cls) > classificator_config.batch_size:
                        num_packages_cls = np.ceil(len(batch_images_cls) / classificator_config.batch_size).astype(
                            np.int32)
                        for j in range(num_packages_cls):
                            batch_images_cls = batch_images_cls[classificator_config.batch_size * j:
                                                                classificator_config.batch_size * (1 + j)]
                            logits = classificator(batch_images_cls.to(device))
                            probabilities = torch.nn.functional.softmax(logits, dim=1)
                            top_p, top_class_idx = probabilities.topk(1, dim=1)

                            # Locate torch Tensors to cpu and convert to numpy
                            top_class_idx = top_class_idx.cpu().numpy().ravel()
                            
                            class_names = [mapping[top_class_idx[idx]] for idx, _ in enumerate(batch_images_cls)]

                            list_predictions.extend([[img_name, len(class_names), class_names]])
                else:
                    list_predictions.extend([img_name, 0, []])
    return list_predictions