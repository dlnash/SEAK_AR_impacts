#############################################################
# Author: Weiming Hu <weiminghu@ucsd.edu>                   #
#                                                           #
#         Center for Western Weather and Water Extremes     #
#         Scripps Institution of Oceanography               #
#         UC San Diego                                      #
#                                                           #
#         https://weiming-hu.github.io/                     #
#         https://cw3e.ucsd.edu/                            #
#                                                           #
# Date of Creation: 2022/08/18                              #
#############################################################

import time
import dask
import types
import warnings
import contextlib
import dask_jobqueue

import numpy as np

from io import StringIO
from tqdm.auto import tqdm
from dask import distributed
from datetime import datetime
from functools import partial
from dask.delayed import Delayed
from tqdm.contrib.concurrent import process_map


####################
# Global variables #
####################

# Version number
__version__ = '0.0.2'

# The supported scheduler
_SUPPORTED_SCHEDULERS_ = ['local', 'slurm']

# The required keyword arguments for schedulers
_REQUIRED_KWARGS_ = {
    'local': ['dashboard_address'],
    'slurm': ['account', 'queue', 'walltime', 'memory', 'dashboard_address']
}

# User variables
LOCAL_KWARGS = {'dashboard_address': ':8989'}

SLURM_KWARGS = {'account': None, 'queue': None, 'walltime': None,
                'memory': '25G', 'dashboard_address': ':8989',
                'death_timeout': 300,
                'local_directory': 'efo_worker_logs',
                'log_directory': 'efo_worker_logs'}

MAX_JOBS_IN_SINGLE_COMPUTE = 10000

#####################
# Wrapper functions #
#####################

def _call_run_simulation(simulation, callback=None):
    """A wrapper function that accepts a simulation and calls the `run_simulation`
    method. This function is created for parallelization with multi-processing.
    """
    
    with contextlib.redirect_stdout(StringIO()):
        ret = simulation.run_simulation()
        
        if callback is None:
            return ret
        else:
            return callback(ret)

        
def _call_run_simulation_with_callback_delayed(simulation, callback=None):
    """A wrapper function that accepts a simulation and calls the `run_simulation`
    method. The difference between this function and `_call_run_simulation` is that,
    this function assumes simulation to be delayed and the callback function will
    also be delayed.
    """
    
    with contextlib.redirect_stdout(StringIO()):
        ret = simulation.run_simulation()
        
        if callback is None:
            return ret
        else:
            return dask.delayed(callback)(ret)
        

@dask.delayed
def _delayed_run_simulation(simulation, callback=None):
    """A delayed version of running the simulation. This function is created
    for parallelization with Dask. This function assumes simulation is not delayed,
    therefore, it is safe to make this function delayed.
    """
    
    return _call_run_simulation(simulation, callback=callback)


