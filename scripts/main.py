
from simulation import Simulation
from config import LAMBDA, SCREEN_WIDTH, TICK_TIME
import pygame  


def main():
    
    pygame.init()  
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_WIDTH))  
    pygame.display.set_caption('Simulation')
      
    clock = pygame.time.Clock()
    pygame.font.init()

    sim = Simulation(
        num_actors=2, 
        pois_lambda=LAMBDA, 
        screen=screen)
   
    
    while True:  
        for event in pygame.event.get():  
            if event.type == pygame.QUIT:  
                return
        screen.fill((0, 0, 0))
        sim.tick()

        pygame.display.flip()
        pygame.display.update()
        clock.tick(1.0/TICK_TIME)


if __name__ == "__main__":
    main()