# utils/timeout.py

import threading

# Custom exception to represent a timeout condition
class TimeoutError(Exception):
    pass

def run_with_timeout(func, timeout: int):
    """
    Runs the given function with a timeout. If it exceeds `timeout` seconds,
    raises TimeoutError. Any exception inside the function is propagated.

    Parameters:
        func (Callable): Function to execute.
        timeout (int): Timeout duration in seconds.

    Returns:
        Any: Result of the function call, if completed within time.

    Raises:
        TimeoutError: If execution exceeds timeout.
        Exception: Any exception raised inside `func`.
    """

    result_container = {}  # Used to capture return value or exception from the thread

    def wrapper():
        try:
            result_container['result'] = func()
        except Exception as e:
            result_container['error'] = e

    # Run the function in a separate thread
    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join(timeout)  # Wait for the thread to complete (or timeout)

    if thread.is_alive():
        # Thread is still running after timeout — job took too long
        raise TimeoutError(f"Job exceeded timeout of {timeout} seconds.")

    if 'error' in result_container:
        # Function raised an exception — propagate it
        raise result_container['error']

    return result_container.get('result')
