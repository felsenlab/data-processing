import os
import sys
import logging

class PrintSuppressor:
    """
    A context manager that suppresses all print calls and logging.
    """
    def __enter__(self):
        self.f = open(os.devnull, 'w')  # Open a null device to discard output
        self.original_stdout = sys.stdout  # Save current stdout
        self.original_stderr = sys.stderr  # Save current stderr

        sys.stdout = self.f  # Redirect stdout
        sys.stderr = self.f  # Redirect stderr

        logging.disable(logging.CRITICAL)  # Suppress logging
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.original_stdout  # Restore stdout
        sys.stderr = self.original_stderr  # Restore stderr

        self.f.close()  # Close the null device
        logging.disable(logging.NOTSET)  # Re-enable logging