"""
NOM : Saou
PRÉNOM : Ayman
SECTION : B1-INFO
MATRICULE : 000593526
"""

from image import Image
from pixel import Pixel


class Encoder:
    def __init__(self, img: Image, version_format=1, **kwargs):
        self.image = img
        self.largeur = img.get_width()
        self.hauteur = img.get_height()
        self.version = version_format
        if self.version == 3 and ('rle' not in kwargs or 'depth' not in kwargs):
            raise ValueError
        self.profondeur = kwargs.get('depth')
        self.rle = kwargs.get('rle')
        self.nombre_pixels = self.largeur * self.hauteur

    def save_to(self, path: str) -> None:
        """
        Ouvre le fichier donné par le path en parametre, compose le header en bytes à partir des donnees de l'image,
        puis appelle differentes fonctions pour composer la suite de bytes representant les pixels en fonction de
        la version, écrit le header et les bytes representant les pixels dans le fichier.
        """
        with open(path, 'wb') as file:
            ulbmp_ascii = b'ULBMP'
            version = self.version.to_bytes(1)
            bytes_header = (12).to_bytes(2, 'little')
            largeur = self.largeur.to_bytes(2, 'little')
            hauteur = self.hauteur.to_bytes(2, 'little')
            header = ulbmp_ascii + version + bytes_header + largeur + hauteur
            if self.version == 1:
                pixels_to_encode = self.encode_pixels_v1()
            elif self.version == 2:
                pixels_to_encode = self.encode_pixels_v2()
            elif self.version == 3:
                profondeur = self.profondeur.to_bytes(1)
                rle = b'\x01' if self.rle and self.profondeur in (8, 24) else b'\x00'
                bytes_header = (14).to_bytes(2, 'little')
                header += profondeur + rle
                pixels_to_encode, header = self.encode_pixels_v3(header, bytes_header, rle)
            elif self.version == 4:
                pixels_to_encode = self.encode_pixels_v4()
            file.write(header + pixels_to_encode)

    def encode_pixels_v1(self):
        """
        Encodage de la version 1 du format ULBMP, parcourt la liste de pixels de l'image et encode l'intensité des
        canaux RGB sur un byte chacun. Return les bytes associés aux pixels.
        """
        pixels_to_encode = b''
        liste_pixels = self.image.get_pixels()
        for pixel in liste_pixels:
            pixels_to_encode += (pixel.get_red().to_bytes(1) + pixel.get_green().to_bytes(1) +
                                 pixel.get_blue().to_bytes(1))
        return pixels_to_encode

    def encode_pixels_v2(self):
        """
        Encodage de la version 2 du format ULBMP, parcourt la liste de pixels de l'image en comparant chaque pixel avec
        le precedent, si le pixel est le meme, continue de parcourir la liste et incremente la variable occurence,
        si occurrence est à 255 ou que le pixel est different du precedent, encode l'occurence sur un byte suivi de
        l'intensité des canaux RGB du pixel répeté sur un byte chacun. Return les bytes associés aux pixels.
        """
        pixels_to_encode = b''
        liste_pixels = self.image.get_pixels()
        pixel_prec = liste_pixels[0]
        occurence = 1
        compteur_pixels = 1
        nombre_pixels = len(liste_pixels)
        for pixel in liste_pixels[1:]:
            compteur_pixels += 1
            if pixel == pixel_prec:
                occurence += 1
                if occurence == 255:
                    pixels_to_encode += (occurence.to_bytes(1) + pixel_prec.get_red().to_bytes(1) +
                                         pixel_prec.get_green().to_bytes(1) + pixel_prec.get_blue().to_bytes(1))
                    occurence = 0
            if pixel != pixel_prec or nombre_pixels == compteur_pixels:
                pixels_to_encode += (occurence.to_bytes(1) + pixel_prec.get_red().to_bytes(1) + pixel_prec.get_green()
                                     .to_bytes(1)
                                     + pixel_prec.get_blue().to_bytes(1))
                occurence = 1
                if nombre_pixels == compteur_pixels and pixel != pixel_prec:
                    pixels_to_encode += (occurence.to_bytes(1) + pixel.get_red().to_bytes(1) +
                                         pixel.get_green().to_bytes(1) + pixel.get_blue().to_bytes(1))
            pixel_prec = pixel
        return pixels_to_encode

    def encode_pixels_v3(self, header, bytes_header, rle):
        """
        Encodage de la version 3 du format ULBMP, prend le header en parametre pour modifier sa taille en fonction de
        la palette si la profondeur ≤ 8, dans le cas d'une profondeur 24, utilise l'encodage de la version 1 si le
        RLE n'est pas activé, et l'encodage de la version 2 s'il l'est, pour une profondeur de 8, si le RLE n'est pas
        activé parcourt la liste de pixels, et pour chaque pixel parcourt les clés et valeurs du dictionnaire de la
        palette, si le pixel est égal à la valeur, encode sa clé associée (indice) en bytes dans la suite de bytes,
        si le RLE est activé, utilise une derivée du code utilisé pour l'encodage de la version 2,
        pour les profondeurs 1, 2 et 4, parcourt la liste de pixels, initialise une liste d'indices vide, encode les
        indices lorsque qu'il y en a assez pour faire un byte ou qu'il n'y a plus de pixels à encoder, reinitialise la
        liste d'indices
        Return les pixels à encoder, et le header dans le cas ou il a été modifié si presence d'une palette.
        """
        liste_pixels = self.image.get_pixels()
        binary_palette, liste_palette = self.get_palette()
        pixels_to_encode = b''
        if self.profondeur != 24:
            bytes_header = (14 + (len(liste_palette) * 3)).to_bytes(2, 'little')
            header += binary_palette
        header = header[0:6] + bytes_header + header[8:]
        if rle == b'\x00':
            if self.profondeur == 24:
                pixels_to_encode = self.encode_pixels_v1()
            elif self.profondeur == 8:
                for pixel in liste_pixels:
                    indice_palette = self.get_indice_palette_from_pixel(liste_palette, pixel)
                    pixels_to_encode += int.to_bytes(indice_palette)
            elif self.profondeur in (1, 2, 4):
                nombre_pixels = len(liste_pixels)
                indices = []
                for pixel in liste_pixels:
                    indice_palette = self.get_indice_palette_from_pixel(liste_palette, pixel)
                    indices.append(indice_palette)
                    nombre_pixels -= 1
                    if len(indices) == (8 // self.profondeur) or nombre_pixels == 0:  # nombre d'indices suffisant
                        byte = 0
                        for i in indices:
                            byte = (byte << self.profondeur) | i
                        if len(indices) != (8 // self.profondeur):
                            # si on est rentré dans la condition parce que dernier pixel
                            byte = byte << ((8 // self.profondeur) - len(indices))
                        pixels_to_encode += int.to_bytes(byte)
                        indices = []
        elif rle == b'\x01':
            if self.profondeur == 24:
                pixels_to_encode = self.encode_pixels_v2()
            elif self.profondeur == 8:
                pixel_prec = liste_pixels[0]
                occurence = 1
                compteur_pixels = 1
                nombre_pixels = len(liste_pixels)
                for pixel in liste_pixels[1:]:
                    compteur_pixels += 1
                    if pixel == pixel_prec:
                        occurence += 1
                        if occurence == 255:
                            indice_palette = self.get_indice_palette_from_pixel(liste_palette, pixel_prec)
                            pixels_to_encode += occurence.to_bytes(1) + indice_palette.to_bytes(1)
                            occurence = 0
                    if pixel != pixel_prec or nombre_pixels == compteur_pixels:
                        indice_palette = self.get_indice_palette_from_pixel(liste_palette, pixel_prec)
                        pixels_to_encode += occurence.to_bytes(1) + indice_palette.to_bytes(1)
                        occurence = 1
                        if nombre_pixels == compteur_pixels and pixel != pixel_prec:
                            indice_palette = self.get_indice_palette_from_pixel(liste_palette, pixel)
                            pixels_to_encode += occurence.to_bytes(1) + indice_palette.to_bytes(1)
                    pixel_prec = pixel
        return pixels_to_encode, header

    def encode_pixels_v4(self):
        """
        Encodage de la version 4 du format ULBMP, initialise un pixel noir comme pixel precedent, parcourt la liste
        de pixels, calcule tous les deltas en fonction du pixel precedent, determine le type de bloc à encoder selon
        les deltas, pour chaque bloc ajoute le nombre nécessaire pour que l'intensité des canaux RGB reste entre les
        bornes 0 et 255, calcule les bytes à encoder puis les encode, definit le pixel comme pixel precedent a la fin
        de la boucle. Return les pixels à encoder.
        """
        pixels_to_encode = b''
        liste_pixels = self.image.get_pixels()
        pixel_prec = Pixel(0, 0, 0)
        for pixel in liste_pixels:
            delta_red, delta_green, delta_blue = Pixel.get_delta(pixel_prec, pixel)
            delta_rg, delta_bg = delta_red - delta_green, delta_blue - delta_green
            delta_gr, delta_br = delta_green - delta_red, delta_blue - delta_red
            delta_rb, delta_gb = delta_red - delta_blue, delta_green - delta_blue
            diff = self.get_diff(delta_red, delta_green, delta_blue)
            if diff[0] == 'small':
                delta_red, delta_green, delta_blue = delta_red + 2, delta_green + 2, delta_blue + 2
                byte0 = (((delta_red << 2) | delta_green) << 2) | delta_blue
                pixels_to_encode += int.to_bytes(byte0)
            elif diff[0] == 'intermediate':
                delta_green, delta_rg, delta_bg = delta_green + 32, delta_rg + 8, delta_bg + 8
                byte0 = 64 | delta_green
                byte1 = (delta_rg << 4) | delta_bg
                pixels_to_encode += int.to_bytes(byte0) + int.to_bytes(byte1)
            elif diff[0] == 'big':
                if diff[1] == 'r':
                    byte0, byte1, byte2 = self.encode_big_diff(delta_red, delta_gr, delta_br, 128)
                    pixels_to_encode += byte0 + byte1 + byte2
                elif diff[1] == 'g':
                    byte0, byte1, byte2 = self.encode_big_diff(delta_green, delta_rg, delta_bg, 144)
                    pixels_to_encode += byte0 + byte1 + byte2
                elif diff[1] == 'b':
                    byte0, byte1, byte2 = self.encode_big_diff(delta_blue, delta_rb, delta_gb, 160)
                    pixels_to_encode += byte0 + byte1 + byte2
            elif diff[0] == 'new':
                pixels_to_encode += (int.to_bytes(255) + int.to_bytes(pixel.get_red()) + int.to_bytes(pixel.get_green())
                                     + int.to_bytes(pixel.get_blue()))
            pixel_prec = pixel
        return pixels_to_encode

    def get_palette(self):
        """
        Convertit la liste de pixels de l'image en un set pour conserver uniquement les elements uniques,
        puis convertit ce meme set en une liste pour profiter de l'usage des indices, pour chaque pixel dans cette
        liste, convertit l'intensité de ses canaux RGB en bytes et l'ajoute dans 'palette_binaire' qui sera ajoutée
        au header.
        """
        liste_palette = list(set(self.image.get_pixels()))
        palette_binaire = b''
        for pixel in liste_palette:
            palette_binaire += pixel.get_red().to_bytes()
            palette_binaire += pixel.get_green().to_bytes()
            palette_binaire += pixel.get_blue().to_bytes()
        return palette_binaire, liste_palette

    @staticmethod
    def get_indice_palette_from_pixel(palette, pixel_to_get):
        """
        Prend la representation en dictionnaire de la palette et un pixel en parametre, return l'indice associé a ce
        pixel dans le dictionnaire de la palette.
        """
        for indice, pixel in enumerate(palette):
            if pixel == pixel_to_get:
                return indice

    @staticmethod
    def get_diff(delta_r, delta_g, delta_b):
        """
        Prend en parametre la difference d'intensité des canaux RGB entre deux pixels et return une liste diff qui
        contient le type de blocs en indice 0, et le type de couleur en indice 1 si le bloc est un bloc BIG_DIFF.
        """
        diff = ['', '']
        if -2 <= delta_r <= 1 and -2 <= delta_g <= 1 and -2 <= delta_b <= 1:
            diff[0] = 'small'
        elif -32 <= delta_g <= 31 and (-8 <= (delta_r - delta_g) <= 7 and -8 <= (delta_b - delta_g) <= 7):
            diff[0] = 'intermediate'
        elif -128 <= delta_r <= 127 and (-32 <= (delta_g - delta_r) <= 31 and -32 <= (delta_b - delta_r) <= 31):
            diff[0], diff[1] = 'big', 'r'
        elif -128 <= delta_g <= 127 and (-32 <= (delta_r - delta_g) <= 31 and -32 <= (delta_b - delta_g) <= 31):
            diff[0], diff[1] = 'big', 'g'
        elif -128 <= delta_b <= 127 and (-32 <= (delta_r - delta_b) <= 31 and -32 <= (delta_g - delta_b) <= 31):
            diff[0], diff[1] = 'big', 'b'
        else:
            diff[0] = 'new'
        return diff

    @staticmethod
    def encode_big_diff(delta1, delta2, delta3, signature):
        """
        Fonction qui generalise l'encodage d'un bloc 'BIG_DIFF', prend en parametre les 3 deltas et les 4 bits
        permettant d'identifier le type de bloc, return les 3 bytes à encoder du bloc.
        """
        delta1, delta2, delta3 = delta1 + 128, delta2 + 32, delta3 + 32
        byte0 = signature + (delta1 >> 4)
        byte1 = ((delta1 & 0b1111) << 4) | (delta2 >> 2)
        byte2 = ((delta2 & 0b11) << 6) | delta3
        return int.to_bytes(byte0), int.to_bytes(byte1), int.to_bytes(byte2)


class Decoder:
    @staticmethod
    def load_from(path: str):
        """
        Lit le contenu dans le fichier donné par le path en parametre recupere la largeur et la hauteur de l'image,
        delimite la partie liée a la palette et celle aux pixels pour la version 3 du format, initialise une liste de
        pixels vide, construit la liste de pixels selon la version du format et return l'image definie par la largeur,
        la hauteur et la liste de pixels.
        """
        with open(path, 'rb') as file:
            data = file.read()
            version = data[5]
            header = data[:6]
            width_and_height = data[8:12]
            expected_header = bytes.fromhex(f'554c424d500{version}')
            if header != expected_header or len(width_and_height) != 4:
                raise Exception('Incorrect format')
            largeur = int.from_bytes(width_and_height[0:2], 'little')
            hauteur = int.from_bytes(width_and_height[2:], 'little')
            pixels_expected = largeur * hauteur
            bytes_pixels = data[12:]
            liste_pixels = []
            if version == 1:
                liste_pixels = decode_pixels_v1(bytes_pixels, liste_pixels)
            elif version == 2:
                liste_pixels = decode_pixels_v2(bytes_pixels, liste_pixels)
            elif version == 3:
                header_size = int.from_bytes(data[6:8], 'little')
                palette = data[14:header_size]
                pixels = data[header_size:]
                depth = data[12]
                rle = data[13] == 1
                liste_pixels = decode_pixels_v3(palette, pixels, liste_pixels, pixels_expected, depth, rle)
            elif version == 4:
                liste_pixels = decode_pixels_v4(bytes_pixels, liste_pixels)
            image = Image(largeur, hauteur, liste_pixels)
            return image


def decode_pixels_v1(bytes_pixels: bytes, liste_pixels: list):
    """
    Decodage de la version 1 du format ULBMP, parcourt la suite de bytes associés aux pixels 3 par 3, associe le
    premier, deuxieme et troisieme byte aux intensités des canaux rouge, vert et bleu respectivement, ajoute dans la
    liste donnée en parametre un Pixel composé des valeurs RGB. Return la liste
    """
    for i in range(0, len(bytes_pixels), 3):
        temp_pixel = bytes_pixels[i:i + 3]
        red, blue, green = temp_pixel[0], temp_pixel[1], temp_pixel[2]
        liste_pixels.append(Pixel(red, blue, green))
    return liste_pixels


def decode_pixels_v2(bytes_pixels: bytes, liste_pixels: list):
    """
    Decodage de la version 2 du format ULBMP, parcourt la suite de bytes associés aux pixels 4 par 4, associe le
    premier byte au nombre de fois qu'il faut multiplier le pixel, et le deuxieme, troisieme et quatrieme byte aux
    intensités des canaux rouge, vert et bleu respectivement, ajoute dans la liste donnée en parametre un Pixel composé
    des valeurs RGB multiplié par le nombre du premier byte. Return la liste
    """
    for i in range(0, len(bytes_pixels), 4):
        temp_pixel = bytes_pixels[i:i + 4]
        red, blue, green = temp_pixel[1], temp_pixel[2], temp_pixel[3]
        liste_pixels += temp_pixel[0] * [Pixel(red, blue, green)]
    return liste_pixels


def decode_pixels_v3(palette: bytes, bytes_pixels: bytes, liste_pixels: list, pixels_expected: int, depth: int,
                     rle=False):
    """
    Decodage de la version 3 du format ULBMP, prend en parametre les suites de bytes composant la palette et les pixels,
    une liste vide, le nombre de pixels attendus, la profondeur et le RLE (sur False par defaut), utilise le decodage de
    la version 1 pour obtenir une palette sous forme de liste, dans le cas d'une profondeur 24, utilise le decodage de
    la version 1 si le RLE n'est pas activé, et le decodage de la version 2 s'il l'est, dans le cas d'une profondeur de
    8, si le RLE n'est pas activé, parcourt la suite bytes qui composent les indices referencant la palette, et ajoute
    dans la liste de pixels le pixel correspondant à l'indice dans la palette sous forme de liste construite plus tot,
    si le RLE est activé, parcourt la suite de bytes 2 par 2, effectue le meme traitement pour le deuxieme byte, mais
    multiplié par le nombre donné dans le premier byte, pour les profondeurs ≤ 4, appelle la fonction palette_from_bits
    pour construire la liste de pixels, return la liste de pixels.
    """
    liste_palette = []
    liste_palette = decode_pixels_v1(palette, liste_palette)
    if depth == 24:
        if not rle:
            liste_pixels = decode_pixels_v1(bytes_pixels, liste_pixels)
        elif rle:
            liste_pixels = decode_pixels_v2(bytes_pixels, liste_pixels)
    if depth == 8:
        if not rle:
            for indice_palette in bytes_pixels:
                pixel_to_add = liste_palette[indice_palette]
                liste_pixels.append(pixel_to_add)
        elif rle:
            for i in range(0, len(bytes_pixels), 2):
                temp_pixel = bytes_pixels[i:i + 2]
                number_of_pixels, indice_palette = temp_pixel[0], temp_pixel[1]
                pixel_to_add = liste_palette[indice_palette]
                liste_pixels += number_of_pixels * [pixel_to_add]
    elif depth in (1, 2, 4):
        liste_pixels = decode_depth_under_8(bytes_pixels, depth, liste_pixels, liste_palette, pixels_expected)
    return liste_pixels


def decode_depth_under_8(bytes_pixels, depth, liste_pixels, liste_palette, pixels_expected):
    """
    Fonction appelée lors du decodage de la version 3 lorsque la profondeur ≤ 4, prend en parametre la suite de byte
    representant les pixels, la profondeur, une liste de vide dans laquelle ajouter les pixels, la liste representant
    la palette, et le nombre de pixels attendus, parcourt la suite de bytes byte par byte, pour chaque byte,
    initialise une liste d'indices vides, verifie s'il reste des pixels à encoder dans l'image de sorte à ne pas
    encoder les bits de padding, si tel est le cas, isole l'indice en fonction de la profondeur et ajoute l'indice
    dans la liste. Parcourt les indices dans la liste 'indices_palette' pour ajouter les pixels associés dans
    'liste_pixels', retourne la liste de pixels.
    """
    nombre_pixels = 0
    for byte in bytes_pixels:
        indices_palette = []
        for i in range(8 - depth, -1, -depth):
            nombre_pixels += 1
            if nombre_pixels <= pixels_expected:
                indice = (byte >> i) & ((2 ** depth) - 1)
                indices_palette.append(indice)
        for indice in indices_palette:
            liste_pixels += [liste_palette[indice]]
    return liste_pixels


def decode_pixels_v4(bytes_pixels: bytes, liste_pixels: list):
    """
    Decodage de la version 4 du format ULBMP, initialise un pixel noir comme pixel precedent pour les comparaisons,
    identifie le bloc à decoder selon les premiers bits de la suite de bytes, ajoute le pixel representé par le bloc
    et incremente i de sorte à parcourir la suite de bytes blocs par blocs. Retourne la liste de pixels.
    """
    i = 0
    pixel_prec = Pixel(0, 0, 0)
    while i < len(bytes_pixels):
        byte0 = bytes_pixels[i]
        if byte0 == 255:  # ULBMP_NEW_PIXEL
            r, g, b = bytes_pixels[i + 1], bytes_pixels[i + 2], bytes_pixels[i + 3]
            pixel_prec = Pixel(r, g, b)
            liste_pixels.append(pixel_prec)
            i += 4
        elif byte0 >> 6 == 0:  # ULBMP_SMALL_DIFF
            delta_r = ((byte0 >> 4) & 0b11) - 2
            delta_g = ((byte0 >> 2) & 0b11) - 2
            delta_b = (byte0 & 0b11) - 2
            liste_pixels, bytes_pixels, pixel_prec, i = decode_blocs(delta_r, delta_g, delta_b, pixel_prec,
                                                                     liste_pixels, bytes_pixels, i, 1)
        elif byte0 >> 6 == 1:  # ULBMP_INTERMEDIATE_DIFF
            delta_g = (byte0 & 0b111111) - 32
            delta_rg = (bytes_pixels[i + 1] >> 4) - 8
            delta_bg = (bytes_pixels[i + 1] & 0b1111) - 8
            delta_r, delta_b = delta_rg + delta_g, delta_bg + delta_g
            liste_pixels, bytes_pixels, pixel_prec, i = decode_blocs(delta_r, delta_g, delta_b, pixel_prec,
                                                                     liste_pixels, bytes_pixels, i, 2)
        elif byte0 >> 4 == 8:  # ULBMP_BIG_DIFF_R
            byte1, byte2 = bytes_pixels[i + 1], bytes_pixels[i + 2]
            delta_r = compose_byte(byte0, byte1, 4, 4) - 128
            delta_gr = compose_byte(byte1, byte2, 2, 6) - 32
            delta_br = (byte2 & 0b111111) - 32
            delta_g, delta_b = delta_gr + delta_r, delta_br + delta_r
            liste_pixels, bytes_pixels, pixel_prec, i = decode_blocs(delta_r, delta_g, delta_b, pixel_prec,
                                                                     liste_pixels, bytes_pixels, i, 3)
        elif byte0 >> 4 == 9:  # ULBMP_BIG_DIFF_G
            byte1, byte2 = bytes_pixels[i + 1], bytes_pixels[i + 2]
            delta_g = compose_byte(byte0, byte1, 4, 4) - 128
            delta_rg = compose_byte(byte1, byte2, 2, 6) - 32
            delta_bg = (byte2 & 0b111111) - 32
            delta_r, delta_b = delta_rg + delta_g, delta_bg + delta_g
            liste_pixels, bytes_pixels, pixel_prec, i = decode_blocs(delta_r, delta_g, delta_b, pixel_prec,
                                                                     liste_pixels, bytes_pixels, i, 3)
        elif byte0 >> 4 == 10:  # ULBMP_BIG_DIFF_B
            byte1, byte2 = bytes_pixels[i + 1], bytes_pixels[i + 2]
            delta_b = compose_byte(byte0, byte1, 4, 4) - 128
            delta_rb = compose_byte(byte1, byte2, 2, 6) - 32
            delta_gb = (byte2 & 0b111111) - 32
            delta_r, delta_g = delta_rb + delta_b, delta_gb + delta_b
            liste_pixels, bytes_pixels, pixel_prec, i = decode_blocs(delta_r, delta_g, delta_b, pixel_prec,
                                                                     liste_pixels, bytes_pixels, i, 3)
    return liste_pixels


def decode_blocs(delta_r, delta_g, delta_b, pixel_prec, liste_pixels, bytes_list, i, increment):
    """
    Fonction generalisant le processus de decodage pour les blocs autre que NEW_PIXEL, est appelée lorsque les delta_r,
    delta_g et delta_b sont definis, prend en parametre les deltas, le pixel precedent, la liste de pixels en
    construction, la suite de bytes, l'indice actuel de la suite de bytes, et increment à ajouter à cet indice pour
    passer au bloc suivant.
    """
    r, g, b = delta_r + pixel_prec.get_red(), delta_g + pixel_prec.get_green(), delta_b + pixel_prec.get_blue()
    pixel_prec = Pixel(r, g, b)
    liste_pixels.append(pixel_prec)
    i += increment  # supprime le bloc traité de la liste de bytes pour passer au prochain
    return liste_pixels, bytes_list, pixel_prec, i


def compose_byte(byte0, byte1, lsb, msb):
    """
    Fonction appelée lorsque qu'on veut restituer un entier dont les bits sont repartis sur plusieurs bytes,
    prend en parametre les deux bytes sur lequel est reparti le byte qu'on veut reconstituer, lsb (least significant
    bit) determine le nombre de bits de poids faible qu'il faut ajouter au byte1 pour 'inserer' la partie 'gauche' du
    byte qu'on veut reconstituer, quant à msb, il détermine le nombre de bits de poids faibles qu'il faut 'enlever' au
    byte2, 'assemble' les deux parties avec l'opérateur '|' (ou).
    """
    lsb_byte1 = byte0 & 0b00001111  # garde uniquement les 4 bits de poids faible du premier byte : 0b10110110 → 0b1011
    left_part = lsb_byte1 << lsb  # ajoute lsb bits de poids faibles pour placer la deuxieme partie : 0b1011 → 0b101100
    msb_byte2 = byte1 >> msb  # garde uniquement les msb bits de poids forts du second byte : 0b1011100 → 0b10
    return left_part | msb_byte2  # reconstitue le byte : 0b101100 | 0b10 → 0b101110