class BatchSimulations:
    """Class for running batch simulations
    
    This class provides different ways to run a set of input scenarios:
    
    1. serial: `n_nodes=1, cores_per_node=1`
    2. multicore: `n_nodes=1, cores_per_node>1`
    3. distributed: `n_nodes>1`
    
    For serial and multicore, tqdm will be used to manage task scheduling.
    For distributed, dask and dask-jobqueue will be used to manage task scheduling.
    """
    
    def __init__(self, n_nodes=1, cores_per_node=1,
                 name=None, silent=False,
                 scheduler=None, scheduler_kwargs=None,
                 callback_func=None,
                 keep_workers_alive=False,
                 min_workers_to_start_computing=20):
        """Initialization

        Args:
            n_nodes (int, optional): The number of nodes to use. Defaults to 1.
            cores_per_node (int, optional): The number of cores to use on each node. Defaults to 1.
            name (str, optional): A nickname for this batch. Defaults to None.
            silent (bool, optional): Whether to be silent. Defaults to False.
            scheduler (str, optional): Required if more than one node are used. Currently supports local or slurm. Defaults to None.
            scheduler_kwargs (dict, optional): Additional keyword arguments passed for schedulers. Templares are avialable at `simulations.SLURM_KWARGS` or `simulations.LOCAL_KWARGS`. Defaults to None.
            callback_func (function, optional): A callback function that accepts the simulation as the only input argument. If provided, this function will be called after `simulation.run_simulation()` and the results will be returned.
            keep_workers_alive (bool, options): A boolean value for whether to keep workers alive after `run_simulations`. Only valid for distributed parallelization. If `True`, users are responsible for terminating workers manually using `terminate_workers`.
            min_workers_to_start_computing (int, options): An integer specifying the minimum number of workers to initiate the computation without waiting for all workers to be ready. This is only used in the distributed computing mode. Set to `None` to wait for all workers.
        """
        
        # Sanity check
        if name is not None:
            assert isinstance(name, str), 'name should be a string'

        assert isinstance(silent, bool), 'silent must be a boolean'
        assert isinstance(n_nodes, int) and n_nodes > 0, 'n_nodes must be a positive integer'
        assert isinstance(cores_per_node, int) and cores_per_node > 0, 'cores_per_node must be a positive integer'
        assert isinstance(keep_workers_alive, bool), 'keep_workers_alive must be a boolean'
        
        if callback_func is not None:
            assert callable(callback_func), 'callback_func must be a function'
        
        # Member initialization
        self.name = name
        self.client = None
        self.cluster = None
        self.silent = silent
        self.n_nodes = n_nodes
        self.simulations = None
        self.n_simulations = None
        self.callback_func = callback_func
        self.cores_per_node = cores_per_node
        self.scheduler_kwargs = scheduler_kwargs
        self.keep_workers_alive = keep_workers_alive
        self.min_workers_to_start_computing = min_workers_to_start_computing
        
        # The number of seconds to wait before checking the status of workers again
        self.wait_interval = 5
        
        # Check whether scheduler is set if more than one node is to be used
        if n_nodes > 1:
            
            if scheduler is None:
                msg = 'Using more than 1 node but scheduler is not set. Try `scheduler=slurm`'.format(scheduler)
                msg += '\nSupported scheduler options are: {}'.format(_SUPPORTED_SCHEDULERS_)
                raise Exception(msg)
            
            elif scheduler not in _SUPPORTED_SCHEDULERS_:
                msg = 'Using more than 1 node but received a unrecognized scheduler ({})'.format(scheduler)
                msg += '\nSupported scheduler options are: {}'.format(_SUPPORTED_SCHEDULERS_)
                raise Exception(msg)
            
            else:
                self.scheduler = scheduler
                
        # Check whether required keyword arguments for scheduler are provided
        if self.parallel_status() == 'distributed':
            
            if self.scheduler_kwargs is None:
                if self.scheduler == 'local':
                    self.scheduler_kwargs = LOCAL_KWARGS
                elif self.scheduler == 'slurm':
                    self.scheduler_kwargs = SLURM_KWARGS
                else:
                    raise Exception('Unknown scheduler: {}'.format(self.scheduler))
            
            for k in _REQUIRED_KWARGS_[self.scheduler]:
                assert k in self.scheduler_kwargs, 'Missing required argument in scheduler_kwargs: {}'.format(k)
                assert self.scheduler_kwargs[k] is not None, f'Missing value in scheduler_kwargs: {k}'
                
    def set_simulations(self, simulations, n_simulations=None):
        """Set simulations to run for this object

        Args:
            simulations (str, optional): A sequence of simulations with the `run_simulation` method
            n_simulations (int, optional): The number of simulations. Only used if `simulations` is a generator. The number of simulations cannot be automatically inferred if a generator is passed as `simulations` without evaluating the generator. Specify this argument will help visualizing a progress bar.
        """
        
        # Determine the number of simulations
        if hasattr(simulations, '__len__'):
            # The argument `simulations` is a sequence. Therefore its size is apparent.
            self.n_simulations = len(simulations)
            
            if n_simulations is not None:
                warnings.warn('The number of simulations is inferred. Ignoring n_simulations.')
                
        else:
            # The argument `simulations` is a generator. It does not have a size unless evaluated.
            assert isinstance(simulations, types.GeneratorType), 'simulations must be either a sequence or a generator!'
            
            if n_simulations is None:
                warnings.warn('simulations are passed as a generator but no size information is available. Pass the number of simulations, e.g., n_simulations=100.')
            
            self.n_simulations = n_simulations
        
        self.simulations = simulations
        
    def run_simulations(self):
        """Run the batch simulations
        """
        if self.simulations is None:
            raise Exception("No simulations to run. Did you forget use 'set_simulations'?")
        
        status = self.parallel_status()
        
        if status == 'serial' or status == 'multicore':
            return self._run_simulations_tqdm()
        elif status == 'distributed':
            return self._run_simulations_dask()
        else:
            raise Exception('Fatal error: unrecognized parallel status {}'.format(status))
    
    def parallel_status(self) -> str:
        """Return the parallelization status as a string
        """
        
        if self.n_nodes > 1:
            return 'distributed'
        elif self.cores_per_node > 1:
            return 'multicore'
        else:
            return 'serial'
    
    def terminate_workers(self):
        
        if self.cluster is None:
            return
        
        assert isinstance(self.client, distributed.client.Client), 'Client is not properly initiated!'
        
        self.client.close()
        self.cluster.close()
        
    def summary(self) -> str:
        summary =  '====== EFO BatchSimulations ======\n'

        if self.name is not None:
            summary += 'name: {}\n'.format(self.name)

        summary += 'number of simulations: {}\n'.format(self.n_simulations)
        summary += 'cores per node: {}\n'.format(self.cores_per_node)
        summary += 'number of nodes: {}\n'.format(self.n_nodes)
        summary += 'parallel mode: {}\n'.format(self.parallel_status())
        
        if self.parallel_status() == 'distributed':
            summary += 'scheduler: {}\n'.format(self.scheduler)
            summary += 'keep workers alive: {}\n'.format(self.keep_workers_alive)
            summary += 'Minimum # workers to start computing: {}\n'.format(
                'All' if self.min_workers_to_start_computing is None else self.min_workers_to_start_computing)
            
            for k, v in self.scheduler_kwargs.items():
                summary += '{}: {}\n'.format(k, v)
        
        summary += '======    End of Summary    ======'
        return summary
    
    def __str__(self) -> str:
        return self.summary()
    
    ###################
    # Private Methods #
    ###################
    
    def _run_simulations_tqdm(self):
        start_time = datetime.now()
        
        # Wrap the callback function
        wrapper = partial(_call_run_simulation, callback=self.callback_func)
        
        # Run simulations
        ret = process_map(wrapper, self.simulations,
                          max_workers=self.cores_per_node, disable=self.silent,
                          total=self.n_simulations, desc='Running simulations')
        
        if not self.silent:
            print('Runtime for running simulations: {}'.format(datetime.now() - start_time))
            
        return ret
    
    def _run_simulations_dask(self):
        assert hasattr(self.simulations, '__len__'), 'Dask parallelization only supports sequence-like simulation list!'
        
        # Initialize runtime loggers
        logger_checkpoints = [datetime.now()]
        logger_names = []
        
        # Request workers
        if not self.silent:
            print('Requesting workers ...')
            
        self._dask_request_workers()
        
        # Wait until workers are ready
        self._dask_wait_for_workers()
        
        logger_names.append('Walltime for requesting workers')
        logger_checkpoints.append(datetime.now())
        
        # Set up dask jobs
        jobs = [
            _call_run_simulation_with_callback_delayed(simulation=x,
                                                       callback=self.callback_func)
            if isinstance(x, Delayed)
            
            else _delayed_run_simulation(simulation=x,
                                         callback=self.callback_func)
            
            for x in tqdm(self.simulations,
                          total=self.n_simulations,
                          disable=self.silent, desc='Setting up dask jobs')
        ]
        
        logger_names.append('Walltime for setting up dask jobs')
        logger_checkpoints.append(datetime.now())
        
        # Run jobs in parallel
        n_chunks =  int(np.ceil(self.n_simulations / MAX_JOBS_IN_SINGLE_COMPUTE))

        if not self.silent:
            print('Running jobs in {} chunk(s) ...'.format(n_chunks))
        
        ret = []
        for i in range(0, self.n_simulations, MAX_JOBS_IN_SINGLE_COMPUTE):
            ret.extend(dask.compute(*jobs[i:(i+MAX_JOBS_IN_SINGLE_COMPUTE)]))
            
            if not self.silent:
                print(f'Finished {int(i/MAX_JOBS_IN_SINGLE_COMPUTE)+1}/{n_chunks}')
        
        logger_names.append('Walltime for running jobs')
        logger_checkpoints.append(datetime.now())
        
        # Terminate workers
        if self.keep_workers_alive:
            if not self.silent:
                print('Workers are still alive. Use terminate_workers to stop them manually.')
        
        else:
            if not self.silent:
                print('Terminating workers ...')
                
            self.terminate_workers()
        
        logger_names.append('Walltime for terminating workers')
        logger_checkpoints.append(datetime.now())
        
        # Print runtime summary
        if not self.silent:
            print()
            for i in range(len(logger_names)):
                walltime = logger_checkpoints[i+1] - logger_checkpoints[i]
                print('{}: {}'.format(logger_names[i], walltime))
                
            print('Total walltime: {}'.format(logger_checkpoints[-1] - logger_checkpoints[0]))
        
        return ret
        
    def _dask_request_workers(self):
        
        # No need to request workers if they are already live
        if isinstance(self.client, distributed.client.Client):
            if self.client.status == 'running':
                return
        
        if self.scheduler == 'local':
            self.cluster = distributed.LocalCluster(
                threads_per_worker=self.cores_per_node,
                **self.scheduler_kwargs)
            
        elif self.scheduler == 'slurm':
            extra_args = {k: v for k, v in self.scheduler_kwargs.items() if k != 'dashboard_address'}

            self.cluster = dask_jobqueue.SLURMCluster(
                cores=self.cores_per_node,
                processes=self.cores_per_node,
                scheduler_options={'dashboard_address': self.scheduler_kwargs['dashboard_address']},
                **extra_args)

        else:
            raise Exception('Unsupported scheduler: {}'.format(self.scheduler))
        
        self.cluster.scale_up(self.n_nodes)
        self.client = distributed.Client(self.cluster)
    
    def _dask_wait_for_workers(self):

        # Numbers of workers
        total = self.n_nodes * self.cores_per_node
        goal = total if self.min_workers_to_start_computing is None else min(self.min_workers_to_start_computing, total)
        
        with tqdm(disable=self.silent, desc='Waiting for workers') as pbar:
            while len(self.cluster.scheduler.workers) < goal:
                time.sleep(self.wait_interval)

                pbar.update(1)
                pbar.set_description('Waiting for workers [{} ready / {} goal / {} total]'.format(
                    len(self.cluster.scheduler.workers), goal, total))

                # Make sure the number of workers are correct
                self.cluster.scale_up(self.n_nodes)