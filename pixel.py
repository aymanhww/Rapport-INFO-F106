"""
NOM : Saou
PRÉNOM : Ayman
SECTION : B1-INFO
MATRICULE : 000593526
"""


class Pixel:
    def __init__(self, R: int, G: int, B: int):
        if R < 0 or R > 255 or G < 0 or G > 255 or B < 0 or B > 255:
            raise Exception('Intensity out of range')
        self.__red = R
        self.__green = G
        self.__blue = B

    def get_red(self):
        return self.__red

    def get_green(self):
        return self.__green

    def get_blue(self):
        return self.__blue

    def get_rgb(self):
        """
        Return un tuple composé de l'intensité des canaux RGB.
        :return:
        """
        return self.__red, self.__green, self.__blue

    def __eq__(self, other):
        return self.get_rgb() == other.get_rgb()

    def __hash__(self):
        """
        Permet de rendre le type Pixel 'hashable' afin de pouvoir convertir une liste de pixels en un set.
        """
        return hash(self.get_rgb())

    def get_delta(self, other):
        """
        Prend en parametre deux pixels et return un tuple composé de la difference de couleurs entre ces deux pixels
        """
        return (other.get_red() - self.get_red(), other.get_green() - self.get_green(), other.get_blue() -
                self.get_blue())
