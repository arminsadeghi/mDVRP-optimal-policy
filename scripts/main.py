
from policies.random_assgn_policy import rnd_assgn_policy_no_return, rnd_assgn_policy_return
from policies.tsp_policy import tsp_policy
from simulation import Simulation
from config import *
import pygame  


def main():
    
    pygame.init()  
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_WIDTH))  
    pygame.display.set_caption('Simulation')
      
    clock = pygame.time.Clock()
    pygame.font.init()


    if POLICY_NAME == "RND_NO_RETURN":
        policy = rnd_assgn_policy_no_return
    
    if POLICY_NAME == "RND_RETURN":
        policy = rnd_assgn_policy_return
    
    if POLICY_NAME == "TSP":
        policy = tsp_policy
    

    sim = Simulation(
        num_actors=NUM_ACTORS, 
        pois_lambda=LAMBDA, 
        screen=screen,
        policy=policy)
   
    
    while True:  
        for event in pygame.event.get():  
            if event.type == pygame.QUIT:  
                return
        screen.fill((0, 0, 0))
        rval = sim.tick()
        if rval == -1:
            break
        pygame.display.flip()
        pygame.display.update()
        clock.tick(1.0/TICK_TIME*SIMULATION_SPEED)
    
    if len(sim.serviced_tasks) > 0:
        print("Average service time:", sim._avg_served_time/len(sim.serviced_tasks))
    print("Total serviced:", len(sim.serviced_tasks))


if __name__ == "__main__":
    main()