# Tests/test_main.py
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path to allow importing project modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import main
# from cable import CableType # Assuming CableType is in cable.py (it's in config.py)
from config import CableType, DEFAULT_CONDUIT_RADIUS # Corrected import

class TestMainLogic(unittest.TestCase):

    def setUp(self):
        # Reset main module's state before each test
        main.cables = []
        main.next_cable_id = 1
        main.current_conduit_radius = DEFAULT_CONDUIT_RADIUS # from config
        main.space = MagicMock() # Mock Pymunk space
        main.conduit_body = None
        main.conduit_segments = []
        # Mock create_cable from cable.py to avoid actual Pymunk body/shape creation in unit tests
        # self.create_cable_patch = patch('main.create_cable') # if create_cable is imported as main.create_cable
        self.create_cable_patch = patch('cable.create_cable') # create_cable is in cable.py, imported by main.py
        self.mock_create_cable = self.create_cable_patch.start()
        
        # Define what mock_create_cable returns
        mock_body = MagicMock()
        mock_shape = MagicMock()
        # Ensure the mock returns a tuple that includes a CableType enum instance
        self.mock_create_cable.side_effect = lambda pos, c_type: (mock_body, mock_shape, c_type)


    def tearDown(self):
        self.create_cable_patch.stop()

    def test_spawn_cable_assigns_ids(self):
        main.spawn_cable(position=(100, 100), cable_type_to_spawn=CableType.SINGLE)
        self.assertEqual(len(main.cables), 1)
        self.assertEqual(main.cables[0][0], 1) # Check ID of first cable
        self.assertEqual(main.cables[0][3], CableType.SINGLE) # Check cable type stored

        main.spawn_cable(position=(110, 110), cable_type_to_spawn=CableType.THREE_CORE)
        self.assertEqual(len(main.cables), 2)
        self.assertEqual(main.cables[1][0], 2) # Check ID of second cable
        self.assertEqual(main.cables[1][3], CableType.THREE_CORE) # Check cable type stored
        
        # Check that Pymunk add was called
        self.assertEqual(main.space.add.call_count, 4) # 2 bodies, 2 shapes

    def test_remove_cables_by_ids(self):
        # Spawn a few cables
        main.spawn_cable(position=(100, 100), cable_type_to_spawn=CableType.SINGLE) # ID 1
        # Retrieve the mocked body and shape for cable ID 2 for assertion later
        body2, shape2, _ = self.mock_create_cable((110,110), CableType.THREE_CORE)
        main.cables.append((main.next_cable_id -1, body2, shape2, CableType.THREE_CORE)) # Manually add to list after mock setup for ID 2
        
        body3, shape3, _ = self.mock_create_cable((120,120), CableType.FOUR_CORE)
        main.cables.append((main.next_cable_id, body3, shape3, CableType.FOUR_CORE)) # Manually add to list for ID 3
        main.next_cable_id+=1 # Simulate spawn's ID increment

        main.remove_cables_by_ids([2,3])
        self.assertEqual(len(main.cables), 1)
        self.assertEqual(main.cables[0][0], 1) # Cable with ID 1 should remain

        # Check that Pymunk remove was called for the correct objects
        self.assertEqual(main.space.remove.call_count, 4) 
        # Example: main.space.remove.assert_any_call(body2, shape2) # This checks if body2 and shape2 were removed in separate calls
        # Correct way to check for multiple calls with specific arguments:
        self.assertTrue(any(call_args == ((body2,),) for call_args in main.space.remove.call_args_list))
        self.assertTrue(any(call_args == ((shape2,),) for call_args in main.space.remove.call_args_list))
        self.assertTrue(any(call_args == ((body3,),) for call_args in main.space.remove.call_args_list))
        self.assertTrue(any(call_args == ((shape3,),) for call_args in main.space.remove.call_args_list))


    def test_remove_cables_by_ids_non_existent(self):
        main.spawn_cable(position=(100, 100), cable_type_to_spawn=CableType.SINGLE) # ID 1
        main.remove_cables_by_ids([99]) # Try to remove non-existent ID
        self.assertEqual(len(main.cables), 1) # Should not change
        self.assertEqual(main.space.remove.call_count, 0) # Nothing should be removed

    def test_reset_view_clears_cables_and_resets_id(self):
        # Mock bodies and shapes to be added to the space for removal check
        mock_body1, mock_shape1, _ = self.mock_create_cable((100,100), CableType.SINGLE)
        main.cables.append((1, mock_body1, mock_shape1, CableType.SINGLE))
        main.next_cable_id = 2
        
        mock_body2, mock_shape2, _ = self.mock_create_cable((110,110), CableType.THREE_CORE)
        main.cables.append((2, mock_body2, mock_shape2, CableType.THREE_CORE))
        main.next_cable_id = 3

        # Simulate adding these to the space so remove can be called on them
        main.space.bodies = [mock_body1, mock_body2] # Simplified mock
        main.space.shapes = [mock_shape1, mock_shape2] # Simplified mock
        
        main.reset_view()
        self.assertEqual(len(main.cables), 0)
        self.assertEqual(main.next_cable_id, 1)
        # Check Pymunk remove calls for each cable's body and shape
        self.assertEqual(main.space.remove.call_count, 4) # 2 cables * (1 body + 1 shape)

    def test_update_simulation_conduit_radius_state(self):
        # This test focuses on the state change, not the full Pymunk interaction
        # Mock rebuild_conduit_in_space to prevent its actual execution
        with patch('main.rebuild_conduit_in_space') as mock_rebuild:
            mock_rebuild.return_value = (MagicMock(), []) # Return dummy body and segments
            main.update_simulation_conduit_radius(250.0)
            self.assertEqual(main.current_conduit_radius, 250.0)
            mock_rebuild.assert_called_once() # Check if it was called

if __name__ == '__main__':
    unittest.main()
