import lidar_location.Point as Point
import math


class Triangle:
    jitter_angle = 0.1  # in rads
    jitter_distance = 0.1  # in meters

    def __init__(self, pt1, pt2, pt3):
        self.pt_list = [pt1, pt2, pt3]
        self.angles = self.get_angles()
        self.distances = self.get_distances()

    # Returns distances between [pt1 and pt2, pt2 and pt3, pt3 and pt1]
    def get_distances(self):
        return [self.get_distance_pt(self.pt_list[0], self.pt_list[1]), self.get_distance_pt(self.pt_list[1], self.pt_list[2]), self.get_distance_pt(self.pt_list[2], self.pt_list[0])]

    def get_beta(self, pt1, pt2):
        return abs(math.acos((-pt1.distance**2 + self.get_distance_pt(pt1, pt2)**2 + pt2.distance**2) / (2 * self.get_distance_pt(pt1, pt2) * pt2.distance))) % math.pi

    def get_gamma(self, pt1, pt2, beta):
        return abs(math.pi - beta - abs(pt2.angle - pt1.angle)) % math.pi

        # Returns angles between segments a-b/b-c [pt1-pt2/pt2-pt3, pt2-pt3/pt3-pt1, pt3-pt1/pt1-pt2]

    def get_angles(self):
        pt1 = self.pt_list[0]
        pt2 = self.pt_list[1]
        pt3 = self.pt_list[2]

        ##print("--- DBUG ----")

        beta1 = self.get_beta(pt1, pt2)
        # print(beta1)
        gamma1 = self.get_gamma(pt1, pt2, beta1)
        # print(gamma1)
        #print(abs(pt2.angle - pt1.angle))

        beta2 = self.get_beta(pt2, pt3)
        gamma2 = self.get_gamma(pt2, pt3, beta2)
        # print(beta2)
        # print(gamma2)
        #print(abs(pt3.angle - pt2.angle))
        beta3 = self.get_beta(pt3, pt1)
        #gamma3 = self.get_gamma(pt3, pt1, beta3)
        # print(beta3)
        # print(gamma3)
        #print(abs(pt1.angle - pt3.angle))

        angle1 = gamma1 + beta2
        angle2 = gamma2 + beta3
        angle3 = math.pi - angle1 - angle2

        return [angle1, angle2, angle3]

    # Returns true if triangle fits within approximation values (distance-angle)

    def compare_triangles(self, triangle2):
        if self.compare_distances(triangle2) and self.compare_angles(triangle2):
            return True
        else:
            return False

    def compare_angles(self, triangle2):
        sorted_local = self.angles
        sorted_local.sort()
        sorted_in = triangle2.angles
        sorted_in.sort()

        for i in range(0, len(sorted_local)):
            if abs(sorted_local[i] - sorted_in[i]) > self.jitter_angle:
                return False

        return True

    def compare_distances(self, triangle2):
        sorted_local = self.distances
        sorted_local.sort()
        sorted_in = triangle2.distances
        sorted_in.sort()

        for i in range(0, len(sorted_local)):
            if abs(sorted_local[i] - sorted_in[i]) > self.jitter_distance:
                return False

        return True

    def get_distance_pt(self, pt1, pt2):
        return math.sqrt(pt2.distance**2 + pt1.distance**2 - 2 * pt1.distance * pt2.distance * math.cos(pt1.angle - pt2.angle))
