
from policies.random_assgn_policy import rnd_assgn_policy_no_return, rnd_assgn_policy_return
from policies.tsp_policy import tsp_policy
from policies.mod_tsp_policy import modified_tsp_policy
from simulation import Simulation
from config import *
import pygame  


def simulate(arrival_rate = LAMBDA):
    
    
    if SHOW_SIM == True:
        pygame.init()  
        screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_WIDTH))  
        pygame.display.set_caption('Simulation')
        
        clock = pygame.time.Clock()
        pygame.font.init()
    else:
        screen = None    


    if POLICY_NAME == "RND_NO_RETURN":
        policy = rnd_assgn_policy_no_return
    
    if POLICY_NAME == "RND_RETURN":
        policy = rnd_assgn_policy_return
    
    if POLICY_NAME == "TSP":
        policy = tsp_policy
    
    if POLICY_NAME == "TSP_MOD":
        policy = modified_tsp_policy
    

    sim = Simulation(
        num_actors=NUM_ACTORS, 
        pois_lambda=arrival_rate, 
        screen=screen,
        policy=policy,
        show_sim=SHOW_SIM)
   
    
    while True:  
        if SHOW_SIM == True:
            for event in pygame.event.get():  
                if event.type == pygame.QUIT:  
                    return
            screen.fill((0, 0, 0))
        rval = sim.tick()
        if rval == -1:
            break

        if SHOW_SIM == True:
            pygame.display.flip()
            pygame.display.update()
            clock.tick(1.0/TICK_TIME*SIMULATION_SPEED)
    
    if len(sim.serviced_tasks) > 0:
        print("Average service time:", sim._avg_served_time/len(sim.serviced_tasks))
    print("Total serviced:", len(sim.serviced_tasks))
    return sim


def multiple_sims():
    f = open("scripts/res_" + POLICY_NAME+ ".txt", "a")
    for lam in [0.05, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8 , 0.9]:
        print("================= LAMBDA: {:.2f} =================".format(lam))
        sim = simulate(arrival_rate=lam)
        f.write(
            str(lam) + "," + str(sim._avg_served_time)+ "," + str(sim._curr_max_time) +\
                 "," + str(len(sim.serviced_tasks))+ "," + str(sim._max_served_time) + "," +  str(sim._avg_served_time/ len(sim.serviced_tasks))+ "\n"
        )
    f.close()

if __name__ == "__main__":
    multiple_sims()