"""
NOM : Saou
PRÉNOM : Ayman
SECTION : B1-INFO
MATRICULE : 000593526
"""


from pixel import Pixel


class Image:
    def __init__(self, width: int, height: int, pixels: list[Pixel]):
        nombre_pixels = 0
        for pixel in pixels:
            if type(pixel) is not Pixel:
                raise Exception
            nombre_pixels += 1
        if nombre_pixels != (width * height):
            raise Exception
        self.largeur = width
        self.hauteur = height
        self.liste = pixels

    def __getitem__(self, pos: tuple[int, int]):
        position_pixel = pos[0] + pos[1] * self.largeur
        self.erreur_index(position_pixel)
        return self.liste[position_pixel]

    def __setitem__(self, pos: tuple[int, int], pix: Pixel):
        position_pixel = pos[0] + pos[1] * self.largeur
        self.erreur_index(position_pixel)
        self.liste[position_pixel] = pix

    def __eq__(self, other):
        return self.largeur == other.largeur and self.hauteur == other.hauteur and self.liste == other.liste

    def get_width(self):
        return self.largeur

    def get_height(self):
        return self.hauteur

    def get_pixels(self):
        return self.liste

    def get_unique_pixels(self):
        """
        Return une liste composée des pixels uniques.
        """
        return list(set(self.liste))

    def erreur_index(self, position):
        if position not in range(len(self.liste)):
            raise IndexError


    def encode_palette(self):
        liste_pixels = self.pixels
        palette = list(set(liste_pixels))
        return palette