from simulation import Simulation
import multiprocessing


def main(run_number=None):
    s = Simulation(verbose=0)
    s.run(days=20)
    s.stats(run_number=run_number)


processes = []
for i in range(3):
    p = multiprocessing.Process(target=main, args=(i,))
    processes.append(p)
    p.start()

for p in processes:
    p.join()
    print('Process Finished')

for p in processes:
    p.close()
