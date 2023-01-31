
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.geometry import Point


def distance(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return np.sqrt(dx*dx + dy*dy)


class Sector:
    def __init__(self, id, polygon=None, centroid=None) -> None:
        self.polygon = polygon
        self.centroid = centroid
        if self.centroid is None:
            self.centroid = (self.polygon.centroid.x, self.polygon.centroid.y)
        self.id = id

    def contains(self, location):
        if type(location) != list and type(location) != np.array and type(location) != tuple:
            return self.id == location
        else:
            return self.polygon.intersects(Point(location[0], location[1]))

    def is_near_centre(self, location, tolerance=0.01):
        dist = Point(location[0], location[1]).distance(self.centroid)
        if dist <= tolerance:
            return True
        return False

    def get_poly(self):
        return self.polygon

    def get_centroid(self):
        return self.centroid


class Field:
    def __init__(self, vertices, centre, count) -> None:
        self.perimeter_len = 0
        self.count = count
        self.centre = centre

        self.sectors = []
        self.sector_index = 0

        for i, v in enumerate(vertices):
            next_v = vertices[(i + 1) % len(vertices)]
            self.perimeter_len += distance(next_v, v)

        sector_perimeter_len = self.perimeter_len / self.count

        vertices = list(vertices)
        first_vertex = [(vertices[1][0] + vertices[0][0])/2, (vertices[1][1] + vertices[0][1])/2]
        vertices.insert(1, first_vertex)
        cv = first_vertex
        next_index = 2

        while count:
            sv = [cv]
            p = 0
            while p < sector_perimeter_len:
                nv = vertices[next_index]
                d = distance(sv[-1], nv)
                remaining = sector_perimeter_len - p

                if d < remaining:
                    p += d
                    next_index = (next_index + 1) % len(vertices)
                else:
                    # need to insert a new vertex
                    p += remaining

                    count -= 1
                    if not count:
                        nv = first_vertex
                    else:
                        ratio = remaining / d
                        nv = [cv[0] + (nv[0] - cv[0])*ratio,  cv[1] + (nv[1] - cv[1])*ratio]

                # append the vertex
                sv.append(nv)
                cv = nv

            sv.append(centre)
            self.sectors.append(Sector(id=count, polygon=Polygon(sv)))

    def next_sector(self):
        self.sector_index = (self.sector_index + 1) % self.count
        return self.sectors[self.sector_index]

    def is_euclidean(self):
        # TODO: All data files are assumed to be non-euclidean for the time being -- distances are encoded in
        #       the datafile and not calculated here.
        return True


class DataField:
    def __init__(self, df, distances) -> None:
        super().__init__()

        self.sectors = []
        self.sector_index = 0
        self.count = 0
        self.distances = distances

        for i, row in df.loc[df['DEPOT'] == True].iterrows():
            self.sectors.append(Sector(id=self.count, centroid=(row['X'], row['Y'])))
            self.count += 1

    def next_sector(self):
        self.sector_index = (self.sector_index + 1) % self.count
        return self.sectors[self.sector_index]

    def is_euclidean(self):
        # TODO: All data files are assumed to be non-euclidean for the time being -- distances are encoded in
        #       the datafile and not calculated here.
        return False


if __name__ == '__main__':
    n = 3
    square = [[0, 0], [1, 0], [1, 1], [0, 1]]
    sectors = Field(square, [0.5, 0.5], n)

    poly_sq = Polygon(square)
    poly_sects = []
    centroids = []

    for _ in range(n):
        sector = sectors.next_sector()

        poly_sects.append(sector.get_poly())
        centroids.append(sector.get_centroid())

    fig = plt.figure()
    plt.clf()

    plt.plot(*poly_sq.exterior.xy)
    for ps in poly_sects:
        plt.plot(*ps.exterior.xy)

    for pt in centroids:
        plt.plot(pt[0], pt[1],  markersize=12, color='k', marker='x')

    plt.show()