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
        return ([[1, 2], ])

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


def solve_time_tsp(name, comment, distances, scale_factor=1.0):

    N = distances.shape[0]
    if N < 3:
        return ([[1, 2], ])

    distances = (distances * scale_factor).astype(int)
    row_strs = [" ".join([str(e) for e in row]) for row in distances]
    distance_str = "\n".join([row for row in row_strs])

    tsp_str = ""
    tsp_str += 'NAME: ' + name + '\n'
    tsp_str += 'TYPE: ATSP\n'
    tsp_str += 'COMMENT: ' + comment + '\n'
    tsp_str += 'DIMENSION: ' + str(N) + '\n'
    tsp_str += 'EDGE_WEIGHT_TYPE: EXPLICIT\n'
    tsp_str += 'EDGE_WEIGHT_FORMAT: FULL_MATRIX\n'
    tsp_str += 'EDGE_WEIGHT_SECTION: \n'
    tsp_str += distance_str + '\n'
    tsp_str += 'EOF\n'

    problem = lkh.LKHProblem.parse(tsp_str)
    path = lkh.solve(solver=solver_path, problem=problem, max_trials=10000, runs=5)

    return path


def solve_trp(name, comment, start_pos, tasks, simulation_time, mean_service_time=0, cost_exponent=1, scale_factor=1.0):

    N = 1
    position_scale = scale_factor  # * 100
    node_coord_str = 'NODE_COORD_SECTION:\n' + \
        str(N) + ' ' + str(int(start_pos[0] * position_scale)) + ' ' + str(int(start_pos[1] * position_scale)) + '\n'
    service_time_str = 'SERVICE_TIME_SECTION:\n' + str(N) + ' 0\n'
    # repurposing demand to account for built-up wait
    demand_str = 'DEMAND_SECTION: \n' + str(N) + ' 0\n'

    for task in tasks:
        if task.is_pending():
            N += 1
            node_coord_str += str(N) + ' ' + str(int(task.location[0] * position_scale)) + ' ' + str(int(task.location[1] * position_scale)) + '\n'
            service_time_str += str(N) + ' ' + str(mean_service_time * scale_factor) + '\n'
            demand_str += str(N) + ' ' + str(int((simulation_time - task.time + task.initial_wait) * scale_factor)) + '\n'

    if N < 3:
        return ([[2], ])

    tsp_str = ""
    tsp_str += 'NAME: ' + name + '\n'
    tsp_str += 'TYPE: TRP\n'
    tsp_str += 'COMMENT: ' + comment + '\n'
    tsp_str += 'DIMENSION: ' + str(N) + '\n'
    tsp_str += 'RISK_THRESHOLD: ' + str(int(cost_exponent*10)) + '\n'
    tsp_str += 'EDGE_WEIGHT_TYPE: EUC_2D\n'
    # repurposing risk threshold for the cost exponent
    tsp_str += node_coord_str
    tsp_str += service_time_str
    tsp_str += demand_str
    tsp_str += 'DEPOT_SECTION:\n'
    tsp_str += '1\n'
    tsp_str += '-1\n'
    tsp_str += 'EOF\n'

    problem = lkh.LKHProblem.parse(tsp_str)
    path = lkh.solve(solver=solver_path, problem=problem, max_trials=5000, runs=5)

    return path


def solve_time_trp(name, comment, tasks, distances, simulation_time, mean_service_time=0, cost_exponent=1, scale_factor=1.0):

    N = distances.shape[0]
    if N < 3:
        return ([[2], ])

    distances = (distances * scale_factor).astype(int)
    row_strs = [" ".join([str(e) for e in row]) for row in distances]
    distance_str = "\n".join([row for row in row_strs])

    service_time_str = 'SERVICE_TIME_SECTION:\n' + '1 0\n'  # no service time at the depot
    service_time_str += '\n'.join([f'{n} {mean_service_time * scale_factor}' for n in range(2, N+1)]) + '\n'

    # repurposing demand to account for built-up wait
    demand_str = 'DEMAND_SECTION: \n' + '1 0\n'  # no waiting at the depot
    for n, task in enumerate(tasks):
        demand_str += f'{n+2} {int((simulation_time - task.time + task.initial_wait) * scale_factor)}\n'

    tsp_str = ""
    tsp_str += 'NAME: ' + name + '\n'
    tsp_str += 'TYPE: TRP\n'
    tsp_str += 'COMMENT: ' + comment + '\n'
    tsp_str += 'DIMENSION: ' + str(N) + '\n'
    tsp_str += 'RISK_THRESHOLD: ' + str(int(cost_exponent*10)) + '\n'
    tsp_str += 'EDGE_WEIGHT_TYPE: EXPLICIT\n'
    tsp_str += 'EDGE_WEIGHT_FORMAT: FULL_MATRIX\n'
    tsp_str += 'EDGE_WEIGHT_SECTION: \n'
    # repurpose RISK_THRESHOLD to pass in cost exponent, multiply by 10 so it goes as an INT
    tsp_str += distance_str + '\n'
    tsp_str += service_time_str + '\n'
    tsp_str += demand_str + '\n'
    tsp_str += 'DEPOT_SECTION:\n'
    tsp_str += '1\n'
    tsp_str += '-1\n'
    tsp_str += 'EOF\n'

    print(tsp_str)

    problem = lkh.LKHProblem.parse(tsp_str)
    path = lkh.solve(solver=solver_path, problem=problem, max_trials=10000, runs=5)

    return path


def test_time_tsp(distances, scale):

    tour = solve_time_tsp("TIME_TSP", "Solving a TIME based TSP problem", distances=distances, scale_factor=scale)
    print(f'Found tour: {tour}')

    return


def test_time_trp(tasks, distances, simulation_time, mean_service_time, scale):

    tour = solve_time_trp("TIME_TRP", "Solving a TIME based TSP problem", tasks=tasks, distances=distances,
                          simulation_time=simulation_time, mean_service_time=mean_service_time, scale_factor=scale)
    print(f'Found tour: {tour}')

    return


if __name__ == "__main__":

    import numpy as np

    class Task:
        def __init__(self, id, t) -> None:
            self.id = id
            self.time = t

    sim_time = 200
    tasks = [Task(n, d) for n, d in zip(range(3), [180, 190, 195])]
    mean_service_time = 2

    distances = np.array([
        [0, 10, 30, 50],
        [10, 0, 10, 30],
        [10, 10, 0, 1],
        [10, 20, 30, 0],
    ])

    print('--- TIME TSP')
    test_time_tsp(distances, scale=100)
    print('--- TIME TRP')
    test_time_trp(tasks, distances, sim_time, mean_service_time, scale=100)

    tasks = [Task(n, d) for n, d in zip(range(3), [199, 199, 5])]
    print('--- TIME TRP (MOD)')
    test_time_trp(tasks, distances, sim_time, mean_service_time, scale=100)
