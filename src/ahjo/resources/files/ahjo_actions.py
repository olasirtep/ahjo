from ahjo.action import action, registered_actions
from ahjo.action import create_multiaction

@action(affects_database=False)
def test_action_import(context):
    """Example/test function for custom actions."""
    print("test works, action imported")

#create_multiaction("complete-build", ["init", "structure", "deploy", "data", "testdata", "test"])
