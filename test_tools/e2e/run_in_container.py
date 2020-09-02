from end_to_end_tests import manager as test_manager

manager = test_manager.EndToEndTestManager()
for test in manager.get_tests():
    t = test[1]()
    t.run_wrapper()