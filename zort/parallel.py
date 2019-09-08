#! /usr/bin/env python
"""
parallel.py
A native python implementation of processing embarrassingly parallel tasks
using concurrent futures. These processes will also display progress bars.
"""
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed


def parallel_process(array, function, n_jobs=16, use_kwargs=False, return_out=False):
    """
        A parallel version of the map function with a progress bar.

        Args:
            array (array-like): An array to iterate over.
            function (function): A python function to apply to the elements of array
            n_jobs (int, default=16): The number of cores to use
            use_kwargs (boolean, default=False): Whether to consider the elements of array as dictionaries of
                keyword arguments to function
        Returns:
            [function(array[0]), function(array[1]), ...]
        Function inspired by:
            http://danshiebler.com/2016-09-14-parallel-progress-bar/
    """
    # Assemble the workers
    with ProcessPoolExecutor(max_workers=n_jobs) as pool:
        # Pass the elements of array into function
        if use_kwargs:
            futures = [pool.submit(function, **a) for a in array]
        else:
            futures = [pool.submit(function, a) for a in array]
        kwargs = {
            'total': len(futures),
            'unit': 'it',
            'unit_scale': True,
            'leave': True
        }
        # Print out the progress as tasks complete
        for _ in tqdm(as_completed(futures), **kwargs):
            pass

    if return_out:
        out = []
        # Get the results from the futures.
        for i, future in tqdm(enumerate(futures)):
            try:
                out.append(future.result())
            except Exception as e:
                out.append(e)
        return out
