import unittest


class SequentialTestLoader(unittest.TestLoader):
    """
    Sort the unit test in sequential order
    Why this is not a default option is beyond me
    SOURCE: https://stackoverflow.com/a/50283484
    """

    def getTestCaseNames(self, testCaseClass):
        test_names = super().getTestCaseNames(testCaseClass)
        testcase_methods = list(testCaseClass.__dict__.keys())
        test_names.sort(key=testcase_methods.index)
        return test_names
