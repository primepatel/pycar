import pygame, neat, sys
from math import sin, cos
from math import radians as rad

ROAD_COLOR, CAR_X, CAR_Y = (58, 58, 60, 255), 30, 20

class Car:
    def __init__(self):
        self.car = pygame.transform.rotate(pygame.transform.scale(pygame.image.load('car.png').convert(), (CAR_X, CAR_Y)), 180)
        self.rotated_car = self.car
        self.position, self.angle, self.speed= [315, 455], 0, 0
        self.distance, self.sensors, self.alive = 0, [], True
        self.center = [self.position[0] + CAR_X / 2, self.position[1] + CAR_Y / 2]
    
    def appear(self, screen):
        screen.blit(self.rotated_car, self.position)
        for radar in self.sensors:
            position = radar[0]
            pygame.draw.line(screen, (0, 200, 0), self.center, position, 1)
            pygame.draw.circle(screen, (0, 200, 0), position, 5)

    def check_collision(self, game_map):
        self.alive = True
        for point in self.edges:
            if game_map.get_at((int(point[0]), int(point[1]))) != ROAD_COLOR:
                self.alive = False
                break
    
    def check_radar(self, degree, game_map):
        x = int(self.center[0])
        y = int(self.center[1])
        length = 0
        while game_map.get_at((x, y)) == ROAD_COLOR and length < 150:
            length = length + 1
            x = int(self.center[0] + cos(rad(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + sin(rad(360 - (self.angle + degree))) * length)
        dist = int((pow(x - self.center[0], 2) + pow(y - self.center[1], 2))**0.5)
        self.sensors.append([(x, y), dist])
    
    def refresh(self, game_map):
        if self.speed == 0:
            self.speed = 10
        self.rotated_car = pygame.transform.rotate(self.car, self.angle)
        self.position[0] += cos(rad(-self.angle)) * self.speed
        self.position[1] += sin(rad(-self.angle)) * self.speed
        self.distance += self.speed
        self.center = [int(self.position[0]) + CAR_X / 2, int(self.position[1]) + CAR_Y / 2]
        self.set_corners()
        self.check_collision(game_map)
        self.sensors.clear()
        for d in range(-90, 91, 30):
            self.check_radar(d, game_map)

    def set_corners(self):
        length = 0.5*((CAR_X**2 + CAR_Y**2)**0.5)
        left_top = [self.center[0] + cos(rad(-self.angle) + 0.588) * length, self.center[1] + sin(rad(-self.angle) + 0.588) * length]
        right_top = [self.center[0] + cos(rad(-self.angle) + 2.159) * length, self.center[1] + sin(rad(-self.angle) + 2.159) * length]
        left_bottom = [self.center[0] + cos(rad(-self.angle)- 2.159) * length, self.center[1] + sin(rad(-self.angle)- 2.159) * length]
        right_bottom = [self.center[0] + cos(rad(-self.angle)- 0.588) * length, self.center[1] + sin(rad(-self.angle)- 0.588) * length]
        self.edges = [left_top, right_top, left_bottom, right_bottom]
    def get_sensor_data(self):
        radars = self.sensors
        return_values = [0, 0, 0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1])
        return return_values

    def reward(self):
        return self.distance+self.speed

class Simulator:
    def __init__(self) -> None:
        self.width = 960
        self.height = 540
        self.map = 0
        self.current_generation = 0
        
    def write(self, screen, size, string, loc):
        font = pygame.font.SysFont("Arial", size)
        text = text = font.render(string, True, (0,0,0))
        text_rect = text.get_rect()
        text_rect.center = loc
        screen.blit(text, text_rect)

    def set_map(self):
        self.game_map = pygame.transform.scale(pygame.image.load(f'.\\maps\\PNG\\map{self.map%4 + 1}.png').convert(), (self.width, self.height))

    def simulate(self, genomes, config):
        self.cars, self.nets = [], []
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        clock = pygame.time.Clock()
        for i, g in genomes:
            net = neat.nn.FeedForwardNetwork.create(g, config)
            self.nets.append(net)
            g.fitness = 0
            self.cars.append(Car())
        self.set_map()
        self.current_generation += 1
        flag = True
        while flag:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)
            key = pygame.key.get_pressed()
            if key[pygame.K_n] == True:
                self.map += 1
                self.set_map()
                screen.blit(self.game_map, (0, 0))
                for car in self.cars:
                    car.angle = 0
                    car.speed = 0
                    car.position = [315, 455]

            for i, car in enumerate(self.cars):
                output = self.nets[i].activate(car.get_sensor_data())
                choice = output.index(max(output))
                if choice == 0:
                    car.angle += 10
                elif choice == 1:
                    car.angle -= 10
                elif choice == 2 and car.speed >= 8:
                    car.speed -= 2
                else:
                    car.speed += 2
            still_alive = 0
            for i, car in enumerate(self.cars):
                if car.alive:
                    still_alive += 1
                    car.refresh(self.game_map)
                    genomes[i][1].fitness += car.reward()
            if still_alive == 0:
                break
            screen.blit(self.game_map, (0, 0))
            for car in self.cars:
                if car.alive:
                    car.appear(screen)
            self.write(screen, 30, "Generation: " + str(self.current_generation), (480, 30))
            self.write(screen, 20, "Alive: " + str(still_alive), (480, 60))
            pygame.display.flip()
            clock.tick(30)

if __name__ == "__main__":
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,neat.DefaultReproduction,neat.DefaultSpeciesSet,neat.DefaultStagnation,config_path)
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    sim = Simulator()
    population.run(sim.simulate, 1000)