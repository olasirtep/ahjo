from ahjo.action import action, registered_actions

@action("test-action-import", False)
def test_action_import(context):
    """Example/test function for custom actions."""
    print("test works, action imported")

#create_multiaction("complete-build", ["init", "structure", "deploy", "data", "testdata", "test"])
