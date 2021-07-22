import dataclasses
import enum
import importlib.util
import os
import pathlib
import re
import termcolor
import unittest

from pprint import pprint as pp

from UnitTester.SequentialTester import SequentialTestLoader

# FIXME: this can be fixed if you run this in virtualenv
# get the specifications from the path given
# spec = importlib.util.spec_from_file_location(
# "test", pathlib.Path("UnitTests/SequentialTest.py"))
# load the specifications as a module to be imported
# __module = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(__module)
# _SequentialTestLoader = __module.SequentialTestLoader


class Indexer(enum.Enum):
    TOTAL, FAILURE = 0, 1


class GenericRunner:
    """
    This is intended to be run in any project that has
    a unit test folder within it

    excluded_dirs: directories not searched in the filesystem construction
    excluded_files: files not loaded in the filesystem during construction
    parent_dir: starting directory for file system construction
    pedantic: more output
    score: what tests have failures and which ones had successes
        - TODO: more complete would have (failures, errors and successes)
    """

    def __init__(self, parent_dir: pathlib.Path, pedantic: bool,
                 excluded_files: list = [
                     "SequentialTest.py", "__init__.py", "BaseTester.py", "README.md"],
                 excluded_dirs: list = ["__pycache__", "TEST"]):

        if not(isinstance(parent_dir, pathlib.Path) and
               parent_dir.is_dir() and
               isinstance(pedantic, bool) and
               isinstance(excluded_files, list) and
               all([isinstance(_, str) for _ in excluded_files]) and
               isinstance(excluded_dirs, list) and
               all([isinstance(_, str) for _ in excluded_dirs])):
            raise ValueError

        self.excluded_dirs = excluded_dirs
        self.excluded_files = excluded_files
        self.file_system = {"UnitTests": {}}
        self.indexer = Indexer
        self.parent_dir = parent_dir
        self.pedantic = pedantic
        self.runner = unittest.TextTestRunner()
        self.score = [0, 0]
        self.construct_filesystem()

    def construct_filesystem(self):
        """
        Read the contents of `UnitTests` and attempt to construct
        a working structure to load all valid tests

        We can also specify which directories/files should be ignored
        during construction.

        pedantic: allows for the test to print to stdout/stderr. This can be toggled to
            False to allow for less output.

        """

        for dirpath, dirs, filepath in os.walk(self.parent_dir, topdown=True):
            dirs.sort()
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            filepath[:] = [f for f in filepath if f not in self.excluded_files]
            test_name = os.path.basename(dirpath)
            if not(test_name == str(self.parent_dir)):
                self.file_system["UnitTests"].update(
                    {
                        test_name: [(pathlib.Path(self.parent_dir / test_name / path),
                                     self.pedantic) for path in filepath]
                    }
                )

    def print_resultant_message(self, container: list):
        """
        Print the output of the unittests ran
        """

        if not(isinstance(container, list) and
               all([isinstance(_, int) for _ in container])):
            raise ValueError

        total, failures = container
        if(failures == 0):
            print(termcolor.colored(
                f'All {total} test(s) have all passed', 'green'
            ))
        else:
            print(termcolor.colored(
                f'{total - failures}/{total} test(s) have passed', 'red'
            ))

    def test_certain_class(self, name: str):
        """
        Test certain module from Tuffix:
        Example: Tuffix.Editors
        """

        if not(isinstance(name, str)):
            raise ValueError

        total_counter = [0, 0]
        test_suite = None
        try:
            test_suite = self.file_system[str(self.parent_dir)][name]
        except KeyError:
            print(f'[ERROR] Could not find test {name}')
            quit()

        print(f"[INFO] Testing all of {name}")
        for __test in test_suite:
            test, _ = __test
            result = self.conduct_test(test)
            total_counter[self.indexer.TOTAL.value] += result[self.indexer.TOTAL.value]
            total_counter[self.indexer.FAILURE.value] += result[self.indexer.FAILURE.value]

        self.print_resultant_message(total_counter)

    def conduct_test(self, path: pathlib.Path):
        """
        Run the test given a path to the module and if it will be pendantic
        """

        if not(isinstance(path, pathlib.Path)):
            raise ValueError(f'{path=} is not a `pathlib.Path`')
        test_re = re.compile(".*Test")

        # get the specifications from the path given
        spec = importlib.util.spec_from_file_location("test", path)
        # load the specifications as a module to be imported
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if(hasattr(module, 'IGNORE_ME')):
            # to make testing go by quicker
            # please remove `IGNORE_ME = True` from all instances

            print(f'[INFO] Ignoring {path}')
            return [0, 0]

        # these tests names must conform to a certain format
        # for example: ExampleTest
        # not working example: SomethingOrAnother

        tests = [_test for _test in dir(module) if (test_re.match(_test))]
        counter = [0, 0]

        for _test in tests:
            print(f'[INFO] Conducting {_test}')
            # get the current instance of the class we are interested in
            test_instance = getattr(module, _test)
            # load the current test into a testloader for unittest
            test_suite = SequentialTestLoader().loadTestsFromTestCase(test_instance)

            total_test_count = test_suite.countTestCases()

            counter[self.indexer.TOTAL.value] += total_test_count

            # send all output from functions to /dev/null if specified

            if(self.pedantic):
                result = self.runner.run(test_suite)
            else:
                with quiet():
                    result = self.runner.run(test_suite)
            counter[self.indexer.FAILURE.value] += (len(result.failures))

        return counter

    def run_all_tests(self):
        """
        Run all tests
        """

        total_counter = [0, 0]
        tests = self.construct_filesystem()
        for name, _ in tests[str(self.parent_dir)].items():
            self.test_certain_class(name)
