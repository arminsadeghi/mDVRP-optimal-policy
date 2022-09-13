import lkh

# Make sure LKH is downloaded and built first!
#
#     http://webhotel4.ruc.dk/~keld/research/LKH-3/
#
solver_path = '../thirdParty/lkh/LKH-3.0.7/LKH'


def solve_tsp(name, comment, start_pos, tasks, scale_factor=1.0):

    N = 1
    node_coord_str = str(N) + ' ' + str(int(start_pos[0] * scale_factor)) + ' ' + str(int(start_pos[1] * scale_factor)) + '\n'

    for task in tasks:
        if task.is_pending():
            N += 1
            node_coord_str += str(N) + ' ' + str(int(task.location[0] * scale_factor)) + ' ' + str(int(task.location[1] * scale_factor)) + '\n'

    if N < 3:
        return([[1, 2], ])

    tsp_str = ""
    tsp_str += 'NAME: ' + name + '\n'
    tsp_str += 'TYPE: TSP\n'
    tsp_str += 'COMMENT: ' + comment + '\n'
    tsp_str += 'DIMENSION: ' + str(N) + '\n'
    tsp_str += 'EDGE_WEIGHT_TYPE: EUC_2D\n'
    tsp_str += 'NODE_COORD_SECTION:\n'
    tsp_str += node_coord_str
    tsp_str += 'EOF\n'

    problem = lkh.LKHProblem.parse(tsp_str)
    path = lkh.solve(solver=solver_path, problem=problem, max_trials=10000, runs=5)

    return path


def solve_trp(name, comment, start_pos, tasks, simulation_time, mean_service_time=0, scale_factor=1.0):

    N = 1
    node_coord_str = 'NODE_COORD_SECTION:\n' + str(N) + ' ' + str(int(start_pos[0] * scale_factor)) + ' ' + str(int(start_pos[1] * scale_factor)) + '\n'
    service_time_str = 'SERVICE_TIME_SECTION:\n' + str(N) + ' 0\n'
    # repurposing demand to account for built-up wait
    demand_str = 'DEMAND_SECTION: \n' + str(N) + ' 0\n'

    for task in tasks:
        if task.is_pending():
            N += 1
            node_coord_str += str(N) + ' ' + str(int(task.location[0] * scale_factor)) + ' ' + str(int(task.location[1] * scale_factor)) + '\n'
            service_time_str += str(N) + ' ' + str(mean_service_time) + '\n'
            demand_str += str(N) + ' ' + str(int((simulation_time - task.time) * scale_factor)) + '\n'

    if N < 3:
        return([[1, 2], ])

    tsp_str = ""
    tsp_str += 'NAME: ' + name + '\n'
    tsp_str += 'TYPE: TRP\n'
    tsp_str += 'COMMENT: ' + comment + '\n'
    tsp_str += 'DIMENSION: ' + str(N) + '\n'
    tsp_str += 'EDGE_WEIGHT_TYPE: EUC_2D\n'
    tsp_str += node_coord_str
    tsp_str += service_time_str
    tsp_str += demand_str
    tsp_str += 'DEPOT_SECTION:\n'
    tsp_str += '1\n'
    tsp_str += '-1\n'
    tsp_str += 'EOF\n'

    problem = lkh.LKHProblem.parse(tsp_str)
    path = lkh.solve(solver=solver_path, problem=problem, max_trials=1000, runs=5)

    return path
