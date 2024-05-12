from encoding import *
import os
import time


def time_loading(paths):
    for path in paths:
        start = time.time()
        image = Decoder.load_from(path)
        end = time.time()
        vitesse = (end - start) * 1000
        print(f"{path} >> {vitesse} ms")


def time_encoding(base_path, v3=True):
    print(base_path)
    image_test = Decoder.load_from(base_path)

    paths = ["1", "2", "4"]
    if v3:
        paths += ["3rle", "3norle"]
    for path in paths:
        version = int(path[0])
        if version in (1, 2, 4):
            start = time.time()
            Encoder(image_test, version).save_to(path + ".ulbmp")
            end = time.time()
        else:
            RLE = True if path[1:] == "rle" else False
            start = time.time()
            Encoder(image_test, 3, depth=8, rle=RLE).save_to(path + ".ulbmp")
            end = time.time()
        vitesse = (end - start)
        print(f"{path} >> {vitesse} s")
        os.remove(path + ".ulbmp")


def compression_ratio(paths):
    size = os.path.getsize(paths[0])
    print("base size (v1) >> ", size, "\n")
    for path in paths[1:]:
        print(f"{path} : size >> {os.path.getsize(path)} | ratio >> {(size / os.path.getsize(path)) * 100}")


checkers = ["checkers.ulbmp", "checkers2.ulbmp", "checkers3_1.ulbmp", "checkers3_2.ulbmp", "checkers3_4.ulbmp",
            "checkers3_8_norle.ulbmp", "checkers3_8_rle.ulbmp", "checkers4.ulbmp"]
airplanes = ["airplane.ulbmp", "airplane2.ulbmp", "airplane4.ulbmp"]
mercures = ["mercure.ulbmp", "mercure2.ulbmp", "mercure3_8_no_rle.ulbmp", "mercure3_8_rle.ulbmp", "mercure4.ulbmp"]
monkeys = ["monkey.ulbmp", "monkey2.ulbmp", "monkey3_8_norle.ulbmp", "monkey3_8_rle.ulbmp", "monkey4.ulbmp"]
